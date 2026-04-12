import json, hashlib

NEW_ENTRIES = [
  {"title": "What is PCOS polycystic ovary syndrome?", "text": "PCOS (Polycystic Ovary Syndrome) is a hormonal disorder common in women of reproductive age. It causes irregular periods, excess androgen levels, and polycystic ovaries. It can lead to fertility problems, diabetes, and heart disease if untreated. Lifestyle changes and medication can help manage it.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of PCOS?", "text": "PCOS symptoms include: irregular or missed periods, excess facial and body hair (hirsutism), acne, oily skin, weight gain especially around the abdomen, thinning hair or hair loss, darkening of skin, and difficulty getting pregnant. Not all women have all symptoms.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What is PCOD polycystic ovarian disease?", "text": "PCOD (Polycystic Ovarian Disease) is a condition where the ovaries produce many immature or partially mature eggs. It causes hormonal imbalance, irregular periods, weight gain, and acne. PCOD is more common than PCOS and can be managed with diet, exercise, and medication.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of PCOD?", "text": "PCOD symptoms include: irregular periods, weight gain, acne, oily skin, excess hair growth on face and body, hair thinning, mood swings, and difficulty conceiving. A healthy diet and regular exercise can significantly improve symptoms.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of tuberculosis TB?", "text": "Tuberculosis (TB) symptoms include: persistent cough lasting more than 2 weeks (sometimes with blood), chest pain, weakness and fatigue, unexplained weight loss, fever, and night sweats. TB mainly affects the lungs but can affect other organs. Anyone with these symptoms should get tested immediately.", "category": "Infectious Disease", "url": ""},
  {"title": "What are symptoms of cough?", "text": "A persistent cough can be caused by respiratory infections, asthma, allergies, acid reflux, or smoking. Common associated symptoms include sore throat, runny nose, and chest tightness. See a doctor if cough lasts more than 2-3 weeks, produces blood, or is accompanied by fever and weight loss.", "category": "Infectious Disease", "url": ""},
  {"title": "Why cough is not going away persistent cough?", "text": "A cough that does not go away (lasting more than 3 weeks) can be caused by: post-nasal drip, asthma, acid reflux (GERD), chronic bronchitis, TB, or in rare cases lung cancer. Smoking is a major cause. You should see a doctor for proper diagnosis if your cough persists.", "category": "Infectious Disease", "url": ""},
  {"title": "What is anemia?", "text": "Anemia is a condition where you don't have enough healthy red blood cells to carry adequate oxygen to your body's tissues. It causes fatigue, weakness, pale skin, and shortness of breath. Iron deficiency is the most common cause. Treatment depends on the type and cause.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of anemia?", "text": "Anemia symptoms include: fatigue and weakness, pale or yellowish skin, irregular heartbeat, shortness of breath, dizziness or lightheadedness, chest pain, cold hands and feet, and headaches. Severe anemia can cause heart problems.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What is thyroid disease?", "text": "Thyroid disease occurs when the thyroid gland produces too much (hyperthyroidism) or too little (hypothyroidism) thyroid hormone. It affects metabolism, energy levels, and many body functions. It is more common in women. Treatment includes medication and sometimes surgery.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of thyroid?", "text": "Hypothyroidism symptoms: fatigue, weight gain, cold sensitivity, constipation, dry skin, and depression. Hyperthyroidism symptoms: weight loss, rapid heartbeat, sweating, nervousness, and tremors. Both conditions require medical diagnosis and treatment.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What is migraine?", "text": "A migraine is a severe headache often accompanied by nausea, vomiting, and sensitivity to light and sound. It can last hours to days. Triggers include stress, certain foods, hormonal changes, and lack of sleep. Migraines are more common in women.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What are symptoms of migraine?", "text": "Migraine symptoms include: throbbing or pulsing pain usually on one side of the head, nausea and vomiting, sensitivity to light and sound, and visual disturbances (aura) before the headache. Pain can be severe enough to interfere with daily activities.", "category": "Non-communicable Disease", "url": ""},
  {"title": "What is appendicitis?", "text": "Appendicitis is inflammation of the appendix, a small pouch attached to the large intestine. It causes severe abdominal pain, nausea, vomiting, and fever. It is a medical emergency requiring immediate surgery. If untreated, the appendix can burst causing life-threatening infection.", "category": "Infectious Disease", "url": ""},
  {"title": "What are symptoms of appendicitis?", "text": "Appendicitis symptoms include: sudden pain that begins around the navel and shifts to the lower right abdomen, pain that worsens with movement, nausea and vomiting, loss of appetite, low-grade fever, and bloating. Seek emergency medical care immediately if you suspect appendicitis.", "category": "Infectious Disease", "url": ""},
]

with open("data/health_knowledge.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

# Prepend new entries
combined = NEW_ENTRIES + existing

with open("data/health_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)

content = json.dumps(combined, indent=2, ensure_ascii=False).encode("utf-8")
new_hash = hashlib.sha256(content).hexdigest()
with open("data/health_knowledge.ledger", "w", encoding="utf-8") as f:
    f.write(new_hash)

print(f"Done. Total: {len(combined)} items. Hash: {new_hash}")
