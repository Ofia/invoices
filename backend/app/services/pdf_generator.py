"""
PDF Generation Service for Consolidated Invoices

This service generates professional PDF invoices for property managers
to bill property owners for services rendered during a specific period.
"""

from datetime import datetime, date
from typing import List
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


class ConsolidatedInvoiceData:
    """Data structure for consolidated invoice generation"""
    def __init__(
        self,
        workspace_name: str,
        start_date: date,
        end_date: date,
        invoice_items: List[dict]
    ):
        self.workspace_name = workspace_name
        self.start_date = start_date
        self.end_date = end_date
        self.invoice_items = invoice_items  # List of {supplier_name, invoice_date, amount}
        self.invoice_number = self._generate_invoice_number()
        self.generated_date = datetime.now()

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number based on timestamp"""
        return f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def calculate_total(self) -> float:
        """Calculate grand total of all invoice items"""
        return sum(item['amount'] for item in self.invoice_items)


def generate_consolidated_invoice_pdf(invoice_data: ConsolidatedInvoiceData) -> BytesIO:
    """
    Generate a professional consolidated invoice PDF.

    Args:
        invoice_data: ConsolidatedInvoiceData object with all invoice information

    Returns:
        BytesIO: PDF file in memory as bytes

    Example:
        data = ConsolidatedInvoiceData(
            workspace_name="Sunset Villa Apartments",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            invoice_items=[
                {"supplier_name": "ABC Plumbing", "invoice_date": date(2026, 1, 5), "amount": 230.00},
                {"supplier_name": "XYZ Electric", "invoice_date": date(2026, 1, 12), "amount": 450.00}
            ]
        )
        pdf_bytes = generate_consolidated_invoice_pdf(data)
    """
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        alignment=TA_CENTER
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER
    )

    # Title
    title = Paragraph("INVOICE", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.1*inch))

    # Invoice Number and Date
    invoice_info = Paragraph(
        f"<b>Invoice #:</b> {invoice_data.invoice_number}<br/>"
        f"<b>Date:</b> {invoice_data.generated_date.strftime('%B %d, %Y')}",
        normal_style
    )
    elements.append(invoice_info)
    elements.append(Spacer(1, 0.2*inch))

    # Property Name
    property_name = Paragraph(
        f"<b>Property:</b> {invoice_data.workspace_name}",
        heading_style
    )
    elements.append(property_name)
    elements.append(Spacer(1, 0.1*inch))

    # Billing Period
    period = Paragraph(
        f"<b>Billing Period:</b> {invoice_data.start_date.strftime('%B %d, %Y')} - "
        f"{invoice_data.end_date.strftime('%B %d, %Y')}",
        normal_style
    )
    elements.append(period)
    elements.append(Spacer(1, 0.3*inch))

    # Invoice Items Table
    # Table Header
    table_data = [
        ['Service Provider', 'Date', 'Amount']
    ]

    # Table Rows
    for item in invoice_data.invoice_items:
        table_data.append([
            item['supplier_name'],
            item['invoice_date'].strftime('%m/%d/%Y') if item['invoice_date'] else 'N/A',
            f"${item['amount']:,.2f}"
        ])

    # Add separator line
    table_data.append(['', '', ''])

    # Grand Total
    total = invoice_data.calculate_total()
    table_data.append([
        '',
        Paragraph('<b>TOTAL DUE:</b>', ParagraphStyle('RightBold', parent=styles['Normal'], fontSize=12, alignment=TA_RIGHT)),
        Paragraph(f'<b>${total:,.2f}</b>', ParagraphStyle('RightBold', parent=styles['Normal'], fontSize=12, alignment=TA_RIGHT))
    ])

    # Create table
    table = Table(table_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])

    # Table styling
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),

        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -3), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -3), colors.HexColor('#333333')),
        ('ALIGN', (0, 1), (0, -3), 'LEFT'),  # Service provider left-aligned
        ('ALIGN', (1, 1), (-1, -3), 'CENTER'),  # Date and amount centered
        ('FONTNAME', (0, 1), (-1, -3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -3), 10),
        ('TOPPADDING', (0, 1), (-1, -3), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -3), 8),

        # Alternating row colors for data rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.HexColor('#f8f9fa')]),

        # Grid lines
        ('GRID', (0, 0), (-1, -3), 0.5, colors.HexColor('#dee2e6')),

        # Separator line before total
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2c3e50')),

        # Total row styling
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2c3e50')),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        "Thank you for your business.<br/>"
        "Please remit payment within 30 days of invoice date.",
        footer_style
    )
    elements.append(footer)

    # Build PDF
    doc.build(elements)

    # Reset buffer position to beginning
    buffer.seek(0)

    return buffer
