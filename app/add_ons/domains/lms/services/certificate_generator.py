"""
Certificate Generator for LMS
Generates certificates from template with user details
"""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import os


class CertificateGenerator:
    """Generate course completion certificates"""
    
    def __init__(self, template_path: str = None):
        """
        Initialize certificate generator
        
        Args:
            template_path: Path to certificate template image (optional)
        """
        self.template_path = template_path
        self.width = 1200
        self.height = 900
        
    def create_template(self) -> Image.Image:
        """
        Create a default certificate template if none provided
        
        Returns:
            PIL Image object
        """
        # Create base image with gradient background
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        border_color = '#2563eb'  # Blue
        border_width = 20
        draw.rectangle(
            [(border_width, border_width), 
             (self.width - border_width, self.height - border_width)],
            outline=border_color,
            width=border_width
        )
        
        # Inner decorative border
        inner_border = border_width + 10
        draw.rectangle(
            [(inner_border, inner_border), 
             (self.width - inner_border, self.height - inner_border)],
            outline='#60a5fa',  # Light blue
            width=3
        )
        
        return img
    
    def generate_certificate(
        self,
        student_name: str,
        course_title: str,
        completion_date: str = None,
        score: int = None,
        instructor_name: str = None,
        certificate_id: str = None
    ) -> BytesIO:
        """
        Generate a certificate with student details
        
        Args:
            student_name: Name of the student
            course_title: Title of the course
            completion_date: Date of completion (defaults to today)
            score: Exam score percentage
            instructor_name: Name of the instructor
            certificate_id: Unique certificate ID
            
        Returns:
            BytesIO object containing the certificate image
        """
        # Load or create template
        if self.template_path and os.path.exists(self.template_path):
            img = Image.open(self.template_path)
        else:
            img = self.create_template()
        
        draw = ImageDraw.Draw(img)
        
        # Set default values
        if not completion_date:
            completion_date = datetime.now().strftime("%B %d, %Y")
        if not certificate_id:
            certificate_id = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 60)
            heading_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
            name_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
            body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 30)
            small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            heading_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Colors
        primary_color = '#1e40af'  # Dark blue
        secondary_color = '#64748b'  # Gray
        accent_color = '#2563eb'  # Blue
        
        # Draw "CERTIFICATE" title
        title_text = "CERTIFICATE"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw.text((title_x, 80), title_text, fill=primary_color, font=title_font)
        
        # Draw "OF COMPLETION" subtitle
        subtitle_text = "OF COMPLETION"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=body_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.width - subtitle_width) // 2
        draw.text((subtitle_x, 160), subtitle_text, fill=secondary_color, font=body_font)
        
        # Draw decorative line
        line_y = 220
        line_margin = 200
        draw.line(
            [(line_margin, line_y), (self.width - line_margin, line_y)],
            fill=accent_color,
            width=2
        )
        
        # Draw "This certifies that"
        certifies_text = "This certifies that"
        certifies_bbox = draw.textbbox((0, 0), certifies_text, font=body_font)
        certifies_width = certifies_bbox[2] - certifies_bbox[0]
        certifies_x = (self.width - certifies_width) // 2
        draw.text((certifies_x, 260), certifies_text, fill=secondary_color, font=body_font)
        
        # Draw student name (large and prominent)
        name_bbox = draw.textbbox((0, 0), student_name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (self.width - name_width) // 2
        draw.text((name_x, 320), student_name, fill=primary_color, font=name_font)
        
        # Draw underline under name
        name_underline_y = 410
        name_underline_margin = 250
        draw.line(
            [(name_underline_margin, name_underline_y), 
             (self.width - name_underline_margin, name_underline_y)],
            fill=accent_color,
            width=2
        )
        
        # Draw "has successfully completed"
        completed_text = "has successfully completed"
        completed_bbox = draw.textbbox((0, 0), completed_text, font=body_font)
        completed_width = completed_bbox[2] - completed_bbox[0]
        completed_x = (self.width - completed_width) // 2
        draw.text((completed_x, 450), completed_text, fill=secondary_color, font=body_font)
        
        # Draw course title
        course_bbox = draw.textbbox((0, 0), course_title, font=heading_font)
        course_width = course_bbox[2] - course_bbox[0]
        course_x = (self.width - course_width) // 2
        draw.text((course_x, 510), course_title, fill=accent_color, font=heading_font)
        
        # Draw score if provided
        if score is not None:
            score_text = f"with a score of {score}%"
            score_bbox = draw.textbbox((0, 0), score_text, font=body_font)
            score_width = score_bbox[2] - score_bbox[0]
            score_x = (self.width - score_width) // 2
            draw.text((score_x, 580), score_text, fill=secondary_color, font=body_font)
            details_y = 650
        else:
            details_y = 620
        
        # Draw date and instructor in two columns
        left_margin = 200
        right_margin = self.width - 200
        
        # Date (left side)
        date_label = "Date of Completion:"
        draw.text((left_margin, details_y), date_label, fill=secondary_color, font=small_font)
        draw.text((left_margin, details_y + 30), completion_date, fill=primary_color, font=body_font)
        
        # Instructor (right side) if provided
        if instructor_name:
            instructor_label = "Instructor:"
            instructor_bbox = draw.textbbox((0, 0), instructor_label, font=small_font)
            instructor_width = instructor_bbox[2] - instructor_bbox[0]
            draw.text((right_margin - instructor_width, details_y), instructor_label, fill=secondary_color, font=small_font)
            
            instructor_name_bbox = draw.textbbox((0, 0), instructor_name, font=body_font)
            instructor_name_width = instructor_name_bbox[2] - instructor_name_bbox[0]
            draw.text((right_margin - instructor_name_width, details_y + 30), instructor_name, fill=primary_color, font=body_font)
        
        # Draw certificate ID at bottom
        cert_id_text = f"Certificate ID: {certificate_id}"
        cert_id_bbox = draw.textbbox((0, 0), cert_id_text, font=small_font)
        cert_id_width = cert_id_bbox[2] - cert_id_bbox[0]
        cert_id_x = (self.width - cert_id_width) // 2
        draw.text((cert_id_x, self.height - 80), cert_id_text, fill=secondary_color, font=small_font)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='PNG', quality=95)
        output.seek(0)
        
        return output
    
    def generate_pdf_certificate(
        self,
        student_name: str,
        course_title: str,
        completion_date: str = None,
        score: int = None,
        instructor_name: str = None,
        certificate_id: str = None
    ) -> BytesIO:
        """
        Generate a PDF certificate (requires reportlab)
        
        Returns:
            BytesIO object containing the PDF certificate
        """
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.utils import ImageReader
            
            # Generate PNG certificate first
            png_cert = self.generate_certificate(
                student_name=student_name,
                course_title=course_title,
                completion_date=completion_date,
                score=score,
                instructor_name=instructor_name,
                certificate_id=certificate_id
            )
            
            # Create PDF
            pdf_output = BytesIO()
            c = canvas.Canvas(pdf_output, pagesize=landscape(letter))
            
            # Convert PNG to ImageReader
            img_reader = ImageReader(png_cert)
            
            # Draw image on PDF (fit to page)
            page_width, page_height = landscape(letter)
            c.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
            
            c.save()
            pdf_output.seek(0)
            
            return pdf_output
            
        except ImportError:
            # If reportlab not available, return PNG
            return self.generate_certificate(
                student_name=student_name,
                course_title=course_title,
                completion_date=completion_date,
                score=score,
                instructor_name=instructor_name,
                certificate_id=certificate_id
            )
