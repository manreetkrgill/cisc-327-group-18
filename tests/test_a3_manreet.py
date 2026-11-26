import pytest
from unittest.mock import patch

# Notification Failure Test (Stub)
@patch("app.routes.loans.send_notification")
def test_overdue_reminder_failure_does_not_break(mock_send, client):
    """Stub returning False: ensure return succeeds but notification fails."""
    mock_send.return_value = False  # Stub: force failure
    
    # 1. Setup an overdue loan
    book = client.post("/books", json={"title": "B", "author": "A", "isbn": "1", "total_copies": 1}).get_json()
    member = client.post("/members", json={"name": "M", "email": "m@example.com"}).get_json()
    loan = client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]}).get_json()
    
    # Force it to be overdue by manually changing the date in the store
    from app import store
    from datetime import date, timedelta
    store.loans[loan["id"]].due_date = date.today() - timedelta(days=5)
    
    # 2. Return the book
    resp = client.put(f"/loans/{loan['id']}/return")
    
    # 3. Assert application behavior (it shouldn't crash)
    assert resp.status_code == 200
    assert store.books[book["id"]].available_copies == 1
    
    # Verify the mock was called (but it returned False)
    mock_send.assert_called_once()

# No Trigger Test (Mock)
@patch("app.routes.loans.send_notification")
def test_on_time_return_sends_no_notification(mock_send, client):
    """Mock verifying no call is made when the book is returned on time."""
    mock_send.return_value = True
    
    # 1. Setup a normal loan (due in 14 days)
    book = client.post("/books", json={"title": "B", "author": "A", "isbn": "1", "total_copies": 1}).get_json()
    member = client.post("/members", json={"name": "M", "email": "m@example.com"}).get_json()
    loan = client.post("/loans", json={"book_id": book["id"], "member_id": member["id"]}).get_json()
    
    # 2. Return the book BEFORE it is due
    resp = client.put(f"/loans/{loan['id']}/return")
    
    # 3. Assert application behavior
    assert resp.status_code == 200
    
    # 4. Interaction verification: Ensure it was NOT called
    mock_send.assert_not_called()