import uuid
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"


def test_success_add_book_via_ui(page: Page):
    unique = f"B-A4-{uuid.uuid4().hex[:8]}"
    page.goto(f"{BASE_URL}/ui/books")
    page.fill("input[name='title']", unique)
    page.fill("input[name='author']", "A4 Test Author")
    page.fill("input[name='isbn']", "9780000000000")
    page.fill("input[name='total_copies']", "2")
    page.click("button:has-text('Add Book')")
    expect(page.locator("table")).to_contain_text(unique)
    expect(page.locator("table")).to_contain_text("A4 Test Author")


def test_error_blank_title_rejected(page: Page):
    page.goto(f"{BASE_URL}/ui/books")
    page.fill("input[name='author']", "A4 Test Author")
    page.fill("input[name='isbn']", "9780000000001")
    page.fill("input[name='total_copies']", "1")
    page.click("button:has-text('Add Book')")
    expect(page).to_have_url(f"{BASE_URL}/ui/books")
    title_input = page.locator("input[name='title']")
    expect(title_input).to_have_js_property("validity.valid", False)
    expect(page.locator("h2:has-text('Add a Book')")).to_be_visible()
