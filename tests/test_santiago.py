import pytest
from datetime import date, timedelta

# --- HELPERS ---
def create_book(client, title="Test Book", total_copies=2):
    r = client.post("/books", json={"title": title, "author": "A", "isbn": "123", "total_copies": total_copies})
    return r.get_json()["id"]

def create_member(client, name="Test Member"):
    r = client.post("/members", json={"name": name, "email": "test@test.com"})
    return r.get_json()["id"]

# --- FEATURE: LOANS (CHECKOUT) ---
def test_checkout_decrements_available_copies(client):
    book_id = create_book(client, total_copies=2)
    member_id = create_member(client)
    
    r = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    assert r.status_code == 201
    assert r.get_json()["book_id"] == book_id
    
    book = client.get(f"/books/{book_id}").get_json()
    assert book["available_copies"] == 1

def test_checkout_nonexistent_book_fails(client):
    member_id = create_member(client)
    r = client.post("/loans", json={"book_id": 999, "member_id": member_id})
    assert r.status_code == 404

# --- FEATURE: RETURNS ---
def test_return_restores_available_copies(client):
    book_id = create_book(client, total_copies=1)
    member_id = create_member(client)
    loan_id = client.post("/loans", json={"book_id": book_id, "member_id": member_id}).get_json()["id"]
    
    r = client.put(f"/loans/{loan_id}/return")
    assert r.status_code == 200
    assert r.get_json()["return_date"] is not None
    
    book = client.get(f"/books/{book_id}").get_json()
    assert book["available_copies"] == 1

def test_repeated_return_is_rejected(client):
    book_id = create_book(client)
    member_id = create_member(client)
    loan_id = client.post("/loans", json={"book_id": book_id, "member_id": member_id}).get_json()["id"]
    
    client.put(f"/loans/{loan_id}/return")
    r = client.put(f"/loans/{loan_id}/return")
    assert r.status_code == 400
    assert r.get_json()["error"] == "Loan already returned"

# --- FEATURE: LIST LOANS (Test the Bug) ---
def test_list_loans_filters_by_member_id(client):
    m1 = create_member(client, "Alice")
    m2 = create_member(client, "Bob")
    b1 = create_book(client, "Book 1")
    b2 = create_book(client, "Book 2")
    
    client.post("/loans", json={"book_id": b1, "member_id": m1})
    client.post("/loans", json={"book_id": b2, "member_id": m2})
    
    # R12.0: A patron should see their own books.
    # BUG: The code filters by book_id instead of member_id.
    r = client.get(f"/loans?member_id={m1}")
    loans = r.get_json()
    
    # This test will FAIL because of the bug. Keep it and document it!
    assert len(loans) == 1, f"Expected 1 loan for Alice, got {len(loans)} (Bug: filtered by book_id)"
    assert loans[0]["member_id"] == m1

# --- FEATURE: RESERVATIONS ---
def test_create_reservation_success(client):
    book_id = create_book(client)
    member_id = create_member(client)
    r = client.post("/reservations", json={"book_id": book_id, "member_id": member_id})
    assert r.status_code == 201
    assert r.get_json()["book_id"] == book_id

# --- FEATURE: FINES (Test the Bug) ---
def test_fine_calculation_for_returned_loan(client):
    book_id = create_book(client)
    member_id = create_member(client)
    loan_id = client.post("/loans", json={"book_id": book_id, "member_id": member_id}).get_json()["id"]
    
    from app import store
    loan = store.loans[loan_id]
    loan.due_date = date.today() - timedelta(days=5)
    
    client.put(f"/loans/{loan_id}/return")
    
    # R9.0: Fine should be fixed at time of return (5 days * 0.25 = 1.25)
    r = client.get(f"/loans/{loan_id}/fine")
    assert r.get_json()["fine_amount"] == 1.25

# --- ENHANCEMENT: MEMBER FINES ---
def test_member_lookup_shows_total_fines(client):
    book_id = create_book(client)
    member_id = create_member(client)
    loan_id = client.post("/loans", json={"book_id": book_id, "member_id": member_id}).get_json()["id"]
    
    # Manually backdate the loan by 4 days
    from app import store
    loan = store.loans[loan_id]
    loan.due_date = date.today() - timedelta(days=4)
    
    r = client.get(f"/members/{member_id}")
    assert r.status_code == 200
    # 4 days * 0.25 = 1.00
    assert r.get_json()["total_fines"] == 1.00

def test_member_lookup_fines_ignore_returned_books(client):
    book_id = create_book(client)
    member_id = create_member(client)
    loan_id = client.post("/loans", json={"book_id": book_id, "member_id": member_id}).get_json()["id"]
    
    from app import store
    loan = store.loans[loan_id]
    loan.due_date = date.today() - timedelta(days=4)
    
    # Return the book (fines stop accumulating for the member total)
    client.put(f"/loans/{loan_id}/return")
    
    r = client.get(f"/members/{member_id}")
    assert r.get_json()["total_fines"] == 0.00

# --- FEATURE: MEMBERS (CRUD) ---
def test_list_members(client):
    create_member(client, "Alice")
    create_member(client, "Bob")
    
    r = client.get("/members")
    assert r.status_code == 200
    members = r.get_json()
    assert len(members) == 2
    assert members[0]["name"] == "Alice"
    assert members[1]["name"] == "Bob"

def test_update_and_delete_member(client):
    member_id = create_member(client, "To Update")
    
    # Update
    r = client.put(f"/members/{member_id}", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Updated Name"
    
    # Delete
    r2 = client.delete(f"/members/{member_id}")
    assert r2.status_code == 204
    
    # Verify deleted
    r3 = client.get(f"/members/{member_id}")
    assert r3.status_code == 404
    