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
