# admin_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QSpinBox,
    QDoubleSpinBox, QComboBox, QFormLayout, QDialog, QTextEdit
)
from PyQt6.QtWidgets import QFileDialog, QAbstractItemView, QDateEdit, QHeaderView
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QShortcut, QKeySequence
import ast
import pratos
import pedidos
from datetime import datetime
from config import get_admin_password_hash, set_admin_password, verify_admin_password
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import os


class PasswordDialog(QDialog):
    """Diálogo para cadastrar/verificar a senha de acesso à aba de Gerenciamento.

    Se o sistema ainda não tiver senha configurada, o diálogo solicitará que o
    usuário defina uma nova senha (com confirmação). Caso contrário, solicitará
    apenas a senha atual.
    """

    def __init__(self, parent=None, setup: bool = False):
        super().__init__(parent)
        self.setup_mode = setup
        self.setWindowTitle("Configurar Senha" if setup else "Acesso Restrito")
        self.setGeometry(400, 300, 400, 200)
        self.setModal(True)

        layout = QVBoxLayout()

        # Título
        titulo_text = (
            "Primeiro acesso: defina a senha de administrador" if setup
            else "Gerenciamento de Vendas"
        )
        titulo = QLabel(titulo_text)
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #E74C3C;")
        layout.addWidget(titulo)

        # Instrução
        instrucao = QLabel(
            "Digite uma senha forte e mantenha-a em local seguro." if setup
            else "Esta seção requer senha de acesso."
        )
        layout.addWidget(instrucao)

        # Campo de senha
        layout.addWidget(QLabel("Senha:"))
        self.senha_input = QLineEdit()
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha_input.setPlaceholderText("Digite a senha")
        self.senha_input.returnPressed.connect(self.verificar_senha)
        layout.addWidget(self.senha_input)

        if setup:
            layout.addWidget(QLabel("Confirmar senha:"))
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_input.setPlaceholderText("Repita a senha")
            self.confirm_input.returnPressed.connect(self.verificar_senha)
            layout.addWidget(self.confirm_input)

        # Botões
        btn_layout = QHBoxLayout()

        btn_ok = QPushButton("Salvar" if setup else "Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.verificar_senha)
        btn_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Foco no campo de senha
        self.senha_input.setFocus()

    def verificar_senha(self):
        """Verifica ou configura a senha de administrador."""
        senha = self.senha_input.text().strip()

        if self.setup_mode:
            confirm = getattr(self, "confirm_input", None)
            if not senha:
                QMessageBox.warning(self, "Erro", "A senha não pode ficar vazia.")
                return
            if confirm is None or senha != confirm.text().strip():
                QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
                return
            set_admin_password(senha)
            QMessageBox.information(self, "Sucesso", "Senha configurada com sucesso.")
            self.accept()
            return

        # Modo de verificação normal
        if verify_admin_password(senha):
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Senha incorreta! Tente novamente.")
            self.senha_input.clear()
            self.senha_input.setFocus()

    def get_senha_correta(self):
        """Verifica se a senha foi confirmada com sucesso."""
        return self.result() == QDialog.DialogCode.Accepted


class EditPratoDialog(QDialog):
    def __init__(self, nome, preco, categoria, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Prato")
        self.nome_input = QLineEdit(nome)
        self.preco_input = QDoubleSpinBox()
        self.preco_input.setMinimum(0.0)
        self.preco_input.setMaximum(999.99)
        self.preco_input.setDecimals(2)
        try:
            self.preco_input.setValue(float(preco))
        except Exception:
            self.preco_input.setValue(0.0)
        self.categoria_input = QComboBox()
        self.categoria_input.addItems(["Marmita", "Bebida", "Sobremesa", "Combo"])
        if categoria in ["Marmita", "Bebida", "Sobremesa", "Combo"]:
            self.categoria_input.setCurrentText(categoria)

        form = QFormLayout()
        form.addRow("Nome:", self.nome_input)
        form.addRow("Preço (R$):", self.preco_input)
        form.addRow("Categoria:", self.categoria_input)

        btn_ok = QPushButton("Salvar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)

        v = QVBoxLayout()
        v.addLayout(form)
        v.addLayout(btn_layout)
        self.setLayout(v)


class PedidoDetalhesDialog(QDialog):
    def __init__(self, pedido_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Pedido")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        try:
            # Extrair dados do pedido (tuple do banco)
            # Colunas: id, numero, cliente, endereco, cep, observacoes, itens, total, pagamento, troco, status, data
            if len(pedido_data) >= 12:
                ped_id, ped_numero, cliente, endereco, cep, observacoes, itens_raw, total, pagamento, troco, status, data = pedido_data[:12]
            else:
                raise ValueError(f"Dados incompletos: esperado 12 colunas, recebido {len(pedido_data)}")
            
            # Título
            titulo = QLabel(f"Pedido #{ped_numero}")
            titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
            layout.addWidget(titulo)
            
            # Info em formato texto
            troco_value = troco if troco is not None else 0
            info_text = f"""
ID: {ped_id}
Número: {ped_numero}
Cliente: {cliente}
Endereço: {endereco}, {cep}
Observações: {observacoes or 'Nenhuma'}
Pagamento: {pagamento}
Troco: R$ {troco_value:.2f}
Status: {status}
Data: {data}
Total: R$ {total:.2f}

Itens do Pedido:
"""
            
            # Parse dos itens
            try:
                if itens_raw is None:
                    itens_list = []
                elif isinstance(itens_raw, str):
                    itens_list = ast.literal_eval(itens_raw)
                else:
                    itens_list = itens_raw
            except Exception as e:
                itens_list = []
                info_text += f"\nErro ao parsear itens: {e}"
            
            for item in itens_list:
                try:
                    if isinstance(item, dict):
                        nome = item.get('nome', 'Item')
                        qtd = item.get('qtd', item.get('quantidade', 1))
                        preco = item.get('preco', 0.0)
                        info_text += f"\n  • {nome} x{qtd} - R$ {preco * qtd:.2f}"
                    else:
                        info_text += f"\n  • {str(item)}"
                except Exception as e:
                    info_text += f"\n  • Erro ao processar item: {e}"
            
            text_display = QLabel(info_text)
            text_display.setStyleSheet("font-family: monospace; white-space: pre-wrap;")
            text_display.setWordWrap(True)
            layout.addWidget(text_display)
            
        except Exception as e:
            # Se houver erro, mostrar mensagem de erro
            error_label = QLabel(f"Erro ao carregar detalhes do pedido:\n{str(e)}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
        
        # Botão fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("btnSecondary")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)
        
        self.setLayout(layout)

class EditarItensDialog(QDialog):
    """Diálogo para editar itens do pedido."""
    def __init__(self, itens_raw, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Itens do Pedido")
        self.setGeometry(100, 100, 700, 500)
        
        try:
            # Parse dos itens
            if itens_raw is None:
                self.itens_list = []
            elif isinstance(itens_raw, str):
                self.itens_list = ast.literal_eval(itens_raw)
            else:
                self.itens_list = itens_raw
        except Exception:
            self.itens_list = []
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Remova itens que não deseja mais:"))
        
        # Tabela de itens
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(4)
        self.tabela_itens.setHorizontalHeaderLabels(["Item", "Quantidade", "Preço Unit.", "Subtotal"])
        self.tabela_itens.setColumnWidth(0, 250)
        self.tabela_itens.setColumnWidth(1, 100)
        self.tabela_itens.setColumnWidth(2, 100)
        self.tabela_itens.setColumnWidth(3, 100)
        self.tabela_itens.setAlternatingRowColors(True)
        
        self._carregar_tabela_itens()
        layout.addWidget(self.tabela_itens)
        
        # Botão remover
        btn_remover = QPushButton("Remover Item Selecionado")
        btn_remover.setObjectName("btnSecondary")
        btn_remover.clicked.connect(self._remover_item_selecionado)
        layout.addWidget(btn_remover)
        
        # Total
        self.total_label = QLabel(f"Total: R$ 0.00")
        self.total_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #26A65B;")
        layout.addWidget(self.total_label)
        self._atualizar_total()
        
        # Botões finais
        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_ok = QPushButton("Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def _carregar_tabela_itens(self):
        """Carrega os itens na tabela."""
        self.tabela_itens.setRowCount(0)
        try:
            for idx, item in enumerate(self.itens_list):
                if isinstance(item, dict):
                    nome = item.get('nome', 'Item')
                    qtd = item.get('qtd', item.get('quantidade', 1))
                    preco = item.get('preco', 0.0)
                    subtotal = float(preco) * int(qtd)
                    
                    self.tabela_itens.insertRow(idx)
                    self.tabela_itens.setItem(idx, 0, QTableWidgetItem(nome))
                    self.tabela_itens.setItem(idx, 1, QTableWidgetItem(str(qtd)))
                    self.tabela_itens.setItem(idx, 2, QTableWidgetItem(f"R$ {float(preco):.2f}"))
                    self.tabela_itens.setItem(idx, 3, QTableWidgetItem(f"R$ {subtotal:.2f}"))
        except Exception as e:
            print(f"Erro ao carregar tabela de itens: {e}")
    
    def _remover_item_selecionado(self):
        """Remove o item selecionado."""
        row = self.tabela_itens.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um item para remover.")
            return
        
        if row < len(self.itens_list):
            self.itens_list.pop(row)
            self._carregar_tabela_itens()
            self._atualizar_total()
    
    def _atualizar_total(self):
        """Recalcula o total."""
        total = 0.0
        for item in self.itens_list:
            if isinstance(item, dict):
                qtd = int(item.get('qtd', item.get('quantidade', 1)) or 1)
                preco = float(item.get('preco', 0.0) or 0.0)
                total += qtd * preco
        self.total_label.setText(f"Total: R$ {total:.2f}")
    
    def obter_itens(self):
        """Retorna os itens modificados."""
        return self.itens_list


class EditarEnderecoDialog(QDialog):
    """Diálogo para editar endereço completo."""
    def __init__(self, endereco, numero, bairro, cep, complemento, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Endereço")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.endereco_input = QLineEdit(endereco or "")
        form.addRow("Rua/Avenida:", self.endereco_input)
        
        self.numero_input = QSpinBox()
        self.numero_input.setMinimum(0)
        self.numero_input.setMaximum(99999)
        self.numero_input.setValue(int(numero) if numero else 0)
        form.addRow("Número:", self.numero_input)
        
        self.bairro_input = QLineEdit(bairro or "")
        form.addRow("Bairro:", self.bairro_input)
        
        self.cep_input = QLineEdit(cep or "")
        form.addRow("CEP:", self.cep_input)
        
        self.complemento_input = QLineEdit(complemento or "")
        self.complemento_input.setPlaceholderText("Ex: Apartamento, casa fundos, etc (Opcional)")
        form.addRow("Complemento:", self.complemento_input)
        
        layout.addLayout(form)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_ok = QPushButton("Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.validar_e_aceitar)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)
    
    def validar_e_aceitar(self):
        """Valida antes de aceitar."""
        if not self.endereco_input.text().strip():
            QMessageBox.warning(self, "Erro", "Rua/Avenida não pode estar vazia.")
            return
        
        if self.numero_input.value() == 0:
            QMessageBox.warning(self, "Erro", "Número não pode ser 0.")
            return
        
        if not self.bairro_input.text().strip():
            QMessageBox.warning(self, "Erro", "Bairro não pode estar vazio.")
            return
        
        if not self.cep_input.text().strip():
            QMessageBox.warning(self, "Erro", "CEP não pode estar vazio.")
            return
        
        self.accept()
    
    def obter_dados(self):
        """Retorna todos os dados do endereço."""
        return (
            self.endereco_input.text().strip(),
            self.numero_input.value(),
            self.bairro_input.text().strip(),
            self.cep_input.text().strip(),
            self.complemento_input.text().strip()
        )


class EditarPagamentoDialog(QDialog):
    """Diálogo para editar pagamento. O troco é calculado automaticamente."""
    def __init__(self, pagamento, valor_recebido, total_pedido, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Pagamento")
        self.setGeometry(100, 100, 500, 300)
        self.total_pedido = total_pedido
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        # Label do total
        lbl_total = QLabel(f"Total do Pedido: R$ {total_pedido:.2f}")
        lbl_total.setStyleSheet("font-weight: bold; color: #2E86DE;")
        form.addRow("", lbl_total)
        
        self.pagamento_combo = QComboBox()
        self.pagamento_combo.addItems(["Dinheiro", "PIX", "Cartão", "Já foi pago no PIX", "Fiado"])
        if pagamento:
            idx = self.pagamento_combo.findText(pagamento)
            if idx >= 0:
                self.pagamento_combo.setCurrentIndex(idx)
        self.pagamento_combo.currentTextChanged.connect(self._atualizar_visibilidade)
        form.addRow("Método de Pagamento:", self.pagamento_combo)
        
        # Label e input de valor recebido
        self.valor_recebido_label = QLabel("Valor Recebido (R$):")
        self.valor_recebido_input = QDoubleSpinBox()
        self.valor_recebido_input.setMinimum(0.0)
        self.valor_recebido_input.setMaximum(99999.99)
        self.valor_recebido_input.setDecimals(2)
        self.valor_recebido_input.setValue(float(valor_recebido) if valor_recebido else 0.0)
        self.valor_recebido_input.valueChanged.connect(self._calcular_troco)
        form.addRow(self.valor_recebido_label, self.valor_recebido_input)
        
        # Label do troco (somente leitura)
        self.troco_label = QLabel("Troco (R$):")
        self.troco_display = QLabel("R$ 0.00")
        self.troco_display.setStyleSheet("font-weight: bold; color: #26A65B; font-size: 11pt;")
        form.addRow(self.troco_label, self.troco_display)
        
        layout.addLayout(form)
        
        # Atualizar visibilidade inicial
        self._atualizar_visibilidade()
        self._calcular_troco()
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnSecondary")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_ok = QPushButton("Confirmar")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def _atualizar_visibilidade(self):
        """Mostra os campos de valor recebido e troco apenas se o pagamento for Dinheiro."""
        eh_dinheiro = self.pagamento_combo.currentText() == "Dinheiro"
        self.valor_recebido_label.setVisible(eh_dinheiro)
        self.valor_recebido_input.setVisible(eh_dinheiro)
        self.troco_label.setVisible(eh_dinheiro)
        self.troco_display.setVisible(eh_dinheiro)
        
        if eh_dinheiro:
            self._calcular_troco()
    
    def _calcular_troco(self):
        """Calcula e exibe o troco automaticamente."""
        if self.pagamento_combo.currentText() == "Dinheiro":
            valor_recebido = self.valor_recebido_input.value()
            troco = valor_recebido - self.total_pedido
            self.troco_display.setText(f"R$ {troco:.2f}")
            
            # Avisar se o valor recebido é insuficiente
            if troco < 0:
                self.troco_display.setStyleSheet("font-weight: bold; color: #E74C3C; font-size: 11pt;")
            else:
                self.troco_display.setStyleSheet("font-weight: bold; color: #26A65B; font-size: 11pt;")
    
    def obter_dados(self):
        """Retorna pagamento, valor recebido e troco calculado."""
        pagamento = self.pagamento_combo.currentText()
        
        if pagamento == "Dinheiro":
            valor_recebido = self.valor_recebido_input.value()
            troco = valor_recebido - self.total_pedido
            return pagamento, valor_recebido, troco
        else:
            # Para outros métodos, retorna 0 para valor recebido e troco
            return pagamento, 0.0, 0.0


class EditarPedidoDialog(QDialog):
    """Diálogo principal para editar pedido com 3 opções."""
    def __init__(self, pedido_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Pedido")
        self.setGeometry(100, 100, 600, 400)
        self.pedido_data = pedido_data
        
        try:
            # Extrair dados do pedido
            self.ped_id = pedido_data[0]
            self.ped_numero = pedido_data[1]
            self.cliente = pedido_data[2]
            self.endereco_atual = pedido_data[3]
            self.cep_atual = pedido_data[4]
            self.obs_atual = pedido_data[5]
            self.itens_raw = pedido_data[6]
            self.total_atual = pedido_data[7]
            self.pagamento_atual = pedido_data[8]
            self.troco_atual = pedido_data[9] or 0.0
            self.bairro_atual = pedido_data[12] if len(pedido_data) > 12 else ""
            self.numero_endereco_atual = pedido_data[13] if len(pedido_data) > 13 else 0
            
            # Parse dos itens
            try:
                if self.itens_raw is None:
                    self.itens_list = []
                elif isinstance(self.itens_raw, str):
                    self.itens_list = ast.literal_eval(self.itens_raw)
                else:
                    self.itens_list = self.itens_raw
            except Exception:
                self.itens_list = []
            
            layout = QVBoxLayout()
            
            # Título
            titulo = QLabel(f"Editar Pedido #{self.ped_numero}")
            titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
            layout.addWidget(titulo)
            
            # Info do cliente
            info = QLabel(f"Cliente: {self.cliente}\nEndereço: {self.endereco_atual}, {self.cep_atual}\nTotal: R$ {self.total_atual:.2f}")
            info.setStyleSheet("font-size: 10pt; color: #555;")
            layout.addWidget(info)
            
            layout.addSpacing(20)
            
            # Botões com atalhos
            self.btn_itens = QPushButton("1 - Alterar Itens")
            self.btn_itens.setObjectName("btnPrimary")
            self.btn_itens.setMinimumHeight(50)
            self.btn_itens.setShortcut("1")
            self.btn_itens.clicked.connect(self.editar_itens)
            layout.addWidget(self.btn_itens)
            
            self.btn_endereco = QPushButton("2 - Alterar Endereço")
            self.btn_endereco.setObjectName("btnPrimary")
            self.btn_endereco.setMinimumHeight(50)
            self.btn_endereco.setShortcut("2")
            self.btn_endereco.clicked.connect(self.editar_endereco)
            layout.addWidget(self.btn_endereco)
            
            self.btn_pagamento = QPushButton("3 - Alterar Pagamento")
            self.btn_pagamento.setObjectName("btnPrimary")
            self.btn_pagamento.setMinimumHeight(50)
            self.btn_pagamento.setShortcut("3")
            self.btn_pagamento.clicked.connect(self.editar_pagamento)
            layout.addWidget(self.btn_pagamento)
            
            layout.addSpacing(20)
            
            # Botões finais
            btn_layout = QHBoxLayout()
            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.setObjectName("btnSecondary")
            btn_cancelar.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancelar)
            
            btn_salvar = QPushButton("Salvar Alterações")
            btn_salvar.setObjectName("btnSuccess")
            btn_salvar.clicked.connect(self.accept)
            btn_layout.addWidget(btn_salvar)
            
            layout.addLayout(btn_layout)
            layout.addStretch()
            
            self.setLayout(layout)
        
        except Exception as e:
            print(f"Erro ao inicializar diálogo de edição: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pedido para edição:\n{str(e)}")
            self.reject()
    
    def editar_itens(self):
        """Abre diálogo para editar itens."""
        dlg = EditarItensDialog(self.itens_list, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.itens_list = dlg.obter_itens()
            # Recalcular total
            total = 0.0
            for item in self.itens_list:
                if isinstance(item, dict):
                    qtd = int(item.get('qtd', item.get('quantidade', 1)) or 1)
                    preco = float(item.get('preco', 0.0) or 0.0)
                    total += qtd * preco
            self.total_atual = total
    
    def editar_endereco(self):
        """Abre diálogo para editar endereço."""
        dlg = EditarEnderecoDialog(self.endereco_atual, self.numero_endereco_atual, self.bairro_atual, self.cep_atual, self.obs_atual, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.endereco_atual, self.numero_endereco_atual, self.bairro_atual, self.cep_atual, self.obs_atual = dlg.obter_dados()
    
    def editar_pagamento(self):
        """Abre diálogo para editar pagamento."""
        dlg = EditarPagamentoDialog(self.pagamento_atual, self.troco_atual, self.total_atual, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.pagamento_atual, valor_recebido, self.troco_atual = dlg.obter_dados()
    
    def obter_dados_alterados(self):
        """Retorna um dicionário com os dados alterados."""
        return {
            'endereco': self.endereco_atual,
            'cep': self.cep_atual,
            'bairro': self.bairro_atual,
            'numero_endereco': self.numero_endereco_atual,
            'pagamento': self.pagamento_atual,
            'troco': self.troco_atual,
            'observacoes': self.obs_atual,
            'itens': self.itens_list
        }

class AdminPanel(QWidget):
    def __init__(self, voltar_callback):
        super().__init__()
        # estilo herdado do app principal
        self.voltar_callback = voltar_callback
        self.setWindowTitle("Painel Admin")
        layout = QVBoxLayout()

        titulo = QLabel("Painel Administrativo")
        titulo.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2E86DE; margin: 10px;")
        layout.addWidget(titulo)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.criar_aba_pratos(), "Gerenciar Pratos")
        self.tabs.addTab(self.criar_aba_pedidos(), "Ver Pedidos")
        self.tabs.addTab(self.criar_aba_vendas(), "Gerenciamento de vendas")
        self.tabs.addTab(self.criar_aba_cancelar(), "Cancelar Pedido")
        self.tabs.addTab(self.criar_aba_entregas(), "Entregas")
        
        # Variável para rastrear se a senha foi confirmada
        self.senha_confirmada = False
        self.indice_aba_vendas = 2  # índice da aba de Gerenciamento de vendas
        
        # Conectar evento de mudança de aba para verificar senha
        self.tabs.currentChanged.connect(self._verificar_acesso_aba)
        
        # Adicionar atalhos de teclado para as abas
        QShortcut(QKeySequence("F1"), self, lambda: self.tabs.setCurrentIndex(0))  # Gerenciar Pratos
        QShortcut(QKeySequence("F2"), self, lambda: self.tabs.setCurrentIndex(1))  # Ver Pedidos
        QShortcut(QKeySequence("F3"), self, lambda: self._acessar_aba_vendas())  # Gerenciamento de vendas
        QShortcut(QKeySequence("F4"), self, lambda: self.tabs.setCurrentIndex(3))  # Cancelar Pedido
        QShortcut(QKeySequence("F5"), self, lambda: self.tabs.setCurrentIndex(4))  # Entregas

        layout.addWidget(self.tabs)

        btn_voltar = QPushButton("← Voltar ao Menu")
        btn_voltar.setObjectName("btnSecondary")
        btn_voltar.clicked.connect(voltar_callback)
        layout.addWidget(btn_voltar)

        self.setLayout(layout)

    def _verificar_acesso_aba(self, indice):
        """Verifica se o acesso à aba requer senha."""
        if indice == self.indice_aba_vendas and not self.senha_confirmada:
            # Voltando para a aba anterior
            self.tabs.blockSignals(True)
            # Encontrar uma aba válida para voltar
            aba_anterior = 0 if indice != 0 else 1
            self.tabs.setCurrentIndex(aba_anterior)
            self.tabs.blockSignals(False)
            
            # Mostrar diálogo de senha
            self._acessar_aba_vendas()
    
    def _acessar_aba_vendas(self):
        """Solicita senha para acessar a aba de vendas.

        Se ainda não houver senha configurada, solicita a criação de uma nova.
        """
        setup_required = get_admin_password_hash() is None
        dialog = PasswordDialog(self, setup=setup_required)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.senha_confirmada = True
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self.indice_aba_vendas)
            self.tabs.blockSignals(False)
        else:
            # Voltar para a aba anterior
            self.tabs.blockSignals(True)
            aba_anterior = 0 if self.tabs.currentIndex() == self.indice_aba_vendas else self.tabs.currentIndex()
            self.tabs.setCurrentIndex(aba_anterior)
            self.tabs.blockSignals(False)

    def criar_aba_pratos(self):
        """Aba para adicionar, editar e remover pratos."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Título da aba
        titulo = QLabel("Gerenciar Pratos")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Seção de entrada
        form = QFormLayout()
        self.prato_nome = QLineEdit()
        self.prato_preco = QDoubleSpinBox()
        self.prato_preco.setMinimum(0.0)
        self.prato_preco.setMaximum(999.99)
        self.prato_preco.setDecimals(2)
        self.prato_categoria = QComboBox()
        self.prato_categoria.addItems(["Marmita", "Bebida", "Sobremesa", "Combo"])

        form.addRow("Nome do Prato:", self.prato_nome)
        form.addRow("Preço (R$):", self.prato_preco)
        form.addRow("Categoria:", self.prato_categoria)

        btn_adicionar = QPushButton("✚ Adicionar Prato")
        btn_adicionar.setObjectName("btnSuccess")
        btn_adicionar.clicked.connect(self.adicionar_prato)

        layout.addLayout(form)
        layout.addWidget(btn_adicionar)

        # Tabela de pratos
        self.tabela_pratos = QTableWidget()
        self.tabela_pratos.setColumnCount(4)
        self.tabela_pratos.setHorizontalHeaderLabels(["ID", "Nome", "Preço", "Categoria"])
        self.tabela_pratos.setColumnWidth(1, 200)
        self.tabela_pratos.setAlternatingRowColors(True)
        # Desabilita edição direta clicando nas células
        self.tabela_pratos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_pratos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(QLabel("Pratos cadastrados:"))
        layout.addWidget(self.tabela_pratos)

        btn_remover = QPushButton("✕ Remover Selecionado")
        btn_remover.setObjectName("btnDanger")
        btn_remover.clicked.connect(self.remover_prato)
        
        btn_atualizar = QPushButton("🔄 Atualizar Lista")
        btn_atualizar.setObjectName("btnWarning")
        btn_atualizar.clicked.connect(self.atualizar_tabela_pratos)

        btn_editar = QPushButton("✎ Editar Selecionado")
        btn_editar.setObjectName("btnSecondary")
        btn_editar.clicked.connect(self.editar_prato_dialog)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_remover)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_atualizar)
        layout.addLayout(btn_layout)

        widget.setLayout(layout)
        self.atualizar_tabela_pratos()
        return widget

    def atualizar_tabela_pratos(self):
        """Carrega pratos da API e mostra na tabela."""
        self.tabela_pratos.setRowCount(0)
        pratos_list = pratos.listar_pratos()
        for idx, prato in enumerate(pratos_list):
            self.tabela_pratos.insertRow(idx)
            self.tabela_pratos.setItem(idx, 0, QTableWidgetItem(str(idx)))
            self.tabela_pratos.setItem(idx, 1, QTableWidgetItem(prato.get("nome", "")))
            self.tabela_pratos.setItem(idx, 2, QTableWidgetItem(f"R$ {prato.get('preco', 0):.2f}"))
            self.tabela_pratos.setItem(idx, 3, QTableWidgetItem(prato.get("categoria", "")))

    def adicionar_prato(self):
        """Adiciona um novo prato."""
        nome = self.prato_nome.text().strip()
        preco = self.prato_preco.value()
        categoria = self.prato_categoria.currentText()

        if not nome:
            QMessageBox.warning(self, "Erro", "Nome do prato não pode estar vazio.")
            return

        try:
            pratos.adicionar_prato(nome, preco, categoria)
            QMessageBox.information(self, "Sucesso", f"Prato '{nome}' adicionado com sucesso!")
            self.prato_nome.clear()
            self.prato_preco.setValue(0.0)
            self.atualizar_tabela_pratos()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))

    def remover_prato(self):
        """Remove o prato selecionado."""
        row = self.tabela_pratos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um prato para remover.")
            return

        nome = self.tabela_pratos.item(row, 1).text()
        reply = QMessageBox.question(self, "Confirmar", f"Remover '{nome}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            pratos.remover_prato(nome)
            QMessageBox.information(self, "Sucesso", f"Prato '{nome}' removido.")
            self.atualizar_tabela_pratos()

    def editar_prato_dialog(self):
        """Abre diálogo para editar o prato selecionado."""
        row = self.tabela_pratos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um prato para editar.")
            return

        old_nome = self.tabela_pratos.item(row, 1).text()
        preco_text = self.tabela_pratos.item(row, 2).text()
        # tenta extrair número do formato 'R$ 12.34'
        try:
            preco = float(preco_text.replace('R$', '').replace(',', '.').strip())
        except Exception:
            preco = 0.0
        categoria = self.tabela_pratos.item(row, 3).text()

        dlg = EditPratoDialog(old_nome, preco, categoria, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            novo_nome = dlg.nome_input.text().strip()
            novo_preco = dlg.preco_input.value()
            nova_categoria = dlg.categoria_input.currentText()
            try:
                updated = pratos.editar_prato(old_nome, novo_nome, novo_preco, nova_categoria)
                if updated:
                    QMessageBox.information(self, "Sucesso", f"Prato '{old_nome}' atualizado.")
                else:
                    QMessageBox.warning(self, "Erro", "Prato não encontrado para atualização.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Falha ao atualizar: {e}")
            self.atualizar_tabela_pratos()

    def criar_aba_pedidos(self):
        """Aba para visualizar pedidos."""
        widget = QWidget()
        layout = QVBoxLayout()
        titulo = QLabel("Pedidos do Sistema")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)
        
        # Filtro de data
        filtro_data_layout = QHBoxLayout()
        filtro_data_layout.addWidget(QLabel("Período:"))
        self.filtro_data_pedidos = QComboBox()
        self.filtro_data_pedidos.addItems(["Hoje", "Esta Semana", "Este Mês"])
        self.filtro_data_pedidos.setCurrentText("Hoje")
        self.filtro_data_pedidos.currentTextChanged.connect(self.atualizar_tabela_pedidos)
        filtro_data_layout.addWidget(self.filtro_data_pedidos)
        filtro_data_layout.addStretch()
        layout.addLayout(filtro_data_layout)
        
        # Barra de busca + filtro por status + filtro por pagamento
        top_controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nome ou telefone...")
        self.search_input.textChanged.connect(self.atualizar_tabela_pedidos)
        top_controls.addWidget(self.search_input)

        top_controls.addWidget(QLabel("Filtrar por status:"))
        self.filtro_status = QComboBox()
        self.filtro_status.addItems(["Todos", "Em preparo", "Despachado", "Cancelado"])
        self.filtro_status.currentTextChanged.connect(self.atualizar_tabela_pedidos)
        top_controls.addWidget(self.filtro_status)

        top_controls.addWidget(QLabel("Filtrar por pagamento:"))
        self.filtro_pagamento = QComboBox()
        self.filtro_pagamento.addItems(["Todos", "Dinheiro", "PIX", "Cartão", "Já foi pago no PIX", "Fiado"])
        self.filtro_pagamento.currentTextChanged.connect(self.atualizar_tabela_pedidos)
        top_controls.addWidget(self.filtro_pagamento)

        top_controls.addStretch()
        layout.addLayout(top_controls)

        self.tabela_pedidos = QTableWidget()
        self.tabela_pedidos.setColumnCount(7)
        self.tabela_pedidos.setHorizontalHeaderLabels(["Número", "Cliente", "Total", "Pagamento", "Status", "Data", "Itens"])
        self.tabela_pedidos.setColumnWidth(1, 120)
        self.tabela_pedidos.setColumnWidth(6, 300)
        self.tabela_pedidos.setAlternatingRowColors(True)
        self.tabela_pedidos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_pedidos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Conectar duplo-clique para exibir detalhes
        self.tabela_pedidos.doubleClicked.connect(self._on_pedido_duplo_clique)

        layout.addWidget(self.tabela_pedidos)

        # Controles rápidos de status
        ops_layout = QHBoxLayout()
        btn_despachar = QPushButton("✎ Alternar Status (Em preparo ↔ Despachado)")
        btn_despachar.setObjectName("btnWarning")
        btn_despachar.clicked.connect(self.marcar_despachado_selecionado)
        ops_layout.addWidget(btn_despachar)
        # Botão para editar pedido selecionado
        btn_editar_pedido = QPushButton("✏️ Editar Pedido")
        btn_editar_pedido.setObjectName("btnPrimary")
        btn_editar_pedido.clicked.connect(self.editar_pedido_selecionado)
        ops_layout.addWidget(btn_editar_pedido)
        # Botão para copiar comanda
        btn_copiar_comanda = QPushButton("📋 Copiar Comanda")
        btn_copiar_comanda.setObjectName("btnPrimary")
        btn_copiar_comanda.clicked.connect(self.copiar_comanda_selecionada)
        ops_layout.addWidget(btn_copiar_comanda)
        # Botão para reimprimir pedido selecionado
        btn_reimprimir = QPushButton("🖨️ Reimprimir Pedido")
        btn_reimprimir.setObjectName("btnPrimary")
        btn_reimprimir.clicked.connect(self.reimprimir_selecionado)
        ops_layout.addWidget(btn_reimprimir)
        ops_layout.addStretch()
        layout.addLayout(ops_layout)

        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setObjectName("btnWarning")
        btn_atualizar.clicked.connect(self.atualizar_tabela_pedidos)
        layout.addWidget(btn_atualizar)

        widget.setLayout(layout)
        self.atualizar_tabela_pedidos()
        return widget

    def atualizar_tabela_pedidos(self):
        """Carrega pedidos e mostra na tabela com filtros de data e status."""
        self.tabela_pedidos.setRowCount(0)
        # Dicionário para armazenar dados completos do pedido por id
        self.pedidos_cache = {}
        try:
            # Determinar intervalo de datas baseado no filtro
            hoje = QDate.currentDate()
            filtro_data = self.filtro_data_pedidos.currentText() if hasattr(self, 'filtro_data_pedidos') else 'Hoje'
            
            if filtro_data == 'Hoje':
                inicio = hoje
                fim = hoje
            elif filtro_data == 'Esta Semana':
                # Últimos 7 dias (de 7 dias atrás até hoje)
                inicio = hoje.addDays(-6)
                fim = hoje
            else:  # 'Este Mês'
                inicio = QDate(hoje.year(), hoje.month(), 1)
                fim = hoje
            
            # Buscar pedidos
            inicio_s = inicio.toString('yyyy-MM-dd')
            fim_s = fim.toString('yyyy-MM-dd')
            pedidos_list = pedidos.pedidos_por_periodo(inicio_s, fim_s)
            
            filtro = self.filtro_status.currentText() if hasattr(self, 'filtro_status') else 'Todos'
            color_map = {
                'em preparo': QColor('#FFF3B0'),
                'despachado': QColor('#CDE7D8'),
                'cancelado': QColor('#FFD6D6')
            }
            row = 0
            for ped in pedidos_list:
                status = (ped[10] or '').strip()
                pagamento = (ped[8] or '').strip()
                
                # Aplicar filtro de status
                filtro = self.filtro_status.currentText() if hasattr(self, 'filtro_status') else 'Todos'
                if filtro != 'Todos' and status != filtro:
                    continue

                # Aplicar filtro de pagamento
                filtro_pag = self.filtro_pagamento.currentText() if hasattr(self, 'filtro_pagamento') else 'Todos'
                if filtro_pag != 'Todos' and pagamento != filtro_pag:
                    continue

                # inserir
                self.tabela_pedidos.insertRow(row)
                # exibir o 'numero' (o número que o gestor usará para cancelar)
                item_num = QTableWidgetItem(str(ped[1]))
                # guardar o id real do DB no UserRole
                ped_id = ped[0]
                item_num.setData(Qt.ItemDataRole.UserRole, ped_id)
                self.tabela_pedidos.setItem(row, 0, item_num)
                self.tabela_pedidos.setItem(row, 1, QTableWidgetItem(ped[2] or ''))
                self.tabela_pedidos.setItem(row, 2, QTableWidgetItem(f"R$ {ped[7]:.2f}"))
                self.tabela_pedidos.setItem(row, 3, QTableWidgetItem(ped[8] or ''))
                self.tabela_pedidos.setItem(row, 4, QTableWidgetItem(status))
                self.tabela_pedidos.setItem(row, 5, QTableWidgetItem(ped[11] or ''))

                # formatar itens em texto legível e colocar tooltip com completo
                itens_text = ''
                try:
                    raw = ped[6]
                    if raw is None:
                        itens_list = []
                    elif isinstance(raw, str):
                        itens_list = ast.literal_eval(raw)
                    else:
                        itens_list = raw

                    parts = []
                    if isinstance(itens_list, list):
                        for it in itens_list:
                            if isinstance(it, dict):
                                nome = it.get('nome', 'Item')
                                qtd = it.get('qtd')
                                if qtd is not None:
                                    parts.append(f"{nome} x{qtd}")
                                else:
                                    parts.append(str(nome))
                            else:
                                parts.append(str(it))
                    else:
                        parts = [str(itens_list)]

                    itens_text = ', '.join(parts)
                    display_text = itens_text if len(itens_text) <= 120 else itens_text[:117] + '...'
                except Exception:
                    display_text = str(ped[6]) if ped[6] is not None else ''
                    itens_text = display_text

                cell = QTableWidgetItem(display_text)
                cell.setToolTip(itens_text)
                self.tabela_pedidos.setItem(row, 6, cell)

                # filtro de busca por nome ou telefone (busca simples em cliente, endereco e itens)
                search = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ''
                if search:
                    hay = ' '.join([
                        str(ped[2] or '').lower(),
                        str(ped[3] or '').lower(),
                        itens_text.lower()
                    ])
                    if search not in hay:
                        # remover a linha inserida (não corresponde)
                        self.tabela_pedidos.removeRow(row)
                        continue

                # colorir linha
                color = color_map.get(status.lower(), None)
                if color:
                    for c in range(self.tabela_pedidos.columnCount()):
                        it = self.tabela_pedidos.item(row, c)
                        if it:
                            it.setBackground(color)

                # Armazenar dados completos do pedido no cache usando ID como chave
                self.pedidos_cache[ped_id] = ped

                row += 1
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao carregar pedidos: {e}')

    def _on_pedido_duplo_clique(self, index):
        """Abre diálogo com detalhes do pedido ao duplo-clicar."""
        row = index.row()
        if row < 0:
            QMessageBox.warning(self, 'Erro', 'Selecione um pedido válido.')
            return
        
        # Obter o ID do pedido a partir do UserRole
        item_num = self.tabela_pedidos.item(row, 0)
        if not item_num:
            QMessageBox.warning(self, 'Erro', 'Pedido não encontrado.')
            return
        
        ped_id = item_num.data(Qt.ItemDataRole.UserRole)
        if ped_id is None or ped_id not in self.pedidos_cache:
            QMessageBox.warning(self, 'Erro', 'Dados do pedido não encontrados no cache.')
            return
        
        pedido_data = self.pedidos_cache[ped_id]
        dlg = PedidoDetalhesDialog(pedido_data, parent=self)
        dlg.exec()

    def reimprimir_selecionado(self):
        """Reimprime a comanda do pedido selecionado usando o módulo printer."""
        row = self.tabela_pedidos.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Erro', 'Selecione um pedido para reimprimir.')
            return

        item_num = self.tabela_pedidos.item(row, 0)
        if not item_num:
            QMessageBox.warning(self, 'Erro', 'Pedido não encontrado.')
            return

        ped_id = item_num.data(Qt.ItemDataRole.UserRole)
        if ped_id is None or ped_id not in self.pedidos_cache:
            QMessageBox.warning(self, 'Erro', 'Dados do pedido não encontrados no cache.')
            return

        ped = self.pedidos_cache[ped_id]
        try:
            # preparar comanda a partir dos campos disponíveis no banco
            # Estrutura esperada: id, numero, cliente, endereco, cep, observacoes, itens, total, pagamento, troco, status, data, bairro, numero_endereco
            numero = ped[1] if len(ped) > 1 else ''
            cliente = ped[2] if len(ped) > 2 else ''
            endereco = ped[3] if len(ped) > 3 else ''
            cep = ped[4] if len(ped) > 4 else ''
            observacoes = ped[5] if len(ped) > 5 else ''
            itens_raw = ped[6] if len(ped) > 6 else ''
            total = ped[7] if len(ped) > 7 else 0.0
            pagamento = ped[8] if len(ped) > 8 else ''
            troco = ped[9] if len(ped) > 9 else None
            data = ped[11] if len(ped) > 11 else ''
            bairro = ped[12] if len(ped) > 12 else ''
            numero_end = ped[13] if len(ped) > 13 else ''

            # parse itens
            try:
                if itens_raw is None:
                    itens_list = []
                elif isinstance(itens_raw, str):
                    itens_list = ast.literal_eval(itens_raw)
                else:
                    itens_list = itens_raw
            except Exception:
                itens_list = []

            linhas = [
                "=" * 50,
                "COMANDA DE PEDIDO",
                "=" * 50,
                f"Pedido: {int(numero) if isinstance(numero, (int, float)) or str(numero).isdigit() else numero}",
                f"Cliente: {cliente}",
                f"Endereço: {endereco}, {numero_end}",
                f"Bairro: {bairro}",
                "",
                "=" * 50,
                "ITENS:",
            ]

            # Calcular total dos itens
            total_itens = 0.0
            for it in itens_list:
                try:
                    if isinstance(it, dict):
                        qtd = it.get('qtd') if it.get('qtd') is not None else it.get('quantidade', 1)
                        nome = it.get('nome', 'Item')
                        subtotal = 0.0
                        try:
                            preco = float(it.get('preco') or 0.0)
                            subtotal = preco * (int(qtd) if qtd is not None else 1)
                            total_itens += subtotal
                        except Exception:
                            subtotal = 0.0
                        linhas.append(f"  {qtd}x {nome} - R$ {subtotal:.2f}")
                        # Adicionar observação do item se existir
                        observacao = it.get('observacao', '').strip() if isinstance(it.get('observacao'), str) else ''
                        if observacao:
                            linhas.append(f"     Obs: {observacao}")
                    else:
                        linhas.append(f"  {str(it)}")
                except Exception:
                    linhas.append(str(it))

            # Calcular taxa de entrega (diferença entre total e itens)
            taxa_entrega = float(total or 0.0) - total_itens
            
            linhas.extend([
                "=" * 50,
                "",
            ])
            
            # Incluir taxa de entrega quando presente
            if taxa_entrega > 0:
                linhas.append(f"Taxa de Entrega: R$ {taxa_entrega:.2f}")
            
            linhas.extend([
                "=" * 50,
                f"TOTAL: R$ {float(total or 0.0):.2f}",
                f"Pagamento: {pagamento}",
            ])
            if troco is not None:
                try:
                    linhas.append(f"Troco: R$ {float(troco):.2f}")
                except Exception:
                    linhas.append(f"Troco: {troco}")

            if observacoes:
                linhas.append(f"Observações: {observacoes}")

            linhas.extend([
                "=" * 50,
                "Obrigado pela sua compra!",
            ])

            texto = "\n".join(linhas)

            # chamar a impressão
            try:
                import printer
                printer.imprimir_texto(texto)
                QMessageBox.information(self, 'Impressão', f'Pedido #{numero} enviado para reimpressão.')
            except Exception as e:
                QMessageBox.warning(self, 'Erro', f'Falha ao reimprimir: {e}')

        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao preparar impressão: {e}')

    def copiar_comanda_selecionada(self):
        """Copia a comanda do pedido selecionado para a área de transferência."""
        row = self.tabela_pedidos.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Erro', 'Selecione um pedido para copiar.')
            return

        item_num = self.tabela_pedidos.item(row, 0)
        if not item_num:
            QMessageBox.warning(self, 'Erro', 'Pedido não encontrado.')
            return

        ped_id = item_num.data(Qt.ItemDataRole.UserRole)
        if ped_id is None or ped_id not in self.pedidos_cache:
            QMessageBox.warning(self, 'Erro', 'Dados do pedido não encontrados no cache.')
            return

        ped = self.pedidos_cache[ped_id]
        try:
            # Preparar comanda a partir dos campos disponíveis no banco
            numero = ped[1] if len(ped) > 1 else ''
            cliente = ped[2] if len(ped) > 2 else ''
            endereco = ped[3] if len(ped) > 3 else ''
            cep = ped[4] if len(ped) > 4 else ''
            observacoes = ped[5] if len(ped) > 5 else ''
            itens_raw = ped[6] if len(ped) > 6 else ''
            total = ped[7] if len(ped) > 7 else 0.0
            pagamento = ped[8] if len(ped) > 8 else ''
            troco = ped[9] if len(ped) > 9 else None
            data = ped[11] if len(ped) > 11 else ''
            bairro = ped[12] if len(ped) > 12 else ''
            numero_end = ped[13] if len(ped) > 13 else ''

            # parse itens
            try:
                if itens_raw is None:
                    itens_list = []
                elif isinstance(itens_raw, str):
                    itens_list = ast.literal_eval(itens_raw)
                else:
                    itens_list = itens_raw
            except Exception:
                itens_list = []

            linhas = [
                "=" * 50,
                "COMANDA DE PEDIDO",
                "=" * 50,
                f"Pedido: {int(numero) if isinstance(numero, (int, float)) or str(numero).isdigit() else numero}",
                f"Cliente: {cliente}",
                f"Endereço: {endereco}, {numero_end}",
                f"Bairro: {bairro}",
                "",
                "=" * 50,
                "ITENS:",
            ]

            # Calcular total dos itens
            total_itens = 0.0
            for it in itens_list:
                try:
                    if isinstance(it, dict):
                        qtd = it.get('qtd') if it.get('qtd') is not None else it.get('quantidade', 1)
                        nome = it.get('nome', 'Item')
                        subtotal = 0.0
                        try:
                            preco = float(it.get('preco') or 0.0)
                            subtotal = preco * (int(qtd) if qtd is not None else 1)
                            total_itens += subtotal
                        except Exception:
                            subtotal = 0.0
                        linhas.append(f"  {qtd}x {nome} - R$ {subtotal:.2f}")
                        # Adicionar observação do item se existir
                        observacao = it.get('observacao', '').strip() if isinstance(it.get('observacao'), str) else ''
                        if observacao:
                            linhas.append(f"     Obs: {observacao}")
                    else:
                        linhas.append(f"  {str(it)}")
                except Exception:
                    linhas.append(str(it))

            # Calcular taxa de entrega (diferença entre total e itens)
            taxa_entrega = float(total or 0.0) - total_itens
            
            linhas.extend([
                "=" * 50,
                "",
            ])
            
            # Incluir taxa de entrega quando presente
            if taxa_entrega > 0:
                linhas.append(f"Taxa de Entrega: R$ {taxa_entrega:.2f}")
            
            linhas.extend([
                "=" * 50,
                f"TOTAL: R$ {float(total or 0.0):.2f}",
                f"Pagamento: {pagamento}",
            ])
            if troco is not None:
                try:
                    linhas.append(f"Troco: R$ {float(troco):.2f}")
                except Exception:
                    linhas.append(f"Troco: {troco}")

            if observacoes:
                linhas.append(f"Observações: {observacoes}")

            linhas.extend([
                "=" * 50,
                "Obrigado pela sua compra!",
            ])

            texto = "\n".join(linhas)

            # Copiar para a área de transferência
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(texto)
            QMessageBox.information(self, 'Copiado', f'Comanda do pedido #{numero} copiada para a área de transferência!')

        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao copiar comanda: {e}')

    def editar_pedido_selecionado(self):
        """Abre o diálogo para editar o pedido selecionado."""
        row = self.tabela_pedidos.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Erro', 'Selecione um pedido para editar.')
            return

        item_num = self.tabela_pedidos.item(row, 0)
        if not item_num:
            QMessageBox.warning(self, 'Erro', 'Pedido não encontrado.')
            return

        ped_id = item_num.data(Qt.ItemDataRole.UserRole)
        if ped_id is None or ped_id not in self.pedidos_cache:
            QMessageBox.warning(self, 'Erro', 'Dados do pedido não encontrados no cache.')
            return

        pedido_data = self.pedidos_cache[ped_id]
        
        # Abrir diálogo de edição
        dlg = EditarPedidoDialog(pedido_data, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Obter dados alterados
            dados_novos = dlg.obter_dados_alterados()
            
            # Atualizar no banco de dados
            sucesso = pedidos.atualizar_pedido_completo(
                ped_id,
                endereco=dados_novos['endereco'],
                cep=dados_novos['cep'],
                bairro=dados_novos['bairro'],
                numero_endereco=dados_novos['numero_endereco'],
                itens=dados_novos['itens'],
                pagamento=dados_novos['pagamento'],
                troco=dados_novos['troco'],
                observacoes=dados_novos['observacoes']
            )
            
            if sucesso:
                QMessageBox.information(self, 'Sucesso', f'Pedido #{pedido_data[1]} atualizado com sucesso!')
                self.atualizar_tabela_pedidos()
            else:
                QMessageBox.warning(self, 'Erro', 'Falha ao atualizar o pedido no banco de dados.')

    def criar_aba_vendas(self):
        """Gerenciamento de vendas: filtros e dashboard."""
        widget = QWidget()
        layout = QVBoxLayout()

        titulo = QLabel("Gerenciamento de vendas")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Filtros: presets e intervalos
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Período:"))
        self.vendas_preset = QComboBox()
        self.vendas_preset.addItems(["Hoje", "Esta Semana", "Este Mês", "Intervalo"]) 
        filtro_layout.addWidget(self.vendas_preset)

        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDisplayFormat('yyyy-MM-dd')
        self.data_inicio.setDate(QDate.currentDate())
        self.data_inicio.setVisible(False)
        filtro_layout.addWidget(self.data_inicio)

        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDisplayFormat('yyyy-MM-dd')
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setVisible(False)
        filtro_layout.addWidget(self.data_fim)

        # filtro por prato
        filtro_layout.addWidget(QLabel("Prato:"))
        self.filtro_prato = QComboBox()
        # preencher mais abaixo (quando a aba for criada)
        filtro_layout.addWidget(self.filtro_prato)

        # filtro por usuário (combo + busca parcial)
        filtro_layout.addWidget(QLabel("Usuário:"))
        self.filtro_usuario = QComboBox()
        self.filtro_usuario.addItem('Todos')
        filtro_layout.addWidget(self.filtro_usuario)
        self.filtro_usuario_busca = QLineEdit()
        self.filtro_usuario_busca.setPlaceholderText('Buscar usuário (parte do nome)')
        self.filtro_usuario_busca.setMinimumWidth(200)
        filtro_layout.addWidget(self.filtro_usuario_busca)

        btn_aplicar = QPushButton("Aplicar Filtro")
        btn_aplicar.setObjectName("btnPrimary")
        filtro_layout.addWidget(btn_aplicar)
        filtro_layout.addStretch()
        layout.addLayout(filtro_layout)

        # Indicadores principais
        indicadores = QHBoxLayout()
        # indicadores estilo cartão
        card_style_base = (
            "padding: 8px 12px; border-radius: 8px; font-weight: bold;"
        )

        self.lbl_total_pedidos = QLabel("Pedidos: 0")
        self.lbl_total_pedidos.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #EAF2FB, stop:1 #D6EAF8); color: #154360;"
        )
        self.lbl_total_pedidos.setMinimumHeight(44)
        self.lbl_total_pedidos.setMargin(6)
        indicadores.addWidget(self.lbl_total_pedidos)

        self.lbl_total_vendido = QLabel("Total Itens: R$ 0.00")
        self.lbl_total_vendido.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E8F8F5, stop:1 #D1F2EB); color: #0B5345;"
        )
        self.lbl_total_vendido.setMinimumHeight(44)
        self.lbl_total_vendido.setMargin(6)
        indicadores.addWidget(self.lbl_total_vendido)
        
        # indicador total taxa de entrega
        self.lbl_taxa_entrega = QLabel("Taxa Entrega: R$ 0.00")
        self.lbl_taxa_entrega.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFF4E6, stop:1 #FFE4B5); color: #E67E22;"
        )
        self.lbl_taxa_entrega.setMinimumHeight(44)
        self.lbl_taxa_entrega.setMargin(6)
        indicadores.addWidget(self.lbl_taxa_entrega)
        
        # indicador total geral
        self.lbl_total_geral = QLabel("Total Geral: R$ 0.00")
        self.lbl_total_geral.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E8E8FF, stop:1 #D1D1F5); color: #333333; font-weight: bold;"
        )
        self.lbl_total_geral.setMinimumHeight(44)
        self.lbl_total_geral.setMargin(6)
        indicadores.addWidget(self.lbl_total_geral)
        # indicador total marmitas vendidas
        self.lbl_total_marmitas = QLabel("Marmitas vendidas: 0")
        self.lbl_total_marmitas.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F7E8F8, stop:1 #F2D1F2); color: #6A1B9A; font-weight: bold;"
        )
        self.lbl_total_marmitas.setMinimumHeight(44)
        self.lbl_total_marmitas.setMargin(6)
        indicadores.addWidget(self.lbl_total_marmitas)
        # indicador total outros itens vendidos
        self.lbl_total_outros_itens = QLabel("Outros itens vendidos: 0")
        self.lbl_total_outros_itens.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFF9E6, stop:1 #FFE8B3); color: #7D6608; font-weight: bold;"
        )
        self.lbl_total_outros_itens.setMinimumHeight(44)
        self.lbl_total_outros_itens.setMargin(6)
        indicadores.addWidget(self.lbl_total_outros_itens)
        # indicador do prato selecionado
        self.lbl_prato_info = QLabel("")
        self.lbl_prato_info.setStyleSheet(
            card_style_base + " background: #FFFFFF; border: 1px solid #E6E6E6; color: #333333; font-weight: normal;"
        )
        self.lbl_prato_info.setMinimumHeight(40)
        self.lbl_prato_info.setMargin(6)
        indicadores.addWidget(self.lbl_prato_info)
        indicadores.addStretch()
        layout.addLayout(indicadores)

        # Tabela detalhada por prato
        self.tabela_vendas = QTableWidget()
        self.tabela_vendas.setColumnCount(3)
        self.tabela_vendas.setHorizontalHeaderLabels(["Prato", "Quantidade", "Receita (R$)"])
        self.tabela_vendas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela_vendas.setColumnWidth(1, 120)
        self.tabela_vendas.setColumnWidth(2, 140)
        layout.addWidget(self.tabela_vendas)

        # Tabela por usuário (Usuário, Pedidos, Itens, Total)
        self.tabela_usuarios = QTableWidget()
        self.tabela_usuarios.setColumnCount(4)
        self.tabela_usuarios.setHorizontalHeaderLabels(["Usuário", "Pedidos", "Itens", "Total (R$)"])
        self.tabela_usuarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela_usuarios.setColumnWidth(1, 100)
        self.tabela_usuarios.setColumnWidth(2, 100)
        self.tabela_usuarios.setColumnWidth(3, 140)
        layout.addWidget(self.tabela_usuarios)

        # Botões de exportação
        export_layout = QHBoxLayout()
        btn_export_xlsx = QPushButton("Exportar XLSX")
        btn_export_xlsx.setObjectName("btnPrimary")
        btn_export_xlsx.clicked.connect(lambda: self.export_vendas_xlsx())
        btn_export_pdf = QPushButton("Exportar PDF")
        btn_export_pdf.setObjectName("btnPrimary")
        btn_export_pdf.clicked.connect(lambda: self.export_vendas_pdf())
        export_layout.addWidget(btn_export_xlsx)
        export_layout.addWidget(btn_export_pdf)
        # botão para limpar pedidos de teste e cancelados
        btn_limpar = QPushButton("🧹 Limpar pedidos teste/cancelados")
        btn_limpar.setObjectName("btnDanger")
        btn_limpar.clicked.connect(self._limpar_pedidos_teste_cancelados)
        export_layout.addWidget(btn_limpar)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        widget.setLayout(layout)

        # ligações
        self.vendas_preset.currentTextChanged.connect(lambda v: self._on_preset_change(v))
        btn_aplicar.clicked.connect(self._aplicar_filtro_vendas)
        # preencher combo de pratos e ligar seu sinal
        try:
            pratos_list = pratos.listar_pratos()
            self.filtro_prato.addItem('Todos')
            for p in pratos_list:
                nome = p.get('nome') if isinstance(p, dict) else str(p)
                self.filtro_prato.addItem(nome)
        except Exception:
            self.filtro_prato.addItem('Todos')

        self.filtro_prato.currentTextChanged.connect(lambda v: self._aplicar_filtro_vendas())
        self.filtro_usuario.currentTextChanged.connect(lambda v: self._aplicar_filtro_vendas())
        self.filtro_usuario_busca.textChanged.connect(lambda v: self._aplicar_filtro_vendas())

        # aplicar filtro inicial (Hoje)
        self.vendas_preset.setCurrentText("Hoje")
        self._aplicar_filtro_vendas()
        return widget

    def atualizar_vendas(self):
        """Compat layer: mantém método antigo chamável, redireciona para a nova função."""
        try:
            # por compatibilidade, mostrar vendas do dia
            hoje = QDate.currentDate().toString('yyyy-MM-dd')
            resumo = pedidos.vendas_resumo_por_periodo(hoje, hoje)
            texto = f"=== VENDAS DO DIA ===\n\n"
            texto += f"Quantidade de pedidos: {resumo['total_pedidos']}\n"
            texto += f"Total Itens: R$ {resumo['total_itens']:.2f}\n"
            texto += f"Taxa Entrega: R$ {resumo['taxa_total']:.2f}\n"
            texto += f"Total Geral: R$ {resumo['total_vendido']:.2f}\n\n"
            texto += "Pratos mais pedidos:\n"
            for prato, qtd_prato, _ in resumo['pratos']:
                texto += f"  - {prato}: {qtd_prato}x\n"
            # se houver label_vendas (compat), atualiza
            if hasattr(self, 'label_vendas'):
                self.label_vendas.setText(texto)
        except Exception as e:
            if hasattr(self, 'label_vendas'):
                self.label_vendas.setText(f"Erro ao carregar vendas: {e}")

    def criar_aba_entregas(self):
        """Aba para gerenciar taxa de entrega: visualizar, filtrar e somar todas as taxas."""
        widget = QWidget()
        layout = QVBoxLayout()

        titulo = QLabel("Gerenciamento de Entregas")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        # Filtros: presets e intervalos
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Período:"))
        self.entrega_preset = QComboBox()
        self.entrega_preset.addItems(["Hoje", "Esta Semana", "Este Mês", "Intervalo"]) 
        filtro_layout.addWidget(self.entrega_preset)

        self.entrega_data_inicio = QDateEdit()
        self.entrega_data_inicio.setCalendarPopup(True)
        self.entrega_data_inicio.setDisplayFormat('yyyy-MM-dd')
        self.entrega_data_inicio.setDate(QDate.currentDate())
        self.entrega_data_inicio.setVisible(False)
        filtro_layout.addWidget(self.entrega_data_inicio)

        self.entrega_data_fim = QDateEdit()
        self.entrega_data_fim.setCalendarPopup(True)
        self.entrega_data_fim.setDisplayFormat('yyyy-MM-dd')
        self.entrega_data_fim.setDate(QDate.currentDate())
        self.entrega_data_fim.setVisible(False)
        filtro_layout.addWidget(self.entrega_data_fim)

        # Filtro por status
        filtro_layout.addWidget(QLabel("Status:"))
        self.entrega_filtro_status = QComboBox()
        self.entrega_filtro_status.addItems(["Todos", "Em preparo", "Despachado", "Cancelado"])
        filtro_layout.addWidget(self.entrega_filtro_status)

        # Filtro por bairro
        filtro_layout.addWidget(QLabel("Bairro:"))
        self.entrega_filtro_bairro = QLineEdit()
        self.entrega_filtro_bairro.setPlaceholderText("Digite o bairro (opcional)")
        self.entrega_filtro_bairro.setMaximumWidth(150)
        filtro_layout.addWidget(self.entrega_filtro_bairro)

        btn_aplicar = QPushButton("Aplicar Filtro")
        btn_aplicar.setObjectName("btnPrimary")
        filtro_layout.addWidget(btn_aplicar)
        filtro_layout.addStretch()
        layout.addLayout(filtro_layout)

        # Indicadores principais
        indicadores = QHBoxLayout()
        card_style_base = "padding: 8px 12px; border-radius: 8px; font-weight: bold;"

        self.entrega_lbl_pedidos_entrega = QLabel("Pedidos com Entrega: 0")
        self.entrega_lbl_pedidos_entrega.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E8F4F8, stop:1 #D1E8F0); color: #0B4F6F;"
        )
        self.entrega_lbl_pedidos_entrega.setMinimumHeight(44)
        self.entrega_lbl_pedidos_entrega.setMargin(6)
        indicadores.addWidget(self.entrega_lbl_pedidos_entrega)

        self.entrega_lbl_total_taxa = QLabel("Total Taxas: R$ 0.00")
        self.entrega_lbl_total_taxa.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFE8E8, stop:1 #FFD1D1); color: #8B0000;"
        )
        self.entrega_lbl_total_taxa.setMinimumHeight(44)
        self.entrega_lbl_total_taxa.setMargin(6)
        indicadores.addWidget(self.entrega_lbl_total_taxa)

        self.entrega_lbl_taxa_media = QLabel("Taxa Média: R$ 0.00")
        self.entrega_lbl_taxa_media.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E8E8FF, stop:1 #D1D1F5); color: #333333;"
        )
        self.entrega_lbl_taxa_media.setMinimumHeight(44)
        self.entrega_lbl_taxa_media.setMargin(6)
        indicadores.addWidget(self.entrega_lbl_taxa_media)

        self.entrega_lbl_taxa_max = QLabel("Taxa Máxima: R$ 0.00")
        self.entrega_lbl_taxa_max.setStyleSheet(
            card_style_base + " background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E8F5E9, stop:1 #D1E8D0); color: #1B5E20;"
        )
        self.entrega_lbl_taxa_max.setMinimumHeight(44)
        self.entrega_lbl_taxa_max.setMargin(6)
        indicadores.addWidget(self.entrega_lbl_taxa_max)

        indicadores.addStretch()
        layout.addLayout(indicadores)

        # Tabela detalhada de entregas
        self.tabela_entregas = QTableWidget()
        self.tabela_entregas.setColumnCount(7)
        self.tabela_entregas.setHorizontalHeaderLabels([
            "Pedido #", "Cliente", "Endereço", "Bairro", "Taxa (R$)", "Status", "Data"
        ])
        self.tabela_entregas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_entregas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela_entregas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabela_entregas.setColumnWidth(3, 100)
        self.tabela_entregas.setColumnWidth(4, 100)
        self.tabela_entregas.setColumnWidth(5, 100)
        self.tabela_entregas.setColumnWidth(6, 130)
        self.tabela_entregas.setAlternatingRowColors(True)
        self.tabela_entregas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabela_entregas)

        # Botões de exportação
        export_layout = QHBoxLayout()
        btn_export_xlsx = QPushButton("Exportar XLSX")
        btn_export_xlsx.setObjectName("btnPrimary")
        btn_export_xlsx.clicked.connect(lambda: self.export_entregas_xlsx())
        btn_export_pdf = QPushButton("Exportar PDF")
        btn_export_pdf.setObjectName("btnPrimary")
        btn_export_pdf.clicked.connect(lambda: self.export_entregas_pdf())
        export_layout.addWidget(btn_export_xlsx)
        export_layout.addWidget(btn_export_pdf)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        widget.setLayout(layout)

        # Ligações de sinais
        self.entrega_preset.currentTextChanged.connect(lambda v: self._on_entrega_preset_change(v))
        btn_aplicar.clicked.connect(self._aplicar_filtro_entregas)
        self.entrega_filtro_status.currentTextChanged.connect(lambda v: self._aplicar_filtro_entregas())
        self.entrega_filtro_bairro.textChanged.connect(lambda v: self._aplicar_filtro_entregas())

        # Aplicar filtro inicial (Hoje)
        self.entrega_preset.setCurrentText("Hoje")
        self._aplicar_filtro_entregas()
        return widget

    def _on_entrega_preset_change(self, preset):
        """Mostra/esconde os campos de data conforme o preset selecionado."""
        self.entrega_data_inicio.setVisible(preset == "Intervalo")
        self.entrega_data_fim.setVisible(preset == "Intervalo")
        self._aplicar_filtro_entregas()

    def _aplicar_filtro_entregas(self):
        """Aplica filtros na aba de entregas e atualiza a tabela."""
        try:
            # Obter datas
            preset = self.entrega_preset.currentText()
            from datetime import datetime, timedelta
            hoje = datetime.now().date()

            if preset == "Hoje":
                inicio = fim = hoje
            elif preset == "Esta Semana":
                inicio = hoje - timedelta(days=hoje.weekday())
                fim = hoje
            elif preset == "Este Mês":
                inicio = hoje.replace(day=1)
                fim = hoje
            else:  # Intervalo
                inicio = self.entrega_data_inicio.date().toPyDate()
                fim = self.entrega_data_fim.date().toPyDate()

            inicio_s = inicio.strftime('%Y-%m-%d')
            fim_s = fim.strftime('%Y-%m-%d')

            # Obter pedidos do período
            rows = pedidos.pedidos_por_periodo(inicio_s, fim_s)

            # Aplicar filtros
            status_filter = self.entrega_filtro_status.currentText()
            bairro_filter = self.entrega_filtro_bairro.text().strip().lower()

            entregas_filtradas = []
            total_taxa = 0.0
            total_pedidos_com_entrega = 0

            for row in rows:
                # Coluna 10 = status, Coluna 12 = bairro
                ped_numero, cliente, endereco, cep, obs, itens_raw, total, pagamento, troco, status_db, data, bairro = (
                    row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]
                )

                # Excluir pedidos cancelados (sempre, independente do filtro)
                if (status_db or "").lower() == "cancelado":
                    continue

                # Aplicar filtro de status
                if status_filter != "Todos" and status_filter.lower() != (status_db or "").lower():
                    continue

                # Aplicar filtro de bairro
                if bairro_filter and bairro_filter not in (bairro or "").lower():
                    continue

                # Calcular taxa de entrega
                try:
                    total_val = float(total or 0.0)
                except:
                    total_val = 0.0

                # Pegar itens para calcular total de itens
                try:
                    if itens_raw is None:
                        itens_list = []
                    elif isinstance(itens_raw, str):
                        itens_list = ast.literal_eval(itens_raw)
                    else:
                        itens_list = itens_raw
                except:
                    itens_list = []

                total_itens = 0.0
                for it in itens_list:
                    if isinstance(it, dict):
                        qtd = int((it.get('qtd') if it.get('qtd') is not None else it.get('quantidade')) or 0)
                        preco = float(it.get('preco') or 0.0)
                        total_itens += (qtd * preco)
                    else:
                        total_itens += 0.0

                taxa_entrega = total_val - total_itens

                # Só incluir se houver taxa de entrega
                if taxa_entrega > 0:
                    total_taxa += taxa_entrega
                    total_pedidos_com_entrega += 1
                    entregas_filtradas.append({
                        'numero': ped_numero,
                        'cliente': cliente,
                        'endereco': endereco,
                        'bairro': bairro or "N/A",
                        'taxa': taxa_entrega,
                        'status': status_db or "Desconhecido",
                        'data': data
                    })

            # Atualizar tabela
            self.tabela_entregas.setRowCount(0)
            for i, entrega in enumerate(entregas_filtradas):
                self.tabela_entregas.insertRow(i)
                self.tabela_entregas.setItem(i, 0, QTableWidgetItem(str(entrega['numero'])))
                self.tabela_entregas.setItem(i, 1, QTableWidgetItem(entrega['cliente']))
                self.tabela_entregas.setItem(i, 2, QTableWidgetItem(entrega['endereco']))
                self.tabela_entregas.setItem(i, 3, QTableWidgetItem(entrega['bairro']))
                
                taxa_item = QTableWidgetItem(f"R$ {entrega['taxa']:.2f}")
                taxa_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela_entregas.setItem(i, 4, taxa_item)
                
                self.tabela_entregas.setItem(i, 5, QTableWidgetItem(entrega['status']))
                self.tabela_entregas.setItem(i, 6, QTableWidgetItem(entrega['data']))

            # Atualizar indicadores
            taxa_media = total_taxa / total_pedidos_com_entrega if total_pedidos_com_entrega > 0 else 0.0
            taxa_max = max([e['taxa'] for e in entregas_filtradas], default=0.0)

            self.entrega_lbl_pedidos_entrega.setText(f"Pedidos com Entrega: {total_pedidos_com_entrega}")
            self.entrega_lbl_total_taxa.setText(f"Total Taxas: R$ {total_taxa:.2f}")
            self.entrega_lbl_taxa_media.setText(f"Taxa Média: R$ {taxa_media:.2f}")
            self.entrega_lbl_taxa_max.setText(f"Taxa Máxima: R$ {taxa_max:.2f}")

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao aplicar filtro: {str(e)}")

    def export_entregas_xlsx(self):
        """Exporta dados de entregas em XLSX."""
        try:
            import pandas as pd

            # Coletar dados da tabela
            dados = []
            for i in range(self.tabela_entregas.rowCount()):
                linha = []
                for j in range(self.tabela_entregas.columnCount()):
                    item = self.tabela_entregas.item(i, j)
                    linha.append(item.text() if item else "")
                dados.append(linha)

            df = pd.DataFrame(
                dados,
                columns=["Pedido #", "Cliente", "Endereço", "Bairro", "Taxa (R$)", "Status", "Data"]
            )

            # Adicionar resumo
            total_taxa = 0.0
            for i in range(self.tabela_entregas.rowCount()):
                taxa_text = self.tabela_entregas.item(i, 4).text().replace("R$ ", "").replace(",", ".")
                try:
                    total_taxa += float(taxa_text)
                except:
                    pass

            default_name = f"entregas_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx"
            fname, _ = QFileDialog.getSaveFileName(self, "Salvar XLSX", default_name, "Excel Files (*.xlsx)")
            if not fname:
                return

            with pd.ExcelWriter(fname, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Entregas", index=False)

                # Adicionar resumo em outra aba
                resumo_df = pd.DataFrame({
                    "Métrica": ["Total de Pedidos", "Total de Taxas", "Taxa Média", "Taxa Máxima"],
                    "Valor": [
                        self.tabela_entregas.rowCount(),
                        self.entrega_lbl_total_taxa.text().replace("Total Taxas: R$ ", ""),
                        self.entrega_lbl_taxa_media.text().replace("Taxa Média: R$ ", ""),
                        self.entrega_lbl_taxa_max.text().replace("Taxa Máxima: R$ ", "")
                    ]
                })
                resumo_df.to_excel(writer, sheet_name="Resumo", index=False)

            QMessageBox.information(self, "Exportado", f"Arquivo salvo: {fname}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao exportar XLSX: {e}")

    def export_entregas_pdf(self):
        """Exporta dados de entregas em PDF."""
        try:
            # Obter datas do filtro atual
            preset = self.entrega_preset.currentText()
            from datetime import datetime, timedelta
            hoje = datetime.now().date()

            if preset == "Hoje":
                inicio = fim = hoje
            elif preset == "Esta Semana":
                inicio = hoje - timedelta(days=hoje.weekday())
                fim = hoje
            elif preset == "Este Mês":
                inicio = hoje.replace(day=1)
                fim = hoje
            else:
                inicio = self.entrega_data_inicio.date().toPyDate()
                fim = self.entrega_data_fim.date().toPyDate()

            inicio_s = inicio.strftime('%Y-%m-%d')
            fim_s = fim.strftime('%Y-%m-%d')

            default_name = f"entregas_{inicio_s}_to_{fim_s}.pdf"
            fname, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", default_name, "PDF Files (*.pdf)")
            if not fname:
                return

            # Criar PDF
            c = canvas.Canvas(fname, pagesize=A4)
            width, height = A4
            x = 40
            y = height - 40
            c.setFont('Helvetica-Bold', 14)
            c.drawString(x, y, 'Relatório de Entregas')
            y -= 20
            c.setFont('Helvetica', 10)
            c.drawString(x, y, f'Período: {inicio_s} a {fim_s}')
            y -= 20
            c.drawString(x, y, f"Total de Pedidos: {self.tabela_entregas.rowCount()}")
            y -= 15
            c.drawString(x, y, f"Total de Taxas: {self.entrega_lbl_total_taxa.text().replace('Total Taxas: ', '')}")
            y -= 15
            c.drawString(x, y, f"Taxa Média: {self.entrega_lbl_taxa_media.text().replace('Taxa Média: ', '')}")
            y -= 15
            c.drawString(x, y, f"Taxa Máxima: {self.entrega_lbl_taxa_max.text().replace('Taxa Máxima: ', '')}")
            y -= 25

            # Cabeçalho da tabela
            c.setFont('Helvetica-Bold', 10)
            c.drawString(x, y, 'Pedido')
            c.drawString(x + 60, y, 'Cliente')
            c.drawString(x + 200, y, 'Bairro')
            c.drawString(x + 280, y, 'Taxa (R$)')
            c.drawString(x + 370, y, 'Status')
            y -= 15
            c.setFont('Helvetica', 9)

            # Dados da tabela
            for i in range(self.tabela_entregas.rowCount()):
                if y < 60:
                    c.showPage()
                    y = height - 40

                numero = self.tabela_entregas.item(i, 0).text()
                cliente = self.tabela_entregas.item(i, 1).text()[:20]
                bairro = self.tabela_entregas.item(i, 3).text()[:15]
                taxa = self.tabela_entregas.item(i, 4).text()
                status = self.tabela_entregas.item(i, 5).text()

                c.drawString(x, y, numero)
                c.drawString(x + 60, y, cliente)
                c.drawString(x + 200, y, bairro)
                c.drawRightString(x + 350, y, taxa)
                c.drawString(x + 370, y, status)
                y -= 14

            c.showPage()
            c.save()

            QMessageBox.information(self, "Exportado", f"Arquivo salvo: {fname}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao exportar PDF: {e}")

    def criar_aba_cancelar(self):
        """Aba para cancelar pedidos."""
        widget = QWidget()
        layout = QVBoxLayout()

        titulo = QLabel("Cancelar Pedido")
        titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E86DE;")
        layout.addWidget(titulo)

        layout.addStretch()

        form = QFormLayout()
        self.cancelar_id = QSpinBox()
        self.cancelar_id.setMinimum(1)
        self.cancelar_id.setMaximum(999999)
        # Agora usamos o número visível (numero) para cancelar
        form.addRow("Número do Pedido:", self.cancelar_id)
        layout.addLayout(form)

        btn_cancelar = QPushButton("✕ Cancelar Pedido")
        btn_cancelar.setObjectName("btnDanger")
        btn_cancelar.setFixedHeight(50)
        btn_cancelar.clicked.connect(self.cancelar_pedido)
        layout.addWidget(btn_cancelar)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def cancelar_pedido(self):
        """Cancela e deleta um pedido pelo ID."""
        numero = self.cancelar_id.value()
        # resolver numero -> id
        pedido_db_id = pedidos.obter_id_por_numero(numero)
        if pedido_db_id is None:
            QMessageBox.warning(self, 'Erro', f'Pedido número {numero} não encontrado.')
            return

        reply = QMessageBox.question(self, "Confirmar", f"Cancelar e deletar pedido #{numero}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                pedidos.deletar_pedido(pedido_db_id)
                QMessageBox.information(self, "Sucesso", f"Pedido #{numero} cancelado e removido do banco.")
                # atualizar tabelas/relatórios dependentes
                self.atualizar_tabela_pedidos()
                self._aplicar_filtro_entregas()
                self._aplicar_filtro_vendas()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao cancelar: {e}")

    def _on_preset_change(self, text):
        """Mostrar/esconder campos de data quando escolher Intervalo."""
        if text == 'Intervalo':
            self.data_inicio.setVisible(True)
            self.data_fim.setVisible(True)
        else:
            self.data_inicio.setVisible(False)
            self.data_fim.setVisible(False)

    def _aplicar_filtro_vendas(self):
        """Lê o preset/datas, chama pedidos.vendas_resumo_por_periodo e atualiza o dashboard."""
        preset = self.vendas_preset.currentText()
        hoje = QDate.currentDate()
        if preset == 'Hoje':
            inicio = hoje
            fim = hoje
        elif preset == 'Esta Semana':
            # Últimos 7 dias (de 7 dias atrás até hoje)
            inicio = hoje.addDays(-6)
            fim = hoje
        elif preset == 'Este Mês':
            inicio = QDate(hoje.year(), hoje.month(), 1)
            fim = hoje
        else:
            inicio = self.data_inicio.date()
            fim = self.data_fim.date()

        inicio_s = inicio.toString('yyyy-MM-dd')
        fim_s = fim.toString('yyyy-MM-dd')
        try:
            # aplicar filtros selecionados
            prato_sel = self.filtro_prato.currentText() if hasattr(self, 'filtro_prato') else 'Todos'
            usuario_sel = self.filtro_usuario.currentText() if hasattr(self, 'filtro_usuario') else 'Todos'
            prato_filter = prato_sel if prato_sel and prato_sel != 'Todos' else None
            usuario_filter = usuario_sel if usuario_sel and usuario_sel != 'Todos' else None

            # se o campo de busca parcial tiver texto, usar busca parcial
            usuario_partial = False
            usuario_param = None
            if hasattr(self, 'filtro_usuario_busca') and self.filtro_usuario_busca.text().strip():
                usuario_param = self.filtro_usuario_busca.text().strip()
                usuario_partial = True
            else:
                usuario_param = usuario_filter

            resumo = pedidos.vendas_resumo_por_periodo(inicio_s, fim_s, usuario=usuario_param, prato_filter=prato_filter, usuario_partial=usuario_partial)
            self.lbl_total_pedidos.setText(f"Pedidos: {resumo['total_pedidos']}")
            self.lbl_total_vendido.setText(f"Total Itens: R$ {resumo['total_itens']:.2f}")
            self.lbl_taxa_entrega.setText(f"Taxa Entrega: R$ {resumo['taxa_total']:.2f}")
            self.lbl_total_geral.setText(f"Total Geral: R$ {resumo['total_vendido']:.2f}")
            # total de marmitas vendidas e outros itens
            total_marmitas = resumo.get('total_marmitas', 0)
            total_outros_itens = resumo.get('total_outros_itens', 0)
            self.lbl_total_marmitas.setText(f"Marmitas vendidas: {total_marmitas}")
            self.lbl_total_outros_itens.setText(f"Outros itens vendidos: {total_outros_itens}")

            # preencher tabela de pratos
            self.tabela_vendas.setRowCount(0)
            for idx, (nome, qtd, receita) in enumerate(resumo['pratos']):
                self.tabela_vendas.insertRow(idx)
                self.tabela_vendas.setItem(idx, 0, QTableWidgetItem(str(nome)))
                self.tabela_vendas.setItem(idx, 1, QTableWidgetItem(str(qtd)))
                self.tabela_vendas.setItem(idx, 2, QTableWidgetItem(f"{receita:.2f}"))

            # preencher combo de usuários com base nos pedidos do período
            try:
                pedidos_periodo = pedidos.pedidos_por_periodo(inicio_s, fim_s)
                usuarios = set()
                for r in pedidos_periodo:
                    usuarios.add((r[2] or '').strip())
                usuarios_list = sorted([u for u in usuarios if u])
                # preservar seleção
                cur = self.filtro_usuario.currentText() if hasattr(self, 'filtro_usuario') else None
                if hasattr(self, 'filtro_usuario'):
                    self.filtro_usuario.blockSignals(True)
                    self.filtro_usuario.clear()
                    self.filtro_usuario.addItem('Todos')
                    for u in usuarios_list:
                        self.filtro_usuario.addItem(u)
                    if cur and cur in [self.filtro_usuario.itemText(i) for i in range(self.filtro_usuario.count())]:
                        self.filtro_usuario.setCurrentText(cur)
                    self.filtro_usuario.blockSignals(False)
            except Exception:
                pass

            # preencher tabela de usuários com resumo (opcionalmente filtrado por prato e usuário)
            try:
                usuarios_resumo = pedidos.resumo_por_usuario(inicio_s, fim_s, prato_filter=prato_filter, usuario_filter=usuario_filter)
                self.tabela_usuarios.setRowCount(0)
                for idx, (usuario, qtd_ped, qtd_itens, gasto) in enumerate(usuarios_resumo):
                    self.tabela_usuarios.insertRow(idx)
                    self.tabela_usuarios.setItem(idx, 0, QTableWidgetItem(str(usuario)))
                    self.tabela_usuarios.setItem(idx, 1, QTableWidgetItem(str(qtd_ped)))
                    self.tabela_usuarios.setItem(idx, 2, QTableWidgetItem(str(qtd_itens)))
                    self.tabela_usuarios.setItem(idx, 3, QTableWidgetItem(f"R$ {gasto:.2f}"))
            except Exception:
                pass

            # mostrar métricas do prato selecionado (se houver)
            try:
                selecionado = self.filtro_prato.currentText() if hasattr(self, 'filtro_prato') else 'Todos'
                if not selecionado or selecionado == 'Todos':
                    self.lbl_prato_info.setText('')
                else:
                    found = None
                    for nome, qtd, receita in resumo['pratos']:
                        if str(nome) == str(selecionado):
                            found = (qtd, receita)
                            break
                    if found:
                        self.lbl_prato_info.setText(f"{selecionado} — Quantidade: {found[0]} — Receita: R$ {found[1]:.2f}")
                    else:
                        self.lbl_prato_info.setText(f"{selecionado} — Quantidade: 0 — Receita: R$ 0.00")
            except Exception:
                self.lbl_prato_info.setText('')
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Falha ao gerar relatório: {e}')

    def _limpar_pedidos_teste_cancelados(self):
        """Aciona a exclusão de pedidos de teste e pedidos cancelados do banco."""
        reply = QMessageBox.question(self, 'Confirmar', 'Excluir todos os pedidos de teste e pedidos cancelados? Esta operação é irreversível.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted = pedidos.excluir_testes_e_cancelados()
            QMessageBox.information(self, 'Limpeza concluída', f'{deleted} pedido(s) excluído(s).')
            # atualizar visualizações/relatórios
            self._aplicar_filtro_vendas()
            self.atualizar_tabela_pedidos()
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Falha ao excluir pedidos: {e}')

    def export_vendas_xlsx(self):
        """Exporta o relatório de vendas como arquivo XLSX."""
        # reutiliza a lógica de período do filtro
        try:
            preset = self.vendas_preset.currentText()
            hoje = QDate.currentDate()
            if preset == 'Hoje':
                inicio = hoje
                fim = hoje
            elif preset == 'Esta Semana':
                dia_sem = hoje.dayOfWeek()
                inicio = hoje.addDays(1 - dia_sem)
                fim = hoje
            elif preset == 'Este Mês':
                inicio = QDate(hoje.year(), hoje.month(), 1)
                fim = hoje
            else:
                inicio = self.data_inicio.date()
                fim = self.data_fim.date()

            inicio_s = inicio.toString('yyyy-MM-dd')
            fim_s = fim.toString('yyyy-MM-dd')

            resumo = pedidos.vendas_resumo_por_periodo(inicio_s, fim_s)
            # cria DataFrame
            df = pd.DataFrame(resumo.get('pratos', []), columns=['Prato', 'Quantidade', 'Receita'])

            default_name = f"vendas_{inicio_s}_to_{fim_s}.xlsx"
            fname, _ = QFileDialog.getSaveFileName(self, "Salvar XLSX", default_name, "Excel Files (*.xlsx)")
            if not fname:
                return

            # gravar com resumo e detalhes
            with pd.ExcelWriter(fname, engine='openpyxl') as writer:
                summary_df = pd.DataFrame({
                    'Métrica': ['Total Pedidos', 'Total Itens', 'Taxa Entrega', 'Total Geral', 'Marmitas vendidas', 'Outros itens vendidos'],
                    'Valor': [
                        resumo.get('total_pedidos', 0),
                        resumo.get('total_itens', 0.0),
                        resumo.get('taxa_total', 0.0),
                        resumo.get('total_vendido', 0.0),
                        resumo.get('total_marmitas', 0),
                        resumo.get('total_outros_itens', 0)
                    ]
                })
                summary_df.to_excel(writer, index=False, sheet_name='Resumo')
                df.to_excel(writer, index=False, sheet_name='Pratos')

            QMessageBox.information(self, 'Exportado', f'Arquivo salvo: {fname}')
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Falha ao exportar XLSX: {e}')

    def export_vendas_pdf(self):
        """Exporta o relatório de vendas como PDF simples."""
        try:
            preset = self.vendas_preset.currentText()
            hoje = QDate.currentDate()
            if preset == 'Hoje':
                inicio = hoje
                fim = hoje
            elif preset == 'Esta Semana':
                dia_sem = hoje.dayOfWeek()
                inicio = hoje.addDays(1 - dia_sem)
                fim = hoje
            elif preset == 'Este Mês':
                inicio = QDate(hoje.year(), hoje.month(), 1)
                fim = hoje
            else:
                inicio = self.data_inicio.date()
                fim = self.data_fim.date()

            inicio_s = inicio.toString('yyyy-MM-dd')
            fim_s = fim.toString('yyyy-MM-dd')

            resumo = pedidos.vendas_resumo_por_periodo(inicio_s, fim_s)

            default_name = f"vendas_{inicio_s}_to_{fim_s}.pdf"
            fname, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", default_name, "PDF Files (*.pdf)")
            if not fname:
                return

            # criar PDF
            c = canvas.Canvas(fname, pagesize=A4)
            width, height = A4
            x = 40
            y = height - 40
            c.setFont('Helvetica-Bold', 14)
            c.drawString(x, y, 'Relatório de Vendas')
            y -= 20
            c.setFont('Helvetica', 10)
            c.drawString(x, y, f'Período: {inicio_s} a {fim_s}')
            y -= 20
            c.drawString(x, y, f"Total de Pedidos: {resumo.get('total_pedidos', 0)}")
            y -= 15
            c.drawString(x, y, f"Total Itens: R$ {resumo.get('total_itens', 0.0):.2f}")
            y -= 15
            c.drawString(x, y, f"Taxa Entrega: R$ {resumo.get('taxa_total', 0.0):.2f}")
            y -= 15
            c.drawString(x, y, f"Total Geral: R$ {resumo.get('total_vendido', 0.0):.2f}")
            y -= 15
            c.drawString(x, y, f"Marmitas vendidas: {resumo.get('total_marmitas', 0)}")
            y -= 15
            c.drawString(x, y, f"Outros itens vendidos: {resumo.get('total_outros_itens', 0)}")
            y -= 25

            c.setFont('Helvetica-Bold', 11)
            c.drawString(x, y, 'Prato')
            c.drawString(x + 300, y, 'Quantidade')
            c.drawString(x + 420, y, 'Receita (R$)')
            y -= 15
            c.setFont('Helvetica', 10)

            for prato, qtd, receita in resumo.get('pratos', []):
                if y < 60:
                    c.showPage()
                    y = height - 40
                c.drawString(x, y, str(prato))
                c.drawString(x + 300, y, str(qtd))
                c.drawRightString(x + 520, y, f"{receita:.2f}")
                y -= 14

            c.showPage()
            c.save()

            QMessageBox.information(self, 'Exportado', f'Arquivo salvo: {fname}')
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Falha ao exportar PDF: {e}')

    def marcar_despachado_selecionado(self):
        """Alterna o status entre 'Em preparo' e 'Despachado'."""
        row = self.tabela_pedidos.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Erro', 'Selecione um pedido para alterar status.')
            return

        numero_item = self.tabela_pedidos.item(row, 0)
        status_item = self.tabela_pedidos.item(row, 4)
        if not numero_item or not status_item:
            QMessageBox.warning(self, 'Erro', 'Seleção inválida.')
            return

        cur_status = (status_item.text() or '').strip().lower()
        if cur_status == 'cancelado':
            QMessageBox.warning(self, 'Operação não permitida', 'Pedido cancelado não pode ser alterado.')
            return

        # Alternar entre Em preparo <-> Despachado
        novo_status = 'Despachado' if cur_status == 'em preparo' else 'Em preparo' if cur_status == 'despachado' else None
        if novo_status is None:
            QMessageBox.information(self, 'Info', 'Apenas pedidos em "Em preparo" ou "Despachado" podem ser alterados.')
            return

        # número visível
        numero = int(numero_item.text())
        pedido_db_id = pedidos.obter_id_por_numero(numero)
        if pedido_db_id is None:
            QMessageBox.warning(self, 'Erro', f'Pedido número {numero} não encontrado no banco.')
            return

        try:
            pedidos.editar_pedido(pedido_db_id, 'status', novo_status)
            QMessageBox.information(self, 'Sucesso', f'Pedido #{numero} marcado como {novo_status}.')
            self.atualizar_tabela_pedidos()
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Falha ao atualizar status: {e}')
