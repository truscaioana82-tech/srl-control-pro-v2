import streamlit as st
from datetime import date
from database import get_connection, carica_tabella, salva_tabella

# --- MODULO 1: PRIMA NOTA & FATTURE MODIFICABILI ---
def mostra_prima_nota():
    st.title("📝 Prima Nota & Registro Fatture")
    tab1, tab2 = st.tabs(["✏️ Storico & Modifica Diretta", "➕ Nuova Registrazione"])
    
    with tab1:
        st.info("💡 Fai doppio clic su qualsiasi cella per modificarla (o seleziona una riga e premi Canc per eliminarla), poi clicca su **Salva Modifiche**.")
        df_all = carica_tabella("fatture")
        if not df_all.empty:
            df_all = df_all.sort_values(by="id", ascending=False)
            df_all["pagata"] = df_all["pagata"].fillna(1).astype(bool)
            
            edited_df = st.data_editor(
                df_all,
                num_rows="dynamic",
                use_container_width=True,
                disabled=["id"],
                column_config={
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA")),
                    "socio": st.column_config.SelectboxColumn("Socio", options=("BAGLI", "TROPEA", "COMUNE")),
                    "pagata": st.column_config.CheckboxColumn("Pagata?")
                }
            )
            if st.button("💾 Salva Modifiche nella Tabella", type="primary"):
                edited_df["pagata"] = edited_df["pagata"].astype(int)
                salva_tabella(edited_df, "fatture")
                st.success("✅ Modifiche salvate!")
                st.rerun()
        else:
            st.warning("Nessun movimento registrato.")

    with tab2:
        with st.form("nuova_fattura"):
            c1, c2, c3 = st.columns(3)
            data_doc = c1.date_input("Data", value=date.today())
            tipo_doc = c2.selectbox("Tipo Documento", options=("FATTURA EMESSA", "FATTURA ACQUISTO", "RICEVUTA"))
            num_doc = c3.text_input("Numero Documento (es. 71/2026)")
            
            c4, c5, c6 = st.columns(3)
            anagrafica = c4.text_input("Cliente / Fornitore")
            imponibile = c5.number_input("Imponibile (€)", min_value=0.0, step=10.0)
            iva_perc = c6.selectbox("IVA %", options=(22, 10, 5, 4, 0))
            
            c7, c8, c9 = st.columns(3)
            socio = c7.selectbox("Socio", options=("BAGLI", "TROPEA", "COMUNE"))
            ritenuta = c8.number_input("Ritenuta %", min_value=0.0, max_value=100.0, value=0.0)
            categoria = c9.text_input("Categoria", value="Generale")
            
            if st.form_submit_button("➕ Registra Movimento"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO fatture (data, tipo, num, anagrafica, imponibile, iva_perc, socio, ritenuta_perc, costo_categoria, pagata) VALUES (?,?,?,?,?,?,?,?,?,1)",
                          (str(data_doc), tipo_doc, num_doc, anagrafica.upper(), imponibile, iva_perc, socio, ritenuta, categoria))
                conn.commit()
                conn.close()
                st.success("✅ Registrazione inserita!")
                st.rerun()

# --- MODULO 2: DIPENDENTI & STIPENDI ---
def mostra_stipendi():
    st.title("👥 Gestione Dipendenti & Stipendi")
    with st.form("nuovo_stipendio"):
        st.subheader("Registra Busta Paga Mensile")
        c1, c2, c3 = st.columns(3)
        data_pag = c1.date_input("Data Pagamento", value=date.today())
        dipendente = c2.text_input("Nome e Cognome Dipendente")
        mese_comp = c3.selectbox("Mese", options=("Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"))
        
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

# --- MODULO 3: LIQUIDAZIONE IVA & F24 ---
def mostra_iva(df_fatture):
    st.title("🧾 Riepilogo IVA")
    if not df_fatture.empty:
        df_fatture['importo_iva'] = df_fatture['imponibile'] * (df_fatture['iva_perc'] / 100)
        iva_v = df_fatture[df_fatture['tipo'] == 'FATTURA EMESSA']['importo_iva'].sum()
        iva_a = df_fatture[df_fatture['tipo'] != 'FATTURA EMESSA']['importo_iva'].sum()
        saldo = iva_a - iva_v
        
        c1, c2, c3 = st.columns(3)
        c1.metric("IVA su Vendite (Debito)", f"€ {iva_v:,.2f}")
        c2.metric("IVA su Acquisti (Credito)", f"€ {iva_a:,.2f}")
        c3.metric("Saldo IVA", f"€ {abs(saldo):,.2f}", "A Credito" if saldo >= 0 else "Da Versare")
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
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO f24 (scadenza, descrizione, importo, pagato) VALUES (?,?,?,0)", (str(scad), desc, imp))
            conn.commit()
            conn.close()
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

