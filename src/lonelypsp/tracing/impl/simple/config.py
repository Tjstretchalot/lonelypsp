from typing import Optional

from lonelypsp.compat import fast_dataclass


@fast_dataclass
class SimpleTracingConfig:
    """Configuration for the simple tracing implementation"""

    trace_max_age_seconds: Optional[int] = 60 * 60 * 24 * 90
    """The maximum age of traces before they are cleaned up by the next run; None for
    no maximum age
    """
