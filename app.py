import streamlit as st
import json
import os
import logging
import threading
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────
# Configuração do Fuso Horário Padrão (Brasília)
# ─────────────────────────────────────────────
FUSO_BR = ZoneInfo("America/Sao_Paulo")

# ─────────────────────────────────────────────
# Logging & Concorrência Safe (Cross-platform)
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

_db_lock = threading.Lock()

# ─────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Perícia ao Alcance de Todos",
    page_icon="🔍",
    layout="centered"
)

# ─────────────────────────────────────────────
# Auto-refresh
# ─────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30_000, key="auto_refresh")
except ImportError:
    pass

# ─────────────────────────────────────────────
# Constantes de horário e Regra de Vagas (Cotas Dinâmicas)
# ─────────────────────────────────────────────
HORA_INICIO = 10          
HORA_FIM    = 20          
DURACAO_MIN = 30          

VAGAS_TOTAL = 10
VAGAS_RESERVADAS_PCD = 2  # As 2 últimas vagas do total de 10 são exclusivas

def gerar_slots() -> list[str]:
    slots = []
    t = datetime.strptime(f"{HORA_INICIO:02d}:00", "%H:%M")
    fim = datetime.strptime(f"{HORA_FIM:02d}:00", "%H:%M")
    while t < fim:
        slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=DURACAO_MIN)
    return slots

SLOTS = gerar_slots()

# ─────────────────────────────────────────────
# Persistência — JSON Seguro
# ─────────────────────────────────────────────
ARQ = Path("dados_checkin.json")

DEFAULT_DB = {
    "dia_ativo": None,
    "sessoes": {}
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
        temp_file = ARQ.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(ARQ)
    except IOError as e:
        logger.error("Erro ao salvar JSON: %s", e)
        raise

def com_lock(fn, *args, **kwargs):
    with _db_lock:
        return fn(*args, **kwargs)

# ─────────────────────────────────────────────
# Operações de negócio
# ─────────────────────────────────────────────
def inscrever(dia: str, slot: str, nome: str, sobrenome: str, eh_pcd: bool) -> tuple[bool, str]:
    def _op():
        db = _ler()
        sessoes_dia = db["sessoes"].setdefault(dia, {})
        lista = sessoes_dia.setdefault(slot, [])

        total_inscritos = len(lista)

        # 1. Validação de teto absoluto
        if total_inscritos >= VAGAS_TOTAL:
            return False, "Este horário já está completamente lotado."

        # 2. Regra Dinâmica de Cotas:
        if total_inscritos >= (VAGAS_TOTAL - VAGAS_RESERVADAS_PCD) and not eh_pcd:
            return False, "As vagas gerais deste horário estão esgotadas. Restam apenas vagas exclusivas para PCD."

        nome_completo = f"{nome.strip()} {sobrenome.strip()}"
        nomes_existentes = [p["nome"].lower() for p in lista]
        
        if nome_completo.lower() in nomes_existentes:
            return False, "Você já está inscrito neste horário."

        lista.append({
            "nome": nome_completo, 
            "presente": False,
            "pcd": eh_pcd
        })
        _salvar(db)
        logger.info("Inscrito: %s | %s | %s | PCD: %s", dia, slot, nome_completo, eh_pcd)
        return True, "ok"

    return com_lock(_op)

def remover_inscricao(dia: str, slot: str, nome_completo: str) -> tuple[bool, str]:
    def _op():
        db = _ler()
        sessoes_dia = db.get("sessoes", {}).get(dia, {})
        lista = sessoes_dia.get(slot, [])
        
        nova_lista = [p for p in lista if p["nome"].lower() != nome_completo.lower()]
        
        if len(nova_lista) == len(lista):
            return False, "Inscrição não encontrada no sistema."
            
        db["sessoes"][dia][slot] = nova_lista
        _salvar(db)
        logger.info("Inscrição removida: %s | %s | %s", dia, slot, nome_completo)
        return True, "ok"

    return com_lock(_op)

def buscar_inscricao_por_nome(dia: str, nome_completo: str) -> dict | None:
    """Busca no JSON se o nome completo já possui um agendamento no dia ativo."""
    if not dia or not nome_completo:
        return None
    db = _ler()
    sessoes_dia = db.get("sessoes", {}).get(dia, {})
    for slot, inscritos in sessoes_dia.items():
        for p in inscritos:
            if p["nome"].lower() == nome_completo.lower():
                return {"dia": dia, "slot": slot, "nome": p["nome"], "pcd": p.get("pcd", False)}
    return None

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

# ─────────────────────────────────────────────
# CSS customizado
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; }

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
.slot-hora { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; color: #e8eaf6; }
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
.confirmacao-nome { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800; color: #e8eaf6; }
.confirmacao-horario { font-size: 3rem; font-family: 'Syne', sans-serif; font-weight: 800; color: #4f8ef7; margin: 8px 0; }
.confirmacao-data { color: #8892b0; font-size: 0.9rem; }

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
.badge-presente { background: #1e4d35; color: #4caf7d; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-ausente { background: #2a2d3a; color: #8892b0; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; }
.badge-pcd { background: #1d3557; color: #a8dadc; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Estado local da sessão
# ─────────────────────────────────────────────
if "confirmar_reset" not in st.session_state:
    st.session_state.confirmar_reset = False

db = com_lock(_ler)
dia_ativo = db.get("dia_ativo")

# Recarrega dados guardados na URL para garantir persistência mesmo após o F5
url_user = st.query_params.get("user")
url_pcd = st.query_params.get("pcd") == "true"

if url_user and "nome_confirmado" not in st.session_state:
    st.session_state.nome_confirmado = url_user
    st.session_state.eh_pcd = url_pcd

# ─────────────────────────────────────────────
# PAINEL ADMIN (sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Admin")
    try:
        senha_correta = st.secrets["admin_pw"]
    except (KeyError, FileNotFoundError):
        senha_correta = "admin123"  
        st.caption("⚠️ Configure secrets.toml em produção.")

    pw = st.text_input("Senha", type="password", key="pw_admin")

    if pw == senha_correta:
        st.success("✅ Admin ativo")
        st.divider()

        st.markdown("**📅 Dia ativo**")
        try:
            val_inicial = date.fromisoformat(dia_ativo) if dia_ativo else datetime.now(FUSO_BR).date()
        except ValueError:
            val_inicial = datetime.now(FUSO_BR).date()

        dia_input = st.date_input("Selecione o dia do evento", value=val_inicial, key="dia_input")
        if st.button("✅ Confirmar dia ativo", use_container_width=True):
            definir_dia_ativo(dia_input.isoformat())
            st.rerun()

        if dia_ativo:
            st.info(f"Dia ativo: **{dia_ativo}**")

        st.divider()

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
                    st.markdown(f"**🕐 {slot}** — {len(inscritos)}/{VAGAS_TOTAL} vagas")
                    for p in inscritos:
                        badge_presenca = '<span class="badge-presente">✓ presente</span>' if p.get("presente", False) else '<span class="badge-ausente">aguardando</span>'
                        badge_pcd = '<span class="badge-pcd">PCD</span>' if p.get("pcd", False) else ''
                        st.markdown(
                            f'<div class="admin-row">'
                            f'<span class="admin-nome">👤 {p["nome"]} {badge_pcd}</span>'
                            f'{badge_presenca}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

        st.divider()

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

agora = datetime.now(FUSO_BR).strftime("%H:%M")

# ── ETAPA 1: Identificação (Se não houver nome na sessão atual nem na URL) ──
nome_confirmado_atual = st.session_state.get("nome_confirmado")

if not nome_confirmado_atual:
    st.markdown("**Digite seus dados para começar:**")
    
    nome_input = st.text_input(
        "Nome e Sobrenome",
        placeholder="Ex: Maria Silva"
    )
    
    marcou_pcd = st.checkbox("Sou Pessoa com Deficiência (PCD) - Possui direito a cotas de horário.")
    
    if st.button("Confirmar Dados", type="primary", use_container_width=True):
        partes = nome_input.strip().split()
        if len(partes) < 2:
            st.warning("⚠️ Digite nome e sobrenome.")
        else:
            nome_limpo = f"{partes[0].strip()} {' '.join(partes[1:]).strip()}"
            st.session_state.nome_confirmado = nome_limpo
            
            inscricao_existente = buscar_inscricao_por_nome(dia_ativo, nome_limpo)
            if inscricao_existente:
                st.session_state.eh_pcd = inscricao_existente["pcd"]
            else:
                st.session_state.eh_pcd = marcou_pcd
                
            # Salva os parâmetros na URL para sobreviver ao F5
            st.query_params["user"] = nome_limpo
            st.query_params["pcd"] = "true" if st.session_state.eh_pcd else "false"
            st.rerun()
    st.stop()

# Nome validado
nome_completo = st.session_state.nome_confirmado

# ── PERSISTÊNCIA CRÍTICA DA TELA DE CONFIRMAÇÃO ──
insc = buscar_inscricao_por_nome(dia_ativo, nome_completo)

if insc:
    slot_inscrito = insc["slot"]
    t_slot = datetime.strptime(slot_inscrito, "%H:%M")
    t_fim  = t_slot + timedelta(minutes=DURACAO_MIN)

    # Se o horário agendado NÃO expirou, fica preso aqui direto (mesmo após F5)
    if agora < t_fim.strftime("%H:%M"):
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
        
        st.write("") 
        if st.button("❌ Sair desta fila / Mudar horário", use_container_width=True):
            sucesso, msg = remover_inscricao(dia_ativo, slot_inscrito, insc["nome"])
            if sucesso:
                st.rerun()
            else:
                st.error(f"Erro ao cancelar: {msg}")
                
        st.stop()
    else:
        # Se o horário já passou, remove do JSON e limpa a URL para liberar um novo agendamento do zero
        remover_inscricao(dia_ativo, slot_inscrito, insc["nome"])
        st.query_params.clear()
        st.session_state.clear()
        st.info("Seu horário anterior expirou. Por favor, insira seus dados novamente para reagendar.")
        st.rerun()

# ── ETAPA 2: Escolha de horário ──
eh_pcd_usuario = st.session_state.eh_pcd
partes = nome_completo.split()
nome      = partes[0]
sobrenome = " ".join(partes[1:])

status_pcd_texto = " [PCD]" if eh_pcd_usuario else ""
st.markdown(f"Olá, **{nome_completo}**{status_pcd_texto}! Escolha um horário:")
if st.button("↩ Alterar cadastro", use_container_width=False):
    st.query_params.clear()
    st.session_state.clear()
    st.rerun()

st.divider()
st.markdown("#### Horários disponíveis")

sessoes_dia = db.get("sessoes", {}).get(dia_ativo, {})
slot_escolhido = None

for slot in SLOTS:
    inscritos = sessoes_dia.get(slot, [])
    total_ocupado = len(inscritos)
    vagas_totais_livres = VAGAS_TOTAL - total_ocupado
    passado = slot < agora

    if passado:
        classe_card = "slot-card slot-passado"
        desabilitado = True
        label = "Passado"
        txt_vagas = "Horário encerrado"
        classe_vagas = "slot-vagas-no"
    else:
        classe_card = "slot-card"
        
        if eh_pcd_usuario:
            vagas_visiveis = vagas_totais_livres
            desabilitado = (vagas_totais_livres == 0)
        else:
            vagas_visiveis = max(0, (VAGAS_TOTAL - VAGAS_RESERVADAS_PCD) - total_ocupado)
            desabilitado = (vagas_visiveis == 0)

        if vagas_totais_livres == 0:
            classe_vagas = "slot-vagas-no"
            txt_vagas = "Lotado"
            label = "Lotado"
        elif vagas_visiveis == 0 and not eh_pcd_usuario:
            classe_vagas = "slot-vagas-no"
            txt_vagas = "Restam apenas vagas PCD"
            label = "Bloqueado"
        elif vagas_visiveis <= 2:
            classe_vagas = "slot-vagas-mid"
            txt_vagas = f"Últimas {vagas_visiveis} vaga{'s' if vagas_visiveis > 1 else ''}"
            label = "Reservar"
        else:
            classe_vagas = "slot-vagas-ok"
            txt_vagas = f"{vagas_visiveis} vaga{'s' if vagas_visiveis > 1 else ''} disponível{'s' if vagas_visiveis > 1 else ''}"
            label = "Reservar"

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
        if st.button(label, key=f"btn_{slot}", disabled=desabilitado, use_container_width=True):
            slot_escolhido = slot

# ── Processar inscrição ──
if slot_escolhido:
    sucesso, msg = inscrever(dia_ativo, slot_escolhido, nome, sobrenome, eh_pcd_usuario)
    if sucesso:
        st.rerun()
    else:
        st.error(f"❌ {msg}")
