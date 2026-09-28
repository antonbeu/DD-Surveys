#!/usr/bin/env python3
import csv
import json
import os
import requests
from base64 import b64encode
from datetime import datetime
from io import BytesIO
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors

# API Credentials
API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# Date range for KW40 (Sept 21-25, 2026)
DATE_FROM = "2026-09-21T00:00:00+00:00"
DATE_TO = "2026-09-25T23:59:59+00:00"

# Survey questions from the API structure
QUESTIONS = [
    {"id": 1, "text": "Welche Kursinhalte waren neu für Sie?", "type": "text"},
    {"id": 2, "text": "Wie war Ihr Vorwissen zum Thema?", "type": "scale"},
    {"id": 3, "text": "Haben Sie durch den Kurs Neues gelernt?", "type": "scale"},
    {"id": 4, "text": "Wie hat Ihnen der Kurs gefallen?", "type": "scale"},
    {"id": 5, "text": "Weitere Gedanken oder Feedback", "type": "text"},
    {"id": 6, "text": "Hat der Kurs Ihr Interesse zum Thema vertieft?", "type": "scale"},
    {"id": 7, "text": "Wie könnten wir das Thema noch vertiefen?", "type": "text"},
    {"id": 8, "text": "Würden Sie den Kurs weiterempfehlen?", "type": "scale"},
]

# Map course titles to collector IDs (from KW40_mapping.json)
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
    # Last name first, then first name
    return f"{parts[-1]}-{' '.join(parts[:-1])}"

def umlaut_slug(text):
    """Replace umlauts for filenames"""
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    text = text.replace('ß', 'ss')
    # Remove emojis and special chars
    text = text.replace('🌱', '').replace('🚀', '').replace('⚔️', '')
    return text.strip()

def fetch_responses(collector_id):
    """Fetch all responses for a collector in the date range"""
    responses = []
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
            responses_list = data.get('responses') or data.get('data') or []

            if not responses_list:
                break

            responses.extend(responses_list)

            if len(responses_list) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching responses for collector {collector_id}: {e}")
            break

    return responses

def aggregate(responses):
    """Aggregate responses by question"""
    aggregated = defaultdict(lambda: {'ratings': [], 'texts': []})

    for resp in responses:
        answers = resp.get('answers', [])
        for answer in answers:
            q_id = answer.get('question_id')
            value = answer.get('value')

            if value:
                if isinstance(value, dict):
                    if 'rating' in value:
                        aggregated[q_id]['ratings'].append(value['rating'])
                    if 'text' in value:
                        aggregated[q_id]['texts'].append(value['text'])
                elif isinstance(value, (int, float)):
                    aggregated[q_id]['ratings'].append(value)
                elif isinstance(value, str):
                    aggregated[q_id]['texts'].append(value)

    return aggregated

def draw_bar_question(ratings, title):
    """Create a matplotlib figure for rating data"""
    if not ratings:
        return None

    from collections import Counter
    counts = Counter(int(r) for r in ratings if isinstance(r, (int, float)))

    if not counts:
        return None

    labels = sorted(counts.keys())
    values = [counts[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.bar(labels, values, color='#1f77b4', edgecolor='navy', alpha=0.7)

    ax.set_ylabel('Count')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xticks(labels)
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')

    return fig

def create_pdf(course_name, leader_name, collector_id, responses):
    """Create a PDF report for a course"""
    os.makedirs('output/KW40-2026', exist_ok=True)

    # Create filename with leader name
    leader_slug_name = leader_slug(leader_name)
    course_slug = umlaut_slug(course_name)
    pdf_filename = f"output/KW40-2026/{leader_slug_name}_KW40_{course_slug}.pdf"

    print(f"  Creating: {pdf_filename}")

    doc = SimpleDocTemplate(pdf_filename, pagesize=A4,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=1  # center
    )
    story.append(Paragraph(f"Feedback: {course_name}", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Summary
    summary_text = f"<b>Zeitraum:</b> 21. - 25. September 2026 (KW40)<br/><b>Antworten:</b> {len(responses)}"
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    aggregated = aggregate(responses)

    # Create charts for rating questions
    for q_id, q_data in sorted(aggregated.items()):
        q_text = next((q['text'] for q in QUESTIONS if q['id'] == q_id), f"Question {q_id}")

        if q_data['ratings']:
            avg_rating = sum(q_data['ratings']) / len(q_data['ratings'])
            question_title = f"{q_text} (avg: {avg_rating:.1f}/5)"

            fig = draw_bar_question(q_data['ratings'], question_title)
            if fig:
                # Save figure to bytes
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                plt.close(fig)

                # Add to PDF
                img = Image(buf, width=6*inch, height=2*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))

        # Add text feedback if available
        if q_data['texts']:
            story.append(Paragraph(f"<b>{q_text} (Text responses):</b>", styles['Heading3']))
            for text in q_data['texts'][:5]:  # Limit to 5 text responses
                if text and len(text) > 0:
                    text_preview = text[:300] + ("..." if len(text) > 300 else "")
                    story.append(Paragraph(f"• {text_preview}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

    # Build PDF
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"  Error creating PDF: {e}")
        return False

# Main process
print("Generating KW40 feedback PDFs...\n")

success_count = 0
for course_name, course_data in sorted(MAPPING.items()):
    collector_id = course_data['collector_id']
    leader_name = course_data['leader']

    print(f"Processing: {course_name} ({leader_name})")

    # Fetch responses
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
