# -*- coding: utf-8 -*-
"""Funções utilitárias: log, normalização de texto, datas e números."""
import re
import time
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd


def log(msg, nivel="INFO"):
    print(f"[{datetime.now():%H:%M:%S}] {nivel:<5} | {msg}", flush=True)


def etapa(titulo):
    print("\n" + "=" * 78 + f"\n  {titulo}\n" + "=" * 78, flush=True)


class Cronometro:
    def __init__(self, nome):
        self.nome = nome

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *a):
        log(f"{self.nome} concluído em {time.time() - self.t0:,.1f}s")


def sem_acento(txt):
    if txt is None or (isinstance(txt, float) and np.isnan(txt)):
        return ""
    txt = unicodedata.normalize("NFKD", str(txt))
    return "".join(c for c in txt if not unicodedata.combining(c)).upper().strip()


def norm_serie(s: pd.Series) -> pd.Series:
    s = s.fillna("").astype(str)
    return (s.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("ascii")
             .str.upper().str.strip())


def norm_col(c):
    return re.sub(r"[^A-Z0-9]+", "_", sem_acento(c)).strip("_")


def registro6(s: pd.Series) -> pd.Series:
    return s.astype(str).str.extract(r"(\d+)")[0].fillna("").str.lstrip("0").str.zfill(6)


def municipio6(s: pd.Series) -> pd.Series:
    d = s.astype(str).str.extract(r"(\d+)")[0].fillna("")
    return d.where(d.str.len() != 7, d.str[:6])


def para_num(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    s = s.astype(str).str.strip()
    br = s.str.contains(",", regex=False)
    s = s.where(~br, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def para_mes(s: pd.Series) -> pd.Series:
    """Converte qualquer formato de data/competência para 'YYYY-MM'."""
    x = s.astype(str).str.strip()
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    m = x.str.match(r"^\d{4}-\d{2}$");                   out[m] = x[m]
    m2 = x.str.match(r"^\d{6}$") & out.isna();           out[m2] = x[m2].str[:4] + "-" + x[m2].str[4:6]
    m3 = x.str.match(r"^\d{2}/\d{4}$") & out.isna();     out[m3] = x[m3].str[3:7] + "-" + x[m3].str[:2]
    m4 = x.str.match(r"^\d{4}/\d{2}$") & out.isna();     out[m4] = x[m4].str[:4] + "-" + x[m4].str[5:7]
    m5 = x.str.match(r"^\d{4}-\d{2}-\d{2}") & out.isna(); out[m5] = x[m5].str[:7]
    resto = out.isna()
    if resto.any():
        dayfirst = x[resto].str.contains("/").mean() > 0.5
        dt = pd.to_datetime(x[resto], errors="coerce", dayfirst=dayfirst)
        out[resto] = dt.dt.strftime("%Y-%m")
    return out


def meses_entre(fim, qtd):
    p = pd.Period(fim, "M")
    return [str(p - i) for i in range(qtd - 1, -1, -1)]


NOMES_MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def rotulo_mes(m):
    a, mm = m.split("-")
    return f"{NOMES_MES[int(mm) - 1]}{a[2:]}"


def ler_csv_flex(caminho, **kw):
    ultimo = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        for sep in (";", ","):
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=enc, low_memory=False, **kw)
                if df.shape[1] > 2:
                    return df
            except Exception as e:  # noqa
                ultimo = e
    raise RuntimeError(f"Não foi possível ler o CSV {caminho}: {ultimo}")
