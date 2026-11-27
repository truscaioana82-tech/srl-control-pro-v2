import streamlit as st
from database import get_connection, carica_tabella, salva_tabella

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
