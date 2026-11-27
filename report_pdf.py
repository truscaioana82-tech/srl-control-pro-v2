import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def genera_pdf_bilancio(periodo, anno, tot, bagli, tropea):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementi = []

    elementi.append(Paragraph("<b>SRL CONTROL PRO • RENDICONTO CONTABILE</b>", styles["Title"]))
    elementi.append(Paragraph(f"Periodo: <b>{periodo}</b> • Anno: <b>{anno}</b> • Data stampa: {date.today()}", styles["Normal"]))
    elementi.append(Spacer(1, 20))

    dati_tabella = [
        ["VOCE DI BILANCIO", "TOTALE SRL", "SOCIO BAGLI", "SOCIO TROPEA"],
        ["Incassi Lordi", f"€ {tot['lordi']:,.2f}", f"€ {bagli['lordi']:,.2f}", f"€ {tropea['lordi']:,.2f}"],
        ["Note di Credito", f"€ {tot['nc']:,.2f}", f"€ {bagli['nc']:,.2f}", f"€ {tropea['nc']:,.2f}"],
        ["Spese Fornitori", f"€ {tot['fornitori']:,.2f}", f"€ {bagli['fornitori']:,.2f}", f"€ {tropea['fornitori']:,.2f}"],
        ["Costo Dipendenti", f"€ {tot['dipendenti']:,.2f}", f"€ {bagli['dipendenti']:,.2f}", f"€ {tropea['dipendenti']:,.2f}"],
        ["IVA a Debito", f"€ {tot['iva_deb']:,.2f}", f"€ {bagli['iva_deb']:,.2f}", f"€ {tropea['iva_deb']:,.2f}"],
        ["IVA a Credito", f"€ {tot['iva_cred']:,.2f}", f"€ {bagli['iva_cred']:,.2f}", f"€ {tropea['iva_cred']:,.2f}"],
        ["Liquidazione IVA", f"€ {tot['liq_iva']:,.2f}", f"€ {bagli['liq_iva']:,.2f}", f"€ {tropea['liq_iva']:,.2f}"],
        ["UTILE NETTO / CASSA", f"€ {tot['utile']:,.2f}", f"€ {bagli['utile']:,.2f}", f"€ {tropea['utile']:,.2f}"],
    ]

    tab = Table(dati_tabella, colWidths=[160, 110, 110, 110])
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d9e1f2")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementi.append(tab)
    doc.build(elementi)
    return buffer.getvalue()

