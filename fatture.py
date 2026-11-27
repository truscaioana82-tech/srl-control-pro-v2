import streamlit as st
from datetime import date
from database import esegui_query, carica_tabella

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
            st.dataframe(df_all, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("2. Seleziona una fattura da Modificare o Cancellare")
            
            opzioni = {
                int(row["id"]): f"ID {int(row['id'])} | {row['data']} | {row['tipo']} n.{row['num']} - {row['anagrafica']} (€ {row['imponibile']})"
                for _, row in df_all.iterrows()
            }
            id_scelto = st.selectbox("Scegli la fattura:", options=list(opzioni.keys()), format_func=lambda x: opzioni[x])
            riga = df_all.set_index("id").loc[id_scelto]
            
            col_mod, col_del = st.columns(2)
            
            with col_mod:
                with st.expander("✏️ MODIFICA QUESTA FATTURA", expanded=True):
                    with st.form("form_modifica"):
                        m1, m2 = st.columns(2)
                        nuova_data = m1.text_input("Data (AAAA-MM-GG)", value=str(riga["data"]))
                        tipi = ("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA")
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
                        
                        nuova_pagata = st.checkbox("Pagata?", value=bool(riga["pagata"]))
                        
                        if st.form_submit_button("💾 Salva Modifiche", type="primary"):
                            esegui_query(
                                '''UPDATE fatture 
                                   SET data=:d, tipo=:t, num=:n, anagrafica=:a, imponibile=:i, iva_perc=:iv, socio=:s, pagata=:p 
                                   WHERE id=:id''',
                                {"d": nuova_data, "t": nuovo_tipo, "n": nuovo_num, "a": nuova_anag.upper(),
                                 "i": nuovo_imp, "iv": nuova_iva, "s": nuovo_socio, "p": int(nuova_pagata), "id": int(id_scelto)}
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
            st.warning("Nessun movimento registrato.")

    with tab2:
        with st.form("nuova_fattura"):
            c1, c2, c3 = st.columns(3)
            data_doc = c1.date_input("Data", value=date.today())
            tipo_doc = c2.selectbox("Tipo Documento", options=("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA"))
            num_doc = c3.text_input("Numero Documento (es. 71/2026)")
            
            c4, c5, c6 = st.columns(3)
            anagrafica = c4.text_input("Cliente / Fornitore")
            imponibile = c5.number_input("Imponibile (€)", min_value=0.0, step=10.0)
            iva_perc = c6.selectbox("IVA %", options=(22, 10, 5, 4, 0))
            
            c7, c8, c9 = st.columns(3)
            socio = c7.selectbox("Socio", options=("BAGLI", "TROPEA", "COMUNE"))
            ritenuta = c8.number_input("Ritenuta %", min_value=0.0, max_value=100.0, value=0.0)
            categoria = c9.text_input("Categoria", value="Generale")
            
            if st.form_submit_button("➕ Registra Movimento"):
                esegui_query(
                    '''INSERT INTO fatture (data, tipo, num, anagrafica, imponibile, iva_perc, socio, ritenuta_perc, costo_categoria, pagata) 
                       VALUES (:d, :t, :n, :a, :i, :iv, :s, :r, :c, 1)''',
                    {"d": str(data_doc), "t": tipo_doc, "n": num_doc, "a": anagrafica.upper(),
                     "i": imponibile, "iv": iva_perc, "s": socio, "r": ritenuta, "c": categoria}
                )
                st.success("✅ Registrazione inserita su Cloud!")
                st.rerun()



