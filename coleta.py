# -*- coding: utf-8 -*-
"""
CAMADA BRONZE - Coleta dos dados abertos da ANS (com cache por Last-Modified)
  1) IGR                              -> pda-023-igr.csv
  2) Demandas NIP (todos os anos)     -> pda-013-...-AAAA.csv
  3) Beneficiários por município      -> pda-024-icb-UF-AAAA_MM.zip (agregado e descartado)
v5: o cache de beneficiários guarda quais operadoras foram agregadas; se entrarem operadoras
    novas (botão Comparar operadoras), o cache é refeito uma única vez.
"""
import json
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
import urllib3

import config as C
from utils import log, registro6, municipio6, norm_serie, ler_csv_flex

if not C.VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (PanoramaMercadologico/5.0)"})


def _head(url):
    try:
        r = _S.head(url, allow_redirects=True, timeout=60, verify=C.VERIFY_SSL)
        return (r.headers.get("Last-Modified") or "") if r.status_code == 200 else None
    except Exception:
        return None


def baixar(url, destino: Path, forcar=False, silencioso=False):
    destino.parent.mkdir(parents=True, exist_ok=True)
    meta = destino.with_suffix(destino.suffix + ".meta.json")
    remoto = _head(url)
    if remoto is None and not destino.exists():
        raise FileNotFoundError(url)
    if destino.exists() and meta.exists() and not forcar:
        local = json.loads(meta.read_text()).get("last_modified")
        if remoto is None or remoto == local:
            if not silencioso:
                log(f"cache OK  -> {destino.name} (ANS: {local})")
            return local
    for tent in range(1, C.HTTP_RETRIES + 1):
        try:
            if not silencioso:
                log(f"baixando  -> {url}")
            tmp = destino.with_suffix(destino.suffix + ".part")
            with _S.get(url, stream=True, timeout=C.HTTP_TIMEOUT, verify=C.VERIFY_SSL) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for bloco in r.iter_content(chunk_size=1024 * 1024):
                        f.write(bloco)
            tmp.replace(destino)
            meta.write_text(json.dumps({"url": url, "last_modified": remoto}))
            return remoto
        except Exception as e:
            log(f"tentativa {tent}/{C.HTTP_RETRIES} falhou ({destino.name}): {e}", "WARN")
    raise RuntimeError(f"Falha ao baixar {url}")


# ------------------------------------------------------------------ IGR
def coletar_igr(usar_cache=False):
    destino = C.DIR_BRONZE / "igr" / "pda-023-igr.csv"
    if not (usar_cache and destino.exists()):
        lm = baixar(C.URL_IGR, destino)
    else:
        meta = destino.with_suffix(".csv.meta.json")
        lm = json.loads(meta.read_text()).get("last_modified") if meta.exists() else None
    df = ler_csv_flex(destino)
    df.columns = [c.strip().upper() for c in df.columns]
    log(f"IGR bruto: {len(df):,} linhas")
    return df, lm


# ------------------------------------------------------------------ NIP
def coletar_nip(usar_cache=False):
    partes, versoes = [], {}
    for ano in C.ANOS_NIP:
        if ano > pd.Timestamp.today().year:
            break
        url = C.URL_NIP.format(ano=ano)
        destino = C.DIR_BRONZE / "nip" / f"pda-013-nip-{ano}.csv"
        try:
            if usar_cache and destino.exists():
                meta = destino.with_suffix(".csv.meta.json")
                lm = json.loads(meta.read_text()).get("last_modified") if meta.exists() else None
            else:
                lm = baixar(url, destino)
        except FileNotFoundError:
            log(f"NIP {ano}: ainda não publicado pela ANS", "WARN")
            continue
        df = ler_csv_flex(destino, dtype=str)
        df.columns = [c.strip().upper() for c in df.columns]
        versoes[ano] = lm
        log(f"NIP {ano}: {len(df):,} linhas")
        partes.append(df)
    if not partes:
        raise RuntimeError("Nenhum arquivo NIP disponível.")
    return pd.concat(partes, ignore_index=True), versoes


# ------------------------------------------------------------------ BENEFICIÁRIOS
def listar_meses_beneficiarios():
    try:
        r = _S.get(C.URL_BENEF_DIR, timeout=60, verify=C.VERIFY_SSL)
        r.raise_for_status()
        return sorted(set(re.findall(r'href="(\d{6})/?"', r.text)))
    except Exception as e:
        log(f"Não consegui listar a pasta de beneficiários: {e}", "WARN")
        return []


_COLS = ["ID_CMPT_MOVEL", "CD_OPERADORA", "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO",
         "COBERTURA_ASSIST_PLAN", "QT_BENEFICIARIO_ATIVO"]
_CHAVE = ["ID_CMPT_MOVEL", "CD_OPERADORA", "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO"]


def _agrega_zip(caminho_zip: Path, registros: set):
    agg = []
    with zipfile.ZipFile(caminho_zip) as z:
        nome = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(nome) as f:
            amostra = f.read(300_000)
        try:
            amostra[:-4].decode("utf-8"); enc = "utf-8"
        except UnicodeDecodeError:
            enc = "latin-1"
        with z.open(nome) as f:
            for bloco in pd.read_csv(f, sep=";", encoding=enc, dtype=str, chunksize=500_000,
                                     usecols=lambda c: c.strip().upper() in _COLS):
                bloco.columns = [c.strip().upper() for c in bloco.columns]
                bloco["CD_OPERADORA"] = registro6(bloco["CD_OPERADORA"])
                bloco = bloco[bloco["CD_OPERADORA"].isin(registros)]
                if bloco.empty:
                    continue
                if "COBERTURA_ASSIST_PLAN" in bloco:
                    cob = norm_serie(bloco["COBERTURA_ASSIST_PLAN"])
                    bloco = bloco[~(cob.str.contains("ODONTO") & ~cob.str.contains("MEDIC|HOSPITAL|AMBULAT"))]
                bloco["QT_BENEFICIARIO_ATIVO"] = pd.to_numeric(bloco["QT_BENEFICIARIO_ATIVO"], errors="coerce").fillna(0)
                bloco["CD_MUNICIPIO"] = municipio6(bloco["CD_MUNICIPIO"])
                agg.append(bloco.groupby(_CHAVE, as_index=False, dropna=False)["QT_BENEFICIARIO_ATIVO"].sum())
    if not agg:
        return pd.DataFrame(columns=_CHAVE + ["QT_BENEFICIARIO_ATIVO"])
    return pd.concat(agg).groupby(_CHAVE, as_index=False, dropna=False)["QT_BENEFICIARIO_ATIVO"].sum()


def _processar_uf(aaaamm, uf, registros, pasta):
    saida = pasta / f"{aaaamm}_{uf}.csv"
    if saida.exists():
        return pd.read_csv(saida, dtype=str), "cache"
    aaaa, mm = aaaamm[:4], aaaamm[4:]
    url = C.URL_BENEF_ARQ.format(aaaamm=aaaamm, uf=uf, aaaa=aaaa, mm=mm)
    zip_path = pasta / "zips" / f"pda-024-icb-{uf}-{aaaa}_{mm}.zip"
    try:
        baixar(url, zip_path, silencioso=True)
    except FileNotFoundError:
        return None, "inexistente"
    df = _agrega_zip(zip_path, registros)
    df.to_csv(saida, index=False)
    zip_path.unlink(missing_ok=True)
    Path(str(zip_path) + ".meta.json").unlink(missing_ok=True)
    return df.astype(str), "baixado"


def _validar_cache(pasta: Path, registros: set):
    """Se o cache foi montado com menos operadoras do que as pedidas agora, apaga para refazer (uma vez)."""
    marcador = pasta / "_registros.json"
    csvs = list(pasta.glob("??????_??.csv"))
    if marcador.exists():
        anteriores = set(json.loads(marcador.read_text()))
    elif csvs:
        anteriores = set()
        for f in csvs:
            try:
                anteriores |= set(registro6(pd.read_csv(f, dtype=str, usecols=["CD_OPERADORA"])["CD_OPERADORA"]))
            except Exception:
                pass
    else:
        anteriores = set(registros)
    novos = set(registros) - anteriores
    if novos and csvs:
        log(f"Beneficiários: {len(novos)} operadoras novas para comparação - o cache de vidas por município "
            f"será refeito UMA vez (a próxima execução volta a ser rápida).", "WARN")
        for f in csvs:
            f.unlink(missing_ok=True)
    marcador.write_text(json.dumps(sorted(set(registros) | (anteriores if not novos else set()))))


def coletar_vidas(meses, registros):
    """Baixa (em paralelo) os meses pedidos que a ANS já publicou. Retorna base e meses obtidos."""
    disponiveis = listar_meses_beneficiarios()
    pasta = C.DIR_BRONZE / "vidas"
    (pasta / "zips").mkdir(parents=True, exist_ok=True)
    _validar_cache(pasta, set(registros))
    tarefas = []
    for mes in sorted(set(meses)):
        aaaamm = mes.replace("-", "")
        tem_cache = any(pasta.glob(f"{aaaamm}_*.csv"))
        if disponiveis and aaaamm not in disponiveis and not tem_cache:
            continue
        tarefas += [(aaaamm, uf) for uf in C.UFS]
    partes, ok = [], set()
    if tarefas:
        log(f"Beneficiários: {len(tarefas)} arquivos (UF x mês) - {C.DOWNLOADS_PARALELOS} downloads em paralelo")
    with ThreadPoolExecutor(max_workers=C.DOWNLOADS_PARALELOS) as ex:
        fut = {ex.submit(_processar_uf, a, u, registros, pasta): (a, u) for a, u in tarefas}
        feitos = 0
        for f in as_completed(fut):
            a, u = fut[f]
            df, st = f.result()
            feitos += 1
            if df is not None:
                partes.append(df)
                ok.add(f"{a[:4]}-{a[4:]}")
            if st == "baixado":
                log(f"  ok {a} {u}  ({feitos}/{len(tarefas)})")
    if not partes:
        return pd.DataFrame(columns=_CHAVE + ["QT_BENEFICIARIO_ATIVO"]), []
    df = pd.concat(partes, ignore_index=True)
    df["QT_BENEFICIARIO_ATIVO"] = pd.to_numeric(df["QT_BENEFICIARIO_ATIVO"], errors="coerce").fillna(0)
    log(f"Beneficiários disponíveis: {sorted(ok)}")
    return df, sorted(ok)
