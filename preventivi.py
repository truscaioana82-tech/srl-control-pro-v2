import io
import streamlit as st
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from rubrica import ottieni_nomi_rubrica

def _genera_pdf_preventivo(num_prev, data_prev, cliente, oggetto, df_voci, iva_perc, note_finali):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elementi = []

    # Intestazione Aziendale
    elementi.append(Paragraph("<b>BAGLI & TROPEA S.R.L.</b>", styles["Title"]))
    elementi.append(Paragraph("Impresa Edile & Ristrutturazioni", styles["Normal"]))
    elementi.append(Spacer(1, 15))

    # Dati Preventivo e Cliente
    dati_testa = [
        [Paragraph(f"<b>PREVENTIVO N. {num_prev}</b><br/>Data: {data_prev}", styles["Normal"]),
         Paragraph(f"<b>SPETT.LE CLIENTE:</b><br/>{cliente}", styles["Normal"])],
        [Paragraph(f"<b>Oggetto / Cantiere:</b> {oggetto}", styles["Normal"]), ""]
    ]
    tab_testa = Table(dati_testa, colWidths=[260, 260])
    tab_testa.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f6f9")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("SPAN", (0, 1), (1, 1)),
    ]))
    elementi.append(tab_testa)
    elementi.append(Spacer(1, 18))

    # Tabella Voci di Lavoro
    righe_tab = [["DESCRIZIONE LAVORAZIONI", "U.M.", "Q.TÀ", "PREZZO UNIT.", "TOTALE"]]
    tot_imponibile = 0.0

    for _, r in df_voci.iterrows():
        desc = str(r.get("Descrizione Lavorazione", "")).strip()
        if not desc:
            continue
        um = str(r.get("U.M.", "a corpo"))
        qta = float(r.get("Quantità") or 0.0)
        prezzo = float(r.get("Prezzo Unitario (€)") or 0.0)
        tot_riga = qta * prezzo
        tot_imponibile += tot_riga

        righe_tab.append([
            Paragraph(desc, styles["Normal"]),
            um,
            f"{qta:,.2f}",
            f"€ {prezzo:,.2f}",
            f"€ {tot_riga:,.2f}"
        ])

    importo_iva = tot_imponibile * (iva_perc / 100.0)
    tot_generale = tot_imponibile + importo_iva

    righe_tab.append(["", "", "", "IMPONIBILE:", f"€ {tot_imponibile:,.2f}"])
    righe_tab.append(["", "", "", f"IVA ({iva_perc}%):", f"€ {importo_iva:,.2f}"])
    righe_tab.append(["", "", "", "TOTALE PREVENTIVO:", f"€ {tot_generale:,.2f}"])

    tab_voci = Table(righe_tab, colWidths=[240, 45, 55, 90, 90])
    tab_voci.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (2, -4), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -4), 0.5, colors.grey),
        ("LINEABOVE", (3, -3), (-1, -3), 0.8, colors.grey),
        ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#d9e1f2")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elementi.append(tab_voci)
    elementi.append(Spacer(1, 20))

    if note_finali.strip():
        elementi.append(Paragraph("<b>Note e Condizioni:</b>", styles["Normal"]))
        elementi.append(Paragraph(note_finali.replace("\n", "<br/>"), styles["Normal"]))
        elementi.append(Spacer(1, 25))

    elementi.append(Paragraph("Timbro e Firma per Accettazione: _______________________________", styles["Normal"]))

    doc.build(elementi)
    return buffer.getvalue()
def mostra_preventivi():
    st.title("📋 Generatore Preventivi & Computi Rapidi")
    
    nomi_clienti = ottieni_nomi_rubrica(["CLIENTE"])
    
    c1, c2, c3 = st.columns([1, 1, 1.5])
    num_prev = c1.text_input("Numero Preventivo", value=f"01/{date.today().year}")
    data_prev = c2.date_input("Data Preventivo", value=date.today())
    iva_scelta = c3.selectbox("Aliquota IVA applicata", options=[10, 22, 4, 0], format_func=lambda x: f"{x}% {'(Ristrutturazione Edile)' if x == 10 else ('(Ordinaria)' if x == 22 else '')}")

    c4, c5 = st.columns(2)
    cli_rubrica = c4.selectbox("Scegli Cliente da Rubrica", options=["-- Scrivi nuovo cliente --"] + nomi_clienti)
    cli_nuovo = c5.text_input("Oppure scrivi Nome / Ragione Sociale Cliente")
    cliente_finale = cli_nuovo.strip().upper() if cli_nuovo.strip() else (cli_rubrica if cli_rubrica != "-- Scrivi nuovo cliente --" else "CLIENTE DA DEFINIRE")

    oggetto_lavori = st.text_input("🏗️ Oggetto / Indirizzo del Cantiere", placeholder="Es. Lavori di ristrutturazione appartamento in Via Etnea - Mascalucia")

    st.divider()
    st.subheader("1. Inserisci le Voci di Lavoro")
    st.caption("Clicca sul segno **+** in fondo alla tabella per aggiungere nuove righe di lavoro.")

    if "righe_preventivo" not in st.session_state:
        st.session_state["righe_preventivo"] = pd.DataFrame([
            {"Descrizione Lavorazione": "Allestimento cantiere, ponteggi e messa in sicurezza", "U.M.": "a corpo", "Quantità": 1.0, "Prezzo Unitario (€)": 0.0},
            {"Descrizione Lavorazione": "Demolizione pavimento esistente e trasporto a discarica autorizzata", "U.M.": "mq", "Quantità": 1.0, "Prezzo Unitario (€)": 0.0},
        ])

    df_editato = st.data_editor(
        st.session_state["righe_preventivo"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Descrizione Lavorazione": st.column_config.TextColumn("Descrizione Lavorazione", width="large"),
            "U.M.": st.column_config.SelectboxColumn("U.M.", options=["a corpo", "mq", "ml", "mc", "ore", "cad."], default="mq"),
            "Quantità": st.column_config.NumberColumn("Quantità", min_value=0.0, step=1.0, format="%.2f"),
            "Prezzo Unitario (€)": st.column_config.NumberColumn("Prezzo Unitario (€)", min_value=0.0, step=10.0, format="€ %.2f")
        },
        key="editor_voci_preventivo"
    )

    # Calcoli in tempo reale
    imp_tot = (df_editato["Quantità"].fillna(0.0) * df_editato["Prezzo Unitario (€)"].fillna(0.0)).sum()
    iva_tot = imp_tot * (iva_scelta / 100.0)
    lordo_tot = imp_tot + iva_tot

    m1, m2, m3 = st.columns(3)
    m1.metric("💶 Totale Imponibile", f"€ {imp_tot:,.2f}")
    m2.metric(f"🧾 IVA ({iva_scelta}%)", f"€ {iva_tot:,.2f}")
    m3.metric("💰 Totale Preventivo", f"€ {lordo_tot:,.2f}")

    note_cond = st.text_area(
        "Note, tempi di esecuzione e modalità di pagamento",
        value="Validità offerta: 30 giorni.\nPagamenti: 30% all'accettazione, 40% a stato avanzamento lavori, 30% a fine lavori."
    )

    pdf_prev = _genera_pdf_preventivo(
        num_prev=num_prev,
        data_prev=data_prev.strftime("%d/%m/%Y"),
        cliente=cliente_finale,
        oggetto=oggetto_lavori or "Lavori edili vari",
        df_voci=df_editato,
        iva_perc=iva_scelta,
        note_finali=note_cond
    )

    st.download_button(
        label="📄 Scarica Preventivo in PDF (Pronto per Cliente)",
        data=pdf_prev,
        file_name=f"Preventivo_{num_prev.replace('/', '-')}_{cliente_finale.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
