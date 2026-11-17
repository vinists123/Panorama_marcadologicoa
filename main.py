# -*- coding: utf-8 -*-
"""
PANORAMA MERCADOLÓGICO DE NIP - Orquestrador (v5 · mensal + comparar operadoras)
================================================================================
Coleta ANS -> Bronze -> Silver -> Calibração com o PPT -> Gold (todas as competências) -> HTML -> SharePoint

    py main.py                     # roda tudo e publica
    py main.py --cache             # não consulta a ANS (usa o que já foi baixado)
    py main.py --sem-publicar      # só gera o HTML local
    py main.py --recalibrar        # refaz a calibração com o PPT
    py main.py --diagnostico       # raio-x das colunas da NIP
"""
import argparse
import json

import pandas as pd

import config as C
import coleta
import dashboard
import metricas
import outras
import sharepoint
import tratamento as T
from calibrar import calibrar, conferencia
from mapas_modelo import carregar_mapas
from utils import log, etapa, Cronometro, rotulo_mes

GRUPOS_PAINEL = ["Amil", "Nicho"]


def executar(usar_cache=False, diagnostico=False, publicar=True, recalibrar=False):
    for p in (C.DIR_BRONZE, C.DIR_SILVER, C.DIR_GOLD, C.DIR_SAIDA):
        p.mkdir(parents=True, exist_ok=True)

    etapa("0) MAPAS")
    m1, m2, m3 = carregar_mapas()

    etapa("1) BRONZE - coleta ANS")
    with Cronometro("IGR"):
        igr_raw, v_igr = coleta.coletar_igr(usar_cache)
    with Cronometro("NIP"):
        nip_raw, v_nip = coleta.coletar_nip(usar_cache)
    if diagnostico:
        T.diagnostico_nip(nip_raw, C.DIR_SILVER / "diagnostico_nip.txt")
        return None

    # ---- outras operadoras de saúde (botão "+ Comparar operadoras")
    op_df = op_sel = None
    m_ext = m1
    try:
        op_df, op_sel = outras.preparar(igr_raw, m1)
        if getattr(C, "OUTRAS_ANALISE_COMPLETA", True):
            m_ext = outras.mapa_ext(m1, op_df)
    except Exception as e:
        log(f"Outras operadoras não preparadas: {e}", "WARN")

    etapa("2) SILVER - tratamento + mapas")
    igr = T.tratar_igr(igr_raw, m1)
    nip_all = T.tratar_nip(nip_raw, m_ext, m2)
    del nip_raw
    refs = metricas.competencias_disponiveis(igr, nip_all[nip_all["X_Grupo_Visao"].isin(GRUPOS_PAINEL)])

    meses_vidas = set()
    for r in refs:
        meses_vidas.update(pd.period_range(pd.Period(r, "M") - (C.MESES_QUAD - 1), r, freq="M").astype(str))
    with Cronometro("Beneficiários por município"):
        vidas_raw, _ = coleta.coletar_vidas(sorted(meses_vidas), set(m_ext["REGISTRO_OPERADORA"]))
    vidas_all = T.tratar_vidas(vidas_raw, m_ext)
    vidas_all["X_Regiao"] = T.mapear_regiao(vidas_all["SG_UF"], vidas_all["NM_MUNICIPIO"], m3)
    nip_all = T.regioes_nip(nip_all, m3, vidas_all)

    nip = nip_all[nip_all["X_Grupo_Visao"].isin(GRUPOS_PAINEL)]
    vidas = vidas_all[vidas_all["X_Grupo_Visao"].isin(GRUPOS_PAINEL)]
    nip_out = nip_all[nip_all["X_Grupo_Visao"] == "Outra"]
    vidas_out = vidas_all[vidas_all["X_Grupo_Visao"] == "Outra"]

    igr.to_csv(C.DIR_SILVER / "silver_igr.csv", index=False, encoding="utf-8-sig")
    nip.drop(columns=[c for c in nip.columns if c.startswith("F_")]).to_csv(
        C.DIR_SILVER / "silver_nip.csv", index=False, encoding="utf-8-sig")

    etapa("3) CALIBRAÇÃO (metodologia do PPT)")
    if recalibrar or not C.ARQ_CALIBRACAO.exists():
        cal = calibrar(igr, nip, vidas, m1, m2) or {}
    else:
        cal = json.loads(C.ARQ_CALIBRACAO.read_text(encoding="utf-8"))
        log(f"Usando calibração salva ({C.ARQ_CALIBRACAO.name}): método={cal.get('metodo_igr')}, "
            f"pré-auto={cal.get('pre_auto_flag')}, excluídos={cal.get('registros_excluidos')}")

    etapa("4) GOLD - todas as competências")
    calc = metricas.Calculadora(igr, nip, vidas, m2, cal)
    dados = {}
    for r in refs:
        dados[r] = calc.referencia(r)
        s6 = dados[r]["s6"]; iq = s6["idx_quad"]
        log(f"  {r}: IGR Amil {s6['amil'][iq]} | Nicho {s6['nicho'][iq]} | {s6['labels'][iq]}")
    if C.COMPETENCIA_PPT in dados:
        conferencia(dados[C.COMPETENCIA_PPT], C.DIR_GOLD / "conferencia_ppt.xlsx")
    serie = calc.serie_mensal(refs[-1])

    pac_outras = None
    if op_df is not None:
        try:
            with Cronometro("Outras operadoras"):
                pac_outras = outras.calcular(op_df, op_sel, refs, calc, dados, serie["meses"],
                                             nip_out if len(nip_out) else None, vidas_out if len(vidas_out) else None)
        except Exception as e:
            log(f"Outras operadoras não calculadas: {e}", "WARN")

    nicho = m1[m1["X_Grupo_Visao"] == "Nicho"]
    excl = set(cal.get("registros_excluidos", []))
    pacote = {
        "meta": {"refs": refs, "ref_padrao": refs[-1], "ref_ppt": C.COMPETENCIA_PPT,
                 "rotulos": {r: rotulo_mes(r) for r in refs},
                 "nicho": "; ".join(f"{sg} = {g['X_Nome_Operadora'].iloc[0]} (registros "
                                    f"{', '.join(x for x in g['REGISTRO_OPERADORA'] if x not in excl)})"
                                    for sg, g in nicho.groupby("X_Sigla")),
                 "metodo": cal.get("metodo_igr", C.METODO_IGR),
                 "fontes": [{"nome": "IGR", "url": C.URL_IGR, "versao": v_igr},
                            {"nome": "Demandas NIP", "url": C.URL_NIP.rsplit("/", 1)[0] + "/",
                             "versao": " · ".join(f"{a}: {v}" for a, v in v_nip.items() if v)},
                            {"nome": "Beneficiários por município", "url": C.URL_BENEF_DIR, "versao": None}]},
        "serie": serie,
        "dados": dados,
        "outras": pac_outras,
    }
    (C.DIR_GOLD / "gold_painel.json").write_text(json.dumps(pacote, ensure_ascii=False, default=str), encoding="utf-8")

    etapa("5) HTML + SharePoint")
    html = dashboard.gerar_html(pacote, C.DIR_SAIDA / C.NOME_HTML)
    log(f"HTML gerado: {html} ({html.stat().st_size / 1e6:.2f} MB) | {len(refs)} competências")
    if publicar:
        try:
            sharepoint.publicar(html)
        except Exception as e:
            log(f"Falha ao publicar no SharePoint: {e}", "ERRO")
    return html


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Panorama Mercadológico de NIP")
    ap.add_argument("--cache", action="store_true")
    ap.add_argument("--diagnostico", action="store_true")
    ap.add_argument("--sem-publicar", action="store_true")
    ap.add_argument("--recalibrar", action="store_true")
    a = ap.parse_args()
    executar(usar_cache=a.cache, diagnostico=a.diagnostico, publicar=not a.sem_publicar, recalibrar=a.recalibrar)
