# Events Manager

A campus events platform where students can discover what's happening today, what's coming up, and what has already ended, and where organisers can post and manage their own events.

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (hosted on Supabase)
- **Frontend:** Python desktop/web UI built with [Flet]
- **Auth (planned):** Google OAuth with three roles: Student, Organiser, Admin

---

## Features

**Available now**

- Three dashboard menus with live counts: **Events Today**, **Upcoming Events**, **Expired Events**
- "Create new event" form with required-field validation and a dropdown of event types (Hackathon, Buildathon, Workshop, Conference, Seminar, Webinar, Guest Lectures, Concert, Others)
- Organiser registration, event/organiser editing and deletion through the REST API
- Unique 5-digit IDs generated for events and organisers
- Frontend auto-starts the backend (uvicorn) if it isn't already running

**Planned**

- Google OAuth sign-in (scrapped Microsoft Identity Platform)
- An **Accounts** section with role-based controls (see [below](#planned-google-oauth-and-accounts-section))

---

## Project Structure

```
events-manager/
├── backend.py             # FastAPI app: all REST endpoints
├── database_connector.py  # SQLAlchemy engine, session, and get_db dependency
├── database_schema.py     # ORM models: organisers, events
├── data_validator.py      # Pydantic request/response models
├── datetime_formatter.py  # Date/time parsing and display helpers
├── client_creator.py      # Supabase client smoke test
├── frontend.py            # Flet UI wired to the live API
├── events_dashboard.py    # Final UI design (target look and feel, sample data)
├── .env                   # Secrets (git-ignored)
├── credentials.txt        # Local notes (git-ignored)
└── .gitignore
```

| File | Purpose |
|------|---------|
| `backend.py` | Defines the FastAPI `app` and every endpoint. Includes `generate_unique_id()` which picks a random 5-digit ID (10000–99999) not already in the table, retrying up to 100 times. |
| `database_connector.py` | Builds a `postgresql+psycopg` URL from env vars, connects on port `6543` (Supabase transaction pooler) with `NullPool` and `prepare_threshold=None`, and exposes `get_db()` as a FastAPI dependency. |
| `database_schema.py` | `organisers` and `events` tables with a one-to-many relationship. |
| `data_validator.py` | `OrganisersCreate`, `OrganisersOut`, `EventIn`, `EventOut`, `EventUpdate`. Name and venue are capped at 100 characters. |
| `datetime_formatter.py` | `parse_date`, `pretty_time` (e.g. `02:30 PM`), `when_label`, `convert_to_date`, `convert_to_time`, `get_date`. |
| `client_creator.py` | Creates a Supabase client from `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` and prints whether it worked. |
| `frontend.py` | The working Flet app: fetches `/all_Events`, groups events client-side, and posts new events. |
| `events_dashboard.py` | The finished visual design for the dashboard (lilac and periwinkle theme, richer cards with description, action and Share buttons). Currently uses sample data via `fetch_events()`, which is meant to be replaced by calls to the FastAPI backend. |

---

## Architecture

```
┌──────────────────────┐    HTTP/JSON     ┌──────────────────┐    SQLAlchemy    ┌──────────────────────┐
│  Flet frontend       │ ───────────────▶ │  FastAPI backend │ ───────────────▶ │ PostgreSQL (Supabase)│
│  frontend.py         │ ◀─────────────── │  backend.py      │ ◀─────────────── │ organisers, events   │
│  events_dashboard.py │                  └──────────────────┘                  └──────────────────────┘
└──────────────────────┘
        │
        └── (planned) Google OAuth ─▶ identifies the user and their role
```

On launch, `frontend.py` pings `{API_URL}/docs`. If the API is unreachable it spawns `uvicorn backend:app --port 8000` as a subprocess and waits up to 30 seconds for it to come up. The subprocess is terminated on exit.

---

## Database Schema

### `organisers`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BigInteger | Primary key, generated in code (no autoincrement) |
| `organiser_name` | Text | Required |
| `email_id` | Text | Required, unique |

### `events`

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | BigInteger | Primary key, generated in code |
| `name` | VARCHAR(100) | Required |
| `description` | Text | Optional |
| `event_date` | Date | |
| `venue` | VARCHAR(100) | |
| `contacts` | Text | Required |
| `event_time` | Time | |
| `organiser_id` | BigInteger | Foreign key to `organisers.id`, required |
| `organiser` | Text | Organiser name (denormalised copy), required |
| `type` | Text | Required, e.g. Workshop or Hackathon |

---

## API Reference

Interactive docs are available at `http://localhost:8000/docs` once the backend is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/all_Events` | List every event |
| GET | `/Events_today` | Events dated today, sorted by time |
| GET | `/Expired_events` | Events dated before today |
| POST | `/Post_event` | Create an event. The `organiser` name must match a registered organiser (case-insensitive), otherwise `404`. |
| POST | `/Register_organiser` | Register a new organiser (`organiser_name`, `email_id`) |
| PUT | `/Edit_event?Event_id=` | Update an event |
| PUT | `/Edit_organiser_details?Organiser_id=` | Update an organiser |
| PUT | `/Delete_event?Event_id=` | Delete an event |
| PUT | `/Delete_organiser?Organiser_id=` | Delete an organiser |

---

## Frontend

`events_dashboard.py` is the **final interface design**; `frontend.py` is the version currently connected to the backenda and I am going to build `frontend.py` exactly like the interface of `events_dashboard.py` with addition to accounts section.

**Menus**

| Menu | Shows | Card action |
|------|-------|-------------|
| Events Today | Events dated today | View details |
| Upcoming Events | Events after today, soonest first | View details / Register |
| Expired Events | Past events, most recent first | View details / View recap |

Menu buttons show a live count badge and highlight the active selection.

---

## Planned: Google OAuth and Accounts Section

Users will sign in with Google. After sign-in, an **Accounts** section appears in the UI whose contents depend on the user's role.

### Roles

| Role | How it's determined (proposed) | Accounts section |
|------|-------------------------------|------------------|
| **Student** | Signed-in Google user whose email is not registered as an organiser or admin | **Manage my events** button is visible but disabled/not clickable |
| **Organiser** | Signed-in email matches an `organisers.email_id` | **Manage my events** is enabled: edit or delete only the events they own |
| **Admin** | Signed-in email is flagged as admin (see below) | Everything an organiser has, plus **add / remove organisers** and **add / remove events** |

### Suggested design

- **Token flow:** Flet completes the Google sign-in and sends the Google ID token to the backend as a `Bearer` token. The backend verifies it (for example with `google-auth`) and reads the verified email from it. Roles should be decided on the server, never trusted from the client.
- **Admin flag:** add a `role` column (`student` / `organiser` / `admin`) or an `admins` table so admin rights are explicit.
- **Ownership check:** on `Edit_event` and `Delete_event`, allow the action only if `events.organiser_id` matches the caller's organiser record, or the caller is an admin.
- **Admin-only endpoints:** `Register_organiser` and `Delete_organiser`, plus event deletion for any event.
- **UI:** hide or disable controls based on the role returned after login. This is for usability only; the backend enforces the real rules.
- **Manage my events:** a new view listing only the signed-in organiser's events (filter by `organiser_id`), with Edit and Delete buttons on each card.

---

## Getting Started

### Prerequisites

- Python 3.10+
- A Supabase project (Postgres database) with the `organisers` and `events` tables
- A Google Cloud OAuth client (only needed once auth is added)

### Install

```bash
git clone <your-repo-url>
cd events-manager

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" \
            pydantic python-dotenv requests supabase flet
```

### Configure

Create a `.env` file in the project root (see [Environment Variables](#environment-variables)).

### Run

Run everything (the frontend starts the backend for you):

```bash
python frontend.py
```

Or run the pieces separately:

```bash
# Terminal 1: API
uvicorn backend:app --port 8000 --reload

# Terminal 2: UI (desktop window)
python frontend.py

# UI in the browser instead
flet run --web frontend.py
```

Preview the finished design with sample data (no backend needed):

```bash
python events_dashboard.py
```

Verify the Supabase connection:

```bash
python client_creator.py
```

> On Flet versions older than 1.0, replace `ft.run(...)` with `ft.app(target=...)`.

---

## Environment Variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `API_URL` | `frontend.py` | Base URL of the backend, e.g. `http://127.0.0.1:8000` |
| `USER` | `database_connector.py` | Database username |
| `DATABASE_PASSWORD` | `database_connector.py` | Database password |
| `HOST` | `database_connector.py` | Database host (Supabase pooler host) |
| `SUPABASE_URL` | `client_creator.py` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `client_creator.py` | Supabase service-role key |