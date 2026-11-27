import streamlit as st
from datetime import date
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

def mostra_prima_nota():
    st.title("📝 Prima Nota & Registro Fatture")
    tab1, tab2 = st.tabs(["✏️ Storico, Modifica & Cancella", "➕ Nuova Registrazione"])
    
    with tab1:
        df_all = carica_tabella("fatture")
        if not df_all.empty:
            df_all = df_all.dropna(subset=["id"])
            df_all["id"] = df_all["id"].astype(int)
            df_all = df_all.sort_values(by="id", ascending=False)
            df_all["pagata"] = df_all["pagata"].fillna(1).astype(bool)
            
            st.subheader("1. Elenco Movimenti")
            
            # --- INIZIO BARRA DI RICERCA E FILTRO SOCIO ---
            col_cerca, col_socio = st.columns([3, 1])
            
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
            # --- FINE BARRA DI RICERCA E FILTRO SOCIO ---
            
            st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
            
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
        nomi_rubrica = ottieni_nomi_rubrica(["CLIENTE", "FORNITORE"])
        with st.form("nuova_fattura"):
            c1, c2, c3 = st.columns(3)
            data_doc = c1.date_input("Data", value=date.today())
            tipo_doc = c2.selectbox("Tipo Documento", options=("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA", "NOTA DI CREDITO"))
            num_doc = c3.text_input("Numero Documento (es. 71/2026 o Polizza)")
            
            c4, c5 = st.columns(2)
            anag_scelta = c4.selectbox("Scegli da Rubrica (oppure scrivi a destra)", options=["-- Scrivi nuovo nome --"] + nomi_rubrica)
            anag_nuova = c5.text_input("Nuovo Cliente / Fornitore / Compagnia Assic.")
            
            c6, c7, c8 = st.columns(3)
            imponibile = c6.number_input("Imponibile (€)", min_value=0.0, step=10.0)
            iva_perc = c7.selectbox("IVA % (0% per Assicurazioni)", options=(22, 10, 5, 4, 0))
            socio = c8.selectbox("Socio", options=("BAGLI", "TROPEA", "COMUNE"))
            
            c9, c10 = st.columns(2)
            ritenuta = c9.number_input("Ritenuta %", min_value=0.0, max_value=100.0, value=0.0)
            categoria = c10.selectbox("Categoria Costo/Ricavo", options=CATEGORIE_COSTI)
            
            if st.form_submit_button("➕ Registra Movimento", type="primary"):
                anag_finale = anag_nuova.strip().upper() if anag_nuova.strip() else (anag_scelta if anag_scelta != "-- Scrivi nuovo nome --" else "")
                esegui_query(
                    '''INSERT INTO fatture (data, tipo, num, anagrafica, imponibile, iva_perc, socio, ritenuta_perc, costo_categoria, pagata) 
                       VALUES (:d, :t, :n, :a, :i, :iv, :s, :r, :c, 1)''',
                    {"d": str(data_doc), "t": tipo_doc, "n": num_doc, "a": anag_finale,
                     "i": imponibile, "iv": iva_perc, "s": socio, "r": ritenuta, "c": categoria}
                )
                st.success("✅ Registrazione inserita su Cloud!")
                st.rerun()



