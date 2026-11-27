import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

@st.cache_resource
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(db_url, pool_pre_ping=True)

def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS fatture_v2 (
            id SERIAL PRIMARY KEY,
            data TEXT,
            tipo TEXT,
            num TEXT,
            anagrafica TEXT,
            imponibile DOUBLE PRECISION,
            iva_perc DOUBLE PRECISION,
            socio TEXT,
            ritenuta_perc DOUBLE PRECISION,
            costo_categoria TEXT,
            pagata INTEGER DEFAULT 1
        )'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS stipendi_v2 (
            id SERIAL PRIMARY KEY,
            data TEXT,
            dipendente TEXT,
            mese TEXT,
            netto DOUBLE PRECISION,
            contributi_f24 DOUBLE PRECISION,
            cassa_edile DOUBLE PRECISION DEFAULT 0,
            socio TEXT
        )'''))
        # Aggiunge automaticamente la colonna cassa_edile se la tabella esiste già
        conn.execute(text('''ALTER TABLE stipendi_v2 ADD COLUMN IF NOT EXISTS cassa_edile DOUBLE PRECISION DEFAULT 0'''))
        
        conn.execute(text('''CREATE TABLE IF NOT EXISTS f24_v2 (
            id SERIAL PRIMARY KEY,
            scadenza TEXT,
            descrizione TEXT,
            importo DOUBLE PRECISION,
            pagato INTEGER DEFAULT 0
        )'''))

def _mappa_tabella(nome):
    mappa = {"fatture": "fatture_v2", "stipendi": "stipendi_v2", "f24": "f24_v2"}
    return mappa.get(nome, nome)

def esegui_query(query, params=None):
    for vecchia, nuova in [("fatture", "fatture_v2"), ("stipendi", "stipendi_v2"), ("f24", "f24_v2")]:
        query = query.replace(f" {vecchia} ", f" {nuova} ").replace(f" {vecchia}\n", f" {nuova}\n")
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(query), params or {})

def carica_tabella(nome_tabella):
    engine = get_engine()
    tabella_reale = _mappa_tabella(nome_tabella)
    return pd.read_sql_query(f"SELECT * FROM {tabella_reale}", engine)

def salva_tabella(df, nome_tabella):
    engine = get_engine()
    tabella_reale = _mappa_tabella(nome_tabella)
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {tabella_reale}"))
        df_to_save = df.drop(columns=["id"], errors="ignore")
        if not df_to_save.empty:
            df_to_save.to_sql(tabella_reale, conn, if_exists="append", index=False)


