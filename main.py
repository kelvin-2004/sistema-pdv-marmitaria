# main.py
import clientes
import pedido
import printer
import pedidos   # módulo para salvar pedidos

def main():
    pedidos.inicializar_banco()

    try:
        cliente = clientes.coletar_cliente()
    except Exception as e:
        print(f"Erro nos dados do cliente: {e}")
        return

    itens = pedido.escolher_itens()
    if not itens:
        print("Nenhum item selecionado. Cancelando.")
        return

    # Pergunta forma de pagamento logo no início
    pagamento = input("Forma de pagamento (Dinheiro/PIX/Cartão): ").strip().lower() or "dinheiro"
    total = pedido.calcular_total(itens)
    troco = None

    # Lógica para dinheiro
    if pagamento == "dinheiro":
        while True:
            valor_txt = input(f"Valor entregue pelo cliente (Total R$ {total:.2f}): ").strip()
            try:
                valor_pago = float(valor_txt.replace(",", "."))
                if valor_pago < total:
                    print("Valor insuficiente, informe um valor maior ou igual ao total.")
                    continue
                troco = valor_pago - total
                break
            except ValueError:
                print("Digite um valor válido (ex: 50 ou 50,00).")

    # Lógica para PIX
    elif pagamento == "pix":
        status_pix = input("O pagamento já foi feito no PIX? (s/N): ").strip().lower()
        if status_pix == "s":
            pagamento = "Já foi pago no PIX"
        else:
            pagamento = "PIX"

    # Lógica para cartão
    elif pagamento == "cartão":
        pagamento = "Cartão"

    texto = pedido.formatar_comanda(cliente, itens, pagamento=pagamento)

    if troco is not None:
        texto += f"Troco: R$ {troco:.2f}\n"

    # Pré-visualização
    print("\n--- Pré-visualização da comanda ---")
    print(texto)

    confirma = input("Imprimir? (s/N): ").strip().lower()
    if confirma == "s":
        printer.imprimir_texto(texto)
        print("Comanda impressa.")

        # salva no banco de pedidos depois da impressão
        try:
            pedidos.salvar_pedido(cliente, itens, total, pagamento, troco)
            print("Pedido registrado no banco de dados.")
        except Exception as e:
            print(f"Falha ao salvar pedido no banco: {e}")
    else:
        print("Impressão cancelada.")

if __name__ == "__main__":
    main()