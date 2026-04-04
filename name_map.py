"""
name_map.py — IVC Pharma Dashboard: Master Name & Entity Mapping
================================================================
Single source of truth for all entity normalization.
Import this in app.py and call normalize_*(name) before any chart or table.

Fuzzy matching threshold: 70 (safe for most pharma name variants).
For joint entries like "JITENDRA/CLEMANCE", use resolve_joint_mr().
"""

from rapidfuzz import process, fuzz

# ─────────────────────────────────────────────────────────────
# 1. MR / FIELD STAFF
# ─────────────────────────────────────────────────────────────

MR_CANONICAL = {
    "MR_001": "NELLY NIAMIEN",
    "MR_002": "CLEMANCE KOUDIANE",
    "MR_003": "JAMBA FRANCK",
    "MR_004": "AHIOUA",
    "MR_005": "TOUALY CLEVAR",
    "MR_006": "JITENDRA MISHRA",   # Country Manager (CM)
    "AGT_001": "ARRA BEHOU",       # Promo Agent (not MR)
}

# Hard-coded overrides first (exact/near-exact variants that fuzzy may miss)
MR_OVERRIDES = {
    # NELLY
    "MME NELLY": "MR_001", "MME NELLY ": "MR_001", "NELLY": "MR_001",
    "NELLY NIAMIEN": "MR_001",
    # CLEMANCE
    "MME CLEMENCE": "MR_002", "MME CLEMANCE": "MR_002", "CLEMANCE": "MR_002",
    "CALMANCE": "MR_002", "IN LIST OF CLAMANCE": "MR_002",
    "CLEMANCE KOUDIANE": "MR_002",
    # JAMBA
    "MR JAMBA FRANCK": "MR_003", "JAMBA FRANK": "MR_003",
    "JAMBA FRANCK": "MR_003", "JAMBA Franck": "MR_003", "JAMAB FRANK": "MR_003",
    # AHIOUA
    "MME AHIOUA": "MR_004", "AHIOUA": "MR_004",
    "IN LIST OF AHIOUA": "MR_004",
    # TOUALY (also appears as VALERY in Feb tracker)
    "MR TOUALY": "MR_005", "TOUALY": "MR_005", "VALERY": "MR_005",
    "MR. TOUALY CLEVAR": "MR_005", "TOUALY CLEVAR": "MR_005",
    # JITENDRA (CM)
    "MR. JITENDER": "MR_006", "JITENDRA": "MR_006",
    "MR. JITENDER MISHRA": "MR_006", "JITENDER SIR": "MR_006",
    "MR. JITENDER ": "MR_006", "JITENDRA MISHRA": "MR_006",
    "1": "MR_006",   # data entry error in report file
    # ARRA BEHOU
    "ARRA BEHOU": "AGT_001",
}

# Joint entries — map to list of IDs
MR_JOINT_MAP = {
    "JITENDRA/NELLY":    ["MR_006", "MR_001"],
    "JITENDRA/CLEMANCE": ["MR_006", "MR_002"],
    "JITENDRA/ARRA":     ["MR_006", "AGT_001"],
    "DELEGAT/CM/AGENT":  ["MR_006", "AGT_001"],
}

def normalize_mr(raw: str) -> str:
    """
    Returns canonical MR ID string.
    Joint entries return comma-separated IDs e.g. 'MR_006,MR_002'.
    Unknown returns 'UNKNOWN'.
    """
    if not raw or str(raw).strip() in ("", "nan"):
        return "UNKNOWN"
    clean = str(raw).strip()
    
    # Check joint entries first
    clean_upper = clean.upper()
    if clean_upper in MR_JOINT_MAP:
        return ",".join(MR_JOINT_MAP[clean_upper])
    
    # Check hard overrides
    if clean_upper in MR_OVERRIDES:
        return MR_OVERRIDES[clean_upper]
    
    # Fuzzy fallback — strip common prefixes before matching
    stripped = clean_upper
    for prefix in ["MME ", "MR. ", "MR ", "IN LIST OF "]:
        stripped = stripped.replace(prefix, "")
    stripped = stripped.strip()
    
    candidates = list(MR_CANONICAL.values())
    match, score, _ = process.extractOne(
        stripped, [c.upper() for c in candidates], scorer=fuzz.token_sort_ratio
    )
    if score >= 70:
        # Return ID from canonical dict
        for id_, name in MR_CANONICAL.items():
            if name.upper() == match:
                return id_
    return "UNKNOWN"

def mr_display_name(mr_id: str) -> str:
    """Convert MR_001 -> 'NELLY NIAMIEN'. Handles comma-separated joint IDs."""
    if "," in mr_id:
        return " + ".join(MR_CANONICAL.get(i, i) for i in mr_id.split(","))
    return MR_CANONICAL.get(mr_id, mr_id)


# ─────────────────────────────────────────────────────────────
# 2. PRODUCTS
# ─────────────────────────────────────────────────────────────

PRODUCT_CANONICAL = {
    "P_001": "COZEE 60",
    "P_002": "COZEE 90",
    "P_003": "COZEE 120",
    "P_004": "FEZEE",
    "P_005": "FUSIZEX 40",       # Tablet
    "P_006": "KLINDEX-M",
    "P_007": "NOSEE",
    "P_008": "OMEZEE 20",
    "P_009": "PROZEE 100",
    "P_010": "CITIZEN INJ",
    "P_011": "FUSIZEX INJ",       # Injectable
    "P_012": "AVETEX INJ",
    "P_013": "BETNEZEN INJ",
    "P_014": "HEMOTRATE INJ",
    "P_015": "OMECID INJ",
    "P_016": "STURIX INJ",
}

PRODUCT_OVERRIDES = {
    # COZEE family
    "COZEE 60": "P_001", "COZEE60": "P_001",
    "COZEE 90": "P_002", "COZEE90": "P_002",
    "COZEE 120": "P_003", "COZEE120": "P_003",
    "COZEE": None,  # too ambiguous — skip, flag separately
    # FEZEE
    "FEZEE": "P_004", "FEZEE GELU BT 10": "P_004",
    # FUSIZEX tablet
    "FUSIZEX 40": "P_005", "FUSIZEX 40MG CPR BOITE DE 30": "P_005",
    # KLINDEX-M (typo variant KLINDEZ-M)
    "KLINDEX-M": "P_006", "KLINDEZ-M": "P_006",
    "KLINDEX M 100MG CAPS VAG BT 7": "P_006", "KLINDEX": "P_006",
    # NOSEE (typo variant NOZEE)
    "NOSEE": "P_007", "NOZEE": "P_007",
    "NOSEE 10MG/10MG CPR BT 30": "P_007",
    # OMEZEE
    "OMEZEE 20": "P_008", "OMEZEE": "P_008",
    "OMEZEE 20MG GELU BT 10": "P_008",
    # PROZEE
    "PROZEE 100": "P_009", "PROZEE": "P_009",
    # CITIZEN INJ
    "CITIZEN- INJ": "P_010", "CITIZEN INJ": "P_010", "CITIZEN": "P_010",
    "CITIZEN 1000MG/4ML B/5AMP (CITICOLINE INJ 1G/4ML)": "P_010",
    "CITIZEN 1000MG SOL INJ 5 AMP": "P_010",
    # FUSIZEX INJ
    "FUSIZEX-INJ": "P_011", "FUSIZEX INJ": "P_011",
    "FUSIZEX 10MG/ML (FUROSEMIDE 10MG/ML)": "P_011",
    "FUSIZEX 10MG SOL INJ AMP B10": "P_011",
    "FUSIZEX 10": "P_011",
    # AVETEX INJ (typo: AVTEX)
    "AVETEX-INJ": "P_012", "AVETEX INJ": "P_012",
    "AVETEX 500MG INJ B/1AMP": "P_012",
    "AVETEX 500MG PDR SOL PERF FL 1": "P_012",
    "AVETEX": "P_012", "AVTEX": "P_012",
    # BETNEZEN INJ
    "BETNEZEN-INJ": "P_013", "BETNEZEN INJ": "P_013",
    "BETNEZEN 4MG/ML B/5AMP": "P_013",
    "BETNEZEN SOL INJ AMP BT 5X1ML": "P_013", "BETNEZEN": "P_013",
    # HEMOTRATE INJ
    "HEMOTRATE-INJ": "P_014", "HEMOTRATE INJ": "P_014",
    "HEMOTRATE-S B/5AMP": "P_014",
    "HEMOTRATE-S SOL INJ AMP 5X5ML": "P_014", "HEMOTRATE": "P_014",
    # OMECID INJ (trailing comma variant)
    "OMECID INJ": "P_015", "OMECID 40 MG INJ  B 1AMP": "P_015",
    "OMECID 40MG PDR SOL PERF FL 1": "P_015",
    "OMECID": "P_015", "OMECID,": "P_015",
    # STURIX INJ
    "STURIX-INJ": "P_016", "STURIX INJ": "P_016",
    "STURIX 500MG/5ML B/5AMP": "P_016",
    "STURIX 500MG SOL INJ AMP 5X5ML": "P_016", "STURIX": "P_016",
    # DISCONTINUED / NOT OUR PRODUCTS — explicitly excluded
    "ARTEQUIN LACTAB 300/375 BT6": None,
    "ARTEQUIN LACTAB 600/750 BT6": None,
    "LETROVIN 2,5MG CPR BOITE 30": None,
    "AVETEX(417 ) DEC-& JAN": "P_012",  # historical label, map to AVETEX INJ
}

PRODUCT_CATEGORIES = {
    "P_001": "TABLET", "P_002": "TABLET", "P_003": "TABLET",
    "P_004": "TABLET", "P_005": "TABLET", "P_006": "TABLET",
    "P_007": "TABLET", "P_008": "TABLET", "P_009": "TABLET",
    "P_010": "INJECTABLE", "P_011": "INJECTABLE", "P_012": "INJECTABLE",
    "P_013": "INJECTABLE", "P_014": "INJECTABLE",
    "P_015": "INJECTABLE", "P_016": "INJECTABLE",
}

def normalize_product(raw: str) -> str:
    """Returns product ID. None = excluded. 'UNKNOWN' = not recognized."""
    if not raw or str(raw).strip() in ("", "nan"):
        return "UNKNOWN"
    clean = str(raw).strip().upper()
    if clean in PRODUCT_OVERRIDES:
        result = PRODUCT_OVERRIDES[clean]
        return result if result is not None else "EXCLUDED"
    # Fuzzy fallback
    candidates = list(PRODUCT_CANONICAL.values())
    match, score, _ = process.extractOne(
        clean, [c.upper() for c in candidates], scorer=fuzz.token_sort_ratio
    )
    if score >= 75:
        for id_, name in PRODUCT_CANONICAL.items():
            if name.upper() == match:
                return id_
    return "UNKNOWN"

def product_display_name(product_id: str) -> str:
    return PRODUCT_CANONICAL.get(product_id, product_id)

def product_category(product_id: str) -> str:
    return PRODUCT_CATEGORIES.get(product_id, "UNKNOWN")


# ─────────────────────────────────────────────────────────────
# 3. ACTIVITY TYPES
# ─────────────────────────────────────────────────────────────

ACTIVITY_CANONICAL = {
    "ACT_COMMISSION":      "COMMISSION",
    "ACT_MOTIVATION":      "MOTIVATION",
    "ACT_PETIT_DEJ":       "PETIT DEJEUNER",
    "ACT_GARD":            "GARD ACTIVITY",
    "ACT_PARTNERSHIP":     "PARTNERSHIP",
    "ACT_CME":             "CME",
    "ACT_INJ_COMMISSION":  "INJECTABLE COMMISSION",
    "ACT_WINE":            "WINE",
    "ACT_KIT_SAVON":       "KIT DE SAVON",
    "ACT_PAGNE":           "PAGNE",
    "ACT_STAMP":           "STAMP",
    "ACT_SAMPLE":          "SAMPLE",
}

ACTIVITY_OVERRIDES = {
    "COMMISSION": "ACT_COMMISSION", "COMISSION": "ACT_COMMISSION",
    "MOTIVATION": "ACT_MOTIVATION", "MOTIVATION ": "ACT_MOTIVATION",
    "PETIT DEJOUNER": "ACT_PETIT_DEJ", "PETITE DEJOUNER": "ACT_PETIT_DEJ",
    "PETITE DEJEUNER": "ACT_PETIT_DEJ", "PETIT DEJEUNER": "ACT_PETIT_DEJ",
    "GARD ACTIVITY": "ACT_GARD", "GARD": "ACT_GARD",
    "PARTNERSHIP": "ACT_PARTNERSHIP",
    "CME": "ACT_CME", "CME PLAN": "ACT_CME",
    "INJECTABLE COMMISSION": "ACT_INJ_COMMISSION",
    "WINE": "ACT_WINE",
    "KIT DE SAVON": "ACT_KIT_SAVON", "KIT SAVON": "ACT_KIT_SAVON",
    "PAGNE": "ACT_PAGNE",
    "STAMP": "ACT_STAMP",
    "SAMPLE PROZEE": "ACT_SAMPLE", "SAMPLE": "ACT_SAMPLE",
}

def normalize_activity(raw: str) -> str:
    if not raw or str(raw).strip() in ("", "nan"):
        return "UNKNOWN"
    clean = str(raw).strip().upper()
    if clean in ACTIVITY_OVERRIDES:
        return ACTIVITY_OVERRIDES[clean]
    match, score, _ = process.extractOne(
        clean, list(ACTIVITY_OVERRIDES.keys()), scorer=fuzz.token_sort_ratio
    )
    if score >= 75:
        return ACTIVITY_OVERRIDES[match]
    return "UNKNOWN"

def activity_display_name(act_id: str) -> str:
    return ACTIVITY_CANONICAL.get(act_id, act_id)


# ─────────────────────────────────────────────────────────────
# 4. TERRITORIES / ZONES
# ─────────────────────────────────────────────────────────────

TERRITORY_CANONICAL = {
    "ZONE_YOP_WEST":  "YOPOUGON WEST",
    "ZONE_YOP_EAST":  "YOPOUGON EAST",
    "ZONE_COCODY":    "COCODY",
    "ZONE_ADJAME":    "ADJAME",
    "ZONE_MARCORI":   "MARCORI + KOUMASSI",
}

TERRITORY_OVERRIDES = {
    "YOPOUGON OUEST": "ZONE_YOP_WEST", "YOUPOUGON WEST": "ZONE_YOP_WEST",
    "YOPOUGON QUEST": "ZONE_YOP_WEST", "YOPOUGON WEST": "ZONE_YOP_WEST",
    "YOPOUGON EAST": "ZONE_YOP_EAST", "YOUPOUGON EAST": "ZONE_YOP_EAST",
    "YOPOUGON EST": "ZONE_YOP_EAST",
    "COCODY": "ZONE_COCODY", "COCODI": "ZONE_COCODY",
    "ADJAME": "ZONE_ADJAME", "ADJAME +ATTACOUBE": "ZONE_ADJAME",
    "ADJAME/ATTACOUBE": "ZONE_ADJAME",
    "MARCORI+KOUMASSI": "ZONE_MARCORI",
    "KOUMASSI+MARCORI+PORT BOUET": "ZONE_MARCORI",
    "MARCORI + KOUMASSI": "ZONE_MARCORI",
}

def normalize_territory(raw: str) -> str:
    if not raw or str(raw).strip() in ("", "nan"):
        return "UNKNOWN"
    clean = str(raw).strip().upper()
    if clean in TERRITORY_OVERRIDES:
        return TERRITORY_OVERRIDES[clean]
    match, score, _ = process.extractOne(
        clean, list(TERRITORY_OVERRIDES.keys()), scorer=fuzz.token_sort_ratio
    )
    if score >= 75:
        return TERRITORY_OVERRIDES[match]
    return "UNKNOWN"

def territory_display_name(zone_id: str) -> str:
    return TERRITORY_CANONICAL.get(zone_id, zone_id)


# ─────────────────────────────────────────────────────────────
# 5. DOCTOR NAMES
# ─────────────────────────────────────────────────────────────

DOCTOR_CANONICAL = {
    # e.g., "DOC_001": "DR. JOHN DOE",
}

DOCTOR_OVERRIDES = {
    # e.g., "JOHN DOE": "DOC_001",
}

_DOCTOR_INDEX = []  # dynamically populated at runtime

def build_doctor_index(doctor_names: list):
    """
    Call once at app startup with all doctor names from visit tracker sheets.
    Deduplicates and normalizes for fuzzy matching.
    """
    global _DOCTOR_INDEX
    cleaned = set()
    for name in doctor_names:
        n = str(name).strip()
        if n and n.lower() not in ("nan", "nom /pernom", ""):
            cleaned.add(n)
    _DOCTOR_INDEX = sorted(cleaned)
    return _DOCTOR_INDEX

def normalize_doctor(raw: str, threshold: int = 72) -> str:
    """
    Returns closest canonical doctor name using exact mapping first,
    then visit tracker index fuzzy match. Falls back to cleaned raw name.
    """
    if not raw or str(raw).strip() in ("", "nan"):
        return "UNKNOWN"
    clean = str(raw).strip().upper()

    if clean in DOCTOR_OVERRIDES:
        doc_id = DOCTOR_OVERRIDES[clean]
        return DOCTOR_CANONICAL.get(doc_id, doc_id)

    clean_original_case = str(raw).strip()
    if not _DOCTOR_INDEX:
        return clean_original_case  # index not built yet, return as-is

    match, score, _ = process.extractOne(
        clean_original_case, _DOCTOR_INDEX, scorer=fuzz.token_sort_ratio
    )
    return match if score >= threshold else clean_original_case


# ─────────────────────────────────────────────────────────────
# 6. DISTRIBUTORS
# ─────────────────────────────────────────────────────────────

DISTRIBUTOR_CANONICAL = {
    "DIST_01": "UBIPHARM / LABOREX",
    "DIST_02": "COPHARMED / LABOREX",
    "DIST_03": "TEDIS",
    "DIST_04": "DPCI",
}

DISTRIBUTOR_OVERRIDES = {
    "UBIPHARM/LABOREX": "DIST_01", "UBIPHARM / LABOREX": "DIST_01",
    "COPHARMED/LABOREX": "DIST_02", "COPHARMED / LABOREX": "DIST_02",
    "TEDIS": "DIST_03",
    "DPCI": "DIST_04",
}

def normalize_distributor(raw: str) -> str:
    clean = str(raw).strip().upper()
    return DISTRIBUTOR_OVERRIDES.get(clean, "UNKNOWN")

def distributor_display_name(dist_id: str) -> str:
    return DISTRIBUTOR_CANONICAL.get(dist_id, dist_id)


# ─────────────────────────────────────────────────────────────
# 7. CURRENCY HELPER
# ─────────────────────────────────────────────────────────────

FCFA_TO_EUR = 655.97

def to_eur(fcfa: float) -> float:
    return round(fcfa / FCFA_TO_EUR, 2)

def to_fcfa(eur: float) -> float:
    return round(eur * FCFA_TO_EUR, 0)


# ─────────────────────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("MR", normalize_mr, [
            "calmance", "jamab frank", "jitender sir", "VALERY",
            "in list of ahioua", "JITENDRA/CLEMANCE", "1"
        ]),
        ("PRODUCT", normalize_product, [
            "KLINDEZ-M", "NOZEE", "AVTEX", "OMECID,", "FUSIZEX-INJ",
            "AVETEX(417 ) DEC-& JAN", "ARTEQUIN LACTAB 300/375 BT6"
        ]),
        ("ACTIVITY", normalize_activity, [
            "COMISSION", "PETITE DEJOUNER", "PETIT DEJOUNER", "MOTIVATION "
        ]),
        ("TERRITORY", normalize_territory, [
            "YOPOUGON OUEST", "YOUPOUGON EAST", "COCODI", "KOUMASSI+MARCORI+PORT BOUET"
        ]),
    ]
    for label, fn, cases in tests:
        print(f"\n=== {label} ===")
        for c in cases:
            result = fn(c)
            print(f"  '{c}' -> {result}")