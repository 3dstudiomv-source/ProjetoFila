import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO (Deve ser a primeira linha)
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. FUNÇÕES DE DADOS
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

# 3. LÓGICA DE MEMÓRIA (Persistence)
# Tenta pegar o ID da URL
id_na_url = st.query_params.get("id")

# Se o ID está na URL, salvamos na "memória da sessão" para não perder
if id_na_url:
    st.session_state["meu_id"] = id_na_url
# Se o ID sumiu da URL, mas temos na memória da sessão, recuperamos
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
        espera = [p for p in dados["fila"] if p["senha"] > atual][:10]
        for p in espera:
            st.info(f"**{p['senha']}°** - {p['nome']}")

        if st.button("♻️ Resetar Sistema"):
            if st.checkbox("Confirmar Reset?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear() # Limpa a memória também
                st.rerun()

# 5. INTERFACE DO CLIENTE
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
            # Salva na URL e na Memória
            st.query_params["id"] = str(nova_s)
            st.session_state["meu_id"] = str(nova_s)
            st.rerun()
else:
    # TELA DE ACOMPANHAMENTO
    try:
        minha_senha = int(id_na_url
