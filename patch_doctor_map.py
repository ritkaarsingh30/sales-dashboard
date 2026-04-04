import re

with open("name_map.py", "r") as f:
    content = f.read()

with open("doctors_map.txt", "r") as f:
    map_content = f.read()

# Get the DOCTOR_CANONICAL block
match = re.search(r'DOCTOR_CANONICAL = \{.*?(^\})', map_content, re.MULTILINE | re.DOTALL)
if match:
    canonical_block = match.group(0)
    # Find the current DOCTOR_CANONICAL block in name_map.py and replace it
    content = re.sub(r'DOCTOR_CANONICAL = \{\s+# e\.g\., "DOC_001": "DR\. JOHN DOE",\n\}', canonical_block, content, flags=re.DOTALL)

# Get the DOCTOR_OVERRIDES block
match = re.search(r'DOCTOR_OVERRIDES = \{.*?(^\})', map_content, re.MULTILINE | re.DOTALL)
if match:
    overrides_block = match.group(0)
    # Find the current DOCTOR_OVERRIDES block in name_map.py and replace it
    content = re.sub(r'DOCTOR_OVERRIDES = \{\s+# e\.g\., "JOHN DOE": "DOC_001",\n\}', overrides_block, content, flags=re.DOTALL)

with open("name_map.py", "w") as f:
    f.write(content)
