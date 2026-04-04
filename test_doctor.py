import pandas as pd
from name_map import normalize_doctor, build_doctor_index

build_doctor_index(["JOHN DOE", "JANE DOE", "DR. SMITH", "DR. JANE DOE"])

print(normalize_doctor("JOHN DO E"))
print(normalize_doctor("DR SMITH"))
