# printer.py
from escpos.printer import Usb
import time
import errno
from pathlib import Path

# IDs da impressora (ajuste conforme seu modelo)
# Vários modelos de impressoras térmicas USB
KNOWN_PRINTERS = [
    (0x0fe6, 0x811e),  # Modelo padrão
    (0x0fe6, 0x8005),  # Alternativo
    (0x04b8, 0x0202),  # Epson
    (0x0483, 0x0110),  # ST Microelectronics
]

# Arquivo de log (no diretório do projeto)
LOG_FILE = str(Path(__file__).resolve().parent / "debug.log")

def log_debug(msg):
    """Registra mensagem de debug"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass


def _find_printer():
    """Tenta encontrar a impressora nos IDs conhecidos"""
    import usb.core
    import usb.util
    
    log_debug("[printer] Procurando por impressora nos IDs conhecidos...")
    
    for vendor_id, product_id in KNOWN_PRINTERS:
        log_debug(f"[printer] Buscando VENDOR_ID=0x{vendor_id:04x}, PRODUCT_ID=0x{product_id:04x}...")
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device is not None:
            log_debug(f"[printer] ✓ Impressora encontrada: 0x{vendor_id:04x}:0x{product_id:04x}")
            return vendor_id, product_id
    
    log_debug("[printer] ✗ Nenhuma impressora encontrada nos IDs conhecidos")
    return None, None


def _open_printer_with_retry(retries=5, delay=0.5):
    """Tenta abrir o dispositivo USB da impressora com retry em caso de Resource busy."""
    # Primeiro, tenta encontrar a impressora
    vendor_id, product_id = _find_printer()
    
    if vendor_id is None:
        raise Exception("Impressora não encontrada! Verifique se está conectada e ligada.")
    
    log_debug(f"[printer] Tentando abrir impressora (VENDOR_ID=0x{vendor_id:04x}, PRODUCT_ID=0x{product_id:04x})")
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            log_debug(f"[printer] Tentativa {attempt} de {retries}")
            p = Usb(vendor_id, product_id, encoding="cp437")
            log_debug(f"[printer] ✓ Impressora aberta com sucesso!")
            return p
        except Exception as e:
            last_exc = e
            log_debug(f"[printer] ✗ Erro na tentativa {attempt}: {e}")
            # Se for erro de recurso ocupado, aguarda e tenta de novo
            is_busy = False
            if isinstance(e, OSError) and getattr(e, 'errno', None) == errno.EBUSY:
                is_busy = True
            if 'resource busy' in str(e).lower() or 'device or resource busy' in str(e).lower() or is_busy:
                wait = delay * attempt
                log_debug(f"[printer] Recurso ocupado, aguardando {wait}s...")
                time.sleep(wait)
                continue
            # Erro diferente — não tentamos novamente
            log_debug(f"[printer] Erro fatal (não será retentado): {e}")
            raise
    # Se não conseguiu após retries, raise último erro
    log_debug(f"[printer] Falha após {retries} tentativas")
    raise last_exc


def imprimir_texto(texto):
    p = None
    try:
        log_debug("[printer] ========== INICIANDO IMPRESSÃO ==========")
        log_debug(f"[printer] Texto a imprimir ({len(texto)} caracteres):\n{texto}\n")
        
        # Remove qualquer linha de agradecimento e aparar espaços
        raw_lines = [l.rstrip() for l in texto.splitlines()]
        filtered = [l for l in raw_lines if 'obrigad' not in l.lower()]

        # Colapsa múltiplas linhas em branco para uma única
        compact_lines = []
        blank = False
        for l in filtered:
            if l.strip() == "":
                if not blank:
                    compact_lines.append("")
                blank = True
            else:
                compact_lines.append(l.strip())
                blank = False

        # junta e remove quebras finais para evitar espaços extras
        texto_limpo = "\n".join(compact_lines).rstrip("\n")

        log_debug(f"[printer] Texto limpo e formatado:\n{texto_limpo}\n")

        # Tenta abrir a impressora com retry para Resource busy
        log_debug("[printer] Abrindo conexão com a impressora...")
        p = _open_printer_with_retry()
        
        # Verifica se a conexão foi estabelecida
        if p is None or not hasattr(p, 'device') or p.device is None:
            raise Exception("Impressora conectada mas o dispositivo não está disponível")

        # Envia o texto diretamente (sem configurações que podem causar problemas)
        log_debug("[printer] Enviando texto para impressora...")
        p.text(texto_limpo)
        log_debug("[printer] ✓ Texto enviado com sucesso!")

        # Tenta enviar feed de linha
        try:
            p._raw(b"\n\n\n")
            log_debug("[printer] Feed de linhas enviado")
        except Exception as e:
            log_debug(f"[printer] Aviso ao enviar feed: {e}")

        # Tenta cortar papel
        try:
            log_debug("[printer] Cortando papel...")
            p.cut()
            log_debug("[printer] ✓ Papel cortado")
        except Exception as e:
            log_debug(f"[printer] Aviso ao cortar papel: {e}")
        
        log_debug("[printer] ✓ IMPRESSÃO CONCLUÍDA COM SUCESSO!")

    except Exception as e:
        # Loga erro de impressão para diagnóstico
        log_debug(f"[printer] ✗✗✗ ERRO NA IMPRESSÃO: {e}")
        import traceback
        log_debug(traceback.format_exc())
    finally:
        # Tenta fechar/limpar o objeto da impressora quando aplicável
        try:
            if p is not None:
                # Alguns drivers possuem método close()
                if hasattr(p, 'close'):
                    try:
                        p.close()
                        log_debug("[printer] Conexão com impressora fechada")
                    except Exception as e:
                        log_debug(f"[printer] Aviso ao fechar: {e}")
                # Tentativa genérica: fechar dispositivo se exposto
                if hasattr(p, 'device'):
                    try:
                        dev = getattr(p, 'device')
                        if hasattr(dev, 'close'):
                            dev.close()
                    except Exception:
                        pass
        except Exception:
            pass