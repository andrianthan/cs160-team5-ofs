"""Put the SMTP credentials into backend/.env, then check they work.

    python set_smtp_credentials.py
    python set_smtp_credentials.py you@gmail.com      # address on the command line
    python set_smtp_credentials.py you@gmail.com --check-only

The app password is read without echoing it and is never printed. A backup of the old
.env is written next to it first. The Gmail address must be the one the app password
belongs to: https://myaccount.google.com/apppasswords (needs 2-Step Verification on).
"""
import argparse
import getpass
import shutil
import sys
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"

# Written when the key is missing. Everything else in the file is left alone.
DEFAULTS = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_STARTTLS": "1",
}


def read_env(path):
    lines = path.read_text().splitlines() if path.exists() else []
    values, seen = {}, set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key not in values:
            values[key] = stripped.split("=", 1)[1]
            seen.add(key)
    return lines, values, seen


def write_env(path, lines, updates):
    """Replace the value of each key in place; append anything that wasn't there."""
    out = []
    written = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                written.add(key)
                continue
        out.append(line)
    for key, value in updates.items():
        if key not in written:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email", nargs="?", help="the Gmail address to send from")
    parser.add_argument("--check-only", action="store_true", help="test the current .env without changing it")
    args = parser.parse_args()

    if not ENV_PATH.exists():
        sys.exit(f"{ENV_PATH} not found. Run this from the backend/ directory.")

    if args.check_only:
        return run_check()

    email = args.email or input("Gmail address to send from: ").strip()
    if not email or "@" not in email:
        sys.exit("That does not look like an email address.")

    if not args.email:
        print("\nThe app password is the 16-character one from "
              "https://myaccount.google.com/apppasswords\n", flush=True)
    password = getpass.getpass("App password (input is hidden): ").strip()
    if not password:
        sys.exit("No password entered.")
    if password.startswith("REPLACE") or password == "...":
        sys.exit("That is still the placeholder. Paste the real 16-character app password.")

    lines, values, _ = read_env(ENV_PATH)
    updates = {
        "SMTP_USERNAME": email,
        "SMTP_PASSWORD": password,
        "SMTP_FROM": f"Basil <{email}>",
    }
    for key, value in DEFAULTS.items():
        if key not in values:
            updates[key] = value

    backup = ENV_PATH.parent / (ENV_PATH.name + ".bak")
    shutil.copy2(ENV_PATH, backup)
    write_env(ENV_PATH, lines, updates)

    print(f"\nWrote SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM to {ENV_PATH.name}")
    print(f"Backup of the previous file: {backup.name}")
    print(f"Sending address: {email}")
    print("Password: not shown.\n")

    return run_check()


def run_check():
    """Try the credentials for real: connect, log in, and send one email."""
    import smtplib
    from email.message import EmailMessage

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from dotenv import load_dotenv

    load_dotenv(ENV_PATH)
    from app.config import Config  # noqa: E402
    from app.notifications import _login  # noqa: E402

    if not Config.SMTP_HOST or not Config.SMTP_USERNAME:
        sys.exit("SMTP_HOST or SMTP_USERNAME is still missing from backend/.env")

    print(f"Connecting to {Config.SMTP_HOST}:{Config.SMTP_PORT} ...")
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=Config.SMTP_TIMEOUT_S) as server:
            if Config.SMTP_STARTTLS:
                server.starttls()
            _login(server, Config.SMTP_USERNAME, Config.SMTP_PASSWORD or "")
            print("Login OK.")
            to = Config.SMTP_USERNAME
            msg = EmailMessage()
            msg["From"], msg["To"], msg["Subject"] = Config.SMTP_FROM, to, "Basil SMTP test"
            msg.set_content("If you can read this, Basil can send order emails.")
            server.send_message(msg)
            print(f"Sent a test email to {to}. Check the inbox (and spam).")
    except smtplib.SMTPAuthenticationError as exc:
        sys.exit(f"Login rejected by the server: {exc.smtp_code} {exc.smtp_error!r}\n"
                 "That is the address or the app password being wrong. Note that a Google\n"
                 "account password will not work here — it has to be an app password.")
    except (smtplib.SMTPException, OSError) as exc:
        sys.exit(f"SMTP check failed: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
