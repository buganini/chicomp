import Sortable from 'sortablejs';

const $ = id=>document.getElementById(id);
const error = message=>{ $('error').textContent=message; $('error').hidden=!message; };
const worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
let components=new Map(), items=[], nextItem=0, nextRequest=0, pending=new Map();
let available=false, busy=false, resultText='', editRevision=0;
let runtimeReady=false, libraryReady=false;
function controls() {
  const locked=!available||busy;
  for(const id of ['input','decompose','compose','example','clear','stroke-filter']) $(id).disabled=locked;
  $('copy').disabled=!resultText;
  for(const node of document.querySelectorAll('.component')) node.disabled=locked;
  sort.option('disabled',locked); trash.option('disabled',locked);
}
function request(action,input) {
  const id=++nextRequest;
  return new Promise((resolve,reject)=>{
    pending.set(id,{resolve,reject}); worker.postMessage({id,action,input});
  });
}
function ready() {
  available=runtimeReady&&libraryReady;
  if(available){$('status').textContent='已就緒 · 所有轉換均在本機完成';$('status').classList.add('ready');}
  controls();
}
function fatal(message) {
  available=false; busy=false; runtimeReady=false;
  $('status').textContent='載入失敗，請重新整理頁面重試';
  error(message);
  for(const task of pending.values()) task.reject(new Error(message));
  pending.clear(); controls();
}
worker.onmessage=({data})=>{
  if(data.type==='status') {$('status').textContent=data.message;return;}
  if(data.type==='ready') {$('data-version').textContent=`資料版本 ${data.version}`;runtimeReady=true;ready();return;}
  if(data.type==='fatal') {fatal(data.message);return;}
  const task=pending.get(data.id);
  if(task){pending.delete(data.id);data.error ? task.reject(new Error(data.error)) : task.resolve(data.result);}
};
worker.onerror=event=>fatal(event.message||'轉換程式無法載入。');

function componentButton(code,selected=false) {
  const entry=components.get(code);
  const button=document.createElement('button');
  button.type='button';button.className='component'+(selected?' selected-item':'');button.dataset.code=code;
  button.title=code;button.setAttribute('aria-label',`部件 ${code}`);
  if(entry?.image){const image=document.createElement('img');image.src=entry.image;image.alt='';image.draggable=false;button.append(image);}
  else {button.textContent=code;button.classList.add('unknown-component');}
  button.disabled=!available||busy;
  return button;
}
function clearResult() {
  resultText='';$('result').textContent='等待組合';$('result').classList.add('empty');
  $('character-info').replaceChildren();$('copy').disabled=true;
}
function changed() {editRevision++;clearResult();error('');}
function renderEditor(focusId) {
  $('editor').replaceChildren(...items.map(item=>{
    const button=componentButton(item.code,true);button.dataset.id=item.id;
    button.addEventListener('dblclick',()=>{if(!busy) add(item.code);});
    button.addEventListener('keydown',event=>{
      if(busy) return;
      const at=items.findIndex(x=>x.id===item.id);
      if(event.key==='Delete'||event.key==='Backspace'){
        event.preventDefault();items.splice(at,1);changed();renderEditor(items[Math.min(at,items.length-1)]?.id);
      } else if(event.key==='ArrowLeft'||event.key==='ArrowRight') {
        event.preventDefault();const to=at+(event.key==='ArrowLeft'?-1:1);
        if(to>=0&&to<items.length){[items[at],items[to]]=[items[to],items[at]];changed();renderEditor(item.id);}
      } else if(event.key==='Enter'){event.preventDefault();add(item.code);}
    });
    return button;
  }));
  if(focusId) $('editor').querySelector(`[data-id="${focusId}"]`)?.focus();
}
function add(code) {
  if(!available||busy) return;
  if(items.length>=256){error('一次最多排列 256 個部件。');return;}
  items.push({id:String(++nextItem),code});changed();renderEditor();
}
function syncOrder() {
  const byId=new Map(items.map(item=>[item.id,item]));
  items=Array.from($('editor').querySelectorAll('.selected-item'),node=>byId.get(node.dataset.id)).filter(Boolean);
  changed();
}
const sort=Sortable.create($('editor'),{group:'components',animation:130,draggable:'.selected-item',
  ghostClass:'sortable-ghost',disabled:true,onEnd:()=>{syncOrder();renderEditor();}});
const trash=Sortable.create($('trash'),{group:'components',sort:false,disabled:true,
  onAdd:event=>{event.item.remove();syncOrder();renderEditor();}});

async function perform(fn) {
  if(!available||busy) return;
  busy=true;error('');controls();
  try{await fn();}catch(e){error(e.message);}finally{busy=false;controls();}
}
$('input-form').addEventListener('submit',event=>{
  event.preventDefault();
  perform(async()=>{
    const codes=await request('decompose',$('input').value);
    if(codes.length>256) throw new Error('拆出的部件超過 256 個，請減少輸入文字。');
    items=codes.map(code=>({id:String(++nextItem),code}));changed();renderEditor();
  });
});
$('example').addEventListener('click',()=>{$('input').value='功夫不好不要艹我';$('input-form').requestSubmit();});
$('clear').addEventListener('click',()=>{items=[];changed();renderEditor();});
$('compose').addEventListener('click',()=>perform(async()=>{
  const revision=editRevision;
  const result=await request('compose',items.map(item=>item.code).join(','));
  if(revision!==editRevision) return;
  resultText=result.text;
  $('result').textContent=result.text||'沒有組合結果';$('result').classList.toggle('empty',!result.text);
  $('character-info').replaceChildren(...result.info.map(info=>{
    const card=document.createElement('div');card.className='character';
    const glyph=document.createElement('strong');glyph.textContent=info.character;
    const label=document.createElement('small');label.textContent=`U+${info.unicode}`;
    if(info.cns){label.append(document.createElement('br'),document.createTextNode(`CNS ${info.cns}`));}
    card.append(glyph,label);return card;
  }));
}));
$('copy').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(resultText);$('copy').textContent='已複製';setTimeout(()=>$('copy').textContent='複製文字',1500);}
  catch{error('無法使用剪貼簿，請選取結果文字複製。');}
});
$('stroke-filter').addEventListener('change',()=>{
  const value=$('stroke-filter').value;
  for(const button of $('components').children) button.hidden=Boolean(value)&&String(components.get(button.dataset.code).strokes)!==value;
});
(async()=>{
  try {
    const response=await fetch(new URL('./components.json',import.meta.url));
    if(!response.ok) throw new Error(`部件清單下載失敗：${response.status}`);
    const list=await response.json();components=new Map(list.map(entry=>[entry.code,entry]));
    const fragment=document.createDocumentFragment();
    for(const entry of list){const button=componentButton(entry.code);button.addEventListener('click',()=>add(entry.code));fragment.append(button);}
    $('components').append(fragment);
    for(const strokes of [...new Set(list.map(entry=>entry.strokes))].sort((a,b)=>a-b)){
      const option=document.createElement('option');option.value=strokes;option.textContent=`${strokes} 畫`;$('stroke-filter').append(option);
    }
    libraryReady=true;ready();
  } catch(e){fatal(e.message);}
})();
clearResult();
