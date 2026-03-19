import streamlit as st
import json, os, time

# 1. Configuração
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. Funções de Dados (Com conversão automática de chaves)
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        default = {"fila": [], "atual": 0, "chamados": 0}
        if not os.path.exists(arq): return default
        try:
            with open(arq, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Normaliza chaves antigas para o formato novo
                if "senha_atual" in data: data["atual"] = data["senha_atual"]
                for p in data.get("fila", []):
                    if "senha" in p: p["s"] = p["senha"]
                    if "nome" in p: p["n"] = p["nome"]
                return data
        except: return default
    else:
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

db = gerenciar_dados("ler")

# 3. Identificação
u_id = st.query_params.get("id")
if u_id: st.session_state["meu_id"] = u_id
elif "meu_id" in st.session_state: u_id = st.session_state["meu_id"]

# 4. Admin
with st.sidebar:
    st.header("Painel Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.success("Acesso OK")
        t_em = db.get("atual", 0)
        t_ch = db.get("chamados", 0)
        st.metric("Total", t_em)
        st.metric("Chamados", t_ch)
        
        if st.button("PROXIMO", type="primary", use_container_width=True):
            if t_ch < t_em:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
                
        st.divider()
        st.write("PROXIMOS 10:")
        # Proteção extra contra KeyError na lista
        lista = [p for p in db.get("fila", []) if p.get("s", 0) > t_ch][:10]
        for p in lista:
            st.text(str(p.get("s", "?")) + " - " + str(p.get("n", "Sem nome")))
            
        if st.button("RESETAR TUDO"):
            if st.checkbox("Confirmar?
