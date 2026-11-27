import streamlit as st
from database import esegui_query, carica_tabella, salva_tabella

def calcola_valori_iva(df):
    if df.empty:
        return 0.0, 0.0, 0.0
    
    t_up = df['tipo'].astype(str).str.upper()
    cat_up = df['costo_categoria'].astype(str).str.upper() if 'costo_categoria' in df.columns else ""
    
    is_nc = t_up.str.contains('CREDITO|NC', na=False)
    is_omaggio = t_up.str.contains('OMAGG', na=False)
    is_dip = t_up.str.contains('STIPEND|DIPEND|BUSTA|PERSONALE|CASSA EDILE', na=False) | (cat_up.str.contains('STIPEND|DIPEND|PERSONALE|CASSA EDILE', na=False) if isinstance(cat_up, object) and hasattr(cat_up, 'str') else False)
    
    is_emessa = t_up.str.contains('EMESS|VENDIT|ENTRAT', na=False) & ~is_nc & ~is_omaggio
    is_acquisto = ~is_emessa & ~is_nc & ~is_omaggio & ~is_dip

    iva_series = df['imponibile'] * (df['iva_perc'] / 100)
    
    iva_v = iva_series[is_emessa].sum() - iva_series[is_nc].sum()
    iva_a = iva_series[is_acquisto].sum()
    saldo = iva_a - iva_v
    
    return iva_v, iva_a, saldo

def mostra_iva(df_fatture):
    st.title("🧾 Riepilogo IVA")
    if not df_fatture.empty:
        # 1. Totale Generale SRL
        st.subheader("🏛️ Totale Generale SRL")
        iva_v, iva_a, saldo = calcola_valori_iva(df_fatture)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("IVA su Vendite (Debito)", f"€ {iva_v:,.2f}")
        c2.metric("IVA su Acquisti (Credito)", f"€ {iva_a:,.2f}")
        c3.metric("Saldo IVA SRL", f"€ {abs(saldo):,.2f}", "A Credito" if saldo >= 0 else "Da Versare", delta_color="normal" if saldo >= 0 else "inverse")
        
        st.divider()
        
        # 2. Dettaglio per Socio
        st.subheader("👥 Dettaglio IVA per Socio")
        col_b, col_t = st.columns(2)
        
        for socio, col in [("BAGLI", col_b), ("TROPEA", col_t)]:
            with col:
                st.markdown(f"### 👤 Socio: {socio}")
                df_socio = df_fatture[df_fatture['socio'].astype(str).str.upper() == socio]
                iv_s, ia_s, sal_s = calcola_valori_iva(df_socio)
                
                m1, m2 = st.columns(2)
                m1.metric("IVA Debito", f"€ {iv_s:,.2f}")
                m2.metric("IVA Credito", f"€ {ia_s:,.2f}")
                st.metric(
                    f"Saldo IVA ({socio})", 
                    f"€ {abs(sal_s):,.2f}", 
                    "A Credito" if sal_s >= 0 else "Da Versare",
                    delta_color="normal" if sal_s >= 0 else "inverse"
                )

        # Mostra eventuale quota COMUNE solo se ci sono movimenti registrati come COMUNE
        df_comune = df_fatture[df_fatture['socio'].astype(str).str.upper() == "COMUNE"]
        if not df_comune.empty:
            st.divider()
            st.markdown("### 🤝 Quota COMUNE")
            iv_c, ia_c, sal_c = calcola_valori_iva(df_comune)
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("IVA Debito (Comune)", f"€ {iv_c:,.2f}")
            cc2.metric("IVA Credito (Comune)", f"€ {ia_c:,.2f}")
            cc3.metric("Saldo IVA (Comune)", f"€ {abs(sal_c):,.2f}", "A Credito" if sal_c >= 0 else "Da Versare")
            
    else:
        st.info("Nessun dato IVA per il periodo selezionato.")

def mostra_f24():
    st.title("📅 Scadenzario F24")
    with st.form("nuovo_f24"):
        c1, c2, c3 = st.columns(3)
        scad = c1.date_input("Data Scadenza")
        desc = c2.text_input("Descrizione Tributo")
        imp = c3.number_input("Importo (€)", min_value=0.0, step=10.0)
        if st.form_submit_button("➕ Aggiungi F24"):
            esegui_query(
                "INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (:sc, :d, :i, 0)",
                {"sc": str(scad), "d": desc, "i": imp}
            )
            st.rerun()

    df_f24 = carica_tabella("f24")
    if not df_f24.empty:
        df_f24["pagato"] = df_f24["pagato"].fillna(0).astype(bool)
        ed_f24 = st.data_editor(
            df_f24.sort_values(by="scadenza"),
            num_rows="dynamic",
            use_container_width=True,
            disabled=["id"],
            column_config={"pagato": st.column_config.CheckboxColumn("Pagato?")}
        )
        if st.button("💾 Aggiorna Scadenzario"):
            ed_f24["pagato"] = ed_f24["pagato"].astype(int)
            salva_tabella(ed_f24, "f24")
            st.success("✅ Scadenzario aggiornato!")
            st.rerun()

