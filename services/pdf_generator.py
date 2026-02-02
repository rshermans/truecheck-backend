from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from models.database import AnalysisResult
import json

class PDFGenerator:
    def generate_report(self, analysis: AnalysisResult) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        story = []
        styles = getSampleStyleSheet()

        # ============ CUSTOM STYLES ============
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=26,
            spaceAfter=10,
            textColor=colors.HexColor('#2563EB'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        content_box_style = ParagraphStyle(
            'ContentBox',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            alignment=TA_JUSTIFY,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10
        )
        
        feedback_style = ParagraphStyle(
            'Feedback',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1F2937'),
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

        # ============ HEADER ============
        story.append(Paragraph("🔷 TrueCheck", title_style))
        story.append(Paragraph("Relatório de Verificação de Factualidade", subtitle_style))
        
        # Info box
        info_data = [[
            f"ID: #{analysis.id}",
            f"Data: {analysis.timestamp.strftime('%d/%m/%Y às %H:%M')}",
            f"Utilizador: {analysis.student_name or 'Anônimo'}"
        ]]
        info_table = Table(info_data, colWidths=[2*inch, 2.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4B5563')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB'))
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))

        # ============ VERDICT ============
        verdict_color = colors.HexColor('#10B981') if analysis.verdict == "Confiável" else colors.HexColor('#EF4444')
        verdict_bg = colors.HexColor('#D1FAE5') if analysis.verdict == "Confiável" else colors.HexColor('#FEE2E2')
        
        verdict_data = [[f"⚖️ Veredito Final: {analysis.verdict}"]]
        verdict_table = Table(verdict_data, colWidths=[6.5*inch])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
            ('TEXTCOLOR', (0, 0), (-1, -1), verdict_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 2, verdict_color)
        ]))
        story.append(verdict_table)
        story.append(Spacer(1, 20))

        # ============ CONTENT ANALYZED ============
        story.append(Paragraph("📄 Conteúdo Analisado", section_title_style))
        
        # Content box with border
        content_text = analysis.content[:800] + "..." if len(analysis.content) > 800 else analysis.content
        content_data = [[Paragraph(f"<i>{content_text}</i>", content_box_style)]]
        content_table = Table(content_data, colWidths=[6.5*inch])
        content_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#3B82F6')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(content_table)
        story.append(Spacer(1, 20))

        # ============ DETAILED COMPARISON ============
        story.append(Paragraph("📊 Comparação Detalhada por Critério", section_title_style))
        
        # Parse details to get individual criteria scores
        details = analysis.details
        criteria_data = [['Critério', 'Score IA', 'Score Aluno', 'Diferença']]
        
        # Map the 4 main criteria from the analysis
        # User perception is stored in full_json_data under "user_perception"
        user_perception = details.get("user_perception", {})
        
        criteria_mapping = [
            ("Credibilidade da Fonte", "sourceReliability", "sourceCredibility"),
            ("Consistência Factual", "factualConsistency", "criticalAnalysis"),
            ("Qualidade do Conteúdo", "contentQuality", "contextEvaluation"),
            ("Integridade Técnica", "technicalIntegrity", "finalJudgment")
        ]
        
        total_diff = 0
        for label, ai_key, user_key in criteria_mapping:
            ai_score = details.get("ai_analysis", {}).get(ai_key, 0)
            user_score = user_perception.get(user_key, 0)
            diff = abs(ai_score - user_score)
            total_diff += diff
            
            # Add emoji based on criterion
            if "Credibilidade" in label:
                icon = "🏛️"
            elif "Consistência" in label:
                icon = "📋"
            elif "Qualidade" in label:
                icon = "✨"
            else:
                icon = "🔧"
            
            criteria_data.append([
                f"{icon} {label}",
                f"{ai_score}/100",
                f"{user_score}/100",
                f"{diff} pts"
            ])
        
        # Overall scores
        criteria_data.append(['━' * 20, '━' * 8, '━' * 12, '━' * 10])
        criteria_data.append([
            '📈 Score Geral',
            f"{analysis.ai_score}/100",
            f"{analysis.user_score}/100",
            f"{abs(analysis.ai_score - analysis.user_score)} pts"
        ])
        criteria_data.append([
            '🎯 Discrepância Total',
            f"{analysis.discrepancy} pontos",
            f"Nível: {analysis.discrepancy_level}",
            ''
        ])
        
        criteria_table = Table(criteria_data, colWidths=[2.5*inch, 1.3*inch, 1.3*inch, 1.4*inch])
        criteria_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -3), colors.HexColor('#F9FAFB')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            # Summary rows
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#DBEAFE')),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(criteria_table)
        story.append(Spacer(1, 20))

        # ============ GAMIFICATION / PERFORMANCE ============
        if hasattr(analysis, 'user') and analysis.user:
            story.append(Paragraph("🎮 Seu Desempenho", section_title_style))
            
            xp_data = [[
                f"🌟 XP Atual: {analysis.user.xp}",
                f"📊 Nível: {analysis.user.level}",
                f"🎯 Precisão: {100 - analysis.discrepancy}%"
            ]]
            xp_table = Table(xp_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
            xp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDF4')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#166534')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#16A34A')),
            ]))
            story.append(xp_table)
            story.append(Spacer(1, 20))

        # ============ EDUCATIONAL FEEDBACK ============
        story.append(Paragraph("💬 Feedback Educativo", section_title_style))
        
        if "result" in details and "feedback" in details["result"]:
            feedback_text = details["result"]["feedback"]
        else:
            # Generate basic feedback based on discrepancy
            if analysis.discrepancy < 10:
                feedback_text = "Excelente trabalho! Sua avaliação está muito alinhada com a análise automatizada. Você demonstrou boa capacidade de análise crítica!"
            elif analysis.discrepancy < 20:
                feedback_text = "Bom trabalho! Sua avaliação está próxima da análise automatizada. Continue praticando para aprimorar suas habilidades de verificação."
            else:
                feedback_text = "Há espaço para melhoria. Revise os critérios de análise e pratique mais verificações para desenvolver seu senso crítico."
        
        story.append(Paragraph(feedback_text, feedback_style))
        story.append(Spacer(1, 20))

        # ============ SOURCES ============
        if analysis.sources:
            story.append(Paragraph("🔗 Fontes e Referências Consultadas", section_title_style))
            
            for i, source in enumerate(analysis.sources, 1):
                rel_color = colors.HexColor('#10B981') if source.get("reliability") == "Alta" else \
                           colors.HexColor('#F59E0B') if source.get("reliability") == "Média" else \
                           colors.HexColor('#EF4444')
                
                source_text = f"""
                <b>{i}. {source.get('name', 'Fonte desconhecida')}</b> 
                <font color='{rel_color.hexval()}' size=8>[{source.get('reliability', 'N/A')}]</font><br/>
                {source.get('description', '')}<br/>
                """
                
                if source.get('url'):
                    source_text += f"<font color='#3B82F6'><u>{source.get('url')}</u></font>"
                
                story.append(Paragraph(source_text, styles['Normal']))
                story.append(Spacer(1, 8))

        # ============ FOOTER ============
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("━" * 80, footer_style))
        story.append(Paragraph(
            "TrueCheck - Plataforma Educativa de Verificação de Factualidade | www.truecheck.pt",
            footer_style
        ))
        story.append(Paragraph(
            "Este relatório foi gerado automaticamente e destina-se apenas a fins educativos.",
            footer_style
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer

pdf_generator = PDFGenerator()
