#!/usr/bin/env python3
# Script de teste para verificar se as observações estão funcionando

# Simular itens com observações
itens = [
    {
        'id': 0,
        'nome': 'Marmita de Frango',
        'preco': 15.00,
        'quantidade': 2,
        'subtotal': 30.00,
        'observacao': 'sem feijão'
    },
    {
        'id': 1,
        'nome': 'Refrigerante 2L',
        'preco': 8.00,
        'quantidade': 1,
        'subtotal': 8.00
    },
    {
        'id': 2,
        'nome': 'Marmita de Carne',
        'preco': 16.00,
        'quantidade': 1,
        'subtotal': 16.00,
        'observacao': 'bem quente, sem cebola'
    }
]

cliente = {
    'nome': 'João Silva',
    'celular': '(11) 98765-4321',
    'endereco': 'Rua das Flores',
    'numero': 123,
    'bairro': 'Centro',
    'obs': ''
}

# Gerar comanda
total = sum(item['subtotal'] for item in itens)
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
    # Adicionar observação do item se existir
    if item.get('observacao'):
        linhas.append(f"       ➜ {item['observacao']}")

linhas.extend([
    "=" * 50,
    f"TOTAL: R$ {total:.2f}",
    f"Pagamento: Dinheiro",
    "=" * 50,
    "Obrigado pela sua compra!",
])

comanda = "\n".join(linhas)
print(comanda)
