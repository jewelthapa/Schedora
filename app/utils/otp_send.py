"""OTP delivery. For dev/coursework: prints to console.
Swap for Flask-Mail SMTP in production."""

def send_otp_via_console(email, code):
    """Print the OTP to the terminal for dev use.

    In a real deployment this would be an SMTP send.
    Kept simple for coursework — the console output is
    the 'email' the user 'receives'."""
    print("=" * 60)
    print(f"[OTP EMAIL SIMULATION]")
    print(f"To: {email}")
    print(f"Your Schedora verification code is: {code}")
    print(f"This code expires in 5 minutes.")
    print("=" * 60)