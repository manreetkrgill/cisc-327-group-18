# Library Management System (LMS)

A small Flask REST API for tracking books, members, and loans. Data is stored
**in memory** (plain Python objects, no database) and is reset every time the
app restarts, and every time the Docker container restarts. This project is
meant to run before you've covered databases.

**Repository layout:** the Assignment 3 features (overdue alerts, notification
service, A3 tests) and the Assignment 4 work (E2E tests, Docker) all live at the
repository root. There is no nested `library-management/` folder.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The app runs at `http://127.0.0.1:5000` (it binds `0.0.0.0:5000` so it is also
reachable from outside a container).

## Web UI

Open `http://127.0.0.1:5000/` in a browser for a basic HTML front end (plain
forms and tables, no JavaScript) to add/delete books and members, and check
books in/out:

| Page | Path |
|---|---|
| Home | `/` |
| Books | `/ui/books` |
| Members | `/ui/members` |
| Loans | `/ui/loans` |

This UI is separate from the JSON API below. It calls the same in-memory store.

## Entities

- **Book**: `id, title, author, isbn, total_copies, available_copies`
- **Member**: `id, name, email, membership_date` (member lookup also returns `total_fines`)
- **Loan**: `id, book_id, member_id, loan_date, due_date, return_date`

## JSON API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/books` | List all books |
| POST | `/books` | Create a book |
| GET | `/books/<id>` | Get one book |
| PUT | `/books/<id>` | Update a book |
| DELETE | `/books/<id>` | Delete a book |
| GET | `/members` | List all members |
| POST | `/members` | Create a member |
| GET | `/members/<id>` | Get one member (includes `total_fines`) |
| PUT | `/members/<id>` | Update a member |
| DELETE | `/members/<id>` | Delete a member |
| POST | `/loans` | Check out a book (`book_id`, `member_id`) |
| PUT | `/loans/<id>/return` | Return a loaned book (sends a notification if late) |
| GET | `/loans?member_id=&book_id=` | Look up loans |
| GET | `/overdue` | List overdue alerts (supports filtering by member) |

## Tests

### Unit / integration tests (Assignments 1-3)

```bash
pytest tests --ignore=tests/e2e
```

The E2E tests need a running server, so they are excluded here and from CI.

### End-to-end tests (Assignment 4, Playwright)

One-time setup (downloads the browser Playwright drives):

```bash
playwright install chromium
```

Start the app in one terminal:

```bash
python run.py
```

Run the E2E tests in a second terminal:

```bash
pytest tests/e2e -v --headed
```

Four tests run: two per member, one success and one error/boundary each.

| File | Test | Scenario |
|---|---|---|
| `tests/e2e/test_a4_santiago.py` | `test_get_books_list` | `GET /books` returns 200 with a JSON list |
| `tests/e2e/test_a4_santiago.py` | `test_add_book_missing_title` | `POST /books` without a title returns 500 |
| `tests/e2e/test_a4_manreet.py` | `test_success_add_book_via_ui` | Fill the `/ui/books` form; the new book appears in the table |
| `tests/e2e/test_a4_manreet.py` | `test_error_blank_title_rejected` | Blank title is blocked by form validation; page stays on `/ui/books` |

## Docker

Build the image and run it on port 5000:

```bash
docker build -t cisc327-a4 .
docker run --rm -p 5000:5000 cisc327-a4
```

Then open `http://localhost:5000`. Stop any local `python run.py` first so port
5000 is free. With the container running, the same E2E command works unchanged:

```bash
pytest tests/e2e -v --headed
```

Docker Hub image: `docker pull manreetgill/cisc327-a4:latest`
(https://hub.docker.com/r/manreetgill/cisc327-a4)

```bash
docker run --rm -p 5000:5000 manreetgill/cisc327-a4:latest
```

Note: data is held in memory, so it resets whenever the container restarts.