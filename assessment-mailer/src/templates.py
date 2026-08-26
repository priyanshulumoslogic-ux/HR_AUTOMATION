import config


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


def mobile_body(name):
    """No attached task for this role - just move-to-next-stage plus the
    shared submission form, unlike the other role bodies above."""
    return f"""Hi {name},

Thank you for applying for the Mobile Application Intern position at Lumos Logic.

We're excited to move you to the next stage of our hiring process.

Kindly fill out the submission form below with your details:

Submission Form:
{config.ASSESSMENT_FORM_URL}

If you have any questions, feel free to reply to this email.

We look forward to hearing from you.

{config.SIGNATURE}
"""


def _fde_style_body(name, role_name):
    """Shared assessment body for Forward Deployed Engineer and Product
    Engineer - same task, same format, only the role name differs."""
    return f"""Hi {name},

Thank you for applying for the {role_name} position at LumosLogic.

As the next step in our selection process, we'd like you to complete a technical assessment. This task will help us evaluate your technical problem-solving, product understanding, API/integration skills, ability to work with real-world requirements, and approach to building practical and scalable solutions.

Technical Assessment Instructions

Please review the complete task details and requirements provided in the assignment document.

Reference Application:
Daily Planner / To-Do List – Google Play

Key Requirements

- Focus on building a practical MVP based on the provided product requirements.
- You are expected to think from both a technical and customer/product perspective.
- Consider how the solution can be configured or adapted based on different customer requirements.
- Design and work with APIs, integrations, data, and backend services where required.
- Use Supabase or a suitable alternative rather than building the backend from scratch.
- You are encouraged to use AI tools efficiently during development.
- The solution should be scalable, maintainable, and well understood by you.
- Focus on solving the core problem rather than implementing unnecessary features.

Submission Guidelines

- Complete the assignment within 2 days of receiving it.
- If you need additional time, please communicate this in advance.
- Please share a brief progress update every day, including:
  - What you completed
  - What you are currently working on
  - Any blockers or challenges
  - What you plan to complete next

Once completed, please send your submission to:
hello@lumoslogic.com

Please include, as applicable:

- Working application / prototype
- Source code repository
- Technical documentation
- Architecture/design
- API and integration details
- Database/schema design
- Deployment/setup instructions
- Key assumptions and technical decisions
- Any limitations or future improvements

The application does not need to be fully production-ready. We are primarily interested in your problem-solving approach, technical implementation, integration thinking, ability to handle real-world requirements, scalability, and communication of technical decisions.

If you have any questions regarding the assessment, feel free to reply to this email.

We look forward to reviewing your submission.

{config.SIGNATURE}
"""


def fde_body(name):
    return _fde_style_body(name, "Forward Deployed Engineer")


def fde_followup_body(name):
    """One-off follow-up for candidates who already got the FDE assessment
    email before its PDF existed - just the missing attachment, not the
    whole assessment message again."""
    return f"""Hi {name},

Following up on the Forward Deployed Engineer technical assessment we sent earlier - please find the assessment document attached to this email.

Everything else from our previous email (submission guidelines and deadline) still applies.

If you have any questions, feel free to reply to this email.

{config.SIGNATURE}
"""


def product_engineer_body(name):
    return _fde_style_body(name, "Product Engineer")


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
