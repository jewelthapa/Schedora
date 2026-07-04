from flask import render_template

from app.auth import login_required


@login_required
def help_page():
    """Render the static help/FAQ page for logged-in users."""
    return render_template("help/help.html")