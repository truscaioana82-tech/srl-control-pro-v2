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


def trova_logo():
    estensioni = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    prima_immagine = None
    for radice, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith(estensioni):
                percorso_completo = os.path.join(radice, file)
                if "logo" in file.lower():
                    return percorso_completo
                if prima_immagine is None:
                    prima_immagine = percorso_completo
    return prima_immagine


def logo_in_base64():
    percorso = trova_logo()
    if percorso and os.path.exists(percorso):
        try:
            with open(percorso, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            _, ext_raw = os.path.splitext(percorso)
            ext = ext_raw.lower().replace(".", "")
            if ext == "jpg":
                ext = "jpeg"
            return f"data:image/{ext};base64,{b64}"
        except Exception:
            return None
    return None


def genera_numero_progressivo(df_all):
    anno = datetime.now().year
    suff = f"/{anno}"
    max_num = 0
    if not df_all.empty and "num" in df_all.columns:
        for num_str in df_all["num"].dropna():
            s = str(num_str).strip()
            if s.endswith(suff):
                parte = s[:-len(suff)].strip()
                if parte.isdigit():
                    max_num = max(max_num, int(parte))
            elif s.isdigit():
                max_num = max(max_num, int(s))
    return f"{max_num + 1}/{anno}"
def renderizza_anteprima_preventivo(num_doc, data_doc, cliente, indirizzo, telefono, descrizione, importo_val):
    righe_html = ""
    righe_valide = 0
    for riga in str(descrizione or "").strip().split("\n"):
        if not riga.strip():
            continue
        righe_valide += 1
        parti = tuple(p.strip() for p in riga.split("|"))
        if len(parti) >= 4:
            p0, p1, p2, p3 = parti[:4]
            righe_html += (
                f"<tr>"
                f"<td style='padding:7px;border:1px solid #d0d7de;'>{p0}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:center;'>{p1}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>{p2}</td>"
                f"<td style='padding:7px;border:1px solid #d0d7de;text-align:right;'>{p3}</td>"
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

    s_badge_tit = ParagraphStyle("BadgeTit", fontName="Helvetica-Bold", fontSize=11, alignment=1, textColor=GIALLO_LOGO)
    s_badge_sub = ParagraphStyle("BadgeSub", fontName="Helvetica-Bold", fontSize=9, alignment=1, textColor=colors.white)
    s_spett_lbl = ParagraphStyle("SpettLbl", fontName="Helvetica-Bold", fontSize=8, textColor=BLU_LOGO)
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
        ((Paragraph(f"PREVENTIVO N. {num_doc}", s_badge_tit),),
         (Paragraph(f"Data: {data_formattata}", s_badge_sub),)),
        colWidths=(165,)
    )
    badge_tab.setStyle(TableStyle((
        ("BACKGROUND", (0, 0), (-1, -1), BLU_LOGO),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    )))

    header_tab = Table(((logo_cell, badge_tab),), colWidths=(374, 165))
    header_tab.setStyle(TableStyle((
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 2, BLU_LOGO),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    )))
    story.append(header_tab)
    story.append(Spacer(1, 12))

    testo_cliente = f"<b>{cliente}</b>"
    if indirizzo:
        testo_cliente += f"<br/>{indirizzo}"
    if telefono:
        testo_cliente += f"<br/>Tel: {telefono}"

    cliente_tab = Table(
        ((Paragraph("SPETT.LE CLIENTE", s_spett_lbl),),
         (Paragraph(testo_cliente, s_spett_val),)),
        colWidths=(539,)
    )
    cliente_tab.setStyle(TableStyle((
        ("BACKGROUND", (0, 0), (-1, -1), BLU_CHIARO),
        ("LINEBEFORE", (0, 0), (0, -1), 4, GIALLO_LOGO),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    )))
    story.append(cliente_tab)
    story.append(Spacer(1, 14))

    righe_pdf = [
        (Paragraph("DESCRIZIONE LAVORAZIONI", s_th),
         Paragraph("MISURE", s_th_c),
         Paragraph("PREZZO UNIT.", s_th_r),
         Paragraph("TOTALE", s_th_r))
    ]

    for riga in descrizione.strip().split("\n"):
        if not riga.strip():
            continue
        parti = tuple(p.strip() for p in riga.split("|"))
        if len(parti) >= 4:
            p0, p1, p2, p3 = parti[:4]
            righe_pdf.append((
                Paragraph(p0, s_cell),
                Paragraph(p1, s_cell_c),
                Paragraph(p2, s_cell_r),
                Paragraph(p3, s_cell_r),
            ))
        else:
            righe_pdf.append((
                Paragraph(riga.strip(), s_cell),
                Paragraph("-", s_cell_c),
                Paragraph("-", s_cell_r),
                Paragraph("-", s_cell_r),
            ))

    righe_pdf.append(("", "", Paragraph("TOTALE (€)", s_tot), Paragraph(importo_str, s_tot)))

    voci_tab = Table(tuple(righe_pdf), colWidths=(279, 80, 90, 90), repeatRows=1)
    n_righe = len(righe_pdf)
    voci_tab.setStyle(TableStyle((
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
    )))
    story.append(voci_tab)
    story.append(Spacer(1, 14))

    cond_tab = Table(
        ((Paragraph("<b>NOTE E CONDIZIONI:</b> Gli importi indicati si intendono IVA esclusa ove applicabile. Validità offerta 30 giorni.", s_cond),),),
        colWidths=(539,)
    )
    cond_tab.setStyle(TableStyle((
        ("LINEBEFORE", (0, 0), (0, -1), 3, BLU_LOGO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    )))
    story.append(cond_tab)
    story.append(Spacer(1, 24))

    footer_tab = Table(
        ((Paragraph("<b>CARTONGESSO &amp; COLOR GROUP S.r.l.</b><br/>Opere in Cartongesso, Controsoffitti e Tinteggiature", s_f_sx),
          Paragraph("Timbro e Firma per Accettazione<br/><br/>______________________________", s_f_dx)),),
        colWidths=(270, 269)
    )
    footer_tab.setStyle(TableStyle((
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, GRIGIO_BORDO),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    )))
    story.append(footer_tab)

    doc.build(story)
    buffer_pdf.seek(0)
    return buffer_pdf.getvalue()
def inizializza_voci_salvate():
    esegui_query(
        """CREATE TABLE IF NOT EXISTS voci_preventivo (
            id SERIAL PRIMARY KEY,
            descrizione TEXT NOT NULL,
            unita_misura TEXT,
            prezzo_unitario DOUBLE PRECISION DEFAULT 0.0
        )"""
    )


def carica_voci_salvate():
    inizializza_voci_salvate()
    try:
        df = carica_tabella("voci_preventivo")
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def tabella_da_testo(testo_desc):
    righe = []
    for riga in str(testo_desc or "").strip().split("\n"):
        if not riga.strip():
            continue
        parti = tuple(p.strip() for p in riga.split("|"))
        if len(parti) >= 4:
            desc, mis, pu_raw, tot_raw = parti[:4]
        elif len(parti) == 3:
            desc, mis, pu_raw = parti
            tot_raw = "0"
        elif len(parti) == 2:
            desc, mis = parti
            pu_raw, tot_raw = "0", "0"
        else:
            desc = parti if parti else ""
            mis, pu_raw, tot_raw = "", "0", "0"

        pu_s = pu_raw.replace("€", "").replace(".", "").replace(",", ".").strip()
        tot_s = tot_raw.replace("€", "").replace(".", "").replace(",", ".").strip()
        try:
            pu_v = float(pu_s)
        except ValueError:
            pu_v = 0.0
        try:
            tot_v = float(tot_s)
        except ValueError:
            tot_v = 0.0
        righe.append({"Descrizione": desc, "Misure": mis, "Prezzo Unit. (€)": pu_v, "Totale (€)": tot_v})
    if not righe:
        righe.append({"Descrizione": "", "Misure": "", "Prezzo Unit. (€)": 0.0, "Totale (€)": 0.0})
    return pd.DataFrame(righe)


def testo_da_tabella(df_righe):
    linee = []
    totale_gen = 0.0
    if df_righe is not None and not df_righe.empty:
        for _, r in df_righe.iterrows():
            desc = str(r.get("Descrizione") or "").strip()
            mis = str(r.get("Misure") or "").strip()
            pu = float(r.get("Prezzo Unit. (€)") or 0.0)
            tot = float(r.get("Totale (€)") or 0.0)

            if tot == 0.0 and pu > 0.0 and mis:
                num_mis = "".join(c for c in mis.replace(",", ".") if c.isdigit() or c == ".")
                try:
                    if num_mis:
                        tot = round(float(num_mis) * pu, 2)
                except ValueError:
                    pass

            if not desc and pu == 0.0 and tot == 0.0:
                continue

            totale_gen += tot
            pu_fmt = f"€ {pu:,.2f}" if pu > 0 else "-"
            tot_fmt = f"€ {tot:,.2f}" if tot > 0 else "-"
            linee.append(f"{desc} | {mis or '-'} | {pu_fmt} | {tot_fmt}")

    return "\n".join(linee), round(totale_gen, 2)
def _render_tab_archivio(df_all, percorso_logo):
    if df_all.empty:
        st.info("Nessun preventivo salvato in archivio.")
        return

    df_all = df_all.dropna(subset=("id",))
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

    if df_vis.empty:
        return

    st.divider()
    st.subheader("2. Anteprima, Stampa PDF, Modifica o Elimina")

    opzioni = {
        int(r["id"]): f"Preventivo n.{r['num']} | {r['data_doc']} | {r['cliente']} (€ {float(r.get('importo') or 0):,.2f})"
        for _, r in df_vis.iterrows()
    }
    id_sel = st.selectbox("Seleziona preventivo:", options=tuple(opzioni.keys()), format_func=lambda x: opzioni[x])
    riga = df_all.set_index("id").loc[id_sel]

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

    pdf_bytes = genera_pdf_bytes(riga.to_dict(), percorso_logo)
    nome_pdf = f"Preventivo_{str(riga['num']).replace('/', '_')}_{str(riga['cliente']).replace(' ', '_')}.pdf"
    st.download_button(
        label="📥 Scarica Preventivo in PDF",
        data=pdf_bytes,
        file_name=nome_pdf,
        mime="application/pdf",
        type="primary",
    )

    st.divider()
    col_m, col_d = st.columns((1.3, 0.7))

    with col_m:
        with st.expander("✏️ Modifica questo preventivo", expanded=False):
            m1, m2 = st.columns(2)
            m_num = m1.text_input("Numero", value=str(riga["num"]), key=f"m_num_{id_sel}")
            m_data = m2.text_input("Data (AAAA-MM-GG)", value=str(riga["data_doc"]), key=f"m_data_{id_sel}")
            m_cli = st.text_input("Cliente", value=str(riga["cliente"]), key=f"m_cli_{id_sel}")
            m3, m4 = st.columns(2)
            m_ind = m3.text_input("Indirizzo", value=str(riga.get("indirizzo") or ""), key=f"m_ind_{id_sel}")
            m_tel = m4.text_input("Telefono", value=str(riga.get("telefono") or ""), key=f"m_tel_{id_sel}")

            st.caption("Modifica i righi direttamente nella tabella (clicca '+' in basso per aggiungere righe):")
            df_mod_init = tabella_da_testo(riga.get("descrizione", ""))
            df_mod_edit = st.data_editor(
                df_mod_init,
                num_rows="dynamic",
                use_container_width=True,
                key=f"ed_mod_{id_sel}",
                column_config={
                    "Descrizione": st.column_config.TextColumn("Descrizione Lavorazioni", width="large"),
                    "Misure": st.column_config.TextColumn("Misure (es. 45 mq)", width="small"),
                    "Prezzo Unit. (€)": st.column_config.NumberColumn("Prezzo Unit. (€)", min_value=0.0, step=1.0, format="%.2f"),
                    "Totale (€)": st.column_config.NumberColumn("Totale (€)", min_value=0.0, step=1.0, format="%.2f"),
                },
            )

            m_desc_str, m_tot_calc = testo_da_tabella(df_mod_edit)
            m_imp = st.number_input(
                "Totale Preventivo (€)",
                value=float(m_tot_calc if m_tot_calc > 0 else (riga.get("importo") or 0.0)),
                step=50.0,
                key=f"m_imp_{id_sel}",
            )

            if st.button("💾 Salva Modifiche", type="primary", key=f"btn_save_mod_{id_sel}"):
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
                        "descrizione": m_desc_str,
                        "importo": m_imp,
                        "id": id_sel,
                    },
                )
                st.success("✅ Preventivo aggiornato!")
                st.rerun()

    with col_d:
        with st.expander("🗑️ Elimina questo preventivo", expanded=False):
            st.warning(f"Vuoi eliminare il preventivo **n.{riga['num']}** per **{riga['cliente']}**?")
            if st.button("🚨 Conferma Eliminazione", type="primary", key=f"btn_del_{id_sel}"):
                esegui_query("DELETE FROM preventivi WHERE id = :id", {"id": id_sel})
                st.success("🗑️ Preventivo eliminato!")
                st.rerun()
def _render_tab_nuovo(df_all, df_voci, percorso_logo):
    st.subheader("➕ Crea Nuovo Preventivo (con Anteprima Live)")
    num_suggerito = genera_numero_progressivo(df_all)

    if "righe_nuovo_prev" not in st.session_state:
        st.session_state["righe_nuovo_prev"] = pd.DataFrame((
            {"Descrizione": "", "Misure": "", "Prezzo Unit. (€)": 0.0, "Totale (€)": 0.0},
        ))

    col_form, col_live = st.columns((1.15, 1.1))

    with col_form:
        c1, c2 = st.columns(2)
        n_num = c1.text_input("Numero Preventivo", value=num_suggerito)
        n_data = c2.date_input("Data", value=date.today())
        n_cli = st.text_input("Cliente / Azienda", placeholder="Es. Mario Rossi")
        c3, c4 = st.columns(2)
        n_ind = c3.text_input("Indirizzo / Cantiere", placeholder="Es. Via Roma 10, Riposto")
        n_tel = c4.text_input("Telefono", placeholder="Es. 333 1234567")

        if not df_voci.empty:
            st.markdown("**📚 Inserisci una descrizione salvata**")
            v_col1, v_col2, v_col3 = st.columns((2.2, 0.8, 1.0))
            opz_voci = {
                int(v["id"]): f"{v['descrizione']} (€ {float(v.get('prezzo_unitario') or 0):,.2f}/{v.get('unita_misura') or 'cad'})"
                for _, v in df_voci.iterrows()
            }
            voce_scelta = v_col1.selectbox("Scegli lavorazione:", options=tuple(opz_voci.keys()), format_func=lambda x: opz_voci[x], label_visibility="collapsed")
            qta_scelta = v_col2.text_input("Misure", placeholder="Es. 45 mq", label_visibility="collapsed")
            if v_col3.button("➕ Inserisci Rigo", use_container_width=True):
                riga_v = df_voci.set_index("id").loc[voce_scelta]
                pu_v = float(riga_v.get("prezzo_unitario") or 0.0)
                mis_txt = qta_scelta.strip() or str(riga_v.get("unita_misura") or "")
                nuova_riga = pd.DataFrame(({
                    "Descrizione": str(riga_v["descrizione"]),
                    "Misure": mis_txt,
                    "Prezzo Unit. (€)": pu_v,
                    "Totale (€)": 0.0,
                },))
                df_corr = st.session_state["righe_nuovo_prev"]
                df_corr = df_corr[df_corr["Descrizione"].astype(str).str.strip() != ""]
                st.session_state["righe_nuovo_prev"] = pd.concat((df_corr, nuova_riga), ignore_index=True)
                st.rerun()

        st.markdown("**Righi Lavorazioni** *(scrivi nelle celle o aggiungi righe in basso)*")
        df_nuovo_edit = st.data_editor(
            st.session_state["righe_nuovo_prev"],
            num_rows="dynamic",
            use_container_width=True,
            key="ed_nuovo_prev",
            column_config={
                "Descrizione": st.column_config.TextColumn("Descrizione Lavorazioni", width="large"),
                "Misure": st.column_config.TextColumn("Misure (es. 45 mq)", width="small"),
                "Prezzo Unit. (€)": st.column_config.NumberColumn("Prezzo Unit. (€)", min_value=0.0, step=1.0, format="%.2f"),
                "Totale (€)": st.column_config.NumberColumn("Totale (€)", min_value=0.0, step=1.0, format="%.2f"),
            },
        )

        n_desc_str, tot_calcolato = testo_da_tabella(df_nuovo_edit)
        n_imp = st.number_input(
            "Totale Preventivo (€) — calcolato dai righi o modificabile",
            min_value=0.0,
            value=float(tot_calcolato),
            step=50.0,
        )

        b1, b2, b3 = st.columns((1.1, 1.1, 0.8))
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
                            "descrizione": n_desc_str,
                            "importo": n_imp,
                        },
                    )
                    st.session_state["righe_nuovo_prev"] = pd.DataFrame((
                        {"Descrizione": "", "Misure": "", "Prezzo Unit. (€)": 0.0, "Totale (€)": 0.0},
                    ))
                    st.success("✅ Preventivo salvato con successo!")
                    st.rerun()

        with b2:
            dati_bozza = {
                "num": n_num,
                "data_doc": str(n_data),
                "cliente": n_cli or "Cliente",
                "indirizzo": n_ind,
                "telefono": n_tel,
                "descrizione": n_desc_str,
                "importo": n_imp,
            }
            pdf_bozza = genera_pdf_bytes(dati_bozza, percorso_logo)
            st.download_button(
                label="📥 Scarica PDF",
                data=pdf_bozza,
                file_name=f"Preventivo_{n_num.replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with b3:
            if st.button("🧹 Svuota", use_container_width=True):
                st.session_state["righe_nuovo_prev"] = pd.DataFrame((
                    {"Descrizione": "", "Misure": "", "Prezzo Unit. (€)": 0.0, "Totale (€)": 0.0},
                ))
                st.rerun()

    with col_live:
        st.markdown("#### 👁️ Anteprima in Tempo Reale")
        renderizza_anteprima_preventivo(
            num_doc=n_num,
            data_doc=n_data.strftime("%d/%m/%Y"),
            cliente=n_cli,
            indirizzo=n_ind,
            telefono=n_tel,
            descrizione=n_desc_str,
            importo_val=n_imp,
        )
def _render_tab_voci(df_voci):
    st.subheader("📚 Gestione Descrizioni Salvate (Listino Rapido)")
    st.caption("Salva qui le lavorazioni che usi più spesso per richiamarle con un clic quando crei un preventivo.")

    with st.form("form_nuova_voce"):
        v1, v2, v3 = st.columns((2.5, 0.8, 0.9))
        nuova_desc = v1.text_input("Descrizione Lavorazione", placeholder="Es. Fornitura e posa parete in cartongesso doppia lastra")
        nuova_um = v2.text_input("Unità di misura", placeholder="Es. mq / ml / corpo")
        nuovo_pu = v3.number_input("Prezzo Unit. (€)", min_value=0.0, step=1.0)

        if st.form_submit_button("💾 Memorizza Descrizione", type="primary"):
            if not nuova_desc.strip():
                st.error("⚠️ Inserisci il testo della descrizione.")
            else:
                esegui_query(
                    """INSERT INTO voci_preventivo (descrizione, unita_misura, prezzo_unitario)
                       VALUES (:desc, :um, :pu)""",
                    {"desc": nuova_desc.strip(), "um": nuova_um.strip(), "pu": nuovo_pu},
                )
                st.success("✅ Descrizione memorizzata!")
                st.rerun()

    st.divider()
    if not df_voci.empty:
        st.markdown("### Elenco Descrizioni Memorizzate")
        st.dataframe(df_voci, use_container_width=True, hide_index=True)

        opz_del_v = {
            int(v["id"]): f"ID {int(v['id'])} - {v['descrizione']} (€ {float(v.get('prezzo_unitario') or 0):,.2f})"
            for _, v in df_voci.iterrows()
        }
        c_del1, c_del2 = st.columns((2.5, 1))
        id_v_del = c_del1.selectbox("Seleziona una descrizione da eliminare:", options=tuple(opz_del_v.keys()), format_func=lambda x: opz_del_v[x])
        if c_del2.button("🗑️ Elimina Descrizione", use_container_width=True):
            esegui_query("DELETE FROM voci_preventivo WHERE id = :id", {"id": id_v_del})
            st.success("🗑️ Descrizione eliminata!")
            st.rerun()
    else:
        st.info("Non hai ancora memorizzato nessuna descrizione. Usa il modulo qui sopra per aggiungere la prima!")


def mostra_preventivi():
    st.title("📋 Gestione Preventivi")
    tab1, tab2, tab3 = st.tabs(("📂 Archivio, Anteprima & PDF", "➕ Nuovo Preventivo", "📚 Descrizioni Salvate"))

    df_all = carica_tabella("preventivi")
    df_voci = carica_voci_salvate()
    percorso_logo = trova_logo()

    with tab1:
        _render_tab_archivio(df_all, percorso_logo)

    with tab2:
        _render_tab_nuovo(df_all, df_voci, percorso_logo)

    with tab3:
        _render_tab_voci(df_voci)


