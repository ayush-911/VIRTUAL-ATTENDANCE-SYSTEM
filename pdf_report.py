from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import csv


def csv_to_pdf(csv_path, pdf_path):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(170, height - 50, "Today's Attendance Report")

    # Date
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 80, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")

    # Header
    y = height - 120
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Name")
    c.drawString(250, y, "Time")
    c.drawString(420, y, "Status")
    c.line(50, y - 5, 550, y - 5)

    y -= 30
    c.setFont("Helvetica", 11)

    # CSV -> rows
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header

        for row in reader:
            if y < 80:
                c.showPage()
                y = height - 80

                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Name")
                c.drawString(250, y, "Time")
                c.drawString(420, y, "Status")
                c.line(50, y - 5, 550, y - 5)

                y -= 30
                c.setFont("Helvetica", 11)

            name = row[0] if len(row) > 0 else "-"
            time_ = row[1] if len(row) > 1 else "-"
            status = row[2] if len(row) > 2 else "Present"

            c.drawString(50, y, name)
            c.drawString(250, y, time_)
            c.drawString(420, y, status)
            y -= 20

    c.save()
    return pdf_path
