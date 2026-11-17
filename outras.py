# -*- coding: utf-8 -*-
"""
OUTRAS OPERADORAS (botão "+ Comparar operadoras" - vale para o painel inteiro)
------------------------------------------------------------------------------
Usa as MESMAS bases já baixadas (IGR, NIP e beneficiários por município, que trazem
todas as operadoras) para calcular, das maiores operadoras médico-hospitalares do país:
  - evolução do IGR (capítulo 1 e linha do tempo)
  - fatias do IGR por tema e transbordo para Pré-Auto (capítulos 2 e 3)
  - grid de maturidade 12 meses (capítulo 1)
  - IGR por praça e por praça x tema (capítulo 4)

config.py (opcional):
  OUTRAS_OPERADORAS_TOP     = 30     # quantas operadoras (por nº de vidas) aparecem na lista
  OUTRAS_OPERADORAS_GRUPOS  = {}     # somar registros num grupo, ex.: {"Grupo X": ["123456", "654321"]}
  OUTRAS_ANALISE_COMPLETA   = True   # False = só IGR (sem temas, Pré-Auto, grid e praças)
"""
import math
import re

import pandas as pd

import config as C
from utils import log, norm_col, norm_serie, registro6, para_num, para_mes

K = 100_000
VIDAS_MIN_PRACA = 1000      # abaixo disso o IGR da praça fica instável e não é exibido


def _r(v, n=2):
    if v is None:
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else round(v, n)


def _nome_curto(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    s = re.sub(r"\b(S\.?\s?/?\s?A\.?|LTDA\.?|EIRELI)(?=\s|$)", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" -.,").title()[:48]


def _aninha(serie):
    """Series com MultiIndex (op, chave) -> {op: {chave: valor}}"""
    out = {}
    for (op, k), v in serie.items():
        out.setdefault(op, {})[k] = v
    return out


# ------------------------------------------------------------------ seleção das operadoras
def preparar(igr_raw, mapa01):
    df = igr_raw.copy()
    df.columns = [norm_col(c) for c in df.columns]
    df["REGISTRO_OPERADORA"] = registro6(df["REGISTRO_OPERADORA"])
    df["COMPETENCIA"] = para_mes(df["COMPETENCIA"])
    for c in ["IGR", "QTD_RECLAMACOES", "QTD_BENEFICIARIOS"]:
        df[c] = para_num(df[c])
    df = df[df["COMPETENCIA"] >= f"{C.ANO_INICIO}-01"]
    if "COBERTURA" in df.columns:
        df = df[norm_serie(df["COBERTURA"]).str.contains(C.COBERTURA_IGR, regex=False)]
    df = df[~df["REGISTRO_OPERADORA"].isin(set(mapa01["REGISTRO_OPERADORA"]))].copy()   # Amil e nicho já estão no painel

    nome = df["RAZAO_SOCIAL"] if "RAZAO_SOCIAL" in df.columns else df["REGISTRO_OPERADORA"]
    df["OP_ID"] = df["REGISTRO_OPERADORA"]
    df["OP_NOME"] = nome.map(_nome_curto)

    grupos = getattr(C, "OUTRAS_OPERADORAS_GRUPOS", {}) or {}
    extras = []
    for nome_g, regs in grupos.items():
        regs = set(registro6(pd.Series([str(r) for r in regs])))
        g = df[df["REGISTRO_OPERADORA"].isin(regs)].copy()
        if g.empty:
            log(f"Grupo '{nome_g}': nenhum registro encontrado no IGR", "WARN")
            continue
        g["OP_ID"] = "G_" + re.sub(r"[^A-Z0-9]", "", nome_g.upper())[:20]
        g["OP_NOME"] = f"{nome_g} (grupo)"
        extras.append(g)
    if extras:
        df = pd.concat([df] + extras, ignore_index=True)

    ult_nome = df.sort_values("COMPETENCIA").groupby("OP_ID")["OP_NOME"].last()
    df["OP_NOME"] = df["OP_ID"].map(ult_nome)

    ult = df["COMPETENCIA"].max()
    vidas = (df[df["COMPETENCIA"] == ult].groupby(["OP_ID", "OP_NOME"], as_index=False)["QTD_BENEFICIARIOS"].sum())
    top = getattr(C, "OUTRAS_OPERADORAS_TOP", 30)
    eh_grupo = vidas["OP_ID"].str.startswith("G_")
    sel = pd.concat([vidas[eh_grupo], vidas[~eh_grupo].nlargest(top, "QTD_BENEFICIARIOS")]).drop_duplicates("OP_ID")
    sel = sel.sort_values("QTD_BENEFICIARIOS", ascending=False).reset_index(drop=True)
    df = df[df["OP_ID"].isin(set(sel["OP_ID"]))]
    log(f"Outras operadoras disponíveis para comparação: {len(sel)} (top {top} por vidas em {ult})")
    return df, sel


def mapa_ext(mapa01, df_outras):
    """MAPA 01 + outras operadoras (grupo 'Outra', sigla = OP_ID). Um registro pode estar em mais de um OP_ID (grupos)."""
    ext = (df_outras[["REGISTRO_OPERADORA", "OP_ID", "OP_NOME"]].drop_duplicates(["REGISTRO_OPERADORA", "OP_ID"])
           .rename(columns={"OP_ID": "X_Sigla", "OP_NOME": "X_Nome_Operadora"}))
    ext["X_Grupo_Visao"] = "Outra"
    base = mapa01[["REGISTRO_OPERADORA", "X_Nome_Operadora", "X_Grupo_Visao", "X_Sigla"]]
    return pd.concat([base, ext[base.columns]], ignore_index=True)


# ------------------------------------------------------------------ cálculo
def calcular(df, sel, refs, calc, dados, meses_serie, nip_out=None, vidas_out=None):
    metodo = calc.metodo
    metodo_grid = calc.cal.get("metodo_grid", getattr(C, "METODO_GRID", "nip_benef"))
    agg = df.groupby(["OP_ID", "COMPETENCIA"]).agg(
        s_igr=("IGR", "sum"), n=("IGR", "count"), rec=("QTD_RECLAMACOES", "sum"), ben=("QTD_BENEFICIARIOS", "sum"))
    tab = {k: g.droplevel(0) for k, g in agg.groupby(level=0)}

    def _t(op, meses):
        t = tab.get(op)
        return None if t is None else t[t.index.isin(meses)]

    def val(op, meses):
        t = _t(op, meses)
        if t is None or t.empty:
            return None
        if metodo == "media":
            v = t["s_igr"].sum() / t["n"].sum() if t["n"].sum() else None
        else:
            v = t["rec"].sum() / t["ben"].sum() * K if t["ben"].sum() else None
        return _r(v)

    def ben(op, meses):
        t = _t(op, meses)
        return float(t["ben"].sum()) if t is not None and len(t) else 0.0

    ids = list(sel["OP_ID"])
    tem_nip = nip_out is not None and len(nip_out) > 0
    n_all = nip_out[nip_out["X_Sigla"].isin(ids)] if tem_nip else None
    flag = calc.flag if tem_nip and calc.flag in nip_out.columns else None
    tem_vidas = vidas_out is not None and len(vidas_out) > 0
    if tem_nip:
        log(f"Outras operadoras: {len(n_all):,} NIPs | Pré-Auto pela regra {flag} | "
            f"praças {'com' if tem_vidas else 'sem'} vidas por município")

    por_ref = {}
    for r in refs:
        per = calc.periodos(r)
        blocos = [m for _, m in per["trimestres"]] + [per["quad"]] + [[m] for m in per["quad"]]
        quad, m12 = per["quad"], per["m12"]
        cq = tq = ttot = c12 = pq = vv = {}
        nm = 1
        if tem_nip:
            nq = n_all[n_all["MES"].isin(quad)]
            n12 = n_all[n_all["MES"].isin(m12)]
            cq = _aninha(nq.groupby(["X_Sigla", "X_Assunto"]).size())
            tq = _aninha(nq.groupby(["X_Sigla", "X_Assunto"])[flag].mean()) if flag else {}
            ttot = nq.groupby("X_Sigla")[flag].mean().to_dict() if flag else {}
            c12 = _aninha(n12.groupby(["X_Sigla", "X_Grupo_Grid"]).size())
            pr = dados[r].get("pracas")
            if pr and tem_vidas:
                regs = [x["nome"] for x in pr["regioes"]]
                nm = len(pr["meses"])
                v = vidas_out[vidas_out["MES"].isin(pr["meses_vidas"]) & vidas_out["X_Regiao"].isin(regs)
                              & vidas_out["X_Sigla"].isin(ids)]
                vv = _aninha(v.groupby(["X_Sigla", "X_Regiao", "MES"])["QT_BENEFICIARIO_ATIVO"].sum()
                             .groupby(level=[0, 1]).mean())
                col = calc.col_reg
                pq = {}
                for (op, reg, t), q in nq[nq[col].isin(regs)].groupby(["X_Sigla", col, "X_Assunto"]).size().items():
                    pq.setdefault(op, {}).setdefault(reg, {})[t] = int(q)

        ent = {}
        for op in ids:
            e = {"evol": [val(op, b) for b in blocos]}
            if tem_nip:
                iq = val(op, quad)
                c = cq.get(op, {}); tot = sum(c.values())
                e["temas"] = {t: _r(iq * q / tot) for t, q in c.items()} if iq and tot else {}
                e["transb"] = {t: _r(x, 4) for t, x in tq.get(op, {}).items()}
                e["transb_tot"] = _r(ttot.get(op), 4)
                g = c12.get(op, {}); tg = sum(g.values())
                if metodo_grid == "fatia_igr":
                    i12 = val(op, m12)
                    e["grid"] = {k: _r(i12 * q / tg) for k, q in g.items()} if i12 and tg else {}
                else:
                    b = ben(op, m12)
                    e["grid"] = {k: _r(q / b * K) for k, q in g.items()} if b else {}
                e["grid_tot"] = _r(sum(x for x in e["grid"].values() if x)) if e["grid"] else None
                if vv:
                    e["pracas"] = {reg: {"vidas": round(vm), "den": round(vm * nm, 1), "nips": pq.get(op, {}).get(reg, {})}
                                   for reg, vm in vv.get(op, {}).items() if vm >= VIDAS_MIN_PRACA}
            ent[op] = e
        por_ref[r] = ent

    serie = {i: [val(i, [m]) for m in meses_serie] for i in ids}
    lista = [{"id": r.OP_ID, "nome": r.OP_NOME, "vidas": float(r.QTD_BENEFICIARIOS)} for r in sel.itertuples()]
    return {"lista": lista, "por_ref": por_ref, "serie": serie, "completa": bool(tem_nip)}
