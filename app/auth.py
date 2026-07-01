"""
Access-control decorators for protected routes.

- login_required: forces the user to be logged in
- role_required("client" | "provider"): forces a specific role

Both work by inspecting the current session (via g.current_user, which
the before_request hook in __init__.py already populates).
"""

from functools import wraps

from flask import g, flash, redirect, url_for, abort


def login_required(view_func):
    """Redirect to /auth/login if the user isn't logged in."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if g.get("current_user") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def role_required(role):
    """Ensure the logged-in user has the given role, else 403.

    Usage:
        @role_required("provider")
        def some_provider_only_view(): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = g.get("current_user")
            if user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if user.get("role") != role:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator