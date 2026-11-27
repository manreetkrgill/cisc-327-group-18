import pytest
from playwright.sync_api import Page, expect


def test_get_books_list(page: Page):
    """Test 1 (Success Case): Successfully retrieve the list of books"""
    response = page.goto("http://127.0.0.1:5000/books")
    assert response.status == 200
    expect(page.locator("body")).to_contain_text("[")


def test_add_book_missing_title(page: Page):
    """Test 2 (Error/Boundary Case): Attempt to add a book without a title"""
    response = page.request.post(
        "http://127.0.0.1:5000/books",
        data={
            "author": "Unknown Author",
            "isbn": "1234567890",
        },
    )
    assert response.status == 500
