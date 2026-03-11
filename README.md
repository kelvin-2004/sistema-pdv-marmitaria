<<<<<<< HEAD
# Sistema de Marmitas

Sistema de pedidos para marmitaria com interface gráfica (PyQt6) e banco de dados local.

## ✅ Objetivo
Fornecer uma forma rápida de executar e testar o sistema em qualquer máquina (Linux/Windows), incluindo:
- Instalar dependências (Python + PyQt6)
- Executar a aplicação (`app.py`)
- Executar testes de integração rápida (`test_sistema_clean.py`)

---

## 🔧 Pré-requisitos
- **Python 3.10+** instalado (recomendado 3.11+)
- Git (para clonar este repositório)

> 💡 No Linux, a instalação do Python normalmente vem com `python3` e `pip3`.

---

## 🚀 Como rodar (modo rápido)
1. Clone este repositório:

```bash
git clone https://github.com/<seu_usuario>/<seu_repositorio>.git
cd "Sistema github"  # ou nome da pasta criada pelo git clone
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

## 📤 Publicar no GitHub
Se você ainda não tem um repositório no GitHub, crie um e, a partir da raiz do projeto, execute:

```bash
git init
git add .
git commit -m "Inicializar projeto Sistema de Marmitas"
# Substitua as URLs abaixo pela URL do seu repositório
git remote add origin https://github.com/<seu_usuario>/<seu_repositorio>.git
git push -u origin main
```

> ⚠️ Ajuste o nome da branch (`main`/`master`) conforme sua configuração.

---

## 🧪 Como testar rapidamente
O repositório inclui scripts de teste que simulam um fluxo completo de pedido sem abrir a GUI.

```bash
python test_sistema_clean.py
```

Esses scripts:
- Criam (ou recriam) o banco de dados SQLite (`pedidos.db`)
- Inserem pratos de exemplo, geram pedidos e salvam no banco
- Imprimem um resumo no console

---

## 🗂️ Estrutura principal do projeto

- `app.py` & `main.py`: entrada principal da aplicação (GUI)
- `pratos.py`, `pedidos.py`, `pedido.py`: lógica de negócio
- `admin_panel.py`: painel de administração (cadastro de pratos, relatórios, etc)
- `config.py`: configurações (senha de admin e caminhos de arquivos)
- `pedidos.db`: banco de dados SQLite (gera na primeira execução)

---

## 📦 Dependências
Dependências principais (listadas em `requirements.txt`):
- PyQt6
- pandas
- reportlab
- python-escpos

---

## 👥 Contribuindo / Testando em outro computador
- Certifique-se de que o `venv/` NÃO está versionado (veja `.gitignore`).
- Ao clonar, crie um novo ambiente virtual e instale as dependências.

---

## 📝 Notas úteis
- Na primeira vez que acessar o **Painel Admin**, o sistema pedirá para configurar uma senha de administrador.
- O arquivo de configuração `config.json` fica na raiz do projeto e contém o hash da senha.
- O banco de dados `pedidos.db` também é gerado na raiz do projeto.

---

## 📄 Documentação adicional
- `DEPLOYMENT_GUIDE.txt`: guia de instalação e distribuição
- `GUIA_OPERACAO.txt`: guia de uso da aplicação

---

## 💡 Dica (Windows)
Em Windows, se houver problemas com acentuação ou encoding, abra o PowerShell e execute:

```powershell
chcp 65001
```
=======
# sistema-pdv-marmitaria
Sistema de Marmitas — Aplicativo de gestão de pedidos para marmitaria com interface gráfica (PyQt6) e banco de dados local (SQLite), feito para facilitar o cadastro de pratos, emissão de comandas e controle de pedidos.
>>>>>>> 9a3e0444a82af8300de7acb5f194c65f0269f228
