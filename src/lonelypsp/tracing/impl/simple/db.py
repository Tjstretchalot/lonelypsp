import asyncio
import os
import queue
import sqlite3
import threading
import time
from enum import Enum, auto
from types import TracebackType
from typing import Any, List, Literal, Optional, Tuple, Type, Union, cast

from lonelypsp.compat import fast_dataclass
from lonelypsp.tracing.impl.simple.config import SimpleTracingConfig


class SimpleTracingDB:
    """Not process-safe or thread-safe, intended to be used in a dedicated thread"""

    def __init__(self, database: str) -> None:
        self.database: str = database
        """the path to where the database is stored, typically `traces.db`"""

        self.conn: Optional[sqlite3.Connection] = None
        """The connection to the database, if open"""

        self.cursor: Optional[sqlite3.Cursor] = None
        """the default cursor for the database, if open"""

    def __enter__(self) -> "SimpleTracingDB":
        conn = sqlite3.connect(self.database)
        try:
            self._setup(conn)

            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys = ON")
            except BaseException:
                cursor.close()
                raise
        except BaseException:
            conn.close()
            raise

        self.conn = conn
        self.cursor = cursor
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        try:
            if self.cursor is not None:
                self.cursor.close()
        finally:
            if self.conn is not None:
                self.conn.close()

    def _setup(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("BEGIN IMMEDIATE TRANSACTION")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY) WITHOUT ROWID"
            )
            cursor.execute("COMMIT TRANSACTION")

            current_file_path = __file__
            current_directory = os.path.dirname(current_file_path)
            migrations_directory = os.path.join(current_directory, "migrations")

            sorted_migrations = sorted(os.listdir(migrations_directory))

            for migration in sorted_migrations:
                if not migration.endswith(".sql"):
                    continue

                cursor.execute("BEGIN DEFERRED TRANSACTION")
                cursor.execute("SELECT 1 FROM migrations WHERE name = ?", (migration,))
                ran_migration = cursor.fetchone() is not None
                cursor.execute("COMMIT TRANSACTION")

                if ran_migration:
                    continue

                migration_path = os.path.join(migrations_directory, migration)
                with open(migration_path, "r") as migration_file:
                    migration_sql = migration_file.read()

                try:
                    cursor.executescript(migration_sql)
                except BaseException as e:
                    raise RuntimeError(f"Failed to run migration {migration}") from e

                cursor.execute("BEGIN IMMEDIATE TRANSACTION")
                cursor.execute("INSERT INTO migrations VALUES (?)", (migration,))
                cursor.execute("COMMIT TRANSACTION")
        finally:
            cursor.close()


class _ThreadQueueItemType(Enum):
    """The type of item in the queue"""

    SCRIPT = auto()
    """A script to execute"""

    STOP = auto()
    """A signal to stop the thread"""


@fast_dataclass
class _ThreadQueueItemScript:
    """A script to execute"""

    type: Literal[_ThreadQueueItemType.SCRIPT]
    """enum discriminator"""

    commands: List[Tuple[str, List[Any]]]
    """the commands to execute() in order"""


@fast_dataclass
class _ThreadQueueItemStop:
    """A signal to stop the thread"""

    type: Literal[_ThreadQueueItemType.STOP]
    """enum discriminator"""


_ThreadQueueItem = Union[
    _ThreadQueueItemScript,
    _ThreadQueueItemStop,
]


def _sweep_traces(
    config: SimpleTracingConfig, cursor: sqlite3.Cursor, now: float
) -> None:
    if config.trace_max_age_seconds is None:
        return

    cursor.execute("BEGIN IMMEDIATE TRANSACTION")
    cursor.execute(
        "DELETE FROM stateless_notifies WHERE created_at < ?",
        (now - config.trace_max_age_seconds,),
    )
    cursor.execute("COMMIT TRANSACTION")


def _thread_main(
    config: SimpleTracingConfig, database: str, q: queue.SimpleQueue
) -> None:
    with SimpleTracingDB(database) as db:
        assert db.cursor is not None

        next_sweep_at: Optional[float] = None
        if config.trace_max_age_seconds is not None:
            next_sweep_at = time.time() + config.trace_max_age_seconds

        while True:
            now = time.time()
            timeout: Optional[float] = None
            if (
                config.trace_max_age_seconds is not None
                and next_sweep_at is not None
                and now >= next_sweep_at
            ):
                _sweep_traces(config, db.cursor, now)
                next_sweep_at = now + config.trace_max_age_seconds

            if next_sweep_at is not None:
                timeout = next_sweep_at - now

            try:
                result = cast(
                    _ThreadQueueItem,
                    q.get(
                        block=True,
                        timeout=None if timeout is None else min(10, timeout),
                    ),
                )
            except queue.Empty:
                continue
            if result.type == _ThreadQueueItemType.STOP:
                break

            for command, args in result.commands:
                db.cursor.execute(command, args)


class SimpleTracingDBSidecar:
    """Starts a thread where the database is setup and allows deferring an entire sequence
    of operations to be run in the same thread

    Acts as an asynchronous context manager for starting/stopping the thread
    """

    def __init__(self, config: SimpleTracingConfig, database: str) -> None:
        self.config: SimpleTracingConfig = config
        """Various configuration options"""

        self.database: str = database
        """The path to the database or :memory: for an in-memory store"""

        self._lock: asyncio.Lock = asyncio.Lock()
        """Lock for interacting with _thread to ensure only one thread is started"""

        self._thread: Optional[threading.Thread] = None
        """The thread running the database"""

        self._queue: Optional[queue.SimpleQueue] = None
        """The queue to push tasks to the thread"""

    async def __aenter__(self) -> "SimpleTracingDBSidecar":
        async with self._lock:
            if self._thread is not None:
                raise RuntimeError("Thread already started")

            q: queue.SimpleQueue = queue.SimpleQueue()
            try:
                thread = threading.Thread(
                    target=_thread_main,
                    args=(self.config, self.database, q),
                    daemon=True,
                )

                await asyncio.get_running_loop().run_in_executor(None, thread.start)
            except BaseException:
                q.put(_ThreadQueueItemStop(type=_ThreadQueueItemType.STOP))
                raise

            self._thread = thread
            self._queue = q
            return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        async with self._lock:
            if self._thread is None:
                raise RuntimeError("Thread not started")
            if self._queue is None:
                raise RuntimeError("Queue not available")

            q = self._queue
            thread = self._thread
            self._queue = None
            self._thread = None

            q.put(_ThreadQueueItemStop(type=_ThreadQueueItemType.STOP))
            await asyncio.get_running_loop().run_in_executor(None, thread.join)

    def enqueue(self, commands: List[Tuple[str, List[Any]]]) -> None:
        assert self._queue is not None
        assert self._thread is not None
        assert self._thread.is_alive()
        self._queue.put(
            _ThreadQueueItemScript(type=_ThreadQueueItemType.SCRIPT, commands=commands)
        )
