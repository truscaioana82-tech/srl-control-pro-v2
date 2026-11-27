import streamlit as st
from datetime import date
from database import esegui_query, carica_tabella, salva_tabella
from rubrica import ottieni_nomi_rubrica

def mostra_stipendi():
    st.title("👥 Gestione Dipendenti, Stipendi & Cassa Edile")
    dipendenti_rubrica = ottieni_nomi_rubrica(["DIPENDENTE"])
    
    with st.form("nuovo_stipendio"):
        st.subheader("Registra Busta Paga & Cassa Edile Mensile")
        c1, c2, c3 = st.columns(3)
        data_pag = c1.date_input("Data Pagamento", value=date.today())
        dip_scelto = c2.selectbox("Scegli Dipendente da Rubrica", options=["-- Scrivi nuovo nome --"] + dipendenti_rubrica)
        dip_nuovo = c3.text_input("Oppure scrivi Nome e Cognome")
        
        c4, c5, c6, c7, c8 = st.columns(5)
        mesi = ("Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre")
        mese_comp = c4.selectbox("Mese", options=mesi)
        netto = c5.number_input("Netto Busta (€)", min_value=0.0, step=50.0)
        contributi = c6.number_input("INPS + F24 (€)", min_value=0.0, step=50.0)
        cassa_edile = c7.number_input("🏗️ Cassa Edile (€)", min_value=0.0, step=20.0)
        socio_dip = c8.selectbox("Socio", options=("BAGLI", "TROPEA", "COMUNE"))
        
        aggiungi_scad = st.checkbox("Invia automaticamente F24 e Cassa Edile allo scadenzario", value=True)
        
        if st.form_submit_button("💾 Registra Stipendio & Cassa Edile", type="primary"):
            dip_finale = dip_nuovo.strip().upper() if dip_nuovo.strip() else (dip_scelto if dip_scelto != "-- Scrivi nuovo nome --" else "")
            esegui_query(
                "INSERT INTO stipendi (data, dipendente, mese, netto, contributi_f24, cassa_edile, socio) VALUES (:d, :dip, :m, :n, :c, :ce, :s)",
                {"d": str(data_pag), "dip": dip_finale, "m": mese_comp, "n": netto, "c": contributi, "ce": cassa_edile, "s": socio_dip}
            )
            if aggiungi_scad:
                if contributi > 0:
                    esegui_query(
                        "INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (:sc, :desc, :imp, 0)",
                        {"sc": str(data_pag), "desc": f"F24 Stipendio {dip_finale} - {mese_comp}", "imp": contributi}
                    )
                if cassa_edile > 0:
                    esegui_query(
                        "INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (:sc, :desc, :imp, 0)",
                        {"sc": str(data_pag), "desc": f"Cassa Edile {dip_finale} - {mese_comp}", "imp": cassa_edile}
                    )
            st.success("✅ Stipendio e Cassa Edile registrati su Cloud!")
            st.rerun()

    st.subheader("Storico Stipendi & Cassa Edile (Modificabile)")
    df_st = carica_tabella("stipendi")
    if not df_st.empty:
        df_st["cassa_edile"] = df_st["cassa_edile"].fillna(0.0)
        ed_st = st.data_editor(df_st.sort_values(by="id", ascending=False), num_rows="dynamic", use_container_width=True, disabled=["id"])
        if st.button("💾 Salva Modifiche Stipendi"):
            salva_tabella(ed_st, "stipendi")
            st.success("✅ Stipendi aggiornati!")
            st.rerun()


