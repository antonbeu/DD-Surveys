#!/usr/bin/env python3
import csv
import json
import os
from collections import defaultdict, Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib import colors

WEEK_NUM = "43"

def umlaut_slug(text):
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'ê': 'e', 'É': 'E', 'á': 'a', 'à': 'a', 'â': 'a',
        '👻': '', '👽': '', '🐶': '', '🤖': '', '✅': '', '❌': '', '☺': '', '😃': '', '🤩': '', '💕': '', '👍': '', '😁': '', '😊': '', '😀': ''
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
    if 'brot' in name.lower() or 'digital' in name.lower():
        parts = name.split()
        return parts[0] if parts else 'Unknown'
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}-{parts[0]}"
    return name.strip()

def draw_bar_chart(values, filename):
    if not values:
        return None
    
    counter = Counter(values)
    labels = [str(k) for k in sorted(counter.keys())]
    counts = [counter[k] for k in sorted(counter.keys())]
    
    fig, ax = plt.subplots(figsize=(5.5, 2.2))
    bars = ax.bar(labels, counts, color='#2E86AB', edgecolor='#1F4D7B', linewidth=1.5)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    ax.set_ylabel('Anzahl', fontsize=9)
    ax.set_ylim(0, max(counts) * 1.2)
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

def is_yes_no(answers):
    """Check if answers are only Ja/Nein/x"""
    clean = [str(a).strip().lower() for a in answers if a]
    return all(v in ['ja', 'nein', 'x', ''] for v in clean)

def is_text_answer(answers):
    """Check if answers are text (not short categorical)"""
    text_answers = [str(a).strip() for a in answers if a and a.strip() and a.strip() not in ['Ja', 'Nein', 'x', '', '-']]
    return len(text_answers) > 0 and any(len(a) > 20 for a in text_answers)

def create_pdf(course_name, leader_name, responses_by_question):
    if not responses_by_question:
        return None
    
    leader_slug_name = leader_slug(leader_name)
    course_slug = umlaut_slug(course_name)
    filename = f"/tmp/kw43_pdfs/{leader_slug_name}_KW{WEEK_NUM}_{course_slug}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1.2*cm, bottomMargin=1.2*cm, leftMargin=1.2*cm, rightMargin=1.2*cm)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=10,
        spaceBefore=0,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1F4D7B'),
        spaceAfter=4,
        spaceBefore=2,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    text_style = ParagraphStyle(
        'Text',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=1,
        leading=9,
        leftIndent=10
    )
    
    # Title
    story.append(Paragraph(course_name, title_style))
    story.append(Spacer(1, 0.15*cm))
    
    for question, answers in responses_by_question.items():
        if not answers:
            continue
        
        # Skip empty questions
        clean_answers = [a for a in answers if a and a.strip()]
        if not clean_answers:
            continue
        
        # Frage
        story.append(Paragraph(question, question_style))
        
        # Try to parse as numbers
        numeric_answers = []
        for ans in clean_answers:
            try:
                numeric_answers.append(int(ans))
            except:
                pass
        
        # Case 1: Numeric (rating scale)
        if numeric_answers and len(numeric_answers) == len(clean_answers):
            chart_file = f"/tmp/chart_{course_name}_{hash(question)}.png"
            draw_bar_chart(numeric_answers, chart_file)
            story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
            story.append(Spacer(1, 0.1*cm))
            
        # Case 2: Yes/No answers
        elif is_yes_no(clean_answers):
            # Show chart only if multiple Ja/Nein
            counter = Counter([a.lower() for a in clean_answers if a.strip().lower() in ['ja', 'nein']])
            if len(counter) > 0:
                chart_file = f"/tmp/chart_{course_name}_{hash(question)}.png"
                draw_bar_chart(clean_answers, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
            story.append(Spacer(1, 0.1*cm))
            
        # Case 3: Categorical (multiple choice)
        elif len(set(clean_answers)) > 1 and len(set(clean_answers)) <= 5:
            # Check if these are short category answers or text
            if not is_text_answer(clean_answers):
                chart_file = f"/tmp/chart_{course_name}_{hash(question)}.png"
                draw_bar_chart(clean_answers, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
                story.append(Spacer(1, 0.1*cm))
            else:
                # Text responses
                for text in clean_answers[:5]:
                    text_clean = str(text).replace('\n', ' ').strip()[:140]
                    if text_clean and text_clean not in ['Ja', 'Nein', 'x', '-', '']:
                        story.append(Paragraph(f"• {text_clean}", text_style))
                story.append(Spacer(1, 0.15*cm))
        
        # Case 4: Text/comment answers
        else:
            text_answers = [a for a in clean_answers if a and a.strip() and a.strip() not in ['Ja', 'Nein', 'x', '', '-']]
            if text_answers:
                for text in text_answers[:5]:
                    text_clean = str(text).replace('\n', ' ').strip()[:140]
                    if text_clean:
                        story.append(Paragraph(f"• {text_clean}", text_style))
            story.append(Spacer(1, 0.15*cm))
    
    try:
        doc.build(story)
        return filename
    except Exception as e:
        print(f"Error: {e}")
        return None

# Parse CSV
csv_file = "/root/.claude/uploads/6ffeaf5f-3332-5ad0-9338-47f78b6cac3f/55fd52ea-UmfrageOnline-Beantwortungen-1908032-2026-10-18-2026-10-24.csv"

responses_by_course = defaultdict(lambda: defaultdict(list))

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if not row.get('Collector'):
            continue
        
        course_name = row['Collector']
        status = row.get('Status', '')
        
        if 'nicht abgeschlossen' in status.lower():
            continue
        
        for key, value in row.items():
            if key not in ['ID', 'Gestartet am', 'Zuletzt aktualisiert am', 'Status', 'Collector', 'Sprache', 'IP-Adresse', 'Gerät']:
                if value and value.strip():
                    responses_by_course[course_name][key].append(value)

with open('/tmp/kw43_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

collector_to_leader = {}
for course_name, course_data in mapping['confirmed'].items():
    collector_name = course_data.get('collector_name', '')
    leader = course_data.get('leader', '')
    if collector_name:
        collector_to_leader[collector_name] = leader
        collector_to_leader[collector_name.strip()] = leader
        collector_to_leader[collector_name.lower().strip()] = leader

os.makedirs('/tmp/kw43_pdfs', exist_ok=True)

print(f"\n{'='*80}")
print(f"KW{WEEK_NUM} - FINAL PDF GENERATION")
print(f"{'='*80}\n")

generated = 0
total_responses = 0

for course_name in sorted(responses_by_course.keys()):
    responses = responses_by_course[course_name]
    response_count = len(next(iter(responses.values()))) if responses else 0
    
    leader_name = 'Unknown'
    for lookup_key in [course_name, course_name.strip(), course_name.lower().strip()]:
        if lookup_key in collector_to_leader:
            leader_name = collector_to_leader[lookup_key]
            break
    
    if response_count > 0:
        pdf_path = create_pdf(course_name, leader_name, responses)
        if pdf_path:
            print(f"✓ {course_name:<50} ({response_count})")
            generated += 1
            total_responses += response_count
        else:
            print(f"✗ {course_name:<50} (Failed)")

print(f"\n{'='*80}")
print(f"Generated: {generated} PDFs | Total: {total_responses} responses")
print(f"{'='*80}\n")

