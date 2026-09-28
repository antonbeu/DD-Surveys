#!/usr/bin/env python3
import csv
import json
import os
import requests
from base64 import b64encode
from datetime import datetime
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from collections import defaultdict

# API Credentials
API_USER = "505973-1597"
API_PASS = "s3ocr33932dpwpffw9ojalf43k9cwc8kz5zi"
SURVEY_ID = "1908032"

# Date range
DATE_FROM = "2026-09-21T00:00:00+00:00"
DATE_TO = "2026-09-25T23:59:59+00:00"

# Survey questions
QUESTIONS = [
    "Welche Kursinhalte waren neu für Sie?",
    "Wie war Ihr Vorwissen zum Thema?",
    "Haben Sie durch den Kurs Neues gelernt?",
    "Wie hat Ihnen der Kurs gefallen?",
    "Weitere Gedanken oder Feedback",
    "Hat der Kurs Ihr Interesse zum Thema vertieft?",
    "Wie könnten wir das Thema noch vertiefen?",
    "Würden Sie den Kurs weiterempfehlen?"
]

auth = b64encode(f"{API_USER}:{API_PASS}".encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

def fetch_responses(collector_id):
    """Fetch all responses for a collector in the date range"""
    responses = []
    page = 1

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

def aggregate_responses(responses):
    """Aggregate responses by question"""
    aggregated = defaultdict(lambda: {'ratings': [], 'texts': []})

    for resp in responses:
        answers = resp.get('answers', [])
        for answer in answers:
            question_id = answer.get('question_id')
            value = answer.get('value')

            if value:
                if isinstance(value, dict):
                    if 'rating' in value:
                        aggregated[question_id]['ratings'].append(value['rating'])
                    if 'text' in value:
                        aggregated[question_id]['texts'].append(value['text'])
                elif isinstance(value, (int, float)):
                    aggregated[question_id]['ratings'].append(value)
                elif isinstance(value, str):
                    aggregated[question_id]['texts'].append(value)

    return aggregated

def draw_bar_chart(data, title, filepath):
    """Create a bar chart for rating data"""
    if not data:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Count ratings
    rating_counts = defaultdict(int)
    for rating in data:
        if isinstance(rating, (int, float)):
            rating_counts[int(rating)] += 1

    if not rating_counts:
        plt.close(fig)
        return None

    labels = sorted(rating_counts.keys())
    counts = [rating_counts[l] for l in labels]

    bars = ax.bar(labels, counts, color='steelblue', edgecolor='navy', alpha=0.7)
    ax.set_xlabel('Rating', fontsize=12)
    ax.set_ylabel('Anzahl Antworten', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(labels)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11)

    plt.tight_layout()
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close(fig)

    return filepath

def create_pdf(course_name, collector_id, responses):
    """Create PDF report for a course"""
    os.makedirs('output/KW25-2026', exist_ok=True)

    # Create filename
    safe_name = course_name.replace('/', '-').replace('?', '').replace('!', '').replace('🌱', '').replace('🚀', '').replace('⚔️', '').strip()
    pdf_filename = f"output/KW25-2026/{safe_name}_{collector_id}.pdf"

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
    summary_text = f"<b>Zeitraum:</b> 21. - 25. September 2026<br/><b>Antworten:</b> {len(responses)}"
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    aggregated = aggregate_responses(responses)

    # Create charts for rating questions
    for q_id, q_data in sorted(aggregated.items()):
        if q_data['ratings']:
            avg_rating = sum(q_data['ratings']) / len(q_data['ratings'])
            question_title = f"Frage {q_id}: Durchschnitt {avg_rating:.1f}/5"

            chart_path = draw_bar_chart(q_data['ratings'], question_title, f'/tmp/chart_{collector_id}_{q_id}.png')

            if chart_path and os.path.exists(chart_path):
                story.append(Image(chart_path, width=6*inch, height=3.5*inch))
                story.append(Spacer(1, 0.2*inch))

        # Add text feedback if available
        if q_data['texts']:
            story.append(Paragraph(f"<b>Textfeedback:</b>", styles['Heading3']))
            for text in q_data['texts'][:3]:  # Limit to 3 text responses
                if text and len(text) > 0:
                    story.append(Paragraph(f"• {text[:200]}...", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

    # Build PDF
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating PDF for {course_name}: {e}")
        return False

# Load mapping
with open('week25_mapping.json', 'r') as f:
    mapping = json.load(f)

print(f"Generating PDFs for {len(mapping['confirmed'])} courses...\n")

success_count = 0
for item in mapping['confirmed']:
    course = item['course']
    collector_id = item['collector_id']

    print(f"Processing: {course}...")

    # Fetch responses
    responses = fetch_responses(collector_id)

    if responses:
        print(f"  → {len(responses)} responses found")

        if create_pdf(course, collector_id, responses):
            print(f"  ✓ PDF created")
            success_count += 1
        else:
            print(f"  ✗ PDF creation failed")
    else:
        print(f"  → No responses found")

print(f"\n✓ Generated {success_count} PDFs successfully")
