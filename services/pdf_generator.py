from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from models.database import AnalysisResult
import json

class PDFGenerator:
    def generate_report(self, analysis: AnalysisResult) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563EB') # Blue-600
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4B5563') # Gray-600
        )

        # Header
        story.append(Paragraph("TrueCheck - Relatório de Verificação", title_style))
        story.append(Paragraph(f"ID da Verificação: #{analysis.id} | Data: {analysis.timestamp.strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        story.append(Spacer(1, 20))

        # Verdict Section
        verdict_color = colors.green if analysis.verdict == "Confiável" else colors.red
        story.append(Paragraph(f"Veredito: <font color='{verdict_color}'>{analysis.verdict}</font>", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Scores Table
        data = [
            ['Critério', 'Score IA', 'Score Usuário'],
            ['Geral', f"{analysis.ai_score}/100", f"{analysis.user_score}/100"],
            ['Discrepância', f"{analysis.discrepancy} pontos", f"Nível: {analysis.discrepancy_level}"]
        ]
        
        table = Table(data, colWidths=[200, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Content Snippet
        story.append(Paragraph("Conteúdo Analisado:", styles['Heading3']))
        story.append(Paragraph(f"<i>{analysis.content}</i>", styles['Italic']))
        story.append(Spacer(1, 20))

        # Detailed Analysis (from JSON)
        details = analysis.details
        if "result" in details and "feedback" in details["result"]:
            story.append(Paragraph("Feedback Educativo:", styles['Heading3']))
            story.append(Paragraph(details["result"]["feedback"], styles['BodyText']))
            story.append(Spacer(1, 20))

        # Sources Section
        if analysis.sources:
            story.append(Paragraph("Fontes e Referências:", styles['Heading3']))
            
            for i, source in enumerate(analysis.sources, 1):
                # Reliability color
                rel_color = "green" if source.get("reliability") == "Alta" else "orange" if source.get("reliability") == "Média" else "red"
                
                source_text = f"""
                <b>{i}. {source.get('name')}</b> 
                <font size=8 color='{rel_color}'>[{source.get('reliability')}]</font><br/>
                {source.get('description')}<br/>
                """
                
                if source.get('url'):
                    source_text += f"<font color='blue'><u><a href='{source.get('url')}'>{source.get('url')}</a></u></font>"
                
                story.append(Paragraph(source_text, styles['BodyText']))
                story.append(Spacer(1, 10))

        doc.build(story)
        buffer.seek(0)
        return buffer

pdf_generator = PDFGenerator()
