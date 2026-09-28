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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors

# API Credentials
API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# Date range for KW40
DATE_FROM = "2026-09-21T00:00:00+00:00"
DATE_TO = "2026-09-25T23:59:59+00:00"

# Map course titles to collector IDs and leaders
MAPPING = {
    "Bilder-Sodoku": {"collector_id": 2053176, "leader": "Dominik Schirra"},
    "Geheimschrift-Detektiv": {"collector_id": 2133528, "leader": "Dominik Schirra"},
    "Philo Club": {"collector_id": 1699147, "leader": "Eileen Egbert"},
    "Lernen zu Lernen!": {"collector_id": 2089422, "leader": "TeeKay"},
    "Fantasielabor": {"collector_id": 2132650, "leader": "Vera Garasenko"},
    "Mathematik der Maya": {"collector_id": 1928660, "leader": "Felicia Schmitt"},
    "Die Belohnungsdetektive": {"collector_id": 2062218, "leader": "Silvia Silva"},
    "Zeitdetektive": {"collector_id": 2133528, "leader": "Marina Mersch"},
    "Einführung in die Klassische Archäologie": {"collector_id": 2143328, "leader": "Paula Maietti"},
    "Scientific errors in Jurassic World": {"collector_id": 1667150, "leader": "Elihu Guzman"},
    "Musik zum Programmieren": {"collector_id": 2043486, "leader": "Dominik Schirra"},
    "Arabische Mathematik": {"collector_id": 2134692, "leader": "Felicia Schmitt"},
    "Strom und Licht": {"collector_id": 2020115, "leader": "Dominik Schirra"},
    "Ozeanströmungen – Motor unseres Klimas": {"collector_id": 1815156, "leader": "Franziska Pausch"},
    "Unter meinem Hut": {"collector_id": 1966708, "leader": "Unknown"},
    "Ich höre was, was du nicht hörst": {"collector_id": 1749813, "leader": "Tobias Litterst"},
    "Pflanzen im All 🌱🚀": {"collector_id": 1746146, "leader": "Markus Paul"},
    "Erfinde dein Spiel": {"collector_id": 1642290, "leader": "Dominik Schirra"},
    "Did dinosaurs get sick?": {"collector_id": 2130121, "leader": "Elihu Guzman"},
    "Pferdequiz": {"collector_id": 1892166, "leader": "Julia Blüher"},
    "Buchclub - Spaß am Lesen": {"collector_id": 1642123, "leader": "JLU Gießen – Team Deutsch"},
    "Baue deine eigene Alarmanlage": {"collector_id": 2091192, "leader": "Dominik Schirra"},
    "Sound Secrets: Physik & Musik": {"collector_id": 2028809, "leader": "Felicia Schmitt"},
    "⚔️ Abenteuer Mittelalter": {"collector_id": 2143337, "leader": "Marina Mersch"},
    "Karel the Robot": {"collector_id": 1852076, "leader": "Dominik Schirra"},
    "How to - Katzen streicheln": {"collector_id": 1961711, "leader": "Julia Blüher"},
    "Yogareise durch unser Sonnensystem": {"collector_id": 1946071, "leader": "Unknown"},
    "When giant insects ruled": {"collector_id": 2132664, "leader": "Elihu Guzman"},
}

def leader_slug(name):
    """Convert 'Dominik Schirra' to 'Schirra-Dominik'"""
    if not name or name == "Unknown":
        return "Unknown"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}-{' '.join(parts[:-1])}"

def umlaut_slug(text):
    """Replace umlauts for filenames"""
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    text = text.replace('ß', 'ss')
    text = text.replace('🌱', '').replace('🚀', '').replace('⚔️', '')
    return text.strip()

def fetch_responses(collector_id):
    """Fetch full response details for a collector"""
    response_ids = []
    page = 1
    auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

    # Get response IDs
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
            print(f"  Error fetching response list: {e}")
            break

    # Fetch full details for each response
    responses = []
    for response_id in response_ids:
        try:
            url = f'https://api.surveyhero.com/v1/surveys/{SURVEY_ID}/responses/{response_id}'
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                responses.append(resp.json())
        except Exception as e:
            print(f"  Error fetching response {response_id}: {e}")

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

            # Parse answer based on type
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

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()

    # Save to bytes
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf

def create_pdf(course_name, leader_name, collector_id, responses):
    """Create PDF report"""
    os.makedirs('output/KW40-2026', exist_ok=True)

    leader_slug_name = leader_slug(leader_name)
    course_slug = umlaut_slug(course_name)
    pdf_filename = f"output/KW40-2026/{leader_slug_name}_KW40_{course_slug}.pdf"

    print(f"  Creating: {pdf_filename}")

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

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )

    # Question style
    q_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )

    # Text response style
    text_style = ParagraphStyle(
        'TextResp',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        leftIndent=15
    )

    # Header
    story.append(Paragraph(f"<b>{course_name}</b>", title_style))
    story.append(Spacer(1, 0.2*cm))

    meta_text = f"<font size=9>KW40 (21. - 25. September 2026) | Antworten: {len(responses)}</font>"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 0.4*cm))

    # Get aggregated questions
    questions = aggregate_by_question(responses)

    # Process each question
    for element_id in sorted(questions.keys()):
        q = questions[element_id]
        q_text = q['text']

        # Question title
        story.append(Paragraph(q_text, q_style))

        # Add chart for ratings
        if q['ratings']:
            avg = sum(q['ratings']) / len(q['ratings'])
            story.append(Paragraph(f"<font size=8><i>Durchschnitt: {avg:.1f}/5</i></font>", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))

            chart_buf = draw_bar_chart(q['ratings'])
            if chart_buf:
                img = Image(chart_buf, width=6*cm, height=1.8*cm)
                story.append(img)
                story.append(Spacer(1, 0.3*cm))

        # Add text responses
        if q['texts']:
            # Filter out choice labels if we also have text responses
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

    # Build PDF
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

# Main
print("Generating KW40 feedback PDFs...\n")
success_count = 0

for course_name in sorted(MAPPING.keys()):
    course_data = MAPPING[course_name]
    collector_id = course_data['collector_id']
    leader_name = course_data['leader']

    print(f"Processing: {course_name} ({leader_name})")

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
