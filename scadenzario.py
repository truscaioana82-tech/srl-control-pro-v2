import streamlit as st
from database import esegui_query, carica_tabella

def mostra_scadenzario():
    st.title("⏳ Fatture da Incassare e da Pagare")
    df = carica_tabella("fatture")
    
    if df.empty:
        st.info("Nessun movimento registrato.")
        return

    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)
    df["pagata"] = df["pagata"].fillna(1).astype(int)
    df["totale_lordo"] = (df["imponibile"] * (1 + df["iva_perc"] / 100)).round(2)
    
    # Filtro per Socio
    socio_scelto = st.selectbox("👤 Filtra per Socio:", options=["Tutti", "BAGLI", "TROPEA", "COMUNE"])
    if socio_scelto != "Tutti":
        df = df[df["socio"].astype(str).str.upper() == socio_scelto]

    da_saldare = df[df["pagata"] == 0].copy()
    
    t_up = da_saldare["tipo"].astype(str).str.upper() if not da_saldare.empty else ""
    is_emessa = t_up.str.contains("EMESS|VENDIT|ENTRAT", na=False) if not da_saldare.empty else []
    
    da_incassare = da_saldare[is_emessa].copy() if not da_saldare.empty else da_saldare
    da_pagare = da_saldare[~is_emessa].copy() if not da_saldare.empty else da_saldare
    
    tot_inc = da_incassare["totale_lordo"].sum() if not da_incassare.empty else 0.0
    tot_pag = da_pagare["totale_lordo"].sum() if not da_pagare.empty else 0.0
    sbilancio = tot_inc - tot_pag
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Crediti da Incassare (Clienti)", f"€ {tot_inc:,.2f}", f"{len(da_incassare)} fatture")
    c2.metric("💸 Debiti da Pagare (Fornitori)", f"€ {tot_pag:,.2f}", f"{len(da_pagare)} fatture")
    c3.metric("⚖️ Saldo Scadenzario", f"€ {abs(sbilancio):,.2f}", "In attivo" if sbilancio >= 0 else "In passivo", delta_color="normal" if sbilancio >= 0 else "inverse")
    
    st.divider()
    if da_saldare.empty:
        st.success("🎉 Tutte le fatture risultano incassate o pagate!")
        return

    tab_inc, tab_pag = st.tabs([
        f"💰 Da Incassare ({len(da_incassare)})", 
        f"💸 Da Pagare ({len(da_pagare)})"
    ])

    with tab_inc:
        if da_incassare.empty:
            st.info("Nessuna fattura cliente da incassare.")
        else:
            st.caption("Spunta la casella **Incassata?** sulle fatture saldate e clicca sul pulsante in basso.")
            da_incassare["Incassata?"] = False
            colonne_visibili = ["Incassata?", "id", "data", "num", "anagrafica", "totale_lordo", "socio"]
            
            ed_inc = st.data_editor(
                da_incassare[colonne_visibili].sort_values(by="data"),
                use_container_width=True,
                hide_index=True,
                disabled=["id", "data", "num", "anagrafica", "totale_lordo", "socio"],
                column_config={
                    "Incassata?": st.column_config.CheckboxColumn("Incassata?", default=False),
                    "totale_lordo": st.column_config.NumberColumn("Totale (€)", format="€ %.2f")
                },
                key="editor_incassi"
            )
            
            selezionate_inc = ed_inc[ed_inc["Incassata?"] == True]["id"].tolist()
            if selezionate_inc:
                if st.button(f"✅ Conferma incasso di {len(selezionate_inc)} fatture", type="primary", key="btn_inc"):
                    for fid in selezionate_inc:
                        esegui_query("UPDATE fatture SET pagata=1 WHERE id=:id", {"id": int(fid)})
                    st.success("✅ Incassi registrati!")
                    st.rerun()

    with tab_pag:
        if da_pagare.empty:
            st.info("Nessuna fattura fornitore da pagare.")
        else:
            st.caption("Spunta la casella **Pagata?** sulle fatture saldate e clicca sul pulsante in basso.")
            da_pagare["Pagata?"] = False
            colonne_visibili = ["Pagata?", "id", "data", "tipo", "num", "anagrafica", "totale_lordo", "socio"]
            
            ed_pag = st.data_editor(
                da_pagare[colonne_visibili].sort_values(by="data"),
                use_container_width=True,
                hide_index=True,
                disabled=["id", "data", "tipo", "num", "anagrafica", "totale_lordo", "socio"],
                column_config={
                    "Pagata?": st.column_config.CheckboxColumn("Pagata?", default=False),
                    "totale_lordo": st.column_config.NumberColumn("Totale (€)", format="€ %.2f")
                },
                key="editor_pagamenti"
            )
            
            selezionate_pag = ed_pag[ed_pag["Pagata?"] == True]["id"].tolist()
            if selezionate_pag:
                if st.button(f"✅ Conferma pagamento di {len(selezionate_pag)} fatture", type="primary", key="btn_pag"):
                    for fid in selezionate_pag:
                        esegui_query("UPDATE fatture SET pagata=1 WHERE id=:id", {"id": int(fid)})
                    st.success("✅ Pagamenti registrati!")
                    st.rerun()

