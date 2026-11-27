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
    df["totale_lordo"] = df["imponibile"] * (1 + df["iva_perc"] / 100)
    
    da_saldare = df[df["pagata"] == 0]
    da_incassare = da_saldare[da_saldare["tipo"] == "FATTURA EMESSA"]
    da_pagare = da_saldare[da_saldare["tipo"] != "FATTURA EMESSA"]
    
    c1, c2 = st.columns(2)
    c1.metric("💰 Crediti da Incassare (Clienti)", f"€ {da_incassare['totale_lordo'].sum():,.2f}", f"{len(da_incassare)} fatture")
    c2.metric("💸 Debiti da Pagare (Fornitori)", f"€ {da_pagare['totale_lordo'].sum():,.2f}", f"{len(da_pagare)} fatture")
    
    st.divider()
    
    if da_saldare.empty:
        st.success("🎉 Tutte le fatture risultano incassate o pagate!")
    else:
        st.subheader("Elenco Fatture Aperte (Non ancora saldate)")
        st.dataframe(
            da_saldare[["id", "data", "tipo", "num", "anagrafica", "totale_lordo", "socio"]],
            use_container_width=True,
            hide_index=True
        )
        
        st.subheader("✅ Segna come Incassata / Pagata")
        opzioni = {
            int(r["id"]): f"ID {int(r['id'])} | {r['tipo']} n.{r['num']} - {r['anagrafica']} (€ {r['totale_lordo']:,.2f})"
            for _, r in da_saldare.iterrows()
        }
        id_saldato = st.selectbox("Seleziona la fattura saldata:", options=list(opzioni.keys()), format_func=lambda x: opzioni[x])
        
        if st.button("✅ Conferma Incasso / Pagamento", type="primary"):
            esegui_query("UPDATE fatture SET pagata=1 WHERE id=:id", {"id": int(id_saldato)})
            st.success("Fattura segnata come saldata!")
            st.rerun()
