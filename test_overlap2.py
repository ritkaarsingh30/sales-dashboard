import re

def is_covered(plan, actual):
    if not plan or not actual or str(plan).strip() in ('nan', '') or str(actual).strip() in ('nan', ''):
        return False

    p_up = str(plan).upper()
    a_up = str(actual).upper()

    # Strip common generic words that might cause false positives
    stopwords = {"ZONE", "DE", "DU", "LA", "LE", "LES"}

    p_words = set(w for w in re.findall(r'[A-Z0-9]{3,}', p_up) if w not in stopwords)
    a_words = set(w for w in re.findall(r'[A-Z0-9]{3,}', a_up) if w not in stopwords)

    if not p_words or not a_words:
        return p_up == a_up

    # Covered if intersection is not empty
    return len(p_words & a_words) > 0

pairs = [
    ("Zone Adjame", "Zone abobodoume locodjro mossikro millionnaire wassakara"),
    ("Zone Adjame", "Zone du CHU de Cocody"),
]

for p, a in pairs:
    print(f"Plan: {p} | Actual: {a} | Covered: {is_covered(p, a)}")
