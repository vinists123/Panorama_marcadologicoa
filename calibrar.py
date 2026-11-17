# -*- coding: utf-8 -*-
"""
CALIBRAÇÃO CONTRA O PPT APRESENTADO
-----------------------------------
Os números do PPT (assets/referencia_ppt.json) foram extraídos dos próprios gráficos do
"Croqui e informações.pptx". Este módulo testa as variações de regra possíveis e escolhe,
de forma objetiva (menor erro), a combinação que reproduz o PPT:

  1) Método do IGR ............ média simples x ponderado
  2) Registros por player ..... quais registros de B / P / S compõem cada player
  3) Regra de Pré-Auto ........ qual coluna/valor da NIP gera o % de transbordo do slide 10
  4) Praças ................... município do beneficiário x local de atendimento; escala direta x IGR

Saídas: dados/calibracao.json (usado pelo main.py) e dados/gold/conferencia_ppt.xlsx
        (cada número do PPT x número calculado x diferença).
"""
import itertools
import json
import re
import unicodedata

import numpy as np
import pandas as pd

import config as C
from metricas import Calculadora
from utils import log, etapa


def _k(nome):
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z]+", s)[0] if re.findall(r"[a-z]+", s) else s


def _mae(a, b):
    p = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    return np.mean([abs(x - y) for x, y in p]) if p else 1e9


def carregar_ref():
    return json.loads(C.ARQ_REF_PPT.read_text(encoding="utf-8"))


def calibrar(igr, nip, vidas, mapa01, mapa02, salvar=True):
    etapa("CALIBRAÇÃO CONTRA O PPT (abr-jul/26)")
    ref = carregar_ref()
    fim = ref["competencia"]
    if fim not in set(igr["COMPETENCIA"]):
        log("Competência do PPT fora da base - calibração ignorada", "WARN")
        return None

    # ---------- 1 + 2) método e registros por player (slide 7)
    melhor = None
    for metodo in ("media", "ponderado"):
        excl, erro_tot, det = [], 0.0, {}
        for sg in ["AMIL", "B", "P", "S"]:
            regs = sorted(mapa01.loc[mapa01["X_Sigla"] == sg, "REGISTRO_OPERADORA"])
            best, cheio = None, None
            for n in range(len(regs), 0, -1):
                for sub in itertools.combinations(regs, n):
                    fora = [r for r in regs if r not in sub]
                    calc = Calculadora(igr, nip, None, mapa02, {"metodo_igr": metodo, "registros_excluidos": fora})
                    per = calc.periodos(fim)
                    s6, s7 = calc.evolucao(per)
                    pl = next((p for p in s7["players"] if p["sigla"] == sg), None)
                    if not pl:
                        continue
                    e = _mae(pl["valores"], ref["s7"][sg])
                    if cheio is None:
                        cheio = (e, fora, sub)          # todos os registros do mapa
                    if best is None or e < best[0]:
                        best = (e, fora, sub)
            # só exclui registros do mapa se a melhora for relevante (evita ajustar ruído)
            if best and cheio and best[0] > cheio[0] - 0.3:
                best = cheio
            if best:
                erro_tot += best[0]
                excl += best[1]
                det[sg] = {"erro_medio": round(best[0], 3), "registros": list(best[2])}
        log(f"  método {metodo:<9}: erro médio por ponto = {erro_tot / 4:.3f}  {det}")
        if melhor is None or erro_tot < melhor[0]:
            melhor = (erro_tot, metodo, excl, det)
    _, metodo, excl, det = melhor
    log(f"=> Método escolhido: {metodo} | registros excluídos: {excl or 'nenhum'}")

    # ---------- 3) regra de Pré-Auto (slide 10)
    calc = Calculadora(igr, nip, None, mapa02, {"metodo_igr": metodo, "registros_excluidos": excl})
    per = calc.periodos(fim)
    n4 = calc.nip[calc.nip["MES"].isin(per["quad"])]
    flags = [c for c in nip.columns if c.startswith("F_")]
    alvo_pod = ref["s10"]["podio"]
    temas = ref["s10"]["temas"]
    ranking = []
    for f in flags:
        pod = n4.groupby("X_Sigla")[f].mean()
        e1 = _mae([pod.get(s) for s in alvo_pod], list(alvo_pod.values()))
        ta = n4[n4["X_Grupo_Visao"] == "Amil"].groupby("X_Assunto")[f].mean()
        tn = n4[n4["X_Grupo_Visao"] == "Nicho"].groupby("X_Assunto")[f].mean()
        e2 = _mae([ta.get(t) for t in temas], ref["s10"]["transb_amil"])
        e3 = _mae([tn.get(t) for t in temas], ref["s10"]["transb_nicho"])
        ranking.append((e1 + e2 + e3, f, {s: round(float(pod.get(s, np.nan)), 4) for s in alvo_pod}))
    ranking.sort()
    for e, f, p in ranking[:5]:
        log(f"  Pré-Auto {f:<55} erro={e:.4f}  pódio={p}")
    flag = ranking[0][1] if ranking else None
    log(f"=> Regra de Pré-Auto escolhida: {flag}")

    # ---------- 4) praças (slide 8)
    if vidas is not None and len(vidas):
        alvo = {_k(n): (a, b) for n, a, b in zip(ref["s8"]["pracas"], ref["s8"]["amil"], ref["s8"]["nicho"])}
        best_p = None
        for mun in ("beneficiario", "local"):
            for esc in ("direto", "igr"):
                cal = {"metodo_igr": metodo, "registros_excluidos": excl, "pre_auto_flag": flag,
                       "praca_municipio": mun, "praca_escala": esc}
                cc = Calculadora(igr, nip, vidas, mapa02, cal)
                r = cc.referencia(fim)
                if not r["pracas"]:
                    continue
                calc_a, ref_a = [], []
                for reg in r["pracas"]["regioes"]:
                    k = _k(reg["nome"])
                    if k in alvo:
                        qa = sum(reg["nips"]["Amil"].values()); qn = sum(reg["nips"]["Nicho"].values())
                        calc_a += [qa / reg["den_amil"] * 1e5 if reg["den_amil"] else None,
                                   qn / reg["den_nicho"] * 1e5 if reg["den_nicho"] else None]
                        ref_a += list(alvo[k])
                e = _mae(calc_a, ref_a)
                log(f"  Praças município={mun:<12} escala={esc:<6} erro médio={e:.2f}")
                if best_p is None or e < best_p[0]:
                    best_p = (e, mun, esc)
        mun, esc = best_p[1], best_p[2]
    else:
        mun, esc = C.PRACA_MUNICIPIO, C.PRACA_ESCALA
    log(f"=> Praças: município={mun}, escala={esc}")

    cal = {"metodo_igr": metodo, "registros_excluidos": excl, "pre_auto_flag": flag,
           "praca_municipio": mun, "praca_escala": esc, "detalhe_players": det,
           "top_pre_auto": [[round(e, 4), f] for e, f, _ in ranking[:5]]}
    if salvar:
        C.ARQ_CALIBRACAO.parent.mkdir(parents=True, exist_ok=True)
        C.ARQ_CALIBRACAO.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"Calibração salva em {C.ARQ_CALIBRACAO}")
    return cal


# ------------------------------------------------------------------ conferência número a número
def conferencia(ref_calc, caminho):
    ref = carregar_ref()
    linhas = []

    def add(slide, item, ppt, calc):
        dif = None if ppt is None or calc is None else round(calc - ppt, 4)
        st = "—" if dif is None else ("OK" if abs(dif) <= 0.051 else ("≈" if abs(dif) <= 0.5 else "DIFERENTE"))
        linhas.append({"slide": slide, "item": item, "PPT": ppt, "calculado": calc, "diferença": dif, "status": st})

    s6 = ref_calc["s6"]
    for i, lab in enumerate(ref["s6"]["labels"]):
        add("s6", f"Amil · {lab}", ref["s6"]["amil"][i], s6["amil"][i])
        add("s6", f"Nicho · {lab}", ref["s6"]["nicho"][i], s6["nicho"][i])
    for p in ref_calc["s7"]["players"]:
        for i, lab in enumerate(ref["s6"]["labels"]):
            add("s7", f"{p['sigla']} · {lab}", ref["s7"][p["sigla"]][i], p["valores"][i])
    t = {x["tema"]: x for x in ref_calc["s9"]["temas"]}
    for i, tema in enumerate(ref["s9"]["temas"]):
        x = t.get(tema, {})
        add("s9", f"Amil · {tema}", ref["s9"]["amil"][i], x.get("amil"))
        add("s9", f"Nicho · {tema}", ref["s9"]["nicho"][i], x.get("nicho"))
        add("s9", f"Amil+Nicho · {tema}", ref["s9"]["total"][i], x.get("total"))
        add("s10", f"Transb. Amil · {tema}", ref["s10"]["transb_amil"][i], x.get("transb_amil"))
        add("s10", f"Transb. Nicho · {tema}", ref["s10"]["transb_nicho"][i], x.get("transb_nicho"))
    for p in ref_calc["s10"]["podio"]:
        add("s10", f"Pódio Pré-Auto · {p['sigla']}", ref["s10"]["podio"].get(p["sigla"]), p["valor"])
    g = {l["grupo"]: l["valores"] for l in ref_calc["s11"]["linhas"]}
    for grupo, vals in ref["s11"]["linhas"].items():
        for col, v in zip(ref["s11"]["colunas"], vals):
            add("s11", f"{grupo} · {col}", v, g.get(grupo, {}).get(col))
    for col, v in zip(ref["s11"]["colunas"], ref["s11"]["total"]):
        add("s11", f"Total · {col}", v, ref_calc["s11"]["total"].get(col))
    if ref_calc.get("pracas"):
        pr = {_k(r["nome"]): r for r in ref_calc["pracas"]["regioes"]}
        for nome, a, n in zip(ref["s8"]["pracas"], ref["s8"]["amil"], ref["s8"]["nicho"]):
            r = pr.get(_k(nome))
            ca = cn = None
            if r:
                qa = sum(r["nips"]["Amil"].values()); qn = sum(r["nips"]["Nicho"].values())
                ca = round(qa / r["den_amil"] * 1e5, 2) if r["den_amil"] else None
                cn = round(qn / r["den_nicho"] * 1e5, 2) if r["den_nicho"] else None
            add("s8", f"Amil · {nome}", a, ca)
            add("s8", f"Nicho · {nome}", n, cn)
    df = pd.DataFrame(linhas)
    resumo = df.groupby("slide")["status"].value_counts().unstack(fill_value=0)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho) as xw:
        resumo.to_excel(xw, sheet_name="resumo")
        df.to_excel(xw, sheet_name="numero_a_numero", index=False)
    log("Conferência com o PPT (OK = diferença até 0,05):\n" + resumo.to_string())
    log(f"Detalhe número a número: {caminho}")
    return df
