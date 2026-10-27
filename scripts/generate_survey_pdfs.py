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

# MAPPING: Multiple-Choice Optionen zu ihrer Eltern-Frage
QUESTION_MAPPING = {
    'In einem Selbstlernkurs': 'Möchtest du das Thema vertiefen?',
    'In einem mehrwöchigen Live-Projekt mit einer Dozentin / einem Dozenten': 'Möchtest du das Thema vertiefen?',
    'In einem Learning Club, der sich mit ähnlichen Themen beschäftigt': 'Möchtest du das Thema vertiefen?',
    'In einem Selbstlernprojekt, das du jederzeit starten kannst ': 'Möchtest du das Thema vertiefen?',
    'Andere': 'Möchtest du das Thema vertiefen?',
}

def umlaut_slug(text):
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'ê': 'e', 'É': 'E', 'á': 'a', 'à': 'a', 'â': 'a',
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
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

def create_pdf(course_name, responses_by_question):
    if not responses_by_question:
        return None
    
    leader_slug_name = 'Kurs'
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
    
    # Process grouped questions
    processed = set()
    
    for question, answers in responses_by_question.items():
        if question in processed:
            continue
        
        clean_answers = [a for a in answers if a and a.strip()]
        if not clean_answers:
            continue
        
        # Check if this is a parent question with options
        if question in ['Möchtest du das Thema vertiefen?']:
            story.append(Paragraph(question, question_style))
            
            # Add chart for main answer
            main_answers = [a for a in clean_answers if a.strip() in ['Ja', 'Nein']]
            if main_answers:
                chart_file = f"/tmp/chart_{hash(question)}.png"
                draw_bar_chart(main_answers, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
                story.append(Spacer(1, 0.15*cm))
            
            # Add option answers as text (NOT as questions)
            for option_col, parent in QUESTION_MAPPING.items():
                if parent == question and option_col in responses_by_question:
                    option_answers = responses_by_question[option_col]
                    clean_opt = [a for a in option_answers if a and a.strip() and a.strip() in ['x', 'Ja', 'Ja ']]
                    if clean_opt:
                        story.append(Paragraph(f"• {option_col.strip()}", text_style))
                    processed.add(option_col)
            
            story.append(Spacer(1, 0.15*cm))
        
        elif question in QUESTION_MAPPING:
            # Skip - already processed as option
            processed.add(question)
        
        else:
            # Normal question
            story.append(Paragraph(question, question_style))
            
            # Numeric?
            numeric = []
            for ans in clean_answers:
                try:
                    numeric.append(int(ans))
                except:
                    pass
            
            if numeric and len(numeric) == len(clean_answers):
                chart_file = f"/tmp/chart_{hash(question)}.png"
                draw_bar_chart(numeric, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
            elif clean_answers[0].strip() in ['Ja', 'Nein']:
                # Yes/No
                if any(a.strip() in ['Ja', 'Nein'] for a in clean_answers):
                    chart_file = f"/tmp/chart_{hash(question)}.png"
                    draw_bar_chart([a for a in clean_answers if a.strip() in ['Ja', 'Nein']], chart_file)
                    story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
            else:
                # Text
                for text in clean_answers[:5]:
                    text_clean = str(text).replace('\n', ' ').strip()[:140]
                    if text_clean and text_clean not in ['Ja', 'Nein', 'x', '', '-']:
                        story.append(Paragraph(f"• {text_clean}", text_style))
            
            story.append(Spacer(1, 0.15*cm))
        
        processed.add(question)
    
    try:
        doc.build(story)
        return filename
    except Exception as e:
        print(f"Error: {e}")
        return None

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

os.makedirs('/tmp/kw43_pdfs', exist_ok=True)

print(f"\nKW{WEEK_NUM} - MAPPED PDF GENERATION")
print(f"{'='*80}\n")

generated = 0
for course_name in sorted(responses_by_course.keys()):
    responses = responses_by_course[course_name]
    response_count = len(next(iter(responses.values()))) if responses else 0
    
    if response_count > 0:
        pdf_path = create_pdf(course_name, responses)
        if pdf_path:
            print(f"✓ {course_name:<50} ({response_count})")
            generated += 1

print(f"\nGenerated: {generated} PDFs")
print(f"{'='*80}\n")

