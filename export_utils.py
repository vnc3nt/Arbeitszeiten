# -*- coding: utf-8 -*-
"""Export utilities for Arbeitszeiten: Excel (.xlsx) and PDF (.pdf) generation."""

import io
import re
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
from translations import get_month_name

# OpenPyXL
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


DEFAULT_ACCENT_HEX = "5B21B6"  # Fallback Deep Indigo/Purple


def _clean_hex(hex_val: Optional[str]) -> str:
    """Normalize hex color string to 6-char uppercase without #."""
    if not hex_val:
        return DEFAULT_ACCENT_HEX
    c = hex_val.strip().lstrip('#')
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    if re.match(r'^[0-9a-fA-F]{6}$', c):
        return c.upper()
    return DEFAULT_ACCENT_HEX


def _tint_hex(hex_val: str, factor: float = 0.88) -> str:
    """Blend hex color towards pure white (factor = 0: color, factor = 1: white)."""
    clean = _clean_hex(hex_val)
    r = int(clean[0:2], 16)
    g = int(clean[2:4], 16)
    b = int(clean[4:6], 16)
    r_tint = int(r + (255 - r) * factor)
    g_tint = int(g + (255 - g) * factor)
    b_tint = int(b + (255 - b) * factor)
    return f"{r_tint:02X}{g_tint:02X}{b_tint:02X}"


def _darken_hex(hex_val: str, factor: float = 0.25) -> str:
    """Darken hex color by scaling towards black."""
    clean = _clean_hex(hex_val)
    r = int(clean[0:2], 16)
    g = int(clean[2:4], 16)
    b = int(clean[4:6], 16)
    r_dark = int(r * (1.0 - factor))
    g_dark = int(g * (1.0 - factor))
    b_dark = int(b * (1.0 - factor))
    return f"{r_dark:02X}{g_dark:02X}{b_dark:02X}"


def _format_duration_display(duration_val) -> str:
    """Format decimal hours into German comma format, e.g. 2.5 -> '2,5h'."""
    if duration_val is None:
        return "-"
    if isinstance(duration_val, (int, float, Decimal)):
        s = f"{float(duration_val):.2f}".rstrip('0').rstrip('.')
        s = s.replace('.', ',')
        return f"{s}h"
    return f"{str(duration_val).replace('.', ',')}h"


def _format_date_display(d: date) -> str:
    """Format date as DD.MM.YYYY."""
    return d.strftime("%d.%m.%Y")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""

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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#71717a"))

        # Footer line
        self.setStrokeColor(colors.HexColor("#e4e4e7"))
        self.setLineWidth(0.5)
        self.line(40, 36, A4[0] - 40, 36)

        # Footer text (without emojis)
        left_text = f"Arbeitszeiten App - Export generiert am {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        page_str = f"Seite {self._pageNumber} von {page_count}"
        self.drawString(40, 24, left_text)
        self.drawRightString(A4[0] - 40, 24, page_str)
        self.restoreState()


def generate_excel_export(
    profile_names: List[str],
    monthly_data: List[Dict[str, Any]],
    user_name: str = "",
    lang: str = "de",
    accent_color: Optional[str] = None
) -> io.BytesIO:
    """
    Generate an Excel workbook containing the export data.
    Uses the profile's accent color for header accents and month separators.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Arbeitszeiten"
    ws.views.sheetView[0].showGridLines = True

    is_multi_profile = len(profile_names) > 1

    # Color calculations based on accent_color
    c_primary = _clean_hex(accent_color)
    c_header_bg = _darken_hex(c_primary, 0.15)
    c_month_bg = _tint_hex(c_primary, 0.88)
    c_month_fg = _darken_hex(c_primary, 0.25)
    c_zebra = "F9FAFB"
    c_border = "D1D5DB"

    font_family = "Segoe UI"
    thin_border_side = Side(border_style="thin", color=c_border)
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_top_thick = Border(top=Side(border_style="medium", color=c_primary), bottom=thin_border_side)

    # 1. Title Block
    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 10

    if is_multi_profile:
        title_text = "Arbeitszeiten - Export mehrerer Profile"
        subtitle_text = f"Profile: {', '.join(profile_names)} | Erstellt: {datetime.now().strftime('%d.%m.%Y')}"
    else:
        profile_name = profile_names[0] if profile_names else "Profil"
        title_text = f"Arbeitszeiten - {profile_name}"
        subtitle_text = f"Benutzer: {user_name} | Erstellt: {datetime.now().strftime('%d.%m.%Y')}"

    ws["A1"] = title_text
    ws["A1"].font = Font(name=font_family, size=16, bold=True, color=c_primary)
    ws["A2"] = subtitle_text
    ws["A2"].font = Font(name=font_family, size=10, italic=True, color="6B7280")

    # Column configuration
    col_count = 3 if is_multi_profile else 2
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=col_count)

    # 2. Table Column Headers
    header_row = 4
    ws.row_dimensions[header_row].height = 24

    headers = ["Datum", "Dauer"]
    if is_multi_profile:
        headers.append("Profil")

    for col_idx, h_text in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=h_text)
        cell.font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color=c_header_bg, end_color=c_header_bg, fill_type="solid")
        cell.alignment = Alignment(horizontal="center" if col_idx == 1 else ("left" if col_idx == 3 else "right"), vertical="center")
        cell.border = border_cell

    current_row = 5
    total_all_hours = Decimal('0')

    # 3. Monthly Blocks
    for month_info in monthly_data:
        m_name = month_info['month_name']
        year = month_info['year']
        entries = month_info['entries']
        m_total = month_info.get('total_hours', Decimal('0'))
        total_all_hours += m_total

        # Month Separator Row (No emojis)
        ws.row_dimensions[current_row].height = 22
        m_label = f"{m_name} {year}  (Gesamt: {_format_duration_display(m_total)})"

        for col_idx in range(1, col_count + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.fill = PatternFill(start_color=c_month_bg, end_color=c_month_bg, fill_type="solid")
            cell.border = border_cell

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=col_count)
        banner_cell = ws.cell(row=current_row, column=1, value=m_label)
        banner_cell.font = Font(name=font_family, size=11, bold=True, color=c_month_fg)
        banner_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        current_row += 1

        if not entries:
            ws.row_dimensions[current_row].height = 20
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=col_count)
            no_entry_cell = ws.cell(row=current_row, column=1, value="Keine Zeiteinträge in diesem Monat")
            no_entry_cell.font = Font(name=font_family, size=9, italic=True, color="9CA3AF")
            no_entry_cell.alignment = Alignment(horizontal="center", vertical="center")
            for col_idx in range(1, col_count + 1):
                ws.cell(row=current_row, column=col_idx).border = border_cell
            current_row += 1
            continue

        # Rows in this month
        for r_idx, entry in enumerate(entries):
            ws.row_dimensions[current_row].height = 20
            row_fill = PatternFill(start_color=c_zebra, end_color=c_zebra, fill_type="solid") if (r_idx % 2 == 1) else PatternFill(fill_type=None)

            c_date = ws.cell(row=current_row, column=1, value=_format_date_display(entry['date']))
            c_date.font = Font(name=font_family, size=10)
            c_date.alignment = Alignment(horizontal="center", vertical="center")
            c_date.border = border_cell
            if row_fill.fill_type: c_date.fill = row_fill

            c_hours = ws.cell(row=current_row, column=2, value=_format_duration_display(entry['hours']))
            c_hours.font = Font(name=font_family, size=10, bold=True)
            c_hours.alignment = Alignment(horizontal="right", vertical="center")
            c_hours.border = border_cell
            if row_fill.fill_type: c_hours.fill = row_fill

            if is_multi_profile:
                c_prof = ws.cell(row=current_row, column=3, value=entry.get('profile_name', ''))
                c_prof.font = Font(name=font_family, size=10)
                c_prof.alignment = Alignment(horizontal="left", vertical="center")
                c_prof.border = border_cell
                if row_fill.fill_type: c_prof.fill = row_fill

            current_row += 1

    # Total Summary Row at bottom
    current_row += 1
    ws.row_dimensions[current_row].height = 24
    lbl_cell = ws.cell(row=current_row, column=1, value="Gesamtsumme aller Monate")
    lbl_cell.font = Font(name=font_family, size=11, bold=True, color="111827")
    lbl_cell.alignment = Alignment(horizontal="left", vertical="center")
    lbl_cell.border = border_top_thick

    total_cell = ws.cell(row=current_row, column=2, value=_format_duration_display(total_all_hours))
    total_cell.font = Font(name=font_family, size=12, bold=True, color=c_primary)
    total_cell.alignment = Alignment(horizontal="right", vertical="center")
    total_cell.border = border_top_thick

    if is_multi_profile:
        third_cell = ws.cell(row=current_row, column=3, value="")
        third_cell.border = border_top_thick

    # Auto-adjust column widths
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 16
    if is_multi_profile:
        ws.column_dimensions['C'].width = 24

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def generate_pdf_export(
    profile_names: List[str],
    monthly_data: List[Dict[str, Any]],
    user_name: str = "",
    lang: str = "de",
    accent_color: Optional[str] = None
) -> io.BytesIO:
    """
    Generate a visually appealing PDF document containing the export data.
    Uses the profile's accent color for titles, borders and headers.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=50
    )

    is_multi_profile = len(profile_names) > 1

    # Palette
    c_primary_hex = _clean_hex(accent_color)
    c_primary = colors.HexColor(f"#{c_primary_hex}")
    c_header_bg = colors.HexColor(f"#{_darken_hex(c_primary_hex, 0.15)}")
    c_month_bg = colors.HexColor(f"#{_tint_hex(c_primary_hex, 0.90)}")
    c_month_border = colors.HexColor(f"#{_tint_hex(c_primary_hex, 0.70)}")
    c_grand_total_bg = colors.HexColor(f"#{_tint_hex(c_primary_hex, 0.94)}")

    c_text_dark = colors.HexColor("#18181b")
    c_text_muted = colors.HexColor("#71717a")
    c_row_alt = colors.HexColor("#FAFAFA")
    c_border = colors.HexColor("#E4E4E7")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ExportTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'ExportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=c_text_muted,
        spaceAfter=15
    )

    month_heading_style = ParagraphStyle(
        'MonthHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=c_primary
    )

    month_total_style = ParagraphStyle(
        'MonthTotal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=2,  # Right aligned
        textColor=c_primary
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=c_text_dark
    )

    cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=cell_style,
        alignment=1
    )

    cell_right = ParagraphStyle(
        'TableCellRight',
        parent=cell_style,
        alignment=2
    )

    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.white
    )
    header_cell_center = ParagraphStyle('HeaderCellCenter', parent=header_cell_style, alignment=1)
    header_cell_right = ParagraphStyle('HeaderCellRight', parent=header_cell_style, alignment=2)

    story = []

    # Title & Header (No emojis)
    if is_multi_profile:
        main_title = "Arbeitszeiten-Übersicht"
        sub_info = f"<b>Profile:</b> {', '.join(profile_names)} &nbsp;&bull;&nbsp; <b>Erstellt am:</b> {datetime.now().strftime('%d.%m.%Y')}"
    else:
        profile_name = profile_names[0] if profile_names else "Profil"
        main_title = f"Arbeitszeiten &ndash; {profile_name}"
        sub_info = f"<b>Benutzer:</b> {user_name} &nbsp;&bull;&nbsp; <b>Erstellt am:</b> {datetime.now().strftime('%d.%m.%Y')}"

    story.append(Paragraph(main_title, title_style))
    story.append(Paragraph(sub_info, subtitle_style))
    story.append(Spacer(1, 10))

    table_width = A4[0] - 80
    if is_multi_profile:
        col_widths = [table_width * 0.28, table_width * 0.28, table_width * 0.44]
    else:
        col_widths = [table_width * 0.50, table_width * 0.50]

    total_hours_all = Decimal('0')

    # Build monthly blocks
    for month_info in monthly_data:
        m_name = month_info['month_name']
        year = month_info['year']
        entries = month_info['entries']
        m_total = month_info.get('total_hours', Decimal('0'))
        total_hours_all += m_total

        month_block = []

        # Month header banner table (No emojis)
        month_banner_data = [
            [
                Paragraph(f"<b>{m_name} {year}</b>", month_heading_style),
                Paragraph(f"Monatssumme: <b>{_format_duration_display(m_total)}</b>", month_total_style)
            ]
        ]
        month_banner_table = Table(
            month_banner_data,
            colWidths=[table_width * 0.60, table_width * 0.40]
        )
        month_banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_month_bg),
            ('BOX', (0, 0), (-1, -1), 1, c_month_border),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 10),
            ('RIGHTPADDING', (-1, -1), (-1, -1), 10),
        ]))
        month_block.append(month_banner_table)
        month_block.append(Spacer(1, 4))

        if not entries:
            no_data = [[Paragraph("<i>Keine Zeiteinträge in diesem Monat vorhanden</i>", cell_center)]]
            no_table = Table(no_data, colWidths=[table_width])
            no_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            month_block.append(no_table)
            month_block.append(Spacer(1, 14))
            story.append(KeepTogether(month_block))
            continue

        # Table data
        if is_multi_profile:
            t_data = [
                [
                    Paragraph("Datum", header_cell_center),
                    Paragraph("Dauer", header_cell_right),
                    Paragraph("Profil", header_cell_style)
                ]
            ]
            for idx, entry in enumerate(entries):
                t_data.append([
                    Paragraph(_format_date_display(entry['date']), cell_center),
                    Paragraph(f"<b>{_format_duration_display(entry['hours'])}</b>", cell_right),
                    Paragraph(entry.get('profile_name', ''), cell_style)
                ])
        else:
            t_data = [
                [
                    Paragraph("Datum", header_cell_center),
                    Paragraph("Dauer", header_cell_right)
                ]
            ]
            for idx, entry in enumerate(entries):
                t_data.append([
                    Paragraph(_format_date_display(entry['date']), cell_center),
                    Paragraph(f"<b>{_format_duration_display(entry['hours'])}</b>", cell_right)
                ])

        t = Table(t_data, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ]
        # Alternating row colors
        for r in range(1, len(t_data)):
            if r % 2 == 0:
                t_style.append(('BACKGROUND', (0, r), (-1, r), c_row_alt))

        t.setStyle(TableStyle(t_style))
        month_block.append(t)
        month_block.append(Spacer(1, 14))

        story.extend(month_block)

    # Grand total box at the end
    story.append(Spacer(1, 10))
    summary_data = [
        [
            Paragraph("<b>Gesamtsumme aller Monate</b>", ParagraphStyle('SumLbl', fontName='Helvetica-Bold', fontSize=11, textColor=c_text_dark)),
            Paragraph(f"<b>{_format_duration_display(total_hours_all)}</b>", ParagraphStyle('SumVal', fontName='Helvetica-Bold', fontSize=13, alignment=2, textColor=c_primary))
        ]
    ]
    summary_table = Table(summary_data, colWidths=[table_width * 0.60, table_width * 0.40])
    summary_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1.5, c_primary),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, c_primary),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), c_grand_total_bg),
    ]))
    story.append(summary_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf
