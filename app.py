import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫", layout="centered")

# 2. FUNÇÕES DE ARQUIVO
def carregar_dados():
    default = {"fila": [], "senha_atual": 0, "chamados": 0}
    if not os.path.exists("dados_fila.json"):
        return default
    try:
        with open("dados_fila.json", "r", encoding='utf-8') as f:
            content = f.read()
            if not content: return default
            return json.loads(content)
    except:
        return default

def salvar_dados(dados):
    with open("dados_fila.json", "w", encoding='utf-8') as f:
        json.dump(dados, f, indent=4)

dados = carregar_dados()

# 3. ESTILO CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .prox-lista { font-size: 14px; color: #555; background: #f0f2f6; padding: 5px 10px; border-radius: 5px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# 4. PAINEL DO ADMINISTRADOR (LATERAL)
with st.sidebar:
    st.header("⚙️ Administração")
    senha = st.text_input("Senha Master", type="password")
    
    if senha == "01a02b03c0":
        st.success("Acesso Liberado")
        total = dados["senha_atual"]
        chamados = dados["chamados"]
        
        st.metric("Total de Senhas", total)
        st.metric("Chamadas no Painel", chamados)
        
        st.divider()
        if st.button("🔔 CHAMAR PRÓXIMO (1)", type="primary"):
            if chamados < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)"):
            dados["chamados"] = min(chamados + 10, total)
            salvar_dados(dados)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos 10 nomes:")
        
        # Filtra apenas quem ainda não foi chamado (senha > chamados)
        proximos = [p for p in dados["fila"] if p["senha"] > chamados][:10]
        
        if proximos:
            for p in proximos:
                st.markdown(f"<div class='prox-lista'><b>{p['senha']}°</b> - {p['nome']}</div>", unsafe_allow_html=True)
        else:
            st.write("Ninguém aguardando na fila.")

        st.divider()
        if st.button("♻️ RESETAR TUDO"):
            if st.checkbox("Confirmar Limpeza?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()
    elif senha != "":
        st.error("Senha Incorreta")

# 5. LÓGICA DO USUÁRIO (CENTRAL)
st.title("🎫 Sistema de Fila Virtual")
params = st.query_params
id_usuario = params.get("id")

if id_usuario is None:
    st.markdown("### Bem-vindo ao evento!")
    nome = st.text_input("Digite seu nome para entrar na fila:")
    if st.button("PEGAR MINHA SENHA"):
        if nome.strip():
            dados["senha_atual"] += 1
            nova_senha = dados["senha_atual"]
            dados["fila"].append({"nome": nome, "senha": nova_senha})
            salvar_dados(dados)
            st.query_params["id"] = str(nova_senha)
            st.rerun()
        else:
            st.warning("Por favor,
