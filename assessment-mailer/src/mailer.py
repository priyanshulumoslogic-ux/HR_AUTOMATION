import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
import role_classifier
import templates

# body_fn only; the subject line is now always derived from the candidate's
# original email ("Re: <their subject>") so the reply threads naturally,
# rather than a fixed subject of our own.
_ROLE_TO_TEMPLATE = {
    role_classifier.QA: (templates.qa_body, config.QA_ASSESSMENT_PDF),
    role_classifier.FULLSTACK: (templates.fullstack_body, config.FULLSTACK_ASSESSMENT_PDF),
    role_classifier.GRAPHIC: (templates.graphic_body, config.GRAPHIC_ASSESSMENT_PDF),
    role_classifier.RECRUITER: (templates.recruiter_body, config.RECRUITER_ASSESSMENT_PDF),
    role_classifier.AI_NATIVE: (templates.ai_native_body, None),
    role_classifier.MOBILE: (templates.mobile_body, None),
    role_classifier.FDE: (templates.fde_body, config.FDE_ASSESSMENT_PDF),
    role_classifier.PRODUCT_ENGINEER: (templates.product_engineer_body, config.PRODUCT_ENGINEER_ASSESSMENT_PDF),
}


def _reply_subject(original_subject):
    if original_subject.strip().lower().startswith("re:"):
        return original_subject
    return f"Re: {original_subject}"


def send_assessment_email(to_email, candidate_name, role, original_message_id, original_references, original_subject,
                           send_address, send_app_password):
    """Sends the reply from send_address/send_app_password - each candidate
    carries its own mailbox's send credentials (see gmail_reader.py), since
    different application inboxes can reply from different addresses (e.g.
    a self-contained mailbox replies from itself rather than the shared HR
    sender)."""
    body_fn, pdf_path = _ROLE_TO_TEMPLATE[role]

    message = MIMEMultipart()
    message["From"] = send_address
    message["To"] = to_email
    message["Subject"] = _reply_subject(original_subject)

    # A synthetic "nomsgid:..." key (see gmail_reader._message_id_for) isn't
    # a real Message-ID and can't be used to thread a reply - only set these
    # headers when the candidate's email actually had one.
    if not original_message_id.startswith("nomsgid:"):
        message["In-Reply-To"] = original_message_id
        message["References"] = f"{original_references} {original_message_id}".strip()

    message.attach(MIMEText(templates.with_terms(body_fn(candidate_name)), "plain"))

    if pdf_path is not None:
        with open(pdf_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
        message.attach(attachment)

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.login(send_address, send_app_password)
        smtp.sendmail(send_address, [to_email], message.as_string())


def send_followup_email(to_email, candidate_name, original_message_id, original_references, original_subject,
                         send_address, send_app_password, pdf_path):
    """One-off follow-up reply (see templates.fde_followup_body) threaded
    into the same original application email as the initial assessment
    reply, so it lands in the same Gmail thread."""
    message = MIMEMultipart()
    message["From"] = send_address
    message["To"] = to_email
    message["Subject"] = _reply_subject(original_subject)

    if not original_message_id.startswith("nomsgid:"):
        message["In-Reply-To"] = original_message_id
        message["References"] = f"{original_references} {original_message_id}".strip()

    message.attach(MIMEText(templates.fde_followup_body(candidate_name), "plain"))

    with open(pdf_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
    message.attach(attachment)

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.login(send_address, send_app_password)
        smtp.sendmail(send_address, [to_email], message.as_string())
