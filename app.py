import streamlit as st
import json
import os
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fila Inteligente - 3D Studio", page_icon="🎫", layout="centered")

# Estilo visual para melhorar a experiência
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; }
    .main-title { font-size: 32px; font-weight: bold; text-align: center; color: #1E1E1E; padding-bottom: 10px; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def carregar_dados():
    if os.path.exists("dados_fila.json"):
        try:
            with open("dados_fila.json", "r") as f:
                return json.load(f)
        except: pass
    return {"fila": [], "senha_atual": 0, "chamados": 0}

def salvar_dados(dados):
    with open("dados_fila.json", "w") as f:
        json.dump(dados, f)

dados = carregar_dados()
id_na_url = st.query_params.get("id")

# --- PAINEL DO ADMINISTRADOR (LATERAL) ---
with st.sidebar:
    st.header("🔐 Gestão da Fila")
    senha_admin = st.text_input("Senha Admin", type="password")
    
    if senha_admin == "01a02b03c0":
        st.success("Acesso Master Ativo")
        st.divider()
        
        # Métricas de Controle
        total = dados["senha_atual"]
        chamados = dados["chamados"]
        espera = total - chamados
        
        c1, c2 = st.columns(2)
        c1.metric("Emitidas", total)
        c2.metric("No Painel", chamados)
        st.metric("Aguardando Agora", espera)
        
        st.divider()
        
        # Botões de Ação
        if st.button("🔔 CHAMAR PRÓXIMO (1)", use_container_width=True, type="primary"):
            if chamados < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)", use_container_width=True):
            novo_limite = min(chamados + 10, total)
            dados["chamados"] = novo_limite
            salvar_dados(dados)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos nomes:")
        proximos = [p for p in dados["fila"] if p["senha"] > chamados][:5]
        for p in proximos:
            st.write(f"**{p['senha']}°** - {p['nome']}")

        if st.button("♻️ RESETAR SISTEMA"):
            if st.checkbox("Confirmar limpeza?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()
    elif senha_admin != "":
        st
