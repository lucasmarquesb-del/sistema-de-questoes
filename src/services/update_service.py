"""Serviço de auto-update OTA via GitHub Releases."""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

from src.version import __version__

logger = logging.getLogger(__name__)

GITHUB_REPO = "lucasmarquesb-del/sistema-de-questoes"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
ASSET_NAME = "OharaBank.zip"

# Pastas/arquivos do usuário que NÃO devem ser sobrescritos
USER_DATA = [
    "database",
    "config.ini",
    ".env",
    "logs",
    "exports",
]


def _parse_version(tag: str) -> tuple[int, ...]:
    """Converte tag 'v1.2.3' em tupla (1, 2, 3)."""
    clean = tag.lstrip("vV")
    return tuple(int(x) for x in clean.split("."))


class UpdateService:
    """Verifica e aplica atualizações do GitHub Releases."""

    def __init__(self):
        self.current_version = __version__

    def check_for_update(self) -> dict | None:
        """
        Consulta o GitHub API para verificar se há uma nova versão.

        Returns:
            dict com {version, download_url, notes} ou None se não há atualização.
        """
        try:
            req = Request(GITHUB_API_URL, headers={"Accept": "application/vnd.github+json"})
            with urlopen(req, timeout=10) as resp:
                import json
                data = json.loads(resp.read().decode())

            tag = data.get("tag_name", "")
            remote_version = _parse_version(tag)
            local_version = _parse_version(self.current_version)

            if remote_version <= local_version:
                logger.info(f"App atualizado. Local: {self.current_version}, Remoto: {tag}")
                return None

            # Procurar asset OharaBank.zip
            download_url = None
            for asset in data.get("assets", []):
                if asset.get("name") == ASSET_NAME:
                    download_url = asset.get("browser_download_url")
                    break

            if not download_url:
                logger.warning(f"Release {tag} não possui asset '{ASSET_NAME}'.")
                return None

            version_str = tag.lstrip("vV")
            logger.info(f"Nova versão disponível: {version_str} (atual: {self.current_version})")

            return {
                "version": version_str,
                "download_url": download_url,
                "notes": data.get("body", ""),
            }

        except URLError as e:
            logger.warning(f"Não foi possível verificar atualizações (rede): {e}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao verificar atualizações: {e}")
            return None

    def download_update(self, url: str, dest: Path, progress_callback=None) -> bool:
        """
        Baixa o arquivo .zip do release.

        Args:
            url: URL de download do asset.
            dest: Caminho de destino para salvar o .zip.
            progress_callback: Callable(bytes_downloaded, total_bytes) opcional.

        Returns:
            True se download concluído com sucesso.
        """
        try:
            req = Request(url)
            with urlopen(req, timeout=300) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB

                with open(dest, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)

            logger.info(f"Download concluído: {dest} ({downloaded} bytes)")
            return True

        except Exception as e:
            logger.error(f"Erro ao baixar atualização: {e}")
            if dest.exists():
                dest.unlink()
            return False

    def apply_update(self, zip_path: Path) -> bool:
        """
        Extrai o zip para uma pasta temporária e gera um script .bat
        que substitui os arquivos do app e reinicia.

        Args:
            zip_path: Caminho do .zip baixado.

        Returns:
            True se o script foi gerado e lançado (o app deve fechar em seguida).
        """
        try:
            app_dir = Path(sys.executable).parent
            temp_dir = Path(tempfile.mkdtemp(prefix="oharabank_update_"))

            # Extrair zip
            logger.info(f"Extraindo {zip_path} para {temp_dir}...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            # Gerar lista de exclusões para o robocopy /XD e /XF
            exclude_dirs = [d for d in USER_DATA if not d.endswith(".ini") and not d.endswith(".env") and "." not in d]
            exclude_files = [f for f in USER_DATA if "." in f]

            xd_flags = " ".join(f'"{d}"' for d in exclude_dirs)
            xf_flags = " ".join(f'"{f}"' for f in exclude_files)

            bat_path = app_dir / "_update.bat"
            exe_name = Path(sys.executable).name

            # Script bat:
            # 1. Espera o app fechar (taskkill + timeout)
            # 2. Copia arquivos novos com robocopy (exclui dados do usuário)
            # 3. Limpa arquivos temporários
            # 4. Reinicia o app
            bat_content = f'''@echo off
chcp 65001 >nul
echo Aguardando o OharaBank fechar...
timeout /t 2 /nobreak >nul

:: Tentar fechar se ainda estiver rodando
taskkill /f /im "{exe_name}" >nul 2>&1
timeout /t 2 /nobreak >nul

echo Aplicando atualizacao...
robocopy "{temp_dir}" "{app_dir}" /E /IS /IT /XD {xd_flags} /XF {xf_flags} /R:3 /W:2 /NDL /NJH /NJS

echo Limpando arquivos temporarios...
rd /s /q "{temp_dir}" >nul 2>&1
del "{zip_path}" >nul 2>&1

echo Reiniciando OharaBank...
start "" "{app_dir / exe_name}"

:: Aguardar um momento e apagar este script
timeout /t 2 /nobreak >nul
del "%~f0" >nul 2>&1
'''
            bat_path.write_text(bat_content, encoding="utf-8")
            logger.info(f"Script de atualização gerado: {bat_path}")

            # Lançar o .bat em processo separado (detached)
            subprocess.Popen(
                ["cmd", "/c", str(bat_path)],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )

            logger.info("Script de atualização lançado. O app será encerrado.")
            return True

        except Exception as e:
            logger.error(f"Erro ao aplicar atualização: {e}", exc_info=True)
            return False
