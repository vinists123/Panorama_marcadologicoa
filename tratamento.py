# -*- coding: utf-8 -*-
"""
CAMADA SILVER - Tratamento, padronização e aplicação dos MAPAS 01/02/03.
v5: aceita o MAPA 01 estendido (Amil + Nicho + outras operadoras para comparação).
"""
import pandas as pd

import config as C
from mapas_modelo import chave_assunto, FALLBACK_TEMAS, grupo_grid
from utils import log, norm_serie, norm_col, registro6, municipio6, para_num, para_mes

_COLS_MAPA = ["REGISTRO_OPERADORA", "X_Grupo_Visao", "X_Sigla"]


# ================================================================== IGR
def tratar_igr(df, mapa01):
    df = df.copy()
    df.columns = [norm_col(c) for c in df.columns]
    obrig = ["REGISTRO_OPERADORA", "COMPETENCIA", "IGR", "QTD_RECLAMACOES", "QTD_BENEFICIARIOS"]
    falt = [c for c in obrig if c not in df.columns]
    if falt:
        raise KeyError(f"IGR sem as colunas {falt}. Encontradas: {list(df.columns)}")
    df["REGISTRO_OPERADORA"] = registro6(df["REGISTRO_OPERADORA"])
    df["COMPETENCIA"] = para_mes(df["COMPETENCIA"])
    for c in ["IGR", "QTD_RECLAMACOES", "QTD_BENEFICIARIOS"]:
        df[c] = para_num(df[c])
    df = df[df["COMPETENCIA"] >= f"{C.ANO_INICIO}-01"]
    if "COBERTURA" in df.columns:
        df = df[norm_serie(df["COBERTURA"]).str.contains(C.COBERTURA_IGR, regex=False)]
    df = df.merge(mapa01[_COLS_MAPA].drop_duplicates(), on="REGISTRO_OPERADORA", how="inner")
    comp = sorted(df["COMPETENCIA"].dropna().unique())
    log(f"IGR silver: {len(df):,} linhas | competências {comp[0]} a {comp[-1]}")
    falt = set(mapa01["REGISTRO_OPERADORA"]) - set(df["REGISTRO_OPERADORA"])
    if falt:
        log(f"Registros do MAPA 01 sem IGR publicado: {sorted(falt)}", "WARN")
    return df[["REGISTRO_OPERADORA", "COMPETENCIA", "IGR", "QTD_RECLAMACOES", "QTD_BENEFICIARIOS",
               "X_Grupo_Visao", "X_Sigla"]].reset_index(drop=True)


# ================================================================== NIP - colunas
def _achar(cols, candidatos, contem=None, evitar=()):
    for c in candidatos:
        if c in cols:
            return c
    if contem:
        for c in cols:
            if all(p in c for p in contem) and not any(e in c for e in evitar):
                return c
    return None


def detectar_colunas_nip(df):
    cols = list(df.columns)
    man = {k: (norm_col(v) if v else None) for k, v in C.COLUNAS_NIP_MANUAL.items()}
    d = {
        "mes": man["mes"] or _achar(cols, ["ANO_MES_ABERTURA", "DT_ABERTURA_DEMANDA", "DT_ABERTURA",
                                           "DATA_ABERTURA"], ["ABERTURA"]),
        "registro": man["registro"] or _achar(cols, ["REGISTRO_OPERADORA", "CD_OPERADORA", "REGISTRO_ANS"], ["REGISTRO"]),
        "cd_municipio": man["cd_municipio"] or _achar(cols, ["CD_MUNICIPIO_BENEFICIARIO", "CD_MUNICIPIO_LOCAL_ATENDIMENTO",
                                                             "CD_MUNICIPIO"], ["MUNICIPIO", "CD"]),
        "nm_municipio": man["nm_municipio"] or _achar(cols, ["MUNICIPIO_BENEFICIARIO", "NM_MUNICIPIO", "MUNICIPIO"],
                                                      ["MUNICIPIO"], ("CD", "COD")),
        "uf": man["uf"] or _achar(cols, ["UF_BENEFICIARIO", "SG_UF", "UF"], ["UF"]),
        "cobertura": man["cobertura"] or _achar(cols, ["TIPOS_COBERTURAS_CONTRATADAS", "COBERTURA"], ["COBERTURA"]),
        "assunto": man["assunto"] or _achar(cols, ["ASSUNTO"], ["ASSUNTO"]),
    }
    usados = {v for v in d.values() if v}
    d["desfecho"] = [c for c in cols if c not in usados and
                     any(p in c for p in ("SITUACAO", "STATUS", "DESFECHO", "FISCALIZ", "AUTO", "ENCAMINH",
                                          "RESULTADO", "FASE", "INFRACAO", "PROCESSO", "CLASSIFICACAO", "NATUREZA"))]
    d["local"] = _achar(cols, ["CD_MUNICIPIO_LOCAL_ATENDIMENTO"], ["LOCAL", "MUNICIPIO"])
    return d


def diagnostico_nip(df, caminho_saida):
    df = df.copy()
    df.columns = [norm_col(c) for c in df.columns]
    d = detectar_colunas_nip(df)
    linhas = ["DIAGNÓSTICO BASE NIP", "=" * 60, f"Linhas: {len(df):,}", "", "Mapeamento automático:"]
    linhas += [f"  {k:<14}: {v}" for k, v in d.items()] + ["", "Colunas e top valores:"]
    for c in df.columns:
        vc = df[c].astype(str).value_counts().head(15)
        linhas.append(f"\n[{c}]  distintos={df[c].nunique():,}")
        linhas += [f"    {str(v)[:90]:<90} {q:>10,}" for v, q in vc.items()]
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text("\n".join(linhas), encoding="utf-8")
    log(f"Diagnóstico salvo em {caminho_saida}")


# ================================================================== NIP - temas
def aplicar_mapa02(assunto: pd.Series, mapa02):
    dp = mapa02.set_index("CHAVE")
    k = chave_assunto(assunto)
    out = pd.DataFrame({"X_Assunto": k.map(dp["X_Assunto"]), "X_Assunto_n2": k.map(dp["X_Assunto_n2"]),
                        "X_Grupo_Grid": k.map(dp["X_Grupo_Grid"])}, index=assunto.index)
    falt = out["X_Assunto"].isna()
    log(f"MAPA 02: {1 - falt.mean():.1%} dos assuntos casaram com o mapa oficial")
    if falt.any():
        ultimo = norm_serie(assunto[falt].fillna("").str.split(">>").str[-1])
        tema = pd.Series(pd.NA, index=ultimo.index, dtype="object")
        for padrao, t in FALLBACK_TEMAS:
            tema[tema.isna() & ultimo.str.contains(padrao, regex=True)] = t
        out.loc[falt, "X_Assunto"] = tema
        out.loc[falt, "X_Assunto_n2"] = tema
        out.loc[falt, "X_Grupo_Grid"] = tema.map(grupo_grid)
        log(f"{falt.sum():,} NIPs fora do MAPA 02 (fallback). Principais:\n"
            + assunto[falt].value_counts().head(10).to_string(), "WARN")
    return out


# ================================================================== NIP - flags candidatas de Pré-Auto
_VAZIOS = {"", "NAN", "NONE", "NULL", "-", "0", "N/A", "NA", "NAO", "NAO SE APLICA", "NAO INFORMADO", "SEM INFORMACAO"}


def flags_pre_auto(df, cols_desfecho):
    """Colunas F_* candidatas a 'transbordo para Pré-Auto'. A calibração escolhe a que reproduz o PPT."""
    F = pd.DataFrame(index=df.index)
    txt_total = pd.Series("", index=df.index)
    for c in cols_desfecho:
        v = norm_serie(df[c])
        txt_total = txt_total + " | " + v
        preenchido = ~v.isin(_VAZIOS)
        F[f"F_{c}_PREENCHIDO"] = preenchido.astype("int8")
        moda = v.mode().iloc[0] if len(v) else ""
        F[f"F_{c}_DIF_MODA"] = (preenchido & (v != moda)).astype("int8")
        F[f"F_{c}_REGEX"] = v.str.contains(C.REGEX_PRE_AUTO + "|" + C.REGEX_AUTO_INFR, regex=True).astype("int8")
        if v.nunique() <= 40:
            for val in v.value_counts().index[:12]:
                if val in _VAZIOS:
                    continue
                F[f"F_{c}__{norm_col(val)[:40]}"] = (v == val).astype("int8")
    F["F_REGEX_GERAL"] = txt_total.str.contains(C.REGEX_PRE_AUTO + "|" + C.REGEX_AUTO_INFR, regex=True).astype("int8")
    return F


# ================================================================== NIP - silver
def tratar_nip(df, mapa01, mapa02):
    """mapa01 pode ser o estendido (Amil + Nicho + outras). Um registro em 2 grupos gera 2 linhas (uma por grupo)."""
    df = df.copy()
    df.columns = [norm_col(c) for c in df.columns]
    d = detectar_colunas_nip(df)
    log(f"Colunas NIP: { {k: v for k, v in d.items()} }")
    if not d["mes"] or not d["registro"] or not d["assunto"]:
        raise KeyError("Não identifiquei mês/registro/assunto na NIP. Preencha COLUNAS_NIP_MANUAL no config.py")

    reg = registro6(df[d["registro"]])
    df = df[reg.isin(set(mapa01["REGISTRO_OPERADORA"]))].reset_index(drop=True)
    if d["cobertura"]:
        cob = norm_serie(df[d["cobertura"]])
        df = df[~(cob.str.contains("ODONTO") & ~cob.str.contains("MEDIC|HOSPITAL|AMBULAT"))].reset_index(drop=True)

    out = pd.DataFrame({
        "MES": para_mes(df[d["mes"]]),
        "REGISTRO_OPERADORA": registro6(df[d["registro"]]),
        "UF_BENEF": norm_serie(df[d["uf"]]) if d["uf"] else "",
        "NM_BENEF": norm_serie(df[d["nm_municipio"]]).str.replace("-", " ", regex=False) if d["nm_municipio"] else "",
        "CD_LOCAL": municipio6(df[d["local"]]) if d["local"] else "",
    }, index=df.index)
    temas = aplicar_mapa02(df[d["assunto"]], mapa02)
    out[["X_Assunto", "X_Assunto_n2", "X_Grupo_Grid"]] = temas.values
    F = flags_pre_auto(df, d["desfecho"])
    out = pd.concat([out, F], axis=1)
    out = out.merge(mapa01[_COLS_MAPA].drop_duplicates(), on="REGISTRO_OPERADORA", how="inner")
    cont = out["X_Grupo_Visao"].value_counts().to_dict()
    log(f"NIP silver: {len(out):,} demandas {cont} | {F.shape[1]} regras candidatas de Pré-Auto")
    return out


# ================================================================== VIDAS
def tratar_vidas(df, mapa01):
    df = df.copy()
    df["MES"] = para_mes(df["ID_CMPT_MOVEL"])
    df["REGISTRO_OPERADORA"] = registro6(df["CD_OPERADORA"])
    df["CD_MUNICIPIO"] = municipio6(df["CD_MUNICIPIO"])
    df["NM_MUNICIPIO"] = norm_serie(df["NM_MUNICIPIO"]).str.replace("-", " ", regex=False)
    df["SG_UF"] = norm_serie(df["SG_UF"])
    df = df.merge(mapa01[_COLS_MAPA].drop_duplicates(), on="REGISTRO_OPERADORA", how="inner")
    return df[["MES", "REGISTRO_OPERADORA", "X_Grupo_Visao", "X_Sigla", "SG_UF", "CD_MUNICIPIO",
               "NM_MUNICIPIO", "QT_BENEFICIARIO_ATIVO"]]


# ================================================================== MAPA 03
def mapear_regiao(uf: pd.Series, nm: pd.Series, mapa03):
    chave = mapa03.drop_duplicates(["SG_UF", "NM_MUNICIPIO"]).set_index(["SG_UF", "NM_MUNICIPIO"])["X_Regiao"]
    idx = pd.MultiIndex.from_arrays([uf.fillna(""), nm.fillna("")])
    reg = pd.Series(chave.reindex(idx).values, index=uf.index)
    reg = reg.fillna("Outros")
    reg[(nm.fillna("") == "")] = "Não informado"
    return reg


def regioes_nip(nip, mapa03, vidas):
    """Cria as duas versões de praça: pelo município do beneficiário e pelo local de atendimento."""
    nip = nip.copy()
    nip["X_Regiao_benef"] = mapear_regiao(nip["UF_BENEF"], nip["NM_BENEF"], mapa03)
    dic = vidas.drop_duplicates("CD_MUNICIPIO").set_index("CD_MUNICIPIO")[["SG_UF", "NM_MUNICIPIO"]]
    uf_l = nip["CD_LOCAL"].map(dic["SG_UF"]).fillna("")
    nm_l = nip["CD_LOCAL"].map(dic["NM_MUNICIPIO"]).fillna("")
    nip["X_Regiao_local"] = mapear_regiao(uf_l, nm_l, mapa03)
    return nip
