import streamlit as st
import json
import os
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão de Fila Pro", page_icon="📊")

def carregar_dados():
    if os.path.exists("dados_fila.json"):
        with open("dados_fila.json", "r") as f:
            return json.load(f)
    return {"fila": [], "senha_atual": 0, "chamados": 0}

def salvar_dados(dados):
    with open("dados_fila.json", "w") as f:
        json.dump(dados, f)

dados = carregar_dados()
params = st.query_params
id_na_url = params.get("id")

# --- PAINEL ADMIN (Lateral) ---
st.sidebar.header("⚙️ Painel de Controle")
senha_input = st.sidebar.text_input("Senha de Acesso", type="password")

# A nova senha que você solicitou
if senha_input == "01a02b03c0":
    st.sidebar.success("Acesso Autorizado")
    
    # Cálculos para as métricas
    total_emitidas = dados["senha_atual"]
    senha_no_painel = dados["chamados"]
    em_espera = total_emitidas - senha_no_painel
    
    # Mostrando os dados de forma organizada
    st.sidebar.divider()
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Emitidas", total_emitidas)
    col2.metric("Chamadas", senha_no_painel)
    st.sidebar.metric("Aguardando agora", em_espera)
    st.sidebar.divider()

    if st.sidebar.button("🔔 CHAMAR PRÓXIMO", use_container_width=True):
        if senha_no_painel < total_emitidas:
            dados["chamados"] += 1
            salvar_dados(dados)
            st.rerun()
        else:
            st.sidebar.warning("Não há ninguém na fila.")

    if st.sidebar.button("♻️ Resetar Sistema Completo"):
        if st.sidebar.checkbox("Confirmar reset?"):
            dados = {"fila": [], "senha_atual": 0, "chamados": 0}
            salvar_dados(dados)
            st.query_params.clear()
            st.rerun()
else:
    if senha_input != "":
        st.sidebar.error("Senha Incorreta")

# --- LÓGICA DO CLIENTE (Corpo Principal) ---
st.title("🎫 Sistema de Fila")

if not id_na_url:
    st.header("📲 Pegar Senha")
    nome = st.text_input("Seu nome:")
    if st.button("Gerar Senha"):
        if nome:
            dados["senha_atual"] += 1
            nova_senha = dados["senha_atual"]
            dados["fila"].append({"nome": nome, "senha": nova_senha})
            salvar_dados(dados)
            st.query_params["id"] = nova_senha
            st.rerun()
else:
    minha_senha = int(id_na_url)
    faltam = minha_senha - dados["chamados"]

    with st.container(border=True):
        st.write(f"### Olá! Sua senha é: **{minha_senha}**")
        if faltam > 0:
            st.metric("Pessoas na sua frente", faltam)
            st.info("Aguarde. Esta página atualiza automaticamente.")
        elif faltam == 0:
            st.success("🎉 SUA VEZ CHEGOU!")
            st.balloons()
        else:
            st.error("❌ Sua vez já passou.")
            if st.button("Pegar nova senha"):
                st.query_params.clear()
                st.rerun()

    time.sleep(15)
    st.rerun()
