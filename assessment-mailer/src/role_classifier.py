QA = "qa"
FULLSTACK = "fullstack"
GRAPHIC = "graphic"
RECRUITER = "recruiter"
AI_NATIVE = "ai_native"
MOBILE = "mobile"
FDE = "fde"
PRODUCT_ENGINEER = "product_engineer"

# Order matters only for readability - classify() counts how many distinct
# roles a subject matches and only returns one when exactly one matches, so
# an ambiguous subject (matching two roles, or none) returns None.
_ROLE_KEYWORDS = [
    (QA, ["qa", "quality assurance", "quality analyst", "test engineer", "sdet", "software tester"]),
    (FULLSTACK, ["full stack", "full-stack", "fullstack", "mern", "mean stack"]),
    (GRAPHIC, ["graphic design", "graphic designer", "graphics designer"]),
    (RECRUITER, ["recruiter", "recruitment intern", "talent acquisition"]),
    (AI_NATIVE, [
        # Bare "ai native"/"ai-native" used to be its own keyword, which
        # wrongly matched *any* AI Native role (e.g. an unrelated AI Native
        # engineering posting) as this one. Only the full role phrase - AI
        # Native + Digital Marketing & Growth, or AI Native + Sales &
        # Business Development - counts now.
        "ai native digital marketing & growth", "ai native digital marketing and growth",
        "ai-native digital marketing & growth", "ai-native digital marketing and growth",
        "ai native sales & business development", "ai native sales and business development",
        "ai-native sales & business development", "ai-native sales and business development",
    ]),
    (MOBILE, [
        "mobile application", "mobile app development", "mobile developer",
        "android developer", "ios developer", "react native",
    ]),
    (FDE, [
        # Candidates write this both ways ("deployed" vs "deployment") -
        # match both so a real applicant's subject line isn't missed.
        "forward deployed engineer", "forward-deployed engineer",
        "forward deployment engineer", "forward-deployment engineer",
    ]),
    (PRODUCT_ENGINEER, ["product engineer"]),
]


def classify(subject):
    """Returns one of the role constants, or None when the subject matches
    none of the known roles or is ambiguous (matches more than one)."""
    if not subject:
        return None

    lowered = subject.lower()
    matched = [
        role for role, keywords in _ROLE_KEYWORDS
        if any(keyword in lowered for keyword in keywords)
    ]

    if len(matched) == 1:
        return matched[0]
    return None
