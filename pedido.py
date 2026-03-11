# pedido.py
import pratos


def carregar_pratos():
    """Retorna a lista de pratos cadastrados (baseado em storage.json)."""
    return pratos.listar_pratos()

def escolher_itens():
    pratos = carregar_pratos()
    itens = []

    print("\n=== Catálogo de Pratos ===")
    for i, prato in enumerate(pratos, start=1):
        print(f"{i}) {prato['nome']} - R$ {prato['preco']:.2f}")

    while True:
        escolha = input("Número do prato (ou ENTER para finalizar): ").strip()
        if escolha == "":
            break
        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(pratos):
                qtd = int(input("Quantidade: "))
                itens.append({
                    "nome": pratos[idx]["nome"],
                    "preco": pratos[idx]["preco"],
                    "qtd": qtd
                })
            else:
                print("Número inválido.")
        except ValueError:
            print("Entrada inválida.")
    return itens

def calcular_total(itens):
    return sum(item["preco"] * item["qtd"] for item in itens)

def formatar_comanda(cliente, itens, pagamento):
    total = calcular_total(itens)
    linhas = []
    linhas.append("=== COMANDA ===")
    linhas.append(f"Cliente: {cliente['nome']}")
    linhas.append(f"Endereço: {cliente['endereco']}")
    linhas.append(f"CEP: {cliente['cep']}")
    if cliente.get("observacoes"):
        linhas.append(f"Obs: {cliente['observacoes']}")
    linhas.append("-----------------------------")
    for item in itens:
        linhas.append(f"{item['qtd']}x {item['nome']}  R$ {item['preco'] * item['qtd']:.2f}")
    linhas.append("-----------------------------")
    linhas.append(f"Total: R$ {total:.2f}")
    linhas.append(f"Pagamento: {pagamento}")
    # ❌ removida a linha "Obrigado!"
    return "\n".join(linhas)

if __name__ == "__main__":
    # Teste rápido
    cliente = {"nome": "Teste", "endereco": "Rua X, 123", "cep": "00000000"}
    itens = escolher_itens()
    texto = formatar_comanda(cliente, itens, "Dinheiro")
    print(texto)