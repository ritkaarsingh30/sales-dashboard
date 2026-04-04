import re

def is_covered(plan, actual):
    if not plan or not actual or str(plan).strip() in ('nan', '') or str(actual).strip() in ('nan', ''):
        return False

    p_up = str(plan).upper()
    a_up = str(actual).upper()

    # Simple check if any word from plan > 3 chars is in actual
    p_words = set(re.findall(r'[A-Z0-9]{3,}', p_up))
    a_words = set(re.findall(r'[A-Z0-9]{3,}', a_up))

    if not p_words or not a_words:
        # Fallback to pure string match if words are too short
        return p_up == a_up

    # If at least one significant word matches, consider it covered
    if p_words & a_words:
        return True
    return False

pairs = [
    ("sicogie,sogephia,", "sicogie/sogephia"),
    ("TOIT ROUGE WASSAKARA", "wassakara toit rouge"),
    ("Yasmine", "Centre médical Yasmine"),
    ("Adjame", "Adjame"),
    ("WITH AGENT/TEAM", ""),
    ("Adjame", "ananeraie"),
    ("Adjame", "selmer"),
    ("Adjame", "Cocody"),
    ("koumassi", "koumassi"),
    ("Adjame -bramacote", "agefosyn"),
    ("Adjame -bramacote", "andokoi - keneya"),
    ("Adjame -bramacote", "Cocody anono,"),
    ("port Bouet", "port Bouet"),
    ("YOPOUGON OUEST", "Port Bouet/Cocodi"),
    ("Zone Adjame", "Zone abobodoume locodjro mossikro millionnaire wassakara"),
    ("Zone Adjame", "Zone du CHU de Cocody"),
]

for p, a in pairs:
    print(f"Plan: {p} | Actual: {a} | Covered: {is_covered(p, a)}")
