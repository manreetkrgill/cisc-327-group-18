import pytest
from unittest.mock import patch
from datetime import date, timedelta
from notification_service import clear_notifications
from app import store
from app.models.loan import Loan
from app.models.book import Book
from app.models.member import Member

@pytest.fixture(autouse=True)
def _clean_simulator():
    clear_notifications()
    yield
    clear_notifications()

@pytest.fixture
def overdue_loan_setup():
    # Create a member and a book (using your exact model signatures)
    member = Member(id=1, name="Test Member", email="test@example.com")
    book = Book(id=1, title="Test Book", author="Author", isbn="123", total_copies=1, available_copies=0)
    store.members[1] = member
    store.books[1] = book
    
    # Create an overdue loan
    loan = Loan(id=1, book_id=1, member_id=1, due_date=date.today() - timedelta(days=5))
    store.loans[1] = loan
    return loan

# --- STUB: Success path ---
def test_overdue_reminder_sent_on_success(monkeypatch, client, overdue_loan_setup):
    monkeypatch.setattr("app.routes.loans.send_notification", lambda r, s, m: True)
    
    response = client.put("/loans/1/return")
    
    assert response.status_code == 200
    assert store.loans[1].return_date == date.today()

# --- STUB: Failure path ---
def test_overdue_reminder_failure_does_not_break(monkeypatch, client, overdue_loan_setup):
    monkeypatch.setattr("app.routes.loans.send_notification", lambda r, s, m: False)
    
    response = client.put("/loans/1/return")
    
    assert response.status_code == 200
    assert store.loans[1].return_date == date.today()

# --- MOCK: Verify arguments ---
def test_overdue_reminder_sends_expected_arguments(client, overdue_loan_setup):
    with patch("app.routes.loans.send_notification", return_value=True) as mock_send:
        client.put("/loans/1/return")
        
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        
        assert args[0] == "test@example.com"
        assert "[City Library] Overdue Return" == args[1]
        assert "Test Member" in args[2]
        assert "Test Book" in args[2]

# --- MOCK: Non-trigger path ---
def test_on_time_return_sends_no_notification(client):
    member = Member(id=2, name="Good Member", email="good@example.com")
    book = Book(id=2, title="Good Book", author="Author", isbn="456", total_copies=1, available_copies=0)
    store.members[2] = member
    store.books[2] = book
    loan = Loan(id=2, book_id=2, member_id=2, due_date=date.today() + timedelta(days=5))
    store.loans[2] = loan

    with patch("app.routes.loans.send_notification") as mock_send:
        response = client.put("/loans/2/return")
        
        assert response.status_code == 200
        mock_send.assert_not_called()

# --- LOANS COVERAGE TESTS ---
def test_return_book_not_found(client):
    response = client.put("/loans/999/return")
    assert response.status_code == 404

def test_return_book_already_returned(client, overdue_loan_setup):
    store.loans[1].return_date = date.today() - timedelta(days=1)
    response = client.put("/loans/1/return")
    assert response.status_code == 400

def test_checkout_book(client):
    book = Book(id=3, title="New Book", author="Author", isbn="789", total_copies=1, available_copies=1)
    store.books[3] = book
    member = Member(id=3, name="New Member", email="new@example.com")
    store.members[3] = member
    
    response = client.post("/loans", json={"book_id": 3, "member_id": 3})
    assert response.status_code == 201
    assert store.books[3].available_copies == 0

def test_checkout_book_not_found(client):
    response = client.post("/loans", json={"book_id": 999, "member_id": 1})
    assert response.status_code == 404

def test_renew_loan(client):
    loan = Loan(id=3, book_id=3, member_id=3, due_date=date.today())
    store.loans[3] = loan
    original_due = loan.due_date
    
    response = client.put("/loans/3/renew")
    assert response.status_code == 200
    assert store.loans[3].due_date > original_due

def test_renew_loan_already_returned(client):
    loan = Loan(id=4, book_id=1, member_id=1, due_date=date.today(), return_date=date.today())
    store.loans[4] = loan
    response = client.put("/loans/4/renew")
    assert response.status_code == 400

def test_list_loans(client):
    response = client.get("/loans")
    assert response.status_code == 200

def test_get_fine_not_found(client):
    response = client.get("/loans/999/fine")
    assert response.status_code == 404

# --- BUG DOCUMENTATION (The xfail test) ---
@pytest.mark.xfail(reason="Known bug: fine uses today's date instead of return_date")
def test_fine_is_fixed_on_return(client):
    loan = Loan(id=5, book_id=1, member_id=1, due_date=date.today() - timedelta(days=10))
    loan.return_date = date.today() - timedelta(days=5)
    store.loans[5] = loan
    
    response = client.get("/loans/5/fine")
    assert response.get_json()["fine_amount"] == 1.25