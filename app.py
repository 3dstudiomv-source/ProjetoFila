import streamlit as st
import json
import os
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fila Virtual Blindada", page_icon="⏳")

def carregar_dados():
    if os.path.exists("dados_fila.json"):
        with open("dados_fila.json", "r") as f:
            return json.load(f)
    return {"fila": [], "senha_atual": 0, "chamados": 0}

def salvar_dados(dados):
    with open("dados_fila.json", "w") as f:
        json.dump(dados, f)

dados = carregar_dados()

# --- MÁGICA DA URL (Lê a senha direto do link do navegador) ---
# Se o link for meusite.app/?id=15, o código abaixo pega o "15"
params = st.query_params
id_na_url = params.get("id")

# --- PAINEL ADMIN ---
st.sidebar.header("⚙️ Admin")
if st.sidebar.text_input("Senha", type="password") == "123":
    if st.sidebar.button("🔔 CHAMAR PRÓXIMO"):
        if dados["chamados"] < dados["senha_atual"]:
            dados["chamados"] += 1
            salvar_dados(dados)
            st.rerun()
    if st.sidebar.button("♻️ Resetar"):
        dados = {"fila": [], "senha_atual": 0, "chamados": 0}
        salvar_dados(dados)
        st.query_params.clear()
        st.rerun()

# --- LÓGICA PRINCIPAL ---
st.title("🎫 Fila Virtual")

# SE NÃO TEM ID NA URL (Usuário novo)
if not id_na_url:
    st.header("📲 Entre na Fila")
    nome = st.text_input("Seu nome:")
    if st.button("Gerar Senha"):
        if nome:
            dados["senha_atual"] += 1
            nova_senha = dados["senha_atual"]
            dados["fila"].append({"nome": nome, "senha": nova_senha})
            salvar_dados(dados)
            # SALVA O ID NA URL (Isso fixa a sessão no celular do cliente)
            st.query_params["id"] = nova_senha
            st.rerun()
else:
    # USUÁRIO JÁ TEM ID (Lemos da URL)
    minha_senha = int(id_na_url)
    faltam = minha_senha - dados["chamados"]

    with st.container(border=True):
        st.write(f"### Sua Senha: **{minha_senha}**")
        if faltam > 0:
            st.metric("Pessoas na frente", faltam)
            st.info("Pode sair do app. Sua posição está salva neste link!")
        elif faltam == 0:
            st.success("🎉 SUA VEZ! Entre agora.")
            st.balloons()
        else:
            st.error("❌ Sua vez passou.")
            if st.button("Pegar nova senha"):
                st.query_params.clear()
                st.rerun()

    # Atualiza a cada 15 segundos para não sobrecarregar
    time.sleep(15)
    st.rerun()