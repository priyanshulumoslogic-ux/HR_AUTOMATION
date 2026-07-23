import config

QA_SUBJECT = "QA Intern Technical Assessment - Lumos Logic"
FULLSTACK_SUBJECT = "Full Stack Intern Technical Assessment - Lumos Logic"
GRAPHIC_SUBJECT = "Graphic Designer Assessment - Lumos Logic"
RECRUITER_SUBJECT = "Recruiter Intern Assessment - Lumos Logic"
AI_NATIVE_SUBJECT = "AI Native Internship - Video Assessment | LumosLogic"


def with_terms(body):
    """Every assessment email leads with the internship terms, then the
    role-specific body below a divider."""
    return f"{config.TERMS_MESSAGE}\n\n---\n\n{body}"


def qa_body(name):
    return f"""Hello {name},

Thank you for applying for the QA Intern position at Lumos Logic.

We're pleased to move you to the next stage of our hiring process. As part of the evaluation, we'd like you to complete the attached Technical Assessment.

Assessment Details:

- Role: QA Intern
- Duration: 2 Days
- Submission Deadline: Please submit your completed assessment within 2 days of receiving this email.

The assessment includes:

- Manual Testing
- Test Case Creation
- Bug Reporting
- Exploratory Testing
- Basic SQL Assessment
- API Testing (Bonus)
- Test Summary Report

Once you have completed the assessment, kindly upload your submission using the Google Form below:

Submission Form:
{config.ASSESSMENT_FORM_URL}

Submission Checklist:

- QA_Test_Assessment.xlsx (All required sheets)
- SQL Assessment (PDF/DOCX)
- Postman Collection (Optional)
- Screenshots of Bugs (if applicable)
- Any additional supporting files

If you have any questions regarding the assessment, feel free to reply to this email.

We wish you the very best and look forward to reviewing your submission.

{config.SIGNATURE}
"""


def fullstack_body(name):
    return f"""Hi {name},

Thank you for applying for the Full Stack Intern position at Lumos Logic.

We're excited to move you to the next stage of our hiring process. As part of the evaluation, we'd like you to complete the assigned technical assessment.

Assessment Details

- Role: Full Stack Intern
- Duration: 2 Days
- Deadline: Please submit your assessment within 2 days of receiving this email.

Once you have completed the assessment, kindly fill out the submission form below and upload all the required details:

Assessment Submission Form:
{config.ASSESSMENT_FORM_URL}

Please ensure that:

- Your project is complete and functional.
- Any GitHub repository or deployment link is accessible.
- All requested information is submitted through the form before the deadline.

If you have any questions regarding the assessment, feel free to reply to this email.

We look forward to reviewing your work.

{config.SIGNATURE}
"""


def _generic_assessment_body(name, role_name):
    """Same Full-Stack-style format, reused for roles whose assessment is an
    attached task (Graphic Designer, Recruiter Intern)."""
    return f"""Hi {name},

Thank you for applying for the {role_name} position at Lumos Logic.

We're excited to move you to the next stage of our hiring process. As part of the evaluation, we'd like you to complete the attached assessment.

Assessment Details

- Role: {role_name}
- Duration: 2 Days
- Deadline: Please submit your assessment within 2 days of receiving this email.

Once you have completed the assessment, kindly fill out the submission form below and upload all the required details:

Assessment Submission Form:
{config.ASSESSMENT_FORM_URL}

Please ensure that:

- Your submission is complete.
- Any links you share (files, portfolio, or documents) are accessible.
- All requested information is submitted through the form before the deadline.

If you have any questions regarding the assessment, feel free to reply to this email.

We look forward to reviewing your work.

{config.SIGNATURE}
"""


def graphic_body(name):
    return _generic_assessment_body(name, "Graphic Designer")


def recruiter_body(name):
    return _generic_assessment_body(name, "Recruiter Intern")


def ai_native_body(name):
    return f"""Hi {name},

Thank you for applying for the AI Native Digital Marketing & Growth Intern (3-Month Internship) / AI Native Sales & Business Development Intern (3-Month Internship) position at LumosLogic.

As the next step in our selection process, we'd like you to complete a video assessment. This task will help us better understand your communication skills, thinking process, creativity, and overall fit for the role.

Video Assessment Instructions:
Please review the task details here:
{config.AI_NATIVE_DOC_URL}

Submission Guidelines:

- Record your responses as instructed in the document.
- Upload the video to Google Drive (or any cloud storage) and make it accessible.
- Once your video is ready, please submit your details and the video link using the form below:

{config.ASSESSMENT_FORM_URL}

If you have any questions regarding the assessment, feel free to reply to this email.

We look forward to reviewing your submission.

{config.SIGNATURE}
"""
