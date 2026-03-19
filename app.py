import streamlit as st
import json, os, time

# 1. Configuração
st.set_page_config(page_title="Perícia ao Alcance de todos", page_icon="🎫")

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

# 3. LÓGICA DE PERSISTÊNCIA (O SEGREDO ESTÁ AQUI)
# Pegamos o ID diretamente da URL
id_cliente = st.query_params.get("id")

# 4. Painel Admin (Lateral)
with st.sidebar:
    st.header("⚙️ Admin")
    pw = st.text_input("Senha", type="password")
    if pw == "01a02b03c0":
        st.success("Admin Ativo")
        t_em = db.get("atual", 0)
        t_ch = db.get("chamados", 0)
        st.metric("Total", t_em, delta=f"+{t_em-t_ch} aguardando")
        
        if st.button("🔔 CHAMAR PRÓXIMO", type="primary"):
            if t_ch < t_em:
                db["chamados"] += 1
                gerenciar_dados("salvar", db)
                st.rerun()
        
        if st.button("♻️ RESET TOTAL"):
            if st.checkbox("Limpar tudo?"):
                gerenciar_dados("salvar", {"fila": [], "atual": 0, "chamados": 0})
                st.query_params.clear()
                st.rerun()

# 5. Interface Principal
st.title("🎫 Fila 3D Studio")

# SE NÃO TEM ID NA URL, MOSTRA CADASTRO
if not id_cliente:
    st.subheader("Bem-vindo! Pegue sua senha:")
    nome = st.text_input("Seu Nome:")
    if st.button("GERAR MINHA SENHA", type="primary"):
        if nome.strip():
            db["atual"] += 1
            nova = db["atual"]
            db["fila"].append({"n": nome, "s": nova})
            gerenciar_dados("salvar", db)
            
            # CRITICAL: Fixa o ID na URL antes de recarregar
            st.query_params["id"] = str(nova)
            time.sleep(0.5) # Pequena pausa para o navegador processar a URL
            st.rerun()
        else:
            st.warning("Nome obrigatório.")

# SE JÁ TEM ID, MOSTRA O STATUS (E NÃO SAI DAQUI)
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
                st.write("A tela atualizará sozinha. Não feche esta aba.")
            elif pos == 0:
                st.success(f"🎉 SUA VEZ, {nome_cli.upper()}!")
                st.subheader("APRESENTE ESTA TELA NA ENTRADA")
                st.balloons()
            else:
                st.warning("Sua senha já passou ou foi chamada.")
                if st.button("Pegar Nova Senha"):
                    st.query_params.clear()
                    st.rerun()
        else:
            # Se o ID na URL não existe no banco, volta pro início
            st.query_params.clear()
            st.rerun()

        # Atualização automática suave
        time.sleep(10)
        st.rerun()
        
    except Exception:
        st.query_params.clear()
        st.rerun()
