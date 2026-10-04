#!/usr/bin/env python3
import json
import requests
from base64 import b64encode

API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

DATE_FROM = "2026-09-28T00:00:00+00:00"
DATE_TO = "2026-10-02T23:59:59+00:00"

print("Fetching collectors with responses in current week...")

auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

collectors = []
page = 1

while True:
    try:
        url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses?page={page}&limit=100&started_on[from]={DATE_FROM}&started_on[to]={DATE_TO}'
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"API error: {resp.status_code}")
            break

        data = resp.json()
        responses_list = data.get('responses', [])

        if not responses_list:
            break

        # Extract unique collector IDs
        for r in responses_list:
            collector_id = r.get('collector_id')
            if collector_id:
                collectors.append(collector_id)

        print(f"  Page {page}: found {len(responses_list)} responses")

        if len(responses_list) < 100:
            break

        page += 1
    except Exception as e:
        print(f"Error: {e}")
        break

# Remove duplicates
collectors = list(set(collectors))
print(f"\n✓ Found {len(collectors)} unique collectors with responses")

# Now fetch details for each collector
print("Fetching collector details...")
collector_details = []

for i, collector_id in enumerate(collectors):
    try:
        url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/collectors/{collector_id}'
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            collector_details.append(data)
            print(f"  {data.get('name')} (ID: {collector_id})")
    except Exception as e:
        pass

print(f"\n✓ Fetched {len(collector_details)} collector details")

# Save
with open('collectors_current_week.json', 'w') as f:
    json.dump(collector_details, f, indent=2, ensure_ascii=False)

print("✓ Saved to collectors_current_week.json")
