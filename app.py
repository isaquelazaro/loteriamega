import streamlit as st
import pandas as pd
import numpy as np
import itertools
import random

# Configuração da página
st.set_page_config(page_title="IA Mega-Sena Pro", layout="wide", page_icon="🎰")

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv('Mega-Sena.csv', sep=';', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['Concurso'] = pd.to_numeric(df['Concurso'], errors='coerce')
        return df.dropna(subset=['Concurso'])
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo CSV: {e}")
        return pd.DataFrame()

def analisar_estatisticas(df):
    colunas_dezenas = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
    ultimo_concurso = df['Concurso'].max()
    todos_numeros = df[colunas_dezenas].values.flatten()
    
    # Frequência
    freq = pd.Series(todos_numeros).value_counts().reindex(range(1, 61), fill_value=0)
    
    # Atrasos
    atrasos = {}
    for n in range(1, 61):
        ultimo_sorteio_n = df[df[colunas_dezenas].isin([n]).any(axis=1)]['Concurso'].max()
        atrasos[n] = int(ultimo_concurso - ultimo_sorteio_n) if not pd.isna(ultimo_sorteio_n) else int(ultimo_concurso)
    
    return freq, pd.Series(atrasos)

# --- INTERFACE PRINCIPAL ---
st.title("🎰 IA Mega-Sena Profissional")
st.markdown("Análise de tendências e fechamentos matemáticos.")

df = carregar_dados()
if not df.empty:
    freq, atrasos = analisar_estatisticas(df)

    tab1, tab2 = st.tabs(["🚀 Gerador IA (Probabilidade)", "📐 Fechamento Matemático"])

    with tab1:
        st.subheader("Sugestão Baseada em Tendências")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            fator_atraso = st.slider("Peso do Atraso vs Frequência", 0.0, 1.0, 0.5)
            qtd_jogos = st.number_input("Quantidade de jogos", 1, 20, 5)
            
            if st.button("Gerar Jogos IA"):
                # Lógica de pesos
                pesos = ( (freq / freq.max()) * (1 - fator_atraso) ) + ( (atrasos / atrasos.max()) * fator_atraso )
                pesos = (pesos + 0.01) / (pesos.sum() + 0.6)
                
                jogos = []
                for _ in range(qtd_jogos):
                    j = sorted(np.random.choice(range(1, 61), size=6, replace=False, p=pesos))
                    jogos.append(j)
                st.session_state['ia_jogos'] = jogos

        with col_b:
            if 'ia_jogos' in st.session_state:
                for j in st.session_state['ia_jogos']:
                    st.success(f"**Jogo:** {' - '.join([f'{n:02d}' for n in j])}")

    with tab2:
        st.subheader("Fechamento (Garanta prêmios com mais números)")
        st.info("Escolha de 8 a 12 números. O sistema gerará as combinações de 6 números para otimizar suas chances.")
        
        # Sugestão de números baseada na IA para o fechamento
        sugestao_numeros = freq.sort_values(ascending=False).head(12).index.tolist()
        
        selecionados = st.multiselect(
            "Selecione as dezenas para o fechamento:",
            options=list(range(1, 61)),
            default=sugestao_numeros[:10]
        )
        
        if len(selecionados) < 7:
            st.warning("Selecione pelo menos 7 números para um fechamento.")
        else:
            total_comb = len(list(itertools.combinations(selecionados, 6)))
            st.write(f"Total de combinações possíveis: **{total_comb}**")
            
            # Limitar para não travar o navegador se escolherem números demais
            amostra = st.slider("Quantos jogos do fechamento deseja visualizar?", 1, min(total_comb, 50), 10)
            
            if st.button("Gerar Fechamento"):
                comb_completas = list(itertools.combinations(selecionados, 6))
                jogos_f = random.sample(comb_completas, amostra)
                
                cols = st.columns(2)
                for i, jogo in enumerate(jogos_f):
                    with cols[i % 2]:
                        st.code(f"Jogo {i+1:02d}: {' - '.join([f'{n:02d}' for n in sorted(jogo)])}")

st.divider()
st.caption(f"Último concurso analisado: {df['Concurso'].max() if not df.empty else 'N/A'}")
