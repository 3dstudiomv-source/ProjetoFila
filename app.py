import streamlit as st
import json, os, time

# 1. Configuração Inicial
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. Funções de Dados (Com tratamento de erro para chaves antigas)
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        default = {"fila": [], "atual": 0, "chamados": 0}
        if not os.path.exists(arq): return default
        try:
            with open(arq, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Garante que as chaves existam (evita KeyError)
                if "atual" not in data and "senha_atual" in data:
                    data["atual"] = data["senha_atual"]
                return data
        except:
            return default
    else:
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

db = gerenciar_dados("ler")

# 3. Identificação do Usuário
u_id = st.query_params.get("id")
if u_id:
    st.session_state["meu_id"] = u_id
elif "meu_id" in st.session_state:
    u_id = st.session_state["meu_id"]

# 4. Painel Administrativo (Lateral)
with st.sidebar:
    st.header("⚙️ Painel Admin")
    pw = st.text_input("Senha Master", type="password")
    if pw == "01a02b03c0":
        st.success("Acesso Liberado")
        t_emitidas = db.get("atual", 0)
        t_chamados = db.get("chamados", 0)
        
        st.metric("Total Senhas", t_emitidas)
        st.metric("No Painel", t_chamados)
        
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if t_chamados < t_emitidas:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        
        if st.button("🚀 CHAMAR GRUPO (10)", use_container_width=True):
            db["chamados"] = min(t_chamados + 10, t_emitidas)
            gerenciar_dados("salvar", db)
            st.rerun()
            
        st.divider()
        st.subheader("📋 Próximos 10")
        lista_prox = [p for p in db["fila"] if p["s"] > t_chamados][:10]
        if lista_prox:
            for p in lista_prox:
                st.text(f"{p['s']}° - {p['n']}")
        else:
            st.write("Fila vazia.")

        if st.button("♻️ RESETAR SISTEMA"):
            if st.checkbox("Confirmar limpeza total?"):
                gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()
    elif pw != "":
        st.error("Senha incorreta")

# 5. Interface do Cliente
st.title("🎫 Fila 3D Studio")

if not u_id:
    st.write("Digite seu nome para entrar na fila:")
    nome_input = st.text_input("Nome:")
    if st.button("PEGAR MINHA SENHA", type="primary"):
        if nome_input.strip():
            db["atual"] += 1
            n_senha = db["atual"]
            db["fila"].append({"n": nome_input, "s": n_senha})
            gerenciar_dados("salvar", db)
            st.query_params["id"] = str(n_senha)
            st.session_state["meu_id"] = str(n_senha)
            st.rerun()
        else:
            st.warning("O nome é obrigatório.")
else:
    try:
        minha_s = int(u_id)
        eu = next((p for p in db["fila"] if p["s"] == minha_s), None)
        if eu:
            pos = minha_s - db["chamados"]
            if pos > 10:
                st.info(f"Olá {eu['n']}! Sua senha é
