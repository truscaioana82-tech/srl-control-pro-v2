import streamlit as st
import xml.etree.ElementTree as ET
from datetime import date, datetime
from database import esegui_query, carica_tabella
from rubrica import ottieni_nomi_rubrica

CATEGORIE_COSTI = (
    "Generale",
    "Assicurazioni Mezzi",
    "Indumenti / DPI",
    "Carburante & Manutenzione",
    "Materiali Edili",
    "Noleggi & Attrezzature",
    "Utenze & Ufficio",
    "Consulenze & Commercialista"
)

def leggi_xml_fattura(file_caricato):
    """Estrae i dati principali da un file XML di Fattura Elettronica italiana."""
    try:
        contenuto = file_caricato.read()
        tree = ET.ElementTree(ET.fromstring(contenuto))
        root = tree.getroot()
        
        def trova_testo(percorso):
            for elem in root.iter():
                if elem.tag.endswith(percorso):
                    return elem.text
            return None

        data_str = trova_testo("Data")
        numero = trova_testo("Numero") or ""
        tipo_doc_cod = trova_testo("TipoDocumento") or ""
        
        imponibile_str = trova_testo("ImponibileImporto") or "0.0"
        aliquota_str = trova_testo("AliquotaIVA") or "22"
        
        cedente = ""
        cessionario = ""
        for elem in root.iter():
            if elem.tag.endswith("CedentePrestatore"):
                for sub in elem.iter():
                    if sub.tag.endswith("Denominazione") and sub.text:
                        cedente = sub.text.strip().upper()
                        break
                    elif sub.tag.endswith("Cognome") and sub.text:
                        nome = next((s.text for s in elem.iter() if s.tag.endswith("Nome") and s.text), "")
                        cedente = f"{sub.text} {nome}".strip().upper()
                        break
            elif elem.tag.endswith("CessionarioCommittente"):
                for sub in elem.iter():
                    if sub.tag.endswith("Denominazione") and sub.text:
                        cessionario = sub.text.strip().upper()
                        break
                    elif sub.tag.endswith("Cognome") and sub.text:
                        nome = next((s.text for s in elem.iter() if s.tag.endswith("Nome") and s.text), "")
                        cessionario = f"{sub.text} {nome}".strip().upper()
                        break

        if "BAGLI" in cedente or "TROPEA" in cedente:
            tipo_finale = "NOTA DI CREDITO" if tipo_doc_cod == "TD04" else "FATTURA EMESSA"
            anagrafica = cessionario
        else:
            tipo_finale = "NOTA DI CREDITO" if tipo_doc_cod == "TD04" else "FATTURA ACQUISTO"
            anagrafica = cedente

        data_obj = datetime.strptime(data_str[:10], "%Y-%m-%d").date() if data_str else date.today()
        
        return {
            "data": data_obj,
            "tipo": tipo_finale,
            "num": numero,
            "anagrafica": anagrafica,
            "imponibile": float(imponibile_str),
            "iva": int(float(aliquota_str))
        }
    except Exception as e:
        st.error(f"Errore nella lettura del file XML: {e}")
        return None
def mostra_prima_nota():
    st.title("📝 Prima Nota & Registro Fatture")
    tab1, tab2 = st.tabs(["✏️ Storico, Modifica & Cancella", "➕ Nuova Registrazione"])
    
    df_all = carica_tabella("fatture")
    
    # Recupera elenco cantieri già usati
    cantieri_set = set(["GENERALE"])
    if not df_all.empty and "cantiere" in df_all.columns:
        cantieri_set.update(df_all["cantiere"].dropna().astype(str).str.upper().tolist())
    df_st_check = carica_tabella("stipendi")
    if not df_st_check.empty and "cantiere" in df_st_check.columns:
        cantieri_set.update(df_st_check["cantiere"].dropna().astype(str).str.upper().tolist())
    lista_cantieri = sorted([c for c in cantieri_set if c.strip()])

    with tab1:
        if not df_all.empty:
            df_all = df_all.dropna(subset=["id"])
            df_all["id"] = df_all["id"].astype(int)
            df_all = df_all.sort_values(by="id", ascending=False)
            if "pagata" in df_all.columns:
                df_all["pagata"] = df_all["pagata"].fillna(1).astype(bool)
            if "cantiere" not in df_all.columns:
                df_all["cantiere"] = "GENERALE"
            df_all["cantiere"] = df_all["cantiere"].fillna("GENERALE").replace("", "GENERALE").astype(str).str.upper()
            
            st.subheader("1. Elenco Movimenti")
            
            col_cerca, col_tipo, col_socio, col_cant = st.columns([2, 1.2, 1, 1.2])
            
            cerca = col_cerca.text_input(
                "🔍 Cerca per numero o cliente/fornitore", 
                placeholder="Es. 16/26 oppure ECOIN..."
            )
            
            tipo_filtro = col_tipo.selectbox(
                "📑 Filtra Tipo",
                options=["Tutti", "Solo Emesse (Ricavi)", "Solo Acquisti / Ricevute", "Note di Credito"]
            )
            
            socio_filtro = col_socio.selectbox(
                "👤 Filtra Socio",
                options=["Tutti", "BAGLI", "TROPEA", "COMUNE"]
            )

            cant_filtro = col_cant.selectbox(
                "🏗️ Filtra Cantiere",
                options=["Tutti"] + lista_cantieri
            )
            
            df_filtrato = df_all.copy()
            
            # Filtro per tipo documento (gestisce sia vecchi che nuovi nomi)
            tipo_upper = df_filtrato["tipo"].astype(str).str.upper()
            if tipo_filtro == "Solo Emesse (Ricavi)":
                df_filtrato = df_filtrato[tipo_upper.isin(["EMESSA", "FATTURA EMESSA"])]
            elif tipo_filtro == "Solo Acquisti / Ricevute":
                df_filtrato = df_filtrato[tipo_upper.isin(["RICEVUTA", "FATTURA ACQUISTO"])]
            elif tipo_filtro == "Note di Credito":
                df_filtrato = df_filtrato[tipo_upper == "NOTA DI CREDITO"]

            if socio_filtro != "Tutti":
                df_filtrato = df_filtrato[df_filtrato["socio"].astype(str).str.upper() == socio_filtro]

            if cant_filtro != "Tutti":
                df_filtrato = df_filtrato[df_filtrato["cantiere"] == cant_filtro]
            
            if cerca:
                filtro_num = df_filtrato["num"].astype(str).str.contains(cerca, case=False, na=False)
                filtro_nome = df_filtrato["anagrafica"].astype(str).str.contains(cerca, case=False, na=False)
                df_filtrato = df_filtrato[filtro_num | filtro_nome]
            
            st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
            
            if not df_filtrato.empty:
                t_up = df_filtrato["tipo"].astype(str).str.upper()
                mask_emesse = t_up.isin(["EMESSA", "FATTURA EMESSA"])
                mask_acquisti = t_up.isin(["RICEVUTA", "FATTURA ACQUISTO"])
                mask_nc = t_up == "NOTA DI CREDITO"

                imp_emesse = df_filtrato.loc[mask_emesse, "imponibile"].sum()
                imp_acquisti = df_filtrato.loc[mask_acquisti, "imponibile"].sum()
                imp_nc = df_filtrato.loc[mask_nc, "imponibile"].sum()

                iva_emesse = (df_filtrato.loc[mask_emesse, "imponibile"] * (df_filtrato.loc[mask_emesse, "iva_perc"] / 100)).sum()
                iva_acquisti = (df_filtrato.loc[mask_acquisti, "imponibile"] * (df_filtrato.loc[mask_acquisti, "iva_perc"] / 100)).sum()

                t1, t2, t3, t4 = st.columns(4)
                t1.metric("📄 Fatture trovate", f"{len(df_filtrato)}")
                t2.metric("📈 Imponibile Emesse", f"€ {imp_emesse:,.2f}", delta=f"IVA: € {iva_emesse:,.2f}", delta_color="off")
                t3.metric("📉 Imponibile Acquisti", f"€ {imp_acquisti:,.2f}", delta=f"IVA: € {iva_acquisti:,.2f}", delta_color="off")
                t4.metric("⚖️ Saldo Imponibile", f"€ {(imp_emesse - imp_acquisti - imp_nc):,.2f}")
            st.divider()
            st.subheader("2. Seleziona una fattura da Modificare o Cancellare")
            
            if not df_filtrato.empty:
                opzioni = {
                    int(row["id"]): f"ID {int(row['id'])} | {row['data']} | {row['tipo']} n.{row['num']} - {row['anagrafica']} [{row['cantiere']}] (€ {row['imponibile']})"
                    for _, row in df_filtrato.iterrows()
                }
                id_scelto = st.selectbox("Scegli la fattura:", options=list(opzioni.keys()), format_func=lambda x: opzioni[x])
                riga = df_all.set_index("id").loc[id_scelto]
                
                col_mod, col_del = st.columns(2)
                
                with col_mod:
                    with st.expander("✏️ MODIFICA QUESTA FATTURA", expanded=True):
                        with st.form("form_modifica"):
                            m1, m2 = st.columns(2)
                            nuova_data = m1.text_input("Data (AAAA-MM-GG)", value=str(riga["data"]))
                            tipi = ("FATTURA EMESSA", "FATTURA ACQUISTO", "EMESSA", "RICEVUTA", "NOTA DI CREDITO")
                            idx_t = tipi.index(riga["tipo"]) if riga["tipo"] in tipi else 0
                            nuovo_tipo = m2.selectbox("Tipo", options=tipi, index=idx_t)
                            
                            m3, m4 = st.columns(2)
                            nuovo_num = m3.text_input("Numero", value=str(riga["num"]))
                            nuova_anag = m4.text_input("Cliente / Fornitore", value=str(riga["anagrafica"]))
                            
                            m5, m6, m7 = st.columns(3)
                            nuovo_imp = m5.number_input("Imponibile (€)", value=float(riga["imponibile"]), step=10.0)
                            nuova_iva = m6.number_input("IVA %", value=float(riga["iva_perc"]), step=1.0)
                            nuova_rit = m7.number_input("Ritenuta %", value=float(riga.get("ritenuta_perc", 0.0)), step=1.0)
                            
                            m8, m9, m10 = st.columns(3)
                            soci = ("BAGLI", "TROPEA", "COMUNE")
                            idx_s = soci.index(str(riga["socio"]).upper()) if str(riga["socio"]).upper() in soci else 0
                            nuovo_socio = m8.selectbox("Socio", options=soci, index=idx_s)
                            
                            cat_attuale = str(riga.get("costo_categoria", "Generale"))
                            idx_c = CATEGORIE_COSTI.index(cat_attuale) if cat_attuale in CATEGORIE_COSTI else 0
                            nuova_cat = m9.selectbox("Categoria", options=CATEGORIE_COSTI, index=idx_c)
                            nuovo_cant = m10.text_input("Cantiere", value=str(riga["cantiere"]))
                            
                            nuova_pagata = st.checkbox("Fattura Pagata / Incassata", value=bool(riga.get("pagata", True)))
                            
                            if st.form_submit_button("💾 Salva Modifiche", type="primary"):
                                esegui_query(
                                    """UPDATE fatture SET data=?, tipo=?, num=?, anagrafica=?, imponibile=?, 
                                       iva_perc=?, ritenuta_perc=?, socio=?, costo_categoria=?, cantiere=?, pagata=? 
                                       WHERE id=?""",
                                    (
                                        nuova_data.strip(),
                                        nuovo_tipo,
                                        nuovo_num.strip(),
                                        nuova_anag.strip().upper(),
                                        nuovo_imp,
                                        nuova_iva,
                                        nuova_rit,
                                        nuovo_socio,
                                        nuova_cat,
                                        nuovo_cant.strip().upper() or "GENERALE",
                                        1 if nuova_pagata else 0,
                                        id_scelto
                                    )
                                )
                                st.success("✅ Fattura aggiornata con successo!")
                                st.rerun()
                
                with col_del:
                    with st.expander("🗑️ ELIMINA QUESTA FATTURA", expanded=False):
                        st.warning(f"Stai per eliminare definitivamente la fattura **n.{riga['num']}** di **{riga['anagrafica']}**.")
                        if st.button("🚨 Conferma Eliminazione", type="primary"):
                            esegui_query("DELETE FROM fatture WHERE id=?", (id_scelto,))
                            st.success("🗑️ Fattura eliminata!")
                            st.rerun()
        else:
            st.info("Nessuna fattura registrata nel database.")
    with tab2:
        st.subheader("➕ Registra una Nuova Fattura")
        
        file_xml = st.file_uploader("📂 Carica file XML Fattura Elettronica (opzionale)", type=["xml"])
        dati_xml = leggi_xml_fattura(file_xml) if file_xml else {}
        if dati_xml:
            st.success(f"Dati estratti da XML: {dati_xml['tipo']} n.{dati_xml['num']} - {dati_xml['anagrafica']}")

        nomi_rubrica = ottieni_nomi_rubrica() if callable(ottieni_nomi_rubrica) else []

        with st.form("form_nuova_fattura"):
            c1, c2 = st.columns(2)
            ins_data = c1.date_input("Data Documento", value=dati_xml.get("data", date.today()))
            tipi_ins = ("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA", "NOTA DI CREDITO")
            idx_ins_t = tipi_ins.index(dati_xml["tipo"]) if dati_xml.get("tipo") in tipi_ins else 0
            ins_tipo = c2.selectbox("Tipo Documento", options=tipi_ins, index=idx_ins_t)

            c3, c4 = st.columns(2)
            ins_num = c3.text_input("Numero Documento", value=dati_xml.get("num", ""))
            ins_anag = c4.text_input("Cliente / Fornitore", value=dati_xml.get("anagrafica", ""), placeholder="Ragione sociale...")

            c5, c6, c7 = st.columns(3)
            ins_imp = c5.number_input("Imponibile (€)", value=float(dati_xml.get("imponibile", 0.0)), step=10.0)
            ins_iva = c6.number_input("Aliquota IVA %", value=float(dati_xml.get("iva", 22)), step=1.0)
            ins_rit = c7.number_input("Ritenuta d'acconto %", value=0.0, step=1.0)

            c8, c9, c10 = st.columns(3)
            ins_socio = c8.selectbox("Socio di riferimento", options=("BAGLI", "TROPEA", "COMUNE"))
            ins_cat = c9.selectbox("Categoria Costo/Ricavo", options=CATEGORIE_COSTI)
            ins_cant = c10.text_input("Cantiere", value="GENERALE")

            ins_pagata = st.checkbox("Già Pagata / Incassata", value=True)

            if st.form_submit_button("💾 Registra Fattura", type="primary"):
                if not ins_num.strip() or not ins_anag.strip():
                    st.error("⚠️ Inserisci almeno il numero e il cliente/fornitore.")
                else:
                    esegui_query(
                        """INSERT INTO fatture (data, tipo, num, anagrafica, imponibile, iva_perc, ritenuta_perc, socio, costo_categoria, cantiere, pagata)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(ins_data),
                            ins_tipo,
                            ins_num.strip(),
                            ins_anag.strip().upper(),
                            ins_imp,
                            ins_iva,
                            ins_rit,
                            ins_socio,
                            ins_cat,
                            ins_cant.strip().upper() or "GENERALE",
                            1 if ins_pagata else 0
                        )
                    )
                    st.success("✅ Nuova fattura salvata nel database!")
                    st.rerun()


