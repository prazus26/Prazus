import os
import secrets
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def main():
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1",
        SECRET_KEY=secrets.token_hex(32),
        BACKEND_URL="http://127.0.0.1:9001"
    )
    with patch("socket.socket.connect", side_effect=AssertionError("Rede bloqueada nos testes do web")):
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent / "tests"))
        resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
