#!/usr/bin/env python3
import json
import os
import requests
from base64 import b64encode
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io

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

def draw_chart(data, data_type):
    """Create matplotlib chart"""
    if data_type == 'ratings' and data:
        from collections import Counter
        counts = Counter(int(r) for r in data if isinstance(r, (int, float)))
        labels = sorted(counts.keys())
        values = [counts[l] for l in labels]

        fig, ax = plt.subplots(figsize=(8, 2.5))
        bars = ax.bar(labels, values, color='#1f77b4', edgecolor='navy', alpha=0.7, width=0.6)

        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        ax.set_xticks(labels)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, max(values) * 1.15)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        return fig

    return None

def create_pdf(course_name, leader_name, collector_id, responses):
    """Create PDF with all responses"""
    os.makedirs('output/KW40-2026', exist_ok=True)

    leader_slug_name = leader_slug(leader_name)
    course_slug = umlaut_slug(course_name)
    pdf_filename = f"output/KW40-2026/{leader_slug_name}_KW40_{course_slug}.pdf"

    print(f"  Creating: {pdf_filename}")

    questions = aggregate_by_question(responses)

    try:
        with PdfPages(pdf_filename) as pdf:
            # Page 1: Title
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.suptitle(f"{course_name} - KW40", fontsize=18, fontweight='bold', y=0.95)

            ax = fig.add_subplot(111)
            ax.axis('off')

            info_text = f"Zeitraum: 21. - 25. September 2026\nAntworten: {len(responses)}"
            ax.text(0.5, 0.85, info_text, ha='center', va='top', fontsize=12,
                   transform=ax.transAxes)

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Pages for each question
            y_pos = 0
            current_fig = None
            current_ax = None

            for element_id in sorted(questions.keys()):
                q = questions[element_id]
                q_text = q['text']

                # Create new page if needed
                if y_pos >= 0.85 or current_fig is None:
                    if current_fig is not None:
                        pdf.savefig(current_fig, bbox_inches='tight')
                        plt.close(current_fig)
                    current_fig, current_ax = plt.subplots(figsize=(8.27, 11.69))
                    current_ax.axis('off')
                    y_pos = 0.95

                # Add question title
                current_ax.text(0.1, y_pos, q_text, fontsize=11, fontweight='bold',
                               transform=current_ax.transAxes, wrap=True)
                y_pos -= 0.04

                # Add chart or data
                if q['ratings']:
                    # Add ratings chart
                    from collections import Counter
                    counts = Counter(int(r) for r in q['ratings'] if isinstance(r, (int, float)))
                    labels = sorted(counts.keys())
                    values = [counts[l] for l in labels]

                    # Create small inline chart
                    avg = sum(q['ratings']) / len(q['ratings'])
                    current_ax.text(0.1, y_pos, f"Average: {avg:.1f}/5", fontsize=10,
                                   transform=current_ax.transAxes)
                    y_pos -= 0.03

                    # Bar data as text
                    for label, count in zip(labels, values):
                        pct = (count / len(q['ratings'])) * 100
                        bar_width = pct / 100 * 0.4
                        current_ax.text(0.1, y_pos, f"{label}: {count} ({pct:.0f}%)",
                                       fontsize=9, transform=current_ax.transAxes)
                        y_pos -= 0.025

                elif q['choices']:
                    # Show choice counts
                    for choice_text, count in sorted(q['choices'].items(), key=lambda x: x[1], reverse=True):
                        current_ax.text(0.1, y_pos, f"• {choice_text}: {count}",
                                       fontsize=9, transform=current_ax.transAxes)
                        y_pos -= 0.025

                # Add text responses
                if q['texts'] and q['type'] == 'text':
                    current_ax.text(0.1, y_pos, "Text responses:", fontsize=9,
                                   fontweight='bold', transform=current_ax.transAxes)
                    y_pos -= 0.025

                    for text in q['texts'][:3]:
                        text_short = text[:80] + ("..." if len(text) > 80 else "")
                        current_ax.text(0.15, y_pos, f"• {text_short}", fontsize=8,
                                       transform=current_ax.transAxes)
                        y_pos -= 0.025

                y_pos -= 0.02

            if current_fig is not None:
                pdf.savefig(current_fig, bbox_inches='tight')
                plt.close(current_fig)

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
