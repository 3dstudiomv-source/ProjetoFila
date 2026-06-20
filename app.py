import streamlit as st
import json
import os
import logging
import threading
from pathlib import Path
from datetime import datetime, date, timedelta

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

# Lock em memória para evitar colisões entre threads do Streamlit
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
# Constantes de horário
# ─────────────────────────────────────────────
HORA_INICIO = 10          
HORA_FIM    = 20          
DURACAO_MIN = 30          
VAGAS_POR_SESSAO = 10

@st.cache_data
def gerar_slots() -> list[str]:
    """Gera e faz cache da lista de horários fixos."""
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
        # Escrita atômica: salva num arquivo temporário e renomeia
        temp_file = ARQ.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(ARQ)
    except IOError as e:
        logger.error("Erro ao salvar JSON: %s", e)
        raise

def com_lock(fn, *args, **kwargs):
    """Garante thread-safety usando threading.Lock nativo."""
    with _db_lock:
        return fn(*args, **kwargs)

# ─────────────────────────────────────────────
# Operações de negócio
# ─────────────────────────────────────────────
def inscrever(dia: str, slot: str, nome: str, sobrenome: str) -> tuple[bool, str]:
    def _op():
        db = _ler()
        sessoes_dia = db["sessoes"].setdefault(dia, {})
        lista = sessoes_dia.setdefault(slot, [])

        if len(lista) >= VAGAS_POR_SESSAO:
            return False, "Este horário já está lotado."

        nome_completo = f"{nome.strip()} {sobrenome.strip()}"
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

# ─────────────────────────────────────────────
# CSS customizado
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://
