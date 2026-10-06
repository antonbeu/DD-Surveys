#!/usr/bin/env python3
import json
import os
import requests
from base64 import b64encode
from collections import defaultdict, Counter
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from datetime import datetime

API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

DATE_FROM = "2026-09-28"
DATE_TO = "2026-10-02"
WEEK_NUM = "40"

def umlaut_slug(text):
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'ê': 'e', 'É': 'E', 'á': 'a', 'à': 'a', 'â': 'a',
        '👻': '', '👽': '', '🐶': ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = ''.join(c if c.isalnum() or c in ' -.' else '' for c in text)
    return text.strip()

def leader_slug(name):
    if not name:
        return 'Unknown'
    if '(' in name:
        name = name.split('(')[0].strip()

    if 'Brot für die Welt' in name or 'brot' in name.lower():
        return 'BrotWelt'

    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}-{parts[0]}"
    return name.strip()

def fetch_responses(collector_id):
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses'
    params = {
        'started_on[from]': DATE_FROM,
        'started_on[to]': DATE_TO
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
    questions = []

    if not responses:
        return questions

    # Get first response to determine all questions
    sample = fetch_response_details(responses[0]['response_id'])
    if 'answers' not in sample:
        return questions

    # Build map of all questions
    q_map = {}
    for answer in sample['answers']:
        q_text = answer.get('question_text', 'Unknown')
        q_type = answer.get('type', '')
        element_id = answer.get('element_id')
        if q_text and element_id not in q_map:
            q_map[element_id] = {
                'text': q_text,
                'type': q_type,
                'element_id': element_id,
                'ratings': [],
                'choices': [],
                'texts': []
            }

    # Aggregate data from all responses
    for resp in responses:
        details = fetch_response_details(resp['response_id'])
        if 'answers' not in details:
            continue
        for answer in details['answers']:
            element_id = answer.get('element_id')
            if element_id not in q_map:
                continue

            answer_type = answer.get('type', '')
            if answer_type == 'number':
                value = answer.get('number')
                if value is not None:
                    q_map[element_id]['ratings'].append(int(value))
            elif answer_type == 'choices':
                choices = answer.get('choices', [])
                for choice in choices:
                    label = choice.get('label', '')
                    if label:
                        q_map[element_id]['choices'].append(label)
            elif answer_type == 'text':
                value = answer.get('text', '')
                if value:
                    q_map[element_id]['texts'].append(value)

    return sorted(q_map.values(), key=lambda x: x['element_id'])

def draw_bar_chart(ratings, filename):
    if not ratings:
        return None

    counts = Counter(ratings)
    labels = sorted(counts.keys())
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(5, 2.5), dpi=100)
    bars = ax.bar([str(l) for l in labels], values, color='#2E86AB', edgecolor='#1F4D7B', linewidth=1.5)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    avg = sum(ratings) / len(ratings) if ratings else 0
    ax.set_ylabel('Anzahl', fontsize=10)
    ax.set_xlabel(f'Bewertung (Ø: {avg:.1f})', fontsize=9)
    ax.set_ylim(0, max(values) * 1.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()
    return filename

def create_pdf(course_title, leader_name, collector_id, responses):
    if not responses:
        return None

    filename = f"output/KW{WEEK_NUM}/{umlaut_slug(leader_slug(leader_name))}_KW{WEEK_NUM}_{umlaut_slug(course_title)}.pdf"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm,
                           topMargin=1*cm, bottomMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=8,
        alignment=1,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=6,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4
    )

    # Title
    story.append(Paragraph(course_title, title_style))
    story.append(Spacer(1, 0.4*cm))

    # Metadata
    meta = f"<b>Zeitraum:</b> {DATE_FROM} bis {DATE_TO} | <b>Antworten:</b> {len(responses)}"
    story.append(Paragraph(meta, normal_style))
    story.append(Spacer(1, 0.6*cm))

    # Questions and answers
    questions = aggregate_by_question(responses)

    for q in questions:
        q_text = q['text']
        ratings = q['ratings']
        choices = q['choices']
        texts = q['texts']

        # Question heading
        story.append(Paragraph(q_text, heading_style))

        # Ratings chart
        if ratings:
            chart_file = f"/tmp/chart_{collector_id}_{q['element_id']}.png"
            if draw_bar_chart(ratings, chart_file):
                try:
                    img = Image(chart_file, width=4.5*inch, height=2*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*cm))
                except:
                    pass

        # Choice counts
        if choices:
            choice_counts = Counter(choices)
            for choice, count in choice_counts.most_common():
                story.append(Paragraph(f"• {choice}: {count}x", normal_style))
            story.append(Spacer(1, 0.3*cm))

        # Text answers
        if texts:
            story.append(Paragraph("<b>Kommentare:</b>", ParagraphStyle(
                'CommentHeader',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                spaceAfter=4
            )))
            for text in texts[:5]:
                text_clean = text.replace('<', '&lt;').replace('>', '&gt;')[:250]
                story.append(Paragraph(f"→ {text_clean}", normal_style))
            story.append(Spacer(1, 0.4*cm))

    try:
        doc.build(story)
        return filename
    except Exception as e:
        print(f"  Error: {e}")
        return None

print("Loading mapping...")
with open('kw40_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print(f"Generating PDFs for {len(mapping['confirmed'])} courses...\n")

generated = 0
failed = 0

for course_title, info in mapping['confirmed'].items():
    collector_id = info['collector_id']
    leader = info['leader']

    print(f"Processing: {course_title}...", end=' ', flush=True)

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
