"""Notification simulator - Assignment 3 (Library Project)."""

_notifications = []

SENDER_PREFIX = "[City Library]"

def is_service_available() -> bool:
    return True

def send_notification(recipient: str, subject: str, message: str) -> bool:
    if not all(isinstance(value, str) and value.strip()
               for value in (recipient, subject, message)):
        return False

    # Light customization: ensure valid email
    if "@" not in recipient:
        return False

    if not is_service_available():
        return False

    _notifications.append({
        "recipient": recipient,
        "subject": subject,
        "message": message,
    })
    return True

def get_notifications() -> list:
    return [n.copy() for n in _notifications]

def clear_notifications() -> None:
    _notifications.clear()