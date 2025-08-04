from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import os

from medications.models import MedicationIntake, Prescription
from .models import ProgressReport

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2563EB')
        )
    
    def generate_patient_progress_report(self, patient, report_type='weekly_summary', days=7):
        """Generate comprehensive patient progress report"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate statistics
        total_intakes = MedicationIntake.objects.filter(
            prescription__patient=patient,
            scheduled_datetime__date__range=(start_date, end_date),
            status__in=['taken', 'missed', 'skipped']
        )
        
        taken_count = total_intakes.filter(status='taken').count()
        missed_count = total_intakes.filter(status='missed').count()
        total_count = total_intakes.count()
        
        compliance_rate = (taken_count / total_count * 100) if total_count > 0 else 0
        
        # Generate report content
        content = self.create_report_content(patient, start_date, end_date, total_intakes)
        
        # Create report record
        report = ProgressReport.objects.create(
            patient=patient,
            report_type=report_type,
            title=f"{report_type.replace('_', ' ').title()} - {patient.get_full_name()}",
            content=content,
            compliance_rate=compliance_rate,
            total_medications=total_count,
            taken_medications=taken_count,
            missed_medications=missed_count,
            report_period_start=start_date,
            report_period_end=end_date,
            generated_by=patient  # In real scenario, this would be the admin generating the report
        )
        
        # Generate PDF
        pdf_buffer = self.create_pdf_report(report)
        
        # Save PDF file
        pdf_filename = f"report_{patient.id}_{report.id}.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'reports', pdf_filename)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        report.pdf_file = f"reports/{pdf_filename}"
        report.save()
        
        return report
    
    def create_report_content(self, patient, start_date, end_date, intakes):
        """Create detailed report content"""
        content = f"""
        Patient Progress Report
        
        Patient: {patient.get_full_name()}
        Medical Record Number: {patient.medical_record_number}
        Report Period: {start_date} to {end_date}
        
        MEDICATION COMPLIANCE SUMMARY:
        - Total Medications Scheduled: {intakes.count()}
        - Medications Taken: {intakes.filter(status='taken').count()}
        - Medications Missed: {intakes.filter(status='missed').count()}
        - Medications Skipped: {intakes.filter(status='skipped').count()}
        
        DETAILED MEDICATION HISTORY:
        """
        
        for intake in intakes.order_by('-scheduled_datetime'):
            content += f"""
        {intake.scheduled_datetime.strftime('%Y-%m-%d %I:%M %p')} - {intake.prescription.medication.name}
        Dosage: {intake.prescription.dosage}
        Status: {intake.get_status_display()}
        """
            if intake.notes:
                content += f"Notes: {intake.notes}\n"
        
        return content
    
    def create_pdf_report(self, report):
        """Create PDF version of the report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(report.title, self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Patient info
        patient_info = [
            ['Patient Name:', report.patient.get_full_name()],
            ['Medical Record:', report.patient.medical_record_number or 'N/A'],
            ['Report Period:', f"{report.report_period_start} to {report.report_period_end}"],
            ['Generated On:', report.created_at.strftime('%Y-%m-%d %H:%M')],
        ]
        
        patient_table = Table(patient_info, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 12))
        
        # Compliance summary
        summary_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total Medications', str(report.total_medications), '100%'],
            ['Taken', str(report.taken_medications), f"{(report.taken_medications/report.total_medications*100):.1f}%" if report.total_medications > 0 else '0%'],
            ['Missed', str(report.missed_medications), f"{(report.missed_medications/report.total_medications*100):.1f}%" if report.total_medications > 0 else '0%'],
            ['Compliance Rate', f"{report.compliance_rate:.1f}%", ''],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 12))
        
        # Content
        content_para = Paragraph(report.content.replace('\n', '<br/>'), self.styles['Normal'])
        story.append(content_para)
        
        doc.build(story)
        return buffer

# Initialize report generator
report_generator = ReportGenerator()