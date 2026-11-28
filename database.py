import re
import time
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


@st.cache_resource
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )


def init_db():
    if st.session_state.get("db_inizializzato"):
        return

    for tentativo in range(3):
        try:
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
                    pagata INTEGER DEFAULT 1,
                    cantiere TEXT DEFAULT 'GENERALE'
                )'''))
                conn.execute(text('''ALTER TABLE fatture_v2 ADD COLUMN IF NOT EXISTS cantiere TEXT DEFAULT 'GENERALE' '''))

                conn.execute(text('''CREATE TABLE IF NOT EXISTS stipendi_v2 (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    dipendente TEXT,
                    mese TEXT,
                    netto DOUBLE PRECISION,
                    contributi_f24 DOUBLE PRECISION,
                    cassa_edile DOUBLE PRECISION DEFAULT 0,
                    socio TEXT,
                    cantiere TEXT DEFAULT 'GENERALE'
                )'''))
                conn.execute(text('''ALTER TABLE stipendi_v2 ADD COLUMN IF NOT EXISTS cassa_edile DOUBLE PRECISION DEFAULT 0'''))
                conn.execute(text('''ALTER TABLE stipendi_v2 ADD COLUMN IF NOT EXISTS cantiere TEXT DEFAULT 'GENERALE' '''))

                conn.execute(text('''CREATE TABLE IF NOT EXISTS f24_v2 (
                    id SERIAL PRIMARY KEY,
                    scadenza TEXT,
                    descrizione TEXT,
                    importo DOUBLE PRECISION,
                    pagato INTEGER DEFAULT 0
                )'''))

                conn.execute(text('''CREATE TABLE IF NOT EXISTS scadenze_edili (
                    id SERIAL PRIMARY KEY,
                    scadenza TEXT,
                    categoria TEXT,
                    mezzo_riferimento TEXT,
                    descrizione TEXT,
                    importo DOUBLE PRECISION DEFAULT 0,
                    socio TEXT,
                    rinnovata INTEGER DEFAULT 0
                )'''))

                conn.execute(text('''CREATE TABLE IF NOT EXISTS preventivi_cloud (
                    id SERIAL PRIMARY KEY,
                    num TEXT,
                    data_doc TEXT,
                    cliente TEXT,
                    indirizzo TEXT,
                    telefono TEXT,
                    descrizione TEXT,
                    importo DOUBLE PRECISION,
                    socio TEXT,
                    stato TEXT DEFAULT 'In Attesa'
                )'''))

                conn.execute(text('''CREATE TABLE IF NOT EXISTS listino_cloud (
                    id SERIAL PRIMARY KEY,
                    codice TEXT UNIQUE,
                    descrizione TEXT,
                    prezzo_unitario DOUBLE PRECISION,
                    unita_misura TEXT
                )'''))

                res = conn.execute(text("SELECT COUNT(*) FROM listino_cloud")).scalar()
                if res == 0:
                    lavori_default = (
                        {"c": "CART01", "d": "FORNITURA E POSA DI CONTROSOFFITTO IN CARTONGESSO COSTITUITO DA STRUTTURA DI SOSTEGNO E LASTRA STANDARD", "p": 35.00, "u": "mq"},
                        {"c": "CART02", "d": "FORNITURA E POSA CONTROPARETE CON STRUTTURA DI SOSTEGNO IN LAMIERA ZINCATA E LASTRA STANDARD", "p": 40.00, "u": "mq"},
                        {"c": "TINT01", "d": "POSA DI RASATURA A PARO + TINTEGGIATURA INTERNA LAVABILE", "p": 18.00, "u": "mq"},
                        {"c": "VELE01", "d": "FORNITURA E POSA IN OPERA DI VELETTA PERIMETRALE PER INCASSO LED", "p": 25.00, "u": "ml"}
                    )
                    for item in lavori_default:
                        conn.execute(
                            text("INSERT INTO listino_cloud (codice, descrizione, prezzo_unitario, unita_misura) VALUES (:c, :d, :p, :u)"),
                            item
                        )
            st.session_state["db_inizializzato"] = True
            return
        except OperationalError:
            st.cache_resource.clear()
            if tentativo == 2:
                raise
            time.sleep(1.5)


def _mappa_tabella(nome):
    mappa = {
        "fatture": "fatture_v2",
        "stipendi": "stipendi_v2",
        "f24": "f24_v2",
        "preventivi": "preventivi_cloud",
        "listino": "listino_cloud"
    }
    return mappa.get(nome, nome)


def esegui_query(query, params=None):
    # Sostituisce in modo sicuro i vecchi nomi delle tabelle ovunque nella query
    mappa_tabelle = {
        "fatture": "fatture_v2",
        "stipendi": "stipendi_v2",
        "f24": "f24_v2",
        "preventivi": "preventivi_cloud",
        "listino": "listino_cloud"
    }
    for vecchia, nuova in mappa_tabelle.items():
        query = re.sub(rf"\b{vecchia}\b", nuova, query)

    # Converte automaticamente vecchie query SQLite con '?' e tuple/liste in dizionari per SQLAlchemy 2.0
    if isinstance(params, (tuple, list)):
        parti = query.split("?")
        if len(parti) - 1 == len(params):
            nuova_query = parti[0]
            nuovi_params = {}
            for i, val in enumerate(params):
                chiave = f"p_{i}"
                # Converte eventuali numeri NumPy (es. np.int64) in tipi standard Python
                if hasattr(val, "item"):
                    val = val.item()
                nuova_query += f":{chiave}" + parti[i + 1]
                nuovi_params[chiave] = val
            query = nuova_query
            params = nuovi_params

    for tentativo in range(2):
        try:
            engine = get_engine()
            with engine.begin() as conn:
                conn.execute(text(query), params or {})
            return
        except OperationalError:
            st.cache_resource.clear()
            if tentativo == 1:
                raise
            time.sleep(1)


def carica_tabella(nome_tabella):
    tabella_reale = _mappa_tabella(nome_tabella)
    for tentativo in range(2):
        try:
            engine = get_engine()
            return pd.read_sql_query(f"SELECT * FROM {tabella_reale}", engine)
        except OperationalError:
            st.cache_resource.clear()
            if tentativo == 1:
                raise
            time.sleep(1)


def salva_tabella(df, nome_tabella):
    tabella_reale = _mappa_tabella(nome_tabella)
    for tentativo in range(2):
        try:
            engine = get_engine()
            with engine.begin() as conn:
                conn.execute(text(f"DELETE FROM {tabella_reale}"))
                df_to_save = df.drop(columns=["id"], errors="ignore")
                if not df_to_save.empty:
                    df_to_save.to_sql(tabella_reale, conn, if_exists="append", index=False)
            return
        except OperationalError:
            st.cache_resource.clear()
            if tentativo == 1:
                raise
            time.sleep(1)


