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
        # Carrega o ficheiro CSV que você subiu
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
    
    freq = pd.Series(todos_numeros).value_counts().reindex(range(1, 61), fill_value=0)
    
    atrasos = {}
    for n in range(1, 61):
        ultimo_sorteio_n = df[df[colunas_dezenas].isin([n]).any(axis=1)]['Concurso'].max()
        atrasos[n] = int(ultimo_concurso - ultimo_sorteio_n) if not pd.isna(ultimo_sorteio_n) else int(ultimo_concurso)
    
    return freq, pd.Series(atrasos)

# --- INTERFACE PRINCIPAL ---
st.title("🎰 Mega-Sena Profissional")

df = carregar_dados()
if not df.empty:
    freq, atrasos = analisar_estatisticas(df)

    # Criação das 3 abas
    tab1, tab2, tab3 = st.tabs(["🚀 Gerador IA", "📐 Fechamento", "🔍 Simulador Histórico"])

    with tab1:
        st.subheader("Sugestão Baseada em Probabilidades")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            fator_atraso = st.slider("Peso do Atraso (Números sumidos)", 0.0, 1.0, 0.5)
            qtd_jogos = st.number_input("Quantidade de jogos", 1, 20, 5)
            if st.button("Gerar Jogos IA"):
                pesos = ( (freq / freq.max()) * (1 - fator_atraso) ) + ( (atrasos / atrasos.max()) * fator_atraso )
                pesos = (pesos + 0.01) / (pesos.sum() + 0.6)
                jogos = [sorted(np.random.choice(range(1, 61), size=6, replace=False, p=pesos)) for _ in range(qtd_jogos)]
                st.session_state['ia_jogos'] = jogos
        with col_b:
            if 'ia_jogos' in st.session_state:
                for j in st.session_state['ia_jogos']:
                    st.success(f"**Jogo:** {' - '.join([f'{n:02d}' for n in j])}")

    with tab2:
        st.subheader("Fechamento Matemático")
        selecionados = st.multiselect("Selecione de 7 a 12 números:", options=list(range(1, 61)), default=list(range(1, 11)))
        if len(selecionados) >= 7:
            total_comb = len(list(itertools.combinations(selecionados, 6)))
            st.write(f"Combinações possíveis: {total_comb}")
            amostra = st.slider("Visualizar quantos jogos?", 1, min(total_comb, 100), 10)
            if st.button("Gerar Fechamento"):
                jogos_f = random.sample(list(itertools.combinations(selecionados, 6)), amostra)
                for i, jogo in enumerate(jogos_f):
                    st.code(f"Jogo {i+1:02d}: {' - '.join([f'{n:02d}' for n in sorted(jogo)])}")

    with tab3:
        st.subheader("Simulador de Resultados")
        st.write("Verifique se o seu jogo já teria ganho alguma vez no passado.")
        meu_jogo = st.multiselect("Escolha 6 números para testar:", options=list(range(1, 61)), max_selections=6)
        
        if len(meu_jogo) == 6:
            if st.button("Simular"):
                meu_set = set(meu_jogo)
                cols_bolas = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
                
                # Comparação com todo o histórico
                df['Acertos'] = df[cols_bolas].apply(lambda row: len(meu_set.intersection(set(row))), axis=1)
                
                res = df['Acertos'].value_counts()
                sena = res.get(6, 0)
                quina = res.get(5, 0)
                quadra = res.get(4, 0)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Senas", sena)
                c2.metric("Quinas", quina)
                c3.metric("Quadras", quadra)
                
                if sena > 0 or quina > 0 or quadra > 0:
                    st.balloons()
                    st.write("### Detalhes das Vitórias Passadas:")
                    st.dataframe(df[df['Acertos'] >= 4][['Concurso', 'Data do Sorteio', 'Acertos']])
                else:
                    st.warning("Este jogo nunca premiou (4, 5 ou 6 acertos) no histórico oficial.")

st.divider()
st.caption(f"Dados atualizados até o Concurso: {df['Concurso'].max() if not df.empty else 'N/A'}")

