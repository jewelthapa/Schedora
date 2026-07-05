import secrets

from flask import Flask, session, request, g, render_template, abort

from config import Config


def create_app():
    app = Flask(__name__)

    # Load configuration (SECRET_KEY, MySQL creds, session settings) from Config
    app.config.from_object(Config)

    # Fail loudly if the secret key wasn't loaded from .env
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not set. Check your .env file.")

    # ----------------------------------------------------------------
    # BEFORE EACH REQUEST
    #   1. Make sure a CSRF token exists in the session.
    #   2. On POST/PUT/PATCH/DELETE, verify the submitted CSRF token.
    #   3. Load the current user (if logged in) onto Flask's `g` object.
    # ----------------------------------------------------------------
    @app.before_request
    def csrf_protect():
        # Ensure every session has a CSRF token
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)

        # Only state-changing methods need CSRF verification
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = session.get("csrf_token")
            form_token = request.form.get("csrf_token")
            if not token or token != form_token:
                abort(403)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.current_user = None
        else:
            # Minimal user info kept in the session; richer lookups happen
            # in repository helpers once those exist.
            g.current_user = {
                "id": user_id,
                "name": session.get("user_name"),
                "role": session.get("user_role"),
            }

    # ----------------------------------------------------------------
    # CONTEXT PROCESSOR
    #   Makes `current_user` and `csrf_token` available in every template
    #   without passing them in manually each render.
    # ----------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        unread = 0
        cu = g.get("current_user")
        if cu is not None:
            # Import here to avoid circular import at app startup
            from app.repository import notification_repo
            unread = notification_repo.count_unread(cu["id"])
        return {
            "current_user": cu,
            "csrf_token": session.get("csrf_token"),
            "unread_notifications": unread,
        }

    # ----------------------------------------------------------------
    # ROUTES (temporary home route until we move it into a blueprint)
    # ----------------------------------------------------------------
    @app.route("/")
    def home():
        return render_template("home.html")

    # ----------------------------------------------------------------
    # BLUEPRINTS
    #   Registered here as we build each feature. Commented out until
    #   the matching routes file exists, so the app still boots.
    # ----------------------------------------------------------------
    from app.routes.authRoutes import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.dashboardRoutes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.routes.notificationRoutes import notification_bp
    app.register_blueprint(notification_bp)

    from app.routes.profileRoutes import profile_bp
    app.register_blueprint(profile_bp)

    from app.routes.helpRoutes import help_bp
    app.register_blueprint(help_bp)

    from app.routes.serviceRoutes import service_bp
    app.register_blueprint(service_bp)

    from app.routes.slotRoutes import slot_bp
    app.register_blueprint(slot_bp)

    from app.routes.browseRoutes import browse_bp
    app.register_blueprint(browse_bp)

    # ----------------------------------------------------------------
    # ERROR HANDLERS
    # ----------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app