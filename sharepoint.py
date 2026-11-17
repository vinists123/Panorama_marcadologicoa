# -*- coding: utf-8 -*-
"""Publicação do HTML no SharePoint (pasta sincronizada OU API)."""
import shutil
from pathlib import Path

import config as C
from utils import log


def publicar(caminho_html: Path):
    modo = C.MODO_PUBLICACAO.lower()
    if modo == "nenhum":
        log("Publicação desativada (MODO_PUBLICACAO='nenhum').")
        return None
    if modo == "pasta":
        destino_dir = Path(C.SP_PASTA_SINCRONIZADA)
        if not destino_dir.exists():
            raise FileNotFoundError(
                f"Pasta sincronizada não encontrada: {destino_dir}\n"
                "  -> No SharePoint, abra a biblioteca 'Painel HTML' e clique em 'Sincronizar'.\n"
                "  -> Copie o caminho da pasta no Explorer e cole em SP_PASTA_SINCRONIZADA (config.py).")
        destino = destino_dir / caminho_html.name
        shutil.copy2(caminho_html, destino)
        log(f"HTML copiado para a pasta sincronizada: {destino}")
        return str(destino)
    if modo == "api":
        from office365.sharepoint.client_context import ClientContext
        if C.SHAREPOINT_CLIENT_ID and C.SHAREPOINT_CLIENT_SECRET:
            from office365.runtime.auth.client_credential import ClientCredential
            cred = ClientCredential(C.SHAREPOINT_CLIENT_ID, C.SHAREPOINT_CLIENT_SECRET)
        else:
            from office365.runtime.auth.user_credential import UserCredential
            cred = UserCredential(C.SHAREPOINT_USER, C.SHAREPOINT_PASSWORD)
        ctx = ClientContext(C.SHAREPOINT_SITE_URL).with_credentials(cred)
        pasta = ctx.web.get_folder_by_server_relative_url(C.SHAREPOINT_FOLDER)
        pasta.upload_file(caminho_html.name, caminho_html.read_bytes()).execute_query()
        log(f"HTML publicado no SharePoint: {C.SHAREPOINT_FOLDER}/{caminho_html.name}")
        return C.SHAREPOINT_FOLDER
    raise ValueError(f"MODO_PUBLICACAO inválido: {C.MODO_PUBLICACAO}")
