import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO (Deve ser a primeira linha)
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. FUNÇÕES DE BANCO DE DADOS
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

# 3. PAINEL DO ADMINISTRADOR (LATERAL)
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    senha_adm = st.text_input("Digite a senha master", type="password")
    
    # Verificação da senha
    if senha_adm == "01a02b03c0":
        st.success("Acesso Autorizado")
        
        # Métricas rápidas
        total = dados["senha_atual"]
        atual = dados["chamados"]
        
        st.metric("Total de Senhas", total)
        st.metric("Senha Atual", atual)
        st.divider()
        
        # Botões de Chamada
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if atual < total:
                dados["chamados"] += 1
                salvar_dados(dados)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)", use_container_width=True):
            dados["chamados"] = min(atual + 10, total)
            salvar_dados(dados)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos 10 Nomes")
        
        # Gera a lista de quem ainda não foi chamado
        espera = [p for p in dados["fila"] if p["senha"] > atual][:10]
        
        if espera:
            for p in espera:
                st.info(f"**{p['senha']}°** - {p['nome']}")
        else:
            st.write("Ninguém na espera.")

        if st.button("♻️ Resetar Sistema"):
            if st.checkbox("Confirmar Reset Total?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()
    elif senha_adm != "":
        st.error("Senha Incorreta")

# 4. INTERFACE DO CLIENTE (CENTRAL)
st.title("🎫 Fila Virtual 3D Studio")

params = st.query_params
user_id = params.get("id")

if user_id is None:
    # TELA INICIAL: PEGAR SENHA
    st.write("Bem-vindo! Por favor, entre na fila para ser atendido.")
    nome_input = st.text_input("Seu Nome:")
    if st.button("PEGAR MINHA SENHA", type="primary"):
        if nome_input.strip():
            dados["senha_atual"] += 1
            nova_s = dados["senha_atual"]
            dados["fila"].append({"nome": nome_input, "senha": nova_s})
            salvar_dados(dados)
            st.query_params["id"] = str(nova_s)
            st.rerun()
        else:
            st.warning("O nome é obrigatório.")
else:
    # TELA DE ACOMPANHAMENTO
    try:
        minha_senha = int(user_id)
        # Busca o nome do usuário na lista
        info = next((p for p in dados["fila"] if p["senha"] == minha_senha), None)
        nome_cliente = info["nome"] if info else "Visitante"
        
        posicao = minha_senha - dados["chamados"]

        if posicao > 10:
            st.info(f"### Olá, {nome_cliente}!")
            st.metric("Sua Senha", minha_senha)
            st.metric("Faltam", posicao, help="Pessoas na sua frente")
            st.write("Você ainda tem tempo. Aproveite o evento!")
        
        elif 1 <= posicao <= 10:
            st.error(f"## 🏃‍♂️ {nome_cliente.upper()}, PREPARE-SE!")
            st.write(f"Sua senha é a **{minha_senha}** e você é o **{posicao}°** da fila.")
            st.subheader("📍 DIRIJA-SE AO LOCAL DO EVENTO AGORA!")
            st.balloons()
            
        elif posicao == 0:
            st.success(f"## 🎉 SUA VEZ, {nome_cliente.upper()}!")
            st.write("Apresente esta tela na entrada.")
            st.balloons()
        
        else:
            st.warning("Esta senha já foi chamada.")
            if st.button("Pegar Nova Senha"):
                st.query_params.clear()
                st.rerun()

        # Atualização automática suave
        time.sleep(10)
        st.rerun()
        
    except:
        st.query_params.clear()
        st.rerun()
