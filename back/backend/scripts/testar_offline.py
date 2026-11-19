"""Suíte isolada: ignora configurações privadas e bloqueia rede.

Executar na raiz: python -m backend.scripts.testar_offline
"""
import os
import sys
import secrets
import unittest
from pathlib import Path
from unittest.mock import patch


def main():
    os.environ.update(DATABASE_URL='sqlite://', PYTHON_DOTENV_DISABLED='1',
        PRAZUS_IA_ENABLED='0', PRAZUS_SINCRONIZAR_AO_INICIAR='0', SECRET_KEY=secrets.token_hex(32))
    with patch('socket.socket.connect', side_effect=AssertionError('Rede bloqueada durante testes offline')):
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1] / 'tests'))
        resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
