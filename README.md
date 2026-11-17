# Panorama Mercadológico de NIP · v3 (mensal + calibrado com o PPT)

Coleta ANS → bronze → silver (mapas) → **calibração com o PPT** → gold (todas as competências) → HTML → SharePoint.

## Rodar (PowerShell, dentro da pasta do projeto)
```powershell
py -m pip install -r requirements.txt
py main.py --cache --sem-publicar     # 1ª vez na v3: reaproveita o que já foi baixado
py main.py                            # rotina mensal: baixa o que mudou na ANS e publica
py main.py --recalibrar               # refaz a calibração com o PPT (se trocar mapas)
```
Ou dois cliques em `executar_panorama.bat`.

## Saídas
- `saida/panorama_mercadologico_nip.html` – painel (seletor de competência no topo; `jul26 · PPT` = mês apresentado)
- `dados/gold/conferencia_ppt.xlsx` – **cada número do PPT x número calculado x diferença**
- `dados/calibracao.json` – regras escolhidas automaticamente (método do IGR, registros por player, regra de Pré-Auto, praças)

## Metodologia (igual ao PPT)
- **IGR de período/grupo**: média simples do IGR publicado (operadora × mês) – o calibrador confirma ou troca para ponderado.
- **Fatias por tema**: IGR do grupo × participação do tema nas NIPs (a soma das fatias = IGR do grupo).
- **Pré-Auto**: % das NIPs com transbordo – a coluna/valor da NIP é escolhida pelo calibrador.
- **Praças**: NIPs da praça ÷ (vidas médias × nº de meses) × 100 mil.

## Mensal
A cada execução entra automaticamente a nova competência assim que IGR e NIP estiverem completos.
`MES_INICIO_PAINEL` (config.py) define a 1ª competência do seletor.
