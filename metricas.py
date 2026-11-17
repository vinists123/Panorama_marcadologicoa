# -*- coding: utf-8 -*-
"""
CAMADA GOLD - Indicadores do painel (metodologia do PPT "Panorama Mercadológico").

IGR do grupo/período ......... METODO_IGR = "media": média simples da coluna IGR da ANS
                                (linhas operadora x mês) - forma usada no PPT;
                                "ponderado": soma reclamações / soma beneficiários x 100 mil.
Fatias por tema (s9/s10) ..... IGR do grupo no período x participação do tema nas NIPs do grupo
                                (a soma das fatias = IGR do grupo, como nos gráficos do PPT).
Grid 12 meses (s11) .......... METODO_GRID: "nip_benef" = NIPs / beneficiários x 100 mil (padrão)
                                ou "fatia_igr" = fatia do IGR (soma = IGR do período).
Transbordo Pré-Auto (s10) .... % das NIPs do tema/grupo com a flag de Pré-Auto.
Praças (s8/s12) .............. NIPs da praça / (vidas médias da praça x nº meses) x 100 mil.
"""
import math

import pandas as pd

import config as C
from mapas_modelo import ORDEM_N2
from utils import log, meses_entre, rotulo_mes

K = 100_000
SIGLAS_NICHO = ["P", "S", "B"]          # ordem das colunas do grid no PPT: P | S | B | AMIL


def _r(v, n=2):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), n)


class Calculadora:
    def __init__(self, igr, nip, vidas, mapa02, cal):
        self.cal = cal
        excl = set(cal.get("registros_excluidos", []))
        self.igr = igr[~igr["REGISTRO_OPERADORA"].isin(excl)]
        self.nip = nip[~nip["REGISTRO_OPERADORA"].isin(excl)]
        self.vidas = vidas[~vidas["REGISTRO_OPERADORA"].isin(excl)] if vidas is not None else None
        self.mapa02 = mapa02
        self.metodo = cal.get("metodo_igr", C.METODO_IGR)
        self.flag = cal.get("pre_auto_flag") or C.PRE_AUTO_FLAG or "F_REGEX_GERAL"
        if self.flag not in self.nip.columns:
            self.flag = "F_REGEX_GERAL"
        self.col_reg = "X_Regiao_local" if cal.get("praca_municipio", C.PRACA_MUNICIPIO) == "local" else "X_Regiao_benef"
        self.escala = cal.get("praca_escala", C.PRACA_ESCALA)
        self.siglas_nicho = [s for s in SIGLAS_NICHO if s in set(self.igr["X_Sigla"])]
        self._cache = {}

    # ---------------------------------------------------------------- filtros
    def _grupo(self, df, g):
        if g == "AMIL":
            return df[df["X_Sigla"] == "AMIL"]
        if g == "NICHO":
            return df[df["X_Grupo_Visao"] == "Nicho"]
        if g == "TODOS":
            return df
        return df[df["X_Sigla"] == g]

    def igr_val(self, g, meses):
        chave = ("igr", g, tuple(meses))
        if chave in self._cache:
            return self._cache[chave]
        b = self._grupo(self.igr, g)
        b = b[b["COMPETENCIA"].isin(meses)]
        if b.empty:
            v = None
        elif self.metodo == "media":
            v = b["IGR"].dropna().mean()
        else:
            den = b["QTD_BENEFICIARIOS"].sum()
            v = b["QTD_RECLAMACOES"].sum() / den * K if den else None
        self._cache[chave] = _r(v)
        return self._cache[chave]

    def nips(self, g, meses):
        n = self._grupo(self.nip, g)
        return n[n["MES"].isin(meses)]

    # ---------------------------------------------------------------- períodos
    def periodos(self, fim):
        quad = meses_entre(fim, C.MESES_QUAD)
        p = pd.Period(quad[0], "M") - 1
        while p.month % 3 != 0:
            p -= 1
        tris = []
        for _ in range(C.QTD_TRIMESTRES):
            tris.append((f"{p.year} {p.month // 3}T", [str(p - 2), str(p - 1), str(p)]))
            p -= 3
        tris.reverse()
        rot = f"Quadrim. ({rotulo_mes(quad[0])[:3]}-{rotulo_mes(quad[-1])[:3]} {quad[-1][2:4]})"
        return {"fim": fim, "quad": quad, "rotulo_quad": rot, "trimestres": tris, "m12": meses_entre(fim, C.MESES_GRID)}

    # ---------------------------------------------------------------- s6 / s7
    def evolucao(self, per):
        blocos = per["trimestres"] + [(per["rotulo_quad"], per["quad"])] + [(m, [m]) for m in per["quad"]]
        labels = [b[0] for b in blocos]
        iq = len(per["trimestres"])
        serie = lambda g: [self.igr_val(g, m) for _, m in blocos]
        s6 = {"labels": labels, "idx_quad": iq, "amil": serie("AMIL"), "nicho": serie("NICHO"),
              "nicho_nome": "Outras do Nicho (" + ",".join(sorted(self.siglas_nicho)) + ")"}
        a, n = s6["amil"][iq], s6["nicho"][iq]
        s6["gap_pct"] = _r((n / a - 1) * 100, 1) if a and n else None     # "fomos X% melhores" (PPT)
        nomes = {"AMIL": "Amil", "B": "Player 1 (B)", "P": "Player 2 (P)", "S": "Player 3 (S)"}
        players = []
        for sg in ["AMIL", "B", "P", "S"]:
            if sg != "AMIL" and sg not in self.siglas_nicho:
                continue
            v = serie(sg)
            ant = v[iq - 1] if iq else None
            players.append({"sigla": sg, "nome": nomes[sg], "valores": v, "quad": v[iq],
                            "var_vs_tri": _r((v[iq] / ant - 1) * 100, 1) if v[iq] and ant else None})
        return s6, {"labels": labels, "idx_quad": iq, "players": players}

    # ---------------------------------------------------------------- fatias por tema
    def _fatias(self, g, meses, coluna="X_Assunto"):
        n = self.nips(g, meses)
        total = len(n)
        ig = self.igr_val(g, meses)
        if not total or ig is None:
            return {}, {}, {}
        cont = n.groupby(coluna).size()
        tr = n.groupby(coluna)[self.flag].mean()
        return ({t: ig * q / total for t, q in cont.items()}, cont.to_dict(), tr.to_dict())

    def temas(self, per, s6):
        meses = per["quad"]
        fa, qa, ta = self._fatias("AMIL", meses)
        fn, qn, tn = self._fatias("NICHO", meses)
        ft, _, _ = self._fatias("TODOS", meses)
        lista = []
        for t in sorted(ft, key=lambda x: -ft[x]):
            a, n = fa.get(t), fn.get(t)
            lista.append({"tema": t, "total": _r(ft.get(t)), "amil": _r(a), "nicho": _r(n),
                          "qtd_amil": int(qa.get(t, 0)), "qtd_nicho": int(qn.get(t, 0)),
                          "transb_amil": _r(ta.get(t), 4), "transb_nicho": _r(tn.get(t), 4),
                          "gap_pct": math.floor((a / n - 1) * 100) if a and n else None})
        tot = sum(x["total"] or 0 for x in lista)
        for x in lista:
            x["share"] = _r((x["total"] or 0) / tot, 4) if tot else 0
        iq = s6["idx_quad"]
        destaques = [x for x in lista if (x["gap_pct"] or 0) > 0 and x["share"] >= C.MIN_SHARE_DESTAQUE]
        s9 = {"periodo": per["rotulo_quad"], "temas": lista, "destaques": [x["tema"] for x in destaques],
              "podio": [{"nome": "Amil", "valor": s6["amil"][iq]},
                        {"nome": s6["nicho_nome"], "valor": s6["nicho"][iq]},
                        {"nome": "Amil + Nicho", "valor": self.igr_val("TODOS", meses)}],
              "qtd_piores": len(destaques)}
        pod = []
        for sg in ["AMIL", "B", "P", "S"]:
            if sg != "AMIL" and sg not in self.siglas_nicho:
                continue
            n = self.nips(sg, meses)
            pod.append({"nome": "Amil" if sg == "AMIL" else f"Player ({sg})", "sigla": sg,
                        "valor": _r(n[self.flag].mean(), 4) if len(n) else None})
        acima = [x["tema"] for x in lista if x["transb_amil"] is not None and x["transb_nicho"] is not None
                 and x["transb_amil"] > x["transb_nicho"]]
        s10 = {"periodo": per["rotulo_quad"], "temas": lista, "podio": pod, "acima": acima, "qtd_acima": len(acima)}
        return s9, s10

    # ---------------------------------------------------------------- s11 grid
    def grid(self, per):
        """
        Grid de maturidade 12 meses (slide 11).
        METODO_GRID = "nip_benef" -> NIPs do grupo de temas / beneficiários do IGR x 100 mil (provável regra do PPT)
        METODO_GRID = "fatia_igr" -> IGR do período x participação do tema (soma = IGR do período)
        """
        meses = per["m12"]
        cols = self.siglas_nicho + ["AMIL"]
        metodo = self.cal.get("metodo_grid", getattr(C, "METODO_GRID", "nip_benef"))

        def taxas(g):
            if metodo == "fatia_igr":
                f = self._fatias(g, meses, "X_Grupo_Grid")[0]
                return f, self.igr_val(g, meses)
            n = self.nips(g, meses)
            b = self._grupo(self.igr, g)
            den = b.loc[b["COMPETENCIA"].isin(meses), "QTD_BENEFICIARIOS"].sum()
            if not den:
                return {}, None
            f = {t: q / den * K for t, q in n.groupby("X_Grupo_Grid").size().items()}
            return f, len(n) / den * K

        fat, tot = {}, {}
        for g in cols + ["TODOS"]:
            fat[g], tot[g] = taxas(g)
        grupos = [g for g in ORDEM_N2 if any(g in fat[x] for x in fat)]
        linhas = []
        for g in grupos:
            vals = {s: _r(fat[s].get(g)) for s in cols}
            vals["NICHO"] = _r(fat["TODOS"].get(g))
            ordem = sorted([s for s in cols if vals[s] is not None], key=lambda s: vals[s])
            linhas.append({"grupo": g, "valores": vals, "rank": {s: i + 1 for i, s in enumerate(ordem)}})
        total = {s: _r(sum(v for v in fat[s].values() if v)) for s in cols}
        total["NICHO"] = _r(sum(v for v in fat["TODOS"].values() if v))
        return {"periodo": f"{rotulo_mes(meses[0]).capitalize()} a {rotulo_mes(meses[-1]).capitalize()}",
                "colunas": cols, "nicho_rotulo": "Nicho A" + "".join(cols[:-1]),
                "linhas": linhas, "total": total, "metodo": metodo}

    # ---------------------------------------------------------------- praças
    def pracas(self, per, s9):
        meses = per["quad"] if C.PERIODO_PRACAS == "quad" else per["m12"]
        nm = len(meses)
        v = self.vidas
        disp = sorted(v["MES"].unique()) if v is not None and len(v) else []
        usados = [m for m in meses if m in disp]
        if not usados and disp:
            anteriores = [m for m in disp if m <= meses[-1]] or disp
            usados = anteriores[-nm:]
        if not usados:
            return None
        vv = v[v["MES"].isin(usados)]
        vm = (vv.groupby(["X_Regiao", "X_Grupo_Visao", "MES"])["QT_BENEFICIARIO_ATIVO"].sum()
                .groupby(["X_Regiao", "X_Grupo_Visao"]).mean().unstack(fill_value=0))
        for g in ("Amil", "Nicho"):
            if g not in vm:
                vm[g] = 0
        n = self.nip[self.nip["MES"].isin(meses)]
        cont = n.groupby([self.col_reg, "X_Grupo_Visao", "X_Assunto"]).size()

        fator = {"Amil": 1.0, "Nicho": 1.0}
        if self.escala == "igr":
            for g, sg in (("Amil", "AMIL"), ("Nicho", "NICHO")):
                ng = (n["X_Grupo_Visao"] == g).sum()
                vt = vm[g].sum() * nm
                bruto = ng / vt * K if vt else None
                ig = self.igr_val(sg, meses)
                if bruto and ig:
                    fator[g] = ig / bruto

        regs = []
        for reg, row in vm.sort_values("Amil", ascending=False).iterrows():
            if reg in C.PRACAS_EXCLUIR or row["Amil"] <= 0:
                continue
            item = {"nome": reg, "vidas_amil": round(row["Amil"]), "vidas_nicho": round(row["Nicho"]),
                    "den_amil": row["Amil"] * nm / fator["Amil"], "den_nicho": row["Nicho"] * nm / fator["Nicho"],
                    "nips": {"Amil": {}, "Nicho": {}}}
            for g in ("Amil", "Nicho"):
                try:
                    item["nips"][g] = {t: int(q) for t, q in cont.loc[(reg, g)].items()}
                except KeyError:
                    pass
            regs.append(item)
            if len(regs) >= C.TOP_REGIOES:
                break
        tema_def = next((x["tema"] for x in s9["temas"] if (x["gap_pct"] or 0) > 0 and x["tema"] in s9["destaques"]),
                        s9["temas"][0]["tema"] if s9["temas"] else None)
        if any(x["tema"] == "Cobert. Rede" and (x["gap_pct"] or 0) > 0 for x in s9["temas"]):
            tema_def = "Cobert. Rede"          # default do PPT (s12)
        return {"periodo": per["rotulo_quad"], "meses": meses, "meses_vidas": usados, "regioes": regs,
                "temas": [x["tema"] for x in s9["temas"]], "tema_default": tema_def,
                "ref_temas": {x["tema"]: x["amil"] for x in s9["temas"]}}

    # ---------------------------------------------------------------- referência completa
    def referencia(self, fim):
        per = self.periodos(fim)
        s6, s7 = self.evolucao(per)
        s9, s10 = self.temas(per, s6)
        return {"ref": fim, "rotulo": rotulo_mes(fim), "s6": s6, "s7": s7, "s9": s9, "s10": s10,
                "s11": self.grid(per), "pracas": self.pracas(per, s9)}

    def serie_mensal(self, fim):
        meses = [str(p) for p in pd.period_range(f"{C.ANO_INICIO}-01", fim, freq="M")]
        out = {"meses": meses}
        for g in ["AMIL", "NICHO", "TODOS"] + self.siglas_nicho:
            out[g] = [self.igr_val(g, [m]) for m in meses]
        return out


# ------------------------------------------------------------------ competências disponíveis
def competencias_disponiveis(igr, nip):
    max_igr = igr.groupby("COMPETENCIA")["X_Sigla"].nunique()
    max_igr = max_igr[max_igr >= max_igr.max()].index.max()
    cont = nip.groupby("MES").size().sort_index()
    if len(cont) >= 2 and cont.iloc[-1] < 0.6 * cont.iloc[-2]:
        log(f"Mês {cont.index[-1]} da NIP incompleto ({cont.iloc[-1]:,} demandas) - desconsiderado", "WARN")
        cont = cont.iloc[:-1]
    fim = min(max_igr, cont.index.max())
    if C.COMPETENCIA_FIM:
        fim = min(fim, C.COMPETENCIA_FIM)
    refs = [str(p) for p in pd.period_range(C.MES_INICIO_PAINEL, fim, freq="M")]
    if C.COMPETENCIA_PPT <= fim and C.COMPETENCIA_PPT not in refs:
        refs = sorted(set(refs + [C.COMPETENCIA_PPT]))
    log(f"Competências do painel: {refs[0]} a {refs[-1]} ({len(refs)})  | IGR até {max_igr}, NIP até {cont.index.max()}")
    return refs
