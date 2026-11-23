"use strict";
const $=id=>document.getElementById(id);
const esc=t=>String(t==null?"":t).replace(/&/g,"&amp;").replace(/</g,"&lt;");
let tMappa=0, ST={}, FUN={}, SETUP={}, assId=null, schermo="guida", pistaMappa=null, tracciato=null, sesAperta=null, rifSel="precedente", ultimaSes=null;
let MODO="dev";try{MODO=localStorage.getItem("simapex_modo")||"dev"}catch(e){}

/* ---------- funzioni da provare (le stesse in Gioca e Sviluppo) ---------- */
const PROVE=[
 {id:"apre",g:"1 · PRIMA DI PARTIRE (Ferrari 296 GT3, Misano)",t:"Il programma è aggiornato",p:["Apri Simapex.exe: se c'è una versione nuova compare «Sto aggiornando...» e si riapre da solo.","Guarda il numero di versione in alto."],a:"Vedi v__VERSIONE__."},
 {id:"setup",t:"Salva il tuo setup di partenza",p:["In ACC salva il setup che usi adesso con un nome che riconosci, per esempio «Base».","Apri la schermata Setup: guarda «Setup trovati in ACC»."],a:"Il tuo setup compare nella lista con auto e pista giuste."},
 {id:"acc",r:"Primi giri di riscaldamento: ritmo tranquillo, senza attaccare. Mappa motore: __MAPPA_C__.",g:"2 · PRIMO TURNO: IMPARI IL CIRCUITO",t:"Schermata Guida: dati in diretta",p:["Lascia Simapex aperto sulla schermata Guida, apri ACC ed entra in pista con il tuo setup «Base».","Guida normalmente: ogni tanto guarda marcia, velocità, giri motore e pedali."],a:"«ACC collegato» in alto e i numeri coincidono con il cruscotto di ACC."},
 {id:"gomme",t:"Gomme: temperature e pressioni",p:["Guarda i 4 riquadri delle gomme a sinistra."],a:"Temperatura e pressione coincidono con quelle di ACC e il colore cambia (blu freddo, verde giusto, giallo caldo, rosso rovente)."},
 {id:"giri",r:"Passo costante: tutti i giri allo stesso ritmo, senza uscire di pista, circa al 95% di quello che sai fare. Mappa motore: __MAPPA_C__. Non cambiarla tra un giro e l'altro.",t:"Tempi dei giri",p:["Fai almeno 8 giri, senza passare dai box (così si disegna anche il circuito).","Guarda «Ultimo» e «Migliore»."],a:"I tempi sono uguali a quelli di ACC."},
 {id:"delta",t:"Delta sul tuo giro migliore",p:["Dal secondo giro guarda il numero grande «Rispetto al tuo giro migliore»."],a:"È verde (con il segno meno) quando sei più veloce del tuo giro migliore in quel punto, rosso quando sei più lento."},
 {id:"carburante",t:"Carburante e giri che restano",p:["Dopo qualche giro guarda il riquadro del carburante."],a:"Consumo per giro e giri che restano sono credibili."},
 {id:"mappa",t:"Si disegna il circuito",p:["Finito il primo giro pulito guarda la mappa nella schermata Guida: compare un puntino che segue l'auto."],a:"Il disegno somiglia al circuito vero e il puntino è nel posto giusto."},
 {id:"base",g:"3 · IL SETUP BASE CON L'IA",t:"Crea il tuo setup base",p:["Nella schermata Setup scegli il setup «Base».","Scrivi (o parla con 🎤) cosa non va. Più sei preciso meglio è.","Tocca «Crea il mio setup base» e aspetta."],a:"Compaiono le modifiche con il motivo e il nome di un file nuovo («... Simapex 1»). I suggerimenti su ABS, controllo trazione e mappa motore compaiono a parte."},
 {id:"carica",t:"ACC accetta il setup nuovo",p:["In ACC, nella lista dei setup, cerca il file nuovo e caricalo."],a:"Il file si vede e si carica senza errori."},
 {id:"mic",t:"Microfono",p:["Nella schermata Setup tocca 🎤 Parla e racconta come va la macchina."],a:"Quello che dici compare scritto nella casella."},
 {id:"guida1",r:"Passo costante, come il primo turno, con la stessa mappa motore (__MAPPA_C__): solo così il programma può dire se il setup è meglio o peggio.",g:"4 · SECONDO TURNO: CON IL SETUP NUOVO",t:"Guida con il setup nuovo",p:["Esci in pista con il setup «Simapex 1» e fai almeno 8 giri, senza box.","Nella schermata Setup, sotto «Setup provati», guarda l'esito deciso dal programma."],a:"Dopo almeno 4 giri puliti il programma scrive meglio, uguale o peggio con il motivo. La macchina deve essere più guidabile."},
 {id:"esito",t:"L'esito del setup è giusto",p:["Confronta l'esito del programma con quello che hai sentito."],a:"Il programma e le tue sensazioni vanno nella stessa direzione."},
 {id:"blocchi",r:"Qui puoi spingere: frena più forte del solito solo nei punti sicuri, poi torna al passo costante. Mappa motore: __MAPPA_C__.",t:"Rileva i blocchi in frenata",p:["Ogni tanto frena più forte del solito fino a bloccare una ruota (almeno 3 volte)."],a:"Compare la scritta rossa BLOCCO con la ruota giusta, e nel report i blocchi sono contati."},
 {id:"migliora1",r:"Passo costante per 5 o più giri puliti, con la stessa mappa (__MAPPA_C__). Le uscite di prova e le qualifiche si fanno solo dopo, con __MAPPA_S__.",g:"5 · MIGLIORAMENTO DEL SETUP",t:"Primo miglioramento (una modifica alla volta)",p:["Scrivi il problema che ti dà più fastidio adesso.","Tocca «Migliora» e carica in ACC il file nuovo. Fai 5 o più giri."],a:"L'assistente propone poche modifiche (massimo 3) legate al problema. L'esito arriva da solo."},
 {id:"migliora2",r:"Come prima: passo costante e stessa mappa (__MAPPA_C__). Spingere al massimo (__MAPPA_S__) si fa solo a setup finito.",t:"Secondo miglioramento",p:["Ripeti con il problema successivo."],a:"Come sopra: poche modifiche, e l'assistente tiene conto dell'esito precedente."},
 {id:"sessioni",g:"6 · A FINE GIORNATA",t:"Le sessioni si salvano da sole",p:["Apri la schermata Sessioni."],a:"Ci sono i turni che hai fatto, con auto, pista, data e giri."},
 {id:"dettaglio",t:"Report della sessione",p:["Tocca una sessione: guarda la mappa, i tratti dove sei migliorato e peggiorato, i blocchi e la tabella dei giri."],a:"I tempi coincidono con ACC e il report si capisce e ti è utile."},
 {id:"confronto",t:"Confronto con la sessione precedente",p:["Nel report scegli «Sessione precedente» o «Tuo record»."],a:"La mappa si colora: verde dove sei più veloce, rosso dove perdi. I tratti principali sono scritti."}
];

/* ---------- test: ingegnere/box e Formula 1 (solo Sviluppo) ---------- */
const PROVE_ING=[
 {id:"ing_voce",g:"7 · INGEGNERE DI PISTA E BOX (ACC e F1)",t:"La voce dell'ingegnere",p:["Apri la schermata Pista, spunta «Voce attiva» e tocca «Prova la voce».","Se non senti niente controlla il volume e che Windows abbia una voce italiana (Impostazioni → Ora e lingua → Voce)."],a:"Senti una frase in italiano."},
 {id:"ing_blocco",t:"Avviso sui blocchi in frenata",p:["Guida con la voce attiva e blocca una ruota in frenata."],a:"L'ingegnere dice quale ruota si è bloccata e come frenare."},
 {id:"ing_giro",t:"Tempo a fine giro",p:["Completa qualche giro con la voce attiva."],a:"A ogni giro dice il tempo e quanto sei lontano dal tuo migliore, e dice quando fai il nuovo migliore."},
 {id:"ing_carb",t:"Avviso carburante",p:["Parti con poco carburante (circa 4 giri) e fai almeno 3 giri così il programma capisce il consumo."],a:"Ti avvisa quando restano 3 giri e poi di rientrare ai box."},
 {id:"ing_gomme",t:"Avviso gomme",p:["Guida spingendo finché le gomme diventano molto calde, oppure appena esci con le gomme fredde."],a:"Ti avvisa se sono troppo calde o troppo fredde. In ACC avvisa anche se le pressioni a caldo sono fuori dall'intervallo."},
 {id:"ing_sess",t:"Consigli diversi per prove, qualifica e gara",p:["Nella schermata Pista guarda l'assistente ai box in una sessione di prove, in una di qualifica e in una gara."],a:"Le frasi cambiano: nelle prove ti dice come misurare il passo, in qualifica come preparare il giro, in gara la strategia."},
 {id:"box",t:"Assistente ai box: strategia",p:["Fai una gara con un numero di giri (o a tempo).","Nella schermata Pista guarda le righe su carburante e gomme."],a:"Ti dice se il carburante basta fino alla fine o quanto ne devi aggiungere, e quando rientrare per le gomme (in F1 con l'usura vera)."},
 {id:"ing_radio",t:"Radio da vero ingegnere",p:["Fai una gara con la voce attiva e ascolta i messaggi in pista."],a:"I messaggi sono brevi, arrivano sui rettilinei e mai in frenata o in curva veloce, e ti dicono quando spingere, quando risparmiare carburante e come stanno le gomme."},
 {id:"ing_box",t:"Uscita dai box e giro di lancio",p:["Esci dai box in qualifica con la voce attiva."],a:"Ti dice di fare il giro di lancio e, a fine giro, che ora puoi spingere. A metà giro ti dice il distacco dal tuo migliore."},
 {id:"piano",t:"Piano per la sessione (Box)",p:["Nella schermata Box scegli prove, qualifica o gara e i giri, poi tocca «Prepara il piano» e anche «Chiedi alla squadra».","Confronta carburante, gomme e mappa con quello che faresti tu."],a:"Il piano è sensato: carburante in linea con il consumo vero, gomme adatte alla sessione, mappa motore giusta."},
 {id:"ing_spotter",t:"Spotter: macchine vicine (solo ACC)",p:["Con la voce attiva, in gara con altre auto, affiancati a un'auto a destra e poi a sinistra."],a:"Dice «macchina a destra» o «a sinistra» dal lato giusto e «libero» quando passa. Se i lati sono scambiati, spunta «Inverti destra e sinistra» nella schermata Pista."},
 {id:"f1_distacchi",t:"Distacchi e ritmo (F1)",p:["In gara F1 chiedi «distacco davanti», «vantaggio dietro» e «ritmo»."],a:"I secondi coincidono con quelli del gioco e a fine giro l'ingegnere li dice da solo."},
 {id:"f1_setup",t:"Consiglio sul setup F1",p:["In F1, nella schermata Box, scrivi un problema della macchina e tocca «Consiglio sul setup»."],a:"Propone una sola modifica con il valore preciso e il motivo, partendo dal setup che hai nel gioco."},
 {id:"ing_radio_ptt",t:"Radio con il tasto del volante",p:["Nella schermata Pista scrivi il numero del tasto del volante (propongo il tasto PlayStation, 25) e tocca Salva.","Tieni premuto il tasto, parla nel microfono delle cuffie e rilascia."],a:"Senti un bip alla pressione, l'ingegnere risponde con la voce nelle cuffie, senza toccare il mouse."},
 {id:"conf_giri",t:"Microsettori e confronto tra giri",p:["In Sessioni apri una sessione, scegli due giri dalla lista in alto alla mappa e tocca Confronta."],a:"La mappa è divisa in 25 microsettori colorati (verde = guadagni, rosso = perdi) e sotto sono elencati i tre migliori e i tre peggiori."},
 {id:"ing_domanda",t:"Domanda all'ingegnere",p:["Nella schermata Pista scrivi una domanda, per esempio «come sono le gomme?», e tocca Chiedi."],a:"Risponde in poche frasi usando i dati di adesso (se la voce è attiva la legge)."}
];
const PROVE_F1=[
 {id:"f1_udp",g:"8 · FORMULA 1 25 (anche con il pacchetto 2026)",t:"Il gioco manda i dati a Simapex",p:["In F1 25 vai su Impostazioni → Telemetria. UDP Telemetry: On. UDP IP: 127.0.0.1. Porta: 20777. Frequenza: 20 Hz o più. Formato: 2025 (non quello del pacchetto 2026).","Se Windows chiede il permesso di rete per Simapex, premi Consenti.","Apri Simapex ed entra in pista."],a:"In alto compare «F1 25 collegato» entro pochi secondi dall'ingresso in pista."},
 {id:"f1_dati",t:"Dati in diretta",p:["Guarda la schermata Guida mentre guidi."],a:"Marcia, velocità, giri motore, pedali e sterzo coincidono con quello che vedi nel gioco."},
 {id:"f1_gomme",t:"Gomme: temperature",p:["Guarda i 4 riquadri delle gomme nella Guida."],a:"Le temperature sono credibili (80-110 °C in pista) e ogni riquadro corrisponde alla ruota giusta (anteriore sinistra = in alto a sinistra)."},
 {id:"f1_giri",t:"Tempi dei giri",p:["Fai almeno 4 giri completi senza passare dai box."],a:"«Ultimo» e «Migliore» sono uguali a quelli del gioco."},
 {id:"f1_pista",t:"Pista e squadra riconosciute",p:["Dopo qualche giro apri la schermata Sessioni."],a:"La pista è quella giusta e l'auto indica la tua squadra."},
 {id:"f1_mappa",t:"Si disegna il circuito",p:["Dopo un giro pulito guarda la mappa nella Guida."],a:"Compare il tracciato e il puntino segue l'auto."},
 {id:"f1_delta",t:"Delta sul tuo giro migliore",p:["Dal secondo giro guarda il numero grande nella Guida."],a:"Verde se sei più veloce del tuo migliore, rosso se più lento."},
 {id:"f1_carb",t:"Carburante (in kg)",p:["Guarda il riquadro del carburante nella Guida dopo qualche giro."],a:"I kg di carburante sono uguali a quelli del gioco e i giri che restano sono credibili."},
 {id:"f1_blocchi",t:"Blocchi in frenata",p:["Frena molto forte per bloccare una ruota, almeno 3 volte."],a:"Compare la scritta rossa BLOCCO con la ruota giusta e il report li conta."},
 {id:"f1_sessione",t:"Prove, qualifica e gara riconosciute",p:["Fai una sessione di prove libere, poi una qualifica e infine una gara breve (anche 3 giri).","Apri Sessioni."],a:"Ogni sessione ha il tipo giusto e il report è diverso (gara: passo e posizione, qualifica: giro migliore)."},
 {id:"f1_report",t:"Report e confronto",p:["Apri una sessione F1 e prova «Sessione precedente» e «Tuo record»."],a:"Mappa colorata e tratti dove guadagni e perdi, come in ACC."},
 {id:"f1_usura",t:"Usura gomme e mescola",p:["Fai una gara con 5 o più giri e guarda la schermata Pista."],a:"L'assistente ai box mostra mescola, giri delle gomme e usura in percentuale."},
 {id:"f1_safety",t:"Safety car e bandiere",p:["Se in gara compare la safety car o una bandiera gialla/blu, ascolta l'ingegnere."],a:"Lo dice a voce. (Se non capita, lascia vuoto.)"},
 {id:"f1_2026",t:"Auto e piste del pacchetto 2026",p:["Se guidi un'auto o una pista nuova del pacchetto 2026 guarda auto e pista nelle Sessioni."],a:"Il nome è sensato. Se vedi «circuito_NN» o «team_NN» scrivimi il numero e lo aggiungo."}
];
const TUTTE=()=>PROVE.concat(PROVE_ING,PROVE_F1);
let MAPPE=null,mappeAuto=null,mappeTentata={};
function testoMappa(n){return n?"mappa "+n:"la mappa consigliata nella nota qui sopra (se non c'è, quella di partenza)"}
async function giroMappe(){const a=ST.auto;if(!a||mappeAuto===a)return;mappeAuto=a;MAPPE=null;
 try{MAPPE=(await api("/api/mappe?auto="+encodeURIComponent(a))).mappe}catch(e){}
 disegnaMappe();if(!MAPPE&&ST.claude_configurato&&MODO==="dev"&&!mappeTentata[a]){mappeTentata[a]=1;cercaMappe()}}
async function cercaMappe(){const a=ST.auto;if(!a)return;$("mappeTesto").textContent="Sto cercando online cosa fa ogni mappa motore di questa auto... (può volerci un minuto)";$("mappeCerca").disabled=true;
 try{const j=await api("/api/mappe/cerca",{auto:a});if(j.ok){MAPPE=j.mappe}else{$("mappeTesto").textContent="Non sono riuscito: "+j.errore;$("mappeCerca").disabled=false;return}}catch(e){$("mappeTesto").textContent="Il programma non risponde."}
 $("mappeCerca").disabled=false;disegnaMappe();disegnaProve()}
function disegnaMappe(){const el=$("mappeTesto");if(!el)return;const m=MAPPE;
 if(!m){el.textContent=ST.auto?"Non ho ancora le mappe di questa auto. "+(ST.claude_configurato?"Tocca il tasto qui sotto.":"Prima collega Claude nelle Impostazioni."):"Entra in pista: appena il programma sa con che auto sei, cerca online cosa fa ogni mappa motore e te lo scrive qui.";return}
 const aff={alta:"affidabile",media:"abbastanza affidabile",bassa:"poco affidabile: controlla tu in pista"}[m.affidabilita]||"";
 el.innerHTML=`<div><b>${esc(m.auto_nome||m.auto)}</b> · <span class="mu">${esc(aff)}${m.ricerca_online?"":" · senza ricerca su internet"}</span></div>`+
 `<ul>${(m.mappe||[]).map(x=>`<li><b>Mappa ${x.numero}:</b> ${esc(x.cosa_fa)}</li>`).join("")}</ul>`+
 `<div><b>Passo costante:</b> ${m.mappa_giri_costanti?"mappa "+m.mappa_giri_costanti+". ":""}${esc(m.quando_passo_costante)}</div>`+
 `<div><b>Spingere:</b> ${m.mappa_spinta?"mappa "+m.mappa_spinta+". ":""}${esc(m.quando_spingere)}</div>`+
 (m.come_si_cambia?`<div><b>Come si cambia:</b> ${esc(m.come_si_cambia)}</div>`:"")+(m.nota?`<div class="mu">Nota: ${esc(m.nota)}</div>`:"")+
 `<div class="mu">Sono solo consigli: la mappa la cambi sempre tu.${(m.fonti||[]).length?" Fonti: "+m.fonti.map(u=>esc(u.replace(/^https?:\/\//,"").split("/")[0])).join(", "):""}</div>`}
$("mappeCerca").onclick=cercaMappe;
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
 if(s==="sessioni")giroSessioni();if(s==="setup"){giroQuaderno();riempiAss()}if(s==="prove")disegnaProve();if(s==="pista")disegnaBox();if(s==="guida")disegnaGuida()}
$("aiutoVai").onclick=()=>{try{localStorage.setItem("simapex_aiuto_visto","1")}catch(e){}vai("guida")};
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
 const inPista=u.stato_codice===2&&!u.in_box;
 $("tAttuale").textContent=inPista&&u.giro_corrente_ms>0?tempoMs(u.giro_corrente_ms):"—";$("tUltimo").textContent=u.ultimo_giro||"—";$("tMigliore").textContent=u.miglior_giro||"—";$("tGiro").textContent=(u.giri_completati||0)+1;
 const d=$("gDelta");if(u.delta_ms==null){d.textContent="—";d.className=""}else{d.textContent=sec(u.delta_ms,true);d.className=u.delta_ms<0?"meglio":u.delta_ms>0?"peggio":""}
 {const UC=u.gioco==="F1 25"?" kg":" L";$("cLitri").textContent=u.carburante!=null?u.carburante.toFixed(1)+UC:"—";$("cCons").textContent=u.consumo_giro?u.consumo_giro.toFixed(2)+UC:"—"}$("cGiri").textContent=u.giri_stimati!=null?u.giri_stimati.toFixed(1):"—";
 const b=$("gBlocco");if(u.blocco_ruota){b.textContent="BLOCCO "+u.blocco_ruota.replace("_"," ").replace("ant","ANT.").replace("post","POST.").toUpperCase();b.classList.add("on")}else b.classList.remove("on");
 mappaGuida();
}
async function mappaGuida(){const u=ST;if(!u.pista)return;
 if(pistaMappa!==u.pista||(!tracciato&&u.pista&&Date.now()-tMappa>10000)){tMappa=Date.now();pistaMappa=u.pista;tracciato=null;try{tracciato=(await api("/api/pista?nome="+encodeURIComponent(u.pista))).pista}catch(e){}
  const s=$("gMappa");$("gMappaV").style.display=tracciato?"none":"block";
  if(!tracciato){s.innerHTML="";return}
  const rd=rotGet(u.pista);let [X,Z]=ruota(tracciato.x,tracciato.z,rd);tracciato._X=X;tracciato._Z=Z;if(tracciato.box){const q=ruota(tracciato.box.x,tracciato.box.z,rd);tracciato._bx=q[0];tracciato._bz=q[1]}tracciato._b=limiti(X,Z);
  s.innerHTML=`<polygon points="${punti(X,Z,tracciato._b)}" fill="none" stroke="#e8ecf2" stroke-width="5" stroke-linejoin="round"/>${tracciato.box?`<polyline points="${punti(tracciato._bx,tracciato._bz,tracciato._b)}" fill="none" stroke="#4da3ff" stroke-width="3" stroke-dasharray="6 5" stroke-linecap="round"/>`:""}<circle id="gAuto" r="9" fill="#ff5a1f" stroke="#fff" stroke-width="3"/>`}
 if(tracciato&&u.pos_norm!=null){const i=Math.min(tracciato.x.length-1,Math.max(0,Math.floor(u.pos_norm*tracciato.x.length)));const q=xy(tracciato._X[i],tracciato._Z[i],tracciato._b);const c=$("gAuto");if(c){c.setAttribute("cx",q[0]);c.setAttribute("cy",q[1])}}}
function rotGet(p){try{return +localStorage.getItem("simapex_rot_"+p)||0}catch(e){return 0}}
function rotSet(p,d){try{localStorage.setItem("simapex_rot_"+p,String(((d%360)+360)%360))}catch(e){}}
function ruota(X,Z,d){if(!d)return[X,Z];const r=d*Math.PI/180,c=Math.cos(r),sn=Math.sin(r);return[X.map((x,i)=>x*c-Z[i]*sn),X.map((x,i)=>x*sn+Z[i]*c)]}
function limiti(X,Z){const mx=Math.min(...X),Mx=Math.max(...X),mz=Math.min(...Z),Mz=Math.max(...Z),W=Math.max(Mx-mx,Mz-mz)||1;return{mx,Mz,W,ox:(W-(Mx-mx))/2,oz:(W-(Mz-mz))/2}}
function xy(x,z,b){return[((x-b.mx+b.ox)/b.W*270+15),((b.Mz-z+b.oz)/b.W*270+15)]}
function punti(X,Z,b){return X.map((x,i)=>xy(x,Z[i],b).map(v=>v.toFixed(1)).join(",")).join(" ")}

/* ---------- stato generale ---------- */
async function giro(){try{ST=await api("/api/stato");FUN=ST.funzioni||FUN;
 const a=$("acc");a.textContent=ST.collegato?(ST.gioco||"ACC")+" collegato":"Gioco non collegato";a.className="pill"+(ST.collegato?" on":"");$("ver").textContent="v"+ST.versione;{const F=ST.gioco==="F1 25",n=$("f1Nota");if(n)n.hidden=!F;["assFile","assBase","assVai","assPress","accNota"].forEach(i=>{const e=$(i);if(e)e.style.display=F?"none":""})}
 if(schermo==="guida")disegnaGuida();try{spotter();radioPtt()}catch(e){}applicaModo()}catch(e){}}
let sigSetup=null;
async function giroSetup(){try{SETUP=await api("/api/setup");riempiAss();listaSetup();if(ST.invio_configurato){const sg=(SETUP.file||[]).map(f=>f.auto+f.pista+f.nome+f.modificato).join("|");if(sigSetup===null||sg!==sigSetup)autoInvia();sigSetup=sg}}catch(e){}}

/* ---------- SESSIONI ---------- */
async function giroSessioni(){try{const l=(await api("/api/sessioni")).sessioni||[];if(!l.length)return;
 $("sesLista").innerHTML=l.map(x=>`<div class="sess ${x.id===sesAperta?"act":""}" data-s="${x.id}"><b>${esc(bello(x.pista))}</b> · ${x.miglior_giro}${x.tipo?` <span class="pill">${esc(x.tipo)}</span>`:""}<small>${esc(bello(x.auto))}</small><small>${dt(x.data)} · ${x.giri} giri${x.blocchi?" · "+x.blocchi+" blocchi":""}</small></div>`).join("");
 if(sesAperta===null||sesAperta===l[0].id)apriSessione(sesAperta===null?l[0].id:sesAperta,true)}catch(e){}}
$("sesLista").onclick=e=>{const t=e.target.closest(".sess");if(t){apriSessione(parseInt(t.dataset.s));giroSessioni()}};
let CMP={a:"",b:""};
async function apriSessione(id,silenzioso){sesAperta=id;let j;try{j=(await api("/api/sessione?id="+id+(CMP.a&&CMP.b?"&a="+encodeURIComponent(CMP.a)+"&b="+encodeURIComponent(CMP.b):""))).sessione}catch(e){return}
 if(!j){$("rep").innerHTML="";return}ultimaSes=j;disegnaReport(j);
 let t=null;try{t=(await api("/api/pista?nome="+encodeURIComponent(j.pista))).pista}catch(e){}j._t=t;disegnaReport(j)}
function coloreSeg(ms){return ms<=-20?"#2ecc71":ms>=20?"#ff4d4d":"#cfd6e2"}
function disegnaReport(j){
 const c=j.confronto,rif=c&&c.rif&&(c.rif.scelto||c.rif[rifSel]||c.rif.precedente||c.rif.record),rifNome=c&&c.rif&&c.rif.scelto?"scelto":(c&&c.rif&&c.rif[rifSel]?rifSel:(c&&c.rif&&c.rif.precedente?"precedente":"record"));
 let h=`<div class="w intest" data-f="dettaglio" data-t="Report della sessione"><h2>${esc(bello(j.pista))} · ${esc(bello(j.auto))}</h2><span class="mu">${dt(j.data)}</span>${j.tipo?`<span class="pill on">${esc(j.tipo)}</span>`:""}<span>Miglior giro <b class="big">${esc(j.miglior_giro)}</b></span><span class="mu">${j.giri} giri · costanza ${(j.costanza_ms/1000).toFixed(1)} s${j.blocchi_totali?" · "+j.blocchi_totali+" blocchi":""}</span></div>`;
 // mappa
 h+=`<div class="w mappa" data-f="confronto" data-t="Mappa e confronto"><div class="row"><b>Dove sei migliorato e peggiorato</b><span class="sw">${c&&c.rif&&c.rif.precedente?`<button data-r="precedente" class="${rifNome==="precedente"?"act":""}">Sessione precedente</button>`:""}${c&&c.rif&&c.rif.record?`<button data-r="record" class="${rifNome==="record"?"act":""}">Tuo record</button>`:""}</span></div>${(()=>{const D=(j.dettaglio_giri||[]).filter(x=>x.k);if(!D.length)return"";const mig=D.reduce((m,x)=>x.k&&(!m||x.k<m.k)?x:m,null),best=D.slice().sort((x,y)=>String(x.tempo).localeCompare(String(y.tempo)))[0],ka=CMP.a||best.k;
  const R=j.riferimenti||[],O=j.giri_confronto||[],kb=CMP.b||(R[0]?R[0].k:"");
  const opt=(k,t)=>`<option value="${esc(k)}"${k===kb?" selected":""}>${esc(t)}</option>`;
  return `<div class="cmpbox"><div><small class="mu">1) Scegli il tuo giro di questa sessione</small><table class="cmpt">${D.map(x=>`<tr><td><input type="radio" name="cmpA" value="${esc(x.k)}"${x.k===ka?" checked":""}></td><td>Giro ${x.giro}</td><td><b>${esc(x.tempo)}</b></td><td class="mu">${x.pulito?"":"lento o sporco"}</td></tr>`).join("")}</table></div>
  <div><small class="mu">2) Confrontalo con</small><select id="cmpB"><optgroup label="Giri di riferimento">${R.map(r=>opt(r.k,r.nome+" · "+tempoMs(r.tempo_ms))).join("")}</optgroup><optgroup label="Altri tuoi giri su questa pista">${O.map(x=>opt(x.k,"Giro "+tempoMs(x.tempo_ms)+" · "+new Date(x.ts*1000).toLocaleString("it-IT",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"})+(x.record?" ★":""))).join("")}</optgroup></select>
  <div class="row"><button class="pri" data-cmp="vai">Confronta</button>${CMP.a?`<button data-cmp="auto">Confronti automatici</button>`:""}</div></div></div>`})()}`;
 if(j._t){const [X,Z]=ruota(j._t.x,j._t.z,rotGet(j.pista)),b=limiti(X,Z),n=X.length;let sv="";
  if(rif){const per=n/rif.segmenti.length;rif.segmenti.forEach((ms,s)=>{const a=Math.floor(s*per),e=Math.min(n,Math.floor((s+1)*per)+1);const pts=[];for(let i=a;i<=e;i++)pts.push(xy(X[i%n],Z[i%n],b).map(v=>v.toFixed(1)).join(","));sv+=`<polyline points="${pts.join(" ")}" fill="none" stroke="${coloreSeg(ms)}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>`});
   [].concat(rif.guadagni,rif.perdite).forEach(s=>{const i=Math.floor((s+0.5)*n/rif.segmenti.length)%n,q=xy(X[i],Z[i],b);sv+=`<circle cx="${q[0]}" cy="${q[1]}" r="11" fill="#0b0e13" stroke="${coloreSeg(rif.segmenti[s])}" stroke-width="2"/><text x="${q[0]}" y="${q[1]+4}" text-anchor="middle" font-size="11" fill="#fff">${s+1}</text>`})}
  else sv=`<polygon points="${punti(X,Z,b)}" fill="none" stroke="#e8ecf2" stroke-width="6" stroke-linejoin="round"/>`;
  (j.blocchi_pos||[]).forEach(k=>{const i=Math.min(n-1,Math.floor(k.pos*n)),q=xy(X[i],Z[i],b);sv+=`<circle cx="${q[0]}" cy="${q[1]}" r="6" fill="#ffc233" stroke="#000" stroke-width="1.5"/>`});
  h+=`<svg viewBox="0 0 300 300">${sv}</svg><div class="leg"><span><i style="background:#2ecc71"></i>più veloce</span><span><i style="background:#ff4d4d"></i>più lento</span><span><i style="background:#ffc233"></i>blocco in frenata</span></div><div class="row"><button data-rot="-10">↺ Ruota</button><button data-rot="10">Ruota ↻</button><button data-rot="90">90°</button><button data-rot="0">Azzera</button></div>`}
 else h+=`<p class="mu">Il disegno della pista compare dopo un giro completo guidato su questa pista.</p>`;
 h+="</div>";
 // frasi
 h+=`<div class="w" data-f="confronto" data-t="Cosa è cambiato"><b>Cosa è cambiato</b>`;
 if(rif){const tot=c.mio.tempo_ms-rif.tempo_ms;h+=`<p>${rifNome==="scelto"?"Il giro A":"Il tuo miglior giro di questa sessione"} è <b class="${tot<0?"mig":"peg"}">${sec(tot,true)} s</b> rispetto ${rifNome==="precedente"?"alla sessione precedente":rifNome==="scelto"?"all'altro giro scelto":"al tuo record"} (${tempoMs(rif.tempo_ms)}).</p>`;
  const riga=(s)=>`<li>Microsettore ${s+1} (dal ${Math.round(s*100/rif.segmenti.length)}% al ${Math.round((s+1)*100/rif.segmenti.length)}% del giro): <b class="${rif.segmenti[s]<0?"mig":"peg"}">${sec(rif.segmenti[s],true)} s</b></li>`;
  h+=rif.guadagni.length?`<p class="mig">Dove sei migliorato</p><ul>${rif.guadagni.map(riga).join("")}</ul>`:`<p class="mu">Nessun tratto in cui sei migliorato in modo netto.</p>`;
  h+=rif.perdite.length?`<p class="peg">Dove sei peggiorato</p><ul>${rif.perdite.map(riga).join("")}</ul>`:`<p class="mu">Nessun tratto in cui sei peggiorato in modo netto.</p>`}
 else h+=`<p class="mu">Per il confronto servono giri registrati su questa pista in almeno due sessioni.</p>`;
 h+=`<ul>${j.note.map(n=>"<li>"+esc(n)+"</li>").join("")}</ul></div>`;
 // grafico
 if(c){const v=c.mio.v,m=Math.max(...v,...(rif?rif.v:[]),1);const lin=(a,col)=>`<polyline fill="none" vector-effect="non-scaling-stroke" stroke="${col}" stroke-width="2" points="${a.map((y,i)=>(i/(a.length-1)*600).toFixed(1)+","+(110-y/m*100).toFixed(1)).join(" ")}"/>`;
  let g=`<svg viewBox="0 0 600 120" preserveAspectRatio="none" style="width:100%;height:9em">${rif?lin(rif.v,"#8f9aae"):""}${lin(v,"#ff5a1f")}</svg>`;
  if(rif){const d=rif.delta,dm=Math.max(...d.map(Math.abs),100);g+=`<svg viewBox="0 0 600 80" preserveAspectRatio="none" style="width:100%;height:6em"><line x1="0" x2="600" y1="40" y2="40" stroke="#444" vector-effect="non-scaling-stroke"/><polyline fill="none" vector-effect="non-scaling-stroke" stroke="#ffc233" stroke-width="2" points="${d.map((y,i)=>(i/(d.length-1)*600).toFixed(1)+","+(40+y/dm*36).toFixed(1)).join(" ")}"/></svg><div class="leg"><span>Sopra: velocità lungo il giro (arancione = tu, grigio = riferimento)</span><span>Sotto: tempo perso (giù = più veloce)</span></div>`}
  if(rif&&rif.f){const l2=(a,col)=>`<polyline fill="none" vector-effect="non-scaling-stroke" stroke="${col}" stroke-width="2" points="${a.map((y,i)=>(i/(a.length-1)*600).toFixed(1)+","+(66-Math.min(1,y)*60).toFixed(1)).join(" ")}"/>`;
   const gr=(t,A,B)=>`<div class="mu" style="margin-top:.5em">${t}</div><svg viewBox="0 0 600 70" preserveAspectRatio="none" style="width:100%;height:5em">${l2(B,"#8f9aae")}${l2(A,"#ff5a1f")}</svg>`;
   g+=gr("Freno (arancione = il tuo giro, grigio = l'altro)",c.mio.f,rif.f)+gr("Gas",c.mio.g,rif.g)}
  h+=`<div class="w tab" data-f="confronto" data-t="Velocità lungo il giro"><b>Telemetria del confronto</b>${g}</div>`}
 // tabella
 h+=`<div class="w tab" data-f="dettaglio" data-t="Tabella dei giri"><b>Giri</b><table><tr><th>Giro</th><th>Tempo</th><th>Carburante</th><th></th></tr>${j.dettaglio_giri.map(x=>`<tr><td>${x.giro}</td><td>${x.tempo}</td><td>${x.carburante==null?"—":x.carburante}</td><td>${x.pulito?"":"lento o sporco "}${x.blocchi?"🔒 "+x.blocchi+" blocchi":""}</td></tr>`).join("")}</table>`;
 if(j.carburante_inizio!=null)h+=`<p class="mu">Carburante: da ${j.carburante_inizio} a ${j.carburante_fine} L.</p>`;
 if(j.gomme&&j.gomme.temperatura_media_C){const t=j.gomme.temperatura_media_C,p=j.gomme.pressione_media_psi;h+=`<p class="mu">Gomme (media): `+Object.keys(t).map(k=>`${bello(k)} ${t[k]}° / ${p[k]} psi`).join(" · ")+`</p>`}
 h+="</div>";
 $("rep").innerHTML=h;applicaModo();
}
$("rep").onclick=e=>{const ro=e.target.closest("button[data-rot]");if(ro){const v=+ro.dataset.rot;rotSet(sesAperta&&ultimaSes?ultimaSes.pista:"",v===0?0:rotGet(ultimaSes.pista)+v);tracciato=null;pistaMappa=null;apriSessione(sesAperta);return}const c=e.target.closest("button[data-cmp]");if(c){if(c.dataset.cmp==="vai"){const r=document.querySelector("input[name=cmpA]:checked");if(!r)return;CMP={a:r.value,b:$("cmpB").value}}else CMP={a:"",b:""};apriSessione(sesAperta);return}
 const b=e.target.closest("button[data-r]");if(b&&ultimaSes){rifSel=b.dataset.r;if(CMP.a){CMP={a:"",b:""};apriSessione(sesAperta)}else disegnaReport(ultimaSes)}};

/* ---------- SETUP ---------- */
function listaSetup(){const f=(SETUP.file||[]);$("setupLista").innerHTML=f.length?"<table>"+f.map(x=>`<tr><td>${esc(bello(x.auto))}</td><td>${esc(bello(x.pista))}</td><td>${esc(x.nome)}</td><td class="${x.valido?"mig":"peg"}">${x.valido?"letto":"non letto"}</td></tr>`).join("")+"</table>":"Apri ACC e salva un setup."}
function riempiAss(){const s=$("assFile");const f=(SETUP.file||[]).filter(x=>x.valido);const sig=f.map(x=>x.auto+x.pista+x.nome).join("|");if(s.dataset.sig===sig)return;s.dataset.sig=sig;const cur=s.value;s.innerHTML=f.length?f.map(x=>`<option value="${esc(x.auto)}/${esc(x.pista)}/${esc(x.nome)}">${esc(bello(x.auto))} · ${esc(bello(x.pista))} · ${esc(x.nome)}</option>`).join(""):'<option value="">Nessun setup trovato: salvane uno in ACC</option>';if(cur)s.value=cur}
async function assChiedi(modo){const file=$("assFile").value;if(!file){$("assMsg").textContent="Salva prima un setup in ACC.";return}
 $("assMsg").textContent=modo==="pressioni"?"Controllo le pressioni a caldo dei tuoi ultimi giri...":"Claude sta lavorando (anche un minuto per il setup base)...";$("assRis").innerHTML="";let j;try{j=await api("/api/assistente/proponi",{file:file,sensazioni:$("assSens").value,modo:modo})}catch(e){$("assMsg").textContent="Il programma non risponde.";return}
 if(!j.ok){$("assMsg").textContent="Non riuscito: "+j.errore;return}
 $("assMsg").textContent="";assId=j.id||null;if(j.modifiche&&j.modifiche.length)$("assSens").value="";
 let h=`<div class="card"><b>${esc(j.problema||"Proposta")}</b><p class="mu">${esc(j.spiegazione||"")}</p>`;
 if(j.modifiche.length){h+="<table>"+j.modifiche.map(m=>`<tr><td>${esc(m.nome)}</td><td>${m.click>0?"+":""}${m.click} click</td><td>${esc(m.motivo)}</td></tr>`).join("")+"</table>";
  h+=`<p><b>Setup creato:</b> ${esc(j.nuovo_file)}<br>In ACC apri la lista dei setup, scegli questo nome e caricalo.</p><p class="mu">${esc(j.cosa_aspettarsi||"")}</p><p class="mu">Dopo almeno 4 giri puliti con questo setup il programma dice da solo se è andato meglio, uguale o peggio.</p>`}
 else h+=`<p>Nessuna modifica proposta.</p><p class="mu">${esc(j.cosa_aspettarsi||"")}</p>`;
 if((j.suggerimenti_pilota||[]).length)h+="<p><b>Da cambiare tu (ABS, controllo trazione, mappa motore):</b></p><ul>"+j.suggerimenti_pilota.map(x=>"<li>"+esc(x)+"</li>").join("")+"</ul>";
 $("assRis").innerHTML=h+"</div>";giroQuaderno()}
$("assPress").onclick=()=>assChiedi("pressioni");$("assBase").onclick=()=>assChiedi("base");$("assVai").onclick=()=>assChiedi("migliora");
async function giroQuaderno(){try{const j=await api("/api/assistente");const q=(j.quaderno||[]).slice().reverse();
 $("assStile").textContent=j.giri_registrati?"Giri registrati per imparare il tuo stile: "+j.giri_registrati+(j.stile?" (profilo pronto)":" (ne servono almeno 3 puliti)"):"Guida con Simapex aperto: registra in silenzio il tuo stile di guida, giro per giro.";
 if(!q.length){$("quad").textContent="Ancora nessun setup creato.";return}
 $("quad").innerHTML="<table>"+q.map((x,i)=>`<tr><td>${esc(x.nuovo||"")}<small class="mu"><br>${esc(x.problema||"")}</small></td><td><b class="${x.esito==="meglio"?"mig":x.esito==="peggio"?"peg":""}">${esc(x.esito?x.esito.toUpperCase():"in attesa dei giri")}</b>${x.esito_motivo?`<small class="mu"><br>${esc(x.esito_motivo)}</small>`:""}${i===0&&x.esito&&x.esito_auto?`<br><small class="mu">Non sei d'accordo?</small> <button data-e="meglio" data-id="${x.id}">Meglio</button><button data-e="uguale" data-id="${x.id}">Uguale</button><button data-e="peggio" data-id="${x.id}">Peggio</button>`:""}</td></tr>`).join("")+"</table>"}catch(e){}}
$("quad").onclick=async e=>{const b=e.target.closest("button[data-e]");if(!b)return;await api("/api/assistente/esito",{id:parseInt(b.dataset.id),esito:b.dataset.e});giroQuaderno()};
async function micControllo(){try{const s=await navigator.mediaDevices.getUserMedia({audio:true});s.getTracks().forEach(t=>t.stop());return null}catch(e){const n=e&&e.name;
 if(n==="NotFoundError"||n==="OverconstrainedError")return"Windows non vede nessun microfono: controlla in Impostazioni → Sistema → Audio → Ingresso che le cuffie siano scelte come microfono.";
 if(n==="NotReadableError")return"Il microfono è occupato da un altro programma (Discord, il gioco, ecc.). Chiudi quello o scegli un altro ingresso.";
 if(n==="NotAllowedError"||n==="SecurityError")return"Il browser blocca il microfono (errore: "+n+"). Se Windows è già a posto, chiudi Simapex e riaprilo dopo l'aggiornamento: ora usa un profilo suo.";
 return"Errore del microfono: "+(n||e)}}
(function(){const R=window.SpeechRecognition||window.webkitSpeechRecognition;const M=t=>{$("assMsg").textContent=t};
 if(!R){$("assMic").onclick=()=>M("Questo browser non ha il riconoscimento vocale. Clicca nella casella e premi Windows + H per dettare.");return}
 let rec=null,on=false;
 $("assMic").onclick=async()=>{if(on){rec&&rec.stop();return}
  const er=await micControllo();if(er){M(er);return}
  try{rec=new R();rec.lang="it-IT";rec.continuous=true;rec.interimResults=false;
  rec.onstart=()=>{M("Sto ascoltando... parla pure.")};
  rec.onresult=ev=>{let t="";for(let i=ev.resultIndex;i<ev.results.length;i++)t+=ev.results[i][0].transcript+" ";$("assSens").value=($("assSens").value+" "+t).trim()};
  rec.onerror=ev=>{const e=ev.error;M(e==="not-allowed"||e==="service-not-allowed"?"Il microfono non parte (codice: "+e+"). In Windows apri Impostazioni → Privacy e sicurezza → Microfono e consenti anche le app desktop; poi Parlato → Riconoscimento vocale online: attivo. Intanto puoi dettare con Windows + H nella casella.":e==="audio-capture"?"Non trovo nessun microfono collegato.":e==="network"?"Il riconoscimento vocale non riesce a collegarsi a internet. Intanto puoi dettare con Windows + H nella casella.":e==="no-speech"?"Non ho sentito niente: riprova e parla più vicino al microfono.":"Microfono: errore "+e+". Puoi dettare con Windows + H nella casella.")};
  rec.onend=()=>{on=false;$("assMic").textContent="🎤 Parla"};rec.start();on=true;$("assMic").textContent="⏹ Stop"}catch(x){on=false;M("Microfono: "+x.message+". Puoi dettare con Windows + H nella casella.")}}})();

/* ---------- PERCORSO ---------- */
const AUTO={acc:()=>!!ST.collegato&&ST.stato_codice===2,gomme:()=>(ST.temp_gomme||[]).some(x=>x>0),giri:()=>(ST.giri_completati||0)>=3,delta:()=>ST.delta_ms!=null,carburante:()=>!!ST.consumo_giro,mappa:()=>!!tracciato,sessioni:()=>!!ultimaSes,apre:()=>!!ST.versione,
 ing_spotter:()=>(ST.vicini||[]).length>0,f1_distacchi:()=>ST.gioco==="F1 25"&&ST.distacco_davanti_ms!=null,f1_udp:()=>ST.gioco==="F1 25"&&!!ST.collegato,f1_giri:()=>ST.gioco==="F1 25"&&(ST.giri_completati||0)>=3,f1_mappa:()=>ST.gioco==="F1 25"&&!!tracciato,f1_carb:()=>ST.gioco==="F1 25"&&!!ST.consumo_giro,f1_usura:()=>ST.gioco==="F1 25"&&!!ST.usura_gomme,f1_delta:()=>ST.gioco==="F1 25"&&ST.delta_ms!=null,ing_voce:()=>ING.voce,ing_giro:()=>ING.msgs.some(m=>/^Giro \d/.test(m.testo)),ing_blocco:()=>ING.msgs.some(m=>/Bloccaggio/.test(m.testo)),box:()=>BOXL.length>1};
function statoAuto(){const o={};for(const k in AUTO){try{o[k]=!!AUTO[k]()}catch(e){o[k]=false}}return o}
/* ---------- PROVE ---------- */
function disegnaProve(){const el=$("proveLista");if(!el)return;let h="";
 TUTTE().forEach((p,i)=>{const x=FUN[p.id]||{};if(p.g)h+=`<h3>${p.g}</h3>`;
  const au=AUTO[p.id]&&AUTO[p.id]();h+=`<div class="prova"><b>${i+1}. ${esc(p.t)}</b><span class="st ${x.s==="ok"?"ok":x.s==="ko"?"ko":""}"> ${x.s==="ok"?"Funziona":x.s==="ko"?"Non funziona":""}</span>${au?`<span class="pill on" style="margin-left:.5em">visto dal programma</span>`:""}<ol>${p.p.map(s=>`<li>${esc(s)}</li>`).join("")}</ol>${p.r?`<div class="st" style="color:var(--ye)"><b>Ritmo e mappa:</b> ${esc(p.r.replace(/__MAPPA_C__/g,testoMappa(MAPPE&&MAPPE.mappa_giri_costanti)).replace(/__MAPPA_S__/g,testoMappa(MAPPE&&MAPPE.mappa_spinta)))}</div>`:""}<div class="mu">Cosa deve succedere: ${esc(p.a.replace("__VERSIONE__",ST.versione||""))}</div><div class="row"><button class="ok ${x.s==="ok"?"sel":""}" data-p="${p.id}" data-s="ok">Funziona</button><button class="ko ${x.s==="ko"?"sel":""}" data-p="${p.id}" data-s="ko">Non funziona</button></div><textarea data-n="${p.id}" placeholder="Nota (facoltativa)">${esc(x.n||"")}</textarea></div>`});
 h=`<div class="prova"><b>Commento generale</b><div class="mu">Scrivi qui qualsiasi cosa che non va o che vorresti diverso, anche non legata a un punto preciso.</div><textarea data-n="generale" placeholder="Commento libero">${esc((FUN.generale||{}).n||"")}</textarea></div>`+h;
 if(el.dataset.h!==h){const f=document.activeElement;if(f&&f.dataset&&f.dataset.n)return;el.innerHTML=h;el.dataset.h=h}}
$("proveLista").onclick=e=>{const b=e.target.closest("button[data-p]");if(b)setFun(b.dataset.p,{s:b.dataset.s})};
$("proveLista").addEventListener("change",e=>{const t=e.target.closest("textarea[data-n]");if(t)setFun(t.dataset.n,{n:t.value})});


/* ---------- INGEGNERE DI PISTA E ASSISTENTE AI BOX ---------- */
let SPOT={on:true,inv:false,prev:""};
try{SPOT.on=localStorage.getItem("simapex_spotter")!=="0";SPOT.inv=localStorage.getItem("simapex_spotter_inv")==="1"}catch(e){}
const TIPI_S={0:"prove libere",1:"qualifica",2:"gara",3:"giro lanciato"};
const RUOTE_IT={ant_sx:"anteriore sinistra",ant_dx:"anteriore destra",post_sx:"posteriore sinistra",post_dx:"posteriore destra"};
let ING={consigli:[],voce:false,msgs:[],ult:{},prev:{},blocchi:0,sess:null,usura:[],coda:[],tempi:[],giriDaBox:0},BOXL=[];
try{ING.voce=localStorage.getItem("simapex_voce")==="1"}catch(e){}
const F1G=()=>ST.gioco==="F1 25";
const media=a=>a&&a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
function sicuro(){const u=ST;return u.in_box||(u.velocita||0)<25||((u.freno||0)<0.1&&Math.abs(u.sterzo||0)<0.2)}
let AC=null;function bip(f,ms){try{AC=AC||new (window.AudioContext||window.webkitAudioContext)();const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=f;g.gain.value=0.08;o.connect(g);g.connect(AC.destination);o.start();o.stop(AC.currentTime+ms/1000)}catch(e){}}
ING.freq="normale";try{ING.freq=localStorage.getItem("simapex_freq")||"normale"}catch(e){}
function emetti(testo,grave){if(ING.voce)bip(1300,45);ING.msgs.unshift({t:new Date(),testo});if(ING.msgs.length>30)ING.msgs.length=30;
 if(ING.voce&&window.speechSynthesis){try{const u=new SpeechSynthesisUtterance(testo);u.lang="it-IT";const v=speechSynthesis.getVoices().find(x=>x.lang&&x.lang.toLowerCase().startsWith("it"));if(v)u.voice=v;u.rate=1.05;if(grave)speechSynthesis.cancel();speechSynthesis.speak(u)}catch(e){}}
 if(schermo==="pista")disegnaBox()}
function parla(chiave,testo,cool,grave){const t=Date.now();if(chiave&&ING.ult[chiave]&&t-ING.ult[chiave]<(cool==null?60000:cool))return;if(chiave)ING.ult[chiave]=t;
 if(grave||sicuro()){emetti(testo,grave);return}
 ING.coda.push({t,testo});if(ING.coda.length>3)ING.coda.shift()}
function svuotaCoda(){if(!ING.coda.length||!sicuro())return;const t=Date.now();ING.coda=ING.coda.filter(x=>t-x.t<25000);const x=ING.coda.shift();if(x)emetti(x.testo,false)}
function parlaTempo(t){const m=/^(\d+):(\d+)\.(\d+)/.exec(t||"");return m?`${+m[1]} ${+m[1]===1?"minuto":"minuti"} e ${+m[2]} secondi e ${+m[3]}`:(t||"")}
const decimi=ms=>{const d=Math.abs(ms)/100;return d<10?(Math.round(d)===1?"1 decimo":Math.round(d)+" decimi"):(Math.abs(ms)/1000).toFixed(1).replace(".",",")+" secondi"};
function ingegnere(){const u=ST;if(!u.collegato||u.stato_codice!==2)return;
 const chiave=(u.auto||"")+"|"+(u.pista||"")+"|"+u.sessione,P=ING.prev;
 if(ING.sess!==chiave){ING.sess=chiave;ING.prev={};ING.blocchi=0;ING.usura=[];ING.ult={};ING.coda=[];ING.tempi=[];ING.giriDaBox=0;
  const tp=TIPI_S[u.sessione];parla(null,(tp?"Sessione di "+tp:"Sessione")+(u.pista?" a "+bello(u.pista):"")+". Buon lavoro.");return}
 const U=F1G()?"chili":"litri";
 // consigli di guida dell'ultimo giro (microsettore dove hai perso di più)
 const cg=u.consiglio_guida;if(cg&&cg.testo&&cg.ts!==P.cgts&&P.cgts!==undefined){ING.consigli.unshift({t:new Date(),testo:cg.testo,micro:cg.micro,breve:cg.breve});if(ING.consigli.length>12)ING.consigli.length=12;ING.cg=cg;if(ING.freq!=="minima")parla("guida"+cg.ts,cg.testo,0)}
 // avviso in tempo reale a inizio del microsettore dove hai perso
 if(ING.cg&&ING.freq!=="minima"&&P.pn!=null&&u.pos_norm!=null&&u.sessione!==2||ING.cg&&ING.freq==="alta"&&P.pn!=null){const st=Math.max(0,(ING.cg.micro-1)/25-0.025);if(P.pn<st&&(u.pos_norm||0)>=st&&(u.pos_norm||0)<st+0.05)parla("live"+ING.cg.micro,"Attento: microsettore "+ING.cg.micro+". "+ING.cg.breve.charAt(0).toUpperCase()+ING.cg.breve.slice(1)+".",30000)}
 // blocchi in frenata
 if(u.blocco_ruota&&!P.blocco){ING.blocchi++;parla("blocco",`Bloccaggio ${RUOTE_IT[u.blocco_ruota]||"ruota"}. Frena meno forte all'inizio e rilascia con progressione.`,12000,true)}
 // giro completato
 const gc=u.giri_completati||0;
 if(P.gc!=null&&gc>P.gc&&u.ultimo_giro_ms>0&&u.ultimo_giro_ms<36000000){
  const nuovoMigliore=u.ultimo_giro_ms<=u.miglior_giro_ms&&gc>=2;
  let t="Giro "+gc+", "+parlaTempo(u.ultimo_giro)+". ";
  if(nuovoMigliore)t+="Nuovo giro migliore!";
  else if(u.miglior_giro_ms>0&&u.miglior_giro_ms<36000000)t+="A "+decimi(u.ultimo_giro_ms-u.miglior_giro_ms)+" dal tuo migliore.";
  if(u.sessione===2&&u.posizione>0)t+=" Sei "+u.posizione+"°.";
  parla("giro"+gc,t,0);
  if(u.giri_totali&&u.giri_totali-gc===1)parla("ultimo","Ultimo giro. Dai tutto.",0);
  if(u.giri_totali&&gc>=u.giri_totali&&u.sessione===2)parla("fine","Gara finita. Chiudi in "+u.posizione+"°. Ottimo lavoro, rientra ai box.",0,true);
 }
 // radio da ingegnere: consigli a fine giro
 consigliGiro(u,gc);
 // posizione in gara
 if(u.sessione===2&&u.posizione>0&&P.pos&&u.posizione!==P.pos&&gc>=1)parla("pos",(u.posizione<P.pos?"Guadagnato una posizione":"Perso una posizione")+", ora "+u.posizione+"°.",10000);
 // carburante
 const gf=F1G()&&u.giri_carburante_gioco!=null?u.giri_carburante_gioco:u.giri_stimati;
 if(gf!=null&&!u.in_box&&(F1G()?true:u.consumo_giro)){
  if(gf<=1.5)parla("carb2","Box box. Carburante quasi finito.",60000,true);
  else if(gf<=3.2&&u.sessione!==3)parla("carb1","Carburante: restano circa "+Math.floor(gf)+" giri.",150000)}
 // gomme: temperature
 const tg=media(u.temp_gomme);
 if(tg!=null&&tg>0&&(u.velocita||0)>60){const caldo=F1G()?118:100,freddo=F1G()?70:65;
  if(tg>caldo)parla("g_caldo","Gomme molto calde, "+Math.round(tg)+" gradi. Alleggerisci le entrate di curva.",120000);
  else if(tg<freddo&&gc>=1&&u.sessione!==3)parla("g_freddo","Gomme fredde, "+Math.round(tg)+" gradi. Scaldale con calma prima di spingere.",120000)}
 // gomme: pressioni a caldo (solo ACC)
 if(!F1G()&&gc>=3&&(u.velocita||0)>50&&(u.pressioni||[]).length===4){const n=["anteriore sinistra","anteriore destra","posteriore sinistra","posteriore destra"];
  const f=u.pressioni.map((x,i)=>x>0&&(x<26.4||x>27.0)?n[i]+" "+x.toFixed(1):null).filter(Boolean);
  if(f.length)parla("press","Pressioni a caldo fuori intervallo: "+f.join(", ")+". Fine sessione le correggiamo.",300000)}
 // usura F1
 if(F1G()&&u.usura_gomme){const m=Math.max(...u.usura_gomme);
  if(m>=75)parla("us75","Box box. Gomme finite, usura al "+Math.round(m)+" per cento.",120000,true);
  else if(m>=60)parla("us60","Usura gomme al "+Math.round(m)+" per cento: valuta il box.",180000)}
 // safety car e bandiere
 if(u.safety_car&&!P.sc)parla("sc",(u.safety_car==="safety car virtuale"?"Safety car virtuale":"Safety car in pista")+". Rallenta: è un buon momento per il box.",0,true);
 else if(!u.safety_car&&P.sc)parla("scf","Si riparte. Attento al ripartire.",0);
 if(u.bandiera==="gialla"&&P.band!=="gialla")parla("bg","Bandiera gialla.",20000);
 if(u.bandiera==="blu"&&P.band!=="blu")parla("bb","Bandiera blu: lascia passare.",30000);
 // tempo rimasto (sessioni a tempo)
 const tr=u.tempo_rimasto_s;if(tr){for(const m of [600,300,60])if(P.tr>m&&tr<=m)parla("tr"+m,"Mancano "+(m/60)+(m===60?" minuto.":" minuti."),0)}
 // uscita e ingresso box
 if(P.box&&!u.in_box){ING.giriDaBox=0;parla('uscita',u.sessione===1?'Uscita dai box: giro di lancio. Scalda gomme e freni, poi attacca.':'Uscita dai box. Primo giro: scalda gomme e freni con calma.',0)}
 else if(!P.box&&u.in_box&&P.box!==undefined)parla('entra','Sei ai box. Limitatore inserito.',0,true);
 // delta a metà giro
 if(P.pn!=null&&P.pn<0.5&&(u.pos_norm||0)>=0.5&&u.delta_ms!=null&&Math.abs(u.delta_ms)>=100&&!u.in_box&&u.sessione!==0)parla('mezzo'+gc,'Mezzo giro: '+decimi(u.delta_ms)+(u.delta_ms<0?' avanti':' indietro')+' sul tuo migliore.'+(u.delta_ms>300?' Recupera nella seconda parte.':''),0);
 radioF1(u);
 ING.prev={cgts:cg?cg.ts:null,da:u.distacco_davanti_ms,db:u.distacco_dietro_ms,meteo:u.meteo,ers:u.ers_pct,blocco:!!u.blocco_ruota,gc,pos:u.posizione,sc:u.safety_car,band:u.bandiera,tr,box:!!u.in_box,pn:u.pos_norm};
 // storico usura per giro (F1)
 if(F1G()&&u.usura_gomme&&(ING.usura.length===0||ING.usura[ING.usura.length-1].gc!==gc))ING.usura.push({gc,w:media(u.usura_gomme)});
}

const secs=ms=>(ms/1000).toFixed(1).replace(".",",")+" secondi";
function radioF1(u){const P=ING.prev;if(!F1G())return;
 const da=u.distacco_davanti_ms,db=u.distacco_dietro_ms,pa=P.da,pb=P.db;
 if(da!=null&&pa!=null&&da<1000&&pa>=1000)parla("dav1","Sei a meno di un secondo da quello davanti. Attacca.",20000);
 if(db!=null&&pb!=null&&db<1000&&pb>=1000)parla("dietro1","Dietro a meno di un secondo: difendi la posizione.",20000);
 if(u.meteo&&P.meteo&&u.meteo!==P.meteo)parla("meteo","Meteo che cambia: ora "+u.meteo+(/pioggia|temporale/.test(u.meteo)?". Valuta le gomme da bagnato.":"."),0,true);
 if(u.ers_pct!=null&&u.ers_pct<8&&(P.ers==null||P.ers>=8))parla("ers","Batteria quasi scarica: usa il recupero in frenata.",90000)}
function consigliGiro(u,gc){const P=ING.prev;if(P.gc==null||gc<=P.gc)return;
 if(F1G()&&u.sessione===2&&(u.distacco_davanti_ms!=null||u.distacco_dietro_ms!=null)){
  const p=[];if(u.distacco_davanti_ms!=null)p.push("davanti "+secs(u.distacco_davanti_ms));if(u.distacco_dietro_ms!=null)p.push("dietro "+secs(u.distacco_dietro_ms));
  let t="Distacchi: "+p.join(", ")+".";
  if(P.da!=null&&u.distacco_davanti_ms!=null){const d=P.da-u.distacco_davanti_ms;if(Math.abs(d)>=150)t+=d>0?" Stai recuperando "+decimi(d)+" a giro.":" Quello davanti scappa di "+decimi(d)+" a giro."}
  if(u.ultimo_davanti_ms&&u.ultimo_giro_ms>0&&u.ultimo_giro_ms<36000000){const d=u.ultimo_giro_ms-u.ultimo_davanti_ms;if(Math.abs(d)>=100)t+=" Davanti fa "+decimi(d)+(d>0?" meglio di te.":" peggio di te.")}
  parla("gap"+gc,t,0)}
 const ok=u.ultimo_giro_ms>0&&u.ultimo_giro_ms<36000000;
 if(ok&&ING.giriDaBox>0)ING.tempi.push(u.ultimo_giro_ms);
 if(u.sessione===1&&ING.giriDaBox===0)parla("lancio","Giro di lancio finito. Ora il giro buono: spingi, gomme e freni sono pronti.",0);
 ING.giriDaBox++;
 const mp=(MAPPE&&MAPPE.mappa_giri_costanti)?" Usa la mappa "+MAPPE.mappa_giri_costanti+".":"";
 const ms=(MAPPE&&MAPPE.mappa_spinta)?" Metti la mappa "+MAPPE.mappa_spinta+".":"";
 // chiamata ai box: carburante, gomme, pioggia, safety car (gara)
 if(u.sessione===2&&!u.in_box){const c=margineCarb();let mot=null,urg=false;
  if(c.rimasti>0&&c.m!=null&&c.m<0&&(u.giri_carburante_gioco!=null?u.giri_carburante_gioco:c.rimasti)<=1.5){mot="il carburante sta finendo";urg=true}
  else if(F1G()&&u.usura_gomme){const w=Math.max(...u.usura_gomme);if(w>=70){mot="le gomme sono al "+Math.round(w)+" per cento di usura";urg=w>=80}}
  if(!mot&&u.meteo&&/pioggia|temporale/i.test(u.meteo)&&/media|dura|morbida|soft|medium|hard/i.test(u.mescola||"")&&P.meteo&&!/pioggia|temporale/i.test(P.meteo)){mot="sta piovendo, serve la gomma da bagnato";urg=true}
  if(mot&&gc!==ING.boxCall){ING.boxCall=gc;parla("boxcall"+gc,(urg?"Box, box, box! ":"Box questo giro. ")+"Entra ai box: "+mot+".",0,true)}}
 if(u.sessione===2&&ING.freq!=="minima"&&gc%(ING.freq==="alta"?2:3)===0)parla("riep"+gc,riepilogoRadio(u),0);
 if(u.sessione===2){const c=margineCarb();
  if(c.m!=null&&c.m<0)parla("save"+gc,"Risparmia carburante: alza prima delle staccate e non insistere sull'acceleratore."+mp+" Ti mancano "+Math.abs(c.m).toFixed(1).replace(".",",")+" giri di carburante.",0);
  else if(c.m!=null&&c.m>=2&&c.rimasti>0&&c.rimasti<=Math.max(3,(u.giri_totali||0)/3))parla("spingi"+gc,"Hai carburante in più: puoi spingere."+ms,0);
  if(F1G()&&ING.usura.length>=3&&c.rimasti!=null){const a=ING.usura[0],b=ING.usura[ING.usura.length-1];if(b.gc>a.gc){const r=(b.w-a.w)/(b.gc-a.gc),fine=b.w+r*c.rimasti;
    if(fine>75&&r>0)parla("gestisci","Gestisci le gomme: perdi circa "+r.toFixed(1).replace(".",",")+" per cento a giro. Obiettivo box tra "+Math.max(1,Math.floor((70-b.w)/r))+" giri.",0);
    else if(fine<55&&r>=0&&gc>=4)parla("gomme_ok","Le gomme reggono bene: puoi alzare il ritmo.",0)}}
  if(ING.tempi.length>=3){const l=ING.tempi.slice(-3);if(Math.max(...l)-Math.min(...l)<500)parla("ritmo","Ritmo costante, ottimo. Mantieni così.",0)}}
 else if(u.sessione===0&&ING.tempi.length>=5)parla("prove5","Hai fatto abbastanza giri puliti per misurare passo e consumo. Se vuoi, rientra e prepariamo la gara.",0)}
function riepilogoRadio(u){const c=margineCarb(),P=[];if(u.posizione>0)P.push("posizione "+u.posizione);
 if(c.gf!=null)P.push("carburante per "+c.gf.toFixed(1).replace(".",",")+" giri"+(c.m!=null?(c.m<0?", non bastano":", bastano"):""));
 if(F1G()&&u.usura_gomme)P.push("gomme al "+Math.round(media(u.usura_gomme))+" per cento");else{const t=media(u.temp_gomme);if(t>0)P.push("gomme a "+Math.round(t)+" gradi")}
 const l=ING.tempi.slice(-3);if(l.length>=2)P.push("passo "+parlaTempo(tempoMs(media(l))));return "Aggiornamento. "+P.join(", ")+"."}
function margineCarb(){const u=ST,gc=u.giri_completati||0;let gf=u.giri_stimati;if(F1G()&&u.giri_carburante_gioco!=null)gf=u.giri_carburante_gioco;
 let rimasti=null;if(u.giri_totali)rimasti=u.giri_totali-gc;else if(u.tempo_rimasto_s&&u.miglior_giro_ms>0&&u.miglior_giro_ms<36000000)rimasti=Math.ceil(u.tempo_rimasto_s/(u.miglior_giro_ms/1000))+1;
 return{gf,rimasti,m:(gf!=null&&rimasti!=null)?gf-rimasti:null}}
function strategia(){const u=ST,L=[];if(!u.collegato){return["Entra in pista: ti dico carburante, gomme e quando rientrare."]}
 const U=F1G()?"kg":"L",gc=u.giri_completati||0,tp=TIPI_S[u.sessione];
 L.push((tp?"Sessione: "+tp+". ":"")+(u.auto?bello(u.auto)+" a "+bello(u.pista||"")+".":""));
 const c=u.carburante,cons=u.consumo_giro;
 let gf=u.giri_stimati;if(F1G()&&u.giri_carburante_gioco!=null)gf=u.giri_carburante_gioco;
 if(c!=null)L.push("Carburante: "+c.toFixed(1)+" "+U+(cons?", consumo "+cons.toFixed(2)+" "+U+" a giro":" (il consumo si misura dopo 2-3 giri puliti)")+(gf!=null?", circa "+gf.toFixed(1)+" giri.":"."));
 let rimasti=null;
 if(u.giri_totali)rimasti=u.giri_totali-gc;
 else if(u.tempo_rimasto_s&&u.miglior_giro_ms>0&&u.miglior_giro_ms<36000000)rimasti=Math.ceil(u.tempo_rimasto_s/(u.miglior_giro_ms/1000))+1;
 if(u.sessione===2){
  if(rimasti!=null&&gf!=null){const m=gf-rimasti;
   if(m>=1)L.push("Gara: mancano circa "+rimasti+" giri. Il carburante basta con "+m.toFixed(1)+" giri di margine: nessun pit per il carburante.");
   else if(m>=0)L.push("Gara: mancano circa "+rimasti+" giri e il carburante basta di poco ("+m.toFixed(1)+" giri di margine). Risparmia un po' o aggiungi un minimo al pit.");
   else L.push("Gara: mancano circa "+rimasti+" giri e il carburante non basta (ne mancano "+Math.abs(m).toFixed(1)+"). Serve un pit"+(cons?": aggiungi almeno "+((Math.abs(m)+1)*cons).toFixed(0)+" "+U+" (un giro di margine incluso).":"."))}
  else if(rimasti==null)L.push("Gara: non so quanti giri mancano (il gioco non li dà): con il consumo qui sopra calcola tu quando rientrare.");
  if(F1G()&&u.usura_gomme){const w=media(u.usura_gomme),H=ING.usura;let r=null;if(H.length>=3){const a=H[0],b=H[H.length-1];if(b.gc>a.gc)r=(b.w-a.w)/(b.gc-a.gc)}
   L.push("Gomme"+(u.mescola?" "+u.mescola:"")+(u.eta_gomme!=null?" ("+u.eta_gomme+" giri)":"")+": usura "+Math.round(w)+"%"+(r>0?", circa "+r.toFixed(1)+"% a giro: al 70% tra "+Math.max(0,Math.floor((70-w)/r))+" giri"+(rimasti!=null&&w+r*rimasti>70?". Prevedi una sosta per le gomme.":"."):"."))}
  else if(!F1G()&&u.temp_gomme){const t=media(u.temp_gomme);if(t>0)L.push("Gomme: temperatura media "+Math.round(t)+" °C ("+(t>100?"troppo calde: alleggerisci":t<65?"ancora fredde":"nel campo giusto")+").")}
  if(u.posizione>0)L.push("Posizione: "+u.posizione+"°.")}
 else if(u.sessione===1||u.sessione===3){
  L.push("Qualifica: fai un giro di lancio per scaldare gomme e freni, poi il giro buono, poi rientra a raffreddare. Meno carburante = più veloce: "+(gf!=null?"ne hai per "+gf.toFixed(1)+" giri; per il giro secco ne bastano 3.":"tieni solo quello che serve."));
  if(F1G()&&u.usura_gomme)L.push("Usura gomme: "+Math.round(media(u.usura_gomme))+"%.")}
 else{
  L.push("Prove: fai almeno 5 giri puliti con lo stesso carburante e lo stesso ritmo, così misuro consumo e passo e ti dico la strategia di gara.");
  if(gc>=3&&cons&&F1G()===false)L.push("Con questo consumo, una gara da 10 giri richiede circa "+(cons*10+cons).toFixed(0)+" "+U+" (un giro di margine incluso).")}
 return L}
function disegnaBox(){const m=$("ingMsgs");if(!m)return;
 m.innerHTML=ING.msgs.length?ING.msgs.map(x=>`<div><small>${x.t.toLocaleTimeString("it-IT")}</small> ${esc(x.testo)}</div>`).join(""):"Nessun messaggio ancora: entra in pista.";
 const cl=$("consigliLista");if(cl&&ING.consigli.length)cl.innerHTML=ING.consigli.map(x=>`<div><small>${x.t.toLocaleTimeString("it-IT")}</small> ${esc(x.testo)}</div>`).join("");
 const bi=$("boxInfo"),bx=ST.box_info;if(bi)bi.textContent=bx?"Corsia box: "+(bx.perdita_ms/1000).toFixed(1)+" s persi rispetto alla pista"+(bx.perdita_con_sosta_ms?", circa "+(bx.perdita_con_sosta_ms/1000).toFixed(1)+" s con la sosta.":"."):"Corsia box non ancora misurata: passa dai box una volta.";
 BOXL=strategia();const b=$("boxLinee");if(b)b.innerHTML=BOXL.map(l=>`<div>${esc(l)}</div>`).join("")}
$("ingVoce").checked=ING.voce;
$("ingVoce").onchange=e=>{ING.voce=e.target.checked;try{localStorage.setItem("simapex_voce",ING.voce?"1":"0")}catch(x){}};
$("ingProva").onclick=()=>{const v=ING.voce;ING.voce=true;parla(null,"Prova radio. Qui è l'ingegnere di pista, mi senti?",0,true);ING.voce=v;if(!window.speechSynthesis)$("ingRis").textContent="Questo programma non ha la voce: puoi comunque leggere i messaggi qui."};

/* ---------- DOMANDE ALL'INGEGNERE ---------- */
function rispostaLocale(q){q=q.toLowerCase();const u=ST,F=F1G();if(!u.collegato)return"Non sono collegato al gioco: entra in pista e chiedimelo.";
 const c=margineCarb(),gc=u.giri_completati||0,ms=x=>secs(x);
 if(/perdo|perdita|costa|costo|quanto tempo.*(box|pit|sosta)|pit ?stop/.test(q)){const b=u.box_info;if(!b)return"Non ho ancora misurato la corsia dei box su questa pista: fai un passaggio dai box (anche senza fermarti) e poi te lo dico.";
  const s1=x=>(x/1000).toFixed(1).replace(".",",");let t="La corsia box ti costa circa "+s1(b.perdita_ms)+" secondi rispetto alla pista"+(b.fermo_ms?"; con una sosta come le tue ("+s1(b.fermo_ms)+" secondi fermo) perdi circa "+s1(b.perdita_con_sosta_ms)+" secondi":"")+".";
  const loss=b.perdita_con_sosta_ms;if(F&&u.gap_leader_ms!=null&&u.gap_altri_ms){const nuovo=u.gap_leader_ms+loss,pos=1+u.gap_altri_ms.filter(g=>g<nuovo).length;t+=" Se rientri adesso e nessun altro rientra, torni in pista in posizione "+pos+(u.posizione>0?" (ora sei "+u.posizione+")":"")+"."}else if(!F)t+=" In ACC non conosco la posizione degli altri, quindi non so dove rientreresti.";return t}
 if(/distacc|davanti|chi ho/.test(q)&&!/dietro/.test(q))return F?(u.distacco_davanti_ms!=null?"Davanti hai "+ms(u.distacco_davanti_ms)+(u.distacco_davanti_ms<1000?". Sei in zona attacco.":"."):"Non ho il distacco: sei primo o non sono in gara."):"In ACC non ho i distacchi dagli avversari, solo i tuoi tempi.";
 if(/dietro|vantaggio|difend/.test(q))return F?(u.distacco_dietro_ms!=null?"Hai "+ms(u.distacco_dietro_ms)+" di vantaggio su quello dietro"+(u.distacco_dietro_ms<1000?": difenditi.":"."):"Non ho il dato: sei ultimo o non sono in gara."):"In ACC non ho i distacchi dagli avversari.";
 if(/ritmo|passo|differenza|veloc/.test(q)){const l=ING.tempi.slice(-3);let t=l.length?"Il tuo passo medio degli ultimi giri è "+tempoMs(media(l))+".":"Non ho ancora giri puliti per misurare il passo.";
  if(F&&u.ultimo_davanti_ms&&u.ultimo_giro_ms<36000000){const d=u.ultimo_giro_ms-u.ultimo_davanti_ms;t+=" Quello davanti ha fatto "+decimi(d)+(d>0?" meglio":" peggio")+" di te nell'ultimo giro."}
  if(F&&u.ultimo_dietro_ms&&u.ultimo_giro_ms<36000000){const d=u.ultimo_giro_ms-u.ultimo_dietro_ms;t+=" Quello dietro "+decimi(d)+(d>0?" meglio":" peggio")+"."}return t}
 if(/gomm|usura|pression/.test(q)){const t=media(u.temp_gomme);let r="Gomme: "+(t?Math.round(t)+" gradi di media":"temperature non disponibili");
  if(F&&u.usura_gomme)r+=", usura "+Math.round(media(u.usura_gomme))+" per cento"+(u.mescola?", mescola "+u.mescola:"")+(u.eta_gomme!=null?", "+u.eta_gomme+" giri":"");
  if(!F&&(u.pressioni||[]).length===4)r+=", pressioni "+u.pressioni.map(x=>x.toFixed(1)).join(" ");return r+"."}
 if(/carburante|benzina|serbatoio/.test(q))return u.carburante!=null?"Hai "+u.carburante.toFixed(1)+(F?" chili":" litri")+(c.gf!=null?", circa "+c.gf.toFixed(1)+" giri":"")+(c.m!=null?(c.m<0?". Non bastano: ti mancano "+Math.abs(c.m).toFixed(1)+" giri.":". Bastano fino alla fine con "+c.m.toFixed(1)+" giri di margine."):"."):"Non ho il dato del carburante.";
 if(/mete|piogg|bagnato|asciutto/.test(q))return F?"Meteo: "+(u.meteo||"non disponibile")+(u.temp_aria!=null?", aria "+Math.round(u.temp_aria)+", asfalto "+Math.round(u.temp_asfalto)+" gradi.":"."):"In ACC non ho il meteo. Asfalto "+Math.round(u.temp_asfalto||0)+" gradi.";
 if(/posizion|che sono|in che/.test(q))return u.posizione>0?"Sei in posizione "+u.posizione+".":"Non ho la posizione.";
 if(/quanti giri|mancano|rimast/.test(q))return c.rimasti!=null?"Mancano circa "+c.rimasti+" giri.":"Non so quanti giri mancano: la sessione non me lo dice.";
 if(/box|rientr|pit|sosta/.test(q)){const L=[];if(c.m!=null&&c.m<0)L.push("per il carburante serve un pit: ti mancano "+Math.abs(c.m).toFixed(1)+" giri");
  if(F&&u.usura_gomme){const w=media(u.usura_gomme);L.push(w>=60?"gomme al "+Math.round(w)+" per cento: rientra presto":"gomme al "+Math.round(w)+" per cento: per ora reggono")}
  if(u.safety_car)L.push("c'è la "+u.safety_car+": buon momento per rientrare");return L.length?"Box: "+L.join("; ")+".":"Per ora non serve rientrare."}
 if(/spingo|spingere|attacc|risparm|push/.test(q)){const L=[];if(c.m!=null&&c.m<0)L.push("risparmia carburante, ti mancano "+Math.abs(c.m).toFixed(1)+" giri");else if(c.m!=null&&c.m>=2)L.push("hai carburante in più, puoi spingere");
  if(F&&u.distacco_davanti_ms!=null&&u.distacco_davanti_ms<2500)L.push("quello davanti è a "+ms(u.distacco_davanti_ms)+": spingi per prenderlo");
  if(F&&u.distacco_dietro_ms!=null&&u.distacco_dietro_ms<1500)L.push("quello dietro è a "+ms(u.distacco_dietro_ms)+": non rilassarti");
  if(F&&u.usura_gomme&&media(u.usura_gomme)>=60)L.push("gomme consumate, gestiscile");
  return L.length?L.join(". ")+".":"Ritmo da mantenere: nessuna ragione per cambiare."}
 if(/ers|batteria/.test(q))return u.ers_pct!=null?"Batteria ERS al "+u.ers_pct+" per cento.":"Non ho il dato ERS.";
 return null}
async function chiediIng(q){q=(q||"").trim();if(!q)return;$("ingDom").value=q;const l=rispostaLocale(q);
 if(l){$("ingRis").textContent="";parla(null,l,0,true);disegnaBox();return}
 $("ingRis").textContent="L'ingegnere sta guardando i dati...";
 try{const d=Object.assign({},ST,{blocchi:ING.blocchi});delete d.funzioni;const j=await api("/api/ingegnere",{domanda:q,dati:d});
  if(j.ok){$("ingRis").textContent="";parla(null,j.risposta,0,true);disegnaBox()}else $("ingRis").textContent="Non riesco: "+j.errore}catch(e){$("ingRis").textContent="Il programma non risponde."}}
$("ingChiedi").onclick=()=>chiediIng($("ingDom").value);
$("ingChips").onclick=e=>{const b=e.target.closest("button[data-q]");if(b)chiediIng(b.dataset.q)};
$("spotOn").checked=SPOT.on;$("spotInv").checked=SPOT.inv;
$("spotOn").onchange=e=>{SPOT.on=e.target.checked;try{localStorage.setItem("simapex_spotter",SPOT.on?"1":"0")}catch(x){}};
$("spotInv").onchange=e=>{SPOT.inv=e.target.checked;try{localStorage.setItem("simapex_spotter_inv",SPOT.inv?"1":"0")}catch(x){}};
(function(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition,b=$("ingMic");if(!SR){b.hidden=true;return}let rec=null,on=false;
 b.onclick=async()=>{if(on){try{rec.stop()}catch(e){}return}
  const er=await micControllo();if(er){$("ingRis").textContent=er;return}
  try{rec=new SR();rec.lang="it-IT";rec.interimResults=false;rec.onresult=ev=>{const t=ev.results[0][0].transcript;$("ingDom").value=t;chiediIng(t)};
   rec.onerror=ev=>{$("ingRis").textContent="Il microfono non parte (codice: "+ev.error+"). Per ora scrivi la domanda o usa i tasti."};rec.onend=()=>{on=false;b.textContent="🎤"};rec.start();on=true;b.textContent="⏹"}
  catch(x){$("ingRis").textContent="Microfono non disponibile: "+x.message}};
 window.micAvvia=()=>{if(!on)b.click()};window.micFerma=()=>{if(on)b.click()}})();
$("ingDom").onkeydown=e=>{if(e.key==="Enter")chiediIng($("ingDom").value)};
setInterval(()=>{try{ingegnere();if(schermo==="pista")disegnaBox();else BOXL=strategia()}catch(e){}},1000);
setInterval(()=>{try{svuotaCoda()}catch(e){}},300);
if(window.speechSynthesis)try{speechSynthesis.getVoices()}catch(e){}



/* ---------- SPOTTER (ACC): macchine vicine ---------- */
function spotter(){const u=ST;if(F1G()||!SPOT.on||!ING.voce||!u.collegato||u.stato_codice!==2||u.in_box){SPOT.prev="";return}
 let dx=false,sx=false;(u.vicini||[]).forEach(c=>{if(Math.abs(c.lon)<=5.5&&Math.abs(c.lat)>=1.2&&Math.abs(c.lat)<=4.5){const dest=SPOT.inv?c.lat<0:c.lat>0;if(dest)dx=true;else sx=true}});
 const k=(dx?"D":"")+(sx?"S":"");
 if(k!==SPOT.prev){if(dx&&sx)parla("spot",k!==SPOT.prev?"Macchine da entrambi i lati.":"",1200,true);else if(dx)parla("spot","Attenzione, macchina a destra.",1200,true);else if(sx)parla("spot","Attenzione, macchina a sinistra.",1200,true);
  else if(SPOT.prev)parla("spotl","Libero.",1200,true);SPOT.prev=k}}


/* ---------- RADIO: tasto sul volante per parlare ---------- */
let PTTp=false;
function radioPtt(){try{tastiVolante()}catch(e){}const on=!!ST.ptt;if(on&&!PTTp){PTTp=true;try{speechSynthesis.cancel()}catch(e){}bip(900,70);if(window.micAvvia)window.micAvvia()}
 else if(!on&&PTTp){PTTp=false;if(window.micFerma)window.micFerma();bip(650,70)}
 if(ST.ptt_tasto&&!$("pttN").value&&document.activeElement!==$("pttN"))$("pttN").value=ST.ptt_tasto;const el=$("pttSt");if(el&&schermo==="pista"){el.textContent=(ST.ptt_tasto?"Tasto radio: "+ST.ptt_tasto+". ":"Tasto radio non impostato. ")+((ST.ptt_visti||[]).length?"Pulsanti premuti ora: "+ST.ptt_visti.join(", ")+".":"")}}
const TASTI_AZ={avanti:"Schermata successiva",indietro:"Schermata precedente",ripeti:"Ripeti l'ultimo messaggio dell'ingegnere",voce:"Voce accesa/spenta"};let TC=null,TCnt=0;
function tastiVolante(){const T=ST.tasti||{},C=ST.tasti_conta||{};
 if(TC&&ST.gioco==="F1 25"){for(const a in TASTI_AZ){if((C[a]||0)>(TC[a]||0)){azioneVolante(a)}}}TC=Object.assign({},C);
 const el=$("tastiAz");if(!el||schermo!=="pista")return;const k=JSON.stringify([T,ST.tasti_assegna]);if(el.dataset.k===k)return;el.dataset.k=k;
 el.innerHTML=Object.keys(TASTI_AZ).map(a=>`<div class="row"><span style="flex:1">${TASTI_AZ[a]}: <b>${ST.tasti_assegna===a?"premi il tasto sul volante…":(T[a]?"tasto "+T[a]:"non assegnato")}</b></span><button data-az="${a}">Assegna</button>${T[a]?`<button data-azt="${a}">Togli</button>`:""}</div>`).join("")}
function azioneVolante(a){bip(1100,40);
 if(a==="avanti"||a==="indietro"){const B=[...document.querySelectorAll("#nav button")].filter(b=>b.offsetParent!==null),i=B.findIndex(b=>b.dataset.s===schermo),n=B[(i+(a==="avanti"?1:B.length-1))%B.length];if(n)n.click()}
 else if(a==="ripeti"){const m=ING.msgs[0];if(m){const v=ING.voce;ING.voce=true;try{speechSynthesis.cancel()}catch(e){}emetti(m.testo.replace(/^\s+/,""),true);ING.voce=v}}
 else if(a==="voce"){ING.voce=!ING.voce;$("ingVoce").checked=ING.voce;try{localStorage.setItem("simapex_voce",ING.voce?"1":"0")}catch(x){}bip(ING.voce?1200:600,80)}}
$("tastiAz").onclick=async e=>{const b=e.target.closest("button");if(!b)return;try{if(b.dataset.az)await api("/api/tasti",{azione:b.dataset.az});else if(b.dataset.azt)await api("/api/tasti",{azione:b.dataset.azt,togli:1})}catch(x){}};
$("pttSalva").onclick=async()=>{try{await api("/api/ptt",{tasto:+$("pttN").value||0});$("pttSt").textContent="Salvato."}catch(e){}};
$("ingFreq").value=ING.freq;$("ingFreq").onchange=e=>{ING.freq=e.target.value;try{localStorage.setItem("simapex_freq",ING.freq)}catch(x){}};

async function f1Chiedi(modo){if(!ST.setup_f1){$("assMsg").textContent="Non vedo ancora il tuo setup: apri F1 25 ed entra in pista (o ai box).";return}
 $("assMsg").textContent="La squadra sta guardando il tuo setup (anche un minuto per quello base)...";$("assRis").innerHTML="";let j;
 try{j=await api("/api/assistente/f1",{sensazioni:$("assSens").value,modo})}catch(e){$("assMsg").textContent="Il programma non risponde.";return}
 if(!j.ok){$("assMsg").textContent="Non riuscito: "+j.errore;return}
 $("assMsg").textContent="";F1P=j;if(j.modifiche&&j.modifiche.length)$("assSens").value="";disegnaF1();giroQuaderno()}
let F1P=null;
function disegnaF1(){const j=F1P;if(!j)return;const S=ST.setup_f1||{};
 let h=`<div class="card"><b>${esc(j.problema||"Proposta")}</b><p class="mu">${esc(j.spiegazione||"")}</p>`;
 if(j.modifiche.length){h+="<p><b>Cambia questi valori nel gioco (Setup della macchina):</b></p><table><tr><th>Parametro</th><th>Ora</th><th></th><th>Metti</th><th>Perché</th></tr>"+j.modifiche.map(m=>{const att=S[m.parametro],fatto=att!=null&&Math.abs(att-m.a)<=0.051;return `<tr><td>${esc(m.parametro)}</td><td>${m.da}</td><td>→</td><td><b>${m.a}</b> ${fatto?'<span class="mig">✓ fatto</span>':""}</td><td>${esc(m.motivo)}</td></tr>`}).join("")+"</table>";
  h+=`<p class="mu">${esc(j.cosa_aspettarsi||"")}</p><p class="mu">Quando i valori nel gioco coincidono il programma lo vede da solo. Dopo almeno 4 giri puliti dice se è andato meglio, uguale o peggio.</p>`}
 else h+=`<p>Nessuna modifica proposta.</p><p class="mu">${esc(j.cosa_aspettarsi||"")}</p>`;
 if((j.suggerimenti_pilota||[]).length)h+="<p><b>Da decidere tu (ABS, controllo trazione, mappa motore):</b></p><ul>"+j.suggerimenti_pilota.map(x=>"<li>"+esc(x)+"</li>").join("")+"</ul>";
 $("assRis").innerHTML=h+"</div>"}
$("f1Base").onclick=()=>f1Chiedi("base");$("f1Vai").onclick=()=>f1Chiedi("migliora");
setInterval(()=>{try{if(F1P&&schermo==="setup")disegnaF1()}catch(e){}},2000);
/* ---------- PIANO PER LA SESSIONE (Box) ---------- */
let PN={auto:true};
function datiAuto(){const u=ST;if(!u.collegato)return null;const tipo=u.sessione===2?2:u.sessione===0?0:u.sessione>=1?1:2;
 let giri=u.giri_totali||0;if(!giri&&u.tempo_rimasto_s&&u.miglior_giro_ms>0&&u.miglior_giro_ms<36000000)giri=Math.ceil(u.tempo_rimasto_s/(u.miglior_giro_ms/1000));
 if(!giri)giri=tipo===1?4:tipo===0?8:10;return{tipo,giri}}
function sincPiano(){if(!PN.auto)return;const a=datiAuto();if(!a)return;if(document.activeElement&&/^pn/.test(document.activeElement.id||""))return;
 $("pnTipo").value=String(a.tipo);$("pnGiri").value=String(a.giri);$("pnNota").textContent="Dati presi dal gioco: "+({0:"prove libere",1:"qualifica",2:"gara"}[a.tipo])+", "+a.giri+" giri"+(ST.giri_totali||ST.tempo_rimasto_s?"":" (stimati: la sessione non li dice)")+". Se vuoi cambiare, modifica i campi."; disegnaPiano(pianoLocale())}
function pianoLocale(){const tipo=+$("pnTipo").value,giri=Math.max(1,+$("pnGiri").value||1),F=F1G(),U=F?"kg":"L",L=[];
 const inp=parseFloat($("pnCons").value),cons=inp>0?inp:(ST.consumo_giro||null),tg=ST.temp_asfalto;
 const nome={0:"Prove libere",1:"Qualifica",2:"Gara"}[tipo];
 L.push({t:"Sessione",v:nome+", "+giri+" giri"+(ST.pista?" a "+bello(ST.pista):"")+(ST.auto?" con "+bello(ST.auto):"")+"."});
 // carburante
 if(cons){const marg=tipo===1?0.7:1.0,carico=(giri+marg)*cons;
  L.push({t:"Carburante",v:"Carica circa "+carico.toFixed(F?1:0)+" "+U+" ("+giri+" giri × "+cons.toFixed(2)+" "+U+" + margine di sicurezza). "+(tipo===1?"In qualifica meno benzina vuol dire più velocità: non caricare oltre il necessario. ":tipo===2?"In gara aggiungi qualcosa se pensi di attaccare molto. ":"")+"Controlla che entri nel serbatoio."})}
 else L.push({t:"Carburante",v:"Non conosco ancora il consumo di questa auto su questa pista. Fai 3 giri puliti (o scrivilo tu qui sopra) e te lo calcolo; per ora parti con più carburante del necessario."});
 // gomme
 if(F){const hot=tg!=null&&tg>=38;let g;
  if(tipo===1)g="Morbida, nuova. Una o due uscite brevi.";
  else if(tipo===0)g="Gomme usate della mescola che userai in gara, per non sprecare quelle nuove.";
  else if(giri<=12)g=(hot?"Media":"Morbida")+" nuova: la gara è corta, una sola sosta non serve.";
  else if(giri<=30)g=(hot?"Dura":"Media")+" nuova, poi "+(hot?"media":"dura")+" alla sosta (circa al giro "+Math.round(giri*0.45)+").";
  else g="Partenza con "+(hot?"dura":"media")+", sosta intorno al giro "+Math.round(giri*0.35)+" e ripartenza con "+(hot?"dura":"media")+"; valuta una seconda sosta.";
  L.push({t:"Gomme",v:g+(tg!=null?" Asfalto a "+Math.round(tg)+" °C"+(hot?": caldo, meglio una mescola più dura.":"."):"")+" (Consiglio di massima: controlla le mescole permesse nel gioco.)"})}
 else L.push({t:"Gomme",v:(tipo===1?"Gomme nuove da asciutto: scaldale con un giro di lancio, poi giro buono.":tipo===0?"Gomme usate se le hai (risparmi quelle nuove) e pressioni di partenza da setup; dopo 3 giri correggile con «Correggi le pressioni».":"Gomme nuove con le pressioni a freddo del setup; a caldo devono stare tra 26,4 e 27,0 psi.")+(giri>25?" Gara lunga: pianifica una sosta con cambio gomme e carburante.":"")});
 // mappa motore
 const mc=MAPPE&&MAPPE.mappa_giri_costanti,mS=MAPPE&&MAPPE.mappa_spinta;
 L.push({t:"Mappa motore",v:(tipo===1?(mS?"Mappa "+mS+" (spinta)":"quella di spinta"):(mc?"Mappa "+mc+" (passo costante)":"quella di passo costante"))+(tipo===2&&mS?"; "+mS+" solo per gli attacchi":"")+(MAPPE?"":" (apri la scheda Percorso per le note sulla mappa di questa auto)")+". La cambi tu, io ti ricordo quando."});
 // come guidare
 L.push({t:"Piano di guida",v:tipo===0?"Primi 2 giri per scaldare, poi almeno 5 giri puliti allo stesso ritmo: così misuro consumo e passo. Poi qualche giro al limite per provare i blocchi.":tipo===1?"Giro di lancio, giro buono, giro di rientro. Se le gomme sono ancora in temperatura puoi fare un secondo giro buono.":"Giri iniziali puliti e senza rischi, poi ritmo costante. Ti dico io quando spingere e quando risparmiare."});
 return L}
function disegnaPiano(L,extra){$("pnRis").innerHTML=L.map(x=>`<div><b>${esc(x.t)}:</b> ${esc(x.v)}</div>`).join("")+(extra?`<div style="margin-top:.5em"><b>La squadra dice:</b> ${esc(extra)}</div>`:"")}
$("pnCalcola").onclick=()=>disegnaPiano(pianoLocale());
["pnTipo","pnGiri","pnCons"].forEach(i=>$(i).addEventListener("change",()=>{PN.auto=false;$("pnNota").textContent="Dati modificati da te.";$("pnAuto").hidden=false}));
$("pnAuto").onclick=()=>{PN.auto=true;$("pnAuto").hidden=true;sincPiano()};
setInterval(()=>{try{if(schermo==="setup")sincPiano()}catch(e){}},3000);
$("pnClaude").onclick=async()=>{const L=pianoLocale();disegnaPiano(L);$("pnRis").insertAdjacentHTML("beforeend",'<div class="mu" id="pnAtt">La squadra sta ragionando...</div>');
 try{const d=Object.assign({},ST);delete d.funzioni;const dom="Sono ai box e devo fare: "+L[0].v+" Questo è il piano base calcolato dal programma:\n"+L.slice(1).map(x=>x.t+": "+x.v).join("\n")+"\nDammi il piano finale in al massimo 6 righe brevi, una per voce: carburante, gomme (nuove o usate, mescola), mappa motore, quando spingere e quando risparmiare. Correggi il piano base se serve.";
  const j=await api("/api/ingegnere",{domanda:dom,dati:d,piano:true});const a=$("pnAtt");if(a)a.remove();
  if(j.ok)disegnaPiano(L,j.risposta);else $("pnRis").insertAdjacentHTML("beforeend",'<div class="st ko">Non riesco a chiedere alla squadra: '+esc(j.errore)+"</div>")}catch(e){const a=$("pnAtt");if(a)a.remove()}};

/* ---------- invio a Claude ---------- */
function istantanea(){const u=ST;return {collegato:u.collegato,auto:u.auto,pista:u.pista,velocita:u.velocita,marcia:u.marcia,giri_motore:u.giri_motore,carburante:u.carburante,pressioni:u.pressioni,temp_gomme:u.temp_gomme,ultimo_giro:u.ultimo_giro,miglior_giro:u.miglior_giro,delta_ms:u.delta_ms}}
function raccogli(){return {ora:new Date().toISOString(),versione:$("ver").textContent,modo:MODO,auto:statoAuto(),commento_generale:(FUN.generale||{}).n||"",prove:TUTTE().map(p=>{const x=FUN[p.id]||{};return {id:p.id,titolo:p.t,stato:x.s==="ok"?"funziona":x.s==="ko"?"non funziona":"non provata",nota:x.n||"",dati_al_momento:null}})}}
let tAuto=null;function autoInvia(){if(!ST.invio_configurato)return;clearTimeout(tAuto);tAuto=setTimeout(async()=>{try{const p=raccogli();p.automatico=true;p.istantanea=istantanea();const j=await api("/api/invia",p);if($("invioSt"))$("invioSt").textContent=j.ok?"Inviato a Claude da solo alle "+new Date().toLocaleTimeString("it-IT"):"Invio non riuscito: "+j.errore}catch(e){}},4000)}
$("invia").onclick=async()=>{if(!ST.invio_configurato){$("copiato").textContent="Prima serve la chiave di accesso (qui sopra).";return}
 $("copiato").textContent="Invio in corso...";try{const j=await api("/api/invia",raccogli());$("copiato").textContent=j.ok?"Inviato a Claude. Scrivi «controlla» nella chat.":"Invio non riuscito: "+j.errore}catch(e){$("copiato").textContent="Invio non riuscito: il programma non risponde."}};
$("azzera").onclick=async()=>{for(const p of TUTTE().concat([{id:"generale"}]))await api("/api/funzione",{id:p.id,s:null,n:""});await giro();disegnaProve()};
$("salvaChiave").onclick=async()=>{const v=$("chiave").value.trim();if(!v){$("chiaveMsg").textContent="Incolla prima la chiave.";return}
 try{const j=await api("/api/chiave",{token:v});if(j.ok){$("chiave").value="";ST.invio_configurato=true;$("chiaveMsg").textContent="Chiave salvata."}else $("chiaveMsg").textContent=j.errore}catch(e){$("chiaveMsg").textContent="Non sono riuscito a salvare."}};
function aggiornaClaudeSt(){$("claudeSt").textContent=ST.claude_configurato?"Chiave salvata su questo PC. Tocca Prova per controllare che funzioni.":"Non collegato. Incolla qui la chiave che inizia con sk-ant- (resta solo su questo PC)."}
$("claudeSalva").onclick=async()=>{const v=$("claudeChiave").value.trim();if(!v){$("claudeMsg").textContent="Incolla prima la chiave.";return}
 try{const j=await api("/api/claude-chiave",{chiave:v});if(j.ok){$("claudeChiave").value="";ST.claude_configurato=true;aggiornaClaudeSt();$("claudeMsg").textContent="Chiave salvata. Ora tocca Prova."}else $("claudeMsg").textContent=j.errore}catch(e){$("claudeMsg").textContent="Non sono riuscito a salvare."}};
$("claudeProva").onclick=async()=>{$("claudeMsg").textContent="Sto chiamando Claude...";try{const j=await api("/api/claude-prova",{});$("claudeMsg").textContent=j.ok?"Funziona! Claude risponde: "+j.risposta:"Non funziona: "+j.errore}catch(e){$("claudeMsg").textContent="Il programma non risponde."}};
async function controllaAgg(){try{const j=await api("/api/aggiornamenti");if(j.disponibile){$("aggv").textContent="v"+j.ultima;$("agg").hidden=false;$("aggb").onclick=()=>window.open(j.scarica,"_blank")}}catch(e){}}
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}

costruisciGomme();applicaModo();try{if(!localStorage.getItem("simapex_aiuto_visto"))vai("aiuto")}catch(e){}
disegnaProve();giro();giroSetup();controllaAgg();
setInterval(giro,200);setInterval(giroMappe,2000);setInterval(()=>{if(schermo==="prove")disegnaProve()},3000);setInterval(giroSetup,5000);setInterval(controllaAgg,3600000);
setInterval(()=>{if(schermo==="sessioni")giroSessioni();if(schermo==="setup")giroQuaderno();aggiornaClaudeSt()},5000);
