/* Domande a voce all'ingegnere: normalizza il testo riconosciuto (anche detto male o con rumore) e ne capisce l'intento. */
(function(g){
const CORREZIONI=[[/\b(benzine|bensina|benzin|benza|benzina)\b/g,"benzina"],[/\b(carburanti|carbonante|carburante|carburatore)\b/g,"carburante"],
 [/\b(gome|gonne|gomma|gomme|gommo)\b/g,"gomme"],[/\b(pressione|pressioni)\b/g,"pressioni"],[/\b(distaco|distacchi|distacco|stacco)\b/g,"distacco"],
 [/\b(posizioni|posizione|posizzione)\b/g,"posizione"],[/\b(mancano|manca|mancava)\b/g,"mancano"],[/\b(rimasti|rimasto|rimaste|rimanenti|restano|rimangono)\b/g,"rimasti"],
 [/\b(meteo|metereologia|meteorologia)\b/g,"meteo"],[/\b(piove|pioggia|piovendo)\b/g,"pioggia"]];
function normalizza(t){t=String(t||"").toLowerCase();try{t=t.normalize("NFD").replace(/[̀-ͯ]/g,"")}catch(e){}
 t=t.replace(/[^a-z0-9 ]+/g," ").replace(/\s+/g," ").trim();for(const[r,s]of CORREZIONI)t=t.replace(r,s);return t}
const REGOLE=[
 ["ripeti",/\b(ripeti|ripetilo|ripeto|di nuovo|ancora una volta|non ho sentito|non ho capito|cosa hai detto|come hai detto|che hai detto)\b/],
 ["carburante",/\b(carburante|benzina|serbatoio|fuel|litri|carburo)\b/],
 ["giri",/\b(quanti giri|giri (mancano|rimasti|alla fine|che mancano)|mancano|rimasti|quanto manca|quanto (ne )?resta|alla fine)\b/],
 ["gomme",/\b(gomme|pressioni|usura|temperatura gomme|temperature)\b/],
 ["distacco",/\b(distacco|davanti|dietro|gap|vantaggio|chi ho|inseguit|avversar)/],
 ["posizione",/\b(posizione|che posto|in che posto|a che punto sono|in che posizione|che sono)\b/],
 ["meteo",/\b(meteo|pioggia|bagnato|asciutto|umido|nuvol|temperatura (dell )?(aria|asfalto|pista))\b/],
 ["tempo",/\b(ultimo giro|ultimo tempo|miglior giro|giro migliore|tempo sul giro|che tempo ho fatto|quanto ho fatto|il mio tempo)\b/],
 ["ritmo",/\b(ritmo|passo|come sto andando|come va|come sto|vado bene|sono veloce)\b/],
 ["spingere",/\b(spingo|spingere|spingi|attacc|risparmi|devo spingere|devo risparmiare|push|forzo)\b/],
 ["box",/\b(box|rientro|rientrare|pit|sosta|fermata|cambio gomme|quando entro)\b/]];
function intento(t){const n=normalizza(t);for(const[k,r]of REGOLE)if(r.test(n))return k;return null}
function parole(t){const n=normalizza(t);return n?n.split(" ").length:0}
/* Sceglie la migliore tra più alternative del riconoscimento: la prima che contiene una richiesta che conosciamo. */
function scegli(alt){let primo=null;for(const a of(alt||[])){if(!a||!a.t)continue;if(!primo)primo=a;const k=intento(a.t);if(k)return{testo:a.t,conf:a.c||0,k}}
 return primo?{testo:primo.t,conf:primo.c||0,k:null}:null}
const API={normalizza,intento,parole,scegli};
if(typeof module!=="undefined"&&module.exports)module.exports=API;else g.VOCE=API})(typeof window!=="undefined"?window:globalThis);
