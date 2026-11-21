"use strict";
const $=id=>document.getElementById(id);
const esc=t=>String(t==null?"":t).replace(/&/g,"&amp;").replace(/</g,"&lt;");
let ST={}, FUN={}, SETUP={}, assId=null, schermo="guida", pistaMappa=null, tracciato=null, sesAperta=null, rifSel="precedente", ultimaSes=null;
let MODO="dev";try{MODO=localStorage.getItem("simapex_modo")||"dev"}catch(e){}

/* ---------- funzioni da provare (le stesse in Gioca e Sviluppo) ---------- */
const PROVE=[
 {id:"apre",g:"1 · PRIMA DI PARTIRE",t:"Il programma è aggiornato",p:["Apri Simapex.exe: se c'è una versione nuova compare «Sto aggiornando...» e si riapre da solo.","Guarda il numero di versione in alto."],a:"Vedi v__VERSIONE__."},
 {id:"setup",t:"Salva il tuo setup di partenza",p:["In ACC salva il setup che usi adesso con un nome che riconosci, per esempio «Base».","Apri la schermata Setup: guarda «Setup trovati in ACC»."],a:"Il tuo setup compare nella lista con auto e pista giuste."},
 {id:"acc",g:"2 · PRIMO TURNO: IMPARI IL CIRCUITO",t:"Schermata Guida: dati in diretta",p:["Lascia Simapex aperto sulla schermata Guida, apri ACC ed entra in pista con il tuo setup «Base».","Guida normalmente: ogni tanto guarda marcia, velocità, giri motore e pedali."],a:"«ACC collegato» in alto e i numeri coincidono con il cruscotto di ACC."},
 {id:"gomme",t:"Gomme: temperature e pressioni",p:["Guarda i 4 riquadri delle gomme a sinistra."],a:"Temperatura e pressione coincidono con quelle di ACC e il colore cambia (blu freddo, verde giusto, giallo caldo, rosso rovente)."},
 {id:"giri",t:"Tempi dei giri",p:["Fai almeno 8 giri, senza passare dai box (così si disegna anche il circuito).","Guarda «Ultimo» e «Migliore»."],a:"I tempi sono uguali a quelli di ACC."},
 {id:"delta",t:"Delta sul tuo giro migliore",p:["Dal secondo giro guarda il numero grande «Rispetto al tuo giro migliore»."],a:"È verde (con il segno meno) quando sei più veloce del tuo giro migliore in quel punto, rosso quando sei più lento."},
 {id:"carburante",t:"Carburante e giri che restano",p:["Dopo qualche giro guarda il riquadro del carburante."],a:"Consumo per giro e giri che restano sono credibili."},
 {id:"mappa",t:"Si disegna il circuito",p:["Finito il primo giro pulito guarda la mappa nella schermata Guida: compare un puntino che segue l'auto."],a:"Il disegno somiglia al circuito vero e il puntino è nel posto giusto."},
 {id:"base",g:"3 · IL SETUP BASE CON L'IA",t:"Crea il tuo setup base",p:["Nella schermata Setup scegli il setup «Base».","Scrivi (o parla con 🎤) cosa non va. Più sei preciso meglio è.","Tocca «Crea il mio setup base» e aspetta."],a:"Compaiono le modifiche con il motivo e il nome di un file nuovo («... Simapex 1»). I suggerimenti su ABS, controllo trazione e mappa motore compaiono a parte."},
 {id:"carica",t:"ACC accetta il setup nuovo",p:["In ACC, nella lista dei setup, cerca il file nuovo e caricalo."],a:"Il file si vede e si carica senza errori."},
 {id:"mic",t:"Microfono",p:["Nella schermata Setup tocca 🎤 Parla e racconta come va la macchina."],a:"Quello che dici compare scritto nella casella."},
 {id:"guida1",g:"4 · SECONDO TURNO: CON IL SETUP NUOVO",t:"Guida con il setup nuovo",p:["Esci in pista con il setup «Simapex 1» e fai almeno 8 giri, senza box.","Nella schermata Setup, sotto «Setup provati», guarda l'esito deciso dal programma."],a:"Dopo almeno 4 giri puliti il programma scrive meglio, uguale o peggio con il motivo. La macchina deve essere più guidabile."},
 {id:"esito",t:"L'esito del setup è giusto",p:["Confronta l'esito del programma con quello che hai sentito."],a:"Il programma e le tue sensazioni vanno nella stessa direzione."},
 {id:"blocchi",t:"Rileva i blocchi in frenata",p:["Ogni tanto frena più forte del solito fino a bloccare una ruota (almeno 3 volte)."],a:"Compare la scritta rossa BLOCCO con la ruota giusta, e nel report i blocchi sono contati."},
 {id:"migliora1",g:"5 · MIGLIORAMENTO DEL SETUP",t:"Primo miglioramento (una modifica alla volta)",p:["Scrivi il problema che ti dà più fastidio adesso.","Tocca «Migliora» e carica in ACC il file nuovo. Fai 5 o più giri."],a:"L'assistente propone poche modifiche (massimo 3) legate al problema. L'esito arriva da solo."},
 {id:"migliora2",t:"Secondo miglioramento",p:["Ripeti con il problema successivo."],a:"Come sopra: poche modifiche, e l'assistente tiene conto dell'esito precedente."},
 {id:"sessioni",g:"6 · A FINE GIORNATA",t:"Le sessioni si salvano da sole",p:["Apri la schermata Sessioni."],a:"Ci sono i turni che hai fatto, con auto, pista, data e giri."},
 {id:"dettaglio",t:"Report della sessione",p:["Tocca una sessione: guarda la mappa, i tratti dove sei migliorato e peggiorato, i blocchi e la tabella dei giri."],a:"I tempi coincidono con ACC e il report si capisce e ti è utile."},
 {id:"confronto",t:"Confronto con la sessione precedente",p:["Nel report scegli «Sessione precedente» o «Tuo record»."],a:"La mappa si colora: verde dove sei più veloce, rosso dove perdi. I tratti principali sono scritti."}
];
const TITOLI={};PROVE.forEach(p=>TITOLI[p.id]=p.t);

/* ---------- utilità ---------- */
function tempoMs(ms){if(!ms||ms<=0||ms>36000000)return "—";const m=Math.floor(ms/60000),r=(ms%60000)/1000;return m+":"+(r<10?"0":"")+r.toFixed(3)}
function bello(s){if(!s)return s;return String(s).replace(/_/g," ").replace(/\b(gt\d|amg|bmw|ao|evo)\b/gi,m=>m.toUpperCase()).replace(/\b([a-z])/g,m=>m.toUpperCase())}
function dt(ts){return ts?new Date(ts*1000).toLocaleString("it-IT",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):""}
function sec(ms,seg){const v=(ms/1000);return (seg&&v>0?"+":"")+v.toFixed(2).replace("-","−")}
async function api(url,corpo){const r=await fetch(url,corpo!==undefined?{method:"POST",body:JSON.stringify(corpo)}:undefined);return r.json()}

/* ---------- modo Gioca / Sviluppo ---------- */
function applicaModo(){
 document.body.classList.toggle("dev",MODO==="dev");document.body.classList.toggle("gioca",MODO!=="dev");
 const b=$("modo");b.textContent=MODO==="dev"?"SVILUPPO":"GIOCA";b.className="modo "+(MODO==="dev"?"dev":"gioca");
 document.querySelectorAll("[data-f]").forEach(el=>{
  const f=el.dataset.f,x=FUN[f]||{};
  el.classList.toggle("nonok",x.s!=="ok");
  if(MODO==="dev"&&el.classList.contains("w")&&!el.classList.contains("g-blocco")&&!el.querySelector(":scope>.pallino")){
   const p=document.createElement("button");p.className="pallino";p.title="Segna se questa parte funziona";p.onclick=e=>{e.stopPropagation();apriPopup(el,p)};el.appendChild(p)}
  const p=el.querySelector(":scope>.pallino");if(p)p.className="pallino"+(x.s==="ok"?" ok":x.s==="ko"?" ko":"");
 });
 if(MODO!=="dev"&&schermo==="prove")vai("guida");
}
$("modo").onclick=()=>{MODO=MODO==="dev"?"gioca":"dev";try{localStorage.setItem("simapex_modo",MODO)}catch(e){}applicaModo();disegnaProve()};
function chiudiPopup(){const p=document.querySelector(".popup");if(p)p.remove()}
function apriPopup(el,ancora){chiudiPopup();const f=el.dataset.f,x=FUN[f]||{};const r=ancora.getBoundingClientRect();
 const p=document.createElement("div");p.className="popup";p.style.top=Math.min(r.bottom+6,innerHeight-220)+"px";p.style.left=Math.max(8,Math.min(r.right-340,innerWidth-360))+"px";
 p.innerHTML=`<b>${esc(el.dataset.t||TITOLI[f]||f)}</b><div class="row"><button class="ok ${x.s==="ok"?"sel":""}" data-s="ok">Funziona</button><button class="ko ${x.s==="ko"?"sel":""}" data-s="ko">Non funziona</button></div><textarea placeholder="Nota (facoltativa)">${esc(x.n||"")}</textarea><div class="row"><button class="chiudi">Chiudi</button></div>`;
 document.body.appendChild(p);
 p.onclick=e=>{const b=e.target.closest("button");if(!b)return;if(b.dataset.s){setFun(f,{s:b.dataset.s,n:p.querySelector("textarea").value});p.remove()}else if(b.classList.contains("chiudi")){setFun(f,{n:p.querySelector("textarea").value});p.remove()}};
}
async function setFun(id,d){try{const r=await api("/api/funzione",Object.assign({id},d));if(r.ok)FUN=r.funzioni}catch(e){}applicaModo();disegnaProve();autoInvia()}
document.addEventListener("click",e=>{if(!e.target.closest(".popup")&&!e.target.closest(".pallino"))chiudiPopup()});

/* ---------- navigazione ---------- */
function vai(s){schermo=s;document.querySelectorAll(".schermo").forEach(x=>x.hidden=x.id!=="s-"+s);document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("act",b.dataset.s===s));
 if(s==="sessioni")giroSessioni();if(s==="setup"){giroQuaderno();riempiAss()}if(s==="prove")disegnaProve();if(s==="guida")disegnaGuida()}
$("nav").onclick=e=>{const b=e.target.closest("button");if(b)vai(b.dataset.s)};
$("intero").onclick=()=>{try{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen()}catch(e){}};
$("chiudi").onclick=async()=>{try{await fetch("/api/chiudi",{method:"POST"})}catch(e){}document.body.innerHTML="<p style='padding:30px'>Programma chiuso. Puoi chiudere questa pagina.</p>"};
try{window.moveTo(0,0);window.resizeTo(screen.availWidth,screen.availHeight)}catch(e){}

/* ---------- GUIDA ---------- */
const NOMI_GOMME=["ant. sx","ant. dx","post. sx","post. dx"];
function classeGomma(t){return t<=1?"":t<70?"freddo":t<=95?"ok":t<=105?"caldo":"rovente"}
function costruisciGomme(){$("gomme4").innerHTML=NOMI_GOMME.map((n,i)=>`<div class="gomma" id="gm${i}"><small>${n}</small><b>—</b><div class="p">—</div><small class="fr"></small></div>`).join("")}
let rpmMax={};
function disegnaGuida(){
 const u=ST;if(!u.collegato){return}
 const t=u.temp_gomme||[],p=u.pressioni||[],fr=u.temp_freni||[];
 for(let i=0;i<4;i++){const g=$("gm"+i);if(!g)continue;g.className="gomma "+classeGomma(t[i]||0);g.querySelector("b").textContent=t[i]?Math.round(t[i])+"°":"—";g.querySelector(".p").textContent=p[i]?p[i].toFixed(1)+" psi":"—";g.querySelector(".fr").textContent=fr[i]?"freno "+Math.round(fr[i])+"°":""}
 $("gMarcia").textContent=u.marcia==null?"N":u.marcia;$("gVel").textContent=Math.round(u.velocita||0);
 const k=u.auto||"";rpmMax[k]=Math.max(rpmMax[k]||7000,u.giri_motore||0);$("gRpm").style.width=Math.min(100,(u.giri_motore||0)/rpmMax[k]*100)+"%";$("gRpmN").textContent=(u.giri_motore||0)+" giri";
 $("pFreno").style.height=Math.round((u.freno||0)*100)+"%";$("pGas").style.height=Math.round((u.acceleratore||0)*100)+"%";
 $("pSterzo").style.left=(50+Math.max(-1,Math.min(1,u.sterzo||0))*46)+"%";
 const att=u.giro_corrente_ms>0?u.giro_corrente_ms:u.giro_attuale_ms;
 $("tAttuale").textContent=tempoMs(att);$("tUltimo").textContent=u.ultimo_giro||"—";$("tMigliore").textContent=u.miglior_giro||"—";$("tGiro").textContent=(u.giri_completati||0)+1;
 const d=$("gDelta");if(u.delta_ms==null){d.textContent="—";d.className=""}else{d.textContent=sec(u.delta_ms,true);d.className=u.delta_ms<0?"meglio":u.delta_ms>0?"peggio":""}
 $("cLitri").textContent=u.carburante!=null?u.carburante.toFixed(1)+" L":"—";$("cCons").textContent=u.consumo_giro?u.consumo_giro.toFixed(2)+" L":"—";$("cGiri").textContent=u.giri_stimati!=null?u.giri_stimati.toFixed(1):"—";
 const b=$("gBlocco");if(u.blocco_ruota){b.textContent="BLOCCO "+u.blocco_ruota.replace("_"," ").replace("ant","ANT.").replace("post","POST.").toUpperCase();b.classList.add("on")}else b.classList.remove("on");
 mappaGuida();
}
async function mappaGuida(){const u=ST;if(!u.pista)return;
 if(pistaMappa!==u.pista){pistaMappa=u.pista;tracciato=null;try{tracciato=(await api("/api/pista?nome="+encodeURIComponent(u.pista))).pista}catch(e){}
  const s=$("gMappa");$("gMappaV").style.display=tracciato?"none":"block";
  if(!tracciato){s.innerHTML="";return}
  const X=tracciato.x,Z=tracciato.z;tracciato._b=limiti(X,Z);
  s.innerHTML=`<polygon points="${punti(X,Z,tracciato._b)}" fill="none" stroke="#e8ecf2" stroke-width="5" stroke-linejoin="round"/><circle id="gAuto" r="9" fill="#ff5a1f" stroke="#fff" stroke-width="3"/>`}
 if(tracciato&&u.pos_norm!=null){const i=Math.min(tracciato.x.length-1,Math.max(0,Math.floor(u.pos_norm*tracciato.x.length)));const q=xy(tracciato.x[i],tracciato.z[i],tracciato._b);const c=$("gAuto");if(c){c.setAttribute("cx",q[0]);c.setAttribute("cy",q[1])}}}
function limiti(X,Z){const mx=Math.min(...X),Mx=Math.max(...X),mz=Math.min(...Z),Mz=Math.max(...Z),W=Math.max(Mx-mx,Mz-mz)||1;return{mx,Mz,W,ox:(W-(Mx-mx))/2,oz:(W-(Mz-mz))/2}}
function xy(x,z,b){return[((x-b.mx+b.ox)/b.W*270+15),((b.Mz-z+b.oz)/b.W*270+15)]}
function punti(X,Z,b){return X.map((x,i)=>xy(x,Z[i],b).map(v=>v.toFixed(1)).join(",")).join(" ")}

/* ---------- stato generale ---------- */
async function giro(){try{ST=await api("/api/stato");FUN=ST.funzioni||FUN;
 const a=$("acc");a.textContent=ST.collegato?"ACC collegato":"ACC non collegato";a.className="pill"+(ST.collegato?" on":"");$("ver").textContent="v"+ST.versione;
 if(schermo==="guida")disegnaGuida();applicaModo()}catch(e){}}
let sigSetup=null;
async function giroSetup(){try{SETUP=await api("/api/setup");riempiAss();listaSetup();if(ST.invio_configurato){const sg=(SETUP.file||[]).map(f=>f.auto+f.pista+f.nome+f.modificato).join("|");if(sigSetup===null||sg!==sigSetup)autoInvia();sigSetup=sg}}catch(e){}}

/* ---------- SESSIONI ---------- */
async function giroSessioni(){try{const l=(await api("/api/sessioni")).sessioni||[];if(!l.length)return;
 $("sesLista").innerHTML=l.map(x=>`<div class="sess ${x.id===sesAperta?"act":""}" data-s="${x.id}"><b>${esc(bello(x.pista))}</b> · ${x.miglior_giro}<small>${esc(bello(x.auto))}</small><small>${dt(x.data)} · ${x.giri} giri${x.blocchi?" · "+x.blocchi+" blocchi":""}</small></div>`).join("");
 if(sesAperta===null||sesAperta===l[0].id)apriSessione(sesAperta===null?l[0].id:sesAperta,true)}catch(e){}}
$("sesLista").onclick=e=>{const t=e.target.closest(".sess");if(t){apriSessione(parseInt(t.dataset.s));giroSessioni()}};
async function apriSessione(id,silenzioso){sesAperta=id;let j;try{j=(await api("/api/sessione?id="+id)).sessione}catch(e){return}
 if(!j){$("rep").innerHTML="";return}ultimaSes=j;disegnaReport(j);
 let t=null;try{t=(await api("/api/pista?nome="+encodeURIComponent(j.pista))).pista}catch(e){}j._t=t;disegnaReport(j)}
function coloreSeg(ms){return ms<=-20?"#2ecc71":ms>=20?"#ff4d4d":"#cfd6e2"}
function disegnaReport(j){
 const c=j.confronto,rif=c&&c.rif&&(c.rif[rifSel]||c.rif.precedente||c.rif.record),rifNome=c&&c.rif&&c.rif[rifSel]?rifSel:(c&&c.rif&&c.rif.precedente?"precedente":"record");
 let h=`<div class="w intest" data-f="dettaglio" data-t="Report della sessione"><h2>${esc(bello(j.pista))} · ${esc(bello(j.auto))}</h2><span class="mu">${dt(j.data)}</span><span>Miglior giro <b class="big">${esc(j.miglior_giro)}</b></span><span class="mu">${j.giri} giri · costanza ${(j.costanza_ms/1000).toFixed(1)} s${j.blocchi_totali?" · "+j.blocchi_totali+" blocchi":""}</span></div>`;
 // mappa
 h+=`<div class="w mappa" data-f="confronto" data-t="Mappa e confronto"><div class="row"><b>Dove sei migliorato e peggiorato</b><span class="sw">${c&&c.rif&&c.rif.precedente?`<button data-r="precedente" class="${rifNome==="precedente"?"act":""}">Sessione precedente</button>`:""}${c&&c.rif&&c.rif.record?`<button data-r="record" class="${rifNome==="record"?"act":""}">Tuo record</button>`:""}</span></div>`;
 if(j._t){const X=j._t.x,Z=j._t.z,b=limiti(X,Z),n=X.length;let sv="";
  if(rif){const per=n/rif.segmenti.length;rif.segmenti.forEach((ms,s)=>{const a=Math.floor(s*per),e=Math.min(n,Math.floor((s+1)*per)+1);const pts=[];for(let i=a;i<=e;i++)pts.push(xy(X[i%n],Z[i%n],b).map(v=>v.toFixed(1)).join(","));sv+=`<polyline points="${pts.join(" ")}" fill="none" stroke="${coloreSeg(ms)}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>`});
   [].concat(rif.guadagni,rif.perdite).forEach(s=>{const i=Math.floor((s+0.5)*n/rif.segmenti.length)%n,q=xy(X[i],Z[i],b);sv+=`<circle cx="${q[0]}" cy="${q[1]}" r="11" fill="#0b0e13" stroke="${coloreSeg(rif.segmenti[s])}" stroke-width="2"/><text x="${q[0]}" y="${q[1]+4}" text-anchor="middle" font-size="11" fill="#fff">${s+1}</text>`})}
  else sv=`<polygon points="${punti(X,Z,b)}" fill="none" stroke="#e8ecf2" stroke-width="6" stroke-linejoin="round"/>`;
  (j.blocchi_pos||[]).forEach(k=>{const i=Math.min(n-1,Math.floor(k.pos*n)),q=xy(X[i],Z[i],b);sv+=`<circle cx="${q[0]}" cy="${q[1]}" r="6" fill="#ffc233" stroke="#000" stroke-width="1.5"/>`});
  h+=`<svg viewBox="0 0 300 300">${sv}</svg><div class="leg"><span><i style="background:#2ecc71"></i>più veloce</span><span><i style="background:#ff4d4d"></i>più lento</span><span><i style="background:#ffc233"></i>blocco in frenata</span></div>`}
 else h+=`<p class="mu">Il disegno della pista compare dopo un giro completo guidato su questa pista.</p>`;
 h+="</div>";
 // frasi
 h+=`<div class="w" data-f="confronto" data-t="Cosa è cambiato"><b>Cosa è cambiato</b>`;
 if(rif){const tot=c.mio.tempo_ms-rif.tempo_ms;h+=`<p>Il tuo miglior giro di questa sessione è <b class="${tot<0?"mig":"peg"}">${sec(tot,true)} s</b> rispetto ${rifNome==="precedente"?"alla sessione precedente":"al tuo record"} (${tempoMs(rif.tempo_ms)}).</p>`;
  const riga=(s)=>`<li>Tratto ${s+1} (dal ${Math.round(s*100/rif.segmenti.length)}% al ${Math.round((s+1)*100/rif.segmenti.length)}% del giro): <b class="${rif.segmenti[s]<0?"mig":"peg"}">${sec(rif.segmenti[s],true)} s</b></li>`;
  h+=rif.guadagni.length?`<p class="mig">Dove sei migliorato</p><ul>${rif.guadagni.map(riga).join("")}</ul>`:`<p class="mu">Nessun tratto in cui sei migliorato in modo netto.</p>`;
  h+=rif.perdite.length?`<p class="peg">Dove sei peggiorato</p><ul>${rif.perdite.map(riga).join("")}</ul>`:`<p class="mu">Nessun tratto in cui sei peggiorato in modo netto.</p>`}
 else h+=`<p class="mu">Per il confronto servono giri registrati su questa pista in almeno due sessioni.</p>`;
 h+=`<ul>${j.note.map(n=>"<li>"+esc(n)+"</li>").join("")}</ul></div>`;
 // grafico
 if(c){const v=c.mio.v,m=Math.max(...v,...(rif?rif.v:[]),1);const lin=(a,col)=>`<polyline fill="none" vector-effect="non-scaling-stroke" stroke="${col}" stroke-width="2" points="${a.map((y,i)=>(i/(a.length-1)*600).toFixed(1)+","+(110-y/m*100).toFixed(1)).join(" ")}"/>`;
  let g=`<svg viewBox="0 0 600 120" preserveAspectRatio="none" style="width:100%;height:9em">${rif?lin(rif.v,"#8f9aae"):""}${lin(v,"#ff5a1f")}</svg>`;
  if(rif){const d=rif.delta,dm=Math.max(...d.map(Math.abs),100);g+=`<svg viewBox="0 0 600 80" preserveAspectRatio="none" style="width:100%;height:6em"><line x1="0" x2="600" y1="40" y2="40" stroke="#444" vector-effect="non-scaling-stroke"/><polyline fill="none" vector-effect="non-scaling-stroke" stroke="#ffc233" stroke-width="2" points="${d.map((y,i)=>(i/(d.length-1)*600).toFixed(1)+","+(40+y/dm*36).toFixed(1)).join(" ")}"/></svg><div class="leg"><span>Sopra: velocità lungo il giro (arancione = tu, grigio = riferimento)</span><span>Sotto: tempo perso (giù = più veloce)</span></div>`}
  h+=`<div class="w tab" data-f="confronto" data-t="Velocità lungo il giro"><b>Velocità lungo il giro</b>${g}</div>`}
 // tabella
 h+=`<div class="w tab" data-f="dettaglio" data-t="Tabella dei giri"><b>Giri</b><table><tr><th>Giro</th><th>Tempo</th><th>Carburante</th><th></th></tr>${j.dettaglio_giri.map(x=>`<tr><td>${x.giro}</td><td>${x.tempo}</td><td>${x.carburante==null?"—":x.carburante}</td><td>${x.pulito?"":"lento o sporco "}${x.blocchi?"🔒 "+x.blocchi+" blocchi":""}</td></tr>`).join("")}</table>`;
 if(j.carburante_inizio!=null)h+=`<p class="mu">Carburante: da ${j.carburante_inizio} a ${j.carburante_fine} L.</p>`;
 if(j.gomme&&j.gomme.temperatura_media_C){const t=j.gomme.temperatura_media_C,p=j.gomme.pressione_media_psi;h+=`<p class="mu">Gomme (media): `+Object.keys(t).map(k=>`${bello(k)} ${t[k]}° / ${p[k]} psi`).join(" · ")+`</p>`}
 h+="</div>";
 $("rep").innerHTML=h;applicaModo();
}
$("rep").onclick=e=>{const b=e.target.closest("button[data-r]");if(b&&ultimaSes){rifSel=b.dataset.r;disegnaReport(ultimaSes)}};

/* ---------- SETUP ---------- */
function listaSetup(){const f=(SETUP.file||[]);$("setupLista").innerHTML=f.length?"<table>"+f.map(x=>`<tr><td>${esc(bello(x.auto))}</td><td>${esc(bello(x.pista))}</td><td>${esc(x.nome)}</td><td class="${x.valido?"mig":"peg"}">${x.valido?"letto":"non letto"}</td></tr>`).join("")+"</table>":"Apri ACC e salva un setup."}
function riempiAss(){const s=$("assFile");const f=(SETUP.file||[]).filter(x=>x.valido);const sig=f.map(x=>x.auto+x.pista+x.nome).join("|");if(s.dataset.sig===sig)return;s.dataset.sig=sig;const cur=s.value;s.innerHTML=f.length?f.map(x=>`<option value="${esc(x.auto)}/${esc(x.pista)}/${esc(x.nome)}">${esc(bello(x.auto))} · ${esc(bello(x.pista))} · ${esc(x.nome)}</option>`).join(""):'<option value="">Nessun setup trovato: salvane uno in ACC</option>';if(cur)s.value=cur}
async function assChiedi(modo){const file=$("assFile").value;if(!file){$("assMsg").textContent="Salva prima un setup in ACC.";return}
 $("assMsg").textContent="Claude sta lavorando (anche un minuto per il setup base)...";$("assRis").innerHTML="";let j;try{j=await api("/api/assistente/proponi",{file:file,sensazioni:$("assSens").value,modo:modo})}catch(e){$("assMsg").textContent="Il programma non risponde.";return}
 if(!j.ok){$("assMsg").textContent="Non riuscito: "+j.errore;return}
 $("assMsg").textContent="";assId=j.id||null;if(j.modifiche&&j.modifiche.length)$("assSens").value="";
 let h=`<div class="card"><b>${esc(j.problema||"Proposta")}</b><p class="mu">${esc(j.spiegazione||"")}</p>`;
 if(j.modifiche.length){h+="<table>"+j.modifiche.map(m=>`<tr><td>${esc(m.nome)}</td><td>${m.click>0?"+":""}${m.click} click</td><td>${esc(m.motivo)}</td></tr>`).join("")+"</table>";
  h+=`<p><b>Setup creato:</b> ${esc(j.nuovo_file)}<br>In ACC apri la lista dei setup, scegli questo nome e caricalo.</p><p class="mu">${esc(j.cosa_aspettarsi||"")}</p><p class="mu">Dopo almeno 4 giri puliti con questo setup il programma dice da solo se è andato meglio, uguale o peggio.</p>`}
 else h+=`<p>Nessuna modifica proposta.</p><p class="mu">${esc(j.cosa_aspettarsi||"")}</p>`;
 if((j.suggerimenti_pilota||[]).length)h+="<p><b>Da cambiare tu (ABS, controllo trazione, mappa motore):</b></p><ul>"+j.suggerimenti_pilota.map(x=>"<li>"+esc(x)+"</li>").join("")+"</ul>";
 $("assRis").innerHTML=h+"</div>";giroQuaderno()}
$("assBase").onclick=()=>assChiedi("base");$("assVai").onclick=()=>assChiedi("migliora");
async function giroQuaderno(){try{const j=await api("/api/assistente");const q=(j.quaderno||[]).slice().reverse();
 $("assStile").textContent=j.giri_registrati?"Giri registrati per imparare il tuo stile: "+j.giri_registrati+(j.stile?" (profilo pronto)":" (ne servono almeno 3 puliti)"):"Guida con Simapex aperto: registra in silenzio il tuo stile di guida, giro per giro.";
 if(!q.length){$("quad").textContent="Ancora nessun setup creato.";return}
 $("quad").innerHTML="<table>"+q.map((x,i)=>`<tr><td>${esc(x.nuovo||"")}<small class="mu"><br>${esc(x.problema||"")}</small></td><td><b class="${x.esito==="meglio"?"mig":x.esito==="peggio"?"peg":""}">${esc(x.esito?x.esito.toUpperCase():"in attesa dei giri")}</b>${x.esito_motivo?`<small class="mu"><br>${esc(x.esito_motivo)}</small>`:""}${i===0&&x.esito&&x.esito_auto?`<br><small class="mu">Non sei d'accordo?</small> <button data-e="meglio" data-id="${x.id}">Meglio</button><button data-e="uguale" data-id="${x.id}">Uguale</button><button data-e="peggio" data-id="${x.id}">Peggio</button>`:""}</td></tr>`).join("")+"</table>"}catch(e){}}
$("quad").onclick=async e=>{const b=e.target.closest("button[data-e]");if(!b)return;await api("/api/assistente/esito",{id:parseInt(b.dataset.id),esito:b.dataset.e});giroQuaderno()};
(function(){const R=window.SpeechRecognition||window.webkitSpeechRecognition;const M=t=>{$("assMsg").textContent=t};
 if(!R){$("assMic").onclick=()=>M("Questo browser non ha il riconoscimento vocale. Clicca nella casella e premi Windows + H per dettare.");return}
 let rec=null,on=false;
 $("assMic").onclick=()=>{if(on){rec&&rec.stop();return}
  try{rec=new R();rec.lang="it-IT";rec.continuous=true;rec.interimResults=false;
  rec.onstart=()=>{M("Sto ascoltando... parla pure.")};
  rec.onresult=ev=>{let t="";for(let i=ev.resultIndex;i<ev.results.length;i++)t+=ev.results[i][0].transcript+" ";$("assSens").value=($("assSens").value+" "+t).trim()};
  rec.onerror=ev=>{const e=ev.error;M(e==="not-allowed"||e==="service-not-allowed"?"Il microfono è bloccato: nella finestra clicca sul lucchetto in alto, consenti il microfono, poi riprova. Intanto puoi dettare con Windows + H nella casella.":e==="audio-capture"?"Non trovo nessun microfono collegato.":e==="network"?"Il riconoscimento vocale non riesce a collegarsi a internet. Intanto puoi dettare con Windows + H nella casella.":e==="no-speech"?"Non ho sentito niente: riprova e parla più vicino al microfono.":"Microfono: errore "+e+". Puoi dettare con Windows + H nella casella.")};
  rec.onend=()=>{on=false;$("assMic").textContent="🎤 Parla"};rec.start();on=true;$("assMic").textContent="⏹ Stop"}catch(x){on=false;M("Microfono: "+x.message+". Puoi dettare con Windows + H nella casella.")}}})();

/* ---------- PROVE ---------- */
function disegnaProve(){const el=$("proveLista");if(!el)return;let h="";
 PROVE.forEach((p,i)=>{const x=FUN[p.id]||{};if(p.g)h+=`<h3>${p.g}</h3>`;
  h+=`<div class="prova"><b>${i+1}. ${esc(p.t)}</b><span class="st ${x.s==="ok"?"ok":x.s==="ko"?"ko":""}"> ${x.s==="ok"?"Funziona":x.s==="ko"?"Non funziona":""}</span><ol>${p.p.map(s=>`<li>${esc(s)}</li>`).join("")}</ol><div class="mu">Cosa deve succedere: ${esc(p.a.replace("__VERSIONE__",ST.versione||""))}</div><div class="row"><button class="ok ${x.s==="ok"?"sel":""}" data-p="${p.id}" data-s="ok">Funziona</button><button class="ko ${x.s==="ko"?"sel":""}" data-p="${p.id}" data-s="ko">Non funziona</button></div><textarea data-n="${p.id}" placeholder="Nota (facoltativa)">${esc(x.n||"")}</textarea></div>`});
 if(el.dataset.h!==h){const f=document.activeElement;if(f&&f.dataset&&f.dataset.n)return;el.innerHTML=h;el.dataset.h=h}}
$("proveLista").onclick=e=>{const b=e.target.closest("button[data-p]");if(b)setFun(b.dataset.p,{s:b.dataset.s})};
$("proveLista").addEventListener("change",e=>{const t=e.target.closest("textarea[data-n]");if(t)setFun(t.dataset.n,{n:t.value})});

/* ---------- invio a Claude ---------- */
function istantanea(){const u=ST;return {collegato:u.collegato,auto:u.auto,pista:u.pista,velocita:u.velocita,marcia:u.marcia,giri_motore:u.giri_motore,carburante:u.carburante,pressioni:u.pressioni,temp_gomme:u.temp_gomme,ultimo_giro:u.ultimo_giro,miglior_giro:u.miglior_giro,delta_ms:u.delta_ms}}
function raccogli(){return {ora:new Date().toISOString(),versione:$("ver").textContent,modo:MODO,prove:PROVE.map(p=>{const x=FUN[p.id]||{};return {id:p.id,titolo:p.t,stato:x.s==="ok"?"funziona":x.s==="ko"?"non funziona":"non provata",nota:x.n||"",dati_al_momento:null}})}}
let tAuto=null;function autoInvia(){if(!ST.invio_configurato)return;clearTimeout(tAuto);tAuto=setTimeout(async()=>{try{const p=raccogli();p.automatico=true;p.istantanea=istantanea();const j=await api("/api/invia",p);if($("invioSt"))$("invioSt").textContent=j.ok?"Inviato a Claude da solo alle "+new Date().toLocaleTimeString("it-IT"):"Invio non riuscito: "+j.errore}catch(e){}},4000)}
$("invia").onclick=async()=>{if(!ST.invio_configurato){$("copiato").textContent="Prima serve la chiave di accesso (qui sopra).";return}
 $("copiato").textContent="Invio in corso...";try{const j=await api("/api/invia",raccogli());$("copiato").textContent=j.ok?"Inviato a Claude. Scrivi «controlla» nella chat.":"Invio non riuscito: "+j.errore}catch(e){$("copiato").textContent="Invio non riuscito: il programma non risponde."}};
$("azzera").onclick=async()=>{for(const p of PROVE)await api("/api/funzione",{id:p.id,s:null,n:""});await giro();disegnaProve()};
$("salvaChiave").onclick=async()=>{const v=$("chiave").value.trim();if(!v){$("chiaveMsg").textContent="Incolla prima la chiave.";return}
 try{const j=await api("/api/chiave",{token:v});if(j.ok){$("chiave").value="";ST.invio_configurato=true;$("chiaveMsg").textContent="Chiave salvata."}else $("chiaveMsg").textContent=j.errore}catch(e){$("chiaveMsg").textContent="Non sono riuscito a salvare."}};
function aggiornaClaudeSt(){$("claudeSt").textContent=ST.claude_configurato?"Chiave salvata su questo PC. Tocca Prova per controllare che funzioni.":"Non collegato. Incolla qui la chiave che inizia con sk-ant- (resta solo su questo PC)."}
$("claudeSalva").onclick=async()=>{const v=$("claudeChiave").value.trim();if(!v){$("claudeMsg").textContent="Incolla prima la chiave.";return}
 try{const j=await api("/api/claude-chiave",{chiave:v});if(j.ok){$("claudeChiave").value="";ST.claude_configurato=true;aggiornaClaudeSt();$("claudeMsg").textContent="Chiave salvata. Ora tocca Prova."}else $("claudeMsg").textContent=j.errore}catch(e){$("claudeMsg").textContent="Non sono riuscito a salvare."}};
$("claudeProva").onclick=async()=>{$("claudeMsg").textContent="Sto chiamando Claude...";try{const j=await api("/api/claude-prova",{});$("claudeMsg").textContent=j.ok?"Funziona! Claude risponde: "+j.risposta:"Non funziona: "+j.errore}catch(e){$("claudeMsg").textContent="Il programma non risponde."}};
async function controllaAgg(){try{const j=await api("/api/aggiornamenti");if(j.disponibile){$("aggv").textContent="v"+j.ultima;$("agg").hidden=false;$("aggb").onclick=()=>window.open(j.scarica,"_blank")}}catch(e){}}
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}

costruisciGomme();applicaModo();disegnaProve();giro();giroSetup();controllaAgg();
setInterval(giro,200);setInterval(giroSetup,5000);setInterval(controllaAgg,3600000);
setInterval(()=>{if(schermo==="sessioni")giroSessioni();if(schermo==="setup")giroQuaderno();aggiornaClaudeSt()},5000);
