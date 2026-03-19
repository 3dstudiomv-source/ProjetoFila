import streamlit as st
import json
import os
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando) ---
st.set_page_config(page_title="Fila Smart - 3D Studio", page_icon="🎫", layout="centered")

# --- 2. ESTILO VISUAL (CSS) ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; }
    .main-title { font-size: 32px; font-weight: bold; text-align: center; color: #1E1E1E; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---
def carregar_dados():
    if os.path.exists("dados_fila.json"):
        try:
            with open("dados_fila.json", "r") as f:
                return json.load(f)
        except:
            return {"fila": [], "senha_atual": 0, "chamados": 0}
    return {"fila": [], "senha_atual": 0, "chamados": 0}

def salvar_dados(dados):
    with open("dados_fila.json", "w") as f:
        json.dump(dados, f)

# Carrega os dados IMEDIATAMENTE
dados = carregar_dados()

# --- 4. LÓGICA DE URL (QUERY PARAMS) ---
# No Streamlit moderno, usamos st.query_params como um dicionário
params = st.query_params
id_na_url = params.get("id", None)

# --- 5. PAINEL DO ADMINISTRADOR (LATERAL) ---
with st.sidebar:
    st.header("🔐 Gestão da Fila")
    senha_admin = st.text_input("Senha Admin", type="password")
    
    if senha_admin == "01a02b03c0":
        st.success("Acesso Master Ativo")
        st.divider()
        
        total = dados["senha_atual"]
        chamados = dados["chamados"]
        espera = total - chamados
        
        c1, c2 = st.columns(2)
        c1.metric("Emitidas", total)
        c2.metric("No Painel", chamados)
        st.metric("Aguardando Agora", espera)
        
        st.divider()
        
        if st.button("🔔 CHAMAR PRÓXIMO (1)", use_container_width=True, type="primary"):
            if chamados < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)", use_container_width=True):
            dados["chamados"] = min(dados["chamados"] + 10, total)
            salvar_dados(dados)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos:")
        proximos = [p for p in dados["fila"] if p["senha"] > chamados][:5]
        for p in proximos:
            st.write(f"**{p['senha']}°** - {p['nome']}")

        if st.button("♻️ RESETAR SISTEMA"):
            salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
            st.query_params.clear()
            st.rerun()
    elif senha_admin != "":
        st.error("Senha incorreta")

# --- 6. INTERFACE DO USUÁRIO (CENTRAL) ---
st.markdown('<p class="main-title">🎫 Sistema de Fila Virtual</p>', unsafe_allow_html=True)

# Lógica principal de exibição
if id_na_url is None:
    # TELA DE ENTRADA
    with st.container(border=True):
        st.subheader("Bem-vindo! Pegue sua senha:")
        nome = st.text_input("Qual o seu nome?")
        if st.button("GERAR MINHA SENHA", use_container_width=True, type="primary"):
            if nome:
                dados["senha_atual"] += 1
                nova_senha = dados["senha_atual"]
                dados["fila"].append({"nome": nome, "senha": nova_senha})
                salvar_dados(dados)
                st.query_params["id"] = str(nova_senha)
                st.rerun()
            else:
                st.warning("Por favor, digite seu nome.")
else:
    # TELA DE ACOMPANHAMENTO
    try:
        minha_senha = int(id_na_url)
        user_info = next((p for p in dados["fila"] if p["senha"] == minha_senha), None)
        nome_user = user_info["nome"] if user_info else "Visitante"
        
        posicao = minha_senha - dados["chamados"]

        if posicao > 10:
            st.info(f"### Olá, **{nome_user}**!")
            st.write(f"Sua senha: **{minha_senha}** | Painel: **{dados['chamados']}**")
            st.metric("Pessoas na sua frente", posicao)
            st.write("⏳ Ainda temos um tempinho.")

        elif 1 <= posicao <= 10:
            st.error(f"## 🏃‍♂️ {nome_user.upper()}, PREPARE-SE!")
            st.markdown(f"### Você é o **{posicao}°** da fila.")
            st.markdown("### 📍 DIRIJA-SE AO LOCAL DO EVENTO AGORA.")
            st.balloons()

        elif posicao == 0:
            st.success(f"## 🎉 {nome_user.upper()}, SUA VEZ!")
            st.markdown("### 🟢 APRESENTE-SE NA ENTRADA IMEDIATAMENTE.")

        else:
            st.warning(f"⚠️ A senha {minha_senha} já foi chamada.")
            if st.button("Pegar nova senha"):
                st.query_params.clear()
                st.rerun()
                
    except Exception as e:
        st.error("Erro ao ler sua senha. Tente pegar uma nova.")
        if st.button("Voltar ao início"):
            st.query_params.clear()
            st.rerun()

# --- 7. AUTO-REFRESH (POSICIONADO NO FINAL) ---
# Atualiza a página a cada 10 segundos para ver se a fila andou
time.sleep(10)
st.rerun()
