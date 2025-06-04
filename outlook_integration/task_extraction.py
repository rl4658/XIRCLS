import re
import spacy

# Load spaCy’s English model once at import time
nlp = spacy.load("en_core_web_sm")

# Regex patterns that often signal action items
TRIGGER_PATTERNS = [
    re.compile(r"^(?:schedule|send|follow up|update|assign|create|plan|review|confirm)\b", re.IGNORECASE),
    re.compile(r"\bshould\b", re.IGNORECASE),
    re.compile(r"\bneed to\b", re.IGNORECASE),
    re.compile(r"\blet'?s\b", re.IGNORECASE),
    re.compile(r"\baction[:\-]\b", re.IGNORECASE),
]

def extract_tasks_rule_based(transcription: str) -> list[str]:
    """
    Given a full transcription string, return a list of sentences that look like "action items."
    """
    doc = nlp(transcription)
    tasks: list[str] = []

    for sent in doc.sents:
        text = sent.text.strip()
        if not text:
            continue

        # 1) Check if the first token is an imperative (base‐form verb, POS tag "VB")
        first_token = sent[0]
        is_imperative = first_token.tag_ == "VB"

        # 2) Check if any trigger regex matches anywhere in the sentence
        has_trigger = any(pattern.search(text) for pattern in TRIGGER_PATTERNS)

        if is_imperative or has_trigger:
            # Collapse multiple spaces/newlines into a single space
            cleaned = re.sub(r"\s+", " ", text)
            tasks.append(cleaned)

    return tasks
