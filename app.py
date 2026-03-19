import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO INICIAL (Obrigatório ser o primeiro comando)
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫", layout="centered")

# 2. FUNÇÕES DE ARQUIVO (Com tratamento de erro robusto)
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

# Inicialização dos dados
dados = carregar_dados()

# 3. ESTILO CSS
st.markdown("""
    <style>
    .main { text-align: center; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .status-card { padding: 20px; border-radius: 15px; border: 1px solid #ddd; margin-bottom: 20px; }
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
        st.metric("Restante na Fila", total - chamados)
        
        st.divider()
        if st.button("🔔 CHAMAR PRÓXIMO (1)"):
            if chamados < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)"):
            dados["chamados"] = min(chamados + 10, total)
            salvar_dados(dados)
            st.rerun()
            
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

# Lemos o ID da URL usando a nova API do Streamlit
params = st.query_params
id_usuario = params.get("id")

if id_usuario is None:
    # --- TELA DE CADASTRO ---
    st.markdown("### Bem-vindo ao evento!")
    with st.container():
        nome = st.text_input("Digite seu nome para entrar na fila:")
        if st.button("PEGAR MINHA SENHA"):
            if nome.strip():
                dados["senha_atual"] += 1
                nova_senha = dados["senha_atual"]
                dados["fila"].append({"nome": nome, "senha": nova_senha})
                salvar_dados(dados)
                # Define o ID na URL e recarrega
                st.query_params["id"] = str(nova_senha)
                st.rerun()
            else:
                st.warning("Por favor, preencha seu nome.")
else:
    # --- TELA DE ACOMPANHAMENTO ---
    try:
        minha_senha = int(id_usuario)
        user_info = next((p for p in dados["fila"] if p["senha"] == minha_senha), None)
        nome_cliente = user_info["nome"] if user_info else "Visitante"
        
        posicao = minha_senha - dados["chamados"]

        if posicao > 10:
            # Espera Normal
            st.info(f"### Olá, {nome_cliente}!")
            st.metric("Sua Senha", minha_senha)
            st.metric("Pessoas na sua frente", posicao)
            st.write("⏳ Você ainda tem tempo. Aproveite as outras atrações!")
            
        elif 1 <= posicao <= 10:
            # Aviso de Proximidade (Aviso dos 10)
            st.error(f"## 🏃‍♂️ {nome_cliente.upper()}, VENHA AGORA!")
            st.markdown(f"### Você é o **{posicao}º** da fila.")
            st.markdown("---")
            st.markdown("### 📍 DIRIJA-SE AO LOCAL DO EVENTO IMEDIATAMENTE.")
            st.balloons()

        elif posicao == 0:
            # Chegou a vez
            st.success(f"## 🎉 {nome_cliente.upper()}, SUA VEZ!")
            st.markdown("### 🟢 APRESENTE-SE NA ENTRADA.")
            st.balloons()
            
        else:
            # Já passou
            st.warning("Sua senha já foi chamada ou é inválida.")
            if st.button("Pegar Nova Senha"):
                st.query_params.clear()
                st.rerun()

        # AUTO-REFRESH: Só acontece se o usuário estiver acompanhando a senha
        time.sleep(10)
        st.rerun()

    except Exception as e:
        st.error("Erro no link da senha.")
        if st.button("Voltar ao Início"):
            st.query_params.clear()
            st.rerun()
