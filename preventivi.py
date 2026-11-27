import os
import io
from datetime import datetime
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage
from database import carica_tabella, esegui_query

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOCIO_1, SOCIO_2 = "BAGLI", "TROPEA"

def trova_logo():
    estensioni_valide = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    if os.path.exists(BASE_DIR):
        for file in os.listdir(BASE_DIR):
            if "logo" in file.lower() and file.lower().endswith(estensioni_valide):
                return os.path.join(BASE_DIR, file)
    return None

def genera_numero_progressivo(df_all):
    anno_corrente = datetime.now().year
    suffisso = f"/{anno_corrente}"
    max_num = 0
    if not df_all.empty and "num" in df_all.columns:
        for num_str in df_all["num"].dropna():
            num_str = str(num_str).strip()
            if num_str.endswith(suffisso):
                parte_num = num_str[:-len(suffisso)].strip()
                if parte_num.isdigit():
                    max_num = max(max_num, int(parte_num))
            elif num_str.isdigit():
                max_num = max(max_num, int(num_str))
    return f"{max_num + 1}/{anno_corrente}"

def genera_pdf_bytes(row_dict, percorso_logo):
    buffer_pdf = io.BytesIO()
    num_doc = str(row_dict["num"])
    data_doc = str(row_dict["data_doc"])
    cliente = str(row_dict["cliente"])
    indirizzo = str(row_dict.get("indirizzo") or "")
    telefono = str(row_dict.get("telefono") or "")
    descrizione = str(row_dict.get("descrizione") or "")
    importo_val = float(row_dict.get("importo") or 0.0)
    importo_str = f"{importo_val:,.2f}"

    data_formattata = data_doc
    try:
        dt_obj = datetime.strptime(data_doc.strip(), "%Y-%m-%d")
        data_formattata = dt_obj.strftime("%d/%m/%Y")
    except ValueError:
        pass

    doc = SimpleDocTemplate(
        buffer_pdf, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=22,
        title=f"Preventivo_{num_doc}"
    )
    story = []

    BLU_LOGO = colors.HexColor("#1b2340")
    BLU_CHIARO = colors.HexColor("#eef2f8")
    GIALLO_LOGO = colors.HexColor("#f2b718")
    GRIGIO_BORDO = colors.HexColor("#d0d7de")
    GRIGIO_TESTO = colors.HexColor("#333333")

    s_badge_titolo = ParagraphStyle("BadgeTit", fontName="Helvetica-Bold", fontSize=11, alignment=1, textColor=GIALLO_LOGO)
    s_badge_sub = ParagraphStyle("BadgeSub", fontName="Helvetica-Bold", fontSize=9, alignment=1, textColor=colors.white)
    s_spett_label = ParagraphStyle("SpettLbl", fontName="Helvetica-Bold", fontSize=8, textColor=BLU_LOGO)
    s_spett_val = ParagraphStyle("SpettVal", fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.black)
    s_cell = ParagraphStyle("Cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.black)
    s_cond = ParagraphStyle("Cond", fontName="Helvetica", fontSize=7.5, leading=10, textColor=GRIGIO_TESTO)
    s_f_sx = ParagraphStyle("FSX", fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=GRIGIO_TESTO)
    s_f_dx = ParagraphStyle("FDX", fontName="Helvetica-Bold", fontSize=8.5, leading=12, alignment=2, textColor=BLU_LOGO)

    if percorso_logo and os.path.exists(percorso_logo):
        try:
            with PILImage.open(percorso_logo) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    sfondo = PILImage.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    sfondo.paste(img, mask=img.split()[-1])
                    img = sfondo
                else:
                    img = img.convert("RGB")
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="JPEG", quality=95)
                img_buffer.seek(0)
            logo_cell = Image(img_buffer, width=310, height=78, kind="proportional")
            logo_cell.hAlign = "LEFT"
        except Exception:
            logo_cell = Image(percorso_logo, width=310, height=78, kind="proportional")
            logo_cell.hAlign = "LEFT"
    else:
        logo_cell = Paragraph("<b><font size='16' color='#1b2340'>CARTONGESSO &amp; COLOR GROUP S.r.l.</font></b><br/><font size='8' color='#333333'>Opere in Cartongesso, Controsoffitti, Isolamenti e Tinteggiature</font>", s_spett_val)

    badge_tab = Table(
        [[Paragraph(f"PREVENTIVO N. {num_doc}", s_badge_titolo)], [Paragraph(f"Data: {data_formattata}", s_badge_sub)]],
        colWidths=[165]
    )
    badge_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLU_LOGO),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    t_top = Table([[logo_cell, badge_tab]], colWidths=[374, 165])
    t_top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(t_top)
    story.append(Spacer(1, 10))

    testo_cli = f"<b>{cliente}</b>"
    if indirizzo:
        testo_cli += f"<br/>{indirizzo}"
    if telefono:
        testo_cli += f"<br/>Tel: {telefono}"

    box_cli = Table([[Paragraph("SPETT.LE CLIENTE", s_spett_label)], [Paragraph(testo_cli, s_spett_val)]], colWidths=[539])
    box_cli.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLU_CHIARO),
        ("BOX", (0, 0), (-1, -1), 0.5, GRIGIO_BORDO),
        ("LINEBEFORE", (0, 0), (0, -1), 3, GIALLO_LOGO),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(box_cli)
    story.append(Spacer(1, 12))

    righe_lavori = [["DESCRIZIONE LAVORAZIONI", "MISURE", "PREZZO UNIT.", "TOTALE"]]
    for riga in descrizione.strip().split("\n"):
        if not riga.strip():
            continue
        parti = [p.strip() for p in riga.split("|")]
        if len(parti) >= 4:
            righe_lavori.append([Paragraph(parti[0], s_cell), parti[1], parti[2], parti[3]])
        else:
            righe_lavori.append([Paragraph(riga.strip(), s_cell), "-", "-", "-"])

    righe_lavori.append(["", "", "TOTALE (€)", f"€ {importo_str}"])

    t_lav = Table(righe_lavori, colWidths=[319, 65, 75, 80])
    t_lav.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLU_LOGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 1), (1, -2), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -2), 0.5, GRIGIO_BORDO),
        ("BACKGROUND", (2, -1), (-1, -1), GIALLO_LOGO),
        ("TEXTCOLOR", (2, -1), (-1, -1), BLU_LOGO),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_lav)
    story.append(Spacer(1, 12))

    box_cond = Table([[Paragraph("<b>NOTE E CONDIZIONI:</b> Gli importi indicati si intendono IVA esclusa ove applicabile. Validità offerta 30 giorni. Pagamenti da concordare all'accettazione.", s_cond)]], colWidths=[539])
    box_cond.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, GRIGIO_BORDO),
        ("LINEBEFORE", (0, 0), (0, -1), 3, BLU_LOGO),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(box_cond)
    story.append(Spacer(1, 14))

    dati_piede_sx = (
        "<font color='#1b2340'><b>CARTONGESSO &amp; COLOR GROUP S.r.l.</b></font><br/>"
        "Strada 11 Cosentini Trav. C3 N.19 - 95018 RIPOSTO (CT)<br/>"
        "Cod. Fisc. e P.IVA: 06150370879 | COD. SDI: KRRH6B9<br/><br/>"
        "<font color='#1b2340'><b>FIRMA AZIENDA:</b></font> ___________________________"
    )
    dati_piede_dx = "CLIENTE (per accettazione)<br/><br/><br/>___________________________"

    t_firme = Table([[Paragraph(dati_piede_sx, s_f_sx), Paragraph(dati_piede_dx, s_f_dx)]], colWidths=[300, 239])
    t_firme.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 1, GRIGIO_BORDO),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_firme)
    doc.build(story)
    buffer_pdf.seek(0)
    return buffer_pdf.getvalue()
def mostra_preventivi():
    if "nuovo_desc" not in st.session_state:
        st.session_state.nuovo_desc = ""
    if "nuovo_imp" not in st.session_state:
        st.session_state.nuovo_imp = 0.0

    percorso_logo = trova_logo()

    col_logo, col_titolo = st.columns([1, 3])
    with col_logo:
        if percorso_logo and os.path.exists(percorso_logo):
            st.image(percorso_logo, width=220)
        else:
            logo_caricato = st.file_uploader("Carica Logo Aziendale (.png/.jpg)", type=["png", "jpg", "jpeg", "webp"])
            if logo_caricato is not None:
                ext = os.path.splitext(logo_caricato.name)[1]
                with open(os.path.join(BASE_DIR, f"logo_aziendale{ext}"), "wb") as f:
                    f.write(logo_caricato.getbuffer())
                st.rerun()
    with col_titolo:
        st.title("📋 Cartongesso & Color Group S.r.l.")
        st.caption("Sistema Gestionale Preventivi Soci — Bagli & Tropea (Cloud Condiviso)")

    df_all = carica_tabella("preventivi")
    if not df_all.empty:
        df_all = df_all.sort_values(by="id", ascending=False)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Registro Preventivi",
        "➕ Nuovo Preventivo",
        "✏️ Modifica / Elimina",
        "🏷️ Listino Prezzi"
    ])

    with tab1:
        if df_all.empty:
            st.info("Nessun preventivo presente nel database cloud.")
        else:
            c_f1, c_f2 = st.columns([2, 1])
            cerca_prev = c_f1.text_input("🔍 Cerca per numero preventivo o cliente:", placeholder="Es. 1/2026 o Rossi...")
            stato_f = c_f2.selectbox("Stato Preventivo:", options=["Tutti", "In Attesa", "Approvato", "Rifiutato"])

            df_filtrato = df_all.copy()
            if stato_f != "Tutti":
                df_filtrato = df_filtrato[df_filtrato["stato"] == stato_f]
            if cerca_prev:
                m_num = df_filtrato["num"].astype(str).str.contains(cerca_prev, case=False, na=False)
                m_cli = df_filtrato["cliente"].astype(str).str.contains(cerca_prev, case=False, na=False)
                df_filtrato = df_filtrato[m_num | m_cli]

            for socio in [SOCIO_1, SOCIO_2]:
                st.subheader(f"👤 Socio: {socio}")
                df_s = df_filtrato[df_filtrato["socio"].astype(str).str.upper() == socio]
                totale_s = df_s["importo"].sum() if not df_s.empty else 0.0
                st.metric("Volume Preventivi", f"€ {totale_s:,.2f}", f"{len(df_s)} preventivi")

                if df_s.empty:
                    st.write("Nessun preventivo trovato per questo socio.")
                else:
                    st.dataframe(
                        df_s[["num", "data_doc", "cliente", "indirizzo", "telefono", "descrizione", "importo", "stato"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "num": "N° Prev", "data_doc": "Data", "cliente": "Cliente",
                            "indirizzo": "Indirizzo/Città", "telefono": "Telefono",
                            "descrizione": "Descrizione Lavori",
                            "importo": st.column_config.NumberColumn("Importo (€)", format="€ %.2f"),
                            "stato": "Stato"
                        }
                    )
                st.divider()

            if not df_filtrato.empty:
                st.subheader("📄 Genera e Scarica PDF")
                opzioni_pdf = {
                    f"N° {r['num']} - {r['cliente']} (€ {float(r['importo']):,.2f})": r
                    for _, r in df_filtrato.iterrows()
                }
                scelta_pdf = st.selectbox("Seleziona preventivo da stampare:", list(opzioni_pdf.keys()))
                riga_scelta = opzioni_pdf[scelta_pdf]
                pdf_bytes = genera_pdf_bytes(riga_scelta, percorso_logo)

                st.download_button(
                    label="📄 Scarica Preventivo in PDF",
                    data=pdf_bytes,
                    file_name=f"Preventivo_{str(riga_scelta['num']).replace('/', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )

    with tab2:
        st.subheader("Compilazione Nuovo Preventivo")
        df_listino = carica_tabella("listino")

        with st.expander("➕ Inserisci voce dal Listino Prezzi", expanded=True):
            if not df_listino.empty:
                dict_listino = {
                    f"{r['codice']} - {str(r['descrizione'])[:55]}... (€ {float(r['prezzo_unitario']):.2f}/{r['unita_misura']})": r
                    for _, r in df_listino.iterrows()
                }
                c1, c2, c3 = st.columns([4, 1, 1])
                voce_sel = c1.selectbox("Voce di listino", list(dict_listino.keys()))
                qta = c2.number_input("Quantità (MQ/ML)", min_value=0.0, step=1.0, value=0.0)
                if c3.button("Aggiungi riga", use_container_width=True):
                    if qta > 0:
                        row_l = dict_listino[voce_sel]
                        prezzo = float(row_l["prezzo_unitario"])
                        tot_riga = qta * prezzo
                        riga_testo = f"{row_l['descrizione']} | {qta} {row_l['unita_misura']} | € {prezzo:,.2f} | € {tot_riga:,.2f}\n"
                        st.session_state.nuovo_desc += riga_testo
                        st.session_state.nuovo_imp += tot_riga
                        st.rerun()
            else:
                st.warning("Nessuna voce presente nel listino.")

        with st.form("form_nuovo_prev"):
            col1, col2, col3, col4 = st.columns(4)
            num_prev = col1.text_input("N° Preventivo", value=genera_numero_progressivo(df_all))
            data_prev = col2.date_input("Data", value=datetime.now())
            socio_prev = col3.selectbox("Socio Gestore", [SOCIO_1, SOCIO_2])
            stato_prev = col4.selectbox("Stato", ["In Attesa", "Approvato", "Rifiutato"])

            c_ana1, c_ana2, c_ana3 = st.columns([2, 2, 1])
            cliente = c_ana1.text_input("Cliente *")
            indirizzo = c_ana2.text_input("Indirizzo / Città")
            telefono = c_ana3.text_input("Telefono")

            descrizione = st.text_area(
                "Dettagli Lavorazioni (formato tabella PDF: Descrizione | Misure | Prezzo Unit. | Totale)",
                value=st.session_state.nuovo_desc,
                height=180
            )
            importo = st.number_input("Importo Totale (€)", min_value=0.0, step=10.0, value=float(st.session_state.nuovo_imp))

            if st.form_submit_button("💾 Salva Preventivo", type="primary"):
                if not cliente.strip():
                    st.error("Inserisci il nome del cliente.")
                else:
                    esegui_query(
                        '''INSERT INTO preventivi (num, data_doc, cliente, indirizzo, telefono, descrizione, importo, socio, stato) 
                           VALUES (:n, :d, :c, :i, :t, :desc, :imp, :s, :st)''',
                        {
                            "n": num_prev.strip(), "d": data_prev.strftime("%Y-%m-%d"),
                            "c": cliente.strip().upper(), "i": indirizzo.strip(),
                            "t": telefono.strip(), "desc": descrizione,
                            "imp": importo, "s": socio_prev, "st": stato_prev
                        }
                    )
                    st.session_state.nuovo_desc = ""
                    st.session_state.nuovo_imp = 0.0
                    st.success("✅ Preventivo salvato su Cloud!")
                    st.rerun()
    with tab3:
        st.subheader("Modifica o Elimina Preventivo")
        if df_all.empty:
            st.info("Nessun preventivo da modificare.")
        else:
            opzioni = {
                f"ID {int(r['id'])} | N° {r['num']} - {r['cliente']} ({r['socio']})": r
                for _, r in df_all.iterrows()
            }
            scelta = st.selectbox("Seleziona preventivo:", list(opzioni.keys()))
            record = opzioni[scelta]

            with st.form("form_modifica_prev"):
                c1, c2, c3, c4 = st.columns(4)
                m_num = c1.text_input("N° Preventivo", value=str(record["num"]))
                m_data = c2.text_input("Data (AAAA-MM-GG)", value=str(record["data_doc"]))
                m_socio = c3.selectbox("Socio", [SOCIO_1, SOCIO_2], index=0 if record["socio"] == SOCIO_1 else 1)
                stati = ["In Attesa", "Approvato", "Rifiutato"]
                idx_stato = stati.index(record["stato"]) if record["stato"] in stati else 0
                m_stato = c4.selectbox("Stato", stati, index=idx_stato)

                c_a1, c_a2, c_a3 = st.columns([2, 2, 1])
                m_cli = c_a1.text_input("Cliente", value=str(record["cliente"]))
                m_ind = c_a2.text_input("Indirizzo", value=str(record["indirizzo"] or ""))
                m_tel = c_a3.text_input("Telefono", value=str(record["telefono"] or ""))

                m_desc = st.text_area("Descrizione Lavori", value=str(record["descrizione"] or ""), height=160)
                m_imp = st.number_input("Importo Totale (€)", min_value=0.0, step=10.0, value=float(record["importo"] or 0.0))

                if st.form_submit_button("💾 Aggiorna Preventivo", type="primary"):
                    esegui_query(
                        '''UPDATE preventivi 
                           SET num=:n, data_doc=:d, socio=:s, stato=:st, cliente=:c, indirizzo=:i, telefono=:t, descrizione=:desc, importo=:imp 
                           WHERE id=:id''',
                        {
                            "n": m_num.strip(), "d": m_data.strip(), "s": m_socio, "st": m_stato,
                            "c": m_cli.strip().upper(), "i": m_ind.strip(), "t": m_tel.strip(),
                            "desc": m_desc, "imp": m_imp, "id": int(record["id"])
                        }
                    )
                    st.success("✅ Preventivo aggiornato!")
                    st.rerun()

            if st.button("🗑️ Elimina Definitivamente questo Preventivo"):
                esegui_query("DELETE FROM preventivi WHERE id=:id", {"id": int(record["id"])})
                st.success("🗑️ Preventivo eliminato!")
                st.rerun()

    with tab4:
        st.subheader("🏷️ Gestione Listino Lavorazioni")
        with st.form("nuova_voce_listino"):
            l1, l2, l3, l4 = st.columns([1.2, 3, 1.2, 1])
            l_cod = l1.text_input("Codice", placeholder="Es. CART03")
            l_desc = l2.text_input("Descrizione Lavorazione")
            l_prez = l3.number_input("Prezzo (€)", min_value=0.0, step=1.0)
            l_um = l4.selectbox("U.M.", ["mq", "ml", "mc", "a corpo", "ore"])
            if st.form_submit_button("➕ Aggiungi al Listino", type="primary"):
                if l_cod.strip() and l_desc.strip():
                    try:
                        esegui_query(
                            "INSERT INTO listino (codice, descrizione, prezzo_unitario, unita_misura) VALUES (:c, :d, :p, :u)",
                            {"c": l_cod.strip().upper(), "d": l_desc.strip().upper(), "p": l_prez, "u": l_um}
                        )
                        st.success("✅ Voce aggiunta al listino!")
                        st.rerun()
                    except Exception:
                        st.error("⚠️ Codice già esistente nel listino.")

        if not df_listino.empty:
            st.dataframe(df_listino[["codice", "descrizione", "prezzo_unitario", "unita_misura"]], use_container_width=True, hide_index=True)

                        
