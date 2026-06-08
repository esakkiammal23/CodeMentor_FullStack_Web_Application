import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas
from django.conf import settings

LANG_FULL_NAMES = {
    'python': 'Python Programming',
    'java': 'Java Programming',
    'ai': 'Artificial Intelligence',
    'ml': 'Machine Learning',
}

def generate_certificate_pdf(user_name, language, score, certificate_id, issued_date):
    media_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(media_dir, exist_ok=True)
    filename = f"cert_{certificate_id}.pdf"
    filepath = os.path.join(media_dir, filename)
    relative_path = f"certificates/{filename}"

    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Background
    c.setFillColorRGB(0.97, 0.97, 1.0)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Border
    c.setStrokeColorRGB(0.2, 0.3, 0.8)
    c.setLineWidth(6)
    c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)
    c.setStrokeColorRGB(0.6, 0.7, 1.0)
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60, fill=0, stroke=1)

    # Title
    c.setFont("Helvetica-Bold", 42)
    c.setFillColorRGB(0.1, 0.2, 0.6)
    c.drawCentredString(width / 2, height - 100, "CERTIFICATE OF ACHIEVEMENT")

    # Subtitle
    c.setFont("Helvetica", 18)
    c.setFillColorRGB(0.3, 0.3, 0.5)
    c.drawCentredString(width / 2, height - 140, "This is to certify that")

    # User name
    c.setFont("Helvetica-Bold", 34)
    c.setFillColorRGB(0.1, 0.1, 0.4)
    c.drawCentredString(width / 2, height - 195, user_name)

    # Underline
    name_width = c.stringWidth(user_name, "Helvetica-Bold", 34)
    c.setStrokeColorRGB(0.2, 0.3, 0.8)
    c.setLineWidth(1.5)
    c.line(width/2 - name_width/2, height - 205, width/2 + name_width/2, height - 205)

    # Achievement text
    c.setFont("Helvetica", 18)
    c.setFillColorRGB(0.3, 0.3, 0.5)
    c.drawCentredString(width / 2, height - 245, "has successfully completed the course and passed the assessment in")

    # Course name
    lang_name = LANG_FULL_NAMES.get(language, language.upper())
    c.setFont("Helvetica-Bold", 28)
    c.setFillColorRGB(0.1, 0.4, 0.7)
    c.drawCentredString(width / 2, height - 295, lang_name)

    # Score
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.1, 0.5, 0.2)
    c.drawCentredString(width / 2, height - 340, f"Score: {score} / 20  |  Grade: {'Distinction' if score >= 19 else 'Merit' if score >= 17 else 'Pass'}")

    # Decorative line
    c.setStrokeColorRGB(0.2, 0.3, 0.8)
    c.setLineWidth(1)
    c.line(80, height - 370, width - 80, height - 370)

    # Date and cert ID
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(80, height - 400, f"Date of Issue: {issued_date}")
    c.drawString(80, height - 420, f"Certificate ID: {certificate_id}")

    # Platform
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.2, 0.3, 0.8)
    c.drawCentredString(width / 2, height - 415, "CodeMentor Learning Platform")

    c.save()
    return filepath, relative_path