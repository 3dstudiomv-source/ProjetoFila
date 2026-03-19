import streamlit as st
import json, os, time

# 1. Configuração de Página
st.set_page_config(page_title="Fila 3D Studio", page_icon="🎫")

# 2. Funções de Dados (Garante compatibilidade de versões)
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        default = {"fila": [], "atual": 0, "chamados": 0}
        if not os.path.exists(arq): return default
        try:
            with open(arq, "r", encoding="utf-8") as f:
                data = json.load(f)
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

# 3. Lógica de Identificação
u_id = st.query_params.get("id")
if u_id: 
    st.session_state["meu_id"] = u_id
elif "meu_id" in st.session_state: 
    u_id = st.session_state["meu_id"]

# 4. Painel Admin (Sidebar)
with st.sidebar:
    st.header("⚙️ Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.success("Acesso OK")
        t_em = db.get("atual", 0)
        t_ch = db.get("chamados", 0)
        st.metric("Total", t_em)
        st.metric("No Painel", t_ch)
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary"):
            if t_ch < t_em:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        st.divider()
        st.write("PROXIMOS 10:")
        lista = [p for p in db.get("fila", []) if p.get("s", 0) > t_ch][:10]
        for p in lista:
            st.text(str(p.get("s", "?")) + " - " + str(p.get("n", "Sem nome")))
        if st.button("♻️ RESETAR TUDO"):
            if st.checkbox("Confirmar reset?"):
                gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

# 5. Interface Principal (Cliente)
st.title("🎫 Fila 3D Studio")

# SE NÃO HOUVER ID, MOSTRA O CADASTRO
if u_id is None:
    st.subheader("Bem-vindo! Pegue sua senha:")
    nome_input = st.text_input("Seu Nome:")
    if st.button("PEGAR MINHA SENHA", type="primary"):
        if nome_input.strip():
            db["atual"] += 1
            n_s = db["atual"]
            db["fila"].append({"n": nome_input, "s": n_s})
            gerenciar_dados("salvar", db)
            st.query_params["id"] = str(n_s)
            st.session_state["meu_id"] = str(n_s)
            st.rerun()
        else:
            st.warning("Por favor, digite seu nome.")

# SE HOUVER ID, MOSTRA A SENHA E STATUS
else:
    try:
        minha_s = int(u_id)
        eu = next((p for p in db.get("fila", []) if p.get("s") == minha_s), None)
        if eu:
            pos = minha_s - db.get("chamados", 0)
            if pos > 10:
                st.info("Olá " + str(eu.get("n")) + "! Sua senha é: " + str(minha_s))
                st.metric("Faltam", pos)
                st.write("Pode passear, avisaremos quando estiver perto!")
            elif 1 <= pos <= 10:
                st.error("🏃 PREPARE-SE " + str(eu.get("n", "")).upper())
                st.subheader("Você é o " + str(pos) + "º da fila. VÁ PARA A ENTRADA!")
                st.balloons()
            elif pos == 0:
                st.success("🎉 SUA VEZ, " + str(eu.get("n", "")).upper() + "!")
                st.write("Apresente esta tela na recepção.")
                st.balloons()
            else:
                st.warning("Sua senha já passou.")
                if st.button("Pegar Nova Senha"):
                    st.query_params.clear()
                    st.session_state.clear()
                    st.rerun()
        
        # Atualiza a cada 10 seg para o cliente
        time.sleep(10)
