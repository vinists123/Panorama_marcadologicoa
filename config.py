# -*- coding: utf-8 -*-
"""
PANORAMA MERCADOLÓGICO DE NIP - Configurações centrais (v3)
Tudo que pode mudar fica aqui. Pode ser sobrescrito por variáveis de ambiente.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# ------------------------------------------------------------------ 1) PASTAS
BASE_DIR   = Path(os.getenv("PANORAMA_BASE_DIR", RAIZ))
DIR_MAPAS  = Path(os.getenv("PANORAMA_DIR_MAPAS", RAIZ / "mapas"))
DIR_ASSETS = RAIZ / "assets"
DIR_BRONZE = BASE_DIR / "dados" / "bronze"
DIR_SILVER = BASE_DIR / "dados" / "silver"
DIR_GOLD   = BASE_DIR / "dados" / "gold"
DIR_SAIDA  = BASE_DIR / "saida"
ARQ_CALIBRACAO = BASE_DIR / "dados" / "calibracao.json"     # gerado pelo calibrar.py
ARQ_REF_PPT    = RAIZ / "assets" / "referencia_ppt.json"    # números do PPT apresentado

# ------------------------------------------------------------------ 2) FONTES ANS
URL_PDA       = "https://dadosabertos.ans.gov.br/FTP/PDA/"
URL_IGR       = URL_PDA + "IGR/IGR_versao_2023/pda-023-igr.csv"
URL_NIP       = URL_PDA + "demandas_dos_consumidores_nip/pda-013-demandas_dos_consumidores_nip-{ano}.csv"
URL_BENEF_DIR = URL_PDA + "informacoes_consolidadas_de_beneficiarios-024/"
URL_BENEF_ARQ = URL_BENEF_DIR + "{aaaamm}/pda-024-icb-{uf}-{aaaa}_{mm}.zip"

VERIFY_SSL   = os.getenv("PANORAMA_VERIFY_SSL", "1") == "1"
HTTP_TIMEOUT = 300
HTTP_RETRIES = 4
DOWNLOADS_PARALELOS = int(os.getenv("PANORAMA_DOWNLOADS_PARALELOS", "4"))

# ------------------------------------------------------------------ 3) PERÍODOS
ANO_INICIO     = 2025                       # início das séries (IGR e NIP)
ANOS_NIP       = list(range(ANO_INICIO, 2100))   # baixa todos os anos que existirem na ANS
MES_INICIO_PAINEL = os.getenv("PANORAMA_MES_INICIO", "2026-01")  # 1ª competência selecionável no painel
QTD_TRIMESTRES = 5                          # trimestres fechados antes do quadrimestre (s6/s7)
MESES_QUAD     = 4                          # "Quadrimestre"
MESES_GRID     = 12                         # grid comparativo (s11)
COMPETENCIA_FIM = os.getenv("PANORAMA_COMPETENCIA_FIM") or None   # None = último mês disponível
PERIODO_PRACAS = "quad"                     # "quad" ou "12m"

# Referência usada para calibrar contra o PPT apresentado (abr-jul/26)
COMPETENCIA_PPT = "2026-07"

# ------------------------------------------------------------------ 4) FILTROS
COBERTURA_IGR = "ASSISTENCIA MEDICA"
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
       "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "XX"]
TOP_REGIOES = 21                            # igual ao PPT (21 praças)
FALLBACK_REGIAO = "outros"
PRACAS_EXCLUIR = ["Outros", "Demais praças", "Não informado"]
MIN_SHARE_DESTAQUE = 0.03                   # tema precisa ter >=3% do IGR para virar destaque (s9)

# ------------------------------------------------------------------ 5) METODOLOGIA (padrão = PPT)
# Valores abaixo são o PADRÃO; o calibrar.py grava em dados/calibracao.json a combinação
# que reproduz o PPT e o main.py usa automaticamente.
METODO_IGR = "media"          # "media" = média simples da coluna IGR (como no PPT) | "ponderado" = soma recl./soma benef.
METODO_GRID = "nip_benef"     # "nip_benef" = NIPs ÷ beneficiários (provável regra do PPT) | "fatia_igr" = soma igual ao IGR
PRE_AUTO_FLAG = None          # coluna-flag escolhida pela calibração (ex.: "F_STATUS_AUTO")
PRACA_MUNICIPIO = "beneficiario"   # "beneficiario" ou "local" (local de atendimento)
PRACA_ESCALA = "direto"            # "direto" (NIP/vidas) ou "igr" (escalado ao IGR da operadora)

REGEX_PRE_AUTO  = r"PRE[ -]?AUTO|FISCALIZ|INSTAURA|PROCESSO ADMINISTRATIVO|SANCION"
REGEX_AUTO_INFR = r"AUTO DE INFRA|LAVRATURA"

COLUNAS_NIP_MANUAL = {"mes": None, "registro": None, "cd_municipio": None, "nm_municipio": None,
                      "uf": None, "cobertura": None, "assunto": None}

# ------------------------------------------------------------------ 6) SHAREPOINT
MODO_PUBLICACAO = os.getenv("PANORAMA_MODO_PUBLICACAO", "pasta")   # pasta | api | nenhum
SP_PASTA_SINCRONIZADA = os.getenv(
    "PANORAMA_SP_PASTA",
    str(Path.home() / "Amil" / "INFOCS - RepositorioCS" / "MISCS" / "ArquivosPBIX" / "Painel HTML"))
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "https://SEU_TENANT.sharepoint.com/sites/CustomerService")
SHAREPOINT_FOLDER   = os.getenv("SHAREPOINT_FOLDER", "/sites/CustomerService/RepositorioCS/MISCS/ArquivosPBIX/Painel HTML")
SHAREPOINT_USER     = os.getenv("SHAREPOINT_USER", "")
SHAREPOINT_PASSWORD = os.getenv("SHAREPOINT_PASSWORD", "")
SHAREPOINT_CLIENT_ID     = os.getenv("SHAREPOINT_CLIENT_ID", "")
SHAREPOINT_CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET", "")
NOME_HTML = "panorama_mercadologico_nip.html"
