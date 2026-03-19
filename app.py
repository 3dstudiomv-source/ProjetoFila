import streamlit as st
import json
import os
import time

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫", layout="centered")

# 2. FUNÇÕES DE DADOS (Persistência)
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

# 3. ESTILO CSS PARA A LISTA
st.markdown("""
    <style>
    .prox-item { background-color: #f0f2f6; padding: 8px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #ff4b4b; font-size: 14px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 4. PAINEL DO ADMINISTRADOR (LATERAL)
with st.sidebar:
    st.header("⚙️ Administração")
    senha_adm = st.text_input("Senha Master", type="password")
    
    if senha_adm == "01a02b03c0":
        st.success("Acesso Liberado")
        total = dados["senha_atual"]
        chamados = dados["chamados"]
        
        st.metric("Senhas Emitidas", total)
        st.metric("Senha no Painel", chamados)
        
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
        st.subheader("📋 Próximos 10 da Fila")
        # Filtra quem ainda vai ser chamado
        lista_proximos = [p for p in dados["fila"] if p["senha"] > chamados][:10]
        
        if lista_proximos:
            for p in lista_proximos:
                st.markdown(f"<div class='prox-item'><b>{p['senha']}°</b> — {p['nome']}</div>", unsafe_allow_html=True)
        else:
            st.write("Fila vazia.")

        st.divider()
        if st.button("♻️ RESETAR TUDO"):
            if st.checkbox("Confirmar reset?"):
                salvar_dados({"fila": [], "senha_atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()
    elif senha_adm != "":
        st.error("Senha Incorreta")

# 5. INTERFACE DO USUÁRIO (CENTRAL)
