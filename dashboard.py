# -*- coding: utf-8 -*-
"""
Gera o HTML do Panorama Mercadológico de NIP - linguagem visual do RMR Amil
(sidebar recolhível, tema escuro/claro, aurora, capítulos, degradês 100/65/4).
HTML 100% autocontido (sem CDN). Todas as competências embutidas com seletor mensal.
v4: Sugestão para direcionamento, linha IGR Total, logo ajustado, chips corrigidos.
v5: botão "+ Comparar operadoras" (Hapvida, Unimeds etc.) nos gráficos de evolução e linha do tempo.
"""
import base64
import json
from datetime import datetime

import config as C

TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panorama Mercadológico de NIP · Dados &amp; Insights</title>
<style>
:root{
  --bg:#EEEDFB; --panel:rgba(255,255,255,.86); --panel-s:#FFFFFF; --panel2:#F3F2FD; --text:#15132B; --muted:#6B6890;
  --line:rgba(67,56,232,.12); --brand:#4338E8; --brand2:#766BFF; --lav:#CBC7F7; --teal:#4AC5BB; --gold:#F0B429;
  --pink:#E25DB0; --good:#14A06B; --bad:#E0464E; --warn:#D98A00; --good-bg:rgba(20,160,107,.12); --bad-bg:rgba(224,70,78,.12); --warn-bg:rgba(240,180,41,.16);
  --chart-text:#15132B; --grid:rgba(67,56,232,.09); --tt-bg:#FFFFFF; --tt-text:#15132B; --pt-stroke:#FFFFFF;
  --aur1:rgba(67,56,232,.22); --aur2:rgba(74,197,187,.18); --aur3:rgba(240,180,41,.10);
  --hero:linear-gradient(125deg,#17145E 0%,#2B22B8 55%,#4338E8 100%);
  --side:linear-gradient(180deg,#120F4A 0%,#1B1270 60%,#120F4A 100%);
  --shadow:0 10px 40px rgba(40,30,140,.10); --glow:0 0 0 rgba(0,0,0,0); --fs:1;
  --nicho:#2A2465; --total:#14A06B;
}
[data-theme="dark"]{
  --bg:#0B0A26; --panel:rgba(23,20,63,.72); --panel-s:#17143F; --panel2:rgba(255,255,255,.05); --text:#F7F6FF; --muted:#A9A5D6;
  --line:rgba(255,255,255,.08); --brand:#766BFF; --brand2:#A79FFF; --lav:#B8B4D6; --good:#3DD39A; --bad:#FF6B72; --warn:#F0B429;
  --good-bg:rgba(61,211,154,.14); --bad-bg:rgba(255,107,114,.14); --warn-bg:rgba(240,180,41,.14); --chart-text:#F7F6FF; --grid:rgba(255,255,255,.07);
  --tt-bg:#201B57; --tt-text:#F7F6FF; --pt-stroke:#17143F;
  --aur1:rgba(118,107,255,.28); --aur2:rgba(74,197,187,.16); --aur3:rgba(240,180,41,.07);
  --hero:linear-gradient(125deg,#0E0B3A 0%,#1E1890 55%,#3A2FD0 100%);
  --side:linear-gradient(180deg,#07061F 0%,#120E4A 100%);
  --shadow:0 10px 40px rgba(0,0,0,.45); --glow:0 0 24px rgba(118,107,255,.35);
  --nicho:#E9E7FF; --total:#3DD39A;
}
*{box-sizing:border-box} html{font-size:calc(14px * var(--fs));scroll-behavior:smooth}
body{margin:0;font-family:Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);transition:background .4s,color .4s;min-height:100vh}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background:radial-gradient(900px 600px at 85% -10%,var(--aur1),transparent 60%),radial-gradient(700px 500px at 10% 30%,var(--aur2),transparent 60%),
  radial-gradient(800px 500px at 60% 110%,var(--aur3),transparent 60%)}
button,select,input{font-family:inherit;font-size:inherit;color:inherit}

/* ---------- sidebar ---------- */
#sb{position:fixed;inset:0 auto 0 0;width:68px;background:var(--side);z-index:60;padding:16px 10px;display:flex;flex-direction:column;gap:4px;
  transition:width .3s cubic-bezier(.2,.8,.2,1),box-shadow .3s;overflow:hidden;border-right:1px solid rgba(255,255,255,.06)}
#sb:hover{width:236px;box-shadow:12px 0 40px rgba(5,3,40,.45)}
.logo{display:flex;align-items:center;gap:10px;color:#fff;padding:8px 2px 22px;white-space:nowrap;min-height:52px}
.logo img{width:44px;height:auto;flex:0 0 auto;transition:width .3s cubic-bezier(.2,.8,.2,1)}
#sb:hover .logo img{width:78px}
.logo small{font-size:.58rem;letter-spacing:.14em;line-height:1.15;font-weight:700;opacity:.85}
.nav{display:flex;align-items:center;gap:14px;padding:11px 13px;border-radius:14px;color:#D9D6FF;cursor:pointer;white-space:nowrap;font-weight:700;font-size:.9rem;
  border:0;background:none;text-align:left;width:100%}
.nav svg{flex:0 0 18px;width:18px;height:18px} .nav:hover{background:rgba(255,255,255,.08)}
.nav.on{background:#fff;color:#17145E;box-shadow:0 6px 20px rgba(118,107,255,.45)}
.nav.plus{color:#FFE08A}
.sb-sec{color:#9D97E0;font-size:.62rem;letter-spacing:.14em;font-weight:800;padding:16px 13px 6px;white-space:nowrap;border-top:1px solid rgba(255,255,255,.08);margin-top:10px}
#sb .lbl{opacity:0;transition:opacity .2s} #sb:hover .lbl{opacity:1}

/* ---------- topo ---------- */
main{margin-left:68px;min-height:100vh}
.top{position:sticky;top:0;z-index:40;display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;padding:12px 30px;
  background:color-mix(in srgb,var(--bg) 70%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.top .ttl small{display:block;color:var(--brand2);font-size:.62rem;letter-spacing:.18em;font-weight:800}
.top .ttl b{font-size:1.2rem}
.pill-view{background:var(--lav);color:#17145E;border-radius:999px;padding:3px 10px;font-size:.7rem;font-weight:800;margin-left:8px;vertical-align:middle}
.top-r{margin-left:auto;display:flex;gap:10px;align-items:center}
.upd{font-size:.72rem;color:var(--muted)}
.comp{display:flex;align-items:center;gap:4px;border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:3px}
.comp button{border:0;background:none;width:28px;height:28px;border-radius:50%;cursor:pointer;font-weight:800}
.comp button:hover{background:var(--panel2)}
.comp select{border:0;background:transparent;font-weight:800;padding:4px 6px;cursor:pointer;outline:none}
.comp select option{background:var(--panel-s);color:var(--text)}
.seg{display:flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--panel)}
.seg button{border:0;background:none;padding:6px 11px;cursor:pointer;font-weight:700;font-size:.78rem}
.seg button.on{background:var(--brand);color:#fff;border-radius:999px}
.toggle{width:54px;height:28px;border-radius:999px;background:linear-gradient(90deg,var(--brand),var(--teal));position:relative;cursor:pointer;border:0}
.toggle::after{content:"☀";position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;background:#fff;color:#F0B429;display:grid;place-items:center;font-size:13px;transition:left .25s}
[data-theme="dark"] .toggle::after{content:"☾";left:29px;color:#17145E}

.wrap{padding:22px 30px 50px;max-width:1720px}
.pg{display:none} .pg.on{display:block;animation:fd .45s ease}
@keyframes fd{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ---------- hero ---------- */
.hero{background:var(--hero);border-radius:26px;padding:26px 30px;color:#fff;position:relative;overflow:hidden;box-shadow:var(--shadow)}
.hero::after{content:"";position:absolute;right:-120px;top:-160px;width:520px;height:520px;border-radius:50%;
  background:radial-gradient(circle,rgba(167,159,255,.45),transparent 65%)}
.hero .eyebrow{font-size:.66rem;letter-spacing:.2em;font-weight:800;opacity:.8}
.hero h1{font-size:1.75rem;margin:6px 0 4px;max-width:900px;line-height:1.2;position:relative;z-index:1}
.hero h1 em{font-style:normal;background:linear-gradient(90deg,#fff,#CBC7F7);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{opacity:.85;margin:0 0 18px;max-width:900px;position:relative;z-index:1}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;position:relative;z-index:1}
.kpi{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:14px 16px;backdrop-filter:blur(6px);transition:transform .2s}
.kpi:hover{transform:translateY(-3px)}
.kpi small{font-size:.66rem;letter-spacing:.12em;font-weight:800;opacity:.8;text-transform:uppercase}
.kpi b{display:block;font-size:1.9rem;margin:6px 0 2px;letter-spacing:-.5px}
.kpi em{font-style:normal;font-size:.76rem;opacity:.85}
.chip-d{display:inline-block;border-radius:999px;padding:2px 8px;font-size:.72rem;font-weight:800;margin-left:4px}
.chip-d.good{background:rgba(61,211,154,.22);color:#B7F5DC} .chip-d.bad{background:rgba(255,107,114,.25);color:#FFD0D3}

/* ---------- capítulos ---------- */
.cap{display:flex;align-items:center;gap:16px;margin:34px 0 14px}
.cap .num{font-size:2.6rem;font-weight:800;line-height:1;background:linear-gradient(135deg,var(--brand),var(--teal));-webkit-background-clip:text;background-clip:text;color:transparent}
.cap .num.star{background:linear-gradient(135deg,var(--gold),var(--pink))}
.cap small{display:block;color:var(--brand2);font-size:.62rem;letter-spacing:.2em;font-weight:800}
.cap b{font-size:1.3rem}
.cap .ln{flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent)}

/* ---------- comparar operadoras ---------- */
.selbar{flex-basis:100%;display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:.7rem;color:var(--muted)}
.selbar:empty{display:none}
.selbar .t{font-weight:800;letter-spacing:.12em;font-size:.6rem;margin-right:4px}
.cmpstrip{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;position:relative;z-index:1;align-items:center}
.cmpstrip:empty{display:none}
.cmpstrip .lb{font-size:.6rem;letter-spacing:.16em;font-weight:800;opacity:.75;margin-right:2px}
.hc{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:6px 12px;font-size:.8rem;backdrop-filter:blur(6px)}
.hc i{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--c);margin-right:6px;box-shadow:0 0 8px var(--c)}
.hc em{font-style:normal;font-size:.7rem;padding:2px 7px;border-radius:999px;margin-left:6px;font-weight:800}
.hc em.good{background:rgba(61,211,154,.22);color:#B7F5DC} .hc em.bad{background:rgba(255,107,114,.25);color:#FFD0D3}
.gd th.ex{color:var(--c);max-width:90px;white-space:normal;line-height:1.15}
.gd th.ex::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--c);margin-right:4px}
.pod .c.ex .b{background:linear-gradient(180deg,var(--c),color-mix(in srgb,var(--c) 50%,transparent) 45%,color-mix(in srgb,var(--c) 4%,transparent))}
.pod .c.ex .v{color:var(--c)}
.cmp-wrap{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:62%}
.opchip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:4px 6px 4px 10px;font-size:.74rem;font-weight:700;
  background:color-mix(in srgb,var(--c) 16%,transparent);border:1px solid color-mix(in srgb,var(--c) 45%,transparent)}
.opchip::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--c)}
.opchip button{border:0;background:none;cursor:pointer;font-weight:800;opacity:.7;padding:0 4px;font-size:.9rem}
.opchip button:hover{opacity:1}
.cmp{position:relative}
#cmpBtn{border:1px solid color-mix(in srgb,var(--brand) 45%,transparent);background:var(--panel);border-radius:999px;padding:8px 14px;cursor:pointer;font-weight:800;font-size:.8rem;
  color:var(--brand2);box-shadow:var(--shadow);white-space:nowrap;transition:all .2s}
[data-theme="light"] #cmpBtn{color:var(--brand)}
#cmpBtn:hover,#cmpBtn.open{background:var(--brand);color:#fff;box-shadow:var(--glow)}
#cmpBtn .cnt{display:inline-grid;place-items:center;min-width:18px;height:18px;border-radius:9px;background:var(--gold);color:#17145E;font-size:.66rem;margin-left:4px;padding:0 4px}
.cmp-pan{display:none;position:absolute;right:0;top:calc(100% + 8px);width:380px;z-index:50;background:var(--panel-s);border:1px solid var(--line);border-radius:18px;
  box-shadow:0 20px 50px rgba(0,0,0,.35);padding:12px}
.cmp-pan.open{display:block;animation:fd .2s ease}
.cmp-pan h5{margin:2px 4px 8px;font-size:.84rem} .cmp-pan h5 small{display:block;color:var(--muted);font-weight:500;font-size:.72rem;margin-top:2px}
#cmpQ{width:100%;border:1px solid var(--line);background:var(--panel2);border-radius:12px;padding:9px 12px;outline:none;margin-bottom:8px}
#cmpQ:focus{border-color:var(--brand2)}
#cmpList{max-height:330px;overflow:auto;display:flex;flex-direction:column;gap:2px}
.op{display:grid;grid-template-columns:18px 10px 1fr;gap:10px;align-items:center;padding:7px 8px;border-radius:10px;cursor:pointer;font-size:.8rem}
.op:hover{background:var(--panel2)}
.op input{accent-color:var(--brand);width:16px;height:16px;cursor:pointer;margin:0}
.op .dt{width:10px;height:10px;border-radius:50%;border:1px solid var(--line)}
.op .nm{font-weight:700;line-height:1.25} .op .nm small{display:block;color:var(--muted);font-weight:500;font-size:.7rem}
.cmp-pan small{letter-spacing:normal!important;font-weight:500!important;color:var(--muted)!important;font-size:.7rem!important}
.cmp-ft{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);margin-top:8px;padding-top:8px;font-size:.7rem;color:var(--muted)}
.cmp-ft button{border:0;background:var(--panel2);border-radius:999px;padding:5px 12px;cursor:pointer;font-weight:800;font-size:.72rem}

.grid{display:grid;gap:16px}
.g2{grid-template-columns:1.1fr 1fr} .gp{grid-template-columns:1fr 300px} .g11{grid-template-columns:1fr 1fr} .g3{grid-template-columns:repeat(3,1fr)}
.gs{grid-template-columns:1.35fr 1fr}
.card{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:18px 20px;box-shadow:var(--shadow);backdrop-filter:blur(10px);min-width:0;transition:box-shadow .3s}
.card:hover{box-shadow:var(--shadow),var(--glow)}
.card h3{margin:0;font-size:1rem} .card h3 i{font-style:normal;color:var(--muted);font-weight:500;font-size:.78rem;margin-left:6px}
.ds{color:var(--muted);font-size:.78rem;margin:4px 0 10px}
.ins{border-radius:14px;padding:10px 14px;font-size:.84rem;margin-top:10px;background:var(--panel2);border-left:4px solid var(--brand);line-height:1.5}
.ins b{color:var(--brand2)} [data-theme="light"] .ins b{color:var(--brand)}
.lg{display:flex;gap:14px;flex-wrap:wrap;font-size:.76rem;color:var(--muted);margin-bottom:4px}
.lg span:before{content:"";display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:6px;vertical-align:middle;background:var(--c)}
.lg span.bar:before{height:10px;width:10px;border-radius:3px}
.lg span.dash:before{background:repeating-linear-gradient(90deg,var(--c) 0 5px,transparent 5px 8px)}
.ch{width:100%;position:relative}
.up{color:var(--bad)!important} .dn{color:var(--good)!important}

/* tabela grid s11 */
table.gd{width:100%;border-collapse:separate;border-spacing:0;font-size:.86rem}
.gd th{padding:10px 8px;font-weight:800;font-size:.72rem;letter-spacing:.06em;color:var(--muted);border-bottom:1px solid var(--line);text-align:center}
.gd th:first-child{text-align:left}
.gd th.am{color:var(--brand2)}
.gd td{padding:9px 8px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}
.gd td:first-child{text-align:left;font-weight:700;white-space:normal}
.gd td.am{font-weight:800;font-size:1rem;color:var(--brand2);background:color-mix(in srgb,var(--brand) 9%,transparent)}
.gd td.ni{font-weight:800}
.gd tr:hover td{background:var(--panel2)}
.gd tr.tot td{font-weight:800;border-top:2px solid var(--brand);border-bottom:0}
.mdl{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;font-size:.6rem;font-weight:800;color:#fff;margin-right:5px;vertical-align:middle;
  box-shadow:0 2px 6px rgba(0,0,0,.25),inset 0 -2px 3px rgba(0,0,0,.18)}
.mdl.m1{background:radial-gradient(circle at 35% 30%,#FDE68A,#D97706)} .mdl.m2{background:radial-gradient(circle at 35% 30%,#F8FAFC,#94A3B8);color:#334155}
.mdl.m3{background:radial-gradient(circle at 35% 30%,#FDBA74,#B45309)} .mdl.m4{background:var(--panel2);color:var(--muted);box-shadow:none}

/* pódio */
.pod{display:flex;align-items:flex-end;justify-content:center;gap:10px;height:250px;padding-top:12px}
.pod .c{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;max-width:84px}
.pod .v{font-weight:800;font-size:1.05rem;margin-bottom:6px}
.pod .b{width:100%;border-radius:14px 14px 6px 6px;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;
  background:linear-gradient(180deg,color-mix(in srgb,var(--lav) 100%,transparent),color-mix(in srgb,var(--lav) 65%,transparent) 45%,color-mix(in srgb,var(--lav) 4%,transparent));transition:height .7s cubic-bezier(.2,.8,.2,1)}
.pod .c.am .b{background:linear-gradient(180deg,var(--brand),color-mix(in srgb,var(--brand) 65%,transparent) 45%,color-mix(in srgb,var(--brand) 4%,transparent));box-shadow:var(--glow)}
.pod .c.am .v{color:var(--brand2)}
.pod .n{font-size:.74rem;color:var(--muted);margin-top:8px;text-align:center;line-height:1.2;min-height:30px}
.pod .b .mdl{width:30px;height:30px;font-size:.72rem;margin:0}
.callouts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:12px}
.co{border-radius:14px;padding:10px 12px;font-size:.8rem;background:var(--bad-bg);border:1px solid color-mix(in srgb,var(--bad) 35%,transparent)}
.co b{color:var(--bad)} .co .big{font-size:1.4rem;font-weight:800;color:var(--bad);display:block}

/* chips praças */
.temas{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 8px}
.chip{border:1px solid var(--line);background:var(--panel2);border-radius:999px;padding:6px 12px;font-size:.78rem;cursor:pointer;font-weight:700;transition:all .2s}
.chip:hover{border-color:var(--brand2)}
.chip.on{background:var(--brand);color:#fff;border-color:var(--brand);box-shadow:var(--glow)}
.chip.dev::after{content:" ▲";color:var(--bad);font-size:.6rem} .chip.on.dev::after{color:#FFD0D3}
details{margin-top:12px} summary{cursor:pointer;color:var(--brand2);font-size:.82rem;font-weight:800}
.tb{max-height:380px;overflow:auto;margin-top:8px;border:1px solid var(--line);border-radius:14px}
.tb table{width:100%;border-collapse:collapse;font-size:.8rem}
.tb th{position:sticky;top:0;background:var(--panel-s);padding:8px;text-align:right;font-size:.7rem;color:var(--muted);letter-spacing:.05em;z-index:1}
.tb th:first-child,.tb td:first-child{text-align:left}
.tb td{padding:7px 8px;border-top:1px solid var(--line);text-align:right}
.tb td.l,.tb th.l{text-align:left}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.72rem;font-weight:800;white-space:nowrap}
.tag.good{background:var(--good-bg);color:var(--good)} .tag.bad{background:var(--bad-bg);color:var(--bad)} .tag.warn{background:var(--warn-bg);color:var(--warn)}
.tag.info{background:color-mix(in srgb,var(--brand) 14%,transparent);color:var(--brand2)}

/* ---------- SUGESTÃO PARA DIRECIONAMENTO ---------- */
.sug-hero{position:relative;overflow:hidden;border-radius:26px;padding:22px 24px;border:1px solid color-mix(in srgb,var(--gold) 35%,transparent);
  background:linear-gradient(120deg,color-mix(in srgb,var(--gold) 14%,var(--panel)) 0%,var(--panel) 40%,color-mix(in srgb,var(--brand) 10%,var(--panel)) 100%);box-shadow:var(--shadow)}
.sug-hero .resumo{font-size:1.02rem;line-height:1.55;max-width:1200px}
.sug-hero .resumo b{color:var(--brand2)} [data-theme="light"] .sug-hero .resumo b{color:var(--brand)}
.front{position:relative;border-radius:20px;padding:18px 18px 16px;background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);overflow:hidden;transition:transform .25s}
.front:hover{transform:translateY(-4px)}
.front::before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:linear-gradient(90deg,var(--bad),var(--gold))}
.front .rk{position:absolute;right:14px;top:10px;font-size:2.8rem;font-weight:800;opacity:.10}
.front .tp{font-size:.62rem;letter-spacing:.16em;font-weight:800;color:var(--muted)}
.front h4{margin:6px 0 2px;font-size:1.08rem;line-height:1.25}
.front .where{color:var(--muted);font-size:.8rem}
.front .nums{display:flex;gap:10px;margin:12px 0 10px;flex-wrap:wrap}
.front .nums div{flex:1;min-width:80px;background:var(--panel2);border-radius:12px;padding:8px 10px}
.front .nums small{display:block;font-size:.6rem;letter-spacing:.1em;color:var(--muted);font-weight:800}
.front .nums b{font-size:1.15rem}
.front .acao{font-size:.82rem;line-height:1.5;border-top:1px dashed var(--line);padding-top:10px}
.front .acao b{color:var(--brand2)} [data-theme="light"] .front .acao b{color:var(--brand)}
.front .area{margin-top:8px}
.rank{display:flex;flex-direction:column;gap:8px}
.rk-row{display:grid;grid-template-columns:22px 1fr 150px 70px;gap:10px;align-items:center;font-size:.82rem;padding:6px 8px;border-radius:12px;cursor:pointer;transition:background .2s}
.rk-row:hover{background:var(--panel2)}
.rk-row input{accent-color:var(--brand);width:16px;height:16px;cursor:pointer}
.rk-row .nm b{display:block;font-size:.84rem} .rk-row .nm span{color:var(--muted);font-size:.74rem}
.rk-bar{height:10px;border-radius:99px;background:var(--panel2);overflow:hidden}
.rk-bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--gold),var(--bad))}
.rk-row .vl{text-align:right;font-weight:800;color:var(--bad)}
.sim{display:flex;flex-direction:column;gap:12px}
.sim .big{display:flex;align-items:center;gap:14px;justify-content:center;padding:10px 0}
.sim .big div{text-align:center} .sim .big small{display:block;font-size:.62rem;letter-spacing:.14em;color:var(--muted);font-weight:800}
.sim .big b{font-size:2.3rem;letter-spacing:-1px} .sim .big .arrow{font-size:1.6rem;color:var(--muted)}
.sim .big .proj b{background:linear-gradient(135deg,var(--good),var(--teal));-webkit-background-clip:text;background-clip:text;color:transparent}
.gauge{height:14px;border-radius:99px;background:var(--panel2);position:relative;overflow:visible;margin:6px 0 18px}
.gauge .f{position:absolute;left:0;top:0;bottom:0;border-radius:99px;background:linear-gradient(90deg,var(--brand),var(--teal));transition:width .6s cubic-bezier(.2,.8,.2,1)}
.gauge .mk{position:absolute;top:-6px;bottom:-6px;width:3px;border-radius:2px;background:var(--text)}
.gauge .mk span{position:absolute;top:24px;left:50%;transform:translateX(-50%);font-size:.66rem;white-space:nowrap;color:var(--muted);font-weight:700}
.alertas{display:flex;flex-direction:column;gap:8px}
.al{display:flex;gap:10px;align-items:flex-start;border-radius:14px;padding:10px 12px;font-size:.8rem;line-height:1.45;background:var(--panel2)}
.al .ic{flex:0 0 26px;height:26px;border-radius:8px;display:grid;place-items:center;font-weight:800;font-size:.8rem}
.al.bad .ic{background:var(--bad-bg);color:var(--bad)} .al.warn .ic{background:var(--warn-bg);color:var(--warn)} .al.good .ic{background:var(--good-bg);color:var(--good)}
.al b{color:var(--text)}

/* metodologia */
.met{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.met .card p{color:var(--muted);font-size:.84rem;line-height:1.55;margin:.4rem 0 0}

#tip{position:fixed;pointer-events:none;background:var(--tt-bg);color:var(--tt-text);font-size:.78rem;padding:10px 12px;border-radius:12px;
  z-index:99;display:none;box-shadow:0 12px 30px rgba(0,0,0,.3);max-width:320px;line-height:1.55;border:1px solid var(--line)}
#tip .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
footer{color:var(--muted);font-size:.72rem;padding:0 30px 30px;max-width:1720px;line-height:1.6}
footer a{color:var(--brand2)}
@media (max-width:1200px){.g2,.gp,.g11,.g3,.gs{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.upd{display:none}.cmp-wrap{max-width:100%}}
</style>
</head>
<body>
<nav id="sb">
  <div class="logo"><img src="data:image/png;base64,__LOGO__" alt="amil"><small class="lbl">DADOS &amp;<br>INSIGHTS</small></div>
  <button class="nav on" data-pg="pg1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12l9-8 9 8M5 10v10h14V10"/></svg><span class="lbl">Panorama geral</span></button>
  <button class="nav plus" data-pg="pg1" data-go="sug"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.9 6.3 6.9.7-5.2 4.7 1.5 6.8L12 17l-6.1 3.5 1.5-6.8L2.2 9l6.9-.7z"/></svg><span class="lbl">Sugestão p/ direcionamento</span></button>
  <button class="nav" data-pg="pg2"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.3-7-11a7 7 0 0114 0c0 4.7-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg><span class="lbl">Visão praças</span></button>
  <button class="nav" data-pg="pg3"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg><span class="lbl">Linha do tempo</span></button>
  <div class="sb-sec lbl">FERRAMENTAS</div>
  <button class="nav" data-pg="pg4"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20V3H6.5A2.5 2.5 0 004 5.5z"/></svg><span class="lbl">Metodologia</span></button>
</nav>

<main>
<div class="top">
  <div class="ttl"><small>DADOS &amp; INSIGHTS</small><b>Panorama Mercadológico de NIP</b><span class="pill-view" id="pv">Panorama geral</span></div>
  <div class="top-r">
    <span class="upd" id="upd"></span>
    <div class="cmp" id="cmp">
      <button id="cmpBtn" type="button"></button>
      <div class="cmp-pan" id="cmpPan">
        <h5>Comparar com outras operadoras de saúde<small>Marque para incluir em todos os gráficos do painel</small></h5>
        <input id="cmpQ" type="text" placeholder="Buscar operadora (ex.: Hapvida, Unimed...)" autocomplete="off">
        <div id="cmpList"></div>
        <div class="cmp-ft"><span id="cmpInfo"></span><button id="cmpClr" type="button">Limpar seleção</button></div>
      </div>
    </div>
    <div class="comp" title="Competência de referência"><button id="prev">‹</button><select id="sel"></select><button id="next">›</button></div>
    <div class="seg"><button id="fsm">A-</button><button id="fsa" class="on">Auto</button><button id="fsp">A+</button></div>
    <button class="toggle" id="tg" title="Tema claro/escuro"></button>
  </div>
  <div class="selbar" id="cmpChips"></div>
</div>

<div class="wrap">
<!-- =================== PANORAMA =================== -->
<section class="pg on" id="pg1">
  <div class="hero">
    <div class="eyebrow" id="hEy"></div>
    <h1 id="hTi"></h1>
    <p id="hSu"></p>
    <div class="kpis" id="kpis"></div>
    <div class="cmpstrip" id="hCmp"></div>
  </div>

  <div class="cap"><span class="num">01</span><div><small>CAPÍTULO 1</small><b>Posicionamento da Amil frente ao nicho</b></div><span class="ln"></span>
  </div>
  <div class="grid g2">
    <div class="grid">
      <div class="card"><h3>IGR Amil vs Nicho <i>Evolução · consolidado</i></h3>
        <div class="ds">Índice Geral de Reclamações ANS (reclamações por 100 mil beneficiários) · menor é melhor</div>
        <div class="lg" id="lg6"></div><div class="ch" id="c6" data-h="260"></div><div class="ins" id="i6"></div></div>
      <div class="card"><h3>IGR Amil vs Nicho <i>Evolução · por empresa do nicho</i></h3>
        <div class="lg" id="lg7"></div><div class="ch" id="c7" data-h="260"></div><div class="ins" id="i7"></div></div>
    </div>
    <div class="card"><h3>Maturidade da Amil em relação ao Nicho por Tema <i id="t11"></i></h3>
      <div class="ds">IGR 12 meses por grupo de temas · medalhas = posição entre as operadoras exibidas (menor é melhor) · Nicho APSB = Amil + P + S + B</div>
      <div id="g11"></div><div class="ins" id="i11"></div></div>
  </div>

  <div class="cap"><span class="num">02</span><div><small>CAPÍTULO 2</small><b>Fatias do IGR por grupo de temas</b></div><span class="ln"></span></div>
  <div class="grid gp">
    <div class="card"><h3>Pareto por tema · IGR <i id="t9"></i></h3>
      <div class="ds">Barras: Amil + Nicho · Linhas: Amil e Nicho · a soma das fatias é o IGR de cada grupo</div>
      <div class="lg" id="lg9"></div><div class="ch" id="c9" data-h="320"></div><div class="callouts" id="co9"></div></div>
    <div class="card"><h3>Pódio IGR <i id="tp9"></i></h3><div class="ds">Quanto menor, melhor</div><div class="pod" id="p9"></div><div class="ins" id="ip9"></div></div>
  </div>

  <div class="cap"><span class="num">03</span><div><small>CAPÍTULO 3</small><b>Transbordo para Pré-Auto de Infração</b></div><span class="ln"></span></div>
  <div class="grid gp">
    <div class="card"><h3>Pareto por tema · Auto de Infração <i id="t10"></i></h3>
      <div class="ds">Barras: IGR do tema (Amil + Nicho) · Linhas: % das NIPs que transbordaram para Pré-Auto</div>
      <div class="lg" id="lg10"></div><div class="ch" id="c10" data-h="320"></div><div class="ins" id="i10"></div></div>
    <div class="card"><h3>Pódio % Pré-Auto</h3><div class="ds">Participação de NIPs com transbordo · menor é melhor</div><div class="pod" id="p10"></div></div>
  </div>

  <!-- ===== PLUS: SUGESTÃO PARA DIRECIONAMENTO ===== -->
  <div class="cap" id="sug"><span class="num star">✦</span><div><small>PLUS · INTELIGÊNCIA DE AÇÃO</small><b>Sugestão para direcionamento · onde atuar primeiro</b></div><span class="ln"></span></div>
  <div class="sug-hero"><div class="resumo" id="sgRes"></div></div>
  <div class="grid g3" style="margin-top:16px" id="sgFront"></div>
  <div class="grid gs" style="margin-top:16px">
    <div class="card"><h3>Ranking de oportunidades <i>praça × tema</i></h3>
      <div class="ds">NIPs evitáveis = NIPs da Amil acima do que teria com a taxa do nicho na mesma praça e tema · marque as frentes para simular o impacto</div>
      <div class="rank" id="sgRank"></div></div>
    <div class="grid">
      <div class="card"><h3>Simulador de impacto no IGR</h3>
        <div class="ds">Se a Amil igualar o nicho nas frentes marcadas ao lado</div>
        <div class="sim" id="sgSim"></div></div>
      <div class="card"><h3>Alertas e pontos de atenção</h3><div class="ds">Tendência, risco regulatório e fortalezas</div><div class="alertas" id="sgAl"></div></div>
    </div>
  </div>
  <div class="card" style="margin-top:16px"><h3>Plano de ação completo <i>temas · praças · praça × tema</i></h3>
    <div class="ds">Priorização automática por volume de NIPs evitáveis · Alta ≥ 50% da maior oportunidade · Média ≥ 20%</div>
    <div class="tb" id="sgTb" style="max-height:460px"></div></div>
</section>

<!-- =================== PRAÇAS =================== -->
<section class="pg" id="pg2">
  <div class="cap" style="margin-top:6px"><span class="num">04</span><div><small>CAPÍTULO 4</small><b>Clusters de Regiões de Saúde personalizados para a Amil</b></div><span class="ln"></span></div>
  <div class="card"><h3>IGR por Região de Saúde · Visão total <i id="t8"></i></h3>
    <div class="ds">Ordenado por vidas Amil (mil) · moldura vermelha = praças onde a Amil está acima do nicho</div>
    <div class="lg" id="lg8"></div><div class="ch" id="c8" data-h="380"></div><div class="ins" id="i8"></div>
    <details><summary>Ver tabela das praças</summary><div class="tb" id="tb8"></div></details></div>
  <div class="card" style="margin-top:16px"><h3>IGR por Região de Saúde · Visão por tema <i id="t12"></i></h3>
    <div class="ds">Selecione o tema (▲ = Amil acima do nicho). Padrão: primeiro em representatividade com desvio.</div>
    <div class="temas" id="chips"></div>
    <div class="lg" id="lg12"></div><div class="ch" id="c12" data-h="400"></div><div class="ins" id="i12"></div>
    <details><summary>Ver tabela das praças</summary><div class="tb" id="tb12"></div></details></div>
</section>

<!-- =================== LINHA DO TEMPO =================== -->
<section class="pg" id="pg3">
  <div class="cap" style="margin-top:6px"><span class="num">05</span><div><small>CAPÍTULO 5</small><b>Linha do tempo mensal · todos os meses disponíveis</b></div><span class="ln"></span></div>
  <div class="card"><h3>IGR mensal · Amil vs Nicho vs IGR Total</h3><div class="ds">Todas as competências publicadas pela ANS desde jan/25 · área = distância para o nicho · tracejado verde = IGR total (Amil + Nicho) · operadoras extras conforme o botão "Comparar operadoras"</div>
    <div class="lg" id="lgT1"></div><div class="ch" id="cT1" data-h="320"></div><div class="ins" id="iT1"></div></div>
  <div class="card" style="margin-top:16px"><h3>IGR mensal · por empresa</h3><div class="ds">Tracejado verde = IGR total do mercado comparado (Amil + Nicho)</div>
    <div class="lg" id="lgT2"></div><div class="ch" id="cT2" data-h="320"></div></div>
  <div class="card" style="margin-top:16px"><h3>Mapa de calor mensal</h3><div class="ds">Verde = melhor que o IGR total (Amil + Nicho) no mês · vermelho = acima</div><div class="tb" id="tbT" style="max-height:none"></div></div>
</section>

<!-- =================== METODOLOGIA =================== -->
<section class="pg" id="pg4">
  <div class="cap" style="margin-top:6px"><span class="num">i</span><div><small>FERRAMENTAS</small><b>Metodologia e fontes</b></div><span class="ln"></span></div>
  <div class="met" id="met"></div>
</section>
</div>
<footer id="foot"></footer>
</main>
<div id="tip"></div>

<script>
const D = __DADOS__;
const ALIAS = {"Autoriz. Regulação":"Cobert. Regulação","Prazo Máximos":"Cobert. Prazo"};
const nomeT = t => ALIAS[t] || t;
const f1 = v => v==null||isNaN(v) ? "–" : v.toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1});
const f2 = v => v==null||isNaN(v) ? "–" : v.toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
const fp = v => v==null||isNaN(v) ? "–" : (v*100).toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1})+"%";
const fi = v => v==null||isNaN(v) ? "–" : Math.round(v).toLocaleString("pt-BR");
const $ = id => document.getElementById(id);
const esc = t => String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;");
const MED = [1,2,3,4].map(k=>`<span class="mdl m${k}">${k}º</span>`);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function COR(){ return {amil:css("--brand"), amil2:css("--brand2"), nicho:css("--nicho"), teal:css("--teal"), gold:css("--gold"), pink:css("--pink"),
  lav:css("--lav"), good:css("--good"), bad:css("--bad"), txt:css("--chart-text"), muted:css("--muted"), grid:css("--grid"), stroke:css("--pt-stroke"),
  total:css("--total"), B:css("--teal"), P:css("--gold"), S:css("--pink"), AMIL:css("--brand")}; }

/* ===================== outras operadoras (comparação) ===================== */
const OUT = D.outras || null;
const PAL = ["#F97316","#06B6D4","#84CC16","#EF4444","#A855F7","#0EA5E9","#EAB308","#10B981","#F43F5E","#8B5CF6"];
let EXTRA = [];
try{ EXTRA = JSON.parse(localStorage.getItem("pm_ops")||"[]"); }catch(e){}
if(OUT) EXTRA = EXTRA.filter(id=>OUT.lista.some(o=>o.id===id)); else EXTRA=[];
const corOp = id => PAL[Math.max(EXTRA.indexOf(id),0)%PAL.length];
const nomeOp = id => (OUT && (OUT.lista.find(o=>o.id===id)||{}).nome) || id;
function salvarOps(){ try{ localStorage.setItem("pm_ops",JSON.stringify(EXTRA)); }catch(e){} }
const OD = id => (OUT && OUT.por_ref && OUT.por_ref[REF] && OUT.por_ref[REF][id]) || null;
const curto = n => { n=String(n); if(n.length<=18) return n; const w=n.split(" "); return w.slice(0,2).join(" "); };
const med = k => k<3 ? MED[k] : `<span class="mdl m4">${k+1}º</span>`;
function igrOp(id,nome,tema){ const p=OD(id)?.pracas?.[nome]; if(!p||!p.den) return null;
  const q=tema?(p.nips[tema]||0):Object.values(p.nips).reduce((a,b)=>a+b,0); return q/p.den*1e5; }
function linhasExtra(fonte){ return EXTRA.map(id=>({name:nomeOp(id),values:fonte(id)||[],color:corOp(id),width:2.2,dash:"3 4",labels:false,r:3})); }
function legExtra(){ return EXTRA.map(id=>({n:nomeOp(id),c:corOp(id),dash:1})); }

/* ===================== motor SVG ===================== */
const tip=$("tip"), CH={};
function showTip(e,h){ tip.innerHTML=h; tip.style.display="block"; tip.style.left=Math.min(e.clientX+16,innerWidth-330)+"px"; tip.style.top=(e.clientY+16)+"px"; }
function hideTip(){ tip.style.display="none"; }
function legend(id,items){ $(id).innerHTML=items.map(i=>`<span class="${i.bar?'bar':''} ${i.dash?'dash':''}" style="--c:${i.c}">${esc(i.n)}</span>`).join(""); }
function nice(v){ if(v<=0) return 1; const p=Math.pow(10,Math.floor(Math.log10(v))), n=v/p; return (n<=1?1:n<=2?2:n<=2.5?2.5:n<=5?5:10)*p; }
function wrap(t,bw){ const max=Math.max(6,Math.floor(bw/6.4)); const out=[]; let cur="";
  String(t).split(/\s+/).forEach(p=>{ if((cur+" "+p).trim().length>max&&cur){out.push(cur);cur=p;} else cur=(cur+" "+p).trim(); }); if(cur) out.push(cur); return out; }
function chart(id,cfg){ CH[id]=cfg; draw(id); }
function draw(id){
  const el=$(id), cfg=CH[id]; if(!el||!el.offsetParent) return; const K=COR();
  const W=el.clientWidth, H=+el.dataset.h||280, n=cfg.labels.length;
  const top=cfg.topRow?42:26, bl=cfg.labelLines||3, bot=18+bl*13+(cfg.bottomRow?24:0), L=46, R=cfg.right?46:16;
  const pw=W-L-R, ph=H-top-bot, bw=pw/n;
  const all=[]; (cfg.bars||[]).forEach(b=>all.push(...b.values)); (cfg.lines||[]).filter(l=>l.axis!=="r").forEach(l=>all.push(...l.values)); if(cfg.ref) all.push(cfg.ref.value);
  const vals=all.filter(v=>v!=null); if(!vals.length){ el.innerHTML=`<div class="ds">Sem dados para o período.</div>`; return; }
  const bar=cfg.bars&&cfg.bars.length; let mn=bar?0:Math.max(0,Math.min(...vals)*.85), mx=Math.max(...vals)*1.12;
  const st=nice((mx-mn)/4); mn=Math.floor(mn/st)*st; mx=Math.ceil(mx/st)*st; if(mx<=mn) mx=mn+st; const nT=Math.round((mx-mn)/st);
  const y=v=>top+ph-(v-mn)/(mx-mn)*ph, cx=i=>L+bw*i+bw/2;
  let yr=null; if(cfg.right){ const rv=[]; cfg.lines.filter(l=>l.axis==="r").forEach(l=>rv.push(...l.values.filter(v=>v!=null))); const rm=Math.max(...rv,0.0001)*1.3; yr=v=>top+ph*.94-(v/rm)*ph*.86; }
  let s=`<svg width="${W}" height="${H}" style="display:block;overflow:visible"><defs>
    <linearGradient id="gb${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${K.lav}" stop-opacity="1"/><stop offset=".45" stop-color="${K.lav}" stop-opacity=".65"/><stop offset="1" stop-color="${K.lav}" stop-opacity=".04"/></linearGradient>
    <linearGradient id="ga${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${K.amil}" stop-opacity=".35"/><stop offset=".55" stop-color="${K.amil}" stop-opacity=".12"/><stop offset="1" stop-color="${K.amil}" stop-opacity=".02"/></linearGradient>
    <filter id="gl${id}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`;
  for(let k=0;k<=nT;k++){ const v=mn+st*k, yy=y(v); s+=`<line x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}" stroke="${K.grid}"/><text x="${L-8}" y="${yy+4}" font-size="10" fill="${K.muted}" text-anchor="end">${(Math.round(v*10)/10).toLocaleString("pt-BR")}</text>`; }
  if(cfg.highlight!=null){ const i=cfg.highlight; s+=`<rect x="${L+bw*i+3}" y="${top-8}" width="${bw-6}" height="${ph+12}" fill="${K.amil}" fill-opacity=".08" stroke="${K.amil2}" stroke-dasharray="5 4" rx="10"/>`; }
  (cfg.alerts||[]).forEach(i=>{ s+=`<rect x="${L+bw*i+4}" y="${top-6}" width="${bw-8}" height="${ph+8}" fill="${K.bad}" fill-opacity=".06" stroke="${K.bad}" stroke-dasharray="4 3" rx="8"/>`; });
  (cfg.bars||[]).forEach(b=>b.values.forEach((v,i)=>{ if(v==null) return; const w=Math.min(bw*.68,64), yy=y(v);
     s+=`<rect x="${cx(i)-w/2}" y="${yy}" width="${w}" height="${top+ph-yy}" rx="8" fill="url(#gb${id})"/>`;
     s+=`<text x="${cx(i)}" y="${top+ph-7}" font-size="10.5" font-weight="700" fill="${K.txt}" text-anchor="middle" opacity=".85">${f1(v)}</text>`; }));
  if(cfg.fillBetween){ const [a,b]=cfg.fillBetween.map(k=>cfg.lines[k].values); const p1=[],p2=[];
     a.forEach((v,i)=>{ if(v!=null&&b[i]!=null){ p1.push(`${cx(i)},${y(v)}`); p2.unshift(`${cx(i)},${y(b[i])}`);} }); s+=`<polygon points="${p1.concat(p2).join(" ")}" fill="${K.amil}" fill-opacity=".10"/>`; }
  if(cfg.areaUnder!=null){ const l=cfg.lines[cfg.areaUnder]; const pts=l.values.map((v,i)=>v==null?null:[cx(i),y(v)]).filter(Boolean);
     if(pts.length>1) s+=`<path d="M${pts[0][0]},${top+ph} L${pts.map(p=>p.join(",")).join(" L")} L${pts[pts.length-1][0]},${top+ph} Z" fill="url(#ga${id})"/>`; }
  if(cfg.ref){ const yy=y(cfg.ref.value); s+=`<line x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}" stroke="${K.good}" stroke-width="2" stroke-dasharray="7 5"/>
     <text x="${W-R}" y="${yy-7}" font-size="11" font-weight="800" fill="${K.good}" text-anchor="end" paint-order="stroke" stroke="${K.stroke}" stroke-width="4">${cfg.ref.label} ${f1(cfg.ref.value)}</text>`; }
  (cfg.lines||[]).forEach((l,li)=>{ const Y=l.axis==="r"?yr:y; const pts=[]; l.values.forEach((v,i)=>{ if(v!=null) pts.push([cx(i),Y(v),v,i]); });
    if(pts.length>1) s+=`<path d="M${pts.map(p=>p[0]+","+p[1]).join(" L")}" fill="none" stroke="${l.color}" stroke-width="${l.width||2.4}" ${l.dash?`stroke-dasharray="${l.dash}"`:""} stroke-linejoin="round" stroke-linecap="round" ${l.glow?`filter="url(#gl${id})"`:""}/>`;
    if(l.dots===false) return;
    pts.forEach(p=>{ s+=`<circle cx="${p[0]}" cy="${p[1]}" r="${l.r||3.8}" fill="${K.stroke}" stroke="${l.color}" stroke-width="2.4"/>`;
      if(l.labels!==false){ let up=true; if(l.axis==="r") up=li%2===1; else { const o=cfg.lines.filter(x=>x!==l&&x.axis!=="r"&&x.labels!==false).map(x=>x.values[p[3]]).filter(v=>v!=null); up=o.every(v=>p[2]>=v); }
        s+=`<text x="${p[0]}" y="${p[1]+(up?-10:18)}" font-size="${l.fs||10.5}" font-weight="800" fill="${l.color}" text-anchor="middle" paint-order="stroke" stroke="${K.stroke}" stroke-width="3.5">${(l.fmt||f1)(p[2])}</text>`; } }); });
  cfg.labels.forEach((t,i)=>wrap(t,bw).slice(0,bl).forEach((pt,k)=>{ s+=`<text x="${cx(i)}" y="${top+ph+17+k*12}" font-size="10" fill="${K.muted}" text-anchor="middle" ${i===cfg.highlight?`font-weight="800" fill="${K.amil2}"`:""}>${esc(pt)}</text>`; }));
  if(cfg.topRow){ s+=`<text x="${L-8}" y="13" font-size="9.5" fill="${K.muted}" text-anchor="end">Vidas mil</text>`; cfg.topRow.forEach((t,i)=>{ s+=`<text x="${cx(i)}" y="13" font-size="10" font-weight="700" fill="${K.muted}" text-anchor="middle">${t}</text>`; }); }
  if(cfg.bottomRow) cfg.bottomRow.forEach((o,i)=>{ if(o) s+=`<text x="${cx(i)}" y="${H-5}" font-size="10.5" font-weight="800" fill="${o.c}" text-anchor="middle">${o.t}</text>`; });
  cfg.labels.forEach((t,i)=>{ s+=`<rect class="hv" data-i="${i}" x="${L+bw*i}" y="${top-8}" width="${bw}" height="${ph+12}" fill="transparent"/>`; });
  el.innerHTML=s+"</svg>";
  el.querySelectorAll(".hv").forEach(r=>{ r.onmousemove=e=>{ const i=+r.dataset.i; let h=`<b>${esc(cfg.labels[i])}</b>`+(cfg.topRow?` <span style="opacity:.7">· ${cfg.topRow[i]} mil vidas Amil</span>`:"")+"<br>";
      (cfg.bars||[]).forEach(b=>h+=`<span class="dot" style="background:${K.lav}"></span>${b.name}: <b>${f1(b.values[i])}</b><br>`);
      (cfg.lines||[]).slice().sort((x,z)=>(x.values[i]??1e9)-(z.values[i]??1e9)).forEach(l=>h+=`<span class="dot" style="background:${l.color}"></span>${esc(l.name)}: <b>${(l.fmt||f1)(l.values[i])}</b><br>`);
      if(cfg.extra) h+=cfg.extra(i); showTip(e,h); r.setAttribute("fill",K.amil); r.setAttribute("fill-opacity",".06"); };
    r.onmouseleave=()=>{ hideTip(); r.setAttribute("fill","transparent"); }; });
}
let rz; addEventListener("resize",()=>{ clearTimeout(rz); rz=setTimeout(()=>Object.keys(CH).forEach(draw),150); });
function podio(id,itens,fmt){ const ord=[...itens].filter(i=>i.valor!=null).sort((a,b)=>a.valor-b.valor); const N=Math.max(ord.length-1,1); const pos=new Map(ord.map((x,k)=>[x.nome,k]));
  $(id).innerHTML=itens.map(it=>{ const k=pos.get(it.nome); const am=/^amil$/i.test(it.nome);
    return `<div class="c ${am?'am':''} ${it.cor?'ex':''}" ${it.cor?`style="--c:${it.cor}"`:""}><div class="v">${fmt(it.valor)}</div><div class="b" style="height:${k==null?28:Math.round(100-k*55/N)}%">${k!=null?med(k):""}</div><div class="n">${esc(it.nome)}</div></div>`; }).join(""); }

/* ===================== estado ===================== */
let REF=D.meta.ref_padrao, temaSel=null, SIMSEL=null;
const sel=$("sel");
sel.innerHTML=D.meta.refs.slice().reverse().map(r=>`<option value="${r}">${D.meta.rotulos[r]}${r===D.meta.ref_ppt?" · PPT":""}</option>`).join("");
sel.value=REF;
function irPara(r){ REF=r; sel.value=r; temaSel=null; SIMSEL=null; render(); }
sel.onchange=()=>irPara(sel.value);
$("prev").onclick=()=>{ const i=D.meta.refs.indexOf(REF); if(i>0) irPara(D.meta.refs[i-1]); };
$("next").onclick=()=>{ const i=D.meta.refs.indexOf(REF); if(i<D.meta.refs.length-1) irPara(D.meta.refs[i+1]); };
$("tg").onclick=()=>{ const h=document.documentElement; h.dataset.theme=h.dataset.theme==="dark"?"light":"dark"; try{localStorage.setItem("pm_tema",h.dataset.theme);}catch(e){} setTimeout(render,30); };
try{ if(localStorage.getItem("pm_tema")) document.documentElement.dataset.theme=localStorage.getItem("pm_tema"); }catch(e){}
function fs(v){ document.documentElement.style.setProperty("--fs",v); ["fsm","fsa","fsp"].forEach(x=>$(x).classList.remove("on")); setTimeout(()=>Object.keys(CH).forEach(draw),30); }
$("fsm").onclick=()=>{fs(.92);$("fsm").classList.add("on")}; $("fsa").onclick=()=>{fs(1);$("fsa").classList.add("on")}; $("fsp").onclick=()=>{fs(1.1);$("fsp").classList.add("on")};
document.querySelectorAll(".nav").forEach(b=>b.onclick=()=>{ document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("on",x===b));
  document.querySelectorAll(".pg").forEach(p=>p.classList.toggle("on",p.id===b.dataset.pg)); $("pv").textContent=b.textContent.trim();
  setTimeout(()=>{ Object.keys(CH).forEach(draw); if(b.dataset.go){ const el=$(b.dataset.go); scrollTo({top:el.getBoundingClientRect().top+scrollY-80,behavior:"smooth"}); } else scrollTo({top:0,behavior:"smooth"}); },30); });

/* ===================== botão "+ Comparar operadoras" ===================== */
function montarCmp(){
  if(!OUT||!OUT.lista||!OUT.lista.length){ $("cmp").style.display="none"; return; }
  $("cmpBtn").innerHTML=`＋ Comparar operadoras${EXTRA.length?`<span class="cnt">${EXTRA.length}</span>`:""}`;
  const q=($("cmpQ").value||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
  const lst=OUT.lista.filter(o=>!q||o.nome.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").includes(q)||o.id.includes(q));
  $("cmpList").innerHTML=lst.map(o=>{ const on=EXTRA.includes(o.id);
    return `<label class="op"><input type="checkbox" data-id="${o.id}" ${on?"checked":""}><span class="dt" style="background:${on?corOp(o.id):"transparent"}"></span>
      <span class="nm">${esc(o.nome)}<small>${o.id.startsWith("G_")?"Grupo":"Reg. ANS "+o.id} · ${fi(o.vidas/1000)} mil vidas</small></span></label>`; }).join("")
    || `<div class="ds" style="padding:8px">Nenhuma operadora encontrada.</div>`;
  $("cmpInfo").textContent=`${OUT.lista.length} maiores operadoras por vidas`;
  $("cmpChips").innerHTML=(EXTRA.length?`<span class="t">COMPARANDO</span>`:"")+EXTRA.map(id=>`<span class="opchip" style="--c:${corOp(id)}">${esc(nomeOp(id))}<button type="button" data-x="${id}" title="Remover">×</button></span>`).join("");
}
$("cmpBtn").onclick=e=>{ e.stopPropagation(); const p=$("cmpPan"); p.classList.toggle("open"); $("cmpBtn").classList.toggle("open",p.classList.contains("open")); if(p.classList.contains("open")) setTimeout(()=>$("cmpQ").focus(),50); };
$("cmpPan").onclick=e=>e.stopPropagation();
document.addEventListener("click",()=>{ $("cmpPan").classList.remove("open"); $("cmpBtn").classList.remove("open"); });
$("cmpQ").oninput=montarCmp;
$("cmpList").onchange=e=>{ const id=e.target.dataset.id; if(!id) return;
  if(e.target.checked){ if(!EXTRA.includes(id)) EXTRA.push(id); } else EXTRA=EXTRA.filter(x=>x!==id);
  salvarOps(); render(); };
$("cmpChips").onclick=e=>{ const id=e.target.dataset&&e.target.dataset.x; if(!id) return; e.stopPropagation(); EXTRA=EXTRA.filter(x=>x!==id); salvarOps(); render(); };
$("cmpClr").onclick=()=>{ EXTRA=[]; salvarOps(); render(); };

/* ===================== render ===================== */
function igrReg(r,tema,g){ const nips=r.nips[g]||{}; const q=tema?(nips[tema]||0):Object.values(nips).reduce((a,b)=>a+b,0); const den=g==="Amil"?r.den_amil:r.den_nicho; return den>0?q/den*1e5:null; }

function render(){
  montarCmp();
  const X=D.dados[REF], K=COR(), s6=X.s6, iq=s6.idx_quad, a=s6.amil[iq], n=s6.nicho[iq];
  const opRef = id => (OD(id) && OD(id).evol) || [];
  $("upd").textContent="Atualizado em "+D.meta.gerado_em;
  $("hEy").textContent=`COMPETÊNCIA ${X.rotulo.toUpperCase()} · ${s6.labels[iq].toUpperCase()}`;
  $("hTi").innerHTML = s6.gap_pct>0 ? `Nos últimos quatro meses, fomos <em>${Math.round(s6.gap_pct)}% melhores</em> que o nicho no Índice de Reclamação proporcional a vidas.`
                                    : `Nos últimos quatro meses, ficamos <em>${Math.round(-s6.gap_pct)}% acima</em> do nicho no Índice de Reclamação proporcional a vidas.`;
  $("hSu").textContent=`Panorama mercadológico da NIP e posicionamento da Amil frente a ${s6.nicho_nome.replace("Outras do Nicho ","").replace(/[()]/g,"")} · dados abertos ANS.`;
  const pa=X.s10.podio.find(x=>x.sigla==="AMIL"), pn=X.s10.podio.filter(x=>x.sigla!=="AMIL");
  const P=X.pracas, R=P?P.regioes:[]; const val=R.filter(r=>r.den_nicho>0); const mel=val.filter(r=>igrReg(r,null,"Amil")<=igrReg(r,null,"Nicho")).length;
  const amPl=X.s7.players.find(p=>p.sigla==="AMIL");
  const kp=[["IGR Amil",f1(a),`${s6.labels[iq]} <span class="chip-d ${amPl.var_vs_tri>0?'bad':'good'}">${amPl.var_vs_tri>0?'+':''}${f1(amPl.var_vs_tri)}% vs tri.</span>`],
           ["IGR Nicho",f1(n),s6.nicho_nome.replace("Outras do Nicho ","")],
           ["Vantagem Amil",(s6.gap_pct>0?"":"-")+f1(Math.abs(s6.gap_pct))+"%","nicho ÷ Amil − 1"],
           ["% Pré-Auto Amil",pa?fp(pa.valor):"–","nicho "+pn.map(x=>x.sigla+" "+fp(x.valor)).join(" · ")],
           ["Praças ≤ nicho",val.length?`${mel}/${val.length}`:"–",val.length?Math.round(mel/val.length*100)+"% das praças":"vidas não publicadas"]];
  $("hCmp").innerHTML = EXTRA.length ? `<span class="lb">COMPARANDO ${s6.labels[iq].toUpperCase()}</span>`
    + [["Amil",a,"#ffffff"]].concat(EXTRA.map(id=>[nomeOp(id),opRef(id)[iq],corOp(id)])).map(([nm,v,c])=>{
        const d=nm!=="Amil"&&v!=null&&a?(v/a-1)*100:null;
        return `<span class="hc" style="--c:${c}"><i></i>${esc(curto(nm))} <b>${f1(v)}</b>${d==null?"":`<em class="${d>0?'good':'bad'}">Amil ${f1(Math.abs(d))}% ${d>0?'melhor':'pior'}</em>`}</span>`; }).join("") : "";
  $("kpis").innerHTML=kp.map(k=>`<div class="kpi"><small>${k[0]}</small><b>${k[1]}</b><em>${k[2]}</em></div>`).join("");

  /* s6 */
  legend("lg6",[{n:"Amil",c:K.amil},{n:s6.nicho_nome,c:K.nicho}].concat(legExtra()));
  chart("c6",{labels:s6.labels,highlight:iq,labelLines:2,areaUnder:1,
    lines:[{name:s6.nicho_nome,values:s6.nicho,color:K.nicho,width:2.2}].concat(linhasExtra(opRef)).concat([{name:"Amil",values:s6.amil,color:K.amil,width:3.4,glow:1}])});
  let t6=`No <b>${s6.labels[iq]}</b>, fomos <b>${f1(Math.abs(s6.gap_pct))}% ${s6.gap_pct>0?"melhores":"piores"}</b> que o nicho (${f1(a)} vs ${f1(n)}).`;
  if(EXTRA.length){
    const rk=[["Amil",a],["Nicho",n]].concat(EXTRA.map(id=>[nomeOp(id),opRef(id)[iq]])).filter(x=>x[1]!=null).sort((x,z)=>x[1]-z[1]);
    const pos=rk.findIndex(x=>x[0]==="Amil")+1;
    t6+=`<br>Incluindo as operadoras selecionadas, a Amil fica em <b>${pos}º de ${rk.length}</b> (menor IGR é melhor): `+rk.map((x,i)=>`${i+1}º ${x[0]==="Amil"?"<b>Amil</b>":esc(x[0])} ${f1(x[1])}`).join(" · ");
  }
  $("i6").innerHTML=t6;
  /* s7 */
  const pl=X.s7.players.map(p=>({name:p.sigla==="AMIL"?"Amil":p.nome,values:p.valores,color:K[p.sigla],width:p.sigla==="AMIL"?3.4:2.2,labels:p.sigla==="AMIL",glow:p.sigla==="AMIL",dash:p.sigla==="AMIL"?null:"5 4"}));
  const plAll=pl.filter(p=>p.name!=="Amil").concat(linhasExtra(opRef)).concat(pl.filter(p=>p.name==="Amil"));
  legend("lg7",pl.map(p=>({n:p.name,c:p.color})).concat(legExtra()));
  chart("c7",{labels:X.s7.labels,highlight:X.s7.idx_quad,labelLines:2,lines:plAll});
  const outros=X.s7.players.filter(p=>p.sigla!=="AMIL"); const sub=outros.filter(p=>p.var_vs_tri>0).length;
  const menorCresc=X.s7.players.every(p=>p.sigla==="AMIL"||p.var_vs_tri==null||amPl.var_vs_tri<=p.var_vs_tri);
  const supera=outros.filter(p=>p.quad>amPl.quad).length;
  let t7=`${sub===outros.length?"Todos os players do nicho tiveram aumento":`${sub} de ${outros.length} players do nicho tiveram aumento`} nos últimos quatro meses`
    +(menorCresc?", enquanto fomos o que apresentou <b>o menor crescimento</b>.":".")+` Superamos <b>${supera} de ${outros.length}</b> players na análise individual.<br>`
    +X.s7.players.map(p=>`${p.sigla==="AMIL"?"<b>Amil</b>":p.nome} <b>${f1(p.quad)}</b> <span class="${p.var_vs_tri>0?'up':'dn'}">(${p.var_vs_tri>0?'+':''}${f1(p.var_vs_tri)}%)</span>`).join(" · ");
  if(EXTRA.length) t7+="<br>"+EXTRA.map(id=>{ const v=opRef(id), q=v[iq], ant=iq?v[iq-1]:null, d=q!=null&&ant?(q/ant-1)*100:null;
      return `${esc(nomeOp(id))} <b>${f1(q)}</b>${d==null?"":` <span class="${d>0?'up':'dn'}">(${d>0?'+':''}${f1(d)}%)</span>`}`; }).join(" · ");
  $("i7").innerHTML=t7;

  /* s11 */
  const g=X.s11; $("t11").textContent="· "+g.periodo; let melhor=0;
  const exG=EXTRA.filter(id=>OD(id)&&OD(id).grid&&Object.keys(OD(id).grid).length);
  const cols=g.colunas.concat(exG), base=c=>g.colunas.includes(c);
  const vget=(l,c)=>base(c)?l.valores[c]:(OD(c).grid[l.grupo]??null);
  let h=`<table class="gd"><tr><th>Qtd 12 meses<br>${g.periodo}</th>${cols.map(c=>base(c)?`<th class="${c==='AMIL'?'am':''}">${c}</th>`:`<th class="ex" style="--c:${corOp(c)}" title="${esc(nomeOp(c))}">${esc(curto(nomeOp(c)))}</th>`).join("")}<th>${g.nicho_rotulo}</th><th>Leitura</th></tr>`;
  g.linhas.forEach(l=>{ const vs=cols.map(c=>[c,vget(l,c)]); const ord=vs.filter(x=>x[1]!=null).sort((x,z)=>x[1]-z[1]).map(x=>x[0]);
    if(ord.indexOf("AMIL")===0) melhor++; const gp=l.valores.AMIL!=null&&l.valores.NICHO?(l.valores.AMIL/l.valores.NICHO-1)*100:null;
    h+=`<tr><td>${l.grupo}</td>`+vs.map(([c,v])=>{ const k=ord.indexOf(c); return `<td class="${c==='AMIL'?'am':''}">${k>=0?med(k):""}${f1(v)}</td>`; }).join("")
      +`<td class="ni">${f1(l.valores.NICHO)}</td><td>${gp==null?"":`<span class="tag ${gp>0?'bad':'good'}">${gp>0?'+':''}${f1(gp)}%</span>`}</td></tr>`; });
  h+=`<tr class="tot"><td>Total</td>${cols.map(c=>`<td class="${c==='AMIL'?'am':''}">${f1(base(c)?g.total[c]:OD(c).grid_tot)}</td>`).join("")}<td class="ni">${f1(g.total.NICHO)}</td><td></td></tr></table>`;
  $("g11").innerHTML=h; const pior=g.linhas.filter(l=>l.valores.AMIL>l.valores.NICHO).map(l=>l.grupo);
  let t11=`Amil em <b>1º lugar em ${melhor} de ${g.linhas.length}</b> grupos de temas${exG.length?` (entre ${cols.length} operadoras)`:""}. `+(pior.length?`Acima do nicho em: <b>${pior.join(", ")}</b>.`:"Abaixo do nicho em todos os grupos.");
  exG.forEach(id=>{ const mel=g.linhas.filter(l=>{const v=OD(id).grid[l.grupo]; return v!=null&&l.valores.AMIL!=null&&v<l.valores.AMIL;}).map(l=>l.grupo);
    t11+=`<br><span style="color:${corOp(id)}">●</span> ${esc(curto(nomeOp(id)))}: ${mel.length?`melhor que a Amil em <b>${mel.join(", ")}</b>`:"Amil é melhor em todos os grupos"}.`; });
  if(EXTRA.length&&!exG.length) t11+=`<br><i style="opacity:.75">As operadoras selecionadas só têm IGR nesta base (rode a versão completa para temas).</i>`;
  $("i11").innerHTML=t11;

  /* s9 */
  const T=X.s9.temas; $("t9").textContent="· "+X.s9.periodo; $("tp9").textContent="· "+X.s9.periodo;
  legend("lg9",[{n:"Amil + Nicho",c:K.lav,bar:1},{n:"Amil",c:K.amil},{n:"Nicho",c:K.nicho}].concat(legExtra()));
  chart("c9",{labels:T.map(t=>nomeT(t.tema)),bars:[{name:"Amil + Nicho",values:T.map(t=>t.total)}],
    lines:[{name:"Nicho",values:T.map(t=>t.nicho),color:K.nicho,width:2.2}].concat(linhasExtra(id=>T.map(t=>OD(id)?.temas?.[t.tema]??null))).concat([{name:"Amil",values:T.map(t=>t.amil),color:K.amil,width:3,glow:1}]),
    alerts:T.map((t,i)=>X.s9.destaques.includes(t.tema)?i:null).filter(i=>i!=null),
    extra:i=>T[i].gap_pct!=null?`<span style="opacity:.8">Amil vs nicho: <b>${T[i].gap_pct>0?'+':''}${T[i].gap_pct}%</b></span>`:""});
  $("co9").innerHTML=T.filter(t=>X.s9.destaques.includes(t.tema)).map(t=>`<div class="co"><span class="big">+${t.gap_pct}%</span><b>${nomeT(t.tema)}:</b> temos ${t.gap_pct}% mais reclamações proporcionalmente à base do que o nicho.</div>`).join("")
    || `<div class="ins">A Amil está abaixo do nicho em todos os temas relevantes.</div>`;
  const pod9=X.s9.podio.concat(EXTRA.map(id=>({nome:curto(nomeOp(id)),valor:opRef(id)[iq]??null,cor:corOp(id)})));
  podio("p9",pod9,f2);
  let tp9=`A Amil é o <b>benchmark de IGR</b> do nicho. Dos <b>${T.length}</b> temas avaliados, não é a melhor em <b>${X.s9.qtd_piores}</b>.`;
  if(EXTRA.length){ const o=pod9.filter(x=>x.valor!=null&&x.nome!=="Amil + Nicho").sort((x,z)=>x.valor-z.valor); tp9+=`<br>Com as operadoras selecionadas, a Amil fica em <b>${o.findIndex(x=>x.nome==="Amil")+1}º de ${o.length}</b>.`; }
  $("ip9").innerHTML=tp9;

  /* s10 */
  $("t10").textContent="· "+X.s10.periodo;
  legend("lg10",[{n:"Amil + Nicho (IGR)",c:K.lav,bar:1},{n:"Transbordo Amil",c:K.amil},{n:"Transbordo Nicho",c:K.nicho}].concat(legExtra()));
  chart("c10",{labels:T.map(t=>nomeT(t.tema)),bars:[{name:"IGR Amil + Nicho",values:T.map(t=>t.total)}],right:true,
    lines:[{name:"Transbordo Nicho",values:T.map(t=>t.transb_nicho),color:K.nicho,axis:"r",fmt:fp,width:2.2},{name:"Transbordo Amil",values:T.map(t=>t.transb_amil),color:K.amil,axis:"r",fmt:fp,width:3,glow:1}]
      .concat(linhasExtra(id=>T.map(t=>OD(id)?.transb?.[t.tema]??null)).map(l=>Object.assign(l,{axis:"r",fmt:fp,name:"Transbordo "+l.name}))),
    alerts:T.map((t,i)=>X.s10.acima.includes(t.tema)?i:null).filter(i=>i!=null)});
  podio("p10",X.s10.podio.concat(EXTRA.filter(id=>OD(id)?.transb_tot!=null).map(id=>({nome:curto(nomeOp(id)),valor:OD(id).transb_tot,cor:corOp(id)}))),fp);
  const ac=X.s10.acima.map(nomeT);
  $("i10").innerHTML=`A Amil ${pa&&pn.every(x=>pa.valor<=x.valor)?"se destaca com o <b>menor transbordo</b> para Pré-Auto":"tem transbordo de <b>"+fp(pa&&pa.valor)+"</b> para Pré-Auto"} — dos <b>${T.length}</b> temas, <b>${ac.length}</b> ${ac.length===1?"ultrapassa":"ultrapassam"} a média do nicho${ac.length?": <b>"+ac.join(", ")+"</b>":""}.`
    +`<br><i style="opacity:.8">Hipótese: se a taxa de êxito no Auto de Infração for favorável, volume superior ao nicho pode representar risco calculado saudável.</i>`;

  /* praças: chips */
  if(P){ $("t8").textContent="· "+P.periodo; $("t12").textContent="· "+P.periodo;
    if(!temaSel||!P.temas.includes(temaSel)) temaSel=P.tema_default;
    $("chips").innerHTML=P.temas.map(t=>{ const l=T.find(x=>x.tema===t); return `<button class="chip ${l&&l.gap_pct>0?'dev':''}" data-t="${esc(t)}">${nomeT(t)}</button>`; }).join("");
    $("chips").onclick=e=>{ const b=e.target.closest(".chip"); if(!b) return; temaSel=b.dataset.t; pracas(); };
  }
  pracas(); sugestoes(); timeline(); metodologia();
}

function tabela(id,R,tema){ const ex=EXTRA.filter(i=>OD(i)?.pracas);
  let h=`<table><tr><th>Praça</th><th>Vidas Amil</th><th>Vidas Nicho</th><th>NIPs Amil</th><th>NIPs Nicho</th><th>IGR Amil</th><th>IGR Nicho</th><th>Δ%</th>${ex.map(i=>`<th style="color:${corOp(i)}">IGR ${esc(curto(nomeOp(i)))}</th>`).join("")}</tr>`;
  R.forEach(r=>{ const a=igrReg(r,tema,"Amil"), n=igrReg(r,tema,"Nicho"); const sm=g=>tema?(r.nips[g][tema]||0):Object.values(r.nips[g]).reduce((x,y)=>x+y,0); const d=a!=null&&n?(a/n-1)*100:null;
    h+=`<tr><td>${r.nome}</td><td>${fi(r.vidas_amil)}</td><td>${fi(r.vidas_nicho)}</td><td>${fi(sm("Amil"))}</td><td>${fi(sm("Nicho"))}</td><td><b>${f2(a)}</b></td><td>${f2(n)}</td><td>${d==null?"–":`<span class="tag ${d>0?'bad':'good'}">${d>0?'+':''}${f1(d)}%</span>`}</td>`
      +ex.map(i=>{ const v=igrOp(i,r.nome,tema); return `<td>${v==null?"–":`<span class="tag ${a!=null&&v<a?'bad':'good'}" title="${a!=null&&v<a?'menor que a Amil':'Amil melhor'}">${f2(v)}</span>`}</td>`; }).join("")+`</tr>`; });
  $(id).innerHTML=h+"</table>"; }
function txtExtraPracas(R,tema,aVals){ return EXTRA.filter(i=>OD(i)?.pracas).map(i=>{ let tot=0,mel=0; R.forEach((r,k)=>{ const v=igrOp(i,r.nome,tema); if(v!=null&&aVals[k]!=null){ tot++; if(v<aVals[k]) mel++; } });
    return tot?`<br><span style="color:${corOp(i)}">●</span> ${esc(curto(nomeOp(i)))}: IGR menor que a Amil em <b>${mel} de ${tot}</b> praças onde atua.`:""; }).join(""); }

function pracas(){
  const X=D.dados[REF], P=X.pracas, K=COR();
  if(!P){ ["c8","c12"].forEach(i=>$(i).innerHTML=`<div class="ds">Beneficiários por município ainda não publicados pela ANS para esta competência.</div>`); return; }
  document.querySelectorAll("#chips .chip").forEach(c=>c.classList.toggle("on",c.dataset.t===temaSel));
  const R=P.regioes, s6=X.s6, top=R.map(r=>fi(r.vidas_amil/1000));
  const a=R.map(r=>igrReg(r,null,"Amil")), n=R.map(r=>igrReg(r,null,"Nicho"));
  legend("lg8",[{n:"Amil",c:K.amil},{n:"Nicho (BPS)",c:K.nicho},{n:"IGR Amil total",c:K.good}].concat(legExtra()));
  chart("c8",{labels:R.map(r=>r.nome),topRow:top,labelLines:3,
    lines:[{name:"Nicho (BPS)",values:n,color:K.nicho,width:2.2,fs:9.5},{name:"Amil",values:a,color:K.amil,width:3.2,glow:1}].concat(linhasExtra(id=>R.map(r=>igrOp(id,r.nome,null)))),
    ref:{value:s6.amil[s6.idx_quad],label:"IGR Amil total"},alerts:a.map((v,i)=>n[i]!=null&&v>n[i]?i:null).filter(i=>i!=null)});
  const v=R.filter((r,i)=>n[i]!=null), mel=a.filter((x,i)=>n[i]!=null&&x<=n[i]).length, pi=R.filter((r,i)=>n[i]!=null&&a[i]>n[i]).map(r=>r.nome);
  $("i8").innerHTML=`Em uma avaliação global do IGR, somos <b>melhores que nossos pares em ${mel} das ${v.length} regiões (${v.length?Math.round(mel/v.length*100):0}%)</b>`
    +(pi.length?` e temos oportunidades em <b>${pi.length} praças (${Math.round(pi.length/v.length*100)}%)</b> — ${pi.join(", ")} — para, pelo menos, alcançar o patamar do nicho.`:".")
    +` <span style="opacity:.7">Vidas: ${P.meses_vidas.join(", ")}.</span>`+txtExtraPracas(R,null,a);
  tabela("tb8",R,null);
  const ta=R.map(r=>igrReg(r,temaSel,"Amil")), tn=R.map(r=>igrReg(r,temaSel,"Nicho")), d=ta.map((x,i)=>x!=null&&tn[i]?x/tn[i]-1:null);
  legend("lg12",[{n:"Amil",c:K.amil},{n:"Nicho (BPS)",c:K.nicho}].concat(legExtra()));
  chart("c12",{labels:R.map(r=>r.nome),topRow:top,labelLines:3,fillBetween:[0,1],
    lines:[{name:"Nicho (BPS)",values:tn,color:K.nicho,width:2.2,fs:9.5},{name:"Amil",values:ta,color:K.amil,width:3.2,glow:1}].concat(linhasExtra(id=>R.map(r=>igrOp(id,r.nome,temaSel)))),
    bottomRow:d.map(x=>x==null?null:{t:(x>0?'+':'')+Math.round(x*100)+"%",c:x>0?K.bad:K.good}),
    ref:P.ref_temas[temaSel]!=null?{value:P.ref_temas[temaSel],label:"Amil total no tema"}:null});
  const pos=d.filter(x=>x!=null&&x>0), t11=d.slice(0,11).filter(x=>x!=null), des=t11.filter(x=>x>0).length;
  $("i12").innerHTML=`<b>${nomeT(temaSel)}:</b> `+(pos.length?`gap em relação ao nicho em <b>${pos.length} praças</b>, variando de <b>+${Math.round(Math.min(...pos)*100)}% até +${Math.round(Math.max(...pos)*100)}%</b>. `:"nenhuma praça acima do nicho. ")
    +`Nas <b>11 primeiras praças</b> (maior volume de vidas Amil), <b>${Math.round(des/Math.max(t11.length,1)*100)}%</b> estão em desvantagem com os concorrentes diretos.`+txtExtraPracas(R,temaSel,ta);
  tabela("tb12",R,temaSel);
}

/* ===================== PLUS · SUGESTÃO PARA DIRECIONAMENTO ===================== */
const ACOES={
 "Cobert. Rede":["Rede / Credenciamento","Revisar a suficiência e os descredenciamentos da rede na praça, priorizando as especialidades com maior demanda, e comunicar com antecedência as substituições de prestador."],
 "Autoriz. Regulação":["Regulação / Autorização","Reduzir negativas e prazos de autorização: revisar critérios de auditoria e guias pendentes, e explicar claramente ao beneficiário o motivo da negativa."],
 "Reembolso":["Reembolso","Acelerar a análise e o pagamento, simplificar a documentação exigida e dar transparência ao cálculo do valor reembolsado."],
 "Cobert. Roll":["Regulação / Jurídico","Revisar as negativas por Rol/DUT e os casos recorrentes, alinhando o parecer técnico e a comunicação ao beneficiário."],
 "Prazo Máximos":["Rede / Agendamento","Garantir agenda dentro dos prazos máximos da ANS: ampliar oferta, central de agendamento e alternativas na rede."],
 "Cobert. CPT":["Comercial / Cadastro","Reforçar a explicação de carência e CPT na venda e no onboarding, e revisar a declaração de saúde."],
 "Mensal. e Reajuste":["Financeiro / Relacionamento","Comunicar o reajuste com antecedência e memória de cálculo, e revisar cobranças indevidas e coparticipação."],
 "Contratos Susp/Recisão":["Financeiro / Retenção","Revisar a régua de inadimplência e garantir notificação prévia antes de suspensão ou rescisão."],
 "Contratos Portabil.":["Cadastro / Movimentação","Simplificar o fluxo de portabilidade e cumprir os prazos de análise."],
 "Contratos - Contratação/ Adesão/Vigência":["Comercial / Cadastro","Revisar o onboarding: ativação, inclusão de dependentes e início de vigência."],
 "Contrato Outros":["Relacionamento","Abrir os casos para identificar causas recorrentes e criar tratativa preventiva."]
};
const acao=t=>ACOES[t]||["Relacionamento","Analisar os casos para identificar a causa raiz e criar tratativa preventiva."];

function montarOportunidades(X){
  const T=X.s9.temas, P=X.pracas, s6=X.s6, iq=s6.idx_quad, igrA=s6.amil[iq];
  const totA=T.reduce((s,t)=>s+(t.qtd_amil||0),0)||1;
  const pts=e=>e/totA*igrA;
  const out=[];
  T.forEach(t=>{ if(t.amil!=null&&t.nicho&&t.amil>t.nicho){ const e=t.qtd_amil*(1-t.nicho/t.amil);
    out.push({tipo:"Tema · Brasil",onde:"Brasil",tema:t.tema,a:t.amil,n:t.nicho,gap:(t.amil/t.nicho-1),exc:e,pts:t.amil-t.nicho}); }});
  if(P){ P.regioes.forEach(r=>{
      const qa=Object.values(r.nips.Amil).reduce((x,y)=>x+y,0), qn=Object.values(r.nips.Nicho).reduce((x,y)=>x+y,0);
      if(r.den_nicho>0&&qn>=10&&qa>=5){ const exp=qn/r.den_nicho*r.den_amil; if(qa>exp)
        out.push({tipo:"Praça",onde:r.nome,tema:null,a:qa/r.den_amil*1e5,n:qn/r.den_nicho*1e5,gap:qa/exp-1,exc:qa-exp,pts:pts(qa-exp),vidas:r.vidas_amil}); }
      P.temas.forEach(tm=>{ const a=r.nips.Amil[tm]||0, b=r.nips.Nicho[tm]||0;
        if(r.den_nicho>0&&b>=5&&a>=5){ const exp=b/r.den_nicho*r.den_amil; const e=a-exp;
          if(e>=2) out.push({tipo:"Praça × Tema",onde:r.nome,tema:tm,a:a/r.den_amil*1e5,n:b/r.den_nicho*1e5,gap:a/exp-1,exc:e,pts:pts(e),vidas:r.vidas_amil}); } }); }); }
  const mx=Math.max(...out.map(o=>o.exc),1);
  out.forEach(o=>o.prio=o.exc>=mx*.5?"Alta":o.exc>=mx*.2?"Média":"Baixa");
  return out.sort((x,y)=>y.exc-x.exc);
}

function sugestoes(){
  const X=D.dados[REF], s6=X.s6, iq=s6.idx_quad, igrA=s6.amil[iq], igrN=s6.nicho[iq];
  const OP=montarOportunidades(X);
  const pt=OP.filter(o=>o.tipo==="Praça × Tema"), temas=OP.filter(o=>o.tipo==="Tema · Brasil"), pr=OP.filter(o=>o.tipo==="Praça");
  const base=pt.length?pt:temas;
  if(SIMSEL===null) SIMSEL=new Set(base.slice(0,5).map((o,i)=>i));
  const top3=base.slice(0,3); const somaTop=top3.reduce((s,o)=>s+o.pts,0);
  const temaMais=temas[0];
  $("sgRes").innerHTML = (base.length
    ? `Com base em ${X.s9.periodo}, as <b>${top3.length} frentes prioritárias</b> concentram cerca de <b>${fi(top3.reduce((s,o)=>s+o.exc,0))} NIPs evitáveis</b> e podem reduzir o IGR da Amil em <b>${f1(somaTop)} pontos</b> (de ${f1(igrA)} para ${f1(igrA-somaTop)}). `
    : `A Amil está igual ou abaixo do nicho em todos os temas e praças analisados neste período. `)
    + (temaMais?`No Brasil, o tema com maior oportunidade é <b>${nomeT(temaMais.tema)}</b> (${f1(temaMais.a)} vs ${f1(temaMais.n)} do nicho, <b>+${Math.round(temaMais.gap*100)}%</b>). `:"")
    + (pr.length?`Em praças, a maior distância para o nicho está em <b>${pr.slice().sort((a,b)=>b.exc-a.exc)[0].onde}</b>. `:"")
    + `<span style="opacity:.75">Sugestões geradas automaticamente a partir dos dados; validar com as áreas responsáveis.</span>`;
  $("sgFront").innerHTML = top3.length ? top3.map((o,i)=>{ const [area,txt]=acao(o.tema);
    return `<div class="front"><span class="rk">#${i+1}</span><div class="tp">FRENTE ${i+1} · ${o.tipo.toUpperCase()}</div>
      <h4>${o.tema?nomeT(o.tema):"IGR geral"}</h4><div class="where">Onde: <b>${o.onde}</b>${o.vidas?` · ${fi(o.vidas/1000)} mil vidas Amil`:""}</div>
      <div class="nums"><div><small>AMIL</small><b class="up">${f1(o.a)}</b></div><div><small>NICHO</small><b>${f1(o.n)}</b></div><div><small>GAP</small><b class="up">+${Math.round(o.gap*100)}%</b></div></div>
      <div class="nums"><div><small>NIPS EVITÁVEIS</small><b>${fi(o.exc)}</b></div><div><small>IMPACTO IGR</small><b class="dn">−${f2(o.pts)}</b></div></div>
      <div class="acao"><b>Ação sugerida:</b> ${txt}</div><div class="area"><span class="tag info">${area}</span> <span class="tag ${o.prio==="Alta"?"bad":o.prio==="Média"?"warn":"good"}">Prioridade ${o.prio}</span></div></div>`; }).join("")
    : `<div class="card"><h3>Sem frentes críticas</h3><div class="ds">Nenhuma praça/tema acima do nicho com volume relevante.</div></div>`;
  const top=base.slice(0,12), mx=Math.max(...top.map(o=>o.exc),1);
  $("sgRank").innerHTML = top.map((o,i)=>`<label class="rk-row"><input type="checkbox" data-i="${i}" ${SIMSEL.has(i)?"checked":""}>
      <span class="nm"><b>${o.tema?nomeT(o.tema):"IGR geral"}</b><span>${o.onde} · Amil ${f1(o.a)} vs nicho ${f1(o.n)} (+${Math.round(o.gap*100)}%)</span></span>
      <span class="rk-bar"><i style="width:${o.exc/mx*100}%"></i></span><span class="vl">${fi(o.exc)}</span></label>`).join("")
    || `<div class="ds">Sem oportunidades relevantes neste período.</div>`;
  $("sgRank").onchange=e=>{ const i=+e.target.dataset.i; if(e.target.checked) SIMSEL.add(i); else SIMSEL.delete(i); simular(base,igrA,igrN); };
  simular(base,igrA,igrN);
  const al=[]; const amPl=X.s7.players.find(p=>p.sigla==="AMIL");
  if(amPl&&amPl.var_vs_tri!=null) al.push(amPl.var_vs_tri>0
     ?["warn","↗",`<b>Tendência de alta:</b> o IGR da Amil subiu <b>${f1(amPl.var_vs_tri)}%</b> vs o trimestre anterior. Acompanhar mês a mês.`]
     :["good","↘",`<b>Tendência de queda:</b> o IGR da Amil caiu <b>${f1(-amPl.var_vs_tri)}%</b> vs o trimestre anterior.`]);
  const ult=s6.amil[s6.amil.length-1], qd=s6.amil[iq];
  if(ult!=null&&qd!=null&&ult>qd*1.05) al.push(["bad","!",`<b>Último mês acima da média:</b> ${s6.labels[s6.labels.length-1]} com ${f1(ult)}, ${f1((ult/qd-1)*100)}% acima da média do quadrimestre.`]);
  X.s10.temas.filter(t=>t.transb_amil!=null&&t.transb_nicho!=null&&t.transb_amil>t.transb_nicho).sort((a,b)=>b.qtd_amil*(b.transb_amil-b.transb_nicho)-a.qtd_amil*(a.transb_amil-a.transb_nicho)).slice(0,2)
    .forEach(t=>al.push(["bad","§",`<b>Risco regulatório · ${nomeT(t.tema)}:</b> transbordo para Pré-Auto de ${fp(t.transb_amil)} vs ${fp(t.transb_nicho)} do nicho (≈ ${fi(t.qtd_amil*(t.transb_amil-t.transb_nicho))} processos a mais).`]));
  const gr=X.s11.linhas.filter(l=>l.rank.AMIL&&l.rank.AMIL>=3).map(l=>l.grupo);
  if(gr.length) al.push(["warn","◔",`<b>Maturidade 12 meses:</b> Amil em 3º/4º lugar em ${gr.join(", ")}.`]);
  if(X.pracas){ const fort=X.pracas.regioes.map(r=>({r,a:igrReg(r,null,"Amil"),n:igrReg(r,null,"Nicho")})).filter(x=>x.n&&x.a<x.n).sort((x,y)=>(x.a/x.n)-(y.a/y.n)).slice(0,3);
    if(fort.length) al.push(["good","★",`<b>Fortalezas para manter:</b> ${fort.map(x=>`${x.r.nome} (${Math.round((x.a/x.n-1)*100)}%)`).join(", ")} — boas práticas para replicar.`]); }
  EXTRA.forEach(id=>{ const o=OD(id); if(!o) return; const v=(o.evol||[])[iq];
    const melh=o.temas?X.s9.temas.filter(t=>o.temas[t.tema]!=null&&t.amil!=null&&o.temas[t.tema]<t.amil).map(t=>nomeT(t.tema)):[];
    al.push([v!=null&&v<igrA?"warn":"good","⇄",`<b>Benchmark · ${esc(nomeOp(id))}:</b> IGR ${f1(v)} vs ${f1(igrA)} da Amil`
      +(o.temas?(melh.length?`; menor que a Amil em <b>${melh.length}</b> tema(s): ${melh.join(", ")} — vale estudar as práticas.`:"; a Amil é melhor em todos os temas."):".")]); });
  $("sgAl").innerHTML=al.map(a=>`<div class="al ${a[0]}"><span class="ic">${a[1]}</span><span>${a[2]}</span></div>`).join("") || `<div class="ds">Sem alertas.</div>`;
  let h=`<table><tr><th class="l">Prioridade</th><th class="l">Tipo</th><th class="l">Onde</th><th class="l">Tema</th><th>Amil</th><th>Nicho</th><th>Gap</th><th>NIPs evitáveis</th><th>Impacto IGR</th><th class="l">Área sugerida</th><th class="l">Ação sugerida</th></tr>`;
  OP.slice(0,60).forEach(o=>{ const [area,txt]=o.tema?acao(o.tema):["Gestão regional","Abrir a praça por tema (Visão Praças) e atacar os temas com maior desvio."];
    h+=`<tr><td class="l"><span class="tag ${o.prio==="Alta"?"bad":o.prio==="Média"?"warn":"good"}">${o.prio}</span></td><td class="l">${o.tipo}</td><td class="l"><b>${o.onde}</b></td><td class="l">${o.tema?nomeT(o.tema):"—"}</td>
      <td><b>${f1(o.a)}</b></td><td>${f1(o.n)}</td><td><span class="tag bad">+${Math.round(o.gap*100)}%</span></td><td><b>${fi(o.exc)}</b></td><td class="dn">−${f2(o.pts)}</td>
      <td class="l"><span class="tag info">${area}</span></td><td class="l" style="min-width:280px;white-space:normal">${txt}</td></tr>`; });
  $("sgTb").innerHTML=h+"</table>";
}

function simular(base,igrA,igrN){
  const selc=[...SIMSEL].map(i=>base[i]).filter(Boolean); const red=selc.reduce((s,o)=>s+o.pts,0), proj=Math.max(igrA-red,0);
  const gapAt=(igrN/igrA-1)*100, gapPj=proj?(igrN/proj-1)*100:null;
  const esc0=Math.max(igrA,igrN)*1.1;
  $("sgSim").innerHTML=`<div class="big"><div><small>IGR ATUAL</small><b>${f1(igrA)}</b></div><span class="arrow">→</span><div class="proj"><small>IGR PROJETADO</small><b>${f1(proj)}</b></div></div>
    <div class="gauge"><span class="f" style="width:${proj/esc0*100}%"></span>
      <span class="mk" style="left:${igrA/esc0*100}%"><span>Atual</span></span><span class="mk" style="left:${igrN/esc0*100}%;background:${COR().bad}"><span>Nicho ${f1(igrN)}</span></span></div>
    <div class="ins" style="margin-top:0">Atuando em <b>${selc.length} frente${selc.length===1?"":"s"}</b> (≈ ${fi(selc.reduce((s,o)=>s+o.exc,0))} NIPs evitáveis), a vantagem da Amil sobre o nicho passa de <b>${f1(gapAt)}%</b> para <b>${f1(gapPj)}%</b>.</div>`;
}

function timeline(){
  const NM=["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
  const S=D.serie, K=COR(), lab=S.meses.map(m=>NM[+m.slice(5,7)-1]+m.slice(2,4));
  const pos=S.meses.indexOf(REF);
  const opSer = id => (OUT && OUT.serie && OUT.serie[id]) || [];
  const TOT=S.TODOS||S.AMIL.map(()=>null);
  const temTot=TOT.some(v=>v!=null);
  const linT={name:"IGR Total (Amil + Nicho)",values:TOT,color:K.total,width:2.2,dash:"6 5",r:2.6,fs:9,labels:false};
  legend("lgT1",[{n:"Amil",c:K.amil},{n:"Nicho",c:K.nicho}].concat(temTot?[{n:"IGR Total (Amil + Nicho)",c:K.total,dash:1}]:[]).concat(legExtra()));
  chart("cT1",{labels:lab,labelLines:1,fillBetween:[0,1],highlight:pos>=0?pos:null,
    lines:[{name:"Nicho",values:S.NICHO,color:K.nicho,width:2.2,fs:9.5},{name:"Amil",values:S.AMIL,color:K.amil,width:3.2,glow:1,fs:9.5}]
      .concat(temTot?[linT]:[]).concat(linhasExtra(opSer))});
  const li=pos>=0?pos:S.meses.length-1, aU=S.AMIL[li], tU=temTot?TOT[li]:null, nU=S.NICHO[li];
  const melhoresT=temTot?S.AMIL.filter((v,i)=>v!=null&&TOT[i]!=null&&v<=TOT[i]).length:0, totM=S.AMIL.filter(v=>v!=null).length;
  let tt=`Em <b>${lab[li]}</b>, a Amil registrou <b>${f1(aU)}</b>`+(temTot?` contra <b>${f1(tU)}</b> do IGR total (Amil + Nicho), <b>${f1(Math.abs((aU/tU-1)*100))}% ${aU<=tU?"abaixo":"acima"}</b>`:"")+` e ${f1(nU)} do nicho.`
     +(temTot?` A Amil ficou abaixo do IGR total em <b>${melhoresT} de ${totM}</b> meses da série.`:"");
  if(EXTRA.length) tt+=`<br>Operadoras selecionadas em ${lab[li]}: `+EXTRA.map(id=>`${esc(nomeOp(id))} <b>${f1(opSer(id)[li])}</b>`).join(" · ");
  $("iT1").innerHTML=tt;
  const pl=["AMIL","B","P","S"].filter(s=>S[s]).map(s=>({name:s==="AMIL"?"Amil":"Player ("+s+")",values:S[s],color:K[s],width:s==="AMIL"?3.2:2,labels:s==="AMIL",glow:s==="AMIL",fs:9.5}));
  if(temTot) pl.push(linT);
  const plAll=pl.concat(linhasExtra(opSer));
  legend("lgT2",plAll.map(p=>({n:p.name,c:p.color,dash:p.dash?1:0})));
  chart("cT2",{labels:lab,labelLines:1,highlight:pos>=0?pos:null,lines:plAll});
  const REFS=temTot?TOT:S.NICHO;
  let h=`<table><tr><th>Operadora</th>${lab.map(l=>`<th>${l}</th>`).join("")}</tr>`;
  const linhas=[["AMIL","Amil",S.AMIL],["TODOS","IGR Total",S.TODOS],["NICHO","Nicho",S.NICHO],["B","Player (B)",S.B],["P","Player (P)",S.P],["S","Player (S)",S.S]]
    .concat(EXTRA.map(id=>[id,nomeOp(id),opSer(id)])).filter(x=>x[2]);
  linhas.forEach(([k,nm,vals])=>{
    h+=`<tr><td><b>${esc(nm)}</b></td>`+vals.map((v,i)=>{ const rf=REFS[i]; const cl=k==="TODOS"||(!temTot&&k==="NICHO")||v==null||rf==null?"":(v<=rf?"good":"bad"); return `<td>${cl?`<span class="tag ${cl}">${f1(v)}</span>`:f1(v)}</td>`; }).join("")+"</tr>"; });
  $("tbT").innerHTML=h+"</table>";
}

function metodologia(){
  const M=D.meta;
  $("met").innerHTML=[
   ["IGR (Índice Geral de Reclamações)",`Fonte oficial ANS. Para trimestres, quadrimestre e grupos de operadoras é usada a <b>${M.metodo==="media"?"média simples do IGR publicado (operadora × mês)":"soma das reclamações ÷ soma dos beneficiários × 100 mil"}</b>, mesma regra do material apresentado. Somente Assistência Médica.`],
   ["IGR Total (Amil + Nicho)","IGR do conjunto das operadoras comparadas (Amil, P, S e B) no mês. Serve de régua de mercado para a Amil na linha do tempo."],
   ["Comparar operadoras","Botão no capítulo 1: no topo do painel: inclui outras operadoras médico-hospitalares (as maiores por nº de vidas no IGR da ANS) em todos os gráficos — evolução, grid, temas, Pré-Auto, praças, pódios e linha do tempo — com a mesma regra de cálculo da Amil. Praças só aparecem onde a operadora tem pelo menos 1 mil vidas. A seleção fica salva no navegador."],
   ["Fatias por tema (Pareto)","IGR do grupo no período × participação do tema nas NIPs do grupo. A soma das 11 fatias reproduz o IGR de cada grupo (Amil, Nicho e Amil + Nicho)."],
   ["Transbordo para Pré-Auto","% das NIPs do tema/operadora que seguiram para Pré-Auto de Infração no período, segundo a base analítica de demandas NIP."],
   ["Grid de maturidade","Janela de 12 meses por grupo de temas; medalhas indicam a posição entre P, S, B e Amil. Nicho APSB = as quatro operadoras juntas."],
   ["Praças (Regiões de Saúde)","NIPs da praça ÷ (vidas médias da praça × nº de meses) × 100 mil. Vidas: beneficiários por município (ANS). Clusters conforme o MAPA de Regiões de Saúde da Amil."],
   ["Sugestão para direcionamento","NIPs evitáveis = NIPs da Amil − NIPs esperadas se a Amil tivesse a taxa do nicho na mesma praça e tema. Impacto no IGR = NIPs evitáveis ÷ NIPs totais da Amil × IGR da Amil. Mínimo de 5 NIPs na Amil e no nicho para entrar no ranking. Ações e áreas são sugestões iniciais para validação."],
   ["Operadoras",M.nicho+". Amil = 326305."],
   ["Atualização mensal","O robô baixa as bases da ANS, só reprocessa o que mudou e publica uma competência nova assim que IGR e NIP estão completos."]
  ].map(c=>`<div class="card"><h3>${c[0]}</h3><p>${c[1]}</p></div>`).join("");
  $("foot").innerHTML=`<b>Fontes (dados abertos ANS):</b> `+M.fontes.map(f=>`<a href="${f.url}" target="_blank">${f.nome}</a>${f.versao?` <span style="opacity:.7">(${f.versao})</span>`:""}`).join(" · ")
   +`<br>Panorama Mercadológico de NIP · Dados &amp; Insights · gerado automaticamente em ${M.gerado_em}.`;
}
render();
</script>
</body>
</html>"""


def _logo_b64():
    p = C.DIR_ASSETS / "logo_amil_branco.png"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""


def gerar_html(dados: dict, caminho_saida):
    dados = dict(dados)
    dados["meta"] = dict(dados["meta"], gerado_em=datetime.now().strftime("%d/%m/%Y %H:%M"))
    js = json.dumps(dados, ensure_ascii=False, separators=(",", ":"),
                    default=lambda o: float(o) if hasattr(o, "__float__") else str(o)).replace("</", "<\\/")
    html = TEMPLATE.replace("__DADOS__", js).replace("__LOGO__", _logo_b64())
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(html, encoding="utf-8")
    return caminho_saida
