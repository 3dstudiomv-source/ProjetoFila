import streamlit as st
import json, os, time

# 1. Configuração (ÍCONE DE LUPA)
st.set_page_config(page_title="Perícia ao Alcance de todos", page_icon="🔍")

# 2. Funções de Dados
def gerenciar_dados(acao="ler", info=None):
    arq = "dados_fila.json"
    if acao == "ler":
        default = {"fila": [], "atual": 0, "chamados": 0}
        if not os.path.exists(arq): return default
        try:
            with open(arq, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "atual" not in d: d["atual"] = d.get("senha_atual", 0)
                return d
        except: return default
    else:
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

db = gerenciar_dados("ler")

# 3. Lógica de Persistência
id_cliente = st.query_params.get("id")

# 4. Painel Lateral (Admin)
with st.sidebar:
    st.header("⚙️ Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.success("Admin Ativo")
        
        # VARIÁVEIS DO PAINEL
        t_inscritos = db.get("atual", 0)     # Total que pegou senha
        t_chamados = db.get("chamados", 0)   # Senha atual no painel
        em_espera = t_inscritos - t_chamados # Quantos faltam atender
        
        # EXIBIÇÃO DAS MÉTRICAS NO ADMIN
        st.metric("Total de Inscrições", t_inscritos)
        st.metric("Senha Atual no Painel", t_chamados)
        st.metric("Pessoas em Espera", em_espera, delta_color="inverse")
        
        st.divider()
        
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if t_chamados < t_inscritos:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        
        st.divider()
        st.write("📋 PRÓXIMOS DA FILA:")
        lista = [p for p in db.get("fila", []) if p.get("s", 0) > t_chamados][:10]
        for p in lista:
            st.text(f"{p.get('s')} - {p.get('n')}")
            
        if st.button("♻️ RESET TOTAL"):
            if st.checkbox("Limpar tudo?"):
                gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()

# 5. Interface Principal (Cliente)
st.title("🔍 Perícia ao Alcance de todos")

if not id_cliente:
    st.subheader("Bem-vindo, Perito(a)! Pegue sua senha:")
    nome = st.text_input("Seu Nome:")
    if st.button("GERAR MINHA SENHA", type="primary"):
        if nome.strip():
            db["atual"] += 1
            nova = db["atual"]
            db["fila"].append({"n": nome, "s": nova})
            gerenciar_dados("salvar", db)
            st.query_params["id"] = str(nova)
            time.sleep(0.5) 
            st.rerun()
        else:
            st.warning("Nome obrigatório.")
else:
    try:
        minha_s = int(id_cliente)
        eu = next((p for p in db["fila"] if p.get("s") == minha_s or p.get("senha") == minha_s), None)
        
        if eu:
            nome_cli = eu.get("n") or eu.get("nome", "Cliente")
            pos = minha_s - db["chamados"]
            
            if pos > 0:
                st.info(f"📍 Olá {nome_cli}! Sua senha é **{minha_s}**")
                st.metric("Posição na Fila", f"{pos}º")
            elif pos == 0:
                st.success(f"🎉 SUA VEZ, {nome_cli.upper()}!")
                st.subheader("APRESENTE ESTA TELA NA ENTRADA")
                st.balloons()
            else:
                st.warning("Sua senha já passou ou já foi chamada.")
                if st.button("Pegar Nova Senha"):
                    st.query_params.clear()
                    st.rerun()
        else:
            st.query_params.clear()
            st.rerun()

        time.sleep(10)
        st.rerun()
        
    except Exception:
        st.query_params.clear()
        st.rerun()
