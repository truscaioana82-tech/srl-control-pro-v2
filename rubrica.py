import streamlit as st
from sqlalchemy import text
from database import get_engine, carica_tabella, salva_tabella

def init_rubrica():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS rubrica_v2 (
            id SERIAL PRIMARY KEY,
            categoria TEXT,
            nome TEXT,
            piva_cf TEXT,
            telefono_email TEXT,
            iban_note TEXT
        )'''))

def ottieni_nomi_rubrica(categoria_filtro=None):
    init_rubrica()
    df = carica_tabella("rubrica_v2")
    if df.empty:
        return []
    if categoria_filtro:
        df = df[df["categoria"].isin(categoria_filtro)]
    return sorted(df["nome"].dropna().unique().tolist())

def mostra_rubrica():
    init_rubrica()
    st.title("📇 Rubrica Clienti, Fornitori & Dipendenti")
    
    with st.form("nuovo_contatto"):
        st.subheader("➕ Aggiungi Nuovo Contatto")
        c1, c2, c3 = st.columns(3)
        cat = c1.selectbox("Tipologia", options=("CLIENTE", "FORNITORE", "DIPENDENTE"))
        nome = c2.text_input("Ragione Sociale / Nome e Cognome")
        piva = c3.text_input("P.IVA / Codice Fiscale")
        
        c4, c5 = st.columns(2)
        contatti = c4.text_input("Telefono / Email")
        note = c5.text_input("IBAN / Mansione / Note")
        
        if st.form_submit_button("💾 Salva in Rubrica", type="primary"):
            if nome.strip():
                engine = get_engine()
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO rubrica_v2 (categoria, nome, piva_cf, telefono_email, iban_note) VALUES (:c, :n, :p, :t, :i)"),
                        {"c": cat, "n": nome.strip().upper(), "p": piva.strip().upper(), "t": contatti.strip(), "i": note.strip()}
                    )
                st.success(f"✅ {nome.upper()} salvato in rubrica!")
                st.rerun()
            else:
                st.warning("Inserisci il nome o la ragione sociale.")

    st.divider()
    st.subheader("📋 Elenco Anagrafiche (Modificabile con doppio clic)")
    df_rub = carica_tabella("rubrica_v2")
    if not df_rub.empty:
        ed_rub = st.data_editor(
            df_rub.sort_values(by="nome"),
            num_rows="dynamic",
            use_container_width=True,
            disabled=["id"],
            column_config={"categoria": st.column_config.SelectboxColumn("Tipologia", options=("CLIENTE", "FORNITORE", "DIPENDENTE"))}
        )
        if st.button("💾 Salva Modifiche Rubrica"):
            salva_tabella(ed_rub, "rubrica_v2")
            st.success("✅ Rubrica aggiornata!")
            st.rerun()
    else:
        st.info("La rubrica è ancora vuota. Aggiungi il primo contatto qui sopra.")
