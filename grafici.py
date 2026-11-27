import streamlit as st
import pandas as pd

def mostra_grafici(df_fatture, df_stipendi):
    st.title("📈 Analisi Grafica: Mensile & Semestrale")
    
    if df_fatture.empty and df_stipendi.empty:
        st.info("Inserisci qualche movimento per visualizzare i grafici.")
        return

    # Pulizia e preparazione date (gestisce anche eventuali date scritte anno-giorno-mese)
    df_f = df_fatture.copy() if not df_fatture.empty else pd.DataFrame()
    if not df_f.empty:
        df_f["data_dt"] = pd.to_datetime(df_f["data"], errors="coerce", format="mixed")
        df_f = df_f.dropna(subset=["data_dt"])
        df_f["Mese_Num"] = df_f["data_dt"].dt.month
        df_f["Mese"] = df_f["data_dt"].dt.strftime("%Y-%m")
        df_f["Semestre"] = df_f["Mese_Num"].apply(lambda m: "1° Semestre (Gen-Giu)" if m <= 6 else "2° Semestre (Lug-Dic)")

    # --- SEZIONE 1: ANDAMENTO SEMESTRALE ---
    st.subheader("🗓️ Riepilogo Semestrale (Entrate, Uscite e Utile)")
    if not df_f.empty:
        ent_sem = df_f[df_f["tipo"] == "FATTURA EMESSA"].groupby("Semestre")["imponibile"].sum()
        usc_sem = df_f[df_f["tipo"] != "FATTURA EMESSA"].groupby("Semestre")["imponibile"].sum()
        
        df_sem = pd.DataFrame({"Entrate (€)": ent_sem, "Uscite (€)": usc_sem}).fillna(0)
        df_sem["Utile (€)"] = df_sem["Entrate (€)"] - df_sem["Uscite (€)"]
        
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.bar_chart(df_sem[["Entrate (€)", "Uscite (€)"]])
        with c2:
            st.dataframe(df_sem.style.format("€ {:,.2f}"), use_container_width=True)

    st.divider()

    # --- SEZIONE 2: ANDAMENTO MENSILE ---
    st.subheader("📅 Riepilogo Mensile (Mese per Mese)")
    if not df_f.empty:
        ent_m = df_f[df_f["tipo"] == "FATTURA EMESSA"].groupby("Mese")["imponibile"].sum()
        usc_m = df_f[df_f["tipo"] != "FATTURA EMESSA"].groupby("Mese")["imponibile"].sum()
        
        df_mensile = pd.DataFrame({"Entrate (€)": ent_m, "Uscite (€)": usc_m}).fillna(0).sort_index()
        df_mensile["Saldo Mese (€)"] = df_mensile["Entrate (€)"] - df_mensile["Uscite (€)"]
        
        c3, c4 = st.columns([1.2, 1])
        with c3:
            st.bar_chart(df_mensile[["Entrate (€)", "Uscite (€)"]])
        with c4:
            st.dataframe(df_mensile.style.format("€ {:,.2f}"), use_container_width=True)

    st.divider()

    # --- SEZIONE 3: CONFRONTO SOCI ---
    st.subheader("👥 Confronto BAGLI vs TROPEA")
    dati_soci = []
    for socio in ["BAGLI", "TROPEA", "COMUNE"]:
        ent = df_f[(df_f["socio"] == socio) & (df_f["tipo"] == "FATTURA EMESSA")]["imponibile"].sum() if not df_f.empty else 0.0
        usc_f = df_f[(df_f["socio"] == socio) & (df_f["tipo"] != "FATTURA EMESSA")]["imponibile"].sum() if not df_f.empty else 0.0
        usc_s = (df_stipendi[df_stipendi["socio"] == socio]["netto"] + df_stipendi[df_stipendi["socio"] == socio]["contributi_f24"]).sum() if not df_stipendi.empty else 0.0
        dati_soci.append({"Socio": socio, "Ricavi (€)": ent, "Costi + Stipendi (€)": usc_f + usc_s})
    
    st.bar_chart(pd.DataFrame(dati_soci).set_index("Socio"))

