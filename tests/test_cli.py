import subprocess
import sys


def test_cli_estudio_init():
    result = subprocess.run(
        [sys.executable, "-m", "src.estudio.cli", "estudio-init"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_cli_simulacion_list_empty():
    result = subprocess.run(
        [sys.executable, "-m", "src.estudio.cli", "simulacion-list"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
