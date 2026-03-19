import streamlit as st
import json, os, time

# 1. Configuração de Página
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. Funções de Dados (Persistência no Arquivo)
def carregar_dados():
    arq = "dados_fila.json"
    default = {"fila": [], "atual": 0, "chamados": 0}
    if not os.path.exists(arq): return default
    try:
        with open(arq, "r", encoding="utf-8") as f:
            d = json.load(f)
            # Normalização de chaves para evitar KeyError
            if "atual" not in d: d["atual"] = d.get("senha_atual", 0)
            if "chamados" not in d: d["chamados"] = 0
            if "fila" not in d: d["fila"] = []
            return d
    except: return default

def salvar_dados(d):
    with open("dados_fila.json", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=4)

db = carregar_dados()

# 3. LÓGICA DE SALVAMENTO NO NAVEGADOR (Persistência de Senha)
# Tenta pegar o ID da URL primeiro
u_id = st.query_params.get("id")

# Se encontrou na URL, salva na memória da sessão
if u_id:
    st.session_state["meu_id"] = str(u_id)
# Se não está na URL, mas está na sessão, recupera para a URL
elif "meu_id" in st.session_state:
    u_id = st.session_state["meu_id"]
    st.query_params["id"] = str(u_id)

# 4. Painel Lateral (Admin)
with st.sidebar:
    st.header("⚙️ Painel Admin")
    pw = st.text_input("Senha Master", type="password")
    if pw == "01a02b03c0":
        st.success("Acesso OK")
        t_em = db.get("atual", 0)
        t_ch = db.get("chamados", 0)
        st.metric("Total Senhas", t_em)
        st.metric("No Painel", t_ch)
        
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if t_ch < t_em:
                db["chamados"] += 1
                salvar_dados(db)
                st.rerun()
        
        st.divider()
        if st.button("♻️ RESETAR SISTEMA"):
            if st.checkbox("Confirmar Limpeza?"):
                salvar_dados({"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

# 5. Interface do Cliente
st.title("🎫 Fila 3D Studio")

if u_id is None:
    # TELA DE CADASTRO
    st.subheader("Olá! Pegue sua senha abaixo:")
    nome_input = st.text_input("Seu Nome:")
    if st.button("GERAR MINHA SENHA", type="primary"):
        if nome_input.strip():
            db["atual"] += 1
            n_s = db["atual"]
            db["fila"].append({"n": nome_input, "s": n_s})
            salvar_dados(db)
            # SALVA NO NAVEGADOR (URL e Sessão)
            st.query_params["id"] = str(n_s)
            st.session_state["meu_id"] = str(n_s)
            st.rerun()
        else:
            st.warning("O nome é obrigatório.")
else:
    # TELA DE ACOMPANHAMENTO (A senha fica salva aqui)
    try:
        minha_s = int(u_id)
        eu = next((p for p in db["fila"] if p.get("s") == minha_s or p.get("senha") == minha_s), None)
        
        if eu:
            nome_cli = eu.get("n") or eu.get("nome", "Cliente")
            pos = minha_s - db.get("chamados", 0)
            
            if pos > 0:
                st.info("Olá " + str(nome_cli) + "! Sua senha é " + str(minha_s))
                st.metric("Sua Posição", pos)
                if pos <= 5: st.warning("Fique por perto! Você é o próximo.")
            elif pos == 0:
                st.success("🎉 SUA VEZ, " + str(nome_cli).upper() + "!")
                st.balloons()
            else:
                st.warning("Sua senha já passou.")
                if st.button("Pegar Nova Senha"):
                    st.query_params.clear()
                    st.session_state.clear()
                    st.rerun()
        
        # Atualização automática para o cliente
        time.sleep(10)
        st.rerun()
    except:
        # Se der erro no ID, limpa para permitir novo cadastro
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()
