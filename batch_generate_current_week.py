#!/usr/bin/env python3
import json
import os
import requests
from base64 import b64encode
from collections import defaultdict, Counter
from io import BytesIO
from difflib import SequenceMatcher
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors

# API Credentials
API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# Date range for current week (Sept 28 - Oct 2, 2026)
DATE_FROM = "2026-09-28T00:00:00+00:00"
DATE_TO = "2026-10-02T23:59:59+00:00"

# Courses from CSV
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

def leader_slug(name):
    """Convert 'Dominik Schirra' to 'Schirra-Dominik'"""
    if not name or name == "Unknown":
        return "Unknown"
    # Remove organization name if present
    name = name.split('(')[0].strip()
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}-{' '.join(parts[:-1])}"

def umlaut_slug(text):
    """Replace umlauts for filenames"""
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    text = text.replace('ß', 'ss')
    text = text.replace('👻', '').replace('👽', '').replace('🌱', '').replace('🚀', '').replace('⚔️', '')
    return text.strip()

def similarity(a, b):
    """Calculate string similarity"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fetch_all_collectors():
    """Fetch all collectors from API"""
    collectors = []
    page = 1
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

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
            if len(collectors_list) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching collectors: {e}")
            break

    return collectors

def match_courses_to_collectors(collectors):
    """Match courses to collector IDs by name similarity"""
    mapping = {}

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

        if best_match and best_score > 0.6:
            mapping[course_name] = {
                'collector_id': best_match.get('collector_id'),
                'score': best_score
            }
            print(f"✓ {course_name} → {best_match.get('name')} ({best_score:.0%})")
        else:
            print(f"❓ {course_name} (no good match)")

    return mapping

def fetch_responses(collector_id):
    """Fetch full response details for a collector"""
    response_ids = []
    page = 1
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

    while True:
        try:
            url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses?collector_id={collector_id}&page={page}&limit=100&started_on[from]={DATE_FROM}&started_on[to]={DATE_TO}'
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                break
            data = resp.json()
            responses_list = data.get('responses', [])
            if not responses_list:
                break
            for r in responses_list:
                response_ids.append(r.get('response_id'))
            if len(responses_list) < 100:
                break
            page += 1
        except Exception as e:
            break

    responses = []
    for response_id in response_ids:
        try:
            url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses/{response_id}'
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                responses.append(resp.json())
        except Exception as e:
            pass

    return responses

def aggregate_by_question(responses):
    """Group answers by question"""
    questions = {}

    for resp in responses:
        answers = resp.get('answers', [])
        for answer in answers:
            element_id = answer.get('element_id')
            question_text = answer.get('question_text', '')
            answer_type = answer.get('type')

            if not element_id:
                continue

            if element_id not in questions:
                questions[element_id] = {
                    'text': question_text,
                    'type': answer_type,
                    'ratings': [],
                    'choices': defaultdict(int),
                    'texts': []
                }

            if answer_type == 'number':
                if answer.get('number') is not None:
                    questions[element_id]['ratings'].append(answer['number'])
            elif answer_type == 'text':
                if answer.get('text'):
                    questions[element_id]['texts'].append(answer['text'])
            elif answer_type == 'choices':
                for choice in answer.get('choices', []):
                    label = choice.get('label', '')
                    if label:
                        questions[element_id]['choices'][label] += 1
                        questions[element_id]['texts'].append(label)

    return questions

def draw_bar_chart(ratings):
    """Create bar chart for ratings"""
    if not ratings:
        return None

    counts = Counter(int(r) for r in ratings if isinstance(r, (int, float)))
    if not counts:
        return None

    labels = sorted(counts.keys())
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(7, 1.8), dpi=100)
    bars = ax.bar(labels, values, color='#2E86AB', edgecolor='#1F4D7B', alpha=0.8, width=0.6)

    ax.set_xlabel('Rating', fontsize=9)
    ax.set_ylabel('Count', fontsize=9)
    ax.set_xticks(labels)
    ax.set_xticklabels(labels)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max(values) * 1.2)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf

def create_pdf(course_name, leader_name, collector_id, responses):
    """Create PDF report"""
    os.makedirs('output/current-week', exist_ok=True)

    leader_slug_name = leader_slug(leader_name)
    course_slug = umlaut_slug(course_name)
    pdf_filename = f"output/current-week/{leader_slug_name}_currentweek_{course_slug}.pdf"

    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )

    q_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )

    text_style = ParagraphStyle(
        'TextResp',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        leftIndent=15
    )

    story.append(Paragraph(f"<b>{course_name}</b>", title_style))
    story.append(Spacer(1, 0.2*cm))

    meta_text = f"<font size=9>September 28 - October 2, 2026 | Antworten: {len(responses)}</font>"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 0.4*cm))

    questions = aggregate_by_question(responses)

    for element_id in sorted(questions.keys()):
        q = questions[element_id]
        q_text = q['text']

        story.append(Paragraph(q_text, q_style))

        if q['ratings']:
            avg = sum(q['ratings']) / len(q['ratings'])
            story.append(Paragraph(f"<font size=8><i>Average: {avg:.1f}/5</i></font>", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))

            chart_buf = draw_bar_chart(q['ratings'])
            if chart_buf:
                img = Image(chart_buf, width=6*cm, height=1.8*cm)
                story.append(img)
                story.append(Spacer(1, 0.3*cm))

        if q['texts']:
            text_responses = []
            for text in q['texts']:
                if q['type'] == 'text' or (q['type'] == 'choices' and text not in q['choices']):
                    text_responses.append(text)

            if not text_responses and q['type'] == 'choices':
                text_responses = list(q['texts'][:5])

            if text_responses:
                for i, text in enumerate(text_responses[:5]):
                    text_short = text[:150]
                    if len(text) > 150:
                        text_short += "..."
                    story.append(Paragraph(f"• {text_short}", text_style))

                story.append(Spacer(1, 0.4*cm))

    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

# Main
print("Fetching collectors from API...")
collectors = fetch_all_collectors()
print(f"✓ Fetched {len(collectors)} collectors\n")

print("Matching courses to collectors...")
mapping = match_courses_to_collectors(collectors)
print(f"\n✓ Matched {len(mapping)} courses\n")

print("Generating PDFs...\n")
success_count = 0

for course_data in COURSES:
    course_name = course_data['course']
    leader_name = course_data['leader']

    if course_name not in mapping:
        print(f"Skipping: {course_name} (no collector match)")
        continue

    collector_id = mapping[course_name]['collector_id']

    print(f"Processing: {course_name}")

    responses = fetch_responses(collector_id)

    if responses:
        print(f"  → {len(responses)} responses found")
        if create_pdf(course_name, leader_name, collector_id, responses):
            print(f"  ✓ PDF created")
            success_count += 1
        else:
            print(f"  ✗ PDF creation failed")
    else:
        print(f"  → No responses found")

print(f"\n✓ Generated {success_count} PDFs successfully")
