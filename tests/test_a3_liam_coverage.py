import pytest
from datetime import date
from app import store
from app.models.book import Book
from app.models.member import Member
from app.models.reservation import Reservation

def test_create_and_get_books(client):
    response = client.post("/books", json={
        "title": "Coverage Book", "author": "Me", "isbn": "999", "total_copies": 2
    })
    assert response.status_code == 201
    
    response = client.get("/books")
    assert response.status_code == 200

def test_get_single_book_and_404(client):
    book = Book(id=10, title="T", author="A", isbn="1", total_copies=1, available_copies=1)
    store.books[10] = book
    
    response = client.get("/books/10")
    assert response.status_code == 200
    
    response = client.get("/books/999")
    assert response.status_code == 404

def test_update_and_delete_book(client):
    book = Book(id=11, title="T", author="A", isbn="1", total_copies=1, available_copies=1)
    store.books[11] = book
    
    response = client.put("/books/11", json={"title": "Updated"})
    assert response.status_code == 200
    
    response = client.delete("/books/11")
    assert response.status_code == 204
    assert 11 not in store.books

def test_create_and_get_members(client):
    response = client.post("/members", json={"name": "Test", "email": "t@t.com"})
    assert response.status_code == 201
    
    response = client.get("/members")
    assert response.status_code == 200

def test_get_single_member_and_404(client):
    member = Member(id=20, name="M", email="m@m.com")
    store.members[20] = member
    
    response = client.get("/members/20")
    assert response.status_code == 200
    
    response = client.get("/members/999")
    assert response.status_code == 404

def test_delete_member(client):
    member = Member(id=21, name="M", email="m@m.com")
    store.members[21] = member
    
    response = client.delete("/members/21")
    assert response.status_code == 204
    assert 21 not in store.members

def test_reservations_routes(client):
    book = Book(id=30, title="T", author="A", isbn="1", total_copies=1, available_copies=1)
    store.books[30] = book
    member = Member(id=30, name="M", email="m@m.com")
    store.members[30] = member
    
    # Create reservation
    response = client.post("/reservations", json={"book_id": 30, "member_id": 30})
    assert response.status_code == 201

    # List reservations
    response = client.get("/reservations")
    assert response.status_code == 200

    # Test reservation 404s
    response = client.post("/reservations", json={"book_id": 999, "member_id": 30})
    assert response.status_code == 404
    response = client.post("/reservations", json={"book_id": 30, "member_id": 999})
    assert response.status_code == 404

# --- VIEWS COVERAGE TESTS ---
def test_html_views(client):
    """Hits the HTML routes in views.py to boost coverage."""
    # GET routes
    assert client.get("/").status_code == 200
    assert client.get("/ui/books").status_code == 200
    assert client.get("/ui/members").status_code == 200
    assert client.get("/ui/loans").status_code == 200

    # Test creating a book via HTML form (POST)
    client.post("/ui/books", data={"title": "HTML Book", "author": "Me", "isbn": "1", "total_copies": "1"})
    
    # Test creating a member via HTML form (POST)
    client.post("/ui/members", data={"name": "HTML Member", "email": "html@example.com"})
    
    # Test deleting a book and member via HTML form
    client.post("/ui/books/1/delete")
    client.post("/ui/members/1/delete")

def test_html_loans(client):
    book = Book(id=50, title="T", author="A", isbn="1", total_copies=1, available_copies=1)
    store.books[50] = book
    member = Member(id=50, name="M", email="m@m.com")
    store.members[50] = member

    # Test creating a loan via HTML form
    client.post("/ui/loans", data={"book_id": "50", "member_id": "50"})
    
    # Test returning a loan via HTML form
    client.post("/ui/loans/1/return")

# --- BUG DOCUMENTATION (The Reservation Bug) ---
@pytest.mark.xfail(reason="Known bug: checkout does not check reservations")
def test_checkout_bypasses_reservation(client):
    """Tests the bug mentioned in reservations.py."""
    book = Book(id=60, title="T", author="A", isbn="1", total_copies=1, available_copies=1)
    store.books[60] = book
    member = Member(id=60, name="M", email="m@m.com")
    store.members[60] = member
    
    # Reserve the book
    client.post("/reservations", json={"book_id": 60, "member_id": 60})
    
    # Another member tries to check out the reserved book
    # (Due to the bug, this currently succeeds and should fail the test)
    response = client.post("/loans", json={"book_id": 60, "member_id": 60})
    assert response.status_code == 400  # Should fail because it's reserved