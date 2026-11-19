"""
PDF & Document Exporter Module
Generates professional luxury real estate advisory reports in PDF format using ReportLab.
"""

import io
from datetime import datetime
from typing import List, Dict, Any

def generate_advisory_pdf(messages: List[Dict[str, Any]]) -> bytes:
    """
    Builds a styled PDF document of the consultation session.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#9e7a36'),
            alignment=1
        )

        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            alignment=1
        )

        role_user_style = ParagraphStyle(
            'RoleUser',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1e3a8a')
        )

        role_assistant_style = ParagraphStyle(
            'RoleAssistant',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#9e7a36')
        )

        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1e293b')
        )

        property_title_style = ParagraphStyle(
            'PropTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )

        property_meta_style = ParagraphStyle(
            'PropMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#334155')
        )

        story = []

        # Header Title
        story.append(Paragraph("DARGLOBAL & WASALT REAL ESTATE ADVISORY", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Consultation Summary Report &bull; Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", subtitle_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#c5a059'), spaceAfter=14))

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            # Clean content of raw markdown
            clean_content = content.replace("**", "").replace("###", "").replace("##", "").replace("*", "")
            
            if role == "user":
                story.append(Paragraph(f"Client Inquiry:", role_user_style))
                story.append(Spacer(1, 3))
                story.append(Paragraph(clean_content, body_style))
                story.append(Spacer(1, 10))
            elif role == "assistant":
                story.append(Paragraph(f"Advisory Response (NVIDIA Nemotron 3.5 Super VL):", role_assistant_style))
                story.append(Spacer(1, 3))
                
                # Split lines for readable paragraphs
                for paragraph in clean_content.split("\n\n"):
                    if paragraph.strip():
                        story.append(Paragraph(paragraph.strip(), body_style))
                        story.append(Spacer(1, 4))

                # Attached property recommendations if present
                cards = msg.get("cards", [])
                if cards:
                    story.append(Spacer(1, 6))
                    for card in cards:
                        title = card.get("title", "Property")
                        source = card.get("source", "Portfolio")
                        price = card.get("price_local", "N/A")
                        usd = card.get("price_usd", "")
                        loc = f"{card.get('city')}, {card.get('country')}"
                        ptype = card.get("property_type", "")
                        beds = card.get("bedrooms", "")
                        partner = card.get("brand_partner", "N/A")
                        
                        prop_data = [
                            [Paragraph(f"<b>{title}</b> ({source})", property_title_style), Paragraph(f"<b>Price:</b> {price} ({usd})", property_title_style)],
                            [Paragraph(f"<b>Location:</b> {loc} | <b>Type:</b> {ptype} | <b>Layout:</b> {beds}", property_meta_style), Paragraph(f"<b>Partner:</b> {partner}", property_meta_style)]
                        ]
                        
                        t = Table(prop_data, colWidths=[330, 200])
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#cbd5e1')),
                            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
                            ('TOPPADDING', (0,0), (-1,-1), 4),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 6))

                story.append(Spacer(1, 8))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=10))

        # Build Document
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        # Fallback text representation if reportlab encounters an issue
        txt_fallback = f"DARGLOBAL & WASALT ADVISORY DOSSIER\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for msg in messages:
            txt_fallback += f"[{msg.get('role', '').upper()}]:\n{msg.get('content', '')}\n\n"
        return txt_fallback.encode('utf-8')
