import streamlit as st
import json
import os
import fcntl
import logging
from pathlib import Path

# ─────────────────────────────────────────────
# CORREÇÃO 1: Configuração de logging adequado
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("fila.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 1. Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(page_title="Perícia ao Alcance de todos", page_icon="🔍")

# ─────────────────────────────────────────────
# CORREÇÃO 2: Auto-refresh sem bloquear worker
# Substitui o time.sleep(10) + st.rerun() no
# fluxo principal por um componente dedicado.
# Instale: pip install streamlit-autorefresh
# ─────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=10_000, key="auto_refresh")
except ImportError:
    logger.warning(
        "streamlit-autorefresh não instalado. "
        "Execute: pip install streamlit-autorefresh"
    )
    st.toast("⚠️ Auto-refresh indisponível. Instale streamlit-autorefresh.", icon="⚠️")

# ─────────────────────────────────────────────
# 2. Funções de Dados com lock de arquivo
# ─────────────────────────────────────────────
ARQ = Path("dados_fila.json")
DEFAULT_DB = {"fila": [], "atual": 0, "chamados": 0}


def _ler_sem_lock() -> dict:
    """Lê o JSON do disco (sem adquirir lock)."""
    if not ARQ.exists():
        return dict(DEFAULT_DB)
    try:
        with ARQ.open("r", encoding="utf-8") as f:
            d = json.load(f)
        # Compatibilidade com versão antiga que usava "senha_atual"
        if "atual" not in d:
            d["atual"] = d.get("senha_atual", 0)
        return d
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Erro ao ler dados_fila.json: %s", e)
        return dict(DEFAULT_DB)


def _salvar_sem_lock(info: dict) -> None:
    """Salva o JSON no disco (sem adquirir lock)."""
    try:
        with ARQ.open("w", encoding="utf-8") as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
    except IOError as e:
        logger.error("Erro ao salvar dados_fila.json: %s", e)
        raise


# ─────────────────────────────────────────────
# CORREÇÃO 3: Race condition — lock exclusivo
# Todas as operações de leitura-modificação-
# escrita são feitas dentro do mesmo lock.
# ─────────────────────────────────────────────
def gerar_senha(nome: str) -> int:
    """Gera uma nova senha de forma atômica (thread/process-safe)."""
    lock_path = Path("dados_fila.lock")
    with lock_path.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)        # bloqueia outros processos
        try:
            db = _ler_sem_lock()
            db["atual"] += 1
            nova = db["atual"]
            db["fila"].append({"n": nome.strip(), "s": nova})
            _salvar_sem_lock(db)
            logger.info("Senha %d gerada para '%s'.", nova, nome.strip())
            return nova
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)    # libera o lock sempre


def chamar_proximo(db: dict) -> dict:
    """Chama a próxima senha de forma atômica."""
    lock_path = Path("dados_fila.lock")
    with lock_path.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            db = _ler_sem_lock()              # relê dentro do lock
            if db["chamados"] < db["atual"]:
                db["chamados"] += 1
                _salvar_sem_lock(db)
                logger.info("Senha %d chamada.", db["chamados"])
            return db
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def resetar_dados() -> None:
    """Apaga todos os dados de forma atômica."""
    lock_path = Path("dados_fila.lock")
    with lock_path.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            _salvar_sem_lock(dict(DEFAULT_DB))
            logger.info("Dados resetados.")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def ler_dados() -> dict:
    """Leitura simples (somente leitura não precisa de lock exclusivo)."""
    return _ler_sem_lock()


# ─────────────────────────────────────────────
# 3. Leitura inicial do banco de dados
# ─────────────────────────────────────────────
db = ler_dados()

# ─────────────────────────────────────────────
# 4. Persistência de sessão via query params
# ─────────────────────────────────────────────
id_cliente = st.query_params.get("id")

# ─────────────────────────────────────────────
# 5. Painel Lateral (Admin)
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Admin")

    # ─────────────────────────────────────────
    # CORREÇÃO 4: Senha via st.secrets
    # Crie .streamlit/secrets.toml com:
    #   admin_pw = "sua_senha_segura"
    # ─────────────────────────────────────────
    try:
        senha_correta = st.secrets["admin_pw"]
    except (KeyError, FileNotFoundError):
        logger.warning(
            "st.secrets['admin_pw'] não configurado. "
            "Crie .streamlit/secrets.toml com admin_pw = 'sua_senha'."
        )
        senha_correta = None
        st.warning("⚠️ secrets.toml não configurado.")

    pw = st.text_input("Senha", type="password")

    if senha_correta and pw == senha_correta:
        st.success("Admin Ativo")

        t_inscritos = db.get("atual", 0)
        t_chamados  = db.get("chamados", 0)
        em_espera   = t_inscritos - t_chamados

        st.metric("Total de Inscrições",    t_inscritos)
        st.metric("Senha Atual no Painel",  t_chamados)
        st.metric("Pessoas em Espera",      em_espera, delta_color="inverse")

        st.divider()

        if st.button("🔔 CHAMAR PRÓXIMO", type="primary", use_container_width=True):
            if t_chamados < t_inscritos:
                db = chamar_proximo(db)
                st.rerun()
            else:
                st.info("Não há mais pessoas na fila.")

        st.divider()
        st.write("📋 PRÓXIMOS DA FILA:")
        lista = [p for p in db.get("fila", []) if p.get("s", 0) > t_chamados][:10]
        for p in lista:
            st.text(f"{p.get('s')} - {p.get('n')}")

        st.divider()

        # ─────────────────────────────────────
        # CORREÇÃO 5: Reset com session_state
        # Evita o comportamento imprevisível do
        # checkbox + button no mesmo ciclo.
        # ─────────────────────────────────────
        if "confirmar_reset" not in st.session_state:
            st.session_state.confirmar_reset = False

        if not st.session_state.confirmar_reset:
            if st.button("♻️ RESET TOTAL", use_container_width=True):
                st.session_state.confirmar_reset = True
                st.rerun()
        else:
            st.error("⚠️ Isso apagará TODOS os dados!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar", type="primary", use_container_width=True):
                    resetar_dados()
                    st.session_state.confirmar_reset = False
                    st.query_params.clear()
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_reset = False
                    st.rerun()

# ─────────────────────────────────────────────
# 6. Interface Principal (Cliente)
# ─────────────────────────────────────────────
st.title("🔍 Perícia ao Alcance de todos")

if not id_cliente:
    st.subheader("Bem-vindo, Perito(a)! Pegue sua senha:")
    nome = st.text_input("Seu Nome:")

    if st.button("GERAR MINHA SENHA", type="primary"):
        if nome.strip():
            # gerar_senha() já é atômico (usa lock internamente)
            nova = gerar_senha(nome)
            st.query_params["id"] = str(nova)
            st.rerun()
        else:
            st.warning("Nome obrigatório.")
else:
    # ─────────────────────────────────────────
    # CORREÇÃO 6: Exceções específicas + log
    # ─────────────────────────────────────────
    try:
        minha_s = int(id_cliente)
    except ValueError:
        logger.warning("id_cliente inválido: '%s'", id_cliente)
        st.query_params.clear()
        st.rerun()
        st.stop()

    try:
        eu = next(
            (p for p in db["fila"] if p.get("s") == minha_s or p.get("senha") == minha_s),
            None
        )

        if eu:
            nome_cli = eu.get("n") or eu.get("nome", "Cliente")
            pos = minha_s - db.get("chamados", 0)

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
            logger.warning("Senha %d não encontrada na fila.", minha_s)
            st.query_params.clear()
            st.rerun()

    except (KeyError, TypeError, StopIteration) as e:
        logger.error("Erro inesperado na interface do cliente: %s", e)
        st.query_params.clear()
        st.rerun()
