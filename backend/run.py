import os

from dotenv import load_dotenv

load_dotenv()  # read backend/.env before Config is imported

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # Say which database this run uses (password hidden). A DATABASE_URL exported in the terminal
    # wins over backend/.env, so this is the quick way to spot "I'm still on the local DB".
    from sqlalchemy.engine import make_url

    db_url = make_url(app.config["SQLALCHEMY_DATABASE_URI"]).render_as_string(hide_password=True)
    print(f" * Database: {db_url}")

    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
