# notification_service.py
SENDER_PREFIX = "[City Library]"

def send_notification(recipient, subject, message):
    """
    Simulates sending a notification. Returns True on success, False on failure.
    """
    # Email validation check (as Santiago claimed he did)
    if not isinstance(recipient, str) or "@" not in recipient:
        return False
        
    # In a real app, this would connect to an SMTP server or API. Here, it just simulates success.
    return True