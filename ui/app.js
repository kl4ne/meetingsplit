(function(){
'use strict';
const el = (id) => document.getElementById(id);
const screens = ['home','import','settings','process','results'];
const names = {home:'Inicio',import:'Importar audio',settings:'Configuración',process:'Procesamiento',results:'Resultados'};
const enDictionary=window.MeetingSplitLocales.englishBySpanish;
let uiLocale='en', currentPage='home', statusOriginal='', stateLabelOriginal='', currentNotice='';
const staticText=[];
const SKIP_DYNAMIC=new Set(['page-crumb','file-title','file-sub','folder-display','state-label','job-status',
'result-eyebrow','result-heading','result-description','result-path','result-files','provider-hint']);
function translate(text){
  if(uiLocale==='es')return text;
  const direct=enDictionary[text];if(direct)return direct;
  // Native processing emits useful progress from Python. Translate without discarding counts.
  let m;
  if((m=/^Exportando audio (\d+) de (\d+)$/.exec(text)))return `Exporting audio ${m[1]} of ${m[2]}`;
  if((m=/^Transcribiendo audio (\d+) de (\d+)$/.exec(text)))return `Transcribing audio ${m[1]} of ${m[2]}`;
  if(text.startsWith('Error: '))return 'Error: '+translate(text.slice(7));
  if(text.startsWith('CUDA no disponible ('))return text.replace('CUDA no disponible (','CUDA unavailable (').replace('Usando CPU en modo seguro.','Using CPU in safe mode.');
  return text;
}
function translatePreserveWhitespace(text){const s=text.trim();return s&&enDictionary[s]?text.replace(s,translate(s)):text;}
function collectStaticText(){
  const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let node;
  while((node=w.nextNode())){
    const parent=node.parentElement;
    if(!parent || ['SCRIPT','STYLE'].includes(parent.tagName)||parent.closest('#developer-signature')||parent.closest('#ui-language-control'))continue;
    if(parent.closest('[id]') && SKIP_DYNAMIC.has(parent.closest('[id]').id))continue;
    const source=node.nodeValue.trim();
    if(enDictionary[source])staticText.push({node,source,original:node.nodeValue});
  }
}
function setStateLabel(spanish){stateLabelOriginal=spanish;el('state-label').textContent=translate(spanish);}
function updateLocalizedDynamicFields(){
  const initial={
    'file-title':'Seleccionar grabación',
    'folder-display':'Pendiente: elegir carpeta local',
    'state-label':'ESPERANDO GRABACIÓN',
    'job-status':'Importa una grabación para comenzar.',
    'result-eyebrow':'TODAVÍA NO HAY UNA REUNIÓN PROCESADA',
    'result-description':'Cuando termine una reunión, podrás abrir la carpeta elegida y consultar los archivos generados sin salir de MeetingSplit.'
  };
  for(const [id,source] of Object.entries(initial)){
    const node=el(id),current=node.textContent;
    if(current===source||current===enDictionary[source])node.textContent=translate(source);
  }
  // Only reset placeholder text when there is no actual meeting result.
  if(!resultPath){
    const heading=el('result-heading');
    const first=heading.firstChild,last=heading.querySelector('em');
    if(first&&last){first.textContent=translate('Tu información,')+' ';last.textContent=translate('organizada con claridad.');}
  }else{
    el('result-eyebrow').textContent=translate('PROCESAMIENTO COMPLETADO');
    el('result-heading').innerHTML=translate('Reunión lista.')+'<br><em>'+translate('Información organizada.')+'</em>';
    el('result-description').textContent=translate('Abre la carpeta para acceder a tus audios, transcripción y otros resultados disponibles según la configuración.');
  }
}
function saveUILocale(lang){try{localStorage.setItem('meetingsplit-ui-language',lang);}catch(_){} if(bridge && typeof bridge.setUILanguage==='function')bridge.setUILanguage(lang);}
function applyUILocale(lang,persist=true){
  uiLocale=lang==='es'?'es':'en';
  document.documentElement.lang=uiLocale;
  document.title=uiLocale==='en'?'MeetingSplit · Private Meeting Studio':'MeetingSplit · Estudio privado de reuniones';
  staticText.forEach(({node,original,source})=>{
    // Never overwrite a user-supplied path, meeting filename or changed result.
    if(node.isConnected)node.nodeValue=original.replace(source,translate(source));
  });
  document.querySelectorAll('.ui-lang-btn').forEach(b=>{
    const active=b.dataset.locale===uiLocale;
    b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));
  });
  el('language-label').textContent=uiLocale==='en'?'LANGUAGE':'IDIOMA';
  const support=el('support-development');
  if(support){
    support.title=uiLocale==='en'?'Open secure PayPal contribution page':'Abrir página segura de aportaciones en PayPal';
    support.setAttribute('aria-label',uiLocale==='en'?'Support MeetingSplit development':'Apoyar el desarrollo de MeetingSplit');
  }
  el('ui-language-control').setAttribute('aria-label',uiLocale==='en'?'Interface language':'Idioma de la aplicación');
  const sidebar=document.querySelector('.sidebar');
  sidebar.setAttribute('aria-label',uiLocale==='en'?'Main navigation':'Navegación principal');
  el('primary-navigation').setAttribute('aria-label',uiLocale==='en'?'Screens':'Pantallas');
  el('page-crumb').textContent=translate(names[currentPage]);
  el('screen-container').setAttribute('aria-label',translate(names[currentPage]));
  updateLocalizedDynamicFields();
  recommendation(false);
  if(statusOriginal)el('job-status').textContent=translate(statusOriginal);
  if(stateLabelOriginal)el('state-label').textContent=translate(stateLabelOriginal);
  if(resultIndexJSON)renderResults(resultIndexJSON);
  if(persist)saveUILocale(uiLocale);
}
window.meetingSplitSetUILanguage=applyUILocale;
document.querySelectorAll('.ui-lang-btn').forEach(b=>b.addEventListener('click',()=>applyUILocale(b.dataset.locale)));
function savedUILocale(){try{return localStorage.getItem('meetingsplit-ui-language')||'en';}catch(_){return 'en';}}
collectStaticText();
let bridge = null, working = false, chosenFile = '', resultPath = '', resultIndexJSON = '';
const navItems = Array.from(document.querySelectorAll('.nav-item'));

function navigate(page){
  if(!screens.includes(page)) return;
  currentPage=page;
  screens.forEach((key)=>{
    const node = el('view-'+key);
    node.hidden = key!==page;
    node.classList.toggle('active-screen',key===page);
  });
  navItems.forEach((node)=>{
    const selected = node.dataset.go===page;
    node.classList.toggle('active',selected);
    if(selected) node.setAttribute('aria-current','page');
    else node.removeAttribute('aria-current');
  });
  el('page-crumb').textContent=translate(names[page]);
  el('view-'+page).scrollTop=0;
  el('screen-container').setAttribute('aria-label',translate(names[page]));
}
window.meetingSplitNavigate = navigate; // Used only for UI inspection and tests.
document.querySelectorAll('[data-go]').forEach((node)=>node.addEventListener('click',()=>navigate(node.dataset.go)));

const wave=el('wave-svg');
if(wave){
  let bars='';
  for(let i=0;i<84;i++){
    const level=Math.abs(Math.sin(i*1.98)*Math.cos(i*.337))*.83+Math.abs(Math.cos(i*.71))*.13;
    const h=4+level*75;
    bars+=`<rect x="${2+i*3.67}" y="${((105-h)/2).toFixed(1)}" width="2.2" height="${h.toFixed(1)}" rx="1" fill="${i<28?'#b28343':i<58?'#f2d69b':'#bf9655'}" />`;
  }
  wave.innerHTML=bars;
}
function setStatus(message,pct){
  statusOriginal=message;
  el('job-status').textContent=translate(message);
  el('progress-fill').style.width=Math.max(0,Math.min(100,Number(pct)||0))+'%';
}
function recommendation(adjustDuration=true){
  const ai=el('provider').value,plan=el('plan').value;
  const target=ai==='gemini'&&plan==='free'?5:(ai==='gemini'?20:15);
  if(adjustDuration)el('minutes').value=String(target);
  let note;
  if(ai==='gemini'&&plan==='free')note='Perfil conservador: 5 minutos por fragmento. Verifica el límite total de audio de tu plan; también puedes entregar la transcripción de texto.';
  else if(ai==='chatgpt'&&plan==='free')note='ChatGPT Free puede tener restricciones para audios. MeetingSplit produce texto local para utilizarlo como alternativa.';
  else note=`Sugerencia para ${ai==='gemini'?'Gemini':'ChatGPT'} de pago: ${target} min por archivo, contando el solapamiento. Los límites reales pueden cambiar.`;
  currentNotice=note;
  el('provider-hint').lastElementChild.textContent=translate(note);
}
el('provider').addEventListener('change',recommendation);
el('plan').addEventListener('change',recommendation);

// Voluntary support opens the owner-provided PayPal NCP link ONLY on click.
// Preview: standard HTTPS anchor opens the browser tab. Native: Qt bridge
// opens the same URL in the user's system browser, with no SDK in the app.
const supportButton=el('support-development');
if(supportButton) supportButton.addEventListener('click',(event)=>{
  if(bridge && typeof bridge.openPayPalSupport==='function'){
    event.preventDefault();
    bridge.openPayPalSupport();
  }
});
el('choose-file').addEventListener('click',()=>{
  if(bridge) bridge.pickFile();
  else {navigate('process');setStatus('Esta vista previa no puede abrir archivos. La selección funciona al ejecutar la aplicación Windows.',0);}
});
el('choose-output').addEventListener('click',()=>{
  if(bridge) bridge.pickOutput();
  else {navigate('import');el('folder-display').textContent=translate('Se seleccionará desde la aplicación Windows.');}
});
function openFolder(){
  if(bridge&&resultPath) bridge.openResult();
  else {navigate('results');el('result-description').textContent=translate('La carpeta de resultados se abrirá desde MeetingSplit en Windows después de procesar una grabación.');}
}
el('open-result').addEventListener('click',openFolder);
el('results-open-folder').addEventListener('click',openFolder);

function finished(){
  working=false;
  el('start-job').disabled=false;
  el('cancel-job').hidden=true;
  el('cancel-job').disabled=false;
}
el('start-job').addEventListener('click',()=>{
  navigate('process');
  if(working) return;
  if(!bridge){setStatus('Vista previa: instala o ejecuta MeetingSplit para procesar audio.',0);return;}
  if(!chosenFile){navigate('import');el('file-title').textContent=translate('Primero selecciona una grabación');return;}
  const data={};
  for(const id of ['action','provider','plan','minutes','overlap','format','model','report'])data[id]=el(id).value;
  data.input_language=el('input-language').value;
  data.report_language=el('report-language').value;
  data.local_summary=el('local-summary').checked;
  data.zip_output=el('zip-output').checked;
  data.ollama_model='qwen3:4b';
  working=true;
  el('cancel-job').hidden=false;
  el('start-job').disabled=true;
  el('open-result').hidden=true;
  setStateLabel('PROCESANDO EN TU PC');
  setStatus('Preparando los archivos en el disco...',2);
  bridge.startJob(JSON.stringify(data));
});
el('cancel-job').addEventListener('click',()=>{
  if(bridge&&working){bridge.cancelJob();el('cancel-job').disabled=true;setStatus('Solicitando cancelación segura; los resultados parciales se conservarán.',0);}
});
function renderResults(index){
  resultIndexJSON=index;
  const container=el('result-files');
  container.textContent='';
  const allowed=new Set(['TRANSCRIPCION_COMPLETA.txt','TRANSCRIPCION_SUBTITULOS.srt',
    'RESUMEN_Y_MINUTA_LOCAL.md','RESULTADOS_COMPLETOS.zip','INSTRUCCIONES_CHATGPT_GEMINI.txt']);
  let items=[];
  try { items=JSON.parse(index); }catch(_){ return; }
  if(!Array.isArray(items))return;
  for(const item of items){
    if(!item || !allowed.has(item.name) || typeof item.label!=='string')continue;
    const button=document.createElement('button');
    button.type='button';button.className='result-file';button.textContent=translate(item.label)+' ↗';
    button.addEventListener('click',()=>{if(bridge)bridge.openOutputFile(item.name);});
    container.appendChild(button);
  }
  container.hidden=container.children.length===0;
}
function showResult(folder){
  finished();
  resultPath=folder;
  el('open-result').hidden=false;
  setStateLabel('PROCESAMIENTO COMPLETADO');
  setStatus('Resultados listos. Puedes abrir la carpeta local.',100);
  el('result-eyebrow').textContent=translate('PROCESAMIENTO COMPLETADO');
  el('result-heading').innerHTML=translate('Reunión lista.')+'<br><em>'+translate('Información organizada.')+'</em>';
  el('result-description').textContent=translate('Abre la carpeta para acceder a tus audios, transcripción y otros resultados disponibles según la configuración.');
  el('result-path').textContent=folder;
  el('result-path').hidden=false;
  el('results-open-folder').hidden=false;
  if(bridge && typeof bridge.getResultIndex==='function') bridge.getResultIndex(renderResults);
  navigate('results');
}
if(typeof QWebChannel!=='undefined' && typeof qt!=='undefined' && qt.webChannelTransport){
  new QWebChannel(qt.webChannelTransport,function(channel){
    bridge=channel.objects.desktop;
    bridge.fileSelected.connect(function(path){
      chosenFile=path;
      el('file-title').textContent=path.split(/[\\/]/).pop();
      el('file-sub').textContent=path;
      setStateLabel('GRABACIÓN LISTA');
      setStatus('Grabación cargada. Revisa las opciones e inicia el procesamiento.',0);
    });
    bridge.folderSelected.connect(path=>{el('folder-display').textContent=path;});
    bridge.progress.connect((msg,pct)=>{setStatus(msg,pct);});
    bridge.completed.connect((path)=>showResult(path));
    bridge.failed.connect((msg)=>{
      finished();
      setStateLabel('REVISAR PROCESAMIENTO');
      setStatus('Error: '+msg,0);
      navigate('process');
    });
    bridge.cancelled.connect((msg)=>{
      finished();
      setStateLabel('CANCELADO');
      setStatus(msg,0);
      navigate('process');
    });
    bridge.getDefaultOutput(path=>{
      el('folder-display').textContent=path||translate('Pendiente: elegir carpeta local');
      if(!path)bridge.ensureOutput();
    });
    if(typeof bridge.getUILanguage==='function')bridge.getUILanguage(value=>applyUILocale(value||'en',false));
  });
}
recommendation();applyUILocale(savedUILocale(),false);navigate('home');
})();
