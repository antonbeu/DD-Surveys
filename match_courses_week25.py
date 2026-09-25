#!/usr/bin/env python3
import csv
import json
import os
from difflib import SequenceMatcher
import requests
from base64 import b64encode

# Read CSV
csv_file = '/root/.claude/uploads/6ffeaf5f-3332-5ad0-9338-47f78b6cac3f/26cd7c49-Export_20260925.csv'

courses = []
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    lines = [line.rstrip('\r\n') for line in f]

    # Find header row
    header_idx = None
    for i, line in enumerate(lines):
        if '"Titel"' in line:
            header_idx = i
            break

    if header_idx is None:
        print("Could not find header row")
    else:
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

print(f"Found {len(courses)} courses:")
for i, course in enumerate(courses, 1):
    print(f"{i}. {course}")

# Fetch collectors from API
api_user = os.environ.get('SURVEYHERO_API_USER', '')
api_pass = os.environ.get('SURVEYHERO_API_PASS', '')

if not api_user or not api_pass:
    print("\n⚠️  No API credentials found. Please provide SURVEYHERO_API_USER and SURVEYHERO_API_PASS.")
    print("Using course titles only for display.")
    collectors_full = []
else:
    auth = b64encode(f"{api_user}:{api_pass}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

    collectors_full = []
    page = 1
    while True:
        try:
            resp = requests.get(
                f'https://api.surveyhero.com/v1/surveys/123456/collectors?page={page}&limit=100',
                headers=headers,
                timeout=10
            )
            if resp.status_code == 401:
                print("❌ API authentication failed")
                break
            if resp.status_code != 200:
                print(f"⚠️  API error: {resp.status_code}")
                break

            data = resp.json()
            if not data.get('data'):
                break

            collectors_full.extend(data['data'])
            if len(data['data']) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching collectors: {e}")
            break

    print(f"\nFetched {len(collectors_full)} collectors from API")

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
            'score': best_score
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

# Save mapping for later use
with open('/tmp/week25_mapping.json', 'w') as f:
    json.dump({
        'confirmed': mapping,
        'unclear': unclear,
        'total_courses': len(courses)
    }, f, indent=2, ensure_ascii=False)

print(f"\n📊 Summary: {len(mapping)} confirmed, {len(unclear)} unclear out of {len(courses)} courses")
