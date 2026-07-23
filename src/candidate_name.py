import re

_NAME_LINE_RE = re.compile(r"^[A-Z][a-zA-Z.'-]+(\s+[A-Z][a-zA-Z.'-]+){1,3}$")
_RESUME_NOISE_WORDS = {
    "resume", "curriculum vitae", "cv", "objective", "summary", "contact",
    "email", "phone", "address", "profile", "linkedin", "github", "portfolio",
    "skills", "education", "experience", "projects", "certifications",
}
_GENERIC_DISPLAY_NAMES = {"undisclosed", "no reply", "noreply", "no-reply"}


def resolve(display_name, email_addr, resume_text):
    """Picks a candidate name to greet in the email: the sender's display
    name from the From header, falling back to a line in their resume that
    looks like a person's name, falling back to a title-cased version of
    their email's local part."""
    name = _from_display_name(display_name)
    if name:
        return name

    name = _from_resume_text(resume_text)
    if name:
        return name

    return _from_email(email_addr)


def _from_display_name(display_name):
    if not display_name:
        return None
    cleaned = display_name.strip().strip('"').strip()
    if not cleaned or "@" in cleaned:
        return None
    if cleaned.lower() in _GENERIC_DISPLAY_NAMES:
        return None
    if not re.search(r"[A-Za-z]", cleaned):
        return None
    return _title_case_if_shouty_or_flat(cleaned)


def _from_resume_text(resume_text):
    if not resume_text:
        return None
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    for line in lines[:8]:
        if "@" in line or re.search(r"\d", line):
            continue
        if len(line) > 40:
            continue
        if any(word in line.lower() for word in _RESUME_NOISE_WORDS):
            continue
        if _NAME_LINE_RE.match(line):
            return line
    return None


def _from_email(email_addr):
    local = (email_addr or "").split("@")[0]
    parts = [p for p in re.split(r"[._\-+0-9]+", local) if p]
    if not parts:
        return "Candidate"
    return " ".join(p.capitalize() for p in parts)


def _title_case_if_shouty_or_flat(name):
    # Respects names with intentional internal casing (e.g. "McDonald");
    # only normalizes names that arrived as ALL CAPS or all lowercase.
    if name.isupper() or name.islower():
        return name.title()
    return name
