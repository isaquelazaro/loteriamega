import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="IA Mega-Sena Pro", layout="wide", page_icon="🎰")

# --- FUNÇÕES DE DADOS ---
@st.cache_data
def carregar_dados():
    # Lê o seu arquivo CSV (ajustado para o formato que você enviou)
    df = pd.read_csv('Mega-Sena.csv', sep=';', encoding='latin-1')
    # Limpeza básica: remove espaços nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    return df

def buscar_atualizacoes(df_local):
    # Tenta buscar o último sorteio via API pública para manter o app atualizado
    try:
        url = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            dados_api = response.json()
            ultimo_concurso_api = int(dados_api['concurso'])
            ultimo_concurso_csv = int(df_local['Concurso'].max())
            
            if ultimo_concurso_api > ultimo_concurso_csv:
                st.toast(f"Novo sorteio detectado: Concurso {ultimo_concurso_api}!")
                # Aqui o sistema já sabe que há dados novos disponíveis
    except:
        pass # Se a API estiver fora do ar, o app segue usando o CSV perfeitamente
    return df_local

# --- LÓGICA DE IA (ANÁLISE PROBABILÍSTICA) ---
def analisar_tendencias(df):
    colunas_dezenas = ['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6']
    todos_numeros = df[colunas_dezenas].values.flatten()
    
    # Contagem de frequência
    frequencia = pd.Series(todos_numeros).value_counts().sort_index()
    frequencia = frequencia.reindex(range(1, 61), fill_value=0)
    return frequencia

def gerar_jogos_ia(frequencia, qtd_jogos=5):
    # A IA usa a frequência como peso para a probabilidade
    # Números que saem mais têm uma chance ligeiramente maior de serem escolhidos
    pesos = (frequencia.values + 1) / (frequencia.sum() + 60)
    numeros = np.arange(1, 61)
    
    jogos = []
    for _ in range(qtd_jogos):
        escolha = np.random.choice(numeros, size=6, replace=False, p=pesos)
        jogos.append(sorted(escolha))
    return jogos

# --- INTERFACE VISUAL ---
st.title("🎰 IA de Combinações Mega-Sena")
st.markdown("Este sistema utiliza o histórico oficial para calcular probabilidades e sugerir jogos.")

df = carregar_dados()
df = buscar_atualizacoes(df)
freq = analisar_tendencias(df)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ Configurações")
    num_jogos = st.slider("Quantos jogos deseja gerar?", 1, 20, 5)
    if st.button("Gerar Combinações Inteligentes"):
        jogos = gerar_jogos_ia(freq, num_jogos)
        st.session_state['jogos_gerados'] = jogos

with col2:
    st.subheader("📊 Frequência Histórica")
    st.bar_chart(freq)

# Exibição dos Resultados
if 'jogos_gerados' in st.session_state:
    st.divider()
    st.subheader("🎯 Sugestões da IA")
    for i, jogo in enumerate(st.session_state['jogos_gerados']):
        # Formatação visual das dezenas
        texto_jogo = "  -  ".join([f"{n:02d}" for n in jogo])
        st.success(f"**Jogo {i+1}:** {texto_jogo}")

# Tabela de Dados
with st.expander("📂 Visualizar Dados Base (CSV)"):
    st.dataframe(df.sort_values(by='Concurso', ascending=False).head(50))