import pytest
from playwright.sync_api import Page, expect

def test_get_books_list(page: Page):
    """Test 1 (Success Case): Successfully retrieve the list of books"""
    # Go to the books endpoint
    response = page.goto("http://127.0.0.1:5000/books")
    
    # Verify the response is successful (200 OK)
    assert response.status == 200
    
    # Verify the body contains a JSON array
    expect(page.locator("body")).to_contain_text("[")

def test_add_book_missing_title(page: Page):
    """Test 2 (Error/Boundary Case): Attempt to add a book without a title"""
    # Use Playwright to send a POST request directly to your API
    response = page.request.post(
        "http://127.0.0.1:5000/books",
        data={
            "author": "Unknown Author",
            "isbn": "1234567890"
            # We intentionally leave out the "title" to test the boundary case
        }
    )
    
    # Your backend code (books.py) does data["title"], which will cause a 
    # KeyError and return a 500 Internal Server Error. We assert that it fails.
    assert response.status == 500