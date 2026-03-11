# Sistema de Marmitas

Sistema de pedidos para marmitaria com interface gráfica (PyQt6) e banco de dados local (SQLite).

## ✅ Objetivo
Executar e testar o sistema de forma rápida em qualquer máquina (Linux/Windows), incluindo:
- Instalar dependências (Python + PyQt6)
- Executar a aplicação (`app.py`)
- Rodar testes de fluxo sem UI (`test_sistema_clean.py`)

---

## 🔧 Pré-requisitos
- **Python 3.10+** instalado (recomendado 3.11+)
- Git (para clonar este repositório)

> 💡 No Linux, `python3` e `pip3` costumam vir instalados juntos.

---

## 🚀 Como rodar (modo rápido)
1. Clone este repositório:

```bash
git clone https://github.com/<seu_usuario>/<seu_repositorio>.git
cd "<nome_da_pasta>"  # normalmente "Sistema github"
```

2. Execute o setup (cria venv e instala dependências):

```bash
./setup.sh
```

3. Execute o aplicativo:

```bash
./run.sh
```

> ✅ Se tudo estiver correto, a interface gráfica do Sistema de Marmitas será exibida.

---

## 🧪 Como testar rapidamente (sem GUI)
O projeto inclui scripts para testar o fluxo de pedidos sem abrir a interface:

```bash
python test_sistema_clean.py
python test_sistema.py
```

Esses scripts:
- Criam (ou recriam) o banco de dados SQLite (`pedidos.db`)
- Inserem pratos de exemplo, geram pedidos e salvam no banco
- Imprimem um resumo no console

---

## 🧭 Arquivos principais
- `app.py` – interface gráfica
- `pratos.py` – cadastro/armazenamento de pratos (`storage.json`)
- `pedidos.py` – persistência de pedidos (SQLite)
- `config.py` – configurações simples (senha admin em `config.json`)
- `storage.json` – dados iniciais de pratos

---

## 📦 Dependências (requirements.txt)
- PyQt6
- pandas
- reportlab
- python-escpos

---

## 👥 Avisos importantes
- Não versionar `venv/` (já está no `.gitignore`).
- Se quiser começar com o projeto “limpo”, remova:

```bash
rm -rf venv/ pedidos.db debug.log relatorio_pedidos.csv
```

---

## 📄 Documentação adicional
- `DEPLOYMENT_GUIDE.txt`: guia de instalação e distribuição
- `GUIA_OPERACAO.txt`: guia de uso da aplicação
