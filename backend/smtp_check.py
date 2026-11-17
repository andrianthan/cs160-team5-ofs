"""Check the SMTP settings in backend/.env before relying on order emails.

    python smtp_check.py                                   # connect and log in only (sends nothing)
    python smtp_check.py you@mail.com                      # send the built-in test email
    python smtp_check.py you@mail.com --subject "..." --body-file note.md

Exits non-zero with a readable message when the settings are wrong, so it works as a
pre-flight check before a demo.
"""
import argparse
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from app.config import Config  # noqa: E402  (reads the environment, so import after load_dotenv)
from app.notifications import _login  # noqa: E402  (the same AUTH the app uses, so both report the same error)

DEFAULT_SUBJECT = "Basil SMTP test"
DEFAULT_BODY = "If you can read this, Basil can send order emails."


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("to", nargs="?", help="address to send the email to")
    p.add_argument("--subject", default=DEFAULT_SUBJECT, help="message subject")
    p.add_argument("--body", help="message body as a string")
    p.add_argument("--body-file", help="file whose text is used as the message body")
    return p.parse_args()


def main():
    args = parse_args()
    missing = [k for k in ("SMTP_HOST", "SMTP_FROM") if not getattr(Config, k)]
    if missing:
        sys.exit(f"Missing in backend/.env: {', '.join(missing)}. See README / .env.example.")

    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text()
    if body is None:
        body = DEFAULT_BODY

    print(f"Connecting to {Config.SMTP_HOST}:{Config.SMTP_PORT} (STARTTLS={'on' if Config.SMTP_STARTTLS else 'off'}) ...")
    print(f"  user: {Config.SMTP_USERNAME or '(none)'}    from: {Config.SMTP_FROM}")
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=Config.SMTP_TIMEOUT_S) as server:
            if Config.SMTP_STARTTLS:
                server.starttls()
            if Config.SMTP_USERNAME:
                _login(server, Config.SMTP_USERNAME, Config.SMTP_PASSWORD or "")
                print("Login OK.")
            else:
                print("No SMTP_USERNAME set; skipping login.")
            if args.to:
                msg = EmailMessage()
                msg["From"], msg["To"], msg["Subject"] = Config.SMTP_FROM, args.to, args.subject
                msg.set_content(body)
                server.send_message(msg)
                print(f"Email sent to {args.to}. Check the inbox (and spam).")
            else:
                print("Nothing sent. Pass an address to send a test email.")
    except (smtplib.SMTPException, OSError) as exc:
        sys.exit(f"SMTP check failed: {exc}")


if __name__ == "__main__":
    main()
