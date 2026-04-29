import threading
from collections import defaultdict
from datetime import datetime, timezone

_attempts: dict[str, list[datetime]] = defaultdict(list)
_lock = threading.Lock()

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 minutos


def is_rate_limited(identifier: str) -> bool:
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - WINDOW_SECONDS
    with _lock:
        _attempts[identifier] = [t for t in _attempts[identifier] if t.timestamp() > cutoff]
        if len(_attempts[identifier]) >= MAX_ATTEMPTS:
            return True
        _attempts[identifier].append(now)
        return False
