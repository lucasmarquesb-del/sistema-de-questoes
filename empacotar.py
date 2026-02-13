"""
Script de empacotamento do OharaBank com PyInstaller.

Uso:
    python empacotar.py

Gera:
    dist/OharaBank/
    ├── OharaBank.exe
    ├── config.ini
    ├── .env  (se existir)
    ├── _internal/
    ├── database/
    ├── imagens/logos/
    ├── templates/latex/
    ├── logs/
    └── exports/
"""

import os
import subprocess
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist" / "OharaBank"
APP_NAME = "OharaBank"
ENTRY_POINT = ROOT / "src" / "main.py"


def check_pyinstaller():
    """Verifica se o PyInstaller está instalado."""
    try:
        import PyInstaller  # noqa: F401
        print(f"[OK] PyInstaller {PyInstaller.__version__} encontrado.")
    except ImportError:
        print("[ERRO] PyInstaller não está instalado.")
        print("       Instale com: pip install pyinstaller")
        sys.exit(1)


def build_command() -> list[str]:
    """Constrói o comando PyInstaller."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        # --- Hidden imports ---
        "--hidden-import", "PyQt6.QtWebEngineWidgets",
        "--hidden-import", "pymongo",
        "--hidden-import", "dns.resolver",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        # --- Dados incluídos no bundle ---
        "--add-data", f"config.ini{os.pathsep}.",
        "--add-data", f"imagens/logos{os.pathsep}imagens/logos",
        "--add-data", f"templates/latex{os.pathsep}templates/latex",
    ]

    # .env opcional
    env_file = ROOT / ".env"
    if env_file.exists():
        cmd += ["--add-data", f".env{os.pathsep}."]

    # Ícone (se houver .ico)
    ico_path = ROOT / "imagens" / "logos" / "logoapp.ico"
    if ico_path.exists():
        cmd += ["--icon", str(ico_path)]

    # --- Excludes ---
    for mod in ["backend", "tests", "pytest", "unittest"]:
        cmd += ["--exclude-module", mod]

    # Entry point
    cmd.append(str(ENTRY_POINT))

    return cmd


def copy_runtime_data():
    """Copia dados editáveis para o diretório de distribuição."""
    if not DIST_DIR.exists():
        print(f"[ERRO] Diretório de saída não encontrado: {DIST_DIR}")
        sys.exit(1)

    # Diretórios de dados que devem ser editáveis pelo usuário
    data_dirs = {
        "database": ROOT / "database",
        "imagens/logos": ROOT / "imagens" / "logos",
        "templates/latex": ROOT / "templates" / "latex",
    }

    for dest_rel, src in data_dirs.items():
        dest = DIST_DIR / dest_rel
        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"  [COPY] {src} -> {dest}")
        else:
            dest.mkdir(parents=True, exist_ok=True)
            print(f"  [MKDIR] {dest} (origem não encontrada)")

    # Arquivos avulsos
    for filename in ["config.ini", ".env"]:
        src = ROOT / filename
        if src.exists():
            shutil.copy2(src, DIST_DIR / filename)
            print(f"  [COPY] {src} -> {DIST_DIR / filename}")

    # Criar pastas vazias para runtime
    for dirname in ["logs", "exports"]:
        d = DIST_DIR / dirname
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [MKDIR] {d}")


def create_release_zip():
    """Cria OharaBank.zip pronto para upload como asset do GitHub Release."""
    zip_path = ROOT / "dist" / f"{APP_NAME}.zip"

    if zip_path.exists():
        zip_path.unlink()

    print(f"  Criando {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in DIST_DIR.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(DIST_DIR)
                zf.write(file, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] {zip_path} ({size_mb:.1f} MB)")


def main():
    print("=" * 60)
    print(f"  Empacotando {APP_NAME}")
    print("=" * 60)

    check_pyinstaller()

    cmd = build_command()

    print("\n[1/4] Executando PyInstaller...")
    print(f"  Comando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"\n[ERRO] PyInstaller retornou código {result.returncode}")
        sys.exit(result.returncode)

    print("\n[2/4] Copiando dados de runtime...")
    copy_runtime_data()

    print("\n[3/4] Verificando build...")
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] {exe_path} ({size_mb:.1f} MB)")
    else:
        print(f"  [AVISO] Executável não encontrado em {exe_path}")

    print("\n[4/4] Gerando .zip para GitHub Release...")
    create_release_zip()

    print("\n" + "=" * 60)
    print(f"  Build concluído! Saída em: {DIST_DIR}")
    print(f"  Release zip: dist/{APP_NAME}.zip")
    print("=" * 60)


if __name__ == "__main__":
    main()
