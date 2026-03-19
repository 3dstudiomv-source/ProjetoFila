import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO (Deve ser a primeira linha)
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. FUNÇÕES DE DADOS (Persistência)
def carregar_dados():
    default = {"fila": [], "senha_atual": 0, "chamados": 0}
    if not os.path.exists("dados_fila.json"):
        return default
    try:
        with open("dados_fila.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def salvar_dados(dados):
    with open("dados_fila.json", "w", encoding='utf-8') as f:
        json.dump(dados, f, indent=4)

dados = carregar_dados()

# 3. LÓGICA DE MEMÓRIA (Persistência no navegador)
id_na_url = st.query_params.get("id")

if id_na_url:
    st.session_state["meu_id"] = id_na_url
elif "meu_id" in st.session_state:
    id_na_url = st.session_state["meu_id"]

# 4. PAINEL DO ADMINISTRADOR (LATERAL)
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    senha_adm = st.text_input("Senha Master", type="password")
    
    if senha_adm == "01a02b03c0":
        st.success("Admin Ativo")
        total = dados["senha_atual"]
        atual = dados["chamados"]
        
        st.metric("Total Emitido", total)
        st.metric("Senha no Painel", atual)
        
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if atual < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR +10", use_container_width=True):
            dados["chamados"] = min(atual + 10, total)
            salvar_dados(dados)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos 10")
        # Lista de espera filtrada e limitada a 10
        espera = [p for p in dados["fila"] if p["senha"] > atual][:10]
        
        if espera:
            for p in espera:
                st.info(f"**{p['senha']}°** - {p['nome']}")
        else:
            st.write("Ninguém na fila.")

        st.divider()
        if st.button("♻️ Resetar Sistema"):
            if st.checkbox("Confirmar Reset?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()
    elif senha_adm != "":
        st.error("Senha Incorreta")

# 5. INTERFACE DO CLIENTE (CENTRAL)
st.title("🎫 Fila Virtual 3D Studio")

if id_na_url is None:
    # TELA DE CADASTRO
    st.write("Pegue sua senha para o atendimento:")
    nome_input = st.text_input("Seu Nome:")
    if st.button("PEGAR MINHA SENHA", type="primary"):
        if nome_input.strip():
            dados["senha_atual"] += 1
            nova_s = dados["senha_atual"]
            dados["fila"].append({"nome": nome_input, "senha": nova_s})
            salvar_dados(dados)
            st.query
