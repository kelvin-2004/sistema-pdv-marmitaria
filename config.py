# config.py
"""Configuração do sistema e armazenamento de dados sensíveis.

Este módulo centraliza o caminho de arquivos usados para armazenamento local
(e.g., banco de dados, configurações de usuário) e fornece helpers simples para
carregar/salvar configurações.
"""

import json
from pathlib import Path
from hashlib import sha256
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_config(data: dict):
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_admin_password_hash() -> Optional[str]:
    """Retorna o hash da senha de administrador ou None se ainda não foi configurada."""
    cfg = _load_config()
    return cfg.get("admin_password_hash")


def set_admin_password(password: str):
    """Configura a senha de administrador (armazenada como hash)."""
    cfg = _load_config()
    cfg["admin_password_hash"] = sha256(password.encode("utf-8")).hexdigest()
    _save_config(cfg)


def verify_admin_password(password: str) -> bool:
    """Verifica se a senha fornecida corresponde à senha de administrador."""
    current = get_admin_password_hash()
    if not current:
        return False
    return sha256(password.encode("utf-8")).hexdigest() == current
