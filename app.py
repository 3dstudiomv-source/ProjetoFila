import streamlit as st
import json, os, time

# 1. Configuração e Estilo
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")
st.markdown("<style>.stMetric {background: #f0f2f6; padding: 10px; border-radius: 10px;}</style>", unsafe_allow_html=True)

# 2. Banco de Dados Simples
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        if not os.path.exists(arq): return {"fila": [], "atual": 0, "chamados": 0}
        with open(arq, "r") as f: return json.load(f)
    else:
        with open(arq, "w") as f: json.dump(info, f)

db = gerenciar_dados("ler")

# 3. Identificação do Usuário (URL ou Memória)
user_id = st.query_params.get("id")
if user_id: st.session_state["meu_id"] = user_id
elif "meu_id" in st.session_state: user_id = st.session_state["meu_id"]

# 4. Painel Administrativo (Lateral)
with st.sidebar:
    st.title("⚙️ Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.metric("Total", db["atual"])
        st.metric("No Painel", db["chamados"])
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary"):
            if db["chamados"] < db["atual"]:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        if st.button("🚀 CHAMAR +10"):
            db["chamados"] = min(db["chamados"] + 10, db["atual"])
            gerenciar_dados("salvar", db)
            st.rerun()
        st.write("---")
        st.subheader("📋 Próximos 10")
        fila_nome = [p for p in db["fila"] if p["s"] > db["chamados"]][:10]
        for p in fila_nome: st.text(f"{p['s']}° - {p['n']}")
        if st.button("♻️ RESET TOTAL"):
            gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()

# 5. Interface do Cliente
st.title("🎫 Fila 3D Studio")

if not user_id:
    nome = st.text_input("Seu Nome:")
    if st.button("PEGAR SENHA", type="primary"):
        if nome:
            db["atual"] += 1
            nova = db["atual"]
            db["fila"].append({"n": nome, "s": nova})
            gerenciar_dados("salvar", db)
            st.query_params["id"] = str(nova)
            st.session_state["meu_id"] = str(nova)
            st.rerun()
else:
    try:
        minha_s = int(user_id)
        me = next((p for p in db["fila"] if p["s"] == minha_s), None)
        if me:
            pos = minha_s - db["chamados"]
            if pos > 10:
                st.info(f"### Olá, {me['n']}!")
                st.metric("Sua Senha", minha_s)
                st.write(f"Faltam {pos} pessoas.")
            elif 1 <= pos <= 10:
                st.error(f"## 🏃 {me['n'].upper()}, VEM
