import csv
import json
import re
from collections import defaultdict

INPUT = r"C:\Users\ashmi\OneDrive\Desktop\MedicalQnA.csv"
OUTPUT = "data/health_knowledge.json"

CATEGORY_MAP = {
    "symptoms": "Infectious Disease",
    "susceptibility": "Infectious Disease",
    "exams and tests": "Diagnosis",
    "treatment": "Treatment",
    "prevention": "Prevention",
    "causes": "Infectious Disease",
    "outlook": "General",
    "information": "General",
}

def clean(text):
    return re.sub(r'\s+', ' ', text or "").strip()

# Group by disease (first word of question title gives rough grouping)
# Strategy: take up to 2 entries per unique question title to maximize diversity
seen_titles = set()
items = []

with open(INPUT, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

# Shuffle-like: sort by qtype to get variety, then deduplicate by title
all_rows.sort(key=lambda r: r.get("qtype", ""))

for row in all_rows:
    qtype = clean(row.get("qtype", ""))
    question = clean(row.get("Question", ""))
    answer = clean(row.get("Answer", ""))

    if not question or not answer:
        continue
    if question.lower() in seen_titles:
        continue
    seen_titles.add(question.lower())

    category = CATEGORY_MAP.get(qtype.lower(), "General")
    items.append({
        "title": question,
        "text": answer,
        "category": category,
        "url": ""
    })

# Cap at 3000 but take evenly from sorted (diverse) list
# Take every Nth item to spread across all diseases
total = len(items)
step = max(1, total // 3000)
sampled = items[::step][:3000]

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(sampled, f, indent=2, ensure_ascii=False)

print(f"Total unique: {total}, Sampled: {len(sampled)} items written to {OUTPUT}")
