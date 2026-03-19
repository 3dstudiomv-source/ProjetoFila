import streamlit as st
import json, os, time

# 1. Configuração Inicial
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. Funções de Dados
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        if not os.path.exists(arq): 
            return {"fila": [], "atual": 0, "chamados": 0}
        try:
            with open(arq, "r", encoding="utf-8") as f: 
                return json.load(f)
        except: 
            return {"fila": [], "atual": 0, "chamados": 0}
    else:
        with open(arq, "w", encoding="utf-8") as f: 
            json.dump(info, f, indent=4)

db = gerenciar_dados("ler")

# 3. Lógica de ID do Usuário
user_id = st.query_params.get("id")
if user_id: 
    st.session_state["meu_id"] = user_id
elif "meu_id" in st.session_state: 
    user_id = st.session_state["meu_id"]

# 4. Painel Administrativo (Lateral)
with st.sidebar:
    st.header("Painel Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.success("Logado")
        total, chamados = db["atual"], db["chamados"]
        st.metric("Total", total)
        st.metric("Chamados", chamados)
        
        if st.button("PROXIMO (1)", type="primary", use_container_width=True):
            if chamados < total:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        
        if st.button("GRUPO (10)", use_container_width=True):
            db["chamados"] = min(chamados + 10, total)
            gerenciar_dados("salvar", db)
            st.rerun()
            
        st.divider()
        st.write("PROXIMOS 10:")
        prox = [p for p in db["fila"] if p["s"] > chamados][:10]
        for p in prox: 
            st.text(f"{p['s']} - {p['n']}")
            
        if st.button("RESETAR SISTEMA"):
            if st.checkbox("Confirmar reset?"):
                gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

# 5. Interface do Cliente (Principal)
st.title("🎫 Fila 3D Studio")

if not user_id:
    nome = st.text
