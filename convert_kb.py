import csv
import json
import re

INPUT = r"C:\Users\ashmi\OneDrive\Desktop\MedicalQnA.csv"
OUTPUT = "data/health_knowledge.json"

# Map qtype to category
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
    text = re.sub(r'\s+', ' ', text or "").strip()
    return text

seen = set()
items = []

with open(INPUT, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    for row in reader:
        qtype = clean(row.get("qtype", ""))
        question = clean(row.get("Question", ""))
        answer = clean(row.get("Answer", ""))

        if not question or not answer:
            continue
        # Skip duplicates
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)

        category = CATEGORY_MAP.get(qtype.lower(), "General")

        items.append({
            "title": question,
            "text": answer,
            "category": category,
            "url": ""
        })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Done. {len(items)} items written to {OUTPUT}")
