"""Member A tests - existing features """

import time
from datetime import date, timedelta

from app import store


# Helpers
def make_book(client, title="Clean Code", author="Robert Martin",
              isbn="978-0132350884", total_copies=1):
    resp = client.post("/books", json={
        "title": title, "author": author, "isbn": isbn,
        "total_copies": total_copies,
    })
    assert resp.status_code == 201
    return resp.get_json()


def make_member(client, name="Manreet", email="manreet@example.com"):
    resp = client.post("/members", json={"name": name, "email": email})
    assert resp.status_code == 201
    return resp.get_json()


def checkout(client, book_id, member_id):
    return client.post("/loans", json={"book_id": book_id, "member_id": member_id})


def available(client, book_id):
    return client.get(f"/books/{book_id}").get_json()["available_copies"]


def quiet(client):
    """Return 500 responses instead of re-raising server exceptions, so that
    tests can assert on the status code a real user would see."""
    client.application.config["PROPAGATE_EXCEPTIONS"] = False
    return client



# F2  Add a book
def test_add_book_returns_all_fields_and_is_retrievable(client):
    resp = client.post("/books", json={
        "title": "Dune", "author": "Frank Herbert",
        "isbn": "111", "total_copies": 3,
    })
    assert resp.status_code == 201
    book = resp.get_json()
    assert book == {
        "id": 1, "title": "Dune", "author": "Frank Herbert",
        "isbn": "111", "total_copies": 3, "available_copies": 3,
    }
    # persistent state: a later GET returns the same record
    assert client.get("/books/1").get_json() == book


def test_add_book_missing_required_field_is_rejected_with_client_error(client):
    """EXPECTED FAIL (D2): R5 (usable by non-technical staff) - an incomplete
    request should get a 4xx message, but the app crashes with HTTP 500
    (KeyError 'author')."""
    quiet(client)
    resp = client.post("/books", json={"title": "No author or isbn"})
    assert resp.status_code in (400, 422)
    assert client.get("/books").get_json() == []  # nothing half-created


# F3  Get one book
def test_get_book_returns_the_matching_book_only(client):
    make_book(client, title="One", isbn="1")
    second = make_book(client, title="Two", isbn="2")
    resp = client.get(f"/books/{second['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Two"
# F1  List / search books   (R1, R3)
def test_search_by_title_is_case_insensitive_and_partial(client):
    make_book(client, title="Clean Code", isbn="1")
    make_book(client, title="Dune", isbn="2")
    found = client.get("/books?search=CLEAN").get_json()
    assert [b["title"] for b in found] == ["Clean Code"]
    found = client.get("/books?search=ean%20co").get_json() 
    assert [b["title"] for b in found] == ["Clean Code"]


def test_search_by_author(client):
    make_book(client, title="Dune", author="Frank Herbert", isbn="1")
    make_book(client, title="Emma", author="Jane Austen", isbn="2")
    found = client.get("/books?search=herbert").get_json()
    assert [b["title"] for b in found] == ["Dune"]


def test_search_by_isbn_finds_the_book(client):
    """EXPECTED FAIL (D1): R1 says staff must be able to look a book up by
    title, author OR ISBN. /books?search=<isbn> returns [] because only title
    and author are compared."""
    make_book(client, title="Clean Code", isbn="978-0132350884")
    make_book(client, title="Dune", author="Frank Herbert", isbn="111")
    found = client.get("/books?search=978-0132350884").get_json()
    assert [b["title"] for b in found] == ["Clean Code"]


# F4  Update a book
def test_update_book_changes_given_fields_and_keeps_the_rest(client):
    book = make_book(client, title="Old", author="Author", isbn="1", total_copies=2)
    resp = client.put(f"/books/{book['id']}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "New"
    # persisted, and untouched fields preserved
    after = client.get(f"/books/{book['id']}").get_json()
    assert after["title"] == "New"
    assert after["author"] == "Author"
    assert after["isbn"] == "1"
    assert after["total_copies"] == 2


# F5  Delete a book
def test_cannot_delete_a_book_that_is_currently_on_loan(client):
    """EXPECTED FAIL (D4): R17 (keep track of books not returned) - deleting a
    book with an open loan should be refused. The app returns 204, orphaning
    the loan; returning that loan later then crashes with HTTP 500."""
    book = make_book(client)
    member = make_member(client)
    checkout(client, book["id"], member["id"])
    resp = client.delete(f"/books/{book['id']}")
    assert resp.status_code in (400, 409)
    assert client.get(f"/books/{book['id']}").status_code == 200
# F6  Check out a book   (R8, R3, R12)
def test_checkout_creates_loan_with_14_day_due_date(client):
    book, member = make_book(client), make_member(client)
    resp = checkout(client, book["id"], member["id"])
    assert resp.status_code == 201
    loan = resp.get_json()
    assert loan["book_id"] == book["id"]
    assert loan["member_id"] == member["id"]
    assert loan["loan_date"] == date.today().isoformat()
    assert loan["due_date"] == (date.today() + timedelta(days=14)).isoformat()
    assert loan["return_date"] is None


def test_checkout_decrements_available_copies_and_loan_is_listed(client):
    book = make_book(client, total_copies=3)
    member = make_member(client)
    loan = checkout(client, book["id"], member["id"]).get_json()
    after = client.get(f"/books/{book['id']}").get_json()
    assert after["available_copies"] == 2
    assert after["total_copies"] == 3          # total never changes
    assert client.get("/loans").get_json() == [loan]


def test_checkout_all_copies_then_one_more_is_refused(client):
    """EXPECTED FAIL (D5): R3/R8 - once available_copies is 0 the book is
    'checked out' and a further checkout must be refused. The app returns 201
    and drives available_copies to -1."""
    book = make_book(client, total_copies=1)
    alice, bob = make_member(client), make_member(client, "Bob", "b@example.com")
    assert checkout(client, book["id"], alice["id"]).status_code == 201
    assert available(client, book["id"]) == 0
    second = checkout(client, book["id"], bob["id"])
    assert second.status_code in (400, 409)
    assert available(client, book["id"]) == 0      # never negative

# F7  Return a loan   (R8, R3)
def test_return_sets_return_date_and_restores_available_copies(client):
    book, member = make_book(client, total_copies=2), make_member(client)
    loan = checkout(client, book["id"], member["id"]).get_json()
    assert available(client, book["id"]) == 1
    resp = client.put(f"/loans/{loan['id']}/return")
    assert resp.status_code == 200
    assert resp.get_json()["return_date"] == date.today().isoformat()
    assert available(client, book["id"]) == 2
    # persisted: the loan list shows the return date
    stored = client.get("/loans").get_json()[0]
    assert stored["return_date"] == date.today().isoformat()


def test_checkout_return_checkout_again_workflow(client):
    """Multi-step: borrow, return, borrow again with a different member."""
    book = make_book(client, total_copies=1)
    alice, bob = make_member(client), make_member(client, "Bob", "b@example.com")
    first = checkout(client, book["id"], alice["id"]).get_json()
    client.put(f"/loans/{first['id']}/return")
    second = checkout(client, book["id"], bob["id"])
    assert second.status_code == 201
    assert second.get_json()["id"] != first["id"]
    assert available(client, book["id"]) == 0
    loans = client.get("/loans").get_json()
    assert [l["return_date"] is None for l in loans] == [False, True]


# F8  Look up loans   (R12, R17)
def test_lookup_loans_by_member_id_returns_that_members_loans(client):
    """EXPECTED FAIL (D8): R12 (see what books I checked out). The member_id
    filter in routes/loans.py compares l.book_id instead of l.member_id, so
    ?member_id=3 returns [] and ?member_id=1 returns book-1 loans."""
    _three_loans(client)
    loans = client.get("/loans?member_id=3").get_json()
    assert sorted(l["id"] for l in loans) == [1, 2]
    assert all(l["member_id"] == 3 for l in loans)
# F9  Renew a loan (R6)
def test_renew_extends_due_date_by_14_days_and_persists(client):
    book, member = make_book(client), make_member(client)
    loan = checkout(client, book["id"], member["id"]).get_json()
    original_due = date.fromisoformat(loan["due_date"])
    resp = client.put(f"/loans/{loan['id']}/renew")
    assert resp.status_code == 200
    expected = (original_due + timedelta(days=14)).isoformat()
    assert resp.get_json()["due_date"] == expected
    assert client.get("/loans").get_json()[0]["due_date"] == expected


def test_renew_is_refused_when_another_member_is_queued_for_the_book(client):
    """EXPECTED FAIL (D9): R6 - a book may be renewed only if nobody is in
    the hold queue. After Bob reserves the book, renewing Alice's loan still
    returns 200 and pushes the due date out by another 14 days."""
    book = make_book(client, total_copies=1)
    alice, bob = make_member(client), make_member(client, "Bob", "b@example.com")
    loan = checkout(client, book["id"], alice["id"]).get_json()
    reserve = client.post("/reservations",
                          json={"book_id": book["id"], "member_id": bob["id"]})
    assert reserve.status_code == 201
    resp = client.put(f"/loans/{loan['id']}/renew")
    assert resp.status_code in (400, 409)
    assert client.get("/loans").get_json()[0]["due_date"] == loan["due_date"]

# F10  Web UI - Loans page (R5, R8)
def test_home_page_links_to_the_loans_page(client):
    """R8: check-out starts one click from the main screen."""
    html = client.get("/").get_data(as_text=True)
    assert 'href="/ui/loans"' in html


def test_ui_checkout_creates_loan_decrements_stock_and_shows_it(client):
    book, member = make_book(client, total_copies=2), make_member(client)
    resp = client.post("/ui/loans",
                       data={"book_id": book["id"], "member_id": member["id"]})
    assert resp.status_code == 302                       # redirect back
    assert resp.headers["Location"].endswith("/ui/loans")
    assert available(client, book["id"]) == 1
    assert len(client.get("/loans").get_json()) == 1     # visible through the API
    html = client.get("/ui/loans").get_data(as_text=True)
    assert "<td>1</td>" in html and "Return" in html

