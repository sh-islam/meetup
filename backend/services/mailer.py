"""
One send() for every email. When SMTP is not configured the message is only appended to
MAIL_LOG, so the whole app can be tested without a mail account. Every send is also
recorded in email_log. Swap _deliver() to move to another transport later.
"""
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from flask import render_template

import config
from db import get_db, now_iso


def send(kind, to_email, subject, ctx, meetup_id=None, participant_id=None, attachments=None):
    """
    kind: template name under templates/email/ (kind.txt and kind.html).
    attachments: list of (filename, mimetype, bytes).
    Returns 'sent' | 'logged' | 'failed'.
    """
    if not subject.startswith("Meetup: "):
        subject = "Meetup: " + subject
    ctx = dict(ctx, subject=subject)
    text = render_template(f"email/{kind}.txt", **ctx)
    html = render_template(f"email/{kind}.html", **ctx)

    _append_log(kind, to_email, subject, text)

    status, error = "logged", None
    if config.mail_configured():
        try:
            _deliver(to_email, subject, text, html, attachments or [])
            status = "sent"
        except Exception as exc:  # noqa: BLE001
            status, error = "failed", str(exc)[:500]

    db = get_db()
    db.execute(
        "INSERT INTO email_log (meetup_id, participant_id, kind, to_email, subject, status, error, sent_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (meetup_id, participant_id, kind, to_email, subject, status, error, now_iso()),
    )
    db.commit()
    return status


def _deliver(to_email, subject, text, html, attachments):
    msg = EmailMessage()
    msg["From"] = formataddr((config.MAIL_FROM_NAME, config.MAIL_FROM))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    for filename, mimetype, data in attachments:
        maintype, subtype = mimetype.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(config.SMTP_USER, config.SMTP_PASS)
        smtp.send_message(msg)


def _append_log(kind, to_email, subject, text):
    try:
        with open(config.MAIL_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n===== {now_iso()}  kind={kind}  to={to_email}\nSubject: {subject}\n\n{text}\n")
    except OSError:
        pass
