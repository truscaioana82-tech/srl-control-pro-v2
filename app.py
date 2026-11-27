def calcola_scheda(df_f, df_s):
    if df_f.empty and df_s.empty:
        return {"lordi": 0.0, "utile": 0.0, "fornitori": 0.0, "dipendenti": 0.0, "cassa_edile": 0.0, "nc": 0.0, "iva_deb": 0.0, "iva_cred": 0.0, "liq_iva": 0.0}
    
    t_up = df_f['tipo'].astype(str).str.upper() if not df_f.empty else pd.Series(dtype=str)
    cat_up = df_f['costo_categoria'].astype(str).str.upper() if not df_f.empty else pd.Series(dtype=str)
    
    is_nc = t_up.str.contains('CREDITO|NC', na=False)
    is_omaggio = t_up.str.contains('OMAGG', na=False)
    is_dip_vecchio = t_up.str.contains('STIPEND|DIPEND|BUSTA|PERSONALE|CASSA EDILE', na=False) | cat_up.str.contains('STIPEND|DIPEND|PERSONALE|CASSA EDILE', na=False)
    is_emessa = t_up.str.contains('EMESS|VENDIT|ENTRAT', na=False) & ~is_nc & ~is_omaggio
    is_fornitore = ~is_emessa & ~is_nc & ~is_omaggio & ~is_dip_vecchio

    f_em = df_f[is_emessa] if not df_f.empty else pd.DataFrame()
    f_nc = df_f[is_nc] if not df_f.empty else pd.DataFrame()
    f_forn = df_f[is_fornitore] if not df_f.empty else pd.DataFrame()
    f_dip_v = df_f[is_dip_vecchio] if not df_f.empty else pd.DataFrame()

    incassi_lordi = (f_em['imponibile'] * (1 + f_em['iva_perc']/100)).sum() if not f_em.empty else 0.0
    note_credito = (f_nc['imponibile'] * (1 + f_nc['iva_perc']/100)).sum() if not f_nc.empty else 0.0
    spese_fornitori = f_forn['imponibile'].sum() if not f_forn.empty else 0.0
    
    ce_nuova = df_s['cassa_edile'].fillna(0.0).sum() if (not df_s.empty and 'cassa_edile' in df_s.columns) else 0.0
    dip_vecchi = f_dip_v['imponibile'].sum() if not f_dip_v.empty else 0.0
    dip_nuovi = (df_s['netto'] + df_s['contributi_f24']).sum() if not df_s.empty else 0.0
    tot_dipendenti = dip_vecchi + dip_nuovi + ce_nuova

    iva_deb = ((f_em['imponibile'] * (f_em['iva_perc']/100)).sum() if not f_em.empty else 0.0) - ((f_nc['imponibile'] * (f_nc['iva_perc']/100)).sum() if not f_nc.empty else 0.0)
    iva_cred = (f_forn['imponibile'] * (f_forn['iva_perc']/100)).sum() if not f_forn.empty else 0.0
    liq_iva = iva_cred - iva_deb

    ricavi_netti = (f_em['imponibile'].sum() if not f_em.empty else 0.0) - (f_nc['imponibile'].sum() if not f_nc.empty else 0.0)
    utile_netto = ricavi_netti - spese_fornitori - tot_dipendenti

    return {
        "lordi": incassi_lordi, "utile": utile_netto, "fornitori": spese_fornitori,
        "dipendenti": tot_dipendenti, "cassa_edile": ce_nuova, "nc": note_credito, "iva_deb": iva_deb,
        "iva_cred": iva_cred, "liq_iva": liq_iva
    }
def calcola_scheda(df_f, df_s):
    if df_f.empty and df_s.empty:
        return {"lordi": 0.0, "utile": 0.0, "fornitori": 0.0, "dipendenti": 0.0, "cassa_edile": 0.0, "nc": 0.0, "iva_deb": 0.0, "iva_cred": 0.0, "liq_iva": 0.0}
    
    t_up = df_f['tipo'].astype(str).str.upper() if not df_f.empty else pd.Series(dtype=str)
    cat_up = df_f['costo_categoria'].astype(str).str.upper() if not df_f.empty else pd.Series(dtype=str)
    
    is_nc = t_up.str.contains('CREDITO|NC', na=False)
    is_omaggio = t_up.str.contains('OMAGG', na=False)
    is_dip_vecchio = t_up.str.contains('STIPEND|DIPEND|BUSTA|PERSONALE|CASSA EDILE', na=False) | cat_up.str.contains('STIPEND|DIPEND|PERSONALE|CASSA EDILE', na=False)
    is_emessa = t_up.str.contains('EMESS|VENDIT|ENTRAT', na=False) & ~is_nc & ~is_omaggio
    is_fornitore = ~is_emessa & ~is_nc & ~is_omaggio & ~is_dip_vecchio

    f_em = df_f[is_emessa] if not df_f.empty else pd.DataFrame()
    f_nc = df_f[is_nc] if not df_f.empty else pd.DataFrame()
    f_forn = df_f[is_fornitore] if not df_f.empty else pd.DataFrame()
    f_dip_v = df_f[is_dip_vecchio] if not df_f.empty else pd.DataFrame()

    incassi_lordi = (f_em['imponibile'] * (1 + f_em['iva_perc']/100)).sum() if not f_em.empty else 0.0
    note_credito = (f_nc['imponibile'] * (1 + f_nc['iva_perc']/100)).sum() if not f_nc.empty else 0.0
    spese_fornitori = f_forn['imponibile'].sum() if not f_forn.empty else 0.0
    
    ce_nuova = df_s['cassa_edile'].fillna(0.0).sum() if (not df_s.empty and 'cassa_edile' in df_s.columns) else 0.0
    dip_vecchi = f_dip_v['imponibile'].sum() if not f_dip_v.empty else 0.0
    dip_nuovi = (df_s['netto'] + df_s['contributi_f24']).sum() if not df_s.empty else 0.0
    tot_dipendenti = dip_vecchi + dip_nuovi + ce_nuova

    iva_deb = ((f_em['imponibile'] * (f_em['iva_perc']/100)).sum() if not f_em.empty else 0.0) - ((f_nc['imponibile'] * (f_nc['iva_perc']/100)).sum() if not f_nc.empty else 0.0)
    iva_cred = (f_forn['imponibile'] * (f_forn['iva_perc']/100)).sum() if not f_forn.empty else 0.0
    liq_iva = iva_cred - iva_deb

    ricavi_netti = (f_em['imponibile'].sum() if not f_em.empty else 0.0) - (f_nc['imponibile'].sum() if not f_nc.empty else 0.0)
    utile_netto = ricavi_netti - spese_fornitori - tot_dipendenti

    return {
        "lordi": incassi_lordi, "utile": utile_netto, "fornitori": spese_fornitori,
        "dipendenti": tot_dipendenti, "cassa_edile": ce_nuova, "nc": note_credito, "iva_deb": iva_deb,
        "iva_cred": iva_cred, "liq_iva": liq_iva
    }
if menu == "📊 Cruscotto & Bilancio":
    st.subheader(f"📊 Cruscotto SRL • {periodo_scelto} ({anno_filtro})")
    
    ripartisci_comune = st.toggle("⚖️ Ripartisci movimenti 'COMUNE' al 50% / 50% tra BAGLI e TROPEA", value=False)
    
    tot = calcola_scheda(df_fatture, df_stipendi)
    
    df_f_b = df_fatture[df_fatture['socio'].astype(str).str.upper() == "BAGLI"] if not df_fatture.empty else pd.DataFrame()
    df_s_b = df_stipendi[df_stipendi['socio'].astype(str).str.upper() == "BAGLI"] if not df_stipendi.empty else pd.DataFrame()
    d_bagli = calcola_scheda(df_f_b, df_s_b)

    df_f_t = df_fatture[df_fatture['socio'].astype(str).str.upper() == "TROPEA"] if not df_fatture.empty else pd.DataFrame()
    df_s_t = df_stipendi[df_stipendi['socio'].astype(str).str.upper() == "TROPEA"] if not df_stipendi.empty else pd.DataFrame()
    d_tropea = calcola_scheda(df_f_t, df_s_t)

    if ripartisci_comune:
        df_f_c = df_fatture[df_fatture['socio'].astype(str).str.upper() == "COMUNE"] if not df_fatture.empty else pd.DataFrame()
        df_s_c = df_stipendi[df_stipendi['socio'].astype(str).str.upper() == "COMUNE"] if not df_stipendi.empty else pd.DataFrame()
        d_comune = calcola_scheda(df_f_c, df_s_c)
        for k in d_bagli:
            d_bagli[k] += d_comune[k] / 2.0
            d_tropea[k] += d_comune[k] / 2.0

    b_pdf1, b_pdf2, b_pdf3 = st.columns(3)
    with b_pdf1:
        pdf_bytes = genera_pdf_bilancio(periodo_scelto, anno_filtro, tot, d_bagli, d_tropea)
        st.download_button(
            label="📄 PDF Bilancio Generale SRL",
            data=pdf_bytes,
            file_name=f"Bilancio_SRL_{anno_filtro}_{date.today()}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with b_pdf2:
        pdf_bagli = genera_pdf_socio("BAGLI", periodo_scelto, anno_filtro, d_bagli)
        st.download_button(
            label="👤 PDF Rendiconto BAGLI",
            data=pdf_bagli,
            file_name=f"Rendiconto_BAGLI_{anno_filtro}_{date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with b_pdf3:
        pdf_tropea = genera_pdf_socio("TROPEA", periodo_scelto, anno_filtro, d_tropea)
        st.download_button(
            label="👤 PDF Rendiconto TROPEA",
            data=pdf_tropea,
            file_name=f"Rendiconto_TROPEA_{anno_filtro}_{date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Incassi Lordi SRL", f"€ {tot['lordi']:,.2f}")
    c2.metric("📈 Utile Netto SRL", f"€ {tot['utile']:,.2f}")
    c3.metric("🧾 Liquidazione IVA SRL", f"€ {abs(tot['liq_iva']):,.2f}", "A Credito" if tot['liq_iva'] >= 0 else "A Debito")

    st.divider()
    col_b, col_t = st.columns(2)
    for socio, d, col in [("BAGLI", d_bagli, col_b), ("TROPEA", d_tropea, col_t)]:
        with col:
            st.subheader(f"👤 Rendiconto: {socio}")
            m1, m2 = st.columns(2)
            m1.metric("💰 Incassi Lordi", f"€ {d['lordi']:,.2f}")
            m2.metric("📈 Utile Netto", f"€ {d['utile']:,.2f}")
            
            st.info(
                f"**Spese Fornitori:** € {d['fornitori']:,.2f} | **Dipendenti (incl. Cassa Edile):** € {d['dipendenti']:,.2f}\n\n"
                f"**🏗️ Cassa Edile Registrata:** € {d['cassa_edile']:,.2f} | **Note di Credito:** € {d['nc']:,.2f}\n\n"
                f"**IVA Debito:** € {d['iva_deb']:,.2f} | **IVA Credito:** € {d['iva_cred']:,.2f}\n\n"
                f"**Liquidazione IVA ({'A CREDITO' if d['liq_iva'] >= 0 else 'A DEBITO'}):** € {abs(d['liq_iva']):,.2f}\n\n"
                f"💵 **LIQUIDITÀ DI CASSA STIMATA:** € {d['utile']:,.2f}"
            )

elif menu == "🏗️ Analisi Cantieri":
    mostra_cantieri(df_fatture, df_stipendi)

elif menu == "📋 Preventivi":
    mostra_preventivi()

elif menu == "📑 Estratto Conto Clienti/Forn.":
    mostra_estratto_conto(df_fatture)

elif menu == "📈 Grafici & Andamento":
    mostra_grafici(df_fatture, df_stipendi)

elif menu == "📝 Prima Nota & Fatture":
    mostra_prima_nota()

elif menu == "⏳ Da Incassare / Pagare":
    mostra_scadenzario()

elif menu == "🚛 Mezzi, Polizze & DURC":
    mostra_scadenze_mezzi()

elif menu == "👥 Dipendenti & Stipendi":
    mostra_stipendi()

elif menu == "📇 Rubrica Clienti & Dipendenti":
    mostra_rubrica()

elif menu == "🧾 Liquidazione IVA":
    mostra_iva(df_fatture)

elif menu == "📅 Acconti & Scadenze F24":
    mostra_f24()

elif menu == "📥 Importa / Esporta Excel":
    mostra_import_export()

