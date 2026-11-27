import streamlit as st
import pandas as pd
import io
from datetime import date
from database import carica_tabella, get_engine

def _pulisci_e_salva(df, engine):
    df.columns = [str(c).strip().lower() for c in df.columns]
    rinomina = {
        "data_doc": "data", "data_fattura": "data",
        "cliente": "anagrafica", "fornitore": "anagrafica", "cliente_fornitore": "anagrafica",
        "numero": "num", "n": "num", "iva": "iva_perc", "categoria": "costo_categoria"
    }
    df = df.rename(columns=rinomina)
    
    colonne = ['data', 'tipo', 'num', 'anagrafica', 'imponibile', 'iva_perc', 'socio', 'ritenuta_perc', 'costo_categoria']
    for col in colonne:
        if col not in df.columns:
            df[col] = str(date.today()) if col == 'data' else (0.0 if 'perc' in col or col == 'imponibile' else "GENERALE")
    
    df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.strftime('%Y-%m-%d').fillna(str(date.today()))
    df['anagrafica'] = df['anagrafica'].fillna("").astype(str).str.upper()
    df['socio'] = df['socio'].fillna("COMUNE").astype(str).str.upper()
    df['imponibile'] = pd.to_numeric(df['imponibile'], errors='coerce').fillna(0.0)
    df['iva_perc'] = pd.to_numeric(df['iva_perc'], errors='coerce').fillna(22.0)
    df['pagata'] = 1
    
    df[colonne + ['pagata']].to_sql("fatture_v2", engine, if_exists="append", index=False)
    return len(df)

def mostra_import_export():
    st.title("📥 Backup & Migrazione Dati")
    
    # --- SCARICA BACKUP ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        carica_tabella("fatture").to_excel(writer, sheet_name="Fatture", index=False)
        carica_tabella("stipendi").to_excel(writer, sheet_name="Stipendi", index=False)
        carica_tabella("f24").to_excel(writer, sheet_name="F24", index=False)
    
    st.download_button("📤 Scarica Backup Completo Excel", data=buffer.getvalue(), file_name=f"Backup_SRL_{date.today()}.xlsx")
    
    st.divider()
    
    # --- IMPORTA DA EXCEL ---
    st.subheader("1️⃣ Importa vecchie fatture da Excel")
    uploaded = st.file_uploader("Seleziona il file Excel (.xlsx) esportato dalla vecchia app", type=["xlsx"])
    if uploaded:
        df_imp = pd.read_excel(uploaded)
        st.write("Anteprima dati trovati nel file:", df_imp.head(5))
        if st.button("📥 Conferma e Carica Excel nel Database Cloud"):
            n = _pulisci_e_salva(df_imp, get_engine())
            st.success(f"✅ Importate {n} fatture da Excel con successo!")

    st.divider()
    
    # --- RECUPERA DAL VECCHIO DATABASE NEON ---
    st.subheader("2️⃣ Recupera Dati Direttamente dal Vecchio Database Neon")
    st.info("Copia automaticamente tutte le fatture salvate nella tua app precedente direttamente qui.")
    if st.button("🚀 Importa Tutto dalla Vecchia App (Neon)", type="primary"):
        engine = get_engine()
        try:
            df_old = pd.read_sql_query("SELECT * FROM fatture", engine)
            if not df_old.empty:
                n = _pulisci_e_salva(df_old, engine)
                st.success(f"✅ Copiate {n} fatture dalla vecchia app!")
            else:
                st.warning("La vecchia tabella fatture su Neon è vuota.")
        except Exception as e:
            st.error(f"Nessuna vecchia tabella trovata o struttura diversa: {e}")
