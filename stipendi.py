import streamlit as st
from datetime import date
from database import esegui_query, carica_tabella, salva_tabella

def mostra_stipendi():
    st.title("👥 Gestione Dipendenti & Stipendi")
    with st.form("nuovo_stipendio"):
        st.subheader("Registra Busta Paga Mensile")
        c1, c2, c3 = st.columns(3)
        data_pag = c1.date_input("Data Pagamento", value=date.today())
        dipendente = c2.text_input("Nome e Cognome Dipendente")
        mesi = ("Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre")
        mese_comp = c3.selectbox("Mese", options=mesi)
        
        c4, c5, c6 = st.columns(3)
        netto = c4.number_input("Netto in Busta (€)", min_value=0.0, step=50.0)
        contributi = c5.number_input("Contributi INPS + IRPEF F24 (€)", min_value=0.0, step=50.0)
        socio_dip = c6.selectbox("Centro di Costo", options=("BAGLI", "TROPEA", "COMUNE"))
        aggiungi_f24 = st.checkbox("Invia automaticamente i contributi allo scadenzario F24", value=True)
        
        if st.form_submit_button("💾 Registra Stipendio"):
            esegui_query(
                "INSERT INTO stipendi (data, dipendente, mese, netto, contributi_f24, socio) VALUES (:d, :dip, :m, :n, :c, :s)",
                {"d": str(data_pag), "dip": dipendente.upper(), "m": mese_comp, "n": netto, "c": contributi, "s": socio_dip}
            )
            if aggiungi_f24 and contributi > 0:
                esegui_query(
                    "INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (:sc, :desc, :imp, 0)",
                    {"sc": str(data_pag), "desc": f"F24 Stipendio {dipendente.upper()} - {mese_comp}", "imp": contributi}
                )
            st.success("✅ Stipendio registrato su Cloud!")
            st.rerun()

    st.subheader("Storico Stipendi (Modificabile)")
    df_st = carica_tabella("stipendi")
    if not df_st.empty:
        ed_st = st.data_editor(df_st.sort_values(by="id", ascending=False), num_rows="dynamic", use_container_width=True, disabled=["id"])
        if st.button("💾 Salva Modifiche Stipendi"):
            salva_tabella(ed_st, "stipendi")
            st.success("✅ Stipendi aggiornati!")
            st.rerun()

