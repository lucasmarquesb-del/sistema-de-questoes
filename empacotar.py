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
    for mod in ["backend", "tests", "pytest"]:
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

    # Copiar MiKTeX Portable (se existir)
    # Suporta tanto installers/miktex-portable/texmfs/... quanto installers/miktex-portable/miktex-portable/texmfs/...
    miktex_src = ROOT / "installers" / "miktex-portable"
    miktex_dest = DIST_DIR / "miktex-portable"
    if miktex_src.exists():
        # Detectar se tem pasta duplicada (miktex-portable/miktex-portable/)
        inner = miktex_src / "miktex-portable"
        if inner.exists() and (inner / "texmfs").exists():
            miktex_src = inner  # Usar o nível interno

        if miktex_dest.exists():
            shutil.rmtree(miktex_dest)
        shutil.copytree(miktex_src, miktex_dest)
        print(f"  [COPY] MiKTeX Portable -> {miktex_dest}")
    else:
        print(f"  [AVISO] MiKTeX Portable não encontrado em {miktex_src}")
        print(f"          Baixe de https://miktex.org/portable e extraia para {miktex_src}")

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


def find_iscc() -> str | None:
    """Procura o compilador Inno Setup (iscc.exe)."""
    import shutil as _shutil

    # Verificar no PATH
    iscc = _shutil.which("iscc")
    if iscc:
        return iscc

    # Caminhos comuns do Inno Setup
    common_paths = [
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 5" / "ISCC.exe",
    ]

    for p in common_paths:
        if p.exists():
            return str(p)

    return None


def build_installer():
    """Compila o instalador com Inno Setup (se disponível)."""
    iss_file = ROOT / "installer.iss"
    if not iss_file.exists():
        print("  [AVISO] installer.iss não encontrado, pulando criação do instalador.")
        return

    iscc = find_iscc()
    if not iscc:
        print("  [AVISO] Inno Setup (ISCC.exe) não encontrado.")
        print("          Instale de https://jrsoftware.org/isinfo.php")
        print("          Ou compile manualmente: iscc installer.iss")
        return

    print(f"  Compilando installer.iss com {iscc}...")
    result = subprocess.run([iscc, str(iss_file)], cwd=str(ROOT))
    if result.returncode == 0:
        setup_path = ROOT / "dist" / "OharaBank_Setup.exe"
        if setup_path.exists():
            size_mb = setup_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] Instalador gerado: {setup_path} ({size_mb:.1f} MB)")
        else:
            print(f"  [OK] Inno Setup concluiu, verifique dist/ para o instalador.")
    else:
        print(f"  [ERRO] Inno Setup retornou código {result.returncode}")


def main():
    print("=" * 60)
    print(f"  Empacotando {APP_NAME}")
    print("=" * 60)

    check_pyinstaller()

    cmd = build_command()

    print("\n[1/5] Executando PyInstaller...")
    print(f"  Comando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"\n[ERRO] PyInstaller retornou código {result.returncode}")
        sys.exit(result.returncode)

    print("\n[2/5] Copiando dados de runtime...")
    copy_runtime_data()

    print("\n[3/5] Verificando build...")
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] {exe_path} ({size_mb:.1f} MB)")
    else:
        print(f"  [AVISO] Executável não encontrado em {exe_path}")

    print("\n[4/5] Gerando .zip para GitHub Release...")
    create_release_zip()

    print("\n[5/5] Gerando instalador (Inno Setup)...")
    build_installer()

    print("\n" + "=" * 60)
    print(f"  Build concluído! Saída em: {DIST_DIR}")
    print(f"  Release zip: dist/{APP_NAME}.zip")
    print("=" * 60)


if __name__ == "__main__":
    main()
