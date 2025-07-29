#!/usr/bin/env python3
"""
Script simples de execução de testes para o Crypto Hunter
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Executa os testes básicos."""
    print("Executando testes...")
    
    # Verifica se o diretório de testes existe
    if not Path("tests").exists():
        print("Diretório de testes não encontrado")
        return False
    
    # Executa pytest
    cmd = [sys.executable, "-m", "pytest", "tests", "-v"]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def main():
    """Função principal."""
    success = run_tests()
    
    if success:
        print("Testes concluídos com sucesso!")
    else:
        print("Alguns testes falharam")
        sys.exit(1)


if __name__ == "__main__":
    main() 