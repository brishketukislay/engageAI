from flask import render_template


# VIEW ROUTES (HTML PAGES)

def register_view_routes(app):

    # MAIN DASHBOARD

    @app.route("/")
    def index():

        return render_template("index.html")

    # FUTURE PAGES (placeholders)

    @app.route("/about")
    def about():

        return render_template("index.html")