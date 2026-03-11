import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFormLayout, QLineEdit, QPushButton,
    QVBoxLayout, QLabel, QComboBox, QTextEdit, QMessageBox, QHBoxLayout,
    QScrollArea, QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem, QDialog,
    QDoubleSpinBox
)
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

import pratos
import pedidos
import printer
from config import get_admin_password_hash
from admin_panel import AdminPanel, PasswordDialog

# Arquivo de log para debug (no diretório do projeto)
LOG_FILE = str(Path(__file__).resolve().parent / "debug.log")

def log_debug(msg):
    """Registra mensagem de debug no arquivo e no console"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass


# ===============================================
# ESTILOS
# ===============================================
MAIN_STYLESHEET = """
    QMainWindow {
        background-color: #ffffff;
    }
    QPushButton {
        background-color: #2E86DE;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        font-size: 12pt;
    }
    QPushButton:hover {
        background-color: #1E5BA8;
    }
    QPushButton[objectName="btnSecondary"] {
        background-color: #95A5A6;
    }
    QPushButton[objectName="btnSecondary"]:hover {
        background-color: #7F8C8D;
    }
    QPushButton[objectName="btnSuccess"] {
        background-color: #26A65B;
    }
    QPushButton[objectName="btnSuccess"]:hover {
        background-color: #1E8449;
    }
"""

MENU_STYLESHEET = """
    QWidget {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    QLabel {
        color: white;
        font-size: 28pt;
        font-weight: bold;
        margin-bottom: 30px;
    }
    QPushButton {
        background-color: #2E86DE;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        font-size: 14pt;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #1E5BA8;
    }
    QPushButton[objectName="btnAdmin"] {
        background-color: #E74C3C;
    }
    QPushButton[objectName="btnAdmin"]:hover {
        background-color: #C0392B;
    }
"""

FORM_STYLESHEET = """
    QWidget {
        background-color: #ffffff;
    }
    QLabel {
        color: #2C3E50;
        font-size: 11pt;
    }
    QLineEdit, QSpinBox, QComboBox {
        background-color: #ECF0F1;
        border: 2px solid #BDC3C7;
        border-radius: 5px;
        padding: 5px;
        font-size: 11pt;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 2px solid #2E86DE;
        background-color: #ffffff;
    }
    QTextEdit {
        background-color: #ECF0F1;
        border: 2px solid #BDC3C7;
        border-radius: 5px;
        padding: 5px;
        font-family: monospace;
    }
    QPushButton {
        background-color: #2E86DE;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #1E5BA8;
    }
    QPushButton[objectName="btnSecondary"] {
        background-color: #95A5A6;
    }
    QPushButton[objectName="btnSecondary"]:hover {
        background-color: #7F8C8D;
    }
    QPushButton[objectName="btnSuccess"] {
        background-color: #26A65B;
    }
    QPushButton[objectName="btnSuccess"]:hover {
        background-color: #1E8449;
    }
"""


# ===============================================
# MENU PRINCIPAL
# ===============================================
class MenuPrincipal(QWidget):
    def __init__(self, novo_pedido_callback, admin_callback):
        super().__init__()
        self.setStyleSheet(MENU_STYLESHEET)
        self.novo_pedido_callback = novo_pedido_callback
        self.admin_callback = admin_callback
        
        layout = QVBoxLayout()
        layout.addStretch()

        titulo = QLabel("Sistema de Marmitas - Kelvin")
        layout.addWidget(titulo)

        layout.addStretch()

        btn_novo = QPushButton("Novo Pedido")
        btn_novo.setFixedHeight(80)
        btn_novo.clicked.connect(novo_pedido_callback)
        layout.addWidget(btn_novo)

        btn_admin = QPushButton("Painel Admin")
        btn_admin.setObjectName("btnAdmin")
        btn_admin.setFixedHeight(80)
        btn_admin.clicked.connect(admin_callback)
        layout.addWidget(btn_admin)

        layout.addStretch()
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("1"), self, novo_pedido_callback)
        QShortcut(QKeySequence("2"), self, admin_callback)


# ===============================================
# FORMULÁRIO DE CLIENTE
# ===============================================
class ClienteForm(QWidget):
    def __init__(self, continuar_callback, voltar_callback=None):
        super().__init__()
        self.setStyleSheet(FORM_STYLESHEET)
        self.voltar_callback = voltar_callback
        self.continuar_callback = continuar_callback
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Nome do Cliente")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Formulário
        form = QFormLayout()
        form.setSpacing(10)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Ex: João Silva")
        self.nome.setMinimumHeight(35)
        self.nome.setFocus()
        # Conectar Enter para continuar
        self.nome.returnPressed.connect(self._on_continuar)

        form.addRow("Nome:", self.nome)

        layout.addLayout(form)
        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.setMinimumHeight(45)
        btn_voltar.setMinimumWidth(120)
        btn_voltar.clicked.connect(self._on_voltar)
        
        btn_continuar = QPushButton("✓ Continuar")
        btn_continuar.setObjectName("btnSuccess")
        btn_continuar.setMinimumHeight(45)
        btn_continuar.setMinimumWidth(150)
        btn_continuar.clicked.connect(self._on_continuar)
        
        btn_layout.addWidget(btn_voltar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_continuar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalho para Esc = Voltar
        QShortcut(QKeySequence("Escape"), self, self._on_voltar)

    def _on_voltar(self):
        if self.voltar_callback:
            self.voltar_callback()

    def _on_continuar(self):
        data = self.get_data()
        if not data.get('nome'):
            QMessageBox.warning(self, "Validação", "Nome é obrigatório!")
            return
        self.continuar_callback(data)

    def get_data(self):
        return {
            'nome': self.nome.text(),
            'celular': '',
            'endereco': '',
            'numero': 0,
            'bairro': '',
            'cep': '',
            'obs': '',
        }


# ===============================================
# SELETOR DE QUANTIDADE POR CATEGORIA
# ===============================================
class QuantidadeWidget(QWidget):
    def __init__(self, pratos_dict):
        super().__init__()
        self.pratos_dict = pratos_dict
        self.quantities = {prato_id: 0 for prato_id in pratos_dict}
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Agrupar pratos por categoria e ordenar alfabeticamente
        categorias = {}
        for prato_id, prato_info in pratos_dict.items():
            categoria = prato_info.get('categoria', 'Outros')
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append((prato_id, prato_info))
        
        # Definir ordem de categorias
        ordem_categorias = ['Marmita', 'Bebidas', 'Combo', 'Sobremesas', 'Outros']
        categorias_ordenadas = {cat: categorias[cat] for cat in ordem_categorias if cat in categorias}
        
        # Adicionar categorias não listadas
        for cat in categorias:
            if cat not in ordem_categorias:
                categorias_ordenadas[cat] = categorias[cat]
        
        # Criar grupos por categoria
        for categoria, pratos_list in categorias_ordenadas.items():
            # Título da categoria
            titulo_cat = QLabel(categoria.upper())
            titulo_cat.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2E86DE; margin-top: 10px;")
            layout.addWidget(titulo_cat)
            
            # Ordenar pratos alfabeticamente dentro da categoria
            pratos_list_sorted = sorted(pratos_list, key=lambda x: x[1]['nome'])
            
            # Adicionar pratos da categoria verticalmente
            prato_layout = QVBoxLayout()
            prato_layout.setSpacing(10)
            prato_layout.setContentsMargins(10, 5, 10, 5)
            
            for idx, (prato_id, prato_info) in enumerate(pratos_list_sorted):
                # Criar grupo do prato (botão + spinner) em horizontal
                item_layout = QHBoxLayout()
                item_layout.setSpacing(10)
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                # Botão para selecionar prato
                btn_prato = QPushButton(f"{prato_info['nome']} - R$ {prato_info['preco']:.2f}")
                btn_prato.setMinimumHeight(50)
                btn_prato.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_prato.setStyleSheet("""
                    QPushButton {
                        background-color: #3498DB;
                        color: white;
                        border: 2px solid #2980B9;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 11pt;
                        padding: 5px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #2980B9;
                    }
                    QPushButton:pressed {
                        background-color: #1F618D;
                    }
                """)
                
                # Spinner para quantidade
                spinner = QSpinBox()
                spinner.setMinimum(0)
                spinner.setMaximum(100)
                spinner.setValue(0)
                spinner.setMinimumHeight(50)
                spinner.setMaximumWidth(100)
                spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
                spinner.setStyleSheet("""
                    QSpinBox {
                        font-size: 12pt;
                        font-weight: bold;
                        padding: 5px;
                    }
                """)
                spinner.valueChanged.connect(lambda v, pid=prato_id: self.set_quantity(pid, v))
                self.quantities[prato_id] = spinner
                
                # Conexão do botão para incrementar quantidade
                btn_prato.clicked.connect(lambda pid=prato_id: self._increment_quantity(pid))
                
                item_layout.addWidget(btn_prato)
                item_layout.addWidget(spinner)
                
                prato_layout.addLayout(item_layout)
        
        layout.addStretch()
        self.setLayout(layout)

    def _increment_quantity(self, prato_id):
        """Incrementa a quantidade quando o botão é clicado"""
        spinner = self.quantities[prato_id]
        if isinstance(spinner, QSpinBox):
            spinner.setValue(spinner.value() + 1)

    def set_quantity(self, prato_id, qty):
        self.quantities[prato_id] = qty

    def get_items(self):
        items = []
        for prato_id, qty_widget in self.quantities.items():
            if isinstance(qty_widget, QSpinBox):
                qty = qty_widget.value()
            else:
                qty = qty_widget
            
            if qty > 0:
                prato_info = self.pratos_dict[prato_id]
                items.append({
                    'id': prato_id,
                    'nome': prato_info['nome'],
                    'preco': prato_info['preco'],
                    'quantidade': qty,
                    'subtotal': prato_info['preco'] * qty
                })
        return items


# ===============================================
# DIALOG DE EXCEÇÃO
# ===============================================
class ExcecaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Exceção")
        self.setGeometry(300, 300, 450, 250)
        self.setStyleSheet(FORM_STYLESHEET)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Adicionar Exceção")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #E74C3C;")
        layout.addWidget(titulo)

        # Formulário
        form = QFormLayout()
        form.setSpacing(10)

        # Campo de descrição
        self.descricao = QLineEdit()
        self.descricao.setPlaceholderText("Ex: Marmita especial, bebida premium")
        self.descricao.setMinimumHeight(35)
        self.descricao.setFocus()
        form.addRow("Descrição:", self.descricao)

        # Campo de valor
        self.valor = QDoubleSpinBox()
        self.valor.setMinimum(0.0)
        self.valor.setMaximum(9999.99)
        self.valor.setValue(0.0)
        self.valor.setDecimals(2)
        self.valor.setPrefix("R$ ")
        self.valor.setMinimumHeight(35)
        self.valor.setSingleStep(0.50)
        form.addRow("Valor:", self.valor)

        layout.addLayout(form)
        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_cancelar = QPushButton("✕ Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)

        btn_ok = QPushButton("✓ Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.setMinimumHeight(40)
        btn_ok.clicked.connect(self._validar_e_confirmar)

        btn_layout.addWidget(btn_cancelar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Return"), self, self._validar_e_confirmar)
        QShortcut(QKeySequence("Escape"), self, self.reject)

    def _validar_e_confirmar(self):
        """Valida os campos antes de confirmar"""
        if not self.descricao.text().strip():
            QMessageBox.warning(self, "Validação", "Descrição é obrigatória!")
            self.descricao.setFocus()
            return
        
        if self.valor.value() <= 0:
            QMessageBox.warning(self, "Validação", "Valor deve ser maior que zero!")
            self.valor.setFocus()
            return
        
        self.accept()

    def get_dados(self):
        """Retorna descrição e valor"""
        return {
            'descricao': self.descricao.text().strip(),
            'valor': self.valor.value()
        }


# ===============================================
# DIALOG DE OBSERVAÇÃO DE ITEM
# ===============================================
class ObservacaoDialog(QDialog):
    def __init__(self, nome_item, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Observação - {nome_item}")
        self.setGeometry(300, 300, 500, 250)
        self.setStyleSheet(FORM_STYLESHEET)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel(f"Observação para: {nome_item}")
        titulo.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Instrução
        instrucao = QLabel("Digite observações específicas para este item (ex: sem feijão, sem cebola)")
        instrucao.setStyleSheet("font-size: 10pt; color: #7F8C8D;")
        layout.addWidget(instrucao)

        # Campo de observação (TextEdit para múltiplas linhas)
        self.observacao = QTextEdit()
        self.observacao.setPlaceholderText("Ex: sem feijão, sem cebola, bem quente")
        self.observacao.setMinimumHeight(100)
        self.observacao.setFocus()
        layout.addWidget(self.observacao)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_limpar = QPushButton("🗑️  Limpar")
        btn_limpar.setObjectName("btnSecondary")
        btn_limpar.setMinimumHeight(40)
        btn_limpar.clicked.connect(self.observacao.clear)
        btn_layout.addWidget(btn_limpar)

        btn_cancelar = QPushButton("✕ Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)

        btn_ok = QPushButton("✓ Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.setMinimumHeight(40)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Return"), self, self.accept)
        QShortcut(QKeySequence("Escape"), self, self.reject)

    def get_observacao(self):
        """Retorna a observação digitada"""
        return self.observacao.toPlainText().strip()


# ===============================================
# DIALOG DE SELEÇÃO DE ITENS POR CATEGORIA
# ===============================================
class SelecionarItensDialog(QDialog):
    def __init__(self, categoria, pratos_dict, parent=None, observacoes_permanentes=None):
        super().__init__(parent)
        self.setWindowTitle(f"Selecionar {categoria}")
        self.setGeometry(100, 100, 600, 600)
        self.setStyleSheet(FORM_STYLESHEET)
        
        self.categoria = categoria
        self.pratos_dict = pratos_dict
        self.quantities = {}
        # CORREÇÃO: Criar uma CÓPIA do dicionário em vez de uma referência
        # Isso evita problemas quando o usuário cancela a seleção mas já adicionou observações
        self.observacoes = dict(observacoes_permanentes) if observacoes_permanentes is not None else {}
        
        # Paleta de cores para os itens
        cores = [
            "#FF6B6B",  # Vermelho
            "#4ECDC4",  # Turquesa
            "#45B7D1",  # Azul claro
            "#FFA07A",  # Salmão
            "#98D8C8",  # Menta
            "#F7DC6F",  # Amarelo
            "#BB8FCE",  # Roxo
            "#85C1E2",  # Azul pastel
            "#F8B739",  # Laranja
            "#52C4B8",  # Verde azulado
            "#FF8C9B",  # Rosa
            "#82E0AA",  # Verde claro
            "#85A5D9",  # Azul indigo
            "#F5B041",  # Ouro
            "#D7BDE2",  # Lavanda
            "#A9DFBF",  # Verde menta
        ]
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Título
        titulo = QLabel(f"Selecione itens de {categoria}")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Scroll area com itens da categoria
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(10)
        
        # Filtrar pratos da categoria
        pratos_categoria = [
            (pid, pinfo) for pid, pinfo in pratos_dict.items()
            if pinfo.get('categoria', 'Outros').lower() == categoria.lower()
        ]
        
        # Ordenar alfabeticamente
        pratos_categoria_sorted = sorted(pratos_categoria, key=lambda x: x[1]['nome'])
        
        for idx, (prato_id, prato_info) in enumerate(pratos_categoria_sorted):
            # Obter cor para este item (repete se necessário)
            cor = cores[idx % len(cores)]
            
            # Layout horizontal para cada prato
            item_layout = QHBoxLayout()
            item_layout.setSpacing(10)
            item_layout.setContentsMargins(10, 5, 10, 5)
            
            # Label com nome e preço com fundo colorido
            label = QLabel(f"{prato_info['nome']} - R$ {prato_info['preco']:.2f}")
            label.setMinimumHeight(45)
            label.setStyleSheet(f"""
                QLabel {{
                    background-color: {cor};
                    color: white;
                    font-size: 11pt;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 5px;
                    border: 2px solid rgba(0, 0, 0, 0.3);
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
                }}
            """)
            item_layout.addWidget(label)
            
            # Spinner para quantidade
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(100)
            spinner.setValue(0)
            spinner.setMinimumHeight(45)
            spinner.setMaximumWidth(120)
            spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.quantities[prato_id] = spinner
            item_layout.addWidget(spinner)
            
            # Botão para adicionar observação
            btn_obs = QPushButton("📝 Obs.")
            btn_obs.setMinimumHeight(45)
            btn_obs.setMaximumWidth(100)
            btn_obs.setStyleSheet("""
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: 2px solid #7F8C8D;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #7F8C8D;
                }
                QPushButton:pressed {
                    background-color: #6C7A7D;
                }
            """)
            log_debug(f"[SelecionarItensDialog loop] Criando botão obs para prato_id={prato_id}, nome={prato_info['nome']}")
            # Usar função parcial para capturar o prato_id corretamente
            from functools import partial
            btn_obs.clicked.connect(partial(self._abrir_observacao, prato_id, prato_info['nome']))
            item_layout.addWidget(btn_obs)
            
            scroll_layout.addLayout(item_layout)
        
        scroll_layout.addStretch()
        
        scroll_widget = QWidget()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("✕ Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_ok = QPushButton("✓ Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.setMinimumHeight(40)
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Escape"), self, self.reject)
    
    def _abrir_observacao(self, prato_id, nome_prato):
        """Abre diálogo para adicionar observação a um prato"""
        dialog = ObservacaoDialog(nome_prato, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            obs = dialog.get_observacao()
            print(f"[_abrir_observacao] prato_id={prato_id}, nome={nome_prato}, obs digitada='{obs}'")
            if obs:
                self.observacoes[prato_id] = obs
                print(f"[_abrir_observacao] Observação salva! self.observacoes agora é: {self.observacoes}")
            elif prato_id in self.observacoes:
                # Se deixou em branco, remove observação anterior
                del self.observacoes[prato_id]
                print(f"[_abrir_observacao] Observação removida")
    
    def get_items(self):
        """Retorna itens selecionados (com quantidade > 0)"""
        items = []
        for prato_id, spinner in self.quantities.items():
            qty = spinner.value()
            if qty > 0:
                prato_info = self.pratos_dict[prato_id]
                item = {
                    'id': prato_id,
                    'nome': prato_info['nome'],
                    'preco': prato_info['preco'],
                    'quantidade': qty,
                    'subtotal': prato_info['preco'] * qty
                }
                # Adicionar observação se existir
                if prato_id in self.observacoes:
                    item['observacao'] = self.observacoes[prato_id]
                    print(f"[get_items] {item['nome']}: observacao={item['observacao']}")
                else:
                    print(f"[get_items] {item['nome']}: SEM observacao (prato_id={prato_id}, observacoes={list(self.observacoes.keys())})")
                items.append(item)
        print(f"[get_items] Items retornados: {[(item['nome'], item.get('observacao', 'SEM OBS')) for item in items]}")
        return items


# ===============================================
# SELETOR DE PRATOS
# ===============================================
class PratosForm(QWidget):
    def __init__(self, continuar_callback, voltar_callback):
        super().__init__()
        self.setStyleSheet(FORM_STYLESHEET)
        self.continuar_callback = continuar_callback
        self.voltar_callback = voltar_callback
        
        # Carregar pratos
        pratos_list = pratos.listar_pratos()
        self.pratos_dict = {i: {**p, 'id': i} for i, p in enumerate(pratos_list)}
        
        # Dicionário para armazenar itens selecionados
        self.itens_selecionados = {}
        # Dicionário para armazenar observações por prato_id (mantém entre categorias)
        self.observacoes_permanentes = {}
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("Selecione a Categoria")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)
        
        # Subtítulo
        subtitulo = QLabel("Pressione 1, 2 ou 3 para selecionar a categoria")
        subtitulo.setStyleSheet("font-size: 11pt; color: #7F8C8D;")
        layout.addWidget(subtitulo)
        
        layout.addStretch()
        
        # Botões das categorias
        categorias_layout = QVBoxLayout()
        categorias_layout.setSpacing(15)
        categorias_layout.setContentsMargins(40, 40, 40, 40)
        
        # Marmita (1)
        btn_marmita = QPushButton("1️⃣  MARMITA")
        btn_marmita.setMinimumHeight(80)
        btn_marmita.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: 3px solid #2980B9;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        btn_marmita.clicked.connect(lambda: self._abrir_categoria("Marmita"))
        categorias_layout.addWidget(btn_marmita)
        
        # Bebida (2)
        btn_bebida = QPushButton("2️⃣  BEBIDA")
        btn_bebida.setMinimumHeight(80)
        btn_bebida.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: 3px solid #8E44AD;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:pressed {
                background-color: #6C3483;
            }
        """)
        btn_bebida.clicked.connect(lambda: self._abrir_categoria("Bebida"))
        categorias_layout.addWidget(btn_bebida)
        
        # Combo (3)
        btn_combo = QPushButton("3️⃣  COMBO")
        btn_combo.setMinimumHeight(80)
        btn_combo.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border: 3px solid #D35400;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
            QPushButton:pressed {
                background-color: #BA4A00;
            }
        """)
        btn_combo.clicked.connect(lambda: self._abrir_categoria("Combo"))
        categorias_layout.addWidget(btn_combo)
        
        # Exceção (4)
        btn_excecao = QPushButton("4️⃣  EXCEÇÃO")
        btn_excecao.setMinimumHeight(80)
        btn_excecao.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: 3px solid #C0392B;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        btn_excecao.clicked.connect(lambda: self._abrir_excecao())
        categorias_layout.addWidget(btn_excecao)
        
        # Adicionar os atalhos de teclado
        QShortcut(QKeySequence("1"), self, lambda: self._abrir_categoria("Marmita"))
        QShortcut(QKeySequence("2"), self, lambda: self._abrir_categoria("Bebida"))
        QShortcut(QKeySequence("3"), self, lambda: self._abrir_categoria("Combo"))
        QShortcut(QKeySequence("4"), self, lambda: self._abrir_excecao())
        
        layout.addLayout(categorias_layout)
        layout.addStretch()

        # Botões inferiores
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.setMinimumHeight(45)
        btn_voltar.setMinimumWidth(120)
        btn_voltar.clicked.connect(voltar_callback)
        
        btn_continuar = QPushButton("✓ Continuar")
        btn_continuar.setObjectName("btnSuccess")
        btn_continuar.setMinimumHeight(45)
        btn_continuar.setMinimumWidth(150)
        btn_continuar.clicked.connect(self._on_continuar)
        
        btn_layout.addWidget(btn_voltar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_continuar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Escape"), self, voltar_callback)
    
    def _abrir_categoria(self, categoria):
        """Abre dialog para selecionar itens da categoria"""
        dialog = SelecionarItensDialog(categoria, self.pratos_dict, self, self.observacoes_permanentes)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Adicionar/atualizar itens selecionados
            novos_itens = dialog.get_items()
            print(f"[_abrir_categoria] Novos itens recebidos do dialog: {[(i['nome'], i.get('observacao', 'SEM OBS')) for i in novos_itens]}")
            for item in novos_itens:
                self.itens_selecionados[item['id']] = item
                print(f"[_abrir_categoria] Armazenado {item['nome']} com obs={item.get('observacao', 'SEM OBS')}")
            # Atualizar observações permanentes com as do diálogo
            print(f"[_abrir_categoria] Observações do diálogo: {dialog.observacoes}")
            self.observacoes_permanentes.update(dialog.observacoes)
            print(f"[_abrir_categoria] Observações permanentes após update: {self.observacoes_permanentes}")
    
    def _abrir_excecao(self):
        """Abre dialog para adicionar uma exceção (item customizado)"""
        try:
            dialog = ExcecaoDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                dados = dialog.get_dados()
                # Gerar um ID único para a exceção
                excecao_id = f"excecao_{len(self.itens_selecionados)}"
                self.itens_selecionados[excecao_id] = {
                    'id': excecao_id,
                    'nome': dados['descricao'],
                    'preco': dados['valor'],
                    'quantidade': 1,
                    'subtotal': dados['valor']
                }
                QMessageBox.information(self, "Sucesso", f"Exceção '{dados['descricao']}' adicionada!")
        except Exception as e:
            print(f"Erro ao abrir exceção: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar exceção: {str(e)}")
    
    def _on_continuar(self):
        if not self.itens_selecionados:
            QMessageBox.warning(self, "Validação", "Selecione pelo menos 1 item!")
            return
        # Os itens já devem ter observações (vindas de get_items do dialog)
        items = []
        for item in self.itens_selecionados.values():
            # Fazer cópia do item (que já pode ter observação)
            item_com_obs = item.copy()
            print(f"[_on_continuar PratosForm] Item: {item['nome']}, observacao atual: {item_com_obs.get('observacao', 'SEM OBS')}")
            items.append(item_com_obs)
        print(f"[_on_continuar PratosForm] Items sendo passados: {[(i['nome'], i.get('observacao', 'SEM OBS')) for i in items]}")
        self.continuar_callback(items)


# ===============================================
# FORMULÁRIO DE ENDEREÇO
# ===============================================
class EnderecoForm(QWidget):
    def __init__(self, continuar_callback, voltar_callback, cliente_data=None):
        super().__init__()
        self.setStyleSheet(FORM_STYLESHEET)
        self.continuar_callback = continuar_callback
        self.voltar_callback = voltar_callback
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Endereço de Entrega")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Formulário
        form = QFormLayout()
        form.setSpacing(10)

        self.endereco = QLineEdit()
        self.endereco.setPlaceholderText("Ex: Rua das Flores")
        self.endereco.setMinimumHeight(35)
        
        self.numero = QSpinBox()
        self.numero.setMinimum(0)
        self.numero.setMaximum(9999)
        self.numero.setValue(0)
        self.numero.setMinimumHeight(35)
        self.numero.setFocus()
        
        self.bairro = QLineEdit()
        self.bairro.setPlaceholderText("Ex: Centro")
        self.bairro.setMinimumHeight(35)
        
        self.cep = QLineEdit()
        self.cep.setInputMask("00000-000")
        self.cep.setPlaceholderText("00000-000")
        self.cep.setMinimumHeight(35)
        
        self.obs = QLineEdit()
        self.obs.setPlaceholderText("Ex: Prédio, casa no fundo")
        self.obs.setMinimumHeight(35)
        
        self.celular = QLineEdit()
        self.celular.setPlaceholderText("(00) 00000-0000")
        self.celular.setMinimumHeight(35)
        self.celular.textChanged.connect(self._format_phone)
        # Conectar Enter para continuar
        self.celular.returnPressed.connect(self._on_continuar)

        form.addRow("Endereço:", self.endereco)
        form.addRow("Número:", self.numero)
        form.addRow("Bairro:", self.bairro)
        form.addRow("CEP:", self.cep)
        form.addRow("Celular:", self.celular)
        form.addRow("Observações:", self.obs)

        layout.addLayout(form)
        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.setMinimumHeight(45)
        btn_voltar.setMinimumWidth(120)
        btn_voltar.clicked.connect(self._on_voltar)
        
        btn_continuar = QPushButton("✓ Continuar")
        btn_continuar.setObjectName("btnSuccess")
        btn_continuar.setMinimumHeight(45)
        btn_continuar.setMinimumWidth(150)
        btn_continuar.clicked.connect(self._on_continuar)
        
        btn_layout.addWidget(btn_voltar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_continuar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Return"), self, self._on_continuar)
        QShortcut(QKeySequence("Escape"), self, self._on_voltar)

    def _format_phone(self):
        """Formata telefone como (XX) XXXXX-XXXX"""
        text = ''.join(c for c in self.celular.text() if c.isdigit())
        self.celular.blockSignals(True)
        
        if len(text) <= 2:
            formatted = f"({text}" if text else ""
        elif len(text) <= 7:
            formatted = f"({text[:2]}) {text[2:]}"
        else:
            text = text[:11]
            formatted = f"({text[:2]}) {text[2:7]}-{text[7:]}"
        
        self.celular.setText(formatted)
        self.celular.blockSignals(False)

    def _on_voltar(self):
        if self.voltar_callback:
            self.voltar_callback()

    def _on_continuar(self):
        data = self.get_data()
        self.continuar_callback(data)

    def get_data(self):
        return {
            'endereco': self.endereco.text(),
            'numero': self.numero.value(),
            'bairro': self.bairro.text(),
            'cep': self.cep.text(),
            'celular': self.celular.text(),
            'obs': self.obs.text()
        }


# ===============================================
# FORMULÁRIO DE PAGAMENTO
# ===============================================
class PagamentoForm(QWidget):
    def __init__(self, continuar_callback, voltar_callback, total_pedido=0, dados_anteriores=None):
        super().__init__()
        self.setStyleSheet(FORM_STYLESHEET)
        self.continuar_callback = continuar_callback
        self.voltar_callback = voltar_callback
        self.total_pedido = total_pedido
        self.dados_anteriores = dados_anteriores or {}
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Forma de Pagamento")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)
        
        # Mostrar o total do pedido (será atualizado quando taxa mudar)
        self.total_label = QLabel(f"Total do Pedido: R$ {total_pedido:.2f}")
        self.total_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #26A65B;")
        layout.addWidget(self.total_label)

        # Formulário
        form = QFormLayout()
        form.setSpacing(10)

        self.pagamento = QComboBox()
        self.pagamento.addItems(["Dinheiro", "PIX", "Cartão", "Já foi pago no PIX", "Fiado"])
        self.pagamento.setMinimumHeight(35)
        self.pagamento.currentTextChanged.connect(self._on_pagamento_changed)
        form.addRow("Pagamento:", self.pagamento)

        self.valor_recebido = QLineEdit()
        self.valor_recebido.setPlaceholderText("R$ 0,00")
        self.valor_recebido.setMinimumHeight(35)
        self.valor_recebido_label = QLabel("Valor Recebido:")
        self.valor_recebido.textChanged.connect(self._validar_valor_recebido)
        form.addRow(self.valor_recebido_label, self.valor_recebido)
        
        # Taxa de entrega
        self.taxa = QLineEdit()
        self.taxa.setPlaceholderText("0,00")
        self.taxa.setMinimumHeight(35)
        self.taxa_label = QLabel("Taxa de Entrega:")
        self.taxa.textChanged.connect(self._on_taxa_changed)
        form.addRow(self.taxa_label, self.taxa)
        
        # Label de erro para valor recebido
        self.erro_valor_label = QLabel()
        self.erro_valor_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        self.erro_valor_label.setVisible(False)
        layout.addWidget(self.erro_valor_label)

        self.status_pix = QLineEdit()
        self.status_pix.setPlaceholderText("Ex: Recebido / Aguardando")
        self.status_pix.setMinimumHeight(35)
        self.status_pix_label = QLabel("Status PIX:")
        form.addRow(self.status_pix_label, self.status_pix)

        layout.addLayout(form)
        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.setMinimumHeight(45)
        btn_voltar.setMinimumWidth(120)
        btn_voltar.clicked.connect(voltar_callback)
        
        btn_continuar = QPushButton("✓ Continuar")
        btn_continuar.setObjectName("btnSuccess")
        btn_continuar.setMinimumHeight(45)
        btn_continuar.setMinimumWidth(150)
        btn_continuar.clicked.connect(self._on_continuar)
        
        btn_layout.addWidget(btn_voltar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_continuar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Return"), self, self._on_continuar)
        QShortcut(QKeySequence("Escape"), self, voltar_callback)
        
        self._on_pagamento_changed()
        
        # Restaurar dados anteriores se houver
        if self.dados_anteriores:
            if 'metodo' in self.dados_anteriores:
                index = self.pagamento.findText(self.dados_anteriores['metodo'])
                if index >= 0:
                    self.pagamento.setCurrentIndex(index)
            if 'valor_recebido' in self.dados_anteriores:
                self.valor_recebido.setText(self.dados_anteriores['valor_recebido'])
            if 'status_pix' in self.dados_anteriores:
                self.status_pix.setText(self.dados_anteriores['status_pix'])
            if 'taxa' in self.dados_anteriores:
                taxa_valor = self.dados_anteriores['taxa']
                if taxa_valor > 0:
                    self.taxa.setText(str(taxa_valor).replace('.', ','))

    def _validar_valor_recebido(self):
        """Valida se o valor recebido é maior ou igual ao total do pedido"""
        if self.pagamento.currentText() != "Dinheiro":
            self.erro_valor_label.setVisible(False)
            return
        
        texto = self.valor_recebido.text()
        if not texto:
            self.erro_valor_label.setVisible(False)
            return
        
        try:
            valor = float(texto.replace(',', '.'))
            taxa_val = self._parse_currency(self.taxa.text())
            total_com_taxa = self.total_pedido + taxa_val
            if valor < total_com_taxa:
                self.erro_valor_label.setText(
                    f"❌ Valor insuficiente! Mínimo: R$ {total_com_taxa:.2f}"
                )
                self.erro_valor_label.setVisible(True)
            else:
                self.erro_valor_label.setVisible(False)
        except ValueError:
            self.erro_valor_label.setVisible(False)

    def _on_pagamento_changed(self):
        metodo = self.pagamento.currentText()
        self.valor_recebido_label.setVisible(metodo == "Dinheiro")
        self.valor_recebido.setVisible(metodo == "Dinheiro")
        self.status_pix_label.setVisible(metodo == "PIX")
        self.status_pix.setVisible(metodo == "PIX")
        self._validar_valor_recebido()

    def _parse_currency(self, texto):
        """Tenta converter um texto em formato brasileiro (vírgula opcional) para float."""
        if not texto:
            return 0.0
        try:
            return float(texto.replace(',', '.'))
        except Exception:
            return 0.0

    def _on_taxa_changed(self):
        taxa_val = self._parse_currency(self.taxa.text())
        total = self.total_pedido + taxa_val
        self.total_label.setText(f"Total do Pedido: R$ {total:.2f}")
        # Revalidar valor recebido caso esteja em dinheiro
        self._validar_valor_recebido()

    def _on_continuar(self):
        # Validar se é dinheiro e o valor está correto
        if self.pagamento.currentText() == "Dinheiro":
            try:
                valor_recebido = float(self.valor_recebido.text().replace(',', '.'))
                taxa_val = self._parse_currency(self.taxa.text())
                total_com_taxa = self.total_pedido + taxa_val
                if valor_recebido < total_com_taxa:
                    QMessageBox.warning(
                        self,
                        "Valor Insuficiente",
                        f"O valor recebido (R$ {valor_recebido:.2f}) não pode ser menor que o total do pedido (R$ {total_com_taxa:.2f})."
                    )
                    return
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Valor Inválido",
                    "Digite um valor válido em reais (ex: 50 ou 50,00)."
                )
                return
        
        self.continuar_callback({
            'metodo': self.pagamento.currentText(),
            'valor_recebido': self.valor_recebido.text(),
            'status_pix': self.status_pix.text(),
            'taxa': self._parse_currency(self.taxa.text()),
        })

    def get_data(self):
        return {
            'metodo': self.pagamento.currentText(),
            'valor_recebido': self.valor_recebido.text(),
            'status_pix': self.status_pix.text(),
            'taxa': self._parse_currency(self.taxa.text()),
        }


# ===============================================
# PREVIEW DO PEDIDO
# ===============================================
class PreviewForm(QWidget):
    def __init__(self, texto, confirmar_callback, registrar_callback, voltar_callback):
        super().__init__()
        self.setStyleSheet(FORM_STYLESHEET)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        titulo = QLabel("Comanda - Prévia do Pedido")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        self.texto = QTextEdit()
        self.texto.setPlainText(texto)
        self.texto.setReadOnly(True)
        layout.addWidget(self.texto)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.setMinimumHeight(45)
        btn_voltar.setMinimumWidth(120)
        btn_voltar.clicked.connect(voltar_callback)
        
        btn_copiar = QPushButton("📋 Copiar")
        btn_copiar.setObjectName("btnSecondary")
        btn_copiar.setMinimumHeight(45)
        btn_copiar.setMinimumWidth(120)
        btn_copiar.clicked.connect(self._copy_to_clipboard)
        
        btn_confirmar = QPushButton("🖨️ Imprimir e Registrar")
        btn_confirmar.setObjectName("btnSuccess")
        btn_confirmar.setMinimumHeight(45)
        btn_confirmar.setMinimumWidth(170)
        btn_confirmar.clicked.connect(confirmar_callback)

        btn_registrar = QPushButton("💾 Registrar (sem imprimir)")
        btn_registrar.setObjectName("btnPrimary")
        btn_registrar.setMinimumHeight(45)
        btn_registrar.setMinimumWidth(170)
        btn_registrar.clicked.connect(registrar_callback)
        
        btn_layout.addWidget(btn_voltar)
        btn_layout.addWidget(btn_copiar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_registrar)
        btn_layout.addWidget(btn_confirmar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Escape"), self, voltar_callback)

    def _copy_to_clipboard(self):
        from PyQt6.QtGui import QClipboard
        QApplication.clipboard().setText(self.texto.toPlainText())
        QMessageBox.information(self, "Copiado", "Comanda copiada!")


# ===============================================
# JANELA PRINCIPAL
# ===============================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Marmitas - Kelvin")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(600, 400)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.statusBar().hide()
        
        # Estado do pedido
        self.cliente = None
        self.itens = None
        self.pagamento = None
        self.pagamento_data = None
        self.taxa = 0.0
        self.troco = None
        
        self.show_menu()

    def show_menu(self):
        self.setCentralWidget(MenuPrincipal(self.show_cliente_form, self.show_admin_panel))

    def show_cliente_form(self):
        self.setCentralWidget(ClienteForm(self.on_cliente_continuar, self.show_menu))

    def on_cliente_continuar(self, cliente_data):
        self.cliente = cliente_data
        self.setCentralWidget(PratosForm(self.on_pratos_continuar, self.show_cliente_form))

    def on_pratos_continuar(self, itens):
        print(f"[on_pratos_continuar] Itens recebidos: {[(i['nome'], i.get('observacao', 'SEM OBS')) for i in itens]}")
        self.itens = itens
        # Ir para formulário de endereço antes do pagamento
        self.setCentralWidget(EnderecoForm(self.on_endereco_continuar, self.on_pratos_voltar))

    def on_endereco_continuar(self, endereco_data):
        # Mesclar dados de endereço com dados do cliente existente
        self.cliente.update(endereco_data)
        total_pedido = sum(item['subtotal'] for item in self.itens)
        self.setCentralWidget(PagamentoForm(self.on_pagamento_continuar, self.on_endereco_voltar, total_pedido))

    def on_endereco_voltar(self):
        self.setCentralWidget(PratosForm(self.on_pratos_continuar, self.show_cliente_form))

    def on_pratos_voltar(self):
        self.setCentralWidget(PratosForm(self.on_pratos_continuar, self.show_cliente_form))

    def on_pagamento_continuar(self, pagamento_data):
        # Armazenar dados do pagamento completos
        self.pagamento_data = pagamento_data
        self.pagamento = pagamento_data['metodo']
        # Sempre armazenar a taxa fornecida (independente do método)
        try:
            taxa = float(pagamento_data.get('taxa', 0) or 0)
        except Exception:
            taxa = 0.0
        self.taxa = taxa

        # Calcular troco apenas se for pagamento em dinheiro
        if self.pagamento == "Dinheiro":
            try:
                valor_total = sum(item['subtotal'] for item in self.itens) + self.taxa
                valor_recebido = float(pagamento_data.get('valor_recebido', '0').replace(',', '.'))
                self.troco = valor_recebido - valor_total
            except Exception:
                self.troco = 0
        else:
            # Não mostrar troco para outros métodos
            self.troco = None
        
        # Gerar texto da comanda
        texto = self._gerar_comanda()
        self.setCentralWidget(PreviewForm(
            texto,
            lambda: self.confirmar_pedido(texto),
            lambda: self.registrar_pedido(texto),
            lambda: self.voltar_para_pagamento()
        ))
    
    def voltar_para_pagamento(self):
        """Volta para o formulário de pagamento preservando os dados anteriores"""
        total_pedido = sum(item['subtotal'] for item in self.itens)
        self.setCentralWidget(PagamentoForm(
            self.on_pagamento_continuar, 
            self.on_endereco_voltar, 
            total_pedido, 
            self.pagamento_data
        ))

    def _gerar_comanda(self):
        print(f"[_gerar_comanda] self.itens: {[(i['nome'], i.get('observacao', 'SEM OBS')) for i in self.itens]}")
        total = sum(item['subtotal'] for item in self.itens)
        linhas = [
            "=" * 50,
            "COMANDA DE PEDIDO",
            "=" * 50,
            f"Cliente: {self.cliente['nome']}",
            f"Celular: {self.cliente['celular']}",
            f"Endereço: {self.cliente['endereco']}, {self.cliente['numero']}",
            f"Bairro: {self.cliente['bairro']}",
            "",
            "=" * 50,
            "ITENS:",
        ]
        
        for item in self.itens:
            linhas.append(f"  {item['quantidade']}x {item['nome']} - R$ {item['subtotal']:.2f}")
            # Adicionar observação do item se existir
            print(f"[_gerar_comanda] Verificando {item['nome']}: tem observacao={item.get('observacao', 'NÃO TEM')}")
            observacao = item.get('observacao', '').strip()
            if observacao:
                linhas.append(f"     Obs: {observacao}")
        
        # Incluir taxa de entrega quando presente
        linhas.extend([
            "=" * 50,
            "",
        ])
        if getattr(self, 'taxa', None):
            linhas.append(f"Taxa de Entrega: R$ {self.taxa:.2f}")

        linhas.extend([
            "=" * 50,
            f"TOTAL: R$ { (total + (getattr(self, 'taxa', 0.0))):.2f}",
            f"Pagamento: {self.pagamento}",
        ])
        
        if self.troco is not None:
            linhas.append(f"Troco: R$ {self.troco:.2f}")
        
        if self.cliente['obs']:
            linhas.append(f"Observações gerais: {self.cliente['obs']}")
        
        linhas.extend([
            "=" * 50,
            "Obrigado pela sua compra!",
        ])
        
        return "\n".join(linhas)

    def confirmar_pedido(self, texto_comanda):
        try:
            printer.imprimir_texto(texto_comanda)
            self.statusBar().showMessage("Comanda enviada para impressão.")
        except Exception as e:
            QMessageBox.warning(self, "Impressão", f"Falha ao imprimir: {e}")

        # Salvar pedido (inclui taxa se houver)
        total = sum(item['subtotal'] for item in self.itens) + (getattr(self, 'taxa', 0.0) or 0.0)
        try:
            numero = pedidos.salvar_pedido(
                self.cliente,
                self.itens,
                total,
                self.pagamento,
                self.troco,
                status="Em preparo",
            )
            self.statusBar().showMessage(f"Pedido #{numero:03d} salvo com sucesso!")
        except Exception as e:
            QMessageBox.warning(self, "Banco de dados", f"Falha ao salvar pedido: {e}")

        # Resetar e voltar ao menu
        self.cliente = None
        self.itens = None
        self.pagamento = None
        self.pagamento_data = None
        self.troco = None
        self.show_menu()

    def registrar_pedido(self, texto_comanda):
        """Registra o pedido no banco sem imprimir (para testes)."""
        # Salvar pedido somente (inclui taxa se houver)
        total = sum(item['subtotal'] for item in self.itens) + (getattr(self, 'taxa', 0.0) or 0.0)
        try:
            numero = pedidos.salvar_pedido(
                self.cliente,
                self.itens,
                total,
                self.pagamento,
                self.troco,
                status="Em preparo",
            )
            QMessageBox.information(self, "Registrado", f"Pedido #{numero:03d} registrado (sem impressão).")
            self.statusBar().showMessage(f"Pedido #{numero:03d} salvo (sem imprimir).")
        except Exception as e:
            QMessageBox.warning(self, "Banco de dados", f"Falha ao salvar pedido: {e}")

        # Resetar e voltar ao menu
        self.cliente = None
        self.itens = None
        self.pagamento = None
        self.pagamento_data = None
        self.troco = None
        self.show_menu()

    def show_admin_panel(self):
        self.setCentralWidget(AdminPanel(self.show_menu))


# ===============================================
# MAIN
# ===============================================
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Se ainda não houver senha configurada, solicitar criação na primeira execução.
    if get_admin_password_hash() is None:
        dlg = PasswordDialog(setup=True)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
