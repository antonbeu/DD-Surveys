#!/usr/bin/env python3
import json
import os
import requests
from base64 import b64encode
from collections import defaultdict
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

DATE_FROM = "2026-09-28T00:00:00Z"
DATE_TO = "2026-10-02T23:59:59Z"
WEEK_NUM = "40"

def umlaut_slug(text):
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'ê': 'e', 'É': 'E', 'á': 'a', 'à': 'a', 'â': 'a',
        '👻': '', '👽': '', '🐶': ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove other special chars except space and hyphen
    text = ''.join(c if c.isalnum() or c in ' -.' else '' for c in text)
    return text.strip()

def leader_slug(name):
    if not name:
        return 'Unknown'
    # Check if it's an organization (no clear first/last name pattern)
    if '(' in name:
        name = name.split('(')[0].strip()

    # Check for known organizations
    if 'Brot für die Welt' in name or 'brot' in name.lower():
        return 'BrotWelt'

    parts = name.strip().split()
    if len(parts) >= 2:
        # Standard LastName-FirstName format
        return f"{parts[-1]}-{parts[0]}"
    return name.strip()

def get_leader_first_name(name):
    if not name:
        return ''
    parts = name.split('(')[0].strip().split()
    return parts[0] if parts else ''

def fetch_responses(collector_id):
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses'
    params = {
        'started_on[from]': DATE_FROM.split('T')[0],
        'started_on[to]': DATE_TO.split('T')[0]
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        all_responses = resp.json().get('responses', [])
        return [r for r in all_responses if r.get('collector_id') == collector_id]
    except:
        return []

def fetch_response_details(response_id):
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses/{response_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        return resp.json()
    except:
        return {}

def aggregate_by_question(responses):
    questions = defaultdict(lambda: {'ratings': [], 'choices': [], 'texts': []})

    for resp in responses:
        details = fetch_response_details(resp['response_id'])
        if 'answers' not in details:
            continue
        for answer in details['answers']:
            q = answer.get('question', 'Unknown')
            value = answer.get('value', '')
            if answer.get('answer_type') == 'rating':
                try:
                    questions[q]['ratings'].append(int(value))
                except:
                    pass
            elif answer.get('answer_type') in ['radio', 'checkbox']:
                if value:
                    questions[q]['choices'].append(value)
            elif answer.get('answer_type') == 'text':
                if value:
                    questions[q]['texts'].append(value)

    return questions

def draw_bar_chart(ratings, filename):
    if not ratings:
        return None

    from collections import Counter
    counts = Counter(ratings)
    labels = sorted(counts.keys())
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(6, 2), dpi=100)
    bars = ax.bar([str(l) for l in labels], values, color='#2E86AB', width=0.6)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)

    ax.set_ylabel('Count', fontsize=9)
    ax.set_ylim(0, max(values) * 1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()
    return filename

def create_pdf(course_title, leader_name, collector_id, responses):
    if not responses:
        return None

    filename = f"output/KW{WEEK_NUM}/{umlaut_slug(leader_slug(leader_name))}_KW{WEEK_NUM}_{umlaut_slug(course_title)}.pdf"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=0.75*cm, leftMargin=0.75*cm,
                           topMargin=0.75*cm, bottomMargin=0.75*cm)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1F4D7B'), spaceAfter=6,
                                 alignment=1)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=11,
                                   textColor=colors.HexColor('#2E86AB'), spaceAfter=4)

    story.append(Paragraph(course_title, title_style))
    story.append(Spacer(1, 0.3*cm))

    meta = f"<b>Zeitraum:</b> 28.09.2026 - 02.10.2026 | <b>Antworten:</b> {len(responses)}"
    story.append(Paragraph(meta, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    questions = aggregate_by_question(responses)

    for q_text, answers in list(questions.items())[:10]:
        if answers['ratings']:
            story.append(Paragraph(q_text, heading_style))
            chart_file = f"/tmp/chart_{collector_id}_{hash(q_text)}.png"
            draw_bar_chart(answers['ratings'], chart_file)
            if os.path.exists(chart_file):
                img = Image(chart_file, width=4*inch, height=1.5*inch)
                story.append(img)
            story.append(Spacer(1, 0.3*cm))

        if answers['texts']:
            story.append(Paragraph(f"<b>{q_text}</b> - Kommentare:", heading_style))
            for text in answers['texts'][:3]:
                story.append(Paragraph(f"• {text[:200]}...", styles['Normal']))
            story.append(Spacer(1, 0.3*cm))

    try:
        doc.build(story)
        return filename
    except Exception as e:
        print(f"Error generating PDF for {course_title}: {e}")
        return None

print("Loading mapping...")
with open('kw40_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print(f"Generating PDFs for {len(mapping['confirmed'])} courses...\n")

auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

generated = 0
failed = 0

for course_title, info in mapping['confirmed'].items():
    collector_id = info['collector_id']
    leader = info['leader']

    print(f"Processing: {course_title}...", end=' ')

    responses = fetch_responses(collector_id)

    if not responses:
        print("❌ No responses")
        failed += 1
        continue

    pdf_file = create_pdf(course_title, leader, collector_id, responses)

    if pdf_file:
        print(f"✓ ({len(responses)} responses)")
        generated += 1
    else:
        print("❌ PDF generation failed")
        failed += 1

print(f"\n{'='*80}")
print(f"Generated: {generated} PDFs")
print(f"Failed: {failed}")
print(f"Total: {generated + failed}")
