# Schedora

**Book trusted local services in seconds.**

Schedora is a full-stack appointment booking web application built with Flask, MySQL, and Jinja2. It connects clients with local service providers — doctors, salons, tutors, gyms, mechanics, and more — with real-time availability, secure booking, and a complete two-sided booking lifecycle.

---

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

## Two-factor authentication (demo mode)

2FA can be enabled per user from the Profile > Edit page. In demo mode, OTP codes are printed to the terminal instead of being sent by email. In production, the `send_otp_via_console` function in `app/utils/otp_send.py` would be replaced with an SMTP call.

---

## License

This project was built for academic coursework. All rights reserved.

---

## Author

Jewel Thapa