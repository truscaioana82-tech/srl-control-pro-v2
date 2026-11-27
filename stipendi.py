import streamlit as st
from datetime import date
from database import get_connection, carica_tabella, salva_tabella

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
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO stipendi (data, dipendente, mese, netto, contributi_f24, socio) VALUES (?,?,?,?,?,?)",
                      (str(data_pag), dipendente.upper(), mese_comp, netto, contributi, socio_dip))
            if aggiungi_f24 and contributi > 0:
                c.execute("INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (?,?,?,0)",
                          (str(data_pag), f"F24 Stipendio {dipendente.upper()} - {mese_comp}", contributi))
            conn.commit()
            conn.close()
            st.success("✅ Stipendio registrato!")
            st.rerun()

    st.subheader("Storico Stipendi (Modificabile)")
    df_st = carica_tabella("stipendi")
    if not df_st.empty:
        ed_st = st.data_editor(df_st.sort_values(by="id", ascending=False), num_rows="dynamic", use_container_width=True, disabled=["id"])
        if st.button("💾 Salva Modifiche Stipendi"):
            salva_tabella(ed_st, "stipendi")
            st.success("✅ Stipendi aggiornati!")
            st.rerun()
