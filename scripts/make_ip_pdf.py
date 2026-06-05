"""
Generate a bilingual (English + Chinese) PDF for the IP clauses.
Reads both _KAGGLE_TEMPLATE.md and _KAGGLE_TEMPLATE_CN.md, lays them
out side by side in a clean professional format.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

# Register built-in CJK font (handles Chinese characters)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

ROOT = Path(__file__).resolve().parent.parent

# Parse the markdown files (skip headers, take numbered clauses)
def parse_clauses(md_path):
    text = md_path.read_text(encoding='utf-8')
    clauses = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Match numbered lines like "1. ..." or "10. ..."
        if line[0].isdigit() and '.' in line[:4]:
            num, body = line.split('.', 1)
            clauses.append((int(num.strip()), body.strip()))
    return clauses

en_clauses = parse_clauses(ROOT / 'IP_CLAUSES_KAGGLE_TEMPLATE.md')
cn_clauses = parse_clauses(ROOT / 'IP_CLAUSES_KAGGLE_TEMPLATE_CN.md')

assert len(en_clauses) == len(cn_clauses), "Clause counts must match!"

# --- Styles ---
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'TitleEN', parent=styles['Title'],
    fontName='Helvetica-Bold', fontSize=18,
    spaceAfter=8, textColor=colors.HexColor('#06101f')
)
title_cn_style = ParagraphStyle(
    'TitleCN', parent=styles['Title'],
    fontName='STSong-Light', fontSize=15,
    spaceAfter=20, textColor=colors.HexColor('#06101f')
)
subtitle_style = ParagraphStyle(
    'Subtitle', parent=styles['Normal'],
    fontName='Helvetica', fontSize=10,
    textColor=colors.HexColor('#4d6b8a'), alignment=1, spaceAfter=24
)
section_style = ParagraphStyle(
    'Section', parent=styles['Heading2'],
    fontName='Helvetica-Bold', fontSize=11,
    textColor=colors.HexColor('#38bdf8'),
    spaceAfter=6, spaceBefore=12
)
en_body_style = ParagraphStyle(
    'BodyEN', parent=styles['Normal'],
    fontName='Helvetica', fontSize=10,
    leading=14, textColor=colors.HexColor('#1a2535'),
)
cn_body_style = ParagraphStyle(
    'BodyCN', parent=styles['Normal'],
    fontName='STSong-Light', fontSize=10.5,
    leading=15, textColor=colors.HexColor('#1a2535'),
)
num_style = ParagraphStyle(
    'Num', parent=styles['Normal'],
    fontName='Helvetica-Bold', fontSize=11,
    textColor=colors.HexColor('#38bdf8'),
    alignment=1,
)
footer_style = ParagraphStyle(
    'Footer', parent=styles['Normal'],
    fontName='Helvetica', fontSize=8,
    textColor=colors.HexColor('#8faac8'), alignment=1,
)

# --- Build PDF ---
out_path = ROOT / 'IP_CLAUSES_BILINGUAL.pdf'
doc = SimpleDocTemplate(
    str(out_path), pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title='IP Clauses (Bilingual)',
    author='CUHK-X Organizing Committee',
)

story = []

# Title
story.append(Paragraph(
    'Intellectual Property Clauses',
    title_style
))
story.append(Paragraph(
    '知识产权条款（中英双语）',
    title_cn_style
))
story.append(Paragraph(
    'Kaggle Reference Template &mdash; Academic-Friendly Version<br/>'
    'CUHK-X 2026 Multimodal Human Activity Challenge',
    subtitle_style
))

# Build bilingual table
# Each row: [Number, English Paragraph, Chinese Paragraph]
table_data = [[
    Paragraph('<b>#</b>', num_style),
    Paragraph('<b>English</b>', ParagraphStyle('h', parent=en_body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#38bdf8'))),
    Paragraph('<b>中文</b>', ParagraphStyle('h', parent=cn_body_style, fontName='STSong-Light', textColor=colors.HexColor('#38bdf8'))),
]]

for (num, en_text), (_, cn_text) in zip(en_clauses, cn_clauses):
    table_data.append([
        Paragraph(str(num), num_style),
        Paragraph(en_text, en_body_style),
        Paragraph(cn_text, cn_body_style),
    ])

table = Table(
    table_data,
    colWidths=[1*cm, 7.5*cm, 7.5*cm],
    repeatRows=1,
)
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf4fb')),
    ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#38bdf8')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING', (0,0), (-1,-1), 8),
    ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7fafc')]),
    ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.HexColor('#dde7f1')),
]))
story.append(table)

# Footer
story.append(Spacer(1, 0.8*cm))
story.append(Paragraph(
    'CUHK-X Multimodal Human Activity Challenge 2026 &mdash; cuhkx.competition@gmail.com',
    footer_style
))

doc.build(story)
print(f"PDF generated: {out_path}")
