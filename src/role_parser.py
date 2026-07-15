import re

import config

_LEADING_FILLER_RE = re.compile(r"^(the|a|an|post of|position of|role of)\s+", re.IGNORECASE)
_TRAILING_FILLER_RE = re.compile(r"\s+(position|role|post|job|opening|vacancy)\.?$", re.IGNORECASE)
_STRIP_CHARS = " \t-:.–—"


def extract_role(subject):
    """Pulls the role/job title out of a subject like "Apply For Junior SAP
    B1 Functional consultant" or "Application for the graphic designer
    position" by cutting everything up to and including whichever of the
    configured subject phrases appears first, then trimming common filler
    words around it."""
    if not subject:
        return ""

    lowered = subject.lower()
    best_index = None
    best_phrase_len = 0
    for phrase in config.SUBJECT_KEYWORDS:
        index = lowered.find(phrase)
        if index != -1 and (best_index is None or index < best_index):
            best_index = index
            best_phrase_len = len(phrase)

    if best_index is None:
        return ""

    role = subject[best_index + best_phrase_len:].strip(_STRIP_CHARS)

    # Repeatedly strip leading filler since phrases can stack, e.g.
    # "the post of X" needs both "the " and "post of " removed in turn.
    while True:
        stripped = _LEADING_FILLER_RE.sub("", role).strip(_STRIP_CHARS)
        if stripped == role:
            break
        role = stripped

    role = _TRAILING_FILLER_RE.sub("", role)
    return role.strip(_STRIP_CHARS)
