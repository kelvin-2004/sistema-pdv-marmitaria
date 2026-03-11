#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migração: Adiciona coluna 'bairro' e 'numero' ao banco de dados
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pedidos.db"

def migrar_banco():
    """Migra o banco de dados para incluir as colunas faltantes"""
    
    if not DB_PATH.exists():
        print(f"✗ Arquivo {DB_PATH} não encontrado")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    try:
        # Verificar se as colunas já existem
        cur.execute("PRAGMA table_info(pedidos)")
        colunas = {row[1] for row in cur.fetchall()}
        
        print(f"✓ Colunas atuais: {', '.join(sorted(colunas))}\n")
        
        # Adicionar coluna 'bairro' se não existir
        if 'bairro' not in colunas:
            print("Adicionando coluna 'bairro'...")
            cur.execute("ALTER TABLE pedidos ADD COLUMN bairro TEXT DEFAULT ''")
            conn.commit()
            print("✓ Coluna 'bairro' adicionada\n")
        else:
            print("✓ Coluna 'bairro' já existe\n")
        
        # Adicionar coluna 'numero' se não existir
        if 'numero_endereco' not in colunas:
            print("Adicionando coluna 'numero' (endereço)...")
            cur.execute("ALTER TABLE pedidos ADD COLUMN numero_endereco INTEGER DEFAULT 0")
            conn.commit()
            print("✓ Coluna 'numero_endereco' adicionada\n")
        else:
            print("✓ Coluna 'numero_endereco' já existe\n")
        
        # Mostrar novo schema
        print("Novo schema:")
        cur.execute("PRAGMA table_info(pedidos)")
        for cid, name, type_, notnull, dflt, pk in cur.fetchall():
            print(f"  {cid+1}. {name} ({type_})" + (" [PK]" if pk else ""))
        
        conn.close()
        print("\n✓ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro durante migração: {e}")
        conn.close()
        return False

def reorganizar_ids():
    """Reorganiza os IDs do banco para remover gaps"""
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    try:
        # Obter todos os IDs atuais
        cur.execute("SELECT id FROM pedidos ORDER BY id ASC")
        ids_atuais = [row[0] for row in cur.fetchall()]
        
        if not ids_atuais:
            print("✓ Banco vazio, nada para reorganizar")
            conn.close()
            return True
        
        print(f"IDs atuais: {ids_atuais}")
        
        # Verificar se há gaps
        ids_esperados = list(range(1, len(ids_atuais) + 1))
        
        if ids_atuais == ids_esperados:
            print("✓ IDs já estão sequenciais, nada a fazer")
            conn.close()
            return True
        
        print(f"IDs esperados: {ids_esperados}")
        print("\nReorganizando IDs...")
        
        # Reorganizar
        for novo_id, id_antigo in enumerate(ids_esperados, 1):
            if id_antigo != ids_atuais[novo_id - 1]:
                cur.execute(
                    "UPDATE pedidos SET id = ? WHERE id = ?",
                    (novo_id, ids_atuais[novo_id - 1])
                )
        
        conn.commit()
        
        # Verificar resultado
        cur.execute("SELECT id FROM pedidos ORDER BY id ASC")
        ids_novos = [row[0] for row in cur.fetchall()]
        print(f"✓ Novos IDs: {ids_novos}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Erro ao reorganizar IDs: {e}")
        conn.close()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 60 + "\n")
    
    # Migrar
    migrar_banco()
    
    print("\n" + "=" * 60)
    print("REORGANIZAR IDs")
    print("=" * 60 + "\n")
    
    # Reorganizar IDs
    reorganizar_ids()
    
    print("\n" + "=" * 60)
    print("✓ Concluído!")
    print("=" * 60)
