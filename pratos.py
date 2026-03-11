# pratos.py
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO = BASE_DIR / "storage.json"

def _load_storage():
    if not ARQUIVO.exists():
        return {"pratos": []}
    with ARQUIVO.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_storage(data):
    with ARQUIVO.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def listar_pratos():
    data = _load_storage()
    return data.get("pratos", [])

def adicionar_prato(nome, preco, categoria="Marmita"):
    if not nome or preco is None:
        raise ValueError("Nome e preço são obrigatórios.")
    data = _load_storage()
    if any(p["nome"].lower() == nome.lower() for p in data["pratos"]):
        raise ValueError("Já existe um prato com esse nome.")
    data["pratos"].append({"nome": nome, "preco": float(preco), "categoria": categoria})
    _save_storage(data)
    return True

def remover_prato(nome):
    data = _load_storage()
    before = len(data["pratos"])
    data["pratos"] = [p for p in data["pratos"] if p["nome"].lower() != nome.lower()]
    _save_storage(data)
    return len(data["pratos"]) < before


def editar_prato(old_name, novo_nome, novo_preco, nova_categoria=None):
    """Edita um prato existente identificado pelo nome antigo.
    Retorna True se encontrado e atualizado, False caso contrário.
    """
    data = _load_storage()
    updated = False
    for p in data.get("pratos", []):
        if p.get("nome", "").lower() == old_name.lower():
            p["nome"] = novo_nome
            p["preco"] = float(novo_preco)
            if nova_categoria is not None:
                p["categoria"] = nova_categoria
            updated = True
            break
    if updated:
        _save_storage(data)
    return updated