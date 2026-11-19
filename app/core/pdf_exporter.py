"""
PDF & Document Exporter Module
Generates high-fidelity luxury real estate advisory reports in PDF format using ReportLab.
Includes running company name and page numbers on the bottom of every page,
plus precise date and timestamp for each user inquiry and assistant response.
Author: Alok Kushwaha
"""

import io
import re
import html
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes total page count and draws a running company footer
    on the bottom of every single page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        
        # Gold Footer Rule
        self.setStrokeColor(colors.HexColor('#c5a059'))
        self.setLineWidth(0.75)
        self.line(40, 36, self._pagesize[0] - 40, 36)
        
        # Left: Company Branding
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(colors.HexColor('#0f172a'))
        self.drawString(40, 22, "DARGLOBAL PLC & WASALT REAL ESTATE ADVISORY")
        
        # Center: Confidentiality Notice
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawCentredString(self._pagesize[0] / 2.0, 22, "CONFIDENTIAL CLIENT ADVISORY DOSSIER")
        
        # Right: Page Numbering
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(colors.HexColor('#0f172a'))
        self.drawRightString(self._pagesize[0] - 40, 22, f"Page {self._pageNumber} of {page_count}")
        
        self.restoreState()


def clean_text_for_pdf(text: str) -> str:
    """
    Sanitizes markdown and XML characters so ReportLab never encounters parser crashes.
    """
    if not text:
        return ""
    # Remove markdown headers and dividers
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    
    # Escape basic XML entities
    text = html.escape(text)
    
    # Restore safe formatting tags from markdown
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    
    # Fix quote symbols and markdown brackets
    text = text.replace("&gt;", "&quot;").replace("&lt;", "&lt;")
    return text


def generate_advisory_pdf(messages: List[Dict[str, Any]]) -> bytes:
    """
    Builds a complete, styled PDF document of the consultation session with timestamps
    and running company footer on every page.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Document Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#9e7a36'),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )

    badge_user_style = ParagraphStyle(
        'BadgeUser',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#ffffff')
    )

    badge_assistant_style = ParagraphStyle(
        'BadgeAssistant',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    body_user_style = ParagraphStyle(
        'BodyUser',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )

    body_assistant_style = ParagraphStyle(
        'BodyAssistant',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )

    prop_header_style = ParagraphStyle(
        'PropHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    prop_price_style = ParagraphStyle(
        'PropPrice',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#15803d'),
        alignment=2
    )

    prop_detail_style = ParagraphStyle(
        'PropDetail',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # 1. Document Header
    story.append(Paragraph("DARGLOBAL & WASALT REAL ESTATE ADVISORY", title_style))
    story.append(Spacer(1, 4))
    gen_time_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
    story.append(Paragraph(f"Client Advisory Session Summary &bull; Report Generated: {gen_time_str}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#c5a059'), spaceAfter=14))

    # 2. Iterate Through All Messages
    for msg in messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp") or datetime.now().strftime("%d %b %Y, %I:%M %p")
        
        # User Inquiry Banner
        if role == "user":
            user_header = [
                [
                    Paragraph(f"<b>CLIENT INQUIRY</b>", badge_user_style),
                    Paragraph(f"<b>Date & Time:</b> {timestamp}", ParagraphStyle('RAlign', parent=badge_user_style, alignment=2))
                ]
            ]
            t_user = Table(user_header, colWidths=[260, 272])
            t_user.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1e293b')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t_user)
            story.append(Spacer(1, 4))
            
            # Content Box
            clean_user_content = clean_text_for_pdf(content)
            user_body = [[Paragraph(clean_user_content, body_user_style)]]
            t_ubody = Table(user_body, colWidths=[532])
            t_ubody.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t_ubody)
            story.append(Spacer(1, 12))

        # Assistant Advisory Response
        elif role == "assistant":
            asst_header = [
                [
                    Paragraph(f"<b>ADVISOR SYNTHESIS &bull; NVIDIA NEMOTRON 3.5 SUPER VL</b>", badge_assistant_style),
                    Paragraph(f"<b>Date & Time:</b> {timestamp}", ParagraphStyle('RAlign2', parent=badge_assistant_style, alignment=2))
                ]
            ]
            t_asst = Table(asst_header, colWidths=[360, 172])
            t_asst.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fae8b4')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t_asst)
            story.append(Spacer(1, 4))

            # Main text content broken by double newlines into neat paragraphs
            clean_asst_content = clean_text_for_pdf(content)
            paragraphs = clean_asst_content.split("\n\n")
            
            flowables_list = []
            for p in paragraphs:
                p_str = p.strip()
                if p_str:
                    # Clean single linebreaks into breaks
                    p_formatted = p_str.replace("\n", "<br/>")
                    flowables_list.append([Paragraph(p_formatted, body_assistant_style)])
            
            if flowables_list:
                t_asst_body = Table(flowables_list, colWidths=[532])
                t_asst_body.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0,0), (-1,-1), 8),
                ]))
                story.append(t_asst_body)
                story.append(Spacer(1, 6))

            # Render Recommended Property Cards if attached
            cards = msg.get("cards", [])
            if cards:
                story.append(Spacer(1, 4))
                story.append(Paragraph("<b>VERIFIED PORTFOLIO RECOMMENDATIONS:</b>", ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#9e7a36'))))
                story.append(Spacer(1, 4))

                for card in cards:
                    title = clean_text_for_pdf(card.get('title', 'Property'))
                    source = card.get('source', 'Portfolio')
                    price_local = card.get('price_local', 'Price on Request')
                    price_usd = card.get('price_usd', '')
                    usd_part = f" ({price_usd})" if price_usd else ""
                    
                    loc = f"{card.get('city', '')}, {card.get('country', '')}"
                    ptype = card.get('property_type', '')
                    beds = card.get('bedrooms', '')
                    partner = card.get('brand_partner', 'N/A')
                    desc = clean_text_for_pdf(card.get('description', ''))
                    if len(desc) > 160:
                        desc = desc[:160] + "..."

                    card_rows = [
                        [
                            Paragraph(f"<b>{title}</b> &bull; <font color='#64748b'>[{source}]</font>", prop_header_style),
                            Paragraph(f"<b>{price_local}{usd_part}</b>", prop_price_style)
                        ],
                        [
                            Paragraph(f"<b>Location:</b> {loc} &nbsp;|&nbsp; <b>Type:</b> {ptype} &nbsp;|&nbsp; <b>Layout:</b> {beds}", prop_detail_style),
                            Paragraph(f"<b>Partner:</b> {partner}", prop_detail_style)
                        ],
                        [
                            Paragraph(f"<b>Overview:</b> {desc}", prop_detail_style),
                            Paragraph(f"<b>Status:</b> {card.get('status', 'Available')}", prop_detail_style)
                        ]
                    ]

                    t_card = Table(card_rows, colWidths=[372, 160])
                    t_card.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#c5a059')),
                        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('LEFTPADDING', (0,0), (-1,-1), 6),
                        ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(t_card)
                    story.append(Spacer(1, 5))

            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=10))

    # Build PDF with two-pass NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
