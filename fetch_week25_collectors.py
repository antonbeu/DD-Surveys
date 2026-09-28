#!/usr/bin/env python3
import csv
import json
import requests
from base64 import b64encode
from difflib import SequenceMatcher
from datetime import datetime

# API Credentials
API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# Date range for this week (Sept 21-25, 2026)
DATE_FROM = "2026-09-21T00:00:00+00:00"
DATE_TO = "2026-09-25T23:59:59+00:00"

# Fetch responses to find which collectors have responses this week
print("Fetching responses for this week (Sept 21-25)...")
auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

active_collector_ids = set()
page = 1

while True:
    try:
        url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses?page={page}&limit=100&started_on[from]={DATE_FROM}&started_on[to]={DATE_TO}'
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"API error: {resp.status_code}")
            break

        data = resp.json()
        responses = data.get('responses') or data.get('data') or []

        if not responses:
            break

        for response in responses:
            if 'collector_id' in response:
                active_collector_ids.add(response['collector_id'])

        print(f"  Page {page}: {len(responses)} responses, {len(active_collector_ids)} active collectors so far")

        if len(responses) < 100:
            break
        page += 1
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"✓ Found {len(active_collector_ids)} active collectors with responses this week")

# Now fetch these specific collectors
collectors_full = []
for collector_id in sorted(active_collector_ids):
    try:
        url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/collectors/{collector_id}'
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            collector = resp.json()
            collectors_full.append(collector)
        else:
            print(f"Could not fetch collector {collector_id}: {resp.status_code}")
    except Exception as e:
        print(f"Error fetching collector {collector_id}: {e}")

print(f"✓ Fetched {len(collectors_full)} collectors")

# Save to file
with open('collectors_full.json', 'w') as f:
    json.dump(collectors_full, f, indent=2, ensure_ascii=False)
print(f"✓ Saved to collectors_full.json")

# Parse courses from CSV
csv_file = '/root/.claude/uploads/6ffeaf5f-3332-5ad0-9338-47f78b6cac3f/26cd7c49-Export_20260925.csv'

courses = []
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    lines = [line.rstrip('\r\n') for line in f]

    header_idx = None
    for i, line in enumerate(lines):
        if '"Titel"' in line:
            header_idx = i
            break

    if header_idx is None:
        print("Could not find header row")
        exit(1)

    reader = csv.DictReader(lines[header_idx:], delimiter=';')
    for row in reader:
        titel = row.get('Titel')
        status = row.get('Status')

        if titel is None or status is None:
            continue

        title = titel.strip().strip('"')
        status_clean = status.strip().strip('"')

        if title and status_clean == 'stattgefunden':
            courses.append(title)

print(f"✓ Parsed {len(courses)} courses from CSV")

# Match courses to collectors
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

mapping = []
unclear = []

for course in courses:
    best_match = None
    best_score = 0

    for collector in collectors_full:
        coll_name = collector.get('name', '')
        score = similarity(course, coll_name)

        if score > best_score:
            best_score = score
            best_match = collector

    if best_match and best_score > 0.85:
        mapping.append({
            'course': course,
            'collector_id': best_match.get('collector_id'),
            'collector_name': best_match.get('name'),
            'score': best_score
        })
    else:
        unclear.append({
            'course': course,
            'best_match': best_match.get('name') if best_match else 'N/A',
            'score': best_score if best_match else 0
        })

print("\n" + "="*80)
print("MATCHES (confidence > 85%):")
print("="*80)
for m in mapping:
    print(f"✓ {m['course']} → {m['collector_name']} ({m['collector_id']}) [{m['score']:.0%}]")

if unclear:
    print("\n" + "="*80)
    print("UNCLEAR MAPPINGS (need confirmation):")
    print("="*80)
    for u in unclear:
        print(f"❓ {u['course']}")
        if u['best_match'] != 'N/A':
            print(f"   Best guess: {u['best_match']} [{u['score']:.0%}]")
        else:
            print(f"   No collector found")

# Save mapping
with open('week25_mapping.json', 'w') as f:
    json.dump({
        'confirmed': mapping,
        'unclear': unclear,
        'total_courses': len(courses)
    }, f, indent=2, ensure_ascii=False)

print(f"\n📊 Summary: {len(mapping)} confirmed, {len(unclear)} unclear out of {len(courses)} courses")
print(f"✓ Mapping saved to week25_mapping.json")
