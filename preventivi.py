import os
import io
import base64
from datetime import datetime, date
import streamlit as st
import streamlit.components.v1 as components
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


def logo_in_base64():
    percorso = trova_logo()
    if percorso and os.path.exists(percorso):
        try:
            with open(percorso, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(percorso)[1].lower().replace(".", "")
            if ext == "jpg":
                ext = "jpeg"
            return f"data:image/{ext};base64,{b64}"
        except Exception:
            return None
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


def renderizza_anteprima_preventivo(num_doc, data_doc, cliente, indirizzo, telefono, descrizione, importo_val):
    righe_html = ""
    righe_valide = 0
    for riga in str(descrizione or "").strip().split("\n"):
        if not riga.strip():
            continue
        righe_valide += 1
        parti = [p.strip() for p in riga.split("|")]
        if len(parti) >= 4:
            righe_html += (
                f"<tr>"
                f"<td style='padding:7px;border:1px solid #d0d7de;'>{parti[0]}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:center;'>{parti[1]}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>{parti[2]}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>{parti[3]}</td>"
                f"</tr>"
            )
        else:
            righe_html += (
                f"<tr>"
                f"<td style='padding:7px;border:1px solid #d0d7de;'>{riga.strip()}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:center;'>-</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>-</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>-</td>"
                f"</tr>"
            )

    if not righe_html:
        righe_html = "<tr><td colspan='4' style='padding:10px;border:1px solid #d0d7de;color:#777;text-align:center;'>Nessuna voce inserita</td></tr>"

    logo_uri = logo_in_base64()
    if logo_uri:
        intestazione_sx = f"<img src='{logo_uri}' style='max-height:70px;max-width:290px;object-fit:contain;' />"
    else:
        intestazione_sx = (
            "<div style='font-size:18px;font-weight:bold;color:#1b2340;'>CARTONGESSO &amp; COLOR GROUP S.r.l.</div>"
            "<div style='font-size:12px;color:#555555;'>Opere in Cartongesso, Controsoffitti, Isolamenti e Tinteggiature</div>"
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ margin: 0; padding: 6px; background: transparent; font-family: Arial, Helvetica, sans-serif; }}
    .foglio {{ background: #ffffff; color: #111111; padding: 24px; border: 1px solid #d0d7de; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
</style>
</head>
<body>
    <div class="foglio">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #1b2340;padding-bottom:12px;margin-bottom:16px;">
            <div>{intestazione_sx}</div>
            <div style="background:#1b2340;color:#ffffff;padding:10px 16px;border-radius:4px;text-align:center;min-width:150px;">
                <div style="color:#f2b718;font-weight:bold;font-size:13px;">PREVENTIVO N. {num_doc}</div>
                <div style="font-size:11px;margin-top:3px;">Data: {data_doc}</div>
            </div>
        </div>
        <div style="background:#eef2f8;border-left:4px solid #f2b718;padding:10px 14px;margin-bottom:16px;font-size:13px;">
            <strong style="color:#1b2340;font-size:11px;letter-spacing:0.5px;">SPETT.LE CLIENTE</strong><br/>
            <strong style="font-size:14px;">{cliente or '---'}</strong><br/>
            {f'{indirizzo}<br/>' if indirizzo else ''}
            {f'Tel: {telefono}' if telefono else ''}
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:14px;">
            <thead>
                <tr style="background:#1b2340;color:#ffffff;">
                    <th style="padding:8px;text-align:left;width:52%;">DESCRIZIONE LAVORAZIONI</th>
                    <th style="padding:8px;text-align:center;width:16%;">MISURE</th>
                    <th style="padding:8px;text-align:right;width:16%;">PREZZO UNIT.</th>
                    <th style="padding:8px;text-align:right;width:16%;">TOTALE</th>
                </tr>
            </thead>
            <tbody>
                {righe_html}
                <tr>
                    <td colspan="2"></td>
                    <td style="background:#f2b718;color:#1b2340;font-weight:bold;padding:8px;text-align:right;">TOTALE (€)</td>
                    <td style="background:#f2b718;color:#1b2340;font-weight:bold;padding:8px;text-align:right;">€ {float(importo_val or 0.0):,.2f}</td>
                </tr>
            </tbody>
        </table>
        <div style="font-size:11px;color:#444444;border-left:3px solid #1b2340;padding-left:8px;margin-bottom:16px;">
            <strong>NOTE E CONDIZIONI:</strong> Gli importi indicati si intendono IVA esclusa ove applicabile. Validità offerta 30 giorni.
        </div>
        <div style="border-top:1px solid #d0d7de;padding-top:10px;display:flex;justify-content:space-between;font-size:11px;color:#555555;">
            <div><strong>CARTONGESSO &amp; COLOR GROUP S.r.l.</strong></div>
            <div style="color:#1b2340;font-weight:bold;">Timbro e Firma per Accettazione ______________________</div>
        </div>
    </div>
</body>
</html>"""

    altezza_box = 370 + (max(1, righe_valide) * 34)
    components.html(html, height=altezza_box, scrolling=True)
def genera_pdf_bytes(row_dict, percorso_logo):
    buffer_pdf = io.BytesIO()
    num_doc = str(row_dict["num"])
    data_doc = str(row_dict["data_doc"])
    cliente = str(row_dict["cliente"])
    indirizzo = str(row_dict.get("indirizzo") or "")
    telefono = str(row_dict.get("telefono") or "")
    descrizione = str(row_dict.get("descrizione") or "")
    importo_val = float(row_dict.get("importo") or 0.0)
    importo_str = f"€ {importo_val:,.2f}"

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
    s_cell_c = ParagraphStyle("CellC", fontName="Helvetica", fontSize=8.5, leading=11, alignment=1, textColor=colors.black)
    s_cell_r = ParagraphStyle("CellR", fontName="Helvetica", fontSize=8.5, leading=11, alignment=2, textColor=colors.black)
    s_th = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.white)
    s_th_c = ParagraphStyle("THC", fontName="Helvetica-Bold", fontSize=8.5, alignment=1, textColor=colors.white)
    s_th_r = ParagraphStyle("THR", fontName="Helvetica-Bold", fontSize=8.5, alignment=2, textColor=colors.white)
    s_tot = ParagraphStyle("Tot", fontName="Helvetica-Bold", fontSize=9.5, alignment=2, textColor=BLU_LOGO)
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
        logo_cell = Paragraph(
            "<b><font size='16' color='#1b2340'>CARTONGESSO &amp; COLOR GROUP S.r.l.</font></b><br/>"
            "<font size='8' color='#333333'>Opere in Cartongesso, Controsoffitti, Isolamenti e Tinteggiature</font>",
            s_spett_val
        )

    badge_tab = Table(
        [[Paragraph(f"PREVENTIVO N. {num_doc}", s_badge_titolo)],
         [Paragraph(f"Data: {data_formattata}", s_badge_sub)]],
        colWidths=[165]
    )
    badge_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLU_LOGO),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    header_tab = Table([[logo_cell, badge_tab]], colWidths=[374, 165])
    header_tab.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 2, BLU_LOGO),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    ]))
    story.append(header_tab)
    story.append(Spacer(1, 12))

    testo_cliente = f"<b>{cliente}</b>"
    if indirizzo:
        testo_cliente += f"<br/>{indirizzo}"
    if telefono:
        testo_cliente += f"<br/>Tel: {telefono}"

    cliente_tab = Table(
        [[Paragraph("SPETT.LE CLIENTE", s_spett_label)],
         [Paragraph(testo_cliente, s_spett_val)]],
        colWidths=[539]
    )
    cliente_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLU_CHIARO),
        ("LINEBEFORE", (0, 0), (0, -1), 4, GIALLO_LOGO),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    story.append(cliente_tab)
    story.append(Spacer(1, 14))

    dati_tab = [[
        Paragraph("DESCRIZIONE LAVORAZIONI", s_th),
        Paragraph("MISURE", s_th_c),
        Paragraph("PREZZO UNIT.", s_th_r),
        Paragraph("TOTALE", s_th_r),
    ]]

    for riga in descrizione.strip().split("\n"):
        if not riga.strip():
            continue
        parti = [p.strip() for p in riga.split("|")]
        if len(parti) >= 4:
            dati_tab.append([
                Paragraph(parti[0], s_cell),
                Paragraph(parti[1], s_cell_c),
                Paragraph(parti[2], s_cell_r),
                Paragraph(parti[3], s_cell_r),
            ])
        else:
            dati_tab.append([
                Paragraph(riga.strip(), s_cell),
                Paragraph("-", s_cell_c),
                Paragraph("-", s_cell_r),
                Paragraph("-", s_cell_r),
            ])

    dati_tab.append([
        "", "",
        Paragraph("TOTALE (€)", s_tot),
        Paragraph(importo_str, s_tot),
    ])

    voci_tab = Table(dati_tab, colWidths=[289, 80, 85, 85], repeatRows=1)
    n_righe = len(dati_tab)
    voci_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLU_LOGO),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("GRID", (0, 0), (-1, n_righe - 2), 0.5, GRIGIO_BORDO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, n_righe - 2), 6),
        ("BOTTOMPADDING", (0, 1), (-1, n_righe - 2), 6),
        ("BACKGROUND", (2, n_righe - 1), (3, n_righe - 1), GIALLO_LOGO),
        ("TOPPADDING", (2, n_righe - 1), (3, n_righe - 1), 7),
        ("BOTTOMPADDING", (2, n_righe - 1), (3, n_righe - 1), 7),
    ]))
    story.append(voci_tab)
    story.append(Spacer(1, 14))

    cond_tab = Table(
        [[Paragraph("<b>NOTE E CONDIZIONI:</b> Gli importi indicati si intendono IVA esclusa ove applicabile. Validità offerta 30 giorni.", s_cond)]],
        colWidths=[539]
    )
    cond_tab.setStyle(TableStyle([
        ("LINEBEFORE", (0, 0), (0, -1), 3, BLU_LOGO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(cond_tab)
    story.append(Spacer(1, 24))

    footer_tab = Table(
        [[Paragraph("<b>CARTONGESSO &amp; COLOR GROUP S.r.l.</b><br/>Opere in Cartongesso, Controsoffitti e Tinteggiature", s_f_sx),
          Paragraph("Timbro e Firma per Accettazione<br/><br/>______________________________", s_f_dx)]],
        colWidths=[270, 269]
    )
    footer_tab.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, GRIGIO_BORDO),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(footer_tab)

    doc.build(story)
    buffer_pdf.seek(0)
    return buffer_pdf.getvalue()
def mostra_preventivi():
    st.title("📋 Gestione Preventivi")
    tab1, tab2 = st.tabs(["📂 Archivio, Anteprima & PDF", "➕ Nuovo Preventivo"])

    df_all = carica_tabella("preventivi")
    percorso_logo = trova_logo()

    with tab1:
        if not df_all.empty:
            df_all = df_all.dropna(subset=["id"])
            df_all["id"] = df_all["id"].astype(int)
            df_all = df_all.sort_values(by="id", ascending=False)

            st.subheader("1. Elenco Preventivi")
            cerca = st.text_input("🔍 Cerca preventivo per numero o cliente", placeholder="Es. 1/2026 oppure Rossi...")

            df_vis = df_all.copy()
            if cerca:
                m_num = df_vis["num"].astype(str).str.contains(cerca, case=False, na=False)
                m_cli = df_vis["cliente"].astype(str).str.contains(cerca, case=False, na=False)
                df_vis = df_vis[m_num | m_cli]

            st.dataframe(df_vis, use_container_width=True, hide_index=True)

            if not df_vis.empty:
                st.divider()
                st.subheader("2. Anteprima, Stampa PDF, Modifica o Elimina")

                opzioni = {
                    int(r["id"]): f"Preventivo n.{r['num']} | {r['data_doc']} | {r['cliente']} (€ {float(r.get('importo') or 0):,.2f})"
                    for _, r in df_vis.iterrows()
                }
                id_sel = st.selectbox("Seleziona preventivo:", options=list(opzioni.keys()), format_func=lambda x: opzioni[x])
                riga = df_all.set_index("id").loc[id_sel]

                # Anteprima visiva
                st.markdown("### 👁️ Anteprima Documento")
                renderizza_anteprima_preventivo(
                    num_doc=riga["num"],
                    data_doc=riga["data_doc"],
                    cliente=riga["cliente"],
                    indirizzo=riga.get("indirizzo", ""),
                    telefono=riga.get("telefono", ""),
                    descrizione=riga.get("descrizione", ""),
                    importo_val=riga.get("importo", 0.0),
                )

                # Download PDF
                pdf_bytes = genera_pdf_bytes(riga.to_dict(), percorso_logo)
                nome_file_pdf = f"Preventivo_{str(riga['num']).replace('/', '_')}_{str(riga['cliente']).replace(' ', '_')}.pdf"
                st.download_button(
                    label="📥 Scarica Preventivo in PDF",
                    data=pdf_bytes,
                    file_name=nome_file_pdf,
                    mime="application/pdf",
                    type="primary",
                )

                st.divider()
                col_m, col_d = st.columns(2)

                with col_m:
                    with st.expander("✏️ Modifica questo preventivo", expanded=False):
                        with st.form("form_mod_prev"):
                            m1, m2 = st.columns(2)
                            m_num = m1.text_input("Numero", value=str(riga["num"]))
                            m_data = m2.text_input("Data (AAAA-MM-GG)", value=str(riga["data_doc"]))
                            m_cli = st.text_input("Cliente", value=str(riga["cliente"]))
                            m3, m4 = st.columns(2)
                            m_ind = m3.text_input("Indirizzo", value=str(riga.get("indirizzo") or ""))
                            m_tel = m4.text_input("Telefono", value=str(riga.get("telefono") or ""))
                            m_desc = st.text_area(
                                "Voci (una per riga: Descrizione | Misure | Prezzo Unit. | Totale)",
                                value=str(riga.get("descrizione") or ""),
                                height=150,
                            )
                            m_imp = st.number_input("Totale Preventivo (€)", value=float(riga.get("importo") or 0.0), step=50.0)

                            if st.form_submit_button("💾 Salva Modifiche"):
                                esegui_query(
                                    """UPDATE preventivi 
                                       SET num = :num, data_doc = :data_doc, cliente = :cliente, 
                                           indirizzo = :indirizzo, telefono = :telefono, 
                                           descrizione = :descrizione, importo = :importo 
                                       WHERE id = :id""",
                                    {
                                        "num": m_num.strip(),
                                        "data_doc": m_data.strip(),
                                        "cliente": m_cli.strip(),
                                        "indirizzo": m_ind.strip(),
                                        "telefono": m_tel.strip(),
                                        "descrizione": m_desc.strip(),
                                        "importo": m_imp,
                                        "id": id_sel,
                                    },
                                )
                                st.success("✅ Preventivo aggiornato!")
                                st.rerun()

                with col_d:
                    with st.expander("🗑️ Elimina questo preventivo", expanded=False):
                        st.warning(f"Vuoi eliminare il preventivo **n.{riga['num']}** per **{riga['cliente']}**?")
                        if st.button("🚨 Conferma Eliminazione", type="primary"):
                            esegui_query("DELETE FROM preventivi WHERE id = :id", {"id": id_sel})
                            st.success("🗑️ Preventivo eliminato!")
                            st.rerun()
        else:
            st.info("Nessun preventivo salvato in archivio.")

    with tab2:
        st.subheader("➕ Crea Nuovo Preventivo (con Anteprima Live)")
        num_suggerito = genera_numero_progressivo(df_all)

        col_form, col_live = st.columns([1, 1.15])

        with col_form:
            c1, c2 = st.columns(2)
            n_num = c1.text_input("Numero Preventivo", value=num_suggerito)
            n_data = c2.date_input("Data", value=date.today())
            n_cli = st.text_input("Cliente / Azienda", placeholder="Es. Mario Rossi")
            c3, c4 = st.columns(2)
            n_ind = c3.text_input("Indirizzo / Cantiere", placeholder="Es. Via Roma 10, Riposto")
            n_tel = c4.text_input("Telefono", placeholder="Es. 333 1234567")

            st.caption("Formato righe: `Descrizione | Misure | Prezzo Unit. | Totale`")
            n_desc = st.text_area(
                "Descrizione Lavorazioni",
                placeholder="Fornitura e posa pareti in cartongesso | 45 mq | € 35,00 | € 1.575,00\nTinteggiatura pareti interne | 120 mq | € 10,00 | € 1.200,00",
                height=160,
            )
            n_imp = st.number_input("Totale Preventivo (€)", min_value=0.0, value=0.0, step=50.0)

            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 Salva in Archivio", type="primary", use_container_width=True):
                    if not n_cli.strip():
                        st.error("⚠️ Inserisci almeno il nome del cliente.")
                    else:
                        esegui_query(
                            """INSERT INTO preventivi (num, data_doc, cliente, indirizzo, telefono, descrizione, importo)
                               VALUES (:num, :data_doc, :cliente, :indirizzo, :telefono, :descrizione, :importo)""",
                            {
                                "num": n_num.strip(),
                                "data_doc": str(n_data),
                                "cliente": n_cli.strip(),
                                "indirizzo": n_ind.strip(),
                                "telefono": n_tel.strip(),
                                "descrizione": n_desc.strip(),
                                "importo": n_imp,
                            },
                        )
                        st.success("✅ Preventivo salvato con successo!")
                        st.rerun()

            with b2:
                # Permette di scaricare subito il PDF anche prima di salvarlo
                dati_bozza = {
                    "num": n_num,
                    "data_doc": str(n_data),
                    "cliente": n_cli or "Cliente",
                    "indirizzo": n_ind,
                    "telefono": n_tel,
                    "descrizione": n_desc,
                    "importo": n_imp,
                }
                pdf_bozza = genera_pdf_bytes(dati_bozza, percorso_logo)
                st.download_button(
                    label="📥 Scarica PDF Subito",
                    data=pdf_bozza,
                    file_name=f"Preventivo_{n_num.replace('/', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        with col_live:
            st.markdown("#### 👁️ Anteprima in Tempo Reale")
            renderizza_anteprima_preventivo(
                num_doc=n_num,
                data_doc=n_data.strftime("%d/%m/%Y"),
                cliente=n_cli,
                indirizzo=n_ind,
                telefono=n_tel,
                descrizione=n_desc,
                importo_val=n_imp,
            )


