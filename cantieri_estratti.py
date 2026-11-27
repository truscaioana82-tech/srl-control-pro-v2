import streamlit as st
import pandas as pd

def mostra_cantieri(df_fatture, df_stipendi):
    st.title("🏗️ Analisi Margine per Cantiere / Commessa")
    
    if df_fatture.empty and df_stipendi.empty:
        st.info("Nessun dato disponibile per il periodo selezionato.")
        return

    df_f = df_fatture.copy() if not df_fatture.empty else pd.DataFrame()
    df_s = df_stipendi.copy() if not df_stipendi.empty else pd.DataFrame()

    if not df_f.empty:
        df_f["cantiere"] = df_f["cantiere"].fillna("GENERALE").replace("", "GENERALE").astype(str).str.upper()
    if not df_s.empty:
        df_s["cantiere"] = df_s["cantiere"].fillna("GENERALE").replace("", "GENERALE").astype(str).str.upper()

    cantieri_f = set(df_f["cantiere"].unique()) if not df_f.empty else set()
    cantieri_s = set(df_s["cantiere"].unique()) if not df_s.empty else set()
    tutti_cantieri = sorted(list(cantieri_f.union(cantieri_s)))

    righe = []
    for cant in tutti_cantieri:
        sub_f = df_f[df_f["cantiere"] == cant] if not df_f.empty else pd.DataFrame()
        sub_s = df_s[df_s["cantiere"] == cant] if not df_s.empty else pd.DataFrame()

        if not sub_f.empty:
            t_up = sub_f["tipo"].astype(str).str.upper()
            cat_up = sub_f["costo_categoria"].astype(str).str.upper()
            is_nc = t_up.str.contains("CREDITO|NC", na=False)
            is_om = t_up.str.contains("OMAGG", na=False)
            is_dip_v = t_up.str.contains("STIPEND|DIPEND|BUSTA|PERSONALE|CASSA EDILE", na=False) | cat_up.str.contains("STIPEND|DIPEND|PERSONALE|CASSA EDILE", na=False)
            is_em = t_up.str.contains("EMESS|VENDIT|ENTRAT", na=False) & ~is_nc & ~is_om
            is_forn = ~is_em & ~is_nc & ~is_om & ~is_dip_v

            ricavi = sub_f[is_em]["imponibile"].sum() - sub_f[is_nc]["imponibile"].sum()
            materiali = sub_f[is_forn]["imponibile"].sum()
            dip_vecchi = sub_f[is_dip_v]["imponibile"].sum()
        else:
            ricavi, materiali, dip_vecchi = 0.0, 0.0, 0.0

        if not sub_s.empty:
            ce = sub_s["cassa_edile"].fillna(0.0).sum() if "cassa_edile" in sub_s.columns else 0.0
            manodopera = dip_vecchi + (sub_s["netto"] + sub_s["contributi_f24"]).sum() + ce
        else:
            manodopera = dip_vecchi

        utile_cant = ricavi - materiali - manodopera
        margine_perc = (utile_cant / ricavi * 100) if ricavi > 0 else 0.0

        righe.append({
            "Cantiere": cant,
            "Ricavi Netti (€)": ricavi,
            "Materiali & Fornitori (€)": materiali,
            "Operai & Cassa Edile (€)": manodopera,
            "Utile Cantiere (€)": utile_cant,
            "Margine %": margine_perc
        })

    df_res = pd.DataFrame(righe).sort_values(by="Utile Cantiere (€)", ascending=False)
    
    st.dataframe(
        df_res.style.format({
            "Ricavi Netti (€)": "€ {:,.2f}",
            "Materiali & Fornitori (€)": "€ {:,.2f}",
            "Operai & Cassa Edile (€)": "€ {:,.2f}",
            "Utile Cantiere (€)": "€ {:,.2f}",
            "Margine %": "{:.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    cantiere_dettaglio = st.selectbox("🔍 Ispeziona movimenti del cantiere:", options=tutti_cantieri)
    if not df_f.empty:
        st.markdown(f"**Fatture collegate a: {cantiere_dettaglio}**")
        st.dataframe(df_f[df_f["cantiere"] == cantiere_dettaglio], use_container_width=True, hide_index=True)
    if not df_s.empty and not df_s[df_s["cantiere"] == cantiere_dettaglio].empty:
        st.markdown(f"**Stipendi collegati a: {cantiere_dettaglio}**")
        st.dataframe(df_s[df_s["cantiere"] == cantiere_dettaglio], use_container_width=True, hide_index=True)
def mostra_estratto_conto(df_fatture):
    st.title("📑 Estratto Conto Cliente / Fornitore")
    
    if df_fatture.empty:
        st.info("Nessun movimento presente nel periodo selezionato.")
        return

    df_f = df_fatture.copy()
    df_f["anagrafica"] = df_f["anagrafica"].fillna("SCONOSCIUTO").astype(str).str.strip().str.upper()
    df_f["pagata"] = df_f["pagata"].fillna(1).astype(int)
    df_f["totale_lordo"] = (df_f["imponibile"] * (1 + df_f["iva_perc"] / 100)).round(2)

    nomi = sorted(df_f["anagrafica"].unique().tolist())
    scelto = st.selectbox("👤 Seleziona Cliente o Fornitore:", options=nomi)

    sub = df_f[df_f["anagrafica"] == scelto].sort_values(by="data", ascending=False)
    
    tot_imp = sub["imponibile"].sum()
    tot_lordo = sub["totale_lordo"].sum()
    saldato = sub[sub["pagata"] == 1]["totale_lordo"].sum()
    aperto = sub[sub["pagata"] == 0]["totale_lordo"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Documenti", f"{len(sub)}")
    c2.metric("💶 Totale Imponibile", f"€ {tot_imp:,.2f}")
    c3.metric("✅ Già Saldato", f"€ {saldato:,.2f}")
    c4.metric("⏳ Ancora Aperto", f"€ {aperto:,.2f}")

    st.divider()
    sub_vista = sub[["data", "tipo", "num", "cantiere", "imponibile", "iva_perc", "totale_lordo", "socio", "pagata"]].copy()
    sub_vista["Stato"] = sub_vista["pagata"].apply(lambda x: "✅ Saldata" if x == 1 else "⏳ Aperta")
    sub_vista = sub_vista.drop(columns=["pagata"])

    st.dataframe(sub_vista, use_container_width=True, hide_index=True)
