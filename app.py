import streamlit as st
import pandas as pd
import numpy as np
import itertools
import random
import requests

# Configuração da página
st.set_page_config(page_title="IA Mega-Sena Pro", layout="wide", page_icon="🎰")

# --- FUNÇÕES DE DADOS E API ---
@st.cache_data(ttl=3600) # Atualiza o cache a cada 1 hora
def carregar_e_atualizar_dados():
    try:
        # 1. Carrega o CSV base
        df = pd.read_csv('Mega-Sena.csv', sep=';', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['Concurso'] = pd.to_numeric(df['Concurso'], errors='coerce')
        df = df.dropna(subset=['Concurso'])
        
        # 2. Busca concursos novos via API para manter o sistema vivo
        ultimo_csv = int(df['Concurso'].max())
        url_latest = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"
        
        res_ultimo = requests.get(url_latest, timeout=5).json()
        ultimo_caixa = int(res_ultimo['concurso'])
        
        if ultimo_caixa > ultimo_csv:
            novos_jogos = []
            for i in range(ultimo_csv + 1, ultimo_caixa + 1):
                r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/megasena/{i}", timeout=5).json()
                novos_jogos.append({
                    'Concurso': i,
                    'Data do Sorteio': r['data'],
                    'Bola1': int(r['dezenas'][0]), 'Bola2': int(r['dezenas'][1]),
                    'Bola3': int(r['dezenas'][2]), 'Bola4': int(r['dezenas'][3]),
                    'Bola5': int(r['dezenas'][4]), 'Bola6': int(r['dezenas'][5])
                })
            df_novos = pd.DataFrame(novos_jogos)
            df = pd.concat([df_novos, df], ignore_index=True)
            st.toast(f"Atualizado: +{len(novos_jogos)} novos sorteios!")
    except Exception as e:
        st.sidebar.warning("API offline. Usando dados do arquivo local.")
        
    return df

def analisar_estatisticas(df):
    cols_bolas = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
    ultimo_c = df['Concurso'].max()
    todos_n = df[cols_bolas].values.flatten()
    
    # Frequência
    freq = pd.Series(todos_n).value_counts().reindex(range(1, 61), fill_value=0)
    
    # Atrasos
    atrasos = {}
    for n in range(1, 61):
        ultimo_n = df[df[cols_bolas].isin([n]).any(axis=1)]['Concurso'].max()
        atrasos[n] = int(ultimo_c - ultimo_n) if not pd.isna(ultimo_n) else int(ultimo_c)
    
    return freq, pd.Series(atrasos)

# --- INÍCIO DO APP ---
st.title("🎰 IA Mega-Sena Profissional")
st.markdown("Sistema inteligente com atualização automática via API e análise de probabilidade.")

df = carregar_e_atualizar_dados()
if not df.empty:
    freq, atrasos = analisar_estatisticas(df)

    tab1, tab2, tab3 = st.tabs(["🚀 Gerador Inteligente", "📐 Fechamento Matemático", "🔍 Simulador de Passado"])

    # ABA 1: GERADOR IA
    with tab1:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.subheader("Configurações da IA")
            fator_atraso = st.slider("Equilíbrio: Frequência (0) vs Atraso (1)", 0.0, 1.0, 0.5)
            qtd_jogos = st.number_input("Quantos jogos gerar?", 1, 50, 5)
            
            if st.button("Gerar Jogos"):
                pesos = ((freq / freq.max()) * (1 - fator_atraso)) + ((atrasos / atrasos.max()) * fator_atraso)
                pesos = (pesos + 0.01) / (pesos.sum())
                
                st.session_state['ia_jogos'] = [sorted(np.random.choice(range(1, 61), size=6, replace=False, p=pesos)) for _ in range(qtd_jogos)]

        with col_b:
            st.subheader("Sugestões da IA")
            if 'ia_jogos' in st.session_state:
                for j in st.session_state['ia_jogos']:
                    st.success(f"**Jogo:** {' - '.join([f'{n:02d}' for n in j])}")

    # ABA 2: FECHAMENTO
    with tab2:
        st.subheader("Fechamento (Desdobramento)")
        selecionados = st.multiselect("Escolha de 7 a 15 números:", options=list(range(1, 61)), default=list(range(1, 11)))
        if len(selecionados) >= 7:
            comb_total = list(itertools.combinations(selecionados, 6))
            st.info(f"Este grupo permite {len(comb_total)} combinações de 6 números.")
            exibir = st.slider("Mostrar quantos jogos?", 1, min(len(comb_total), 200), 20)
            if st.button("Executar Fechamento"):
                for i, jogo in enumerate(random.sample(comb_total, exibir)):
                    st.code(f"Jogo {i+1:02d}: {' - '.join([f'{n:02d}' for n in sorted(jogo)])}")

    # ABA 3: SIMULADOR
    with tab3:
        st.subheader("Simulador Histórico")
        meu_jogo = st.multiselect("Selecione 6 números para testar:", options=list(range(1, 61)), max_selections=6)
        if len(meu_jogo) == 6:
            if st.button("Simular"):
                meu_set = set(meu_jogo)
                cols_b = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
                df['Hits'] = df[cols_b].apply(lambda x: len(meu_set.intersection(set(x))), axis=1)
                
                res = df['Hits'].value_counts()
                c1, c2, c3 = st.columns(3)
                c1.metric("Senas (6)", res.get(6, 0))
                c2.metric("Quinas (5)", res.get(5, 0))
                c3.metric("Quadras (4)", res.get(4, 0))
                
                if df['Hits'].max() >= 4:
                    st.balloons()
                    st.dataframe(df[df['Hits'] >= 4][['Concurso', 'Data do Sorteio', 'Hits']].sort_values('Hits', ascending=False))
                else:
                    st.warning("Esse jogo nunca teve mais de 3 acertos no passado.")

st.divider()
st.caption(f"Base de dados: Concurso {df['Concurso'].max() if not df.empty else 'N/A'}")
