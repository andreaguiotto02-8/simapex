# -*- coding: utf-8 -*-
PAGINA = r"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Simapex</title>
<link rel="icon" href="/favicon.ico"><link rel="icon" type="image/png" href="/icona-192.png"><link rel="apple-touch-icon" href="/icona-192.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0e1116">
<style>
:root{--bg:#0e1116;--card:#171c24;--line:#2a3140;--tx:#e8ecf2;--mu:#98a2b3;--ac:#ff5a1f;--ok:#2ecc71;--ko:#ff4d4d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.45 system-ui,Segoe UI,Arial,sans-serif}
header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:0;letter-spacing:.5px}.v{color:var(--mu);font-size:13px}
.pill{padding:4px 10px;border-radius:99px;font-size:13px;background:#2a3140}.pill.on{background:#12391f;color:var(--ok)}
.sp{flex:1}button{font:inherit;color:var(--tx);background:#232a36;border:1px solid var(--line);border-radius:10px;padding:8px 14px;cursor:pointer}
button.pri{background:var(--ac);border-color:var(--ac);color:#fff}button.ok{background:#12391f;border-color:#1f6b3b}button.ko{background:#3d1717;border-color:#7a2a2a}
button.sel{outline:2px solid var(--tx)}
nav{display:flex;gap:8px;padding:12px 16px 0}nav button{border-radius:10px 10px 0 0}nav button.act{background:var(--ac);border-color:var(--ac);color:#fff}
main{padding:16px;max-width:900px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:14px}
.card h2{font-size:17px;margin:0 0 6px}.mu{color:var(--mu)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.k{background:#10141b;border:1px solid var(--line);border-radius:10px;padding:8px 10px}.k b{display:block;font-size:22px}.k span{color:var(--mu);font-size:12px}
textarea{width:100%;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px;font:inherit;min-height:44px}
ol{margin:6px 0 10px 20px;padding:0}.row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:5px 6px;border-bottom:1px solid var(--line)}
.st{font-size:13px;margin-left:8px}.st.ok{color:var(--ok)}.st.ko{color:var(--ko)}
</style></head><body>
<header><h1>SIMAPEX</h1><span class="v" id="ver">v__VERSIONE__</span><span class="pill" id="acc">ACC non collegato</span><span class="sp"></span><button id="chiudi">Chiudi programma</button></header>
<nav><button id="tg" class="act">Gioca</button><button id="ts">Sviluppo</button></nav>
<main>
<div id="agg" class="card" hidden style="border-color:var(--ac)"><b>C'è una versione nuova di Simapex: <span id="aggv"></span></b><div class="row"><button class="pri" id="aggb">Scarica la versione nuova</button></div><div class="mu">Chiudi Simapex, apri il file scaricato e cancella quello vecchio.</div></div>
<section id="gioca">
 <div class="card"><h2>Funzioni confermate</h2><p class="mu">Qui compariranno le funzioni che hai provato nella sezione Sviluppo e confermato. Per ora non ce n'è nessuna: quando vuoi solo guidare, usa ACC normalmente.</p></div>
</section>
<section id="svil" hidden>
 <div class="card"><h2>Dati in diretta</h2><p class="mu" id="msg">Apri ACC ed entra in pista per vedere i dati.</p>
  <div class="grid" id="dati"></div></div>
 <div class="card"><h2>Prove da fare</h2><p class="mu">Fai le prove una alla volta. Per ognuna tocca «Funziona» o «Non funziona» e, se serve, scrivi una nota. Alla fine tocca «Copia risultati» e incollali nella chat con Claude.</p><div id="prove"></div>
  <div class="row"><button class="pri" id="invia">Invia a Claude</button><button id="copia">Copia risultati</button><button id="azzera">Azzera le prove</button></div><div class="st" id="copiato"></div></div>
 <div class="card" id="claudeBox"><h2>Collegamento a Claude (API)</h2><p class="mu" id="claudeSt">Non collegato. Incolla qui la chiave che inizia con sk-ant- (resta solo su questo PC).</p><div class="row"><input id="claudeChiave" type="password" autocomplete="off" placeholder="sk-ant-..." style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"><button class="pri" id="claudeSalva">Salva</button><button id="claudeProva">Prova</button></div><div class="st" id="claudeMsg"></div></div>
 <div class="card" id="chiaveBox" hidden><h2>Chiave di accesso per l'invio</h2><p class="mu">Serve una volta sola. Incolla qui la chiave di GitHub che ti ha dato Claude.</p><div class="row"><input id="chiave" type="password" autocomplete="off" placeholder="Incolla la chiave" style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"><button class="pri" id="salvaChiave">Salva</button></div><div class="st" id="chiaveMsg"></div></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);
let ultimo={}, setup={};
const PROVE=[
 {id:"apre",t:"Il programma si apre",p:["Fai doppio clic su Simapex.exe.","Si apre una pagina nel browser con la scritta SIMAPEX in alto."],a:"In alto vedi il numero di versione."},
 {id:"acc",t:"Riconosce ACC",p:["Apri Assetto Corsa Competizione ed entra in una sessione di pratica, in pista.","Guarda in alto in questa pagina."],a:"La scritta diventa verde («ACC collegato») e sotto «Dati in diretta» compaiono auto e pista giuste."},
 {id:"dati",t:"Legge i dati mentre guidi",p:["Guida qualche secondo.","Confronta velocità, marcia e giri motore con quelli del cruscotto di ACC.","Guarda carburante e pressioni gomme (in psi)."],a:"I numeri coincidono con quelli del gioco, con differenze piccolissime."},
 {id:"giri",t:"Legge i tempi dei giri",p:["Completa almeno un giro intero.","Guarda «Ultimo giro» e «Miglior giro»."],a:"Sono uguali ai tempi mostrati da ACC."},
 {id:"setup",t:"Trova i tuoi setup",p:["In ACC salva un setup (anche quello di base) per un'auto e una pista.","Torna qui: sotto «Setup trovati» compare l'elenco."],a:"Vedi auto, pista e nome del file che hai salvato."}
];
function carica(){try{return JSON.parse(localStorage.getItem("simapex_prove")||"{}")}catch(e){return {}}}
function salva(r){try{localStorage.setItem("simapex_prove",JSON.stringify(r))}catch(e){}autoInvia()}
let tAuto=null;function autoInvia(){if(!ultimo.invio_configurato)return;clearTimeout(tAuto);tAuto=setTimeout(async()=>{try{const p=raccogli();p.automatico=true;const r=await fetch("/api/invia",{method:"POST",body:JSON.stringify(p)});const j=await r.json();$("copiato").textContent=j.ok?"Inviato a Claude in automatico ("+new Date().toLocaleTimeString("it-IT")+").":"Invio automatico non riuscito: "+j.errore}catch(e){}},4000)}
function istantanea(){const u=ultimo;return {collegato:u.collegato,auto:u.auto,pista:u.pista,velocita:u.velocita,marcia:u.marcia,giri_motore:u.giri_motore,carburante:u.carburante,pressioni:u.pressioni,temp_gomme:u.temp_gomme,ultimo_giro:u.ultimo_giro,miglior_giro:u.miglior_giro,giri_completati:u.giri_completati,stato_gioco:u.stato_gioco,setup_trovati:(setup.file||[]).length}}
function disegnaProve(){const r=carica();$("prove").innerHTML=PROVE.map((p,i)=>{const x=r[p.id]||{};return `<div class="card" style="background:#10141b"><b>${i+1}. ${p.t}</b><span class="st ${x.s==='ok'?'ok':x.s==='ko'?'ko':''}">${x.s==='ok'?'Funziona':x.s==='ko'?'Non funziona':''}</span><ol>${p.p.map(s=>`<li>${s}</li>`).join("")}</ol><div class="mu">Cosa deve succedere: ${p.a}</div><div class="row"><button class="ok ${x.s==='ok'?'sel':''}" data-p="${p.id}" data-s="ok">Funziona</button><button class="ko ${x.s==='ko'?'sel':''}" data-p="${p.id}" data-s="ko">Non funziona</button></div><textarea data-n="${p.id}" placeholder="Nota (facoltativa)">${(x.n||"").replace(/</g,"&lt;")}</textarea></div>`}).join("")}
$("prove").addEventListener("click",e=>{const b=e.target.closest("button[data-p]");if(!b)return;const r=carica();const x=r[b.dataset.p]||{};x.s=b.dataset.s;x.snap=istantanea();r[b.dataset.p]=x;salva(r);const nn=document.querySelectorAll("textarea[data-n]");nn.forEach(t=>{const q=r[t.dataset.n]||{};q.n=t.value;r[t.dataset.n]=q});salva(r);disegnaProve()});
$("prove").addEventListener("input",e=>{const t=e.target.closest("textarea[data-n]");if(!t)return;const r=carica();const x=r[t.dataset.n]||{};x.n=t.value;r[t.dataset.n]=x;salva(r)});
$("azzera").onclick=()=>{salva({});disegnaProve()};
$("copia").onclick=async()=>{const r=carica();let t="Risultati prove Simapex "+($("ver").textContent)+"\n";PROVE.forEach((p,i)=>{const x=r[p.id]||{};t+=`\n${i+1}. ${p.t}: ${x.s==='ok'?'FUNZIONA':x.s==='ko'?'NON FUNZIONA':'non provata'}`;if(x.n)t+=` — nota: ${x.n}`;if(x.snap&&x.s)t+=`\n   dati al momento: ${JSON.stringify(x.snap)}`});t+="\n";try{await navigator.clipboard.writeText(t);$("copiato").textContent="Copiato: incollalo nella chat"}catch(e){const a=document.createElement("textarea");a.value=t;document.body.appendChild(a);a.select();document.execCommand("copy");a.remove();$("copiato").textContent="Copiato: incollalo nella chat"}};
function raccogli(){const r=carica();return {ora:new Date().toISOString(),versione:$("ver").textContent,prove:PROVE.map(p=>{const x=r[p.id]||{};return {id:p.id,titolo:p.t,stato:x.s==="ok"?"funziona":x.s==="ko"?"non funziona":"non provata",nota:x.n||"",dati_al_momento:x.snap||null}})}}
$("invia").onclick=async()=>{if(!ultimo.invio_configurato){$("chiaveBox").hidden=false;$("copiato").textContent="Prima serve la chiave di accesso (qui sotto).";return}
 $("copiato").textContent="Invio in corso...";try{const r=await fetch("/api/invia",{method:"POST",body:JSON.stringify(raccogli())});const j=await r.json();$("copiato").textContent=j.ok?"Inviato a Claude. Scrivi «controlla» nella chat.":"Invio non riuscito: "+j.errore}catch(e){$("copiato").textContent="Invio non riuscito: il programma non risponde."}};
$("salvaChiave").onclick=async()=>{const v=$("chiave").value.trim();if(!v){$("chiaveMsg").textContent="Incolla prima la chiave.";return}
 try{const r=await fetch("/api/chiave",{method:"POST",body:JSON.stringify({token:v})});const j=await r.json();if(j.ok){$("chiave").value="";$("chiaveBox").hidden=true;ultimo.invio_configurato=true;$("copiato").textContent="Chiave salvata. Ora tocca «Invia a Claude».";}else $("chiaveMsg").textContent=j.errore}catch(e){$("chiaveMsg").textContent="Non sono riuscito a salvare."}};
function aggiornaClaudeSt(){$("claudeSt").textContent=ultimo.claude_configurato?"Chiave salvata su questo PC. Tocca Prova per controllare che funzioni.":"Non collegato. Incolla qui la chiave che inizia con sk-ant- (resta solo su questo PC)."}
$("claudeSalva").onclick=async()=>{const v=$("claudeChiave").value.trim();if(!v){$("claudeMsg").textContent="Incolla prima la chiave.";return}
 try{const r=await fetch("/api/claude-chiave",{method:"POST",body:JSON.stringify({chiave:v})});const j=await r.json();if(j.ok){$("claudeChiave").value="";ultimo.claude_configurato=true;aggiornaClaudeSt();$("claudeMsg").textContent="Chiave salvata. Ora tocca Prova."}else $("claudeMsg").textContent=j.errore}catch(e){$("claudeMsg").textContent="Non sono riuscito a salvare."}};
$("claudeProva").onclick=async()=>{$("claudeMsg").textContent="Sto chiamando Claude...";try{const r=await fetch("/api/claude-prova",{method:"POST",body:"{}"});const j=await r.json();$("claudeMsg").textContent=j.ok?"Funziona! Claude risponde: "+j.risposta:"Non funziona: "+j.errore}catch(e){$("claudeMsg").textContent="Il programma non risponde."}};
async function controllaAgg(){try{const r=await fetch("/api/aggiornamenti");const j=await r.json();if(j.disponibile){$("aggv").textContent="v"+j.ultima;$("agg").hidden=false;$("aggb").onclick=()=>window.open(j.scarica,"_blank")}}catch(e){}}
function k(l,v){return `<div class="k"><b>${v===undefined||v===""?"—":v}</b><span>${l}</span></div>`}
function disegnaDati(){const u=ultimo,a=$("acc");a.textContent=u.collegato?"ACC collegato":"ACC non collegato";a.className="pill"+(u.collegato?" on":"");
 if(!u.collegato){$("msg").textContent="Apri ACC ed entra in pista per vedere i dati.";$("dati").innerHTML="";return}
 $("msg").textContent="Stato del gioco: "+(u.stato_gioco||"?");const p=u.pressioni||[],t=u.temp_gomme||[];
 $("dati").innerHTML=k("Auto",u.auto)+k("Pista",u.pista)+k("Velocità (km/h)",u.velocita)+k("Marcia",u.marcia)+k("Giri motore",u.giri_motore)+k("Carburante (L)",u.carburante)+k("Ultimo giro",u.ultimo_giro)+k("Miglior giro",u.miglior_giro)+k("Giri completati",u.giri_completati)+k("Pressioni psi (AS AD PS PD)",p.join(" · "))+k("Temp. gomme °C (AS AD PS PD)",t.join(" · "))+(setup.cartella===null?k("Setup trovati","cartella non trovata"):k("Setup trovati",(setup.file||[]).length))+((setup.file||[]).length?`<div class="k" style="grid-column:1/-1"><span>Setup trovati (auto · pista · file)</span><table>${setup.file.slice(0,12).map(f=>`<tr><td>${f.auto}</td><td>${f.pista}</td><td>${f.nome}</td><td>${f.valido?"ok":"formato non riconosciuto"}</td></tr>`).join("")}</table></div>`:"")}
async function giro(){try{const r=await fetch("/api/stato");ultimo=await r.json();disegnaDati();aggiornaClaudeSt()}catch(e){}}
let sigSetup=null;async function giroSetup(){try{const r=await fetch("/api/setup");setup=await r.json();disegnaDati();if(ultimo.invio_configurato){const sg=(setup.file||[]).map(f=>f.auto+f.pista+f.nome+f.modificato).join("|");if(sigSetup!==null&&sg!==sigSetup)autoInvia();if(sigSetup===null)autoInvia();sigSetup=sg}}catch(e){}}
$("tg").onclick=()=>{$("gioca").hidden=false;$("svil").hidden=true;$("tg").className="act";$("ts").className=""};
$("ts").onclick=()=>{$("gioca").hidden=true;$("svil").hidden=false;$("ts").className="act";$("tg").className=""};
$("chiudi").onclick=async()=>{try{await fetch("/api/chiudi",{method:"POST"})}catch(e){}document.body.innerHTML="<p style='padding:30px'>Programma chiuso. Puoi chiudere questa pagina.</p>"};
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}
disegnaProve();giro();giroSetup();controllaAgg();setInterval(controllaAgg,3600000);setInterval(giro,500);setInterval(giroSetup,5000);
</script></body></html>
"""
