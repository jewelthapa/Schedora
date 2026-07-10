# Schedora

**Book trusted local services in seconds.**

Schedora is a full-stack appointment booking web application built with Flask, MySQL, and Jinja2. It connects clients with local service providers such as doctors, salons, tutors, gyms, mechanics, and photographers. Clients get real-time availability and can lock in a time in seconds, while providers get a simple way to list services, manage slots, and respond to booking requests.

---

## Features

### For clients
* Browse and search services by category
* View provider details and available time slots
* Book appointments in seconds
* Manage bookings (view, cancel)
* Save favourite providers
* Leave reviews after completed appointments
* Get QR-code booking tickets for accepted bookings

### For providers
* List and manage services with categories and pricing
* Open time slots with overlap prevention
* Accept or reject incoming booking requests
* View reviews received with average rating
* Real-time booking notifications

### Security and auth
* Password hashing with `scrypt` (Werkzeug)
* CSRF protection on all state-changing routes
* Session expiry with a 30-minute sliding timeout
* Account lockout after 5 failed login attempts (15-minute cooldown)
* Two-factor authentication using an email OTP (opt-in)
* Role-based access control (client or provider)
* IDOR protection on all ownership-sensitive operations

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

* Python 3.13 or newer
* MySQL 8 or newer, running on port 3306
* pip and virtualenv
* Git

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

The app runs at `http://127.0.0.1:5001`.

---

## Environment variables

Create a `.env` file in the project root with the following format. Do not commit this file.
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

Test accounts and their passwords will be provided separately for grading and demonstration.

The database also seeds about 45 additional provider accounts so the browse view has realistic content. These seeded accounts cannot be logged into because their password hashes are placeholders. They exist only to populate the listings.

---

## Security highlights

Schedora uses several overlapping security measures.

### Authentication
* Cryptographic password hashing with Werkzeug's `scrypt`, using a per-user salt so identical passwords produce different stored hashes.
* Account lockout after 5 failed login attempts, with a 15-minute cooldown.
* Enumeration protection. Nonexistent emails and wrong passwords return identical error messages so an attacker cannot harvest valid accounts.
* Two-factor authentication using time-limited email OTPs. Codes are 6 digits, expire in 5 minutes, are single-use, and are generated with Python's `secrets` module for cryptographic randomness.
* OTP brute-force protection. Codes are invalidated after 3 wrong attempts.

### Session security
* Server-side sessions with cryptographic signing (Flask's built-in session store).
* Sliding session expiry. Sessions time out after 30 minutes of inactivity.
* Session invalidation on logout via `session.clear()`.
* Users doing 2FA login sit in a temporary "pending" state (a `pending_user_id` in the session) between password and OTP steps. This means an unfinished login cannot reach any protected page.

### Request-level security
* CSRF protection. Every state-changing form carries a per-session token that is verified on the server.
* Parameterized SQL queries everywhere. Since values never get concatenated into SQL strings, injection attacks are prevented at the driver level.
* Role-based access control. Every controller uses `@login_required` and `@role_required(...)` decorators.

### Data integrity
* Atomic transactions for multi-step operations. For example, creating a booking inserts the booking and marks the slot as booked in the same transaction, rolling back if either fails.
* Ownership checks on all edit and delete routes. Users can only modify resources they own, which prevents Insecure Direct Object Reference (IDOR) attacks.
* Whitelist validation on constrained inputs (categories, roles, statuses). Invalid values are rejected before reaching the database.
* Optimistic locking on slot booking. The `is_booked` flag is checked before insert to prevent double-booking race conditions.

---

## Two-factor authentication (demo mode)

2FA is opt-in and can be turned on from the Profile then Edit page. In demo mode, the OTP is printed to the terminal instead of being emailed. Swapping to real email delivery is a matter of replacing the `send_otp_via_console` function in `app/utils/otp_send.py` with an SMTP call.

---

## License

Built for academic coursework. All rights reserved.

---

## Author

Jewel Thapa