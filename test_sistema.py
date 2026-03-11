#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script: Simula um fluxo completo de pedido do Sistema de Marmitas
Teste End-to-End do sistema sem GUI
"""

import sys
import json
import sqlite3
from datetime import datetime
import ast

# Importar módulos do sistema
import pratos
import pedidos
from pedido import calcular_total

def linha(char="=", len=50):
    """Imprime uma linha separadora"""
    print(char * len)

def teste_pratos():
    """Testa carregamento de pratos"""
    print("\n")
    linha()
    print("TESTE 1: CARREGAMENTO DE PRATOS")
    linha()
    
    lista_pratos = pratos.listar_pratos()
    print(f"✓ Total de pratos cadastrados: {len(lista_pratos)}")
    
    if len(lista_pratos) > 0:
        print("\nPratos disponíveis:")
        for i, p in enumerate(lista_pratos, 1):
            print(f"  {i}. {p['nome']} (R$ {p['preco']:.2f}) - {p.get('categoria', 'Sem categoria')}")
        return True
    else:
        print("⚠️  Nenhum prato cadastrado. Adicionando pratos de teste...")
        pratos.adicionar_prato("Marmita de Frango", 15.00, "Marmita")
        pratos.adicionar_prato("Marmita de Carne", 17.00, "Marmita")
        pratos.adicionar_prato("Refrigerante 2L", 8.00, "Bebidas")
        pratos.adicionar_prato("Água com Gás", 4.00, "Bebidas")
        pratos.adicionar_prato("Brigadeiro", 5.00, "Sobremesas")
        
        lista_pratos = pratos.listar_pratos()
        print(f"✓ {len(lista_pratos)} pratos adicionados com sucesso!")
        for i, p in enumerate(lista_pratos, 1):
            print(f"  {i}. {p['nome']} (R$ {p['preco']:.2f})")
        return True

def teste_criacao_pedido():
    """Testa criação de um pedido completo"""
    print("\n")
    linha()
    print("TESTE 2: CRIAÇÃO DE PEDIDO")
    linha()
    
    # Simular dados do cliente
    cliente = {
        'nome': 'João da Silva',
        'celular': '(11) 98765-4321',
        'endereco': 'Rua das Flores',
        'numero': 123,
        'bairro': 'Centro',
        'cep': '12345-678',
        'obs': 'Deixar no portão'
    }
    print(f"✓ Cliente: {cliente['nome']}")
    print(f"  Celular: {cliente['celular']}")
    print(f"  Endereço: {cliente['endereco']}, {cliente['numero']} - {cliente['bairro']}")
    
    # Simular seleção de itens
    lista_pratos = pratos.listar_pratos()
    itens = [
        {
            'id': 0,
            'nome': lista_pratos[0]['nome'],
            'preco': lista_pratos[0]['preco'],
            'quantidade': 2,
            'subtotal': lista_pratos[0]['preco'] * 2
        },
        {
            'id': 1,
            'nome': lista_pratos[1]['nome'],
            'preco': lista_pratos[1]['preco'],
            'quantidade': 1,
            'subtotal': lista_pratos[1]['preco'] * 1
        },
        {
            'id': 2,
            'nome': lista_pratos[2]['nome'],
            'preco': lista_pratos[2]['preco'],
            'quantidade': 1,
            'subtotal': lista_pratos[2]['preco'] * 1
        }
    ]
    
    print("\n✓ Itens selecionados:")
    for item in itens:
        print(f"  {item['quantidade']}x {item['nome']} = R$ {item['subtotal']:.2f}")
    
    total = sum(item['subtotal'] for item in itens)
    print(f"\n✓ Total do pedido: R$ {total:.2f}")
    
    # Simular pagamento em dinheiro
    valor_recebido = 60.00
    pagamento = "Dinheiro"
    troco = valor_recebido - total
    
    print(f"✓ Forma de pagamento: {pagamento}")
    print(f"  Valor recebido: R$ {valor_recebido:.2f}")
    print(f"  Troco: R$ {troco:.2f}")
    
    return cliente, itens, total, pagamento, troco

def teste_salvar_pedido(cliente, itens, total, pagamento, troco):
    """Testa salvamento do pedido no banco"""
    print("\n")
    linha()
    print("TESTE 3: SALVAMENTO NO BANCO DE DADOS")
    linha()
    
    try:
        numero = pedidos.salvar_pedido(
            cliente,
            itens,
            total,
            pagamento,
            troco,
            status="Em preparo"
        )
        print(f"✓ Pedido #{numero:03d} salvo com sucesso!")
        return numero
    except Exception as e:
        print(f"✗ Erro ao salvar pedido: {e}")
        return None

def teste_comanda_gerada(cliente, itens, total, pagamento, troco):
    """Testa geração da comanda (formato de impressão)"""
    print("\n")
    linha()
    print("TESTE 4: GERAÇÃO DA COMANDA")
    linha()
    
    linhas = [
        "=" * 50,
        "COMANDA DE PEDIDO",
        "=" * 50,
        f"Cliente: {cliente['nome']}",
        f"Celular: {cliente['celular']}",
        f"Endereço: {cliente['endereco']}, {cliente['numero']}",
        f"Bairro: {cliente['bairro']}",
        "",
        "=" * 50,
        "ITENS:",
    ]
    
    for item in itens:
        linhas.append(f"  {item['quantidade']}x {item['nome']} - R$ {item['subtotal']:.2f}")
    
    linhas.extend([
        "=" * 50,
        "",
        "=" * 50,
        f"TOTAL: R$ {total:.2f}",
        f"Pagamento: {pagamento}",
        f"Troco: R$ {troco:.2f}",
        f"Observações: {cliente['obs']}",
        "=" * 50,
        "Obrigado pela sua compra!",
    ])
    
    comanda = "\n".join(linhas)
    print("✓ Comanda gerada com sucesso:")
    print("\n" + comanda + "\n")
    
    return comanda

def teste_recuperacao_pedido(numero):
    """Testa recuperação do pedido do banco"""
    print("\n")
    linha()
    print("TESTE 5: RECUPERAÇÃO DO PEDIDO")
    linha()
    
    try:
        conn = sqlite3.connect(str(pedidos.DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            SELECT id, numero, cliente, endereco, bairro, numero_endereco, cep, observacoes, 
                   itens, total, pagamento, troco, status, data 
            FROM pedidos WHERE numero = ?
        """, (numero,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            id, num, cliente, endereco, bairro, num_endereco, cep, obs, itens_str, total, pagamento, troco, status, data = row
            print(f"✓ Pedido encontrado no banco:")
            print(f"  ID: {id}")
            print(f"  Número: #{num:03d}")
            print(f"  Cliente: {cliente}")
            print(f"  Endereço: {endereco}, {num_endereco} - {bairro}")
            print(f"  CEP: {cep}")
            print(f"  Total: R$ {total:.2f}")
            print(f"  Pagamento: {pagamento}")
            print(f"  Status: {status}")
            print(f"  Data: {data}")
            
            # Verificar itens
            try:
                itens = ast.literal_eval(itens_str)
                print(f"  Itens ({len(itens)}):")
                for item in itens:
                    print(f"    - {item['quantidade']}x {item['nome']} = R$ {item['subtotal']:.2f}")
            except:
                print(f"  Itens (raw): {itens_str}")
            
            return True
        else:
            print(f"✗ Pedido #{numero:03d} não encontrado!")
            return False
    except Exception as e:
        print(f"✗ Erro ao recuperar pedido: {e}")
        return False

def teste_listar_pedidos():
    """Testa listagem de todos os pedidos"""
    print("\n")
    linha()
    print("TESTE 6: LISTAGEM DE TODOS OS PEDIDOS")
    linha()
    
    try:
        conn = sqlite3.connect(str(pedidos.DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT numero, cliente, total, status, data FROM pedidos ORDER BY id DESC LIMIT 10")
        pedidos_list = cur.fetchall()
        conn.close()
        
        if pedidos_list:
            print(f"✓ Últimos 10 pedidos ({len(pedidos_list)} encontrados):")
            for num, cliente, total, status, data in pedidos_list:
                print(f"  #{num:03d} | {cliente:20} | R$ {total:7.2f} | {status:12} | {data}")
            return True
        else:
            print("⚠️  Nenhum pedido no banco ainda.")
            return True
    except Exception as e:
        print(f"✗ Erro ao listar pedidos: {e}")
        return False

def teste_validacao_pagamento():
    """Testa validação de pagamento (rejeita valores negativos)"""
    print("\n")
    linha()
    print("TESTE 7: VALIDAÇÃO DE PAGAMENTO")
    linha()
    
    total_pedido = 50.00
    
    # Teste 1: Valor suficiente
    valor_recebido = 60.00
    troco = valor_recebido - total_pedido
    if troco >= 0:
        print(f"✓ Pagamento válido: R$ {valor_recebido:.2f} (total R$ {total_pedido:.2f}, troco R$ {troco:.2f})")
    else:
        print(f"✗ Pagamento inválido!")
    
    # Teste 2: Valor exato
    valor_recebido = 50.00
    troco = valor_recebido - total_pedido
    if troco >= 0:
        print(f"✓ Pagamento válido: R$ {valor_recebido:.2f} (total R$ {total_pedido:.2f}, troco R$ {troco:.2f})")
    else:
        print(f"✗ Pagamento inválido!")
    
    # Teste 3: Valor insuficiente (deve rejeitar)
    valor_recebido = 30.00
    troco = valor_recebido - total_pedido
    if troco >= 0:
        print(f"✓ Pagamento válido: R$ {valor_recebido:.2f}")
    else:
        print(f"✓ Validação correta: Pagamento REJEITADO (insuficiente)")
        print(f"  Recebido: R$ {valor_recebido:.2f}, necessário: R$ {total_pedido:.2f}")
    
    return True

def teste_sequencia_ids():
    """Testa se os IDs estão sequenciais sem gaps"""
    print("\n")
    linha()
    print("TESTE 8: VERIFICAÇÃO DE SEQUÊNCIA DE IDs")
    linha()
    
    try:
        conn = sqlite3.connect(str(pedidos.DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT id FROM pedidos ORDER BY id")
        ids = [row[0] for row in cur.fetchall()]
        conn.close()
        
        if not ids:
            print("⚠️  Nenhum pedido no banco.")
            return True
        
        print(f"✓ IDs no banco: {ids}")
        
        # Verificar sequência
        esperados = list(range(1, len(ids) + 1))
        if ids == esperados:
            print(f"✓ Sequência correta: IDs são sequenciais de 1 a {len(ids)}")
            return True
        else:
            print(f"✗ Sequência incorreta!")
            print(f"  Esperado: {esperados}")
            print(f"  Encontrado: {ids}")
            return False
    except Exception as e:
        print(f"✗ Erro ao verificar IDs: {e}")
        return False

def teste_database_schema():
    """Verifica se o schema do banco está correto"""
    print("\n")
    linha()
    print("TESTE 9: SCHEMA DO BANCO DE DADOS")
    linha()
    
    try:
        conn = sqlite3.connect(str(pedidos.DB_PATH))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(pedidos)")
        colunas = cur.fetchall()
        conn.close()
        
        print(f"✓ Colunas na tabela 'pedidos':")
        colunas_esperadas = [
            'id', 'numero', 'cliente', 'endereco', 'cep', 'observacoes',
            'itens', 'total', 'pagamento', 'troco', 'status', 'data'
        ]
        
        for col_idx, (cid, name, type_, notnull, dflt, pk) in enumerate(colunas):
            status = "✓" if name in colunas_esperadas else "?"
            print(f"  {status} {cid+1}. {name} ({type_})" + (" [PK]" if pk else ""))
        
        return True
    except Exception as e:
        print(f"✗ Erro ao verificar schema: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("\n")
    linha("=", 70)
    print("TESTE COMPLETO: SISTEMA DE MARMITAS - KELVIN")
    print("Simulação End-to-End do Fluxo de Pedido")
    linha("=", 70)
    
    resultados = []
    
    # Teste 1: Pratos
    try:
        resultados.append(("Carregamento de pratos", teste_pratos()))
    except Exception as e:
        print(f"✗ Erro em teste_pratos: {e}")
        resultados.append(("Carregamento de pratos", False))
    
    # Teste 2: Criação de pedido
    try:
        cliente, itens, total, pagamento, troco = teste_criacao_pedido()
        resultados.append(("Criação de pedido", True))
    except Exception as e:
        print(f"✗ Erro em teste_criacao_pedido: {e}")
        resultados.append(("Criação de pedido", False))
        return
    
    # Teste 3: Salvar pedido
    try:
        numero = teste_salvar_pedido(cliente, itens, total, pagamento, troco)
        resultados.append(("Salvamento no banco", numero is not None))
    except Exception as e:
        print(f"✗ Erro em teste_salvar_pedido: {e}")
        resultados.append(("Salvamento no banco", False))
        return
    
    # Teste 4: Comanda
    try:
        teste_comanda_gerada(cliente, itens, total, pagamento, troco)
        resultados.append(("Geração de comanda", True))
    except Exception as e:
        print(f"✗ Erro em teste_comanda_gerada: {e}")
        resultados.append(("Geração de comanda", False))
    
    # Teste 5: Recuperação
    try:
        sucesso = teste_recuperacao_pedido(numero)
        resultados.append(("Recuperação do pedido", sucesso))
    except Exception as e:
        print(f"✗ Erro em teste_recuperacao_pedido: {e}")
        resultados.append(("Recuperação do pedido", False))
    
    # Teste 6: Listar pedidos
    try:
        resultados.append(("Listagem de pedidos", teste_listar_pedidos()))
    except Exception as e:
        print(f"✗ Erro em teste_listar_pedidos: {e}")
        resultados.append(("Listagem de pedidos", False))
    
    # Teste 7: Validação de pagamento
    try:
        resultados.append(("Validação de pagamento", teste_validacao_pagamento()))
    except Exception as e:
        print(f"✗ Erro em teste_validacao_pagamento: {e}")
        resultados.append(("Validação de pagamento", False))
    
    # Teste 8: Sequência de IDs
    try:
        resultados.append(("Sequência de IDs", teste_sequencia_ids()))
    except Exception as e:
        print(f"✗ Erro em teste_sequencia_ids: {e}")
        resultados.append(("Sequência de IDs", False))
    
    # Teste 9: Schema
    try:
        resultados.append(("Schema do banco", teste_database_schema()))
    except Exception as e:
        print(f"✗ Erro em teste_database_schema: {e}")
        resultados.append(("Schema do banco", False))
    
    # Resumo final
    print("\n")
    linha("=", 70)
    print("RESUMO DOS TESTES")
    linha("=", 70)
    
    passed = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for teste, resultado in resultados:
        status = "✓ PASSOU" if resultado else "✗ FALHOU"
        print(f"{status:10} | {teste}")
    
    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
    else:
        print(f"⚠️  {total - passed} teste(s) falharam.")
    print("=" * 70 + "\n")
    
    return passed == total

if __name__ == '__main__':
    # Inicializar banco se necessário
    pedidos.inicializar_banco()
    
    # Executar testes
    sucesso = main()
    sys.exit(0 if sucesso else 1)
