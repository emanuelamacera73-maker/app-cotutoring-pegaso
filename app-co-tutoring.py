import streamlit as st
import pandas as pd
import numpy as np
import io

# Disable automatic Google Translate to prevent removeChild React DOM errors
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ==========================================
# CONFIGURAZIONE PAGINA E STILE
# ==========================================
st.set_page_config(
    page_title="Pegaso Co-Tutoring Matching Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GESTIONE STATO INIZIALE (DEMO DATASET)
# ==========================================
if 'tutors_df' not in st.session_state:
    st.session_state['tutors_df'] = pd.DataFrame([
        {'nome': 'Dr. Iadicicco', 'sede': 'Napoli', 'agency': 82, 'communion': 88, 'coscienziosita': 90, 'apertura': 85, 'skills': 'Bilancio, E-Portfolio', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Macera', 'sede': 'Napoli', 'agency': 55, 'communion': 85, 'coscienziosita': 88, 'apertura': 80, 'skills': 'Diario, Inclusione', 'belbin_role': 'Sociale', 'disponibile': True},
        {'nome': 'Dr. Messina', 'sede': 'Napoli', 'agency': 60, 'communion': 92, 'coscienziosita': 85, 'apertura': 90, 'skills': 'E-Portfolio, Metodologie', 'belbin_role': 'Valutazione', 'disponibile': True},
        {'nome': 'Dr. Salis', 'sede': 'Napoli', 'agency': 78, 'communion': 80, 'coscienziosita': 92, 'apertura': 75, 'skills': 'Regia, Diario', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Scialpi', 'sede': 'Napoli', 'agency': 50, 'communion': 90, 'coscienziosita': 86, 'apertura': 88, 'skills': 'Bilancio, Metodologie', 'belbin_role': 'Sociale', 'disponibile': True},
        {'nome': 'Dr. Scipilliti', 'sede': 'Roma', 'agency': 80, 'communion': 84, 'coscienziosita': 89, 'apertura': 82, 'skills': 'Inclusione, E-Portfolio', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Rossi', 'sede': 'Roma', 'agency': 52, 'communion': 86, 'coscienziosita': 87, 'apertura': 85, 'skills': 'Bilancio, Diario', 'belbin_role': 'Sociale', 'disponibile': True},
    ])

if 'classrooms_df' not in st.session_state:
    st.session_state['classrooms_df'] = pd.DataFrame([
        {'nome_aula': 'Aula Magna A1', 'sede': 'Napoli', 'n_corsisti': 85, 'tipo': 'Triade'},
        {'nome_aula': 'Aula Laboratorio B2', 'sede': 'Napoli', 'n_corsisti': 48, 'tipo': 'Diade'},
        {'nome_aula': 'Aula Seminariale R1', 'sede': 'Roma', 'n_corsisti': 52, 'tipo': 'Diade'},
    ])

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("Co-Tutoring Pegaso")
st.sidebar.caption("Modello di Abbinamento Regionale (Parte Quinta)")

menu_choice = st.sidebar.radio(
    "Navigazione Moduli:",
    [
        "⚡ Engine di Matching Regionale",
        "📝 Profilazione Tutor (QP-CoT)",
        "📊 Caricamento Batch (Excel/CSV)",
        "📜 Patto di Corresponsabilità",
        "📖 Quadro Scientifico (Parte Quinta)"
    ]
)

st.sidebar.divider()
st.sidebar.info("📌 **Ateneo Pegaso** - Percorsi Abilitanti D.P.C.M. 4 agosto 2023")

# ==========================================
# ALGORITMO DI MATCHING (ENGINE)
# ==========================================
def compute_diad_score(t1, t2, w1=0.35, w2=0.30, w3=0.35):
    if t1['sede'] != t2['sede'] or not t1['disponibile'] or not t2['disponibile']:
        return -1e6
    
    s1 = set([s.strip() for s in str(t1['skills']).split(',')])
    s2 = set([s.strip() for s in str(t2['skills']).split(',')])
    all_skills = s1.union(s2)
    skills_coverage = min(len(all_skills) / 4.0, 1.0)
    
    comm_fit = 1.0 - (abs(t1['communion'] - t2['communion']) / 100.0)
    cosc_fit = 1.0 - (abs(t1['coscienziosita'] - t2['coscienziosita']) / 100.0)
    comm_cosc_score = (comm_fit + cosc_fit) / 2.0
    
    a1, a2 = t1['agency'], t2['agency']
    if a1 > 75 and a2 > 75:
        agency_score = 0.2
    elif (a1 >= 60 and a2 < 60) or (a2 >= 60 and a1 < 60):
        agency_score = 1.0
    else:
        agency_score = 0.7
        
    total_score = (w1 * skills_coverage) + (w2 * comm_cosc_score) + (w3 * agency_score)
    return round(total_score * 100, 2)

def compute_triad_score(t1, t2, t3, w1=0.35, w2=0.30, w3=0.35):
    d12 = compute_diad_score(t1, t2, w1, w2, w3)
    d23 = compute_diad_score(t2, t3, w1, w2, w3)
    d13 = compute_diad_score(t1, t3, w1, w2, w3)
    
    if min(d12, d23, d13) < 0:
        return -1e6
        
    avg_diad = (d12 + d23 + d13) / 3.0
    roles = {t1['belbin_role'], t2['belbin_role'], t3['belbin_role']}
    belbin_bonus = 15.0 if len(roles) == 3 else (5.0 if len(roles) == 2 else 0.0)
    return round(avg_diad + belbin_bonus, 2)

# ==========================================
# MODULO 1: ENGINE DI MATCHING REGIONALE
# ==========================================
if menu_choice == "⚡ Engine di Matching Regionale":
    st.header("Engine di Matching e Ottimizzazione Regionale")
    st.write("Abbinamento automatico in **Diadi** e **Triadi** basato su complementarità di Agency, omofilia di Communion e ruoli di Belbin.")
    
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    
    with col_ctrl1:
        st.subheader("Parametri e Filtri")
        selected_sede = st.selectbox("Filtra Sede Regionale:", ["Tutte"] + list(st.session_state['tutors_df']['sede'].unique()))
        
        st.write("**Pesi Algoritmo Optimization:**")
        w_agency = st.slider("Peso Complementarità Agency", 0.0, 1.0, 0.35, 0.05)
        w_communion = st.slider("Peso Omofilia Communion/Coscienziosità", 0.0, 1.0, 0.30, 0.05)
        w_skills = st.slider("Peso Copertura Skills", 0.0, 1.0, 0.35, 0.05)
        
        run_btn = st.button("🚀 Calcola Abbinamenti Ottimali", type="primary", use_container_width=True)

    with col_ctrl2:
        st.subheader("Visualizzazione Dati di Ingresso")
        st.caption("Co-Tutor Disponibili:")
        st.dataframe(st.session_state['tutors_df'], use_container_width=True, height=180)
        
        st.caption("Aule Regionali da Coprire:")
        st.dataframe(st.session_state['classrooms_df'], use_container_width=True, height=140)

    if run_btn:
        st.divider()
        st.subheader("📋 Esito Abbinamenti Ottimali Generati")
        
        tutors = st.session_state['tutors_df']
        classrooms = st.session_state['classrooms_df']
        
        if selected_sede != "Tutte":
            tutors = tutors[tutors['sede'] == selected_sede]
            classrooms = classrooms[classrooms['sede'] == selected_sede]
            
        avail_tutors = tutors.copy()
        results = []

        # 1. Matching Triadi (>70 corsisti)
        triad_rooms = classrooms[classrooms['tipo'] == 'Triade']
        for _, room in triad_rooms.iterrows():
            best_triad, best_score = None, -1
            t_idx = avail_tutors.index.tolist()
            
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    for k in range(j + 1, len(t_idx)):
                        t1 = avail_tutors.loc[t_idx[i]]
                        t2 = avail_tutors.loc[t_idx[j]]
                        t3 = avail_tutors.loc[t_idx[k]]
                        
                        score = compute_triad_score(t1, t2, t3, w_skills, w_communion, w_agency)
                        if score > best_score:
                            best_score = score
                            best_triad = (t1, t2, t3, t_idx[i], t_idx[j], t_idx[k])
                            
            if best_triad:
                t1, t2, t3, i1, i2, i3 = best_triad
                results.append({
                    'Aula': room['nome_aula'],
                    'Sede': room['sede'],
                    'Tipo': 'Triade',
                    'Corsisti': room['n_corsisti'],
                    'Co-Tutor 1 (Azione)': f"{t1['nome']} ({t1['belbin_role']})",
                    'Co-Tutor 2 (Sociale)': f"{t2['nome']} ({t2['belbin_role']})",
                    'Co-Tutor 3 (Valutazione)': f"{t3['nome']} ({t3['belbin_role']})",
                    'Matching Score': best_score
                })
                avail_tutors = avail_tutors.drop([i1, i2, i3])

        # 2. Matching Diadi (40-70 corsisti)
        diad_rooms = classrooms[classrooms['tipo'] == 'Diade']
        for _, room in diad_rooms.iterrows():
            best_diad, best_score = None, -1
            t_idx = avail_tutors.index.tolist()
            
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    t1 = avail_tutors.loc[t_idx[i]]
                    t2 = avail_tutors.loc[t_idx[j]]
                    
                    score = compute_diad_score(t1, t2, w_skills, w_communion, w_agency)
                    if score > best_score:
                        best_score = score
                        best_diad = (t1, t2, t_idx[i], t_idx[j])
                        
            if best_diad:
                t1, t2, i1, i2 = best_diad
                results.append({
                    'Aula': room['nome_aula'],
                    'Sede': room['sede'],
                    'Tipo': 'Diade',
                    'Corsisti': room['n_corsisti'],
                    'Co-Tutor 1 (Azione)': f"{t1['nome']} (Agency:{t1['agency']})",
                    'Co-Tutor 2 (Sociale)': f"{t2['nome']} (Agency:{t2['agency']})",
                    'Co-Tutor 3 (Valutazione)': "— (Non previsto)",
                    'Matching Score': best_score
                })
                avail_tutors = avail_tutors.drop([i1, i2])

        res_df = pd.DataFrame(results)
        st.session_state['matching_results'] = res_df
        
        st.success(f"✅ Matching completato con successo per {len(results)} aule!")
        st.dataframe(res_df, use_container_width=True)
        
        # Download risultati Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            res_df.to_excel(writer, index=False, sheet_name='Abbinamenti')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Scarica Report Abbinamenti (.xlsx)",
            data=excel_data,
            file_name="Abbinamenti_Co_Tutor_Pegaso.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==========================================
# MODULO 2: PROFILAZIONE TUTOR (QP-CoT)
# ==========================================
elif menu_choice == "📝 Profilazione Tutor (QP-CoT)":
    st.header("Questionario di Profilazione e Stili di Co-Tutoraggio (QP-CoT)")
    st.write("Compila la scheda anagrafica e i **15 quesiti psicometrici** per inserire un nuovo Co-Tutor nel sistema di abbinamento.")
    
    with st.form("qp_cot_form"):
        st.subheader("1. Anagrafica e Competenze")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nome_tutor = st.text_input("Nome e Cognome:", "Dr. Nuovo Tutor")
            sede_tutor = st.selectbox("Sede d'Afferimento:", ["Napoli", "Roma", "Milano", "Bari", "Palermo"])
        with col_f2:
            skills_tutor = st.multiselect("Competenze Specifiche:", ["Bilancio", "Diario", "E-Portfolio", "Inclusione", "Metodologie", "Regia"], default=["Bilancio", "E-Portfolio"])
            disponibile_tutor = st.checkbox("Disponibile per il modulo", value=True)
            
        st.subheader("2. Batteria dei 15 Quesiti Psicometrici (Likert 1–5)")
        st.caption("1 = Completamente in disaccordo, 5 = Completamente in accordo")
        
        item1 = st.slider("1. Mi trovo naturale ed efficace nel prendere la parola in plenaria e guidare la classe.", 1, 5, 4)
        item2 = st.slider("2. Non ho difficoltà a fare un passo indietro per lasciare la conduzione principale al collega.", 1, 5, 4)
        item3 = st.slider("3. Quando in aula vi sono momenti di esitazione, intervengo in modo deciso e assertivo.", 1, 5, 3)
        item4 = st.slider("4. Ritengo fondamentale definire nei minimi dettagli la lezione con il collega nel co-planning.", 1, 5, 5)
        item5 = st.slider("5. Cercare il contatto visivo ed empatico con il collega durante la lezione è prioritario.", 1, 5, 5)
        item6 = st.slider("6. Nel confronto post-aula mi sento a mio agio nel condividere incertezze o errori commessi.", 1, 5, 4)
        item7 = st.slider("7. Considero i 60 minuti di co-progettazione preparatoria un vincolo non negoziabile.", 1, 5, 5)
        item8 = st.slider("8. In aula monitoro costantemente l'orologio ed il rispetto delle tempistiche.", 1, 5, 4)
        item9 = st.slider("9. Completo sempre con precisione e puntualità la documentazione entro 48 ore.", 1, 5, 4)
        item10 = st.slider("10. Se la classe lo richiede, riadatto la Co-Roadmap al volo senza problemi.", 1, 5, 4)
        item11 = st.slider("11. Amo sperimentare strategie didattiche dinamiche (es. Station Teaching).", 1, 5, 4)
        item12 = st.slider("12. Mi attivo al meglio nel coordinare l'architettura generale e le sintesi (Azione).", 1, 5, 4)
        item13 = st.slider("13. La mia massima efficacia è nel facilitare i piccoli gruppi ai tavoli (Sociale).", 1, 5, 3)
        item14 = st.slider("14. Trovo stimolante osservare con metodo i dati d'aula e analizzare le interazioni (Valutazione).", 1, 5, 3)
        item15 = st.slider("15. Considero la presenza del collega come una risorsa speculare per crescere insieme.", 1, 5, 5)
        
        submit_profiling = st.form_submit_button("💾 Salva e Calcola Profilo Tutor", type="primary")

    if submit_profiling:
        agency_score = int(((item1 + item3) / 2.0) * 20 - (item2 * 5) + 25)
        communion_score = int(((item4 + item5 + item6) / 3.0) * 20)
        cosc_score = int(((item7 + item8 + item9) / 3.0) * 20)
        apertura_score = int(((item10 + item11) / 2.0) * 20)
        
        belbin_scores = {'Azione': item12, 'Sociale': item13, 'Valutazione': item14}
        belbin_role = max(belbin_scores, key=belbin_scores.get)
        
        new_tutor = {
            'nome': nome_tutor,
            'sede': sede_tutor,
            'agency': max(min(agency_score, 100), 10),
            'communion': max(min(communion_score, 100), 10),
            'coscienziosita': cosc_score,
            'apertura': apertura_score,
            'skills': ", ".join(skills_tutor),
            'belbin_role': belbin_role,
            'disponibile': disponibile_tutor
        }
        
        st.session_state['tutors_df'] = pd.concat([st.session_state['tutors_df'], pd.DataFrame([new_tutor])], ignore_index=True)
        st.success(f"🎉 Profilo registrato con successo per **{nome_tutor}**!")
        st.json(new_tutor)

# ==========================================
# MODULO 3: CARICAMENTO BATCH (EXCEL/CSV)
# ==========================================
elif menu_choice == "📊 Caricamento Batch (Excel/CSV)":
    st.header("Caricamento Batch Dati (Excel / CSV)")
    st.write("Importa o esporta l'elenco dei **Co-Tutor** e delle **Aule Regionali** via file Excel.")
    
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.subheader("Elenco Attuale Co-Tutor")
        st.dataframe(st.session_state['tutors_df'], use_container_width=True)
        uploaded_tutors = st.file_uploader("Carica File Co-Tutor (.xlsx / .csv)", type=["xlsx", "csv"], key="tutor_up")
        if uploaded_tutors:
            df_up = pd.read_excel(uploaded_tutors) if uploaded_tutors.name.endswith('.xlsx') else pd.read_csv(uploaded_tutors)
            st.session_state['tutors_df'] = df_up
            st.success("Tabella Co-Tutor aggiornata!")
            
    with col_up2:
        st.subheader("Elenco Attuale Aule Regionali")
        st.dataframe(st.session_state['classrooms_df'], use_container_width=True)
        uploaded_rooms = st.file_uploader("Carica File Aule (.xlsx / .csv)", type=["xlsx", "csv"], key="room_up")
        if uploaded_rooms:
            df_rm = pd.read_excel(uploaded_rooms) if uploaded_rooms.name.endswith('.xlsx') else pd.read_csv(uploaded_rooms)
            st.session_state['classrooms_df'] = df_rm
            st.success("Tabella Aule aggiornata!")

# ==========================================
# MODULO 4: PATTO DI CORRESPONSABILITÀ
# ==========================================
elif menu_choice == "📜 Patto di Corresponsabilità":
    st.header("Generatore del Patto di Corresponsabilità Professionale")
    st.write("Genera il documento formale vincolante da far sottoscrivere al team abbinato prima dell'ingresso in aula.")
    
    t1_name = st.selectbox("Seleziona Co-Tutor 1:", st.session_state['tutors_df']['nome'].unique(), index=0)
    t2_name = st.selectbox("Seleziona Co-Tutor 2:", st.session_state['tutors_df']['nome'].unique(), index=1)
    
    patto_text = f"""
    =================================================================================
             UNIVERSITÀ TELEMATICA PEGASO — PERCORSI ABILITANTI (D.P.C.M. 4 AGOSTO 2023)
                   PATTO DI CORRESPONSABILITÀ PROFESSIONALE TRA CO-TUTOR
    =================================================================================
    
    I sottoscritti Co-Tutor:
    1. {t1_name}
    2. {t2_name}
    
    impegnati nella conduzione del laboratorio di Tirocinio Indiretto,
    
    SOTTOSCRIVONO IL SEGUENTE IMPEGNO ETICO-OPERATIVO:
    
    1. PARITÀ DI STATUS: Operare in aula con pari dignità e corresponsabilità (parity of professional status),
       garantendo un'immagine unitaria e priva di gerarchizzazione di fronte al gruppo classe.
    2. TEMPI PROTETTI PRE-AULA: Svolgere tassativamente i 60 minuti di co-progettazione preparatoria (co-planning)
       per concordare la Co-Roadmap e la ripartizione dei ruoli.
    3. CO-REGIA FLUIDA: Alternare la voce e la conduzione in aula applicando le 5 configurazioni fisiche in presenza.
    4. INTERVISIONE NON GIUDICANTE: Dedicare 45 minuti entro 48 ore dalla lezione al debriefing riflessivo (co-debriefing)
       fondato sulla rilevazione dei dati oggettivi d'aula.
    
    Data: ____________________
    
    Firme dei Co-Tutor:
    ___________________________ ({t1_name})
    ___________________________ ({t2_name})
    """
    
    st.code(patto_text, language="text")
    st.download_button("📥 Scarica Patto di Corresponsabilità (.txt)", patto_text, file_name=f"Patto_Corresponsabilita_{t1_name}_{t2_name}.txt")

# ==========================================
# MODULO 5: QUADRO SCIENTIFICO (PARTE QUINTA)
# ==========================================
elif menu_choice == "📖 Quadro Scientifico (Parte Quinta)":
    st.header("Quadro Scientifico e Fondamenti Metodologici (Parte Quinta)")
    st.markdown("""
    ### Parte Quinta — La complementarità relazionale nel co-tutoraggio: modelli scientifici e psicometrici per l'abbinamento
    
    Il modello di abbinamento in diadi e triadi si fonda su tre pilastri scientifici integrati:
    
    1. **Big Five / OCEAN (*Goldberg, 1990; Rhodes, 2021*)**:
       - *Coscienziosità*: assicura il rispetto dei 60 min di co-planning e 45 min di co-debriefing.
       - *Stabilità Emotiva*: disattiva le dinamiche di ansia da prestazione e giudizio gerarchico (*judgementoring*).
    
    2. **Circomplesso Interpersonale e Complementarità (*Wiggins, 1991; Kiesler, 1996*)**:
       - *Omofilia sulla Communion*: entrambi i tutor ad elevata affiliazione per un clima psicologicamente sicuro.
       - *Complementarità sull'Agency*: un profilo guida assertivo affiancato da un profilo flessibile nell'ascolto per evitare scontri di regia.
    
    3. **Ruoli di Team di Belbin (*Belbin, 2010*)**:
       - Nelle **Triadi**, saturazione di 3 ruoli distinti: **Azione** (Plenaria), **Sociale** (Sottogruppi) e **Valutazione** (Osservazione OMF), azzerando il rischio di passività del terzo tutor.
    """)
