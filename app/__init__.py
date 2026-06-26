from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    # Temporary route so we can preview the home page.
    # Tomorrow this moves into a proper blueprint/controller.
    @app.route("/")
    def home():
        return render_template("home.html")

    return app