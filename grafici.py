import streamlit as st
import pandas as pd

def prepara_dati_grafici(df_fatture, df_stipendi):
    df_f = df_fatture.copy() if not df_fatture.empty else pd.DataFrame()
    df_s = df_stipendi.copy() if not df_stipendi.empty else pd.DataFrame()
    
    if not df_f.empty:
        df_f["data_dt"] = pd.to_datetime(df_f["data"], errors="coerce", format="mixed")
        df_f = df_f.dropna(subset=["data_dt"])
        df_f["Mese_Num"] = df_f["data_dt"].dt.month
        df_f["Mese"] = df_f["data_dt"].dt.strftime("%Y-%m")
        df_f["Semestre"] = df_f["Mese_Num"].apply(lambda m: "1° Semestre (Gen-Giu)" if m <= 6 else "2° Semestre (Lug-Dic)")
        
        t_up = df_f["tipo"].astype(str).str.upper()
        cat_up = df_f["costo_categoria"].astype(str).str.upper() if "costo_categoria" in df_f.columns else pd.Series("", index=df_f.index)
        
        is_nc = t_up.str.contains("CREDITO|NC", na=False)
        is_omaggio = t_up.str.contains("OMAGG", na=False)
        is_dip_v = t_up.str.contains("STIPEND|DIPEND|BUSTA|PERSONALE|CASSA EDILE", na=False) | cat_up.str.contains("STIPEND|DIPEND|PERSONALE|CASSA EDILE", na=False)
        
        df_f["is_ricavo"] = t_up.str.contains("EMESS|VENDIT|ENTRAT", na=False) & ~is_nc & ~is_omaggio
        df_f["is_nc"] = is_nc
        df_f["is_costo"] = ~df_f["is_ricavo"] & ~is_nc & ~is_omaggio & ~is_dip_v
        df_f["is_dip_v"] = is_dip_v

    if not df_s.empty:
        df_s["data_dt"] = pd.to_datetime(df_s["data"], errors="coerce", format="mixed")
        df_s = df_s.dropna(subset=["data_dt"])
        df_s["Mese_Num"] = df_s["data_dt"].dt.month
        df_s["Mese"] = df_s["data_dt"].dt.strftime("%Y-%m")
        df_s["Semestre"] = df_s["Mese_Num"].apply(lambda m: "1° Semestre (Gen-Giu)" if m <= 6 else "2° Semestre (Lug-Dic)")
        ce = df_s["cassa_edile"].fillna(0.0) if "cassa_edile" in df_s.columns else 0.0
        df_s["tot_costo_dip"] = df_s["netto"].fillna(0.0) + df_s["contributi_f24"].fillna(0.0) + ce

    return df_f, df_s
def mostra_grafici(df_fatture, df_stipendi):
    st.title("📈 Analisi Grafica & Ripartizione Costi")
    
    if df_fatture.empty and df_stipendi.empty:
        st.info("Inserisci qualche movimento per visualizzare i grafici.")
        return

    df_f, df_s = prepara_dati_grafici(df_fatture, df_stipendi)

    # --- SEZIONE 1: ANDAMENTO SEMESTRALE ---
    st.subheader("🗓️ Riepilogo Semestrale (Ricavi, Costi Totali e Utile)")
    ent_sem = (df_f[df_f["is_ricavo"]].groupby("Semestre")["imponibile"].sum() - df_f[df_f["is_nc"]].groupby("Semestre")["imponibile"].sum().reindex(df_f["Semestre"].unique(), fill_value=0)) if not df_f.empty else pd.Series(dtype=float)
    usc_f_sem = df_f[df_f["is_costo"] | df_f["is_dip_v"]].groupby("Semestre")["imponibile"].sum() if not df_f.empty else pd.Series(dtype=float)
    usc_s_sem = df_s.groupby("Semestre")["tot_costo_dip"].sum() if not df_s.empty else pd.Series(dtype=float)
    
    df_sem = pd.DataFrame({
        "Ricavi (€)": ent_sem,
        "Fornitori (€)": usc_f_sem,
        "Dipendenti (€)": usc_s_sem
    }).fillna(0)
    df_sem["Uscite Totali (€)"] = df_sem["Fornitori (€)"] + df_sem["Dipendenti (€)"]
    df_sem["Utile Netto (€)"] = df_sem["Ricavi (€)"] - df_sem["Uscite Totali (€)"]
    
    if not df_sem.empty:
        c1, c2 = st.columns([1.1, 1.2])
        with c1:
            st.bar_chart(df_sem[["Ricavi (€)", "Uscite Totali (€)"]])
        with c2:
            st.dataframe(df_sem[["Ricavi (€)", "Uscite Totali (€)", "Utile Netto (€)"]].style.format("€ {:,.2f}"), use_container_width=True)

    st.divider()

    # --- SEZIONE 2: ANDAMENTO MENSILE ---
    st.subheader("📅 Riepilogo Mensile (Mese per Mese)")
    ent_m = df_f[df_f["is_ricavo"]].groupby("Mese")["imponibile"].sum() if not df_f.empty else pd.Series(dtype=float)
    nc_m = df_f[df_f["is_nc"]].groupby("Mese")["imponibile"].sum() if not df_f.empty else pd.Series(dtype=float)
    usc_f_m = df_f[df_f["is_costo"] | df_f["is_dip_v"]].groupby("Mese")["imponibile"].sum() if not df_f.empty else pd.Series(dtype=float)
    usc_s_m = df_s.groupby("Mese")["tot_costo_dip"].sum() if not df_s.empty else pd.Series(dtype=float)
    
    df_mensile = pd.DataFrame({
        "Ricavi": ent_m,
        "NC": nc_m,
        "Fornitori": usc_f_m,
        "Stipendi": usc_s_m
    }).fillna(0).sort_index()
    
    df_mensile["Ricavi (€)"] = df_mensile["Ricavi"] - df_mensile["NC"]
    df_mensile["Uscite (€)"] = df_mensile["Fornitori"] + df_mensile["Stipendi"]
    df_mensile["Saldo Mese (€)"] = df_mensile["Ricavi (€)"] - df_mensile["Uscite (€)"]
    
    if not df_mensile.empty:
        c3, c4 = st.columns([1.2, 1])
        with c3:
            st.bar_chart(df_mensile[["Ricavi (€)", "Uscite (€)"]])
        with c4:
            st.dataframe(df_mensile[["Ricavi (€)", "Uscite (€)", "Saldo Mese (€)"]].style.format("€ {:,.2f}"), use_container_width=True)

    st.divider()

    # --- SEZIONE 3: ANALISI SPESE PER CATEGORIA ---
    st.subheader("🏷️ Ripartizione Spese Fornitori per Categoria")
    if not df_f.empty and df_f["is_costo"].any():
        df_cat = df_f[df_f["is_costo"]].copy()
        df_cat["costo_categoria"] = df_cat["costo_categoria"].fillna("Generale").replace("", "Generale")
        
        spese_cat = df_cat.groupby("costo_categoria")["imponibile"].sum().sort_values(ascending=False)
        tot_spese = spese_cat.sum()
        
        df_riep_cat = pd.DataFrame({
            "Spesa Imponibile (€)": spese_cat,
            "Incidenza %": (spese_cat / tot_spese * 100) if tot_spese > 0 else 0
        })
        
        cc1, cc2 = st.columns([1.2, 1])
        with cc1:
            st.bar_chart(spese_cat, horizontal=True)
        with cc2:
            st.dataframe(
                df_riep_cat.style.format({"Spesa Imponibile (€)": "€ {:,.2f}", "Incidenza %": "{:.1f}%"}),
                use_container_width=True
            )
    else:
        st.info("Nessuna spesa fornitore registrata nel periodo selezionato.")

    st.divider()

    # --- SEZIONE 4: CONFRONTO SOCI ---
    st.subheader("👥 Confronto BAGLI vs TROPEA")
    dati_soci = []
    for socio in ["BAGLI", "TROPEA", "COMUNE"]:
        s_f = df_f[df_f["socio"].astype(str).str.upper() == socio] if not df_f.empty else pd.DataFrame()
        s_s = df_s[df_s["socio"].astype(str).str.upper() == socio] if not df_s.empty else pd.DataFrame()
        
        ent = (s_f[s_f["is_ricavo"]]["imponibile"].sum() - s_f[s_f["is_nc"]]["imponibile"].sum()) if not s_f.empty else 0.0
        usc_f = s_f[s_f["is_costo"] | s_f["is_dip_v"]]["imponibile"].sum() if not s_f.empty else 0.0
        usc_s = s_s["tot_costo_dip"].sum() if not s_s.empty else 0.0
        
        dati_soci.append({"Socio": socio, "Ricavi (€)": ent, "Costi + Stipendi (€)": usc_f + usc_s})
    
    st.bar_chart(pd.DataFrame(dati_soci).set_index("Socio"))

