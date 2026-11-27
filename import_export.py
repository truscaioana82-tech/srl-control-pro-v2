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
            df[col] = str(date.today()) if col == 'data' else (0.0 if 'perc' in col or col == 'imponibile' else "Generale")
    
    df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.strftime('%Y-%m-%d').fillna(str(date.today()))
    df['anagrafica'] = df['anagrafica'].fillna("").astype(str).str.upper()
    df['socio'] = df['socio'].fillna("COMUNE").astype(str).str.upper()
    df['imponibile'] = pd.to_numeric(df['imponibile'], errors='coerce').fillna(0.0)
    df['iva_perc'] = pd.to_numeric(df['iva_perc'], errors='coerce').fillna(22.0)
    df['pagata'] = 1
    
    df[colonne + ['pagata']].to_sql("fatture", engine, if_exists="append", index=False)
    return len(df)

def mostra_import_export():
    st.title("📥 Backup & Migrazione Dati")
    
    # --- SCARICA BACKUP COMPLETO ---
    st.subheader("💾 Salva una copia sul tuo computer")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        carica_tabella("fatture").to_excel(writer, sheet_name="Fatture", index=False)
        carica_tabella("stipendi").to_excel(writer, sheet_name="Stipendi", index=False)
        carica_tabella("f24").to_excel(writer, sheet_name="F24", index=False)
        try:
            carica_tabella("rubrica").to_excel(writer, sheet_name="Rubrica", index=False)
        except Exception:
            pass
    
    st.download_button(
        label="📤 Scarica Backup Completo Excel (Fatture, Stipendi, F24, Rubrica)",
        data=buffer.getvalue(),
        file_name=f"Backup_SRL_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    
    st.divider()
    
    # --- IMPORTA DA EXCEL ---
    st.subheader("1️⃣ Importa fatture da Excel")
    uploaded = st.file_uploader("Seleziona un file Excel (.xlsx)", type=["xlsx"])
    if uploaded:
        df_imp = pd.read_excel(uploaded)
        st.write("Anteprima dati trovati nel file:", df_imp.head(5))
        if st.button("📥 Conferma e Carica Excel nel Database Cloud"):
            n = _pulisci_e_salva(df_imp, get_engine())
            st.success(f"✅ Importate {n} fatture da Excel con successo!")

