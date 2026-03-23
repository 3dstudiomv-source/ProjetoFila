import streamlit as st
import json
import os
import fcntl
import logging
from pathlib import Path
from datetime import datetime, date, timedelta

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("checkin.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Perícia ao Alcance de Todos",
    page_icon="🔍",
    layout="centered"
)

# ─────────────────────────────────────────────
# Auto-refresh (instale: pip install streamlit-autorefresh)
# ─────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30_000, key="auto_refresh")
except ImportError:
    pass

# ─────────────────────────────────────────────
# Constantes de horário
# ─────────────────────────────────────────────
HORA_INICIO = 10          # 10h
HORA_FIM    = 20          # 20h (última sessão começa às 19h30)
DURACAO_MIN = 30          # 30 minutos por sessão
VAGAS_POR_SESSAO = 10

def gerar_slots() -> list[str]:
    """Gera lista de horários ex: ['10:00','10:30',...,'19:30']"""
    slots = []
    t = datetime.strptime(f"{HORA_INICIO:02d}:00", "%H:%M")
    fim = datetime.strptime(f"{HORA_FIM:02d}:00", "%H:%M")
    while t < fim:
        slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=DURACAO_MIN)
    return slots

SLOTS = gerar_slots()

# ─────────────────────────────────────────────
# Persistência — JSON com lock
# ─────────────────────────────────────────────
ARQ      = Path("dados_checkin.json")
ARQ_LOCK = Path("dados_checkin.lock")

DEFAULT_DB = {
    "dia_ativo": None,        # "2024-06-15"
    "sessoes": {}
    # estrutura: { "2024-06-15": { "10:00": [{"nome":"...", "presente": false}, ...] } }
}

def _ler() -> dict:
    if not ARQ.exists():
        return dict(DEFAULT_DB)
    try:
        with ARQ.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Erro ao ler JSON: %s", e)
        return dict(DEFAULT_DB)

def _salvar(data: dict) -> None:
    try:
        with ARQ.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error("Erro ao salvar JSON: %s", e)
        raise

def com_lock(fn, *args, **kwargs):
    """Executa fn dentro de lock exclusivo de arquivo."""
    with ARQ_LOCK.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            return fn(*args, **kwargs)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)

# ─────────────────────────────────────────────
# Operações de negócio
# ─────────────────────────────────────────────
def inscrever(dia: str, slot: str, nome: str, sobrenome: str) -> tuple[bool, str]:
    """
    Tenta inscrever uma pessoa num slot. Retorna (sucesso, mensagem).
    Executado dentro de lock.
    """
    def _op():
        db = _ler()
        sessoes_dia = db["sessoes"].setdefault(dia, {})
        lista = sessoes_dia.setdefault(slot, [])

        # Verifica vagas
        if len(lista) >= VAGAS_POR_SESSAO:
            return False, "Este horário já está lotado."

        nome_completo = f"{nome.strip()} {sobrenome.strip()}"

        # Verifica duplicata no mesmo slot
        nomes_existentes = [p["nome"].lower() for p in lista]
        if nome_completo.lower() in nomes_existentes:
            return False, "Você já está inscrito neste horário."

        lista.append({"nome": nome_completo, "presente": False})
        _salvar(db)
        logger.info("Inscrito: %s | %s | %s", dia, slot, nome_completo)
        return True, "ok"

    return com_lock(_op)

def definir_dia_ativo(dia: str) -> None:
    def _op():
        db = _ler()
        db["dia_ativo"] = dia
        _salvar(db)
        logger.info("Dia ativo definido: %s", dia)
    com_lock(_op)

def resetar_dia(dia: str) -> None:
    def _op():
        db = _ler()
        db["sessoes"].pop(dia, None)
        _salvar(db)
        logger.info("Dia %s resetado.", dia)
    com_lock(_op)

def ler_db() -> dict:
    return _ler()

# ─────────────────────────────────────────────
# CSS customizado
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
}

.slot-card {
    background: #0f1117;
    border: 1.5px solid #2a2d3a;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: border-color 0.2s;
}
.slot-card:hover { border-color: #4f8ef7; }
.slot-hora {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #e8eaf6;
}
.slot-vagas-ok  { color: #4caf7d; font-size: 0.85rem; font-weight: 500; }
.slot-vagas-mid { color: #f0a500; font-size: 0.85rem; font-weight: 500; }
.slot-vagas-no  { color: #e05c5c; font-size: 0.85rem; font-weight: 500; }
.slot-passado   { opacity: 0.4; }

.confirmacao-box {
    background: linear-gradient(135deg, #1a2744 0%, #0f1117 100%);
    border: 2px solid #4f8ef7;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    margin-top: 20px;
}
.confirmacao-nome {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #e8eaf6;
}
.confirmacao-horario {
    font-size: 3rem;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    color: #4f8ef7;
    margin: 8px 0;
}
.confirmacao-data {
    color: #8892b0;
    font-size: 0.9rem;
}

.admin-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: #1a1d27;
}
.admin-nome { color: #e8eaf6; font-size: 0.95rem; }

.badge-presente {
    background: #1e4d35;
    color: #4caf7d;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-ausente {
    background: #2a2d3a;
    color: #8892b0;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Estado local da sessão
# ─────────────────────────────────────────────
if "inscrito" not in st.session_state:
    st.session_state.inscrito = None
    # {"dia": "...", "slot": "...", "nome": "..."}

if "confirmar_reset" not in st.session_state:
    st.session_state.confirmar_reset = False

# ─────────────────────────────────────────────
# Leitura do banco
# ─────────────────────────────────────────────
db = ler_db()
dia_ativo = db.get("dia_ativo")

# ─────────────────────────────────────────────
# PAINEL ADMIN (sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Admin")

    try:
        senha_correta = st.secrets["admin_pw"]
    except (KeyError, FileNotFoundError):
        senha_correta = "admin123"  # fallback para desenvolvimento
        st.caption("⚠️ Configure secrets.toml em produção.")

    pw = st.text_input("Senha", type="password", key="pw_admin")

    if pw == senha_correta:
        st.success("✅ Admin ativo")
        st.divider()

        # ── Definir dia ativo ──
        st.markdown("**📅 Dia ativo**")
        dia_input = st.date_input(
            "Selecione o dia do evento",
            value=date.fromisoformat(dia_ativo) if dia_ativo else date.today(),
            key="dia_input"
        )
        if st.button("✅ Confirmar dia ativo", use_container_width=True):
            definir_dia_ativo(dia_input.isoformat())
            st.rerun()

        if dia_ativo:
            st.info(f"Dia ativo: **{dia_ativo}**")

        st.divider()

        # ── Lista de inscritos por horário ──
        st.markdown("**📋 Inscritos por horário**")
        if not dia_ativo:
            st.warning("Nenhum dia ativo configurado.")
        else:
            sessoes_dia = db.get("sessoes", {}).get(dia_ativo, {})
            if not sessoes_dia:
                st.info("Nenhuma inscrição ainda.")
            else:
                for slot in SLOTS:
                    inscritos = sessoes_dia.get(slot, [])
                    if not inscritos:
                        continue
                    st.markdown(f"**🕐 {slot}** — {len(inscritos)}/{VAGAS_POR_SESSAO} vagas")
                    for p in inscritos:
                        presente = p.get("presente", False)
                        badge = '<span class="badge-presente">✓ presente</span>' if presente else '<span class="badge-ausente">aguardando</span>'
                        st.markdown(
                            f'<div class="admin-row">'
                            f'<span class="admin-nome">👤 {p["nome"]}</span>'
                            f'{badge}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

        st.divider()

        # ── Reset ──
        if not st.session_state.confirmar_reset:
            if st.button("♻️ Resetar dia atual", use_container_width=True):
                st.session_state.confirmar_reset = True
                st.rerun()
        else:
            st.error(f"Apagar todas inscrições de {dia_ativo}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sim", type="primary", use_container_width=True):
                    if dia_ativo:
                        resetar_dia(dia_ativo)
                    st.session_state.confirmar_reset = False
                    st.rerun()
            with c2:
                if st.button("❌ Não", use_container_width=True):
                    st.session_state.confirmar_reset = False
                    st.rerun()

# ─────────────────────────────────────────────
# INTERFACE CLIENTE
# ─────────────────────────────────────────────
st.markdown("## 🔍 Perícia ao Alcance de Todos")

if not dia_ativo:
    st.info("O evento ainda não foi configurado pelo organizador. Volte em breve!")
    st.stop()

# Verifica se a pessoa já está inscrita (no horário ainda válido)
insc = st.session_state.inscrito
agora = datetime.now().strftime("%H:%M")

if insc and insc.get("dia") == dia_ativo:
    slot_inscrito = insc["slot"]
    # Calcula fim do slot
    t_slot = datetime.strptime(slot_inscrito, "%H:%M")
    t_fim  = t_slot + timedelta(minutes=DURACAO_MIN)

    if agora < t_fim.strftime("%H:%M"):
        # Ainda no período válido — mostra confirmação
        st.markdown(
            f'<div class="confirmacao-box">'
            f'<div class="confirmacao-data">📅 {dia_ativo} &nbsp;|&nbsp; sua reserva</div>'
            f'<div class="confirmacao-nome">👤 {insc["nome"]}</div>'
            f'<div class="confirmacao-horario">⏰ {slot_inscrito}</div>'
            f'<div style="color:#8892b0;font-size:0.85rem;">Apresente esta tela ao chegar.<br>'
            f'Diga seu nome ao organizador.</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.stop()
    else:
        # Horário já passou — libera nova inscrição
        st.session_state.inscrito = None
        st.info("Seu horário já passou. Você pode se inscrever em uma nova sessão.")

# ── Formulário de inscrição ──
st.markdown(f"**Evento:** {dia_ativo}  \n**Escolha seu horário e preencha seus dados.**")
st.divider()

# Dados pessoais
c1, c2 = st.columns(2)
with c1:
    nome = st.text_input("Nome *", placeholder="Ex: Maria")
with c2:
    sobrenome = st.text_input("Sobrenome *", placeholder="Ex: Silva")

st.markdown("#### Horários disponíveis")

sessoes_dia = db.get("sessoes", {}).get(dia_ativo, {})

slot_escolhido = None

for slot in SLOTS:
    inscritos = sessoes_dia.get(slot, [])
    vagas_livres = VAGAS_POR_SESSAO - len(inscritos)
    passado = slot < agora

    # Classe visual
    if passado:
        classe_card = "slot-card slot-passado"
    else:
        classe_card = "slot-card"

    if vagas_livres == 0:
        classe_vagas = "slot-vagas-no"
        txt_vagas = "Lotado"
    elif vagas_livres <= 3:
        classe_vagas = "slot-vagas-mid"
        txt_vagas = f"{vagas_livres} vaga{'s' if vagas_livres > 1 else ''} restante{'s' if vagas_livres > 1 else ''}"
    else:
        classe_vagas = "slot-vagas-ok"
        txt_vagas = f"{vagas_livres} vagas disponíveis"

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown(
            f'<div class="{classe_card}">'
            f'<span class="slot-hora">🕐 {slot}</span>'
            f'<span class="{classe_vagas}">{txt_vagas}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col_btn:
        desabilitado = passado or vagas_livres == 0
        label = "Lotado" if vagas_livres == 0 else ("Passado" if passado else "Reservar")
        if st.button(label, key=f"btn_{slot}", disabled=desabilitado, use_container_width=True):
            slot_escolhido = slot

# ── Processar inscrição ──
if slot_escolhido:
    if not nome.strip() or not sobrenome.strip():
        st.warning("⚠️ Preencha nome e sobrenome antes de reservar.")
    else:
        sucesso, msg = inscrever(dia_ativo, slot_escolhido, nome, sobrenome)
        if sucesso:
            st.session_state.inscrito = {
                "dia":  dia_ativo,
                "slot": slot_escolhido,
                "nome": f"{nome.strip()} {sobrenome.strip()}"
            }
            st.rerun()
        else:
            st.error(f"❌ {msg}")
