import streamlit as st
import pandas as pd
import io
from datetime import date
from database import init_db, carica_tabella, get_connection
from fatture import mostra_prima_nota
from stipendi import mostra_stipendi
from iva_f24 import mostra_iva, mostra_f24
from scadenzario import mostra_scadenzario
from grafici import mostra_grafici

st.set_page_config(page_title="SRL Control Pro 2.0", page_icon="🏛️", layout="wide")
init_db()

st.sidebar.title("🏛️ SRL Control Pro 2.0")
st.sidebar.caption("BAGLI & TROPEA • Versione Completa")

menu = st.sidebar.radio("Navigazione", [
    "📊 Cruscotto & Bilancio",
    "📈 Grafici & Andamento",
    "📝 Prima Nota & Fatture",
    "⏳ Da Incassare / Pagare",
    "👥 Dipendenti & Stipendi",
    "🧾 Liquidazione IVA",
    "📅 Acconti & Scadenze F24",
    "📥 Importa / Esporta Excel"
])

st.sidebar.divider()
anno_filtro = st.sidebar.selectbox("Anno di riferimento", options=("Tutti", "2025", "2026", "2027"), index=2)

mesi_map = {
    "Tutto l'anno": None,
    "1° Semestre (Gen-Giu)": ["01", "02", "03", "04", "05", "06"],
    "2° Semestre (Lug-Dic)": ["07", "08", "09", "10", "11", "12"],
    "Gennaio": ["01"], "Febbraio": ["02"], "Marzo": ["03"],
    "Aprile": ["04"], "Maggio": ["05"], "Giugno": ["06"],
    "Luglio": ["07"], "Agosto": ["08"], "Settembre": ["09"],
    "Ottobre": ["10"], "Novembre": ["11"], "Dicembre": ["12"]
}
periodo_scelto = st.sidebar.selectbox("Mese / Periodo", options=list(mesi_map.keys()))

df_fatture = carica_tabella("fatture")
df_stipendi = carica_tabella("stipendi")

# Filtro Anno
if anno_filtro != "Tutti" and not df_fatture.empty:
    df_fatture = df_fatture[df_fatture['data'].astype(str).str.startswith(anno_filtro)]
if anno_filtro != "Tutti" and not df_stipendi.empty:
    df_stipendi = df_stipendi[df_stipendi['data'].astype(str).str.startswith(anno_filtro)]

# Filtro Mese / Semestre
mesi_target = mesi_map[periodo_scelto]
if mesi_target is not None:
    if not df_fatture.empty:
        df_fatture = df_fatture[df_fatture['data'].astype(str).str.slice(5, 7).isin(mesi_target)]
    if not df_stipendi.empty:
        df_stipendi = df_stipendi[df_stipendi['data'].astype(str).str.slice(5, 7).isin(mesi_target)]

if menu == "📊 Cruscotto & Bilancio":
    st.title(f"📊 Cruscotto SRL • {periodo_scelto} ({anno_filtro})")
    incassi = df_fatture[df_fatture['tipo'] == 'FATTURA EMESSA'] if not df_fatture.empty else pd.DataFrame()
    costi = df_fatture[df_fatture['tipo'].isin(['FATTURA ACQUISTO', 'RICEVUTA'])] if not df_fatture.empty else pd.DataFrame()
    
    tot_lordi = (incassi['imponibile'] * (1 + incassi['iva_perc']/100)).sum() if not incassi.empty else 0.0
    tot_stipendi = (df_stipendi['netto'] + df_stipendi['contributi_f24']).sum() if not df_stipendi.empty else 0.0
    utile_netto = (incassi['imponibile'].sum() if not incassi.empty else 0.0) - (costi['imponibile'].sum() if not costi.empty else 0.0) - tot_stipendi
    
    iva_deb = (incassi['imponibile'] * (incassi['iva_perc']/100)).sum() if not incassi.empty else 0.0
    iva_cred = (costi['imponibile'] * (costi['iva_perc']/100)).sum() if not costi.empty else 0.0
    pos_iva = iva_cred - iva_deb
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Incassi Lordi SRL", f"€ {tot_lordi:,.2f}")
    c2.metric("📈 Utile Netto SRL", f"€ {utile_netto:,.2f}")
    c3.metric("🧾 Posizione IVA", f"€ {abs(pos_iva):,.2f}", "A Credito" if pos_iva >= 0 else "A Debito")
    c4.metric("👥 Costo Personale", f"€ {tot_stipendi:,.2f}")

    st.divider()
    col_b, col_t = st.columns(2)
    for socio, col in [("BAGLI", col_b), ("TROPEA", col_t)]:
        with col:
            st.subheader(f"👤 Rendiconto: {socio}")
            inc_s = incassi[incassi['socio'] == socio] if not incassi.empty else pd.DataFrame()
            cos_s = costi[costi['socio'] == socio] if not costi.empty else pd.DataFrame()
            sti_s = df_stipendi[df_stipendi['socio'] == socio] if not df_stipendi.empty else pd.DataFrame()
            
            lordo_s = (inc_s['imponibile'] * (1 + inc_s['iva_perc']/100)).sum() if not inc_s.empty else 0.0
            utile_s = (inc_s['imponibile'].sum() if not inc_s.empty else 0.0) - (cos_s['imponibile'].sum() if not cos_s.empty else 0.0) - ((sti_s['netto'] + sti_s['contributi_f24']).sum() if not sti_s.empty else 0.0)
            
            m1, m2 = st.columns(2)
            m1.metric("Incassi Lordi", f"€ {lordo_s:,.2f}")
            m2.metric("Utile Netto", f"€ {utile_s:,.2f}")

elif menu == "📈 Grafici & Andamento":
    mostra_grafici(df_fatture, df_stipendi)

elif menu == "📝 Prima Nota & Fatture":
    mostra_prima_nota()

elif menu == "⏳ Da Incassare / Pagare":
    mostra_scadenzario()

elif menu == "👥 Dipendenti & Stipendi":
    mostra_stipendi()

elif menu == "🧾 Liquidazione IVA":
    mostra_iva(df_fatture)

elif menu == "📅 Acconti & Scadenze F24":
    mostra_f24()

elif menu == "📥 Importa / Esporta Excel":
    st.title("📥 Backup & Migrazione Dati")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        carica_tabella("fatture").to_excel(writer, sheet_name="Fatture", index=False)
        carica_tabella("stipendi").to_excel(writer, sheet_name="Stipendi", index=False)
        carica_tabella("f24").to_excel(writer, sheet_name="F24", index=False)
    
    st.download_button("📤 Scarica Backup Excel", data=buffer.getvalue(), file_name=f"Backup_SRL_{date.today()}.xlsx")
    
    st.divider()
    uploaded = st.file_uploader("Importa fatture da Excel", type=["xlsx"])
    if uploaded and st.button("📥 Carica nel Database"):
        df_imp = pd.read_excel(uploaded)
        colonne = ['data', 'tipo', 'num', 'anagrafica', 'imponibile', 'iva_perc', 'socio', 'ritenuta_perc', 'costo_categoria']
        for col in colonne:
            if col not in df_imp.columns:
                df_imp[col] = str(date.today()) if col == 'data' else (0 if 'perc' in col or col == 'imponibile' else "GENERALE")
        conn = get_connection()
        df_imp[colonne].to_sql("fatture", conn, if_exists="append", index=False)
        conn.close()
        st.success(f"✅ Importate {len(df_imp)} righe!")


