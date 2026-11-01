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
