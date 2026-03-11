# pedidos.py
import sqlite3
from datetime import datetime, date
import csv
import ast
from pathlib import Path
import pratos

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pedidos.db"

def inicializar_banco():
    """Cria a tabela de pedidos se não existir"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER,
            cliente TEXT,
            endereco TEXT,
            cep TEXT,
            observacoes TEXT,
            itens TEXT,
            total REAL,
            pagamento TEXT,
            troco REAL,
            status TEXT,
            data TEXT,
            bairro TEXT,
            numero_endereco INTEGER
        )
    """)
    conn.commit()
    conn.close()


def zerar_banco():
    """Exclui o banco de dados e recria a tabela vazia."""
    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
    except Exception:
        pass
    inicializar_banco()

def proximo_numero():
    """Retorna o próximo número sequencial de pedido"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT MAX(numero) FROM pedidos")
    ultimo = cur.fetchone()[0]
    conn.close()
    return (ultimo or 0) + 1

def salvar_pedido(cliente, itens, total, pagamento, troco=None, status="Em preparo"):
    """Salva um pedido no banco"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    numero = proximo_numero()
    cur.execute("""
        INSERT INTO pedidos (numero, cliente, endereco, cep, observacoes, itens, total, pagamento, troco, status, data, bairro, numero_endereco)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero,
        cliente["nome"],
        cliente["endereco"],
        cliente["cep"],
        cliente.get("obs", ""),
        str(itens),
        total,
        pagamento,
        troco,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        cliente.get("bairro", ""),
        cliente.get("numero", 0)
    ))
    conn.commit()
    conn.close()
    return numero

def listar_pedidos():
    """Retorna todos os pedidos registrados"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    # Mostrar pedidos com ids menores primeiro (ordem ascendente)
    cur.execute("SELECT * FROM pedidos ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return rows

def excluir_pedido(pedido_id):
    """Exclui um pedido pelo ID e reorganiza os IDs dos pedidos restantes para manter sequência"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # Excluir o pedido
    cur.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    conn.commit()
    
    # Reorganizar IDs para manter sequência contínua
    cur.execute("SELECT id FROM pedidos ORDER BY id ASC")
    ids_existentes = [row[0] for row in cur.fetchall()]
    
    # Se houver gaps, reorganizar
    if ids_existentes:
        for novo_id, id_antigo in enumerate(ids_existentes, 1):
            if novo_id != id_antigo:
                cur.execute("UPDATE pedidos SET id = ? WHERE id = ?", (novo_id, id_antigo))
        conn.commit()
    
    conn.close()

def editar_pedido(pedido_id, campo, novo_valor):
    """Edita um campo específico de um pedido"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(f"UPDATE pedidos SET {campo} = ? WHERE id = ?", (novo_valor, pedido_id))
    conn.commit()
    conn.close()

def atualizar_pedido_completo(pedido_id, endereco=None, cep=None, bairro=None, numero_endereco=None, itens=None, pagamento=None, troco=None, observacoes=None):
    """Atualiza múltiplos campos de um pedido de uma vez.
    Parâmetros opcionais são ignorados se None.
    Retorna True se sucesso, False caso contrário.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        
        # Construir query dinamicamente com apenas os campos fornecidos
        updates = []
        params = []
        
        if endereco is not None:
            updates.append("endereco = ?")
            params.append(endereco)
        if cep is not None:
            updates.append("cep = ?")
            params.append(cep)
        if bairro is not None:
            updates.append("bairro = ?")
            params.append(bairro)
        if numero_endereco is not None:
            updates.append("numero_endereco = ?")
            params.append(numero_endereco)
        if itens is not None:
            # Converter lista de itens para string se necessário
            if isinstance(itens, list):
                itens_str = str(itens)
            else:
                itens_str = itens
            updates.append("itens = ?")
            params.append(itens_str)
        if pagamento is not None:
            updates.append("pagamento = ?")
            params.append(pagamento)
        if troco is not None:
            updates.append("troco = ?")
            params.append(troco)
        if observacoes is not None:
            updates.append("observacoes = ?")
            params.append(observacoes)
        
        # Se nenhum campo foi fornecido, retornar sem fazer nada
        if not updates:
            return True
        
        # Adicionar ID como último parâmetro
        params.append(pedido_id)
        
        # Executar query
        query = f"UPDATE pedidos SET {', '.join(updates)} WHERE id = ?"
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao atualizar pedido: {e}")
        return False

def obter_pedido_por_id(pedido_id):
    """Retorna os dados completos de um pedido pelo ID"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def obter_id_por_numero(numero):
    """Retorna o `id` do pedido dado o `numero` (sequencial exibido para o usuário).
    Retorna None se não existir."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id FROM pedidos WHERE numero = ?", (numero,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# --- Relatórios ---

def pedidos_do_dia():
    """Retorna pedidos feitos no dia atual"""
    hoje = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos WHERE date(data) = ?", (hoje,))
    rows = cur.fetchall()
    conn.close()
    return rows

def total_vendas_dia():
    """Retorna o total vendido no dia"""
    hoje = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT SUM(total) FROM pedidos WHERE date(data) = ?", (hoje,))
    total = cur.fetchone()[0]
    conn.close()
    return total or 0.0

def quantidade_pedidos_dia():
    """Retorna quantos pedidos foram feitos no dia"""
    hoje = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pedidos WHERE date(data) = ?", (hoje,))
    qtd = cur.fetchone()[0]
    conn.close()
    return qtd or 0

def pratos_mais_pedidos():
    """Retorna os pratos mais pedidos (contagem simples)"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT itens FROM pedidos")
    rows = cur.fetchall()
    conn.close()

    contagem = {}
    for row in rows:
        try:
            itens = ast.literal_eval(row[0])  # transforma string em lista de forma segura
        except Exception:
            try:
                itens = eval(row[0])
            except Exception:
                itens = []
        for item in itens:
            nome = item["nome"]
            # Suporta chaves 'qtd' ou 'quantidade' dependendo de como o item foi salvo
            qtd = item.get("qtd") if isinstance(item, dict) else None
            if qtd is None:
                try:
                    qtd = int(item.get("quantidade"))
                except Exception:
                    qtd = 0
            contagem[nome] = contagem.get(nome, 0) + qtd
    return sorted(contagem.items(), key=lambda x: x[1], reverse=True)


def pedidos_por_periodo(data_inicio, data_fim):
    """Retorna pedidos entre duas datas (inclusive). Datas devem ser strings 'YYYY-MM-DD'."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos WHERE date(data) BETWEEN ? AND ? ORDER BY id ASC", (data_inicio, data_fim))
    rows = cur.fetchall()
    conn.close()
    return rows


def vendas_resumo_por_periodo(data_inicio, data_fim, usuario=None, prato_filter=None, usuario_partial=False):
    """Calcula resumo de vendas entre duas datas: quantidade de pedidos, total vendido,
    e lista de (prato, quantidade, receita) ordenada por receita descendente."""
    rows = pedidos_por_periodo(data_inicio, data_fim)
    # aplicar filtro por usuário e por prato, se fornecidos
    if usuario is not None:
        if usuario_partial:
            # busca parcial (case-insensitive)
            rows = [r for r in rows if usuario.lower() in (r[2] or '').strip().lower()]
        else:
            rows = [r for r in rows if (r[2] or '').strip() == usuario]
    if prato_filter is not None:
        filtered = []
        for r in rows:
            itens_raw = r[6]
            try:
                if itens_raw is None:
                    itens_list = []
                elif isinstance(itens_raw, str):
                    from ast import literal_eval
                    itens_list = literal_eval(itens_raw)
                else:
                    itens_list = itens_raw
            except Exception:
                itens_list = []
            found = False
            for it in itens_list:
                if isinstance(it, dict):
                    nome = (it.get('nome') or '').strip()
                    if nome == prato_filter:
                        found = True
                        break
                else:
                    if str(it).strip() == prato_filter:
                        found = True
                        break
            if found:
                filtered.append(r)
        rows = filtered

    total_pedidos = len(rows)
    total_vendido = 0.0
    total_itens = 0.0  # Total apenas dos itens, sem taxa de entrega
    contagem = {}
    receita = {}

    for row in rows:
        try:
            total_vendido += float(row[7] or 0.0)
        except Exception:
            pass
        itens_raw = row[6]
        try:
            if itens_raw is None:
                itens_list = []
            elif isinstance(itens_raw, str):
                from ast import literal_eval
                itens_list = literal_eval(itens_raw)
            else:
                itens_list = itens_raw
        except Exception:
            itens_list = []

        for it in itens_list:
            if isinstance(it, dict):
                nome = it.get('nome') or 'Item'
                # aceitar tanto 'qtd' quanto 'quantidade'
                qtd = int((it.get('qtd') if it.get('qtd') is not None else it.get('quantidade')) or 0)
                preco = 0.0
                try:
                    preco = float(it.get('preco') or 0.0)
                except Exception:
                    preco = 0.0
                contagem[nome] = contagem.get(nome, 0) + qtd
                receita[nome] = receita.get(nome, 0.0) + (qtd * preco)
                total_itens += (qtd * preco)  # Adicionar ao total de itens
            else:
                nome = str(it)
                contagem[nome] = contagem.get(nome, 0) + 1
                receita[nome] = receita.get(nome, 0.0)

    pratos_resumo = []
    # calcular total de marmitas vendidas e outros itens (baseado na categoria dos pratos cadastrados)
    total_marmitas = 0
    total_outros_itens = 0
    try:
        pratos_cadastrados = {p.get('nome', '').strip(): p.get('categoria', '') for p in pratos.listar_pratos()}
    except Exception:
        pratos_cadastrados = {}
    for nome in contagem:
        pratos_resumo.append((nome, contagem[nome], receita.get(nome, 0.0)))
        # somar marmitas quando o prato cadastrado for da categoria Marmita
        try:
            cat = pratos_cadastrados.get(nome, '')
            if isinstance(cat, str) and cat.lower() == 'marmita':
                total_marmitas += contagem[nome]
            else:
                total_outros_itens += contagem[nome]
        except Exception:
            total_outros_itens += contagem[nome]

    pratos_resumo.sort(key=lambda x: x[2], reverse=True)
    
    # Calcular taxa de entrega como diferença entre total e itens
    taxa_total = total_vendido - total_itens
    
    return {
        'total_pedidos': total_pedidos,
        'total_vendido': total_vendido,
        'total_itens': total_itens,
        'taxa_total': taxa_total,
        'pratos': pratos_resumo,
        'total_marmitas': total_marmitas,
        'total_outros_itens': total_outros_itens
    }


def excluir_testes_e_cancelados():
    """Exclui pedidos cujo cliente contenha 'test'/'teste' (case-insensitive)
    e pedidos com status 'Cancelado'. Retorna o número de registros excluídos."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    # contar antes
    cur.execute("SELECT COUNT(*) FROM pedidos")
    antes = cur.fetchone()[0]

    # Excluir por status 'Cancelado'
    cur.execute("DELETE FROM pedidos WHERE LOWER(status) = 'cancelado'")
    # Excluir por cliente que contenha 'test' ou 'teste'
    cur.execute("DELETE FROM pedidos WHERE LOWER(cliente) LIKE '%test%'")
    cur.execute("DELETE FROM pedidos WHERE LOWER(cliente) LIKE '%teste%'")
    conn.commit()

    # contar depois
    cur.execute("SELECT COUNT(*) FROM pedidos")
    depois = cur.fetchone()[0]
    conn.close()
    return antes - depois


def vendas_por_prato_na_data(data_str, nome_prato):
    """Retorna quantidade e receita do `nome_prato` na data especificada (YYYY-MM-DD)."""
    rows = pedidos_por_periodo(data_str, data_str)
    qtd_total = 0
    receita_total = 0.0
    for row in rows:
        itens_raw = row[6]
        try:
            if itens_raw is None:
                itens_list = []
            elif isinstance(itens_raw, str):
                from ast import literal_eval
                itens_list = literal_eval(itens_raw)
            else:
                itens_list = itens_raw
        except Exception:
            itens_list = []

        for it in itens_list:
            if isinstance(it, dict):
                nome = (it.get('nome') or '').strip()
                if nome == nome_prato:
                    try:
                        qtd = int((it.get('qtd') if it.get('qtd') is not None else it.get('quantidade')) or 0)
                    except Exception:
                        qtd = 0
                    try:
                        preco = float(it.get('preco') or 0.0)
                    except Exception:
                        preco = 0.0
                    qtd_total += qtd
                    receita_total += (qtd * preco)
            else:
                # se item for string, comparar diretamente
                if str(it).strip() == nome_prato:
                    qtd_total += 1
    return {'nome': nome_prato, 'quantidade': qtd_total, 'receita': receita_total}


def resumo_por_usuario(data_inicio, data_fim, prato_filter=None, usuario_filter=None):
    """Retorna lista de tuplas (usuario, qtd_pedidos, total_itens, total_gasto)
    opcionalmente filtrando por `prato_filter` (somente considerar pedidos que contenham esse prato)
    e opcionalmente filtrando por `usuario_filter` (mostrar apenas esse usuário específico)."""
    rows = pedidos_por_periodo(data_inicio, data_fim)
    summary = {}
    for row in rows:
        cliente = (row[2] or '').strip()
        
        # se houver filtro por usuário, verificar se este pedido pertence a esse usuário
        if usuario_filter is not None and cliente != usuario_filter:
            continue
        
        itens_raw = row[6]
        try:
            if itens_raw is None:
                itens_list = []
            elif isinstance(itens_raw, str):
                from ast import literal_eval
                itens_list = literal_eval(itens_raw)
            else:
                itens_list = itens_raw
        except Exception:
            itens_list = []

        # se houver filtro por prato, verificar se o pedido contém o prato
        if prato_filter is not None:
            found = False
            for it in itens_list:
                if isinstance(it, dict):
                    if (it.get('nome') or '') == prato_filter:
                        found = True
                        break
                else:
                    if str(it) == prato_filter:
                        found = True
                        break
            if not found:
                continue

        qtd_itens = 0
        for it in itens_list:
            if isinstance(it, dict):
                try:
                    qtd_itens += int((it.get('qtd') if it.get('qtd') is not None else it.get('quantidade')) or 0)
                except Exception:
                    pass
            else:
                qtd_itens += 1

        gasto = 0.0
        try:
            gasto = float(row[7] or 0.0)
        except Exception:
            gasto = 0.0

        if cliente not in summary:
            summary[cliente] = {'pedidos': 0, 'itens': 0, 'gasto': 0.0}
        summary[cliente]['pedidos'] += 1
        summary[cliente]['itens'] += qtd_itens
        summary[cliente]['gasto'] += gasto

    result = []
    for cliente, vals in summary.items():
        result.append((cliente, vals['pedidos'], vals['itens'], vals['gasto']))

    # ordenar por gasto desc
    result.sort(key=lambda x: x[3], reverse=True)
    return result

def pedidos_por_cliente(nome_cliente):
    """Retorna pedidos de um cliente específico"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos WHERE cliente = ?", (nome_cliente,))
    rows = cur.fetchall()
    conn.close()
    return rows

def deletar_pedido(ped_id):
    """Deleta um pedido do banco de dados pelo ID."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("DELETE FROM pedidos WHERE id = ?", (ped_id,))
    conn.commit()
    conn.close()

# --- Exportação ---

def exportar_csv(nome_arquivo="relatorio_pedidos.csv"):
    """Exporta todos os pedidos para um arquivo CSV"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos")
    rows = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]
    conn.close()

    with open(nome_arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(colunas)
        writer.writerows(rows)
    return nome_arquivo