# -*- coding: utf-8 -*-
PAGINA = r"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Simapex</title>
<link rel="icon" href="/favicon.ico"><link rel="icon" type="image/png" href="/icona-192.png"><link rel="apple-touch-icon" href="/icona-192.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0e1116">
<style>
:root{--bg:#0e1116;--card:#171c24;--line:#2a3140;--tx:#e8ecf2;--mu:#98a2b3;--ac:#ff5a1f;--ok:#2ecc71;--ko:#ff4d4d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:clamp(16px,1.3vw,22px)/1.45 system-ui,Segoe UI,Arial,sans-serif}
header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid var(--line)}
h1{font-size:1.25em;margin:0;letter-spacing:.5px}.v{color:var(--mu);font-size:.8em}
.pill{padding:4px 10px;border-radius:99px;font-size:.8em;background:#2a3140}.pill.on{background:#12391f;color:var(--ok)}
.sp{flex:1}button{font:inherit;color:var(--tx);background:#232a36;border:1px solid var(--line);border-radius:10px;padding:8px 14px;cursor:pointer}
button.pri{background:var(--ac);border-color:var(--ac);color:#fff}button.ok{background:#12391f;border-color:#1f6b3b}button.ko{background:#3d1717;border-color:#7a2a2a}
button.sel{outline:2px solid var(--tx)}
nav{display:flex;gap:8px;padding:12px 16px 0}nav button{border-radius:10px 10px 0 0}nav button.act{background:var(--ac);border-color:var(--ac);color:#fff}
main{padding:16px 20px;max-width:none}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:14px}
.card h2{font-size:1.1em;margin:0 0 6px}.mu{color:var(--mu)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.k{background:#10141b;border:1px solid var(--line);border-radius:10px;padding:8px 10px}.k b{display:block;font-size:1.4em;overflow-wrap:anywhere;line-height:1.15}.k b.t{font-size:1em}.k{min-width:0}.k span{color:var(--mu);font-size:.75em}
textarea{width:100%;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px;font:inherit;min-height:44px}
ol{margin:6px 0 10px 20px;padding:0}.row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}table{width:100%;border-collapse:collapse;font-size:.9em}td,th{text-align:left;padding:5px 6px;border-bottom:1px solid var(--line)}
.st{font-size:13px;margin-left:8px}.st.ok{color:var(--ok)}.st.ko{color:var(--ko)}
.cols{display:grid;grid-template-columns:1fr;gap:0 18px;align-items:start}@media(min-width:900px){.cols{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}}.cols>div{min-width:0}.grid{grid-template-columns:repeat(auto-fit,minmax(9em,1fr))}</style></head><body>
<header><h1>SIMAPEX</h1><span class="v" id="ver">v__VERSIONE__</span><span class="pill" id="acc">ACC non collegato</span><span class="sp"></span><button id="chiudi">Chiudi programma</button></header>
<nav><button id="tg" class="act">Gioca</button><button id="ts">Sviluppo</button></nav>
<main>
<div id="agg" class="card" hidden style="border-color:var(--ac)"><b>C'è una versione nuova di Simapex: <span id="aggv"></span></b><div class="row"><button class="pri" id="aggb">Scarica la versione nuova</button></div><div class="mu">Chiudi Simapex, apri il file scaricato e cancella quello vecchio.</div></div>
<section id="gioca">
 <div class="card"><h2>Funzioni confermate</h2><p class="mu">Qui compariranno le funzioni che hai provato nella sezione Sviluppo e confermato. Per ora non ce n'è nessuna: quando vuoi solo guidare, usa ACC normalmente.</p></div>
</section>
<section id="svil" hidden>
<div class="cols"><div>
 <div class="card"><h2>Dati in diretta</h2><p class="mu" id="msg">Apri ACC ed entra in pista per vedere i dati.</p>
  <div class="grid" id="dati"></div></div>
 <div class="card"><h2>Programma di prova (una giornata in pista)</h2><p class="mu">Fai le fasi in ordine, come se fosse una normale giornata di guida: non serve guardare il programma mentre guidi. Per ognuna tocca «Funziona» o «Non funziona» e, se serve, scrivi una nota. I risultati arrivano a Claude da soli.</p><div id="prove"></div>
  <div class="row"><button class="pri" id="invia">Invia a Claude</button><button id="copia">Copia risultati</button><button id="azzera">Azzera le prove</button></div><div class="st" id="copiato"></div></div>
 </div><div>
 <div class="card" id="assBox"><h2>Assistente setup (prova)</h2><p class="mu">Scegli un setup salvato in ACC, racconta come va la macchina e Claude propone poche modifiche. Il programma crea un setup NUOVO nella lista di ACC: l'originale non viene toccato.</p>
 <div class="row"><select id="assFile" style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"></select></div>
 <div class="row"><textarea id="assSens" rows="3" placeholder="Come va la macchina? Per esempio: sottosterza in ingresso curva, le gomme dietro scaldano troppo..." style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"></textarea></div>
 <div class="row"><button id="assMic">🎤 Parla</button><button class="pri" id="assBase">Crea il mio setup base</button><button id="assVai">Migliora (una modifica alla volta)</button></div><p class="mu" id="assStile"></p>
 <div class="st" id="assMsg"></div><div id="assRis"></div></div>
 <div class="card" id="sesBox"><h2>Sessioni</h2><p class="mu">Si salvano da sole mentre guidi. Tocca una sessione per vedere il report.</p><div id="sesLista" class="mu">Nessuna sessione ancora: guida qualche giro.</div><div id="rep"></div></div>
 <div class="card" id="claudeBox"><h2>Collegamento a Claude (API)</h2><p class="mu" id="claudeSt">Non collegato. Incolla qui la chiave che inizia con sk-ant- (resta solo su questo PC).</p><div class="row"><input id="claudeChiave" type="password" autocomplete="off" placeholder="sk-ant-..." style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"><button class="pri" id="claudeSalva">Salva</button><button id="claudeProva">Prova</button></div><div class="st" id="claudeMsg"></div></div>
 <div class="card" id="chiaveBox" hidden><h2>Chiave di accesso per l'invio</h2><p class="mu">Serve una volta sola. Incolla qui la chiave di GitHub che ti ha dato Claude.</p><div class="row"><input id="chiave" type="password" autocomplete="off" placeholder="Incolla la chiave" style="flex:1;min-width:220px;background:#10141b;color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px"><button class="pri" id="salvaChiave">Salva</button></div><div class="st" id="chiaveMsg"></div></div>
</div></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);
let ultimo={}, setup={};
const PROVE=[
 {"id": "apre", "g": "1 · PRIMA DI PARTIRE", "t": "Il programma è aggiornato", "p": ["Apri Simapex.exe: si aggiorna da solo.", "Guarda il numero di versione in alto a sinistra."], "a": "Vedi v0.11.2."},
 {"id": "setup", "t": "Salva il tuo setup di partenza", "p": ["In ACC salva il setup che usi adesso con un nome che riconosci, per esempio «Base».", "Torna qui e guarda «Setup trovati» nel riquadro dell'assistente (sotto)."], "a": "Il tuo setup compare nella lista con auto e pista giuste."},
 {"id": "acc", "g": "2 · PRIMO TURNO: IMPARI IL CIRCUITO", "t": "Simapex riconosce ACC", "p": ["Lascia Simapex aperto, apri ACC ed entra in pista (pratica) con il tuo setup «Base».", "Guida normalmente, senza pensare al programma.", "Dopo qualche secondo guarda i dati in diretta."], "a": "In alto compare «ACC collegato» e velocità, marcia, giri motore e carburante coincidono con il cruscotto di ACC."},
 {"id": "giri", "t": "Legge i tempi dei giri", "p": ["Fai almeno 8 giri, senza passare dai box (così si disegna anche il circuito).", "Ogni tanto guarda «Ultimo giro» e «Miglior giro»."], "a": "I tempi sono uguali a quelli di ACC."},
 {"id": "mappa", "t": "Si disegna il circuito", "p": ["Finiti i giri, apri il riquadro «Sessioni» e tocca la sessione."], "a": "Compare il disegno della pista e somiglia al circuito vero."},
 {"id": "base", "g": "3 · IL SETUP BASE CON L'IA", "t": "Crea il tuo setup base", "p": ["Nel riquadro «Assistente setup» scegli il setup «Base».", "Scrivi (o parla con 🎤) cosa non va: per esempio «sottosterza in ingresso», «posteriore instabile in frenata», «gomme dietro troppo calde». Più sei preciso meglio è.", "Tocca «Crea il mio setup base» e aspetta qualche secondo."], "a": "Compaiono le modifiche con il motivo di ognuna e il nome di un file nuovo (finisce con «Simapex 1»). L'assistente usa anche le gomme e il tuo stile del primo turno."},
 {"id": "carica", "t": "ACC accetta il setup nuovo", "p": ["In ACC, nella lista dei setup, cerca il file nuovo e caricalo."], "a": "Il file si vede e si carica senza errori. Se ACC non lo mostra o dà errore, scrivilo nella nota."},
 {"id": "mic", "t": "Microfono", "p": ["Nell'assistente tocca 🎤 Parla, consenti il microfono e racconta come va la macchina."], "a": "Quello che dici compare scritto nella casella. Se non funziona, scrivi a mano e segna «Non funziona»."},
 {"id": "guida1", "g": "4 · SECONDO TURNO: CON IL SETUP NUOVO", "t": "Guida con il setup nuovo", "p": ["Esci in pista con il setup «Simapex 1» e fai almeno 8 giri, sempre senza box.", "Poi tocca «Meglio», «Uguale» o «Peggio» sotto le modifiche dell'assistente.", "Nella nota scrivi cosa senti di diverso."], "a": "L'esito è segnato; la macchina deve essere più guidabile di prima. Se no, scrivi cosa non va."},
 {"id": "blocchi", "t": "Rileva i blocchi in frenata", "p": ["In questo turno frena una volta ogni tanto più forte del solito, fino a bloccare una ruota (almeno 3 volte).", "Guarda il report della sessione."], "a": "Il report dice che hai bloccato, con la ruota giusta. Se dice zero blocchi o ne segna troppi, scrivilo."},
 {"id": "zone", "t": "Temperature gomme a 3 zone", "p": ["Nel report guarda la temperatura delle gomme: interna, centro, esterna."], "a": "Compaiono le 3 zone di ogni gomma, con valori sensati (tra 60 e 110 gradi dopo qualche giro)."},
 {"id": "migliora1", "g": "5 · MIGLIORAMENTO DEL SETUP", "t": "Primo miglioramento (una modifica alla volta)", "p": ["Scrivi il problema che ti dà più fastidio adesso.", "Tocca «Migliora» e carica in ACC il file nuovo.", "Fai 5 o più giri e segna Meglio, Uguale o Peggio."], "a": "L'assistente propone poche modifiche (massimo 3) legate al problema che hai scritto."},
 {"id": "migliora2", "t": "Secondo miglioramento", "p": ["Ripeti con il problema successivo."], "a": "Come sopra: poche modifiche, e l'assistente tiene conto dell'esito precedente."},
 {"id": "sessioni", "g": "6 · A FINE GIORNATA", "t": "Le sessioni si sono salvate da sole", "p": ["Apri il riquadro «Sessioni».", "Controlla che ci siano i turni che hai fatto, con auto, pista, data e giri."], "a": "Ogni turno è nell'elenco, con il miglior giro giusto."},
 {"id": "dettaglio", "t": "Dettaglio della sessione", "p": ["Tocca una sessione.", "Controlla la tabella dei giri, il carburante, i blocchi, le gomme e i setup provati."], "a": "I tempi coincidono con ACC; i giri lenti o sporchi sono segnati; il report si capisce e ti è utile."}
];
function carica(){try{return JSON.parse(localStorage.getItem("simapex_prove")||"{}")}catch(e){return {}}}
function salva(r){try{localStorage.setItem("simapex_prove",JSON.stringify(r))}catch(e){}autoInvia()}
let tAuto=null;function autoInvia(){if(!ultimo.invio_configurato)return;clearTimeout(tAuto);tAuto=setTimeout(async()=>{try{const p=raccogli();p.automatico=true;const r=await fetch("/api/invia",{method:"POST",body:JSON.stringify(p)});const j=await r.json();$("copiato").textContent=j.ok?"Inviato a Claude in automatico ("+new Date().toLocaleTimeString("it-IT")+").":"Invio automatico non riuscito: "+j.errore}catch(e){}},4000)}
function istantanea(){const u=ultimo;return {collegato:u.collegato,auto:u.auto,pista:u.pista,velocita:u.velocita,marcia:u.marcia,giri_motore:u.giri_motore,carburante:u.carburante,pressioni:u.pressioni,temp_gomme:u.temp_gomme,ultimo_giro:u.ultimo_giro,miglior_giro:u.miglior_giro,giri_completati:u.giri_completati,stato_gioco:u.stato_gioco,setup_trovati:(setup.file||[]).length}}
function disegnaProve(){const r=carica();$("prove").innerHTML=PROVE.map((p,i)=>{const x=r[p.id]||{};return `${p.g?`<h3 style="margin:14px 0 6px">${p.g}</h3>`:""}<div class="card" style="background:#10141b"><b>${i+1}. ${p.t}</b><span class="st ${x.s==='ok'?'ok':x.s==='ko'?'ko':''}">${x.s==='ok'?'Funziona':x.s==='ko'?'Non funziona':''}</span><ol>${p.p.map(s=>`<li>${s}</li>`).join("")}</ol><div class="mu">Cosa deve succedere: ${p.a}</div><div class="row"><button class="ok ${x.s==='ok'?'sel':''}" data-p="${p.id}" data-s="ok">Funziona</button><button class="ko ${x.s==='ko'?'sel':''}" data-p="${p.id}" data-s="ko">Non funziona</button></div><textarea data-n="${p.id}" placeholder="Nota (facoltativa)">${(x.n||"").replace(/</g,"&lt;")}</textarea></div>`}).join("")}
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
let assId=null;
function riempiAss(){const s=$("assFile");const f=(setup.file||[]).filter(x=>x.valido);const sig=f.map(x=>x.auto+x.pista+x.nome).join("|");if(s.dataset.sig===sig)return;s.dataset.sig=sig;const cur=s.value;s.innerHTML=f.length?f.map(x=>`<option value="${x.auto}/${x.pista}/${x.nome}">${bello(x.auto)} · ${bello(x.pista)} · ${x.nome}</option>`).join(""):'<option value="">Nessun setup trovato</option>';if(cur)s.value=cur}
async function assChiedi(modo){const file=$("assFile").value;if(!file){$("assMsg").textContent="Salva prima un setup in ACC.";return}
 $("assMsg").textContent="Claude sta lavorando (qualche secondo)...";$("assRis").innerHTML="";try{const r=await fetch("/api/assistente/proponi",{method:"POST",body:JSON.stringify({file:file,sensazioni:$("assSens").value,modo:modo})});const j=await r.json();
 if(!j.ok){$("assMsg").textContent="Non riuscito: "+j.errore;return}
 $("assMsg").textContent="";assId=j.id||null;
 let h=`<div class="k" style="margin-top:8px"><b class="t">${j.problema||"Proposta"}</b><span>${j.spiegazione||""}</span></div>`;
 if(j.modifiche.length){h+="<table>"+j.modifiche.map(m=>`<tr><td>${m.nome}</td><td>${m.click>0?"+":""}${m.click} click</td><td>${m.motivo}</td></tr>`).join("")+"</table>";
  h+=`<p><b>Setup creato:</b> ${j.nuovo_file}<br>In ACC apri la lista dei setup, scegli questo nome e caricalo.</p><p class="mu">${j.cosa_aspettarsi||""}</p>
  <div class="row"><span>Dopo averlo provato:</span><button data-e="meglio">Meglio</button><button data-e="uguale">Uguale</button><button data-e="peggio">Peggio</button></div>`}
 else h+=`<p>Nessuna modifica proposta.</p><p class="mu">${j.cosa_aspettarsi||""}</p>`;
 $("assRis").innerHTML=h;
 }catch(e){$("assMsg").textContent="Il programma non risponde."}}
$("assBase").onclick=()=>assChiedi("base");$("assVai").onclick=()=>assChiedi("migliora");
let sesAperta=null;
function dt(ts){return ts?new Date(ts*1000).toLocaleString("it-IT",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):""}
async function giroReport(){try{const r=await fetch("/api/sessioni");const l=(await r.json()).sessioni||[];if(!l.length)return;
 $("sesLista").innerHTML="<table>"+l.map(x=>`<tr data-s="${x.id}" style="cursor:pointer"><td>${dt(x.data)}</td><td>${bello(x.auto)} · ${bello(x.pista)}</td><td>${x.giri} giri</td><td>${x.miglior_giro}</td><td>${x.blocchi?x.blocchi+" blocchi":""}</td></tr>`).join("")+"</table>";
 if(sesAperta===null||sesAperta===l[0].id)apriSessione(l[0].id)}catch(e){}}
async function apriSessione(id){sesAperta=id;try{const r=await fetch("/api/sessione?id="+id);const j=(await r.json()).sessione;if(!j){$("rep").innerHTML="";return}
 const e=t=>String(t).replace(/</g,"&lt;");
 let h=`<h3 style="margin:12px 0 4px">${e(bello(j.auto))} · ${e(bello(j.pista))} · ${dt(j.data)}</h3><ul>${j.note.map(n=>"<li>"+e(n)+"</li>").join("")}</ul>`;
 h+="<table><tr><th>Giro</th><th>Tempo</th><th>Carb.</th><th></th></tr>"+j.dettaglio_giri.map(x=>`<tr><td>${x.giro}</td><td>${x.tempo}</td><td>${x.carburante===null?"—":x.carburante}</td><td>${x.pulito?"":"lento/sporco "}${x.blocchi?"🔒"+x.blocchi:""}</td></tr>`).join("")+"</table>";
 if(j.carburante_inizio!==null)h+=`<p class="mu">Carburante: da ${j.carburante_inizio} a ${j.carburante_fine} L.</p>`;
 if(j.quaderno&&j.quaderno.length)h+="<p><b>Setup provati su questa pista</b></p><table>"+j.quaderno.map(q=>`<tr><td>${e(q.nuovo||"")}</td><td>${e(q.problema||"")}</td><td>${e(q.esito||"da segnare")}</td></tr>`).join("")+"</table>";
 $("rep").innerHTML=h;mappa(j.pista)}catch(x){}}
async function mappa(pista){try{const r=await fetch("/api/pista?nome="+encodeURIComponent(pista));const t=(await r.json()).pista;const box=document.createElement("div");box.className="k";box.style.marginTop="10px";
 if(!t){box.innerHTML='<span>Mappa: si disegna da sola dopo un giro completo guidato su questa pista.</span>';$("rep").prepend(box);return}
 const X=t.x,Z=t.z,mx=Math.min(...X),Mx=Math.max(...X),mz=Math.min(...Z),Mz=Math.max(...Z),W=Math.max(Mx-mx,Mz-mz)||1;
 const pts=X.map((x,i)=>((x-mx)/W*280+10).toFixed(1)+","+((Mz-Z[i])/W*280+10).toFixed(1)).join(" ");
 box.innerHTML=`<svg viewBox="0 0 300 300" style="max-width:320px;width:100%"><polygon points="${pts}" fill="none" stroke="#e8ecf2" stroke-width="5" stroke-linejoin="round"/></svg><span>Circuito (${t.lunghezza_m} m)</span>`;$("rep").prepend(box)}catch(e){}}
$("sesLista").addEventListener("click",e=>{const t=e.target.closest("tr[data-s]");if(t)apriSessione(parseInt(t.dataset.s))});
async function giroStile(){try{const r=await fetch("/api/assistente");const j=await r.json();$("assStile").textContent=j.giri_registrati?"Giri registrati per imparare il tuo stile: "+j.giri_registrati+(j.stile?" (profilo pronto)":" (ne servono almeno 3 puliti)"):"Guida con Simapex aperto: registra in silenzio il tuo stile di guida, giro per giro."}catch(e){}}
$("assRis").addEventListener("click",async e=>{const b=e.target.closest("button[data-e]");if(!b||!assId)return;try{await fetch("/api/assistente/esito",{method:"POST",body:JSON.stringify({id:assId,esito:b.dataset.e})});$("assMsg").textContent="Segnato: "+b.dataset.e+". Il prossimo consiglio ne terrà conto."}catch(x){}});
(function(){const R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R){$("assMic").hidden=true;return}let rec=null,on=false;
 $("assMic").onclick=()=>{if(on){rec&&rec.stop();return}rec=new R();rec.lang="it-IT";rec.continuous=true;rec.interimResults=false;
  rec.onresult=ev=>{let t="";for(let i=ev.resultIndex;i<ev.results.length;i++)t+=ev.results[i][0].transcript+" ";$("assSens").value=($("assSens").value+" "+t).trim()};
  rec.onerror=ev=>{$("assMsg").textContent="Microfono: "+(ev.error==="not-allowed"?"consenti l'uso del microfono nella finestra.":ev.error)};
  rec.onend=()=>{on=false;$("assMic").textContent="🎤 Parla"};rec.start();on=true;$("assMic").textContent="⏹ Stop"}})();
async function controllaAgg(){try{const r=await fetch("/api/aggiornamenti");const j=await r.json();if(j.disponibile){$("aggv").textContent="v"+j.ultima;$("agg").hidden=false;$("aggb").onclick=()=>window.open(j.scarica,"_blank")}}catch(e){}}
function bello(s){if(!s)return s;return String(s).replace(/_/g," ").replace(/\b(gt\d|amg|bmw|ao|evo)\b/gi,m=>m.toUpperCase()).replace(/\b([a-z])/g,m=>m.toUpperCase())}
function k(l,v,t){return `<div class="k"><b${t?' class="t"':""}>${v===undefined||v===""?"—":v}</b><span>${l}</span></div>`}
function disegnaDati(){const u=ultimo,a=$("acc");a.textContent=u.collegato?"ACC collegato":"ACC non collegato";a.className="pill"+(u.collegato?" on":"");
 if(!u.collegato){$("msg").textContent="Apri ACC ed entra in pista per vedere i dati.";$("dati").innerHTML="";return}
 $("msg").textContent="Stato del gioco: "+(u.stato_gioco||"?");const p=u.pressioni||[],t=u.temp_gomme||[];
 $("dati").innerHTML=k("Auto",bello(u.auto),1)+k("Pista",bello(u.pista),1)+k("Velocità (km/h)",u.velocita)+k("Marcia",u.marcia)+k("Giri motore",u.giri_motore)+k("Carburante (L)",u.carburante)+k("Ultimo giro",u.ultimo_giro)+k("Miglior giro",u.miglior_giro)+k("Giri completati",u.giri_completati)+k("Pressioni psi (AS AD PS PD)",p.join(" · "),1)+k("Temp. gomme °C (AS AD PS PD)",t.join(" · "),1)+(setup.cartella===null?k("Setup trovati","cartella non trovata"):k("Setup trovati",(setup.file||[]).length))+((setup.file||[]).length?`<div class="k" style="grid-column:1/-1"><span>Setup salvati in ACC. Ogni riga: auto · pista · nome del setup · «letto» = il programma ha capito il file</span><table>${setup.file.slice(0,12).map(f=>`<tr><td>${bello(f.auto)}</td><td>${bello(f.pista)}</td><td>${f.nome}</td><td>${f.valido?"letto":"non riconosciuto"}</td></tr>`).join("")}</table></div>`:"")}
async function giro(){try{const r=await fetch("/api/stato");ultimo=await r.json();disegnaDati();aggiornaClaudeSt()}catch(e){}}
let sigSetup=null;async function giroSetup(){try{const r=await fetch("/api/setup");setup=await r.json();disegnaDati();riempiAss();if(ultimo.invio_configurato){const sg=(setup.file||[]).map(f=>f.auto+f.pista+f.nome+f.modificato).join("|");if(sigSetup!==null&&sg!==sigSetup)autoInvia();if(sigSetup===null)autoInvia();sigSetup=sg}}catch(e){}}
$("tg").onclick=()=>{$("gioca").hidden=false;$("svil").hidden=true;$("tg").className="act";$("ts").className=""};
$("ts").onclick=()=>{$("gioca").hidden=true;$("svil").hidden=false;$("ts").className="act";$("tg").className=""};
$("chiudi").onclick=async()=>{try{await fetch("/api/chiudi",{method:"POST"})}catch(e){}document.body.innerHTML="<p style='padding:30px'>Programma chiuso. Puoi chiudere questa pagina.</p>"};
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}
disegnaProve();giro();giroSetup();controllaAgg();setInterval(controllaAgg,3600000);setInterval(giro,500);setInterval(giroSetup,5000);giroStile();setInterval(giroStile,15000);giroReport();setInterval(giroReport,15000);
</script></body></html>
"""
