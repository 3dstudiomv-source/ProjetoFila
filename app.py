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
# Constantes de horário e Regra de Vagas (Cotas)
# ─────────────────────────────────────────────
HORA_INICIO = 10          
HORA_FIM    = 20          
DURACAO_MIN = 30          

VAGAS_TOTAL = 10
VAGAS_PCD_EXCLUSIVAS = 2  # 20% de 10
VAGAS_GERAIS = 8          # 80% de 10

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

        # Contagem atual de ocupação
        total_inscritos = len(lista)
        inscritos_pcd = sum(1 for p in lista if p.get("pcd", False))
        inscritos_gerais = total_inscritos - inscritos_pcd

        if total_inscritos >= VAGAS_TOTAL:
            return False, "Este horário já está completamente lotado."

        # Regra de negócio para validação das vagas/cotas
        if eh_pcd:
            # PCDs têm direito a entrar enquanto houver vaga total, 
            # ocupando primeiro as suas exclusivas e depois as gerais.
            pass  
        else:
            # Usuário Geral só pode se inscrever se não tiver estourado o limite Geral (8)
            if inscritos_gerais >= VAGAS_GERAIS:
                return False, "Vagas gerais esgotadas. Restam apenas vagas exclusivas para PCD."

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
if "inscrito" not in st.session_state:
    st.session_state.inscrito = None
if "nome_confirmado" not in st.session_state:
    st.session_state.nome_confirmado = None  
if "eh_pcd" not in st.session_state:
    st.session_state.eh_pcd = False
if "confirmar_reset" not in st.session_state:
    st.session_state.confirmar_reset = False

db = com_lock(_ler)
dia_ativo = db.get("dia_ativo")

# ─────────────────────────────────────────────
# PAINEL ADMIN (sidebar)
# ─────────────────────────────────────────────
