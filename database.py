import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

@st.cache_resource
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url, pool_pre_ping=True)

def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS fatture (
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
        conn.execute(text('''CREATE TABLE IF NOT EXISTS stipendi (
            id SERIAL PRIMARY KEY,
            data TEXT,
            dipendente TEXT,
            mese TEXT,
            netto DOUBLE PRECISION,
            contributi_f24 DOUBLE PRECISION,
            socio TEXT
        )'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS f24 (
            id SERIAL PRIMARY KEY,
            scadenza TEXT,
            descrizione TEXT,
            importo DOUBLE PRECISION,
            pagato INTEGER DEFAULT 0
        )'''))

def esegui_query(query, params=None):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(query), params or {})

def carica_tabella(nome_tabella):
    engine = get_engine()
    return pd.read_sql_query(f"SELECT * FROM {nome_tabella}", engine)

def salva_tabella(df, nome_tabella):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {nome_tabella}"))
        df_to_save = df.drop(columns=["id"], errors="ignore")
        if not df_to_save.empty:
            df_to_save.to_sql(nome_tabella, conn, if_exists="append", index=False)
