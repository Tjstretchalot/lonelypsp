import io

from fastapi import APIRouter

from lonelypsp.tracing.impl.simple.db import SimpleTracingDB

router = APIRouter()


DB_PATH: str = "tracing.db"


@router.get("/index.html")
def index() -> str:
    result = io.StringIO()
    result.write(
        """
<html>
<head>
    <title>LonelyPS - stats</title>
</head>
<body>
"""
    )

    with SimpleTracingDB(DB_PATH) as db:
        assert db.cursor is not None
        result.write("<h1>Notify</h1>")

        db.cursor.execute("BEGIN DEFERRED TRANSACTION")
        try:
            db.cursor.execute("SELECT COUNT(*) FROM stateless_notifies")
            num_notifies = db.cursor.fetchone()[0]

            result.write(f"<p>There were {num_notifies} notifications to ")

            db.cursor.execute(
                "SELECT COUNT(DISTINCT json_extract(extra, '$.broadcaster')) "
                "FROM stateless_notify_timings "
                "WHERE name = 'sending_request'"
            )
            num_broadcaster = db.cursor.fetchone()[0]
            result.write(f"{num_broadcaster} broadcasters</p>")

            result.write("</p>")
        finally:
            db.cursor.execute("COMMIT TRANSACTION")

    result.write("</body></html>")
    return result.getvalue()
