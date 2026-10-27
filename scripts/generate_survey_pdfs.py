#!/usr/bin/env python3
import csv
import os
from collections import defaultdict, Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib import colors

WEEK_NUM = "43"

# EXACT column names from CSV (mit \xa0 am Ende wo nötig!)
QUESTION_MAPPING = {
    'In einem Selbstlernkurs': 'Möchtest du das Thema vertiefen?',
    'In einem mehrwöchigen Live-Projekt mit einer Dozentin / einem Dozenten': 'Möchtest du das Thema vertiefen?',
    'In einem Learning Club, der sich mit ähnlichen Themen beschäftigt': 'Möchtest du das Thema vertiefen?',
    'In einem Selbstlernprojekt, das du jederzeit starten kannst\xa0': 'Möchtest du das Thema vertiefen?',  # \xa0 = Non-Breaking-Space!
    'Andere': 'Möchtest du das Thema vertiefen?',
}

def umlaut_slug(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return ''.join(c if c.isalnum() or c in ' -.' else '' for c in text).strip()

def draw_bar_chart(values, filename):
    counter = Counter(values)
    labels = [str(k) for k in sorted(counter.keys())]
    counts = [counter[k] for k in sorted(counter.keys())]
    
    fig, ax = plt.subplots(figsize=(5.5, 2.2))
    bars = ax.bar(labels, counts, color='#2E86AB', edgecolor='#1F4D7B', linewidth=1.5)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    ax.set_ylabel('Anzahl', fontsize=9)
    ax.set_ylim(0, max(counts) * 1.2)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

def create_pdf(course_name, responses_by_question):
    course_slug = umlaut_slug(course_name)
    filename = f"/tmp/kw43_pdfs/Kurs_KW{WEEK_NUM}_{course_slug}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1.2*cm, bottomMargin=1.2*cm, leftMargin=1.2*cm, rightMargin=1.2*cm)
    story = []
    
    title_style = ParagraphStyle('Title', fontSize=16, textColor=colors.HexColor('#1F4D7B'), spaceAfter=10, fontName='Helvetica-Bold')
    question_style = ParagraphStyle('Question', fontSize=10, textColor=colors.HexColor('#1F4D7B'), spaceAfter=4, spaceBefore=2, fontName='Helvetica-Bold')
    normal_text_style = ParagraphStyle('NormalText', fontSize=8, textColor=colors.black, spaceAfter=1, leading=9, leftIndent=10, fontName='Helvetica')
    
    story.append(Paragraph(course_name, title_style))
    story.append(Spacer(1, 0.15*cm))
    
    processed = set()
    
    for question, answers in responses_by_question.items():
        if question in processed:
            continue
        
        clean_answers = [a for a in answers if a and a.strip()]
        if not clean_answers:
            continue
        
        if question == 'Möchtest du das Thema vertiefen?':
            story.append(Paragraph(question, question_style))
            
            main_answers = [a for a in clean_answers if a.strip() in ['Ja', 'Nein']]
            if main_answers:
                chart_file = f"/tmp/chart_{hash(question)}.png"
                draw_bar_chart(main_answers, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
                story.append(Spacer(1, 0.1*cm))
            
            for option_col, parent in QUESTION_MAPPING.items():
                if parent == question and option_col in responses_by_question:
                    option_answers = responses_by_question[option_col]
                    clean_opt = [a for a in option_answers if a and a.strip() in ['x', 'Ja']]
                    if clean_opt:
                        # Bullet point mit normalem schwarzem Text
                        story.append(Paragraph(f"• {option_col.strip()}", normal_text_style))
                    processed.add(option_col)
            
            story.append(Spacer(1, 0.15*cm))
        
        elif question in QUESTION_MAPPING:
            processed.add(question)
        
        else:
            story.append(Paragraph(question, question_style))
            
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
            elif all(a.strip() in ['Ja', 'Nein'] for a in clean_answers):
                chart_file = f"/tmp/chart_{hash(question)}.png"
                draw_bar_chart(clean_answers, chart_file)
                story.append(Image(chart_file, width=4.8*inch, height=1.9*inch))
            else:
                for text in clean_answers[:5]:
                    text_clean = str(text).replace('\n', ' ').strip()[:140]
                    if text_clean and text_clean not in ['Ja', 'Nein', 'x', '', '-']:
                        story.append(Paragraph(f"• {text_clean}", normal_text_style))
            
            story.append(Spacer(1, 0.15*cm))
        
        processed.add(question)
    
    doc.build(story)

csv_file = "/root/.claude/uploads/6ffeaf5f-3332-5ad0-9338-47f78b6cac3f/55fd52ea-UmfrageOnline-Beantwortungen-1908032-2026-10-18-2026-10-24.csv"

responses_by_course = defaultdict(lambda: defaultdict(list))

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if not row.get('Collector') or 'nicht abgeschlossen' in row.get('Status', '').lower():
            continue
        
        course_name = row['Collector']
        for key, value in row.items():
            if key not in ['ID', 'Gestartet am', 'Zuletzt aktualisiert am', 'Status', 'Collector', 'Sprache', 'IP-Adresse', 'Gerät'] and value and value.strip():
                responses_by_course[course_name][key].append(value)

os.makedirs('/tmp/kw43_pdfs', exist_ok=True)

print(f"\nFINAL - Mit exakten CSV-Spaltennamen\n")
for course in sorted(responses_by_course.keys()):
    if len(next(iter(responses_by_course[course].values()))) > 0:
        create_pdf(course, responses_by_course[course])
        print(f"✓ {course}")

print()

