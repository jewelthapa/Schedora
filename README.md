# Schedora

**Book trusted local services in seconds.**

Schedora is a full-stack appointment booking web application built with Flask, MySQL, and Jinja2. It connects clients with local service providers — doctors, salons, tutors, gyms, mechanics, and more — with real-time availability, secure booking, and a complete two-sided booking lifecycle.

---

---

## Screenshots

<!-- Add screenshots here before submission. Suggested screens: -->
<!-- 1. Landing page / hero -->
<!-- 2. Login (light + dark mode) -->
<!-- 3. Client dashboard -->
<!-- 4. Browse services with category filters -->
<!-- 5. Service detail with slots -->
<!-- 6. Booking confirmation -->
<!-- 7. Provider Bookings (Accept/Reject) -->
<!-- 8. QR ticket -->
<!-- 9. Reviews page -->
<!-- 10. 2FA OTP entry -->

*Screenshots will be added during final documentation pass.*

## Features

### For clients
- Browse and search services by category
- View provider details and available time slots
- Book appointments in seconds
- Manage bookings (view, cancel)
- Save favorite providers
- Leave reviews after completed appointments
- Get QR-code booking tickets for accepted bookings

### For providers
- List and manage services with categories and pricing
- Open time slots with overlap prevention
- Accept or reject incoming booking requests
- View reviews received with average rating
- Real-time booking notifications

### Security & Auth
- Password hashing with `scrypt` (Werkzeug)
- CSRF protection on all state-changing routes
- Session expiry (30-minute sliding timeout)
- Account lockout after 5 failed login attempts (15-minute cooldown)
- Two-factor authentication (email OTP, opt-in)
- Role-based access control (client / provider)
- IDOR protection on all ownership-sensitive operations

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.13, Flask |
| Database | MySQL 8 (via PyMySQL) |
| Templates | Jinja2 |
| Frontend | HTML5, CSS3 (custom design system), vanilla JavaScript |
| Auth | Werkzeug scrypt, Flask sessions |
| QR codes | `qrcode` (Pillow backend) |
| Config | `python-dotenv` for environment variables |

---

## Prerequisites

- Python 3.13+
- MySQL 8+ (running on port 3306)
- pip and virtualenv
- Git

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/jewelthapa/Schedora.git
cd Schedora

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up the database
mysql -u root -p < schema.sql

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your MySQL credentials and a SECRET_KEY

# 6. Run the app
python3 run.py
```

The app will be available at `http://127.0.0.1:5001`.

---

## Environment variables

Create a `.env` file in the project root with the following format (do not commit this file):

SECRET_KEY=your-secret-key-here
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_NAME=schedora
Generate a secure `SECRET_KEY` with:

```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Test credentials

Test accounts and their passwords will be provided separately during grading and demonstration.

The database seeds ~45 additional provider accounts for realistic browsing. These seeded accounts cannot be logged into (their password hashes are placeholders); they exist only to populate the Browse view.

---

## Project structure

Schedora follows a layered MVC-style architecture with clear separation between routes, controllers, repositories, and templates.

Schedora/
├── run.py                       # Application entry point
├── config.py                    # Configuration loader (reads .env)
├── schema.sql                   # Database schema (all tables + relationships)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
├── README.md
│
└── app/
├── init.py              # Flask app factory (create_app)
├── auth.py                  # login_required + role_required decorators
├── database.py              # PyMySQL connection helper
│
├── controllers/             # Request handlers (business logic)
│   ├── authController.py         # Register, login, logout, OTP
│   ├── dashboardController.py    # Role-aware dashboards
│   ├── profileController.py      # View + edit profile
│   ├── notificationController.py # CRUD for notifications
│   ├── serviceController.py      # Provider services CRUD
│   ├── slotController.py         # Provider time slots CRUD
│   ├── browseController.py       # Browse + service detail
│   ├── bookingController.py      # Client bookings + QR ticket
│   ├── incomingBookingController.py # Provider accept/reject
│   ├── reviewController.py       # Reviews
│   ├── favoriteController.py     # Favorites
│   └── helpController.py         # Static help page
│
├── routes/                  # URL to controller wiring
│   └── *Routes.py           # One file per feature blueprint
│
├── repository/              # DB access layer
│   ├── otp_repo.py               # OTP generation + verification
│   ├── notification_repo.py      # Notification helpers
│   ├── user_repo.py
│   └── booking_repo.py
│
├── utils/                   # Utility modules
│   └── otp_send.py               # OTP delivery (console for demo)
│
├── templates/               # Jinja2 templates
│   ├── base.html
│   ├── dash_base.html
│   ├── home.html
│   ├── auth/                     # Login, register, OTP entry
│   ├── dashboard/                # Client + provider dashboards
│   ├── profile/                  # View + edit
│   ├── notifications/            # Notification list
│   ├── services/                 # My services + form
│   ├── slots/                    # Availability + form
│   ├── browse/                   # Browse + service detail
│   ├── bookings/                 # Booking flows + ticket
│   ├── reviews/                  # Create + provider view
│   ├── favorites/                # Saved providers
│   ├── help/                     # FAQ
│   ├── partials/                 # Nav
│   └── errors/                   # 403 / 404 / 500
│
└── static/
├── css/style.css        # Custom design system
└── js/main.js           # Theme toggle + sidebar collapse

### Architecture overview

- **`run.py`** boots the Flask app using the factory pattern from `app/__init__.py`.
- **`__init__.py`** wires up sessions, CSRF, blueprint registration, and context processors (e.g. injecting `current_user` and unread notification count into every template).
- **Blueprints** in `app/routes/` register URL patterns and map them to controller functions. Each feature gets its own blueprint (e.g. `booking_bp`, `review_bp`) for clean separation.
- **Controllers** in `app/controllers/` contain the request/response logic — validation, session handling, redirects, flash messages.
- **Repositories** in `app/repository/` handle direct database access with parameterized queries. Reusable helpers keep controllers thin.
- **Templates** extend two base layouts: `base.html` (public pages) and `dash_base.html` (logged-in dashboard shell with sidebar and role-aware navigation).

### Database schema

Eight main tables with proper foreign key relationships and cascading deletes:

- **users** — accounts (client or provider role), auth fields, 2FA toggle, lockout counters
- **services** — provider service listings with category and price
- **time_slots** — provider availability with overlap prevention
- **bookings** — client-to-provider bookings with status lifecycle (pending → accepted/rejected/cancelled/completed)
- **reviews** — one review per booking, 1–5 star rating with optional comment
- **favorites** — clients save providers (unique constraint prevents duplicates)
- **notifications** — cross-user notifications from booking events
- **otp_codes** — time-limited codes for 2FA verification

All destructive operations use `ON DELETE CASCADE` so removing a user cleanly removes their related data.

---

## Security highlights

Schedora implements defense-in-depth across multiple layers:

### Authentication
- **Cryptographic password hashing** with Werkzeug's `scrypt` (per-user salt, computationally expensive to brute-force)
- **Account lockout** after 5 failed login attempts, with a 15-minute cooldown
- **Enumeration protection** — nonexistent emails and wrong passwords return identical error messages, preventing attackers from harvesting valid accounts
- **Two-factor authentication** via time-limited email OTP (6 digits, 5-minute expiry, single-use, cryptographically random via Python's `secrets` module)
- **OTP brute-force protection** — codes are invalidated after 3 wrong attempts

### Session security
- **Server-side sessions** with cryptographic signing (Flask's built-in session store)
- **Sliding session expiry** — sessions expire after 30 minutes of inactivity
- **Session invalidation** on logout via `session.clear()`
- **Pending vs. authenticated states** — 2FA users have `pending_user_id` between password entry and OTP verification, not `user_id`, so unfinished logins can't access protected pages

### Request-level security
- **CSRF protection** — every state-changing form includes a per-session token, verified server-side
- **Parameterized SQL queries** everywhere — no string concatenation, so SQL injection is prevented at the driver level
- **Role-based access control** via `@login_required` and `@role_required(...)` decorators on every controller

### Data integrity
- **Atomic transactions** for multi-step operations (e.g. booking creation locks the slot in the same transaction, rollback on failure)
- **Ownership checks** on all edit/delete operations — users can only modify their own resources (prevents Insecure Direct Object Reference attacks)
- **Whitelist validation** on constrained inputs (categories, roles, status values) — invalid values are rejected before hitting the database
- **Optimistic locking** on slot booking — checks `is_booked` before insert to prevent double-booking race conditions

## Two-factor authentication (demo mode)

2FA can be enabled per user from the Profile > Edit page. In demo mode, OTP codes are printed to the terminal instead of being sent by email. In production, the `send_otp_via_console` function in `app/utils/otp_send.py` would be replaced with an SMTP call.

---

## License

This project was built for academic coursework. All rights reserved.

---

## Author

Jewel Thapa