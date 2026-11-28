import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def _crea_tabella_stile(dati, col_widths):
    tab = Table(dati, colWidths=col_widths)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d9e1f2")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    return tab

def genera_pdf_bilancio(periodo, anno, tot, bagli, tropea):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementi = []

    elementi.append(Paragraph("<b>SRL CONTROL PRO • RENDICONTO CONTABILE GENERALE</b>", styles["Title"]))
    elementi.append(Paragraph(f"Periodo: <b>{periodo}</b> • Anno: <b>{anno}</b> • Data stampa: {date.today()}", styles["Normal"]))
    elementi.append(Spacer(1, 16))

    dati_tabella = [
        ["VOCE DI BILANCIO", "TOTALE SRL", "SOCIO BAGLI", "SOCIO TROPEA"],
        ["Incassi Lordi", f"€ {tot['lordi']:,.2f}", f"€ {bagli['lordi']:,.2f}", f"€ {tropea['lordi']:,.2f}"],
        ["Note di Credito", f"€ {tot['nc']:,.2f}", f"€ {bagli['nc']:,.2f}", f"€ {tropea['nc']:,.2f}"],
        ["Spese Fornitori (tot.)", f"€ {tot['fornitori']:,.2f}", f"€ {bagli['fornitori']:,.2f}", f"€ {tropea['fornitori']:,.2f}"],
        ["   • di cui Materiali", f"€ {tot.get('spese_materiali', 0.0):,.2f}", f"€ {bagli.get('spese_materiali', 0.0):,.2f}", f"€ {tropea.get('spese_materiali', 0.0):,.2f}"],
        ["   • di cui Carburante", f"€ {tot.get('spese_carburante', 0.0):,.2f}", f"€ {bagli.get('spese_carburante', 0.0):,.2f}", f"€ {tropea.get('spese_carburante', 0.0):,.2f}"],
        ["   • di cui Altre Spese", f"€ {tot.get('spese_altre', 0.0):,.2f}", f"€ {bagli.get('spese_altre', 0.0):,.2f}", f"€ {tropea.get('spese_altre', 0.0):,.2f}"],
        ["Costo Dipendenti (tot.)", f"€ {tot['dipendenti']:,.2f}", f"€ {bagli['dipendenti']:,.2f}", f"€ {tropea['dipendenti']:,.2f}"],
        ["   • di cui Cassa Edile", f"€ {tot['cassa_edile']:,.2f}", f"€ {bagli['cassa_edile']:,.2f}", f"€ {tropea['cassa_edile']:,.2f}"],
        ["IVA a Debito", f"€ {tot['iva_deb']:,.2f}", f"€ {bagli['iva_deb']:,.2f}", f"€ {tropea['iva_deb']:,.2f}"],
        ["IVA a Credito", f"€ {tot['iva_cred']:,.2f}", f"€ {bagli['iva_cred']:,.2f}", f"€ {tropea['iva_cred']:,.2f}"],
        ["Liquidazione IVA", f"€ {tot['liq_iva']:,.2f}", f"€ {bagli['liq_iva']:,.2f}", f"€ {tropea['liq_iva']:,.2f}"],
        ["UTILE NETTO / CASSA", f"€ {tot['utile']:,.2f}", f"€ {bagli['utile']:,.2f}", f"€ {tropea['utile']:,.2f}"],
    ]

    elementi.append(_crea_tabella_stile(dati_tabella, [175, 105, 105, 105]))
    doc.build(elementi)
    return buffer.getvalue()

def genera_pdf_socio(nome_socio, periodo, anno, d):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementi = []

    elementi.append(Paragraph(f"<b>RENDICONTO PERSONALE • SOCIO {nome_socio}</b>", styles["Title"]))
    elementi.append(Paragraph(f"Periodo: <b>{periodo}</b> • Anno: <b>{anno}</b> • Data stampa: {date.today()}", styles["Normal"]))
    elementi.append(Spacer(1, 16))

    stato_iva = "A Credito" if d["liq_iva"] >= 0 else "A Debito"
    dati_tabella = [
        ["VOCE DI BILANCIO", f"IMPORTO ({nome_socio})"],
        ["Incassi Lordi", f"€ {d['lordi']:,.2f}"],
        ["Note di Credito", f"€ {d['nc']:,.2f}"],
        ["Spese Fornitori (tot.)", f"€ {d['fornitori']:,.2f}"],
        ["   • di cui Materiali", f"€ {d.get('spese_materiali', 0.0):,.2f}"],
        ["   • di cui Carburante", f"€ {d.get('spese_carburante', 0.0):,.2f}"],
        ["   • di cui Altre Spese", f"€ {d.get('spese_altre', 0.0):,.2f}"],
        ["Costo Dipendenti (incl. Cassa Edile)", f"€ {d['dipendenti']:,.2f}"],
        ["   • di cui Cassa Edile Registrata", f"€ {d['cassa_edile']:,.2f}"],
        ["IVA a Debito", f"€ {d['iva_deb']:,.2f}"],
        ["IVA a Credito", f"€ {d['iva_cred']:,.2f}"],
        [f"Liquidazione IVA ({stato_iva})", f"€ {abs(d['liq_iva']):,.2f}"],
        ["UTILE NETTO / LIQUIDITÀ CASSA", f"€ {d['utile']:,.2f}"],
    ]

    elementi.append(_crea_tabella_stile(dati_tabella, [280, 180]))
    doc.build(elementi)
    return buffer.getvalue()



