# -*- coding: utf-8 -*-
"""
MAPAS OFICIAIS do Panorama Mercadológico (lidos direto da pasta /mapas, sem renomear):

  MAPA 01 - MAPA_GRUPOS_EMPRESAS_V01.xlsx       -> operadoras (Amil + B, P, S)
  MAPA 02 - MAPA_ASSUNTO_RECLASSIFICADO_V01.xlsx -> ASSUNTO ANS -> 11 temas (X_Assunto)
  MAPA 03 - MAPA Regiões de Saúde.xlsx           -> município -> praça (coluna "Pareto")

Modelos antigos (MAPA_01_*, MAPA_02_*, MAPA_03_*) e temporários do Excel (~$) são ignorados.
"""
import glob
import re
import unicodedata
from pathlib import Path

import pandas as pd

import config as C
from utils import log, registro6, norm_serie


def limpa_rotulo(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def chave_assunto(s: pd.Series) -> pd.Series:
    """Chave robusta: sem acento, maiúsculo, só letras/números (resolve espaços extras e '¿')."""
    s = s.fillna("").astype(str).str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
    return s.str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)


def _achar_arquivo(padroes, ignorar=("MAPA_01", "MAPA_02", "MAPA_03")):
    for p in padroes:
        achados = sorted(f for f in glob.glob(str(C.DIR_MAPAS / p))
                         if not Path(f).name.startswith("~$")
                         and not any(Path(f).name.upper().startswith(i) for i in ignorar))
        if achados:
            return Path(achados[-1])
    raise FileNotFoundError(f"Mapa não encontrado em {C.DIR_MAPAS} (padrões: {padroes})")


# ------------------------------------------------------------------ MAPA 01
SIGLAS = [(r"AMIL", "AMIL"), (r"BRADESCO", "B"), (r"PORTO", "P"), (r"SUL ?AM", "S")]


def carregar_mapa01():
    arq = _achar_arquivo(["MAPA_GRUPOS_EMPRESAS*.xlsx"])
    m = pd.read_excel(arq, dtype=str).fillna("")
    m["REGISTRO_OPERADORA"] = registro6(m["REGISTRO_OPERADORA"])
    razao = m["RAZAO_SOCIAL"] if "RAZAO_SOCIAL" in m else ""
    ref = norm_serie(m["X_Nome_Apelido"] + " " + m["X_Nome_Operadora"] + " " + razao)
    m["X_Sigla"] = ""
    for padrao, sig in SIGLAS:
        m.loc[(m["X_Sigla"] == "") & ref.str.contains(padrao, regex=True), "X_Sigla"] = sig
    if (m["X_Sigla"] == "").any():
        log(f"MAPA 01: sem sigla -> {m.loc[m['X_Sigla'] == '', 'X_Nome_Apelido'].tolist()} (ficam fora)", "WARN")
        m = m[m["X_Sigla"] != ""]
    m["X_Grupo_Visao"] = m["X_Sigla"].map(lambda s: "Amil" if s == "AMIL" else "Nicho")
    log(f"MAPA 01 ({arq.name}): {len(m)} registros | " +
        ", ".join(f"{s}={sorted(g['REGISTRO_OPERADORA'])}" for s, g in m.groupby("X_Sigla")))
    return m[["REGISTRO_OPERADORA", "X_Nome_Operadora", "X_Grupo_Visao", "X_Sigla"]].reset_index(drop=True)


# ------------------------------------------------------------------ MAPA 02
GRID_GRUPO = {"AUTORIZ REGULACAO": "Autorização", "COBERT ROLL": "Autorização", "COBERT REDE": "Rede",
              "REEMBOLSO": "Reembolso", "MENSAL E REAJUSTE": "Mensalidade e Reajustes",
              "PRAZO MAXIMOS": "Prazo máximo de atendimento", "COBERT CPT": "Carência/CPT"}
GRID_OUTROS = "Contratos Outros Não Assistenciais"
ORDEM_N2 = ["Autorização", "Rede", "Reembolso", "Mensalidade e Reajustes",
            "Prazo máximo de atendimento", "Carência/CPT", GRID_OUTROS]
FALLBACK_TEMAS = [
    (r"PORTABILIDADE", "Contratos Portabil."), (r"REEMBOLSO", "Reembolso"),
    (r"SUSPENS|RESCIS", "Contratos Susp/Recisão"), (r"REAJUSTE|MENSALIDADE|COBRANCA", "Mensal. e Reajuste"),
    (r"CARENCIA|PREEXIST|CPT", "Cobert. CPT"), (r"PRAZO", "Prazo Máximos"), (r"REDE", "Cobert. Rede"),
    (r"\bROL\b", "Cobert. Roll"), (r"CONTRATACAO|ADESAO|VIGENCIA", "Contratos - Contratação/ Adesão/Vigência"),
    (r"ACESSO|AUTORIZ|REGULACAO|COBERTURA", "Autoriz. Regulação"), (r".*", "Contrato Outros")]


def grupo_grid(tema):
    k = re.sub(r"[^A-Z ]", "", unicodedata.normalize("NFKD", str(tema)).encode("ascii", "ignore").decode().upper())
    return GRID_GRUPO.get(re.sub(r"\s+", " ", k).strip(), GRID_OUTROS)


def carregar_mapa02():
    arq = _achar_arquivo(["MAPA_ASSUNTO*.xlsx"])
    m = pd.read_excel(arq, dtype=str).fillna("")
    m["X_Assunto"] = m["X_Assunto"].map(limpa_rotulo)
    m["X_Assunto_n2"] = m["X_Assunto_n2"].map(limpa_rotulo)
    m["CHAVE"] = chave_assunto(m["ASSUNTO"])
    m["X_Grupo_Grid"] = m["X_Assunto"].map(grupo_grid)
    m = m.drop_duplicates("CHAVE")
    log(f"MAPA 02 ({arq.name}): {len(m)} assuntos -> {m['X_Assunto'].nunique()} temas")
    return m[["ASSUNTO", "CHAVE", "X_Assunto", "X_Assunto_n2", "X_Grupo_Grid"]]


# ------------------------------------------------------------------ MAPA 03
def carregar_mapa03():
    arq = _achar_arquivo(["MAPA Regi*.xlsx", "MAPA*Regi*.xlsx"])
    m = pd.read_excel(arq, dtype=str).fillna("")
    m.columns = [limpa_rotulo(c) for c in m.columns]
    col_mun = next((c for c in m.columns if "MUNIC" in c.upper()), None)
    col_par = next((c for c in m.columns if "PARETO" in c.upper()), None)
    if not col_mun or not col_par:
        raise KeyError(f"{arq.name} precisa das colunas 'Município' e 'Pareto'. Encontradas: {list(m.columns)}")
    partes = m[col_mun].str.split(" - ", n=1, expand=True)
    out = pd.DataFrame({"SG_UF": norm_serie(partes[0]),
                        "NM_MUNICIPIO": norm_serie(partes[1]).str.replace("-", " ", regex=False),
                        "X_Regiao": m[col_par].map(limpa_rotulo)})
    log(f"MAPA 03 ({arq.name}): {len(out):,} municípios -> {out['X_Regiao'].nunique()} praças")
    return out


def carregar_mapas():
    return carregar_mapa01(), carregar_mapa02(), carregar_mapa03()
