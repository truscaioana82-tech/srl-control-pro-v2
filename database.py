import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect("gestionale_srl.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS fatture (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        tipo TEXT,
        num TEXT,
        anagrafica TEXT,
        imponibile REAL,
        iva_perc REAL,
        socio TEXT,
        ritenuta_perc REAL,
        costo_categoria TEXT,
        pagata INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS stipendi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        dipendente TEXT,
        mese TEXT,
        netto REAL,
        contributi_f24 REAL,
        socio TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS f24 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scadenza TEXT,
        descrizione TEXT,
        importo REAL,
        pagato INTEGER DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()

def carica_tabella(nome_tabella):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {nome_tabella}", conn)
    conn.close()
    return df

def salva_tabella(df, nome_tabella):
    conn = get_connection()
    df.to_sql(nome_tabella, conn, if_exists="replace", index=False)
    conn.close()
