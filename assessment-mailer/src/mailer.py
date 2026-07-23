import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
import role_classifier
import templates

# (subject, body_fn, pdf_path). pdf_path is None for roles whose assessment
# is a link/document rather than an attached file (AI Native video task).
_ROLE_TO_TEMPLATE = {
    role_classifier.QA: (templates.QA_SUBJECT, templates.qa_body, config.QA_ASSESSMENT_PDF),
    role_classifier.FULLSTACK: (templates.FULLSTACK_SUBJECT, templates.fullstack_body, config.FULLSTACK_ASSESSMENT_PDF),
    role_classifier.GRAPHIC: (templates.GRAPHIC_SUBJECT, templates.graphic_body, config.GRAPHIC_ASSESSMENT_PDF),
    role_classifier.RECRUITER: (templates.RECRUITER_SUBJECT, templates.recruiter_body, config.RECRUITER_ASSESSMENT_PDF),
    role_classifier.AI_NATIVE: (templates.AI_NATIVE_SUBJECT, templates.ai_native_body, None),
}


def send_assessment_email(to_email, candidate_name, role):
    subject, body_fn, pdf_path = _ROLE_TO_TEMPLATE[role]

    message = MIMEMultipart()
    message["From"] = config.SEND_GMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(templates.with_terms(body_fn(candidate_name)), "plain"))

    if pdf_path is not None:
        with open(pdf_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
        message.attach(attachment)

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.login(config.SEND_GMAIL_ADDRESS, config.SEND_GMAIL_APP_PASSWORD)
        smtp.sendmail(config.SEND_GMAIL_ADDRESS, [to_email], message.as_string())
