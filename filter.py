# filter.py
from config import cfg

_scoring = cfg["scoring"]
_lang = cfg["language_filters"]

PRIORITY_KEYWORDS       = _scoring["priority_keywords"]
BASE_KEYWORDS           = _scoring["base_keywords"]
PRIORITY_COMPANIES      = _scoring["priority_companies"]
REFERRAL_COMPANIES      = _scoring.get("referral_companies", [])
NEGATIVE_TITLE_KEYWORDS = _scoring["negative_title_keywords"]
BLOCKED_COMPANIES       = _scoring["blocked_companies"]
SENIOR_TITLE_KEYWORDS   = _scoring["senior_title_keywords"]

GERMAN_WORDS            = _lang["german_words"]
GERMAN_REQUIRED_PHRASES = _lang["german_required_phrases"]
SWEDISH_WORDS           = _lang["swedish_words"]
SWEDISH_REQUIRED_PHRASES = _lang["swedish_required_phrases"]


def score_job(row, filter_german=True, filter_swedish=False):
    title       = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()
    company     = str(row.get("company", "")).lower()

    # --- hard exclusions (return -1 immediately) ---

    if filter_german:
        if any(w in description for w in GERMAN_WORDS):
            return -1
        if any(p in description for p in GERMAN_REQUIRED_PHRASES):
            return -1

    if filter_swedish:
        if any(w in description for w in SWEDISH_WORDS):
            return -1
        if any(p in description for p in SWEDISH_REQUIRED_PHRASES):
            return -1

    if any(kw in title for kw in NEGATIVE_TITLE_KEYWORDS):
        return -1

    if not any(kw in title or kw in description for kw in BASE_KEYWORDS):
        return -1

    if any(c in company for c in BLOCKED_COMPANIES):
        return -1

    # --- scoring ---

    # Priority keywords matched in description OR title
    score = sum(kw in description or kw in title for kw in PRIORITY_KEYWORDS)

    # Referral companies — highest bonus (+3), you have a contact here
    if any(c in company for c in REFERRAL_COMPANIES):
        score += 3

    # Priority companies — strong targets (+2)
    elif any(c in company for c in PRIORITY_COMPANIES):
        score += 1

    # Senior title penalty
    if any(kw in title for kw in SENIOR_TITLE_KEYWORDS):
        score = max(0, score - 3)

    return score