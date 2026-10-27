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

def is_option_column(col_name):
    """Spalten die mit 'In einem', 'Mit ' anfangen oder 'Andere' sind = Optionen"""
    stripped = col_name.strip()
    return stripped.startswith('In einem') or stripped.startswith('Mit ') or stripped == 'Andere'

def create_pdf(course_name, data_row, all_columns):
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
    
    for i, col in enumerate(all_columns):
        if col in processed or is_option_column(col):
            continue  # Überspringe Optionen jetzt noch
        
        answer = data_row.get(col, '').strip()
        if not answer:
            continue
        
        story.append(Paragraph(col, question_style))
        
        # Ja/Nein Frage?
        if answer in ['Ja', 'Nein']:
            # Schaue nach folgenden Optionen
            ja_nein_counter = Counter()
            for j in range(i + 1, len(all_columns)):
                next_col = all_columns[j]
                if is_option_column(next_col):
                    next_val = data_row.get(next_col, '').strip()
                    if next_val in ['x', 'Ja']:
                        ja_nein_counter[next_col] += 1
                    processed.add(next_col)
                else:
                    break  # Stoppe bei nächster Nicht-Option
            
            # Zeige Ja/Nein Optionen als Bullet Points
            if ja_nein_counter:
                for opt, count in ja_nein_counter.most_common():
                    opt_clean = opt.strip()
                    story.append(Paragraph(f"• {opt_clean}: {count}x", normal_text_style))
            story.append(Spacer(1, 0.1*cm))
        else:
            # Text Antwort
            text_clean = answer.replace('\n', ' ').strip()[:140]
            if text_clean and text_clean not in ['-', '']:
                story.append(Paragraph(f"• {text_clean}", normal_text_style))
            story.append(Spacer(1, 0.1*cm))
        
        processed.add(col)
    
    doc.build(story)

csv_file = "/root/.claude/uploads/6ffeaf5f-3332-5ad0-9338-47f78b6cac3f/55fd52ea-UmfrageOnline-Beantwortungen-1908032-2026-10-18-2026-10-24.csv"

os.makedirs('/tmp/kw43_pdfs', exist_ok=True)

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    all_columns = [c for c in reader.fieldnames if c not in ['ID', 'Gestartet am', 'Zuletzt aktualisiert am', 'Status', 'Collector', 'Sprache', 'IP-Adresse', 'Gerät']]
    f.seek(0)
    reader = csv.DictReader(f, delimiter=';')
    
    courses_done = set()
    for row in reader:
        if not row.get('Collector') or 'nicht abgeschlossen' in row.get('Status', '').lower():
            continue
        
        course_name = row['Collector']
        if course_name not in courses_done:
            create_pdf(course_name, row, all_columns)
            courses_done.add(course_name)
            print(f"✓ {course_name}")

print(f"\n{len(courses_done)} PDFs generated")

