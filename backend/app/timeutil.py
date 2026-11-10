from datetime import timezone


def as_utc(dt):
    """SQLite returns timezone-aware columns without their timezone; they were stored as UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso_utc(dt):
    """ISO 8601 with the +00:00 offset, so browsers don't read the time as local time."""
    return as_utc(dt).isoformat() if dt is not None else None
