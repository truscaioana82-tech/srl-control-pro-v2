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
    
    with tab1:
        if not df_all.empty:
            df_all = df_all.dropna(subset=["id"])
            df_all["id"] = df_all["id"].astype(int)
            df_all = df_all.sort_values(by="id", ascending=False)
            df_all["pagata"] = df_all["pagata"].fillna(1).astype(bool)
            
            st.subheader("1. Elenco Movimenti")
            
            col_cerca, col_socio = st.columns()
            
            cerca = col_cerca.text_input(
                "🔍 Cerca per numero fattura o nome cliente/fornitore", 
                placeholder="Es. 16/26 oppure ECOIN..."
            )
            
            socio_filtro = col_socio.selectbox(
                "👤 Filtra per Socio",
                options=["Tutti", "BAGLI", "TROPEA", "COMUNE"]
            )
            
            df_filtrato = df_all.copy()
            
            if socio_filtro != "Tutti":
                df_filtrato = df_filtrato[df_filtrato["socio"].astype(str).str.upper() == socio_filtro]
            
            if cerca:
                filtro_num = df_filtrato["num"].astype(str).str.contains(cerca, case=False, na=False)
                filtro_nome = df_filtrato["anagrafica"].astype(str).str.contains(cerca, case=False, na=False)
                df_filtrato = df_filtrato[filtro_num | filtro_nome]
            
            st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
            
            if not df_filtrato.empty:
                tot_imp = df_filtrato["imponibile"].sum()
                tot_iva = (df_filtrato["imponibile"] * (df_filtrato["iva_perc"] / 100)).sum()
                tot_lordo = tot_imp + tot_iva
                
                t1, t2, t3, t4 = st.columns(4)
                t1.metric("📄 Fatture trovate", f"{len(df_filtrato)}")
                t2.metric("💶 Totale Imponibile", f"€ {tot_imp:,.2f}")
                t3.metric("🧾 Totale IVA", f"€ {tot_iva:,.2f}")
                t4.metric("💰 Totale Lordo", f"€ {tot_lordo:,.2f}")
            
            st.divider()
            st.subheader("2. Seleziona una fattura da Modificare o Cancellare")
            
            if not df_filtrato.empty:
                opzioni = {
                    int(row["id"]): f"ID {int(row['id'])} | {row['data']} | {row['tipo']} n.{row['num']} - {row['anagrafica']} (€ {row['imponibile']})"
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
                            tipi = ("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA", "NOTA DI CREDITO")
                            idx_t = tipi.index(riga["tipo"]) if riga["tipo"] in tipi else 0
                            nuovo_tipo = m2.selectbox("Tipo", options=tipi, index=idx_t)
                            
                            m3, m4 = st.columns(2)
                            nuovo_num = m3.text_input("Numero", value=str(riga["num"]))
                            nuova_anag = m4.text_input("Cliente / Fornitore", value=str(riga["anagrafica"]))
                            
                            m5, m6, m7 = st.columns(3)
                            nuovo_imp = m5.number_input("Imponibile (€)", value=float(riga["imponibile"]), step=10.0)
                            nuova_iva = m6.number_input("IVA %", value=float(riga["iva_perc"]), step=1.0)
                            soci = ("BAGLI", "TROPEA", "COMUNE")
                            idx_s = soci.index(riga["socio"]) if riga["socio"] in soci else 0
                            nuovo_socio = m7.selectbox("Socio", options=soci, index=idx_s)
                            
                            cat_attuale = str(riga["costo_categoria"]) if riga["costo_categoria"] in CATEGORIE_COSTI else "Generale"
                            nuova_cat = st.selectbox("Categoria", options=CATEGORIE_COSTI, index=CATEGORIE_COSTI.index(cat_attuale))
                            nuova_pagata = st.checkbox("Pagata?", value=bool(riga["pagata"]))
                            
                            if st.form_submit_button("💾 Salva Modifiche", type="primary"):
                                esegui_query(
                                    '''UPDATE fatture 
                                       SET data=:d, tipo=:t, num=:n, anagrafica=:a, imponibile=:i, iva_perc=:iv, socio=:s, costo_categoria=:c, pagata=:p 
                                       WHERE id=:id''',
                                    {"d": nuova_data, "t": nuovo_tipo, "n": nuovo_num, "a": nuova_anag.upper(),
                                     "i": nuovo_imp, "iv": nuova_iva, "s": nuovo_socio, "c": nuova_cat, "p": int(nuova_pagata), "id": int(id_scelto)}
                                )
                                st.success(f"✅ Fattura ID {id_scelto} aggiornata!")
                                st.rerun()

                with col_del:
                    with st.expander("🗑️ CANCELLA QUESTA FATTURA", expanded=True):
                        st.warning(f"Stai per eliminare la fattura **ID {id_scelto}** ({riga['anagrafica']}).")
                        if st.button("🗑️ Cancella Definitivamente"):
                            esegui_query("DELETE FROM fatture WHERE id=:id", {"id": int(id_scelto)})
                            st.success(f"🗑️ Fattura ID {id_scelto} eliminata!")
                            st.rerun()
            else:
                st.info("Nessuna fattura trovata con i criteri di ricerca inseriti.")
        else:
            st.warning("Nessun movimento registrato.")
    with tab2:
        st.info("💡 **Caricamento rapido:** Trascina qui una Fattura Elettronica (.xml) scaricata da Aruba per compilare i campi in automatico.")
        file_xml = st.file_uploader("📂 Carica file fattura (.xml)", type=["xml"])
        dati_xml = leggi_xml_fattura(file_xml) if file_xml else None
        if dati_xml:
            st.success(f"✅ Dati estratti dal file XML: **{dati_xml['anagrafica']}** (Doc. n. {dati_xml['num']} - € {dati_xml['imponibile']:,.2f})")

        nomi_rubrica = ottieni_nomi_rubrica(["CLIENTE", "FORNITORE"])
        with st.form("nuova_fattura"):
            c1, c2, c3 = st.columns(3)
            data_default = dati_xml["data"] if dati_xml else date.today()
            data_doc = c1.date_input("Data", value=data_default)
            
            tipi_opz = ("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA", "NOTA DI CREDITO")
            idx_tipo = tipi_opz.index(dati_xml["tipo"]) if (dati_xml and dati_xml["tipo"] in tipi_opz) else 0
            tipo_doc = c2.selectbox("Tipo Documento", options=tipi_opz, index=idx_tipo)
            
            num_default = dati_xml["num"] if dati_xml else ""
            num_doc = c3.text_input("Numero Documento (es. 71/2026 o Polizza)", value=num_default)
            
            c4, c5 = st.columns(2)
            anag_scelta = c4.selectbox("Scegli da Rubrica (oppure scrivi a destra)", options=["-- Scrivi nuovo nome --"] + nomi_rubrica)
            anag_default = dati_xml["anagrafica"] if dati_xml else ""
            anag_nuova = c5.text_input("Nuovo Cliente / Fornitore / Compagnia Assic.", value=anag_default)
            
            c6, c7, c8 = st.columns(3)
            imp_default = dati_xml["imponibile"] if dati_xml else 0.0
            imponibile = c6.number_input("Imponibile (€)", min_value=0.0, value=imp_default, step=10.0)
            
            iva_opz = (22, 10, 5, 4, 0)
            idx_iva = iva_opz.index(dati_xml["iva"]) if (dati_xml and dati_xml["iva"] in iva_opz) else 0
            iva_perc = c7.selectbox("IVA % (0% per Assicurazioni)", options=iva_opz, index=idx_iva)
            
            socio = c8.selectbox("Socio", options=("BAGLI", "TROPEA", "COMUNE"))
            
            c9, c10 = st.columns(2)
            ritenuta = c9.number_input("Ritenuta %", min_value=0.0, max_value=100.0, value=0.0)
            categoria = c10.selectbox("Categoria Costo/Ricavo", options=CATEGORIE_COSTI)
            
            col_chk1, col_chk2, col_chk3 = st.columns(3)
            gia_pagata = col_chk1.checkbox("Già pagata / incassata?", value=True)
            salva_in_rubrica = col_chk2.checkbox("Salva nuovo nome in Rubrica", value=True)
            ignora_doppione = col_chk3.checkbox("Forza salvataggio se doppione", value=False)
            
            if st.form_submit_button("➕ Registra Movimento", type="primary"):
                anag_finale = anag_nuova.strip().upper() if anag_nuova.strip() else (anag_scelta if anag_scelta != "-- Scrivi nuovo nome --" else "")
                num_pulito = num_doc.strip()
                anno_doc = str(data_doc)[:4]
                
                is_doppione = False
                if not df_all.empty and num_pulito and anag_finale:
                    stesso_num = df_all["num"].astype(str).str.strip().str.upper() == num_pulito.upper()
                    stessa_anag = df_all["anagrafica"].astype(str).str.strip().str.upper() == anag_finale
                    stesso_anno = df_all["data"].astype(str).str.startswith(anno_doc)
                    if (stesso_num & stessa_anag & stesso_anno).any():
                        is_doppione = True
                
                if is_doppione and not ignora_doppione:
                    st.warning(f"⚠️ **Attenzione:** Risulta già registrato il documento **n. {num_pulito}** di **{anag_finale}** nel **{anno_doc}**! Se sei sicuro di volerlo inserire comunque, spunta *'Forza salvataggio se doppione'* e clicca di nuovo.")
                else:
                    esegui_query(
                        '''INSERT INTO fatture (data, tipo, num, anagrafica, imponibile, iva_perc, socio, ritenuta_perc, costo_categoria, pagata) 
                           VALUES (:d, :t, :n, :a, :i, :iv, :s, :r, :c, :p)''',
                        {"d": str(data_doc), "t": tipo_doc, "n": num_pulito, "a": anag_finale,
                         "i": imponibile, "iv": iva_perc, "s": socio, "r": ritenuta, "c": categoria, "p": int(gia_pagata)}
                    )
                    
                    if salva_in_rubrica and anag_nuova.strip() and anag_finale not in [n.upper() for n in nomi_rubrica]:
                        tipo_rub = "CLIENTE" if "EMESSA" in tipo_doc else "FORNITORE"
                        try:
                            esegui_query(
                                "INSERT INTO rubrica (nome, tipo) VALUES (:n, :t)",
                                {"n": anag_finale, "t": tipo_rub}
                            )
                        except Exception:
                            pass
                            
                    st.success("✅ Registrazione inserita su Cloud!")
                    st.rerun()




