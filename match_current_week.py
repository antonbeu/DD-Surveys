#!/usr/bin/env python3
import json
import requests
from base64 import b64encode
from difflib import SequenceMatcher

API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

COURSES = [
    {"course": "Psycho-Detektiv:innen & Lerntricks", "leader": "Klarissa Jarck (Uni Marburg)"},
    {"course": "Kühler Kopf in hitzigen Krisen", "leader": "Klarissa Jarck (Uni Marburg)"},
    {"course": "Brückenbau", "leader": "Brot für die Welt"},
    {"course": "Japan Quest: Naruto, Language & Legends", "leader": "Brot für die Welt"},
    {"course": "Save the City: A climate detective game", "leader": "Brot für die Welt"},
    {"course": "👻 Geisterschule", "leader": "Vera Garasenko"},
    {"course": "Die Welt in den Händen", "leader": "Tobias Litterst"},
    {"course": "Die Logik des Unsichtbaren", "leader": "Silvia Silva"},
    {"course": "Yogareise zu Hexen, Vampiren und Co.", "leader": "Marthe Brand"},
    {"course": "Gibt es Aliens? 👽", "leader": "Markus Paul"},
    {"course": "Himmelsscheibe von Nebra", "leader": "Markus Paul"},
    {"course": "Sterne, Galaxien und Nebel", "leader": "Markus Paul"},
    {"course": "Können Tiere die Uhr lesen?", "leader": "Julia Blüher"},
    {"course": "Hunde - Supernasen!", "leader": "Julia Blüher"},
    {"course": "Mein Haustier und ich", "leader": "Julia Blüher"},
    {"course": "Titanoboa and the jungle of El Cerrejón", "leader": "Elihu Guzman"},
    {"course": "The lost German rainforest", "leader": "Elihu Guzman"},
    {"course": "Buchstaben-Puzzle", "leader": "Dominik Schirra"},
    {"course": "Mathe MAL anders", "leader": "Dominik Schirra"},
    {"course": "Die Geheimschrift der Freimaurer", "leader": "Dominik Schirra"},
    {"course": "Pizza-Cards selbst gestalten", "leader": "Dominik Schirra"},
    {"course": "Dein Start mit Java", "leader": "David Heyer"},
    {"course": "Vom Bild zur Geschichte", "leader": "Cora Remmert"},
    {"course": "Pokémon inspiriertes Schreibcamp", "leader": "Cora Remmert"},
    {"course": "Es war einmal...", "leader": "Cora Remmert"},
    {"course": "The amazing brain", "leader": "Carolina Espinosa"},
]

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

print("Fetching collectors...")
auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

collectors = []
page = 1

while True:
    try:
        url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/collectors?page={page}&limit=100'
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            break
        data = resp.json()
        collectors_list = data.get('collectors', [])
        if not collectors_list:
            break
        collectors.extend(collectors_list)
        print(f"  Page {page}: {len(collectors_list)} collectors")
        if len(collectors_list) < 100:
            break
        page += 1
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"✓ Loaded {len(collectors)} collectors\n")

# Match courses to collectors
mapping = {}
unclear = []

for course_data in COURSES:
    course_name = course_data['course']
    best_match = None
    best_score = 0

    for collector in collectors:
        coll_name = collector.get('name', '')
        score = similarity(course_name, coll_name)

        if score > best_score:
            best_score = score
            best_match = collector

    if best_match and best_score > 0.85:
        mapping[course_name] = {
            'collector_id': best_match.get('collector_id'),
            'collector_name': best_match.get('name'),
            'score': best_score
        }
        print(f"✓ {course_name}")
        print(f"  → {best_match.get('name')} ({best_score:.0%})")
    else:
        unclear.append({
            'course': course_name,
            'best_match': best_match.get('name') if best_match else 'N/A',
            'score': best_score if best_match else 0
        })
        print(f"❓ {course_name}")
        if best_match:
            print(f"  Best: {best_match.get('name')} ({best_score:.0%})")

print(f"\n{'='*80}")
print(f"SUMMARY: {len(mapping)} matched, {len(unclear)} unclear\n")

if unclear:
    print("UNCLEAR MATCHES - NEED YOUR INPUT:")
    print("="*80)
    for u in unclear:
        print(f"\n❓ {u['course']}")
        if u['best_match'] != 'N/A':
            print(f"   Best guess: {u['best_match']} ({u['score']:.0%})")
            print(f"   Accept? (y/n/collector_id): ", end='', flush=True)
        else:
            print(f"   No collector found")
            print(f"   Collector ID: ", end='', flush=True)

# Save mapping
with open('current_week_mapping.json', 'w') as f:
    json.dump({
        'confirmed': mapping,
        'unclear': unclear,
        'total_courses': len(COURSES)
    }, f, indent=2, ensure_ascii=False)

print(f"\n✓ Mapping saved to current_week_mapping.json")
