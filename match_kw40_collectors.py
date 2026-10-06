#!/usr/bin/env python3
import json
import requests
import csv
from base64 import b64encode
from difflib import SequenceMatcher
from io import StringIO

API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# CSV data embedded
CSV_DATA = """Titel;Labels;Status;Zugewiesen;Fällig bis;von ... bis .../ Bsp. 10:00 - 11:30 Uhr;👩‍💻Kursleitung (stamm);⏺️ Kursformat;✅#Plätze;✅# Anmeldungen;✅# Besucht?
stattgefunden;
Psycho-Detektiv:innen & Lerntricks;EMAIL;stattgefunden;;2026-09-29 11:30;11:30 - 13:00 Uhr;Klarissa Jarck (Uni Marburg);Inspiration;15;8;
Kühler Kopf in hitzigen Krisen;EMAIL;stattgefunden;;2026-09-28 11:30;11:30 - 13:00 Uhr;Klarissa Jarck (Uni Marburg);Inspiration;15;8;
Brückenbau;EMAIL;stattgefunden;;2026-10-01 09:00;09:00 - 10:00 Uhr;Brot für die Welt;Inspiration;15;6;6
Japan Quest: Naruto, Language & Legends;EMAIL;stattgefunden;;2026-09-28 16:00;16:00 - 17:15 Uhr;Brot für die Welt;Inspiration;15;13;10
Save the City: A climate detective game;;stattgefunden;;2026-10-01 16:00;16:00 - 17:00 Uhr;Brot für die Welt;Inspiration;15;10;7
👻 Geisterschule;EMAIL;stattgefunden;;2026-09-28 17:00;17:00 - 18:30 Uhr;Vera Garasenko;Inspiration;19;19;14
Die Welt in den Händen;EMAIL;stattgefunden;;2026-10-01 14:00;14:00 - 15:15 Uhr;Tobias Litterst;Inspiration;15;14;
Die Logik des Unsichtbaren;EMAIL;stattgefunden;;2026-09-29 10:00;10:00 - 11:15 Uhr;Silvia Silva;Inspiration;18;18;13
Yogareise zu Hexen, Vampiren und Co.;EMAIL;stattgefunden;;2026-10-02 15:00;15:00 - 16:00 Uhr;Marthe Brand;Inspiration;15;14;11
Gibt es Aliens? 👽;EMAIL;stattgefunden;;2026-10-02 13:30;13:30 - 15:00 Uhr;Markus Paul;Inspiration;25;25;16
Himmelsscheibe von Nebra;EMAIL;stattgefunden;;2026-09-29 14:00;14:00 - 15:30 Uhr;Markus Paul;Inspiration;15;10;8
Sterne, Galaxien und Nebel;EMAIL;stattgefunden;;2026-10-01 10:00;10:00 - 11:30 Uhr;Markus Paul;Inspiration;22;22;8
Können Tiere die Uhr lesen?;EMAIL;stattgefunden;;2026-09-29 11:00;11:00 - 12:00 Uhr;Julia Blüher;Inspiration;15;15;9
Hunde - Supernasen!;EMAIL;stattgefunden;;2026-09-30 09:00;09:00 - 10:00 Uhr;Julia Blüher;Inspiration;18;18;8
Mein Haustier und ich;EMAIL;stattgefunden;;2026-10-01 11:00;11:00 - 12:00 Uhr;Julia Blüher;Inspiration;15;15;5
Titanoboa and the jungle of El Cerrejón;EMAIL;stattgefunden;;2026-09-28 16:30;16:30 - 18:00 Uhr;Elihu Guzman;Inspiration;15;9;4
The lost German rainforest;EMAIL;stattgefunden;;2026-10-02 16:30;16:30 - 18:00 Uhr;Elihu Guzman;Inspiration;15;7;4
Buchstaben-Puzzle;EMAIL;stattgefunden;;2026-10-01 10:00;10:00 - 11:30 Uhr;Dominik Schirra;Inspiration;15;15;
Mathe MAL anders;EMAIL;stattgefunden;;2026-09-28 10:00;10:00 - 11:30 Uhr;Dominik Schirra;Inspiration;19;19;11
Die Geheimschrift der Freimaurer;EMAIL;stattgefunden;;2026-09-29 10:00;10:00 - 11:30 Uhr;Dominik Schirra;Inspiration;15;11;9
Pizza-Cards selbst gestalten;EMAIL;stattgefunden;;2026-09-30 10:00;10:00 - 11:30 Uhr;Dominik Schirra;Inspiration;15;13;
Dein Start mit Java;EMAIL;stattgefunden;;2026-10-02 10:00;10:00 - 11:15 Uhr;David Heyer;Inspiration;15;17;12
Vom Bild zur Geschichte;EMAIL;stattgefunden;;2026-09-28 10:30;10:30 - 12:00 Uhr;Cora Remmert;Inspiration;15;11;7
Pokémon inspiriertes Schreibcamp;EMAIL;stattgefunden;;2026-09-29 10:30;10:30 - 12:00 Uhr;Cora Remmert;Inspiration;17;17;15
Es war einmal...;EMAIL;stattgefunden;;2026-09-30 10:30;10:30 - 12:00 Uhr;Cora Remmert;Inspiration;16;16;11
The amazing brain;EMAIL;stattgefunden;;2026-09-28 12:00;12:00 - 13:15 Uhr;Carolina Espinosa;Inspiration;15;8;6
"""

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

print("Parsing CSV...")
reader = csv.DictReader(StringIO(CSV_DATA), delimiter=';')
courses = []
for row in reader:
    if row.get('Titel', '').strip() and row['Status'] == 'stattgefunden':
        courses.append({
            'title': row['Titel'].strip().strip('"'),
            'leader': row['👩‍💻Kursleitung (stamm)'].strip() if row.get('👩‍💻Kursleitung (stamm)') else ''
        })

print(f"Found {len(courses)} courses\n")

print("Fetching collectors from API...")
auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}
url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/collectors'
resp = requests.get(url, headers=headers, timeout=30)
collectors = resp.json().get('collectors', [])
print(f"✓ Loaded {len(collectors)} collectors\n")

# Match courses to collectors
print("Matching courses to collectors...\n")
mapping = {'confirmed': {}, 'unclear': []}

# Manual overrides for unclear matches (from user)
manual_mappings = {
    'Mars: more than a red planet': 2000940,
    'Abenteuer Arktis & Antarktis': 1815081,
    None: 1815170,  # placeholder
    'Mathebabylon': 2078956,
}

for course in courses:
    title = course['title']
    best_match = None
    best_score = 0

    for collector in collectors:
        coll_name = collector.get('name', '')
        score = similarity(title, coll_name)
        if score > best_score:
            best_score = score
            best_match = collector

    if best_score > 0.70:
        mapping['confirmed'][title] = {
            'collector_id': best_match['collector_id'],
            'collector_name': best_match['name'],
            'leader': course['leader'],
            'score': round(best_score, 2)
        }
        print(f"✓ {title}")
        print(f"  → {best_match['name']} ({best_score:.0%})")
    else:
        mapping['unclear'].append({
            'course': title,
            'leader': course['leader'],
            'best_match': best_match['name'] if best_match else 'N/A',
            'score': round(best_score, 2) if best_match else 0
        })
        print(f"❓ {title}")
        if best_match:
            print(f"   Best: {best_match['name']} ({best_score:.0%})")

print(f"\n{'='*80}")
print(f"SUMMARY: {len(mapping['confirmed'])} confirmed, {len(mapping['unclear'])} unclear\n")

# Save mapping
with open('kw40_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print("✓ Mapping saved to kw40_mapping.json")
