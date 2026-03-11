#!/usr/bin/env bash
# Setup do projeto Marmitaria (cria venv e instala dependências)

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 não encontrado. Instale Python 3.10+ e tente novamente."
  exit 1
fi

if [ ! -f "requirements.txt" ]; then
  echo "❌ requirements.txt não encontrado. Execute este script na raiz do projeto."
  exit 1
fi

# Criar ambiente virtual
if [ ! -d "venv" ]; then
  echo "→ Criando ambiente virtual..."
  python3 -m venv venv
fi

# Ativar ambiente virtual
# shellcheck disable=SC1091
source "venv/bin/activate"

# Atualizar pip
echo "→ Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "→ Instalando dependências..."
pip install -r requirements.txt

# Garantir arquivos mínimos
if [ ! -f "storage.json" ]; then
  echo "→ Criando storage.json padrão..."
  cat > storage.json <<'EOF'
{
  "pratos": []
}
EOF
fi

# Criar run.sh se não existir
if [ ! -f "run.sh" ]; then
  cat > run.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Ativa venv (se existir)
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

python app.py
EOF
  chmod +x run.sh
fi

echo "\n✅ Configuração concluída!"
echo "→ Para executar: ./run.sh"
