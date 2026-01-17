import streamlit as st
import pandas as pd
import numpy as np
import itertools
import random
import requests

st.set_page_config(page_title="IA Mega-Sena Pro", layout="wide", page_icon="🍀")

@st.cache_data(ttl=3600)
def carregar_e_atualizar_dados():
    try:
        # Carrega o CSV com proteção de formato
        df = pd.read_csv('Mega-Sena.csv', sep=';', encoding='latin-1', low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        
        # Converte Concurso e Bolas para numérico, removendo erros
        for col in ['Concurso', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['Concurso', 'Bola1'])
        
        # Tenta API
        try:
            ultimo_csv = int(df['Concurso'].max())
            r_ver = requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena/latest", timeout=3).json()
            ultimo_api = int(r_ver['concurso'])
            
            if ultimo_api > ultimo_csv:
                novos = []
                for i in range(ultimo_csv + 1, ultimo_api + 1):
                    r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/megasena/{i}", timeout=3).json()
                    novos.append({
                        'Concurso': i, 'Data do Sorteio': r['data'],
                        'Bola1': int(r['dezenas'][0]), 'Bola2': int(r['dezenas'][1]),
                        'Bola3': int(r['dezenas'][2]), 'Bola4': int(r['dezenas'][3]),
                        'Bola5': int(r['dezenas'][4]), 'Bola6': int(r['dezenas'][5])
                    })
                df = pd.concat([pd.DataFrame(novos), df], ignore_index=True)
        except:
            pass # Se a API falhar, o app abre com o que tem no CSV
            
        return df
    except Exception as e:
        st.error(f"Erro crítico ao ler o arquivo: {e}")
        return pd.DataFrame()

# --- Restante do código (IA, Fechamento, Simulador) ---
df = carregar_e_atualizar_dados()

if not df.empty:
    st.title("🍀 IA Mega-Sena Profissional")
    
    # Lógica de estatísticas
    cols_b = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
    ultimo_c = df['Concurso'].max()
    todos_n = df[cols_b].values.flatten()
    freq = pd.Series(todos_n).value_counts().reindex(range(1, 61), fill_value=0)
    
    atrasos = {}
    for n in range(1, 61):
        idx = df[df[cols_b].isin([n]).any(axis=1)]['Concurso']
        atrasos[n] = int(ultimo_c - idx.max()) if not idx.empty else int(ultimo_c)
    atrasos = pd.Series(atrasos)

    tab1, tab2, tab3 = st.tabs(["🚀 Gerador IA", "📐 Fechamento", "🔍 Simulador"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            fator = st.slider("Equilíbrio Freq/Atraso", 0.0, 1.0, 0.5)
            n_jogos = st.number_input("Jogos", 1, 20, 5)
            if st.button("Gerar 🍀"):
                p = ((freq/freq.max())*(1-fator)) + ((atrasos/atrasos.max())*fator)
                p = (p+0.01)/p.sum()
                st.session_state['jogos'] = [sorted(np.random.choice(range(1,61), 6, False, p)) for _ in range(n_jogos)]
        with c2:
            if 'jogos' in st.session_state:
                for j in st.session_state['jogos']:
                    st.success(f"🍀 Jogo: {' - '.join([f'{x:02d}' for x in j])}")

    # (Módulos de Fechamento e Simulador simplificados para evitar erros)
    with tab2:
        sel = st.multiselect("Dezenas (7-12):", range(1,61), default=range(1,11))
        if len(sel) >= 7:
            if st.button("Gerar Fechamento"):
                comb = list(itertools.combinations(sel, 6))
                for i, j in enumerate(random.sample(comb, min(len(comb), 15))):
                    st.code(f"Jogo {i+1:02d}: {' - '.join([f'{x:02d}' for x in sorted(j)])}")

    with tab3:
        teste = st.multiselect("Seu jogo:", range(1,61), max_selections=6)
        if len(teste) == 6:
            if st.button("Simular"):
                df['Hits'] = df[cols_b].apply(lambda x: len(set(teste).intersection(set(x))), axis=1)
                st.write(f"Senas: {len(df[df.Hits==6])} | Quinas: {len(df[df.Hits==5])} | Quadras: {len(df[df.Hits==4])}")
                if df.Hits.max() >= 4: st.dataframe(df[df.Hits >= 4][['Concurso','Hits']])

st.caption(f"Último Concurso: {df['Concurso'].max() if not df.empty else 'Erro'}")
