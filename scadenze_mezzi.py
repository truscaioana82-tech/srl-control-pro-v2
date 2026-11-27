import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import esegui_query, carica_tabella, salva_tabella

CATEGORIE_SCADENZE = (
    "Assicurazione Mezzo",
    "Bollo / Revisione Mezzo",
    "DURC / Patente a Crediti",
    "Contratto / Noleggio",
    "Visite Mediche / Corsi Sicurezza",
    "Altra Scadenza"
)

def mostra_scadenze_mezzi():
    st.title("🚛 Scadenzario Mezzi, Polizze, DURC & Contratti")
    
    # --- MODULO NUOVO INSERIMENTO ---
    with st.expander("➕ Aggiungi Nuova Scadenza (Mezzo, Polizza, DURC o Contratto)", expanded=False):
        with st.form("form_nuova_scadenza_edile"):
            c1, c2, c3 = st.columns(3)
            data_scad = c1.date_input("Data Scadenza", value=date.today())
            categoria = c2.selectbox("Categoria", options=CATEGORIE_SCADENZE)
            socio = c3.selectbox("Socio di riferimento", options=("COMUNE", "BAGLI", "TROPEA"))
            
            c4, c5, c6 = st.columns([1.2, 2, 1])
            mezzo_rif = c4.text_input("Targa / Mezzo / Ente", placeholder="Es. Fiat Ducato AB123CD o INPS")
            descrizione = c5.text_input("Descrizione / Polizza / Note", placeholder="Es. Polizza Unipol n. 12345 o Rinnovo DURC")
            importo = c6.number_input("Importo previsto (€)", min_value=0.0, step=10.0, value=0.0)
            
            if st.form_submit_button("💾 Salva Scadenza", type="primary"):
                esegui_query(
                    '''INSERT INTO scadenze_edili (scadenza, categoria, mezzo_riferimento, descrizione, importo, socio, rinnovata) 
                       VALUES (:sc, :cat, :m, :d, :imp, :so, 0)''',
                    {
                        "sc": str(data_scad),
                        "cat": categoria,
                        "m": mezzo_rif.strip().upper(),
                        "d": descrizione.strip(),
                        "imp": importo,
                        "so": socio
                    }
                )
                st.success("✅ Scadenza registrata su Cloud!")
                st.rerun()

    df = carica_tabella("scadenze_edili")
    if df.empty:
        st.info("Nessuna scadenza registrata. Apri il riquadro qui sopra per inserire la prima polizza, revisione o DURC!")
        return
    df["rinnovata"] = df["rinnovata"].fillna(0).astype(bool)
    df["scad_dt"] = pd.to_datetime(df["scadenza"], errors="coerce").dt.date
    oggi = date.today()

    # Calcolo giorni alla scadenza solo per quelle NON ancora rinnovate
    df["Giorni"] = df.apply(
        lambda r: (r["scad_dt"] - oggi).days if (not r["rinnovata"] and pd.notnull(r["scad_dt"])) else 9999,
        axis=1
    )

    scadute = df[(~df["rinnovata"]) & (df["Giorni"] < 0)]
    in_scadenza_30 = df[(~df["rinnovata"]) & (df["Giorni"] >= 0) & (df["Giorni"] <= 30)]
    attive_attesa = df[~df["rinnovata"]]

    # --- ALERT VISIVI IN ALTO ---
    if not scadute.empty:
        st.error(f"🚨 **ATTENZIONE: Hai {len(scadute)} scadenze già SUPERATE!** Controlla subito la tabella qui sotto.")
    if not in_scadenza_30.empty:
        st.warning(f"⚠️ **AVVISO: Hai {len(in_scadenza_30)} scadenze nei prossimi 30 giorni!**")

    m1, m2, m3 = st.columns(3)
    m1.metric("🚨 Scadute", f"{len(scadute)}")
    m2.metric("⏳ In scadenza (entro 30 gg)", f"{len(in_scadenza_30)}")
    m3.metric("💶 Importo Totale da Rinnovare", f"€ {attive_attesa['importo'].fillna(0).sum():,.2f}")

    st.divider()

    # --- FILTRI RAPIDI ---
    f1, f2, f3 = st.columns(3)
    filtro_stato = f1.selectbox("Mostra:", options=["Solo da rinnovare / attive", "Tutte (anche già rinnovate)"])
    filtro_cat = f2.selectbox("Filtra Categoria:", options=["Tutte"] + list(CATEGORIE_SCADENZE))
    filtro_socio = f3.selectbox("Filtra Socio:", options=["Tutti", "COMUNE", "BAGLI", "TROPEA"])

    df_vista = df.copy()
    if filtro_stato == "Solo da rinnovare / attive":
        df_vista = df_vista[~df_vista["rinnovata"]]
    if filtro_cat != "Tutte":
        df_vista = df_vista[df_vista["categoria"] == filtro_cat]
    if filtro_socio != "Tutti":
        df_vista = df_vista[df_vista["socio"] == filtro_socio]

    df_vista = df_vista.sort_values(by="scadenza")

    def etichetta_stato(row):
        if row["rinnovata"]:
            return "✅ Rinnovata"
        g = row["Giorni"]
        if g < 0:
            return f"🚨 SCADUTA da {abs(g)} gg"
        elif g == 0:
            return "🚨 SCADE OGGI"
        elif g <= 30:
            return f"⚠️ Scade tra {g} gg"
        else:
            return f"🟢 Ok ({g} gg)"

    df_vista["Stato"] = df_vista.apply(etichetta_stato, axis=1)

    st.caption("Puoi modificare direttamente date, importi o spuntare **Rinnovata?** nella tabella e poi cliccare su **Salva Modifiche Tabella**.")
    colonne_editor = ["Stato", "rinnovata", "scadenza", "categoria", "mezzo_riferimento", "descrizione", "importo", "socio", "id"]
    
    ed_df = st.data_editor(
        df_vista[colonne_editor],
        use_container_width=True,
        hide_index=True,
        disabled=["id", "Stato"],
        column_config={
            "rinnovata": st.column_config.CheckboxColumn("Rinnovata?", default=False),
            "scadenza": st.column_config.TextColumn("Scadenza (AAAA-MM-GG)"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIE_SCADENZE),
            "mezzo_riferimento": st.column_config.TextColumn("Targa / Mezzo / Ente"),
            "descrizione": st.column_config.TextColumn("Descrizione / Polizza"),
            "importo": st.column_config.NumberColumn("Importo (€)", format="€ %.2f"),
            "socio": st.column_config.SelectboxColumn("Socio", options=["COMUNE", "BAGLI", "TROPEA"])
        },
        key="editor_scadenze_edili"
    )

    if st.button("💾 Salva Modifiche Tabella", type="primary"):
        for _, r in ed_df.iterrows():
            esegui_query(
                '''UPDATE scadenze_edili 
                   SET scadenza=:sc, categoria=:cat, mezzo_riferimento=:m, descrizione=:d, importo=:imp, socio=:so, rinnovata=:rin 
                   WHERE id=:id''',
                {
                    "sc": str(r["scadenza"]),
                    "cat": r["categoria"],
                    "m": str(r["mezzo_riferimento"]).upper(),
                    "d": str(r["descrizione"]),
                    "imp": float(r["importo"] or 0.0),
                    "so": r["socio"],
                    "rin": int(bool(r["rinnovata"])),
                    "id": int(r["id"])
                }
            )
        st.success("✅ Scadenzario mezzi e polizze aggiornato!")
        st.rerun()

