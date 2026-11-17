"""Script to validate and fix skills dictionary duplicates."""

import json
from collections import defaultdict
from pathlib import Path

dict_path = Path(__file__).parent / "api" / "extraction" / "skills_dictionary.json"

with open(dict_path) as f:
    data = json.load(f)

# Find duplicates
canonical_counts = defaultdict(list)
alias_to_canonical = defaultdict(list)

for category, skills in data["skills"].items():
    for skill in skills:
        canonical = skill["canonical"]
        canonical_counts[canonical].append(category)

        # Register canonical as alias
        alias_to_canonical[canonical.lower()].append(canonical)

        # Register other aliases
        for alias in skill.get("aliases", []):
            alias_to_canonical[alias.lower()].append(canonical)

# Report duplicates
print("Duplicate canonical names:")
for canonical, categories in canonical_counts.items():
    if len(categories) > 1:
        print(f"  {canonical}: {categories}")

print("\nAmbiguous aliases:")
for alias, canonicals in alias_to_canonical.items():
    if len(canonicals) > 1:
        print(f"  {alias}: {canonicals}")
