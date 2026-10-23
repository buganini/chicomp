import createBsdconv from './bsdconv.mjs';
import {decompress} from 'compress-utils/zstd/decompress';

let engine;
const status = message => postMessage({type:'status', message});
async function fetchOK(url) {
  const response = await fetch(url);
  if(!response.ok) throw new Error(`下載失敗：${response.status} ${new URL(url).pathname}`);
  return response;
}
const ready = (async()=>{
  status('下載轉換資料…');
  const base = new URL('.', import.meta.url);
  const manifest = await (await fetchOK(new URL('codecs.json',base))).json();
  const packed = new Uint8Array(await (await fetchOK(new URL(manifest.archive,base))).arrayBuffer());
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',packed)),b=>b.toString(16).padStart(2,'0')).join('');
  if(hash!==manifest.sha256) throw new Error('轉換資料校驗失敗，請重新整理頁面。');
  status('準備字庫…');
  const [data, module] = await Promise.all([decompress(packed),createBsdconv({
    locateFile:name=>new URL(name,base).href,
  })]);
  if(data.length!==manifest.size) throw new Error('轉換資料長度不符。');
  for(const file of manifest.files) {
    const target=`/usr/local/share/bsdconv/${file.path}`;
    module.FS.mkdirTree(target.slice(0,target.lastIndexOf('/')));
    module.FS.writeFile(target,data.subarray(file.offset,file.offset+file.length));
  }
  engine=module;
  postMessage({type:'ready',version:manifest.sources.properties.version});
})();
ready.catch(error=>postMessage({type:'fatal',message:error.message}));

function convert(chain,input,strict=true) {
  const pointer=engine.ccall('chicomp_convert','number',['string','string','number'],[chain,input,Number(strict)]);
  if(!pointer) throw new Error('找不到完整的轉換結果，請檢查輸入字元或部件順序。');
  try{return engine.UTF8ToString(pointer);}finally{engine._bsdconv_free(pointer);}
}
function info(text) {
  return Array.from(text,character=>{
    const packet=convert('UTF-8:CNS11643:BSDCONV',character,false);
    const match=/^02([0-9A-F]{2})([0-9A-F]{4})$/.exec(packet);
    return {character,unicode:character.codePointAt(0).toString(16).toUpperCase(),
      cns:match ? `${parseInt(match[1],16)}-${match[2]}` : null};
  });
}
self.onmessage=async({data:{id,action,input}})=>{
  try {
    await ready;
    if(typeof input!=='string' || input.includes('\0') || input.length>4096) throw new Error('輸入過長或含有不支援的字元。');
    let result;
    if(action==='decompose') {
      result=input ? convert('UTF-8:ZH-DECOMP:SPLIT:BSDCONV-KEYWORD,BSDCONV',input).split(',').filter(Boolean) : [];
    } else if(action==='compose') {
      if(input && !/^(04(?:[0-9A-F]{2})+)(,04(?:[0-9A-F]{2})+)*$/.test(input)) throw new Error('部件資料不正確。');
      // The validated stream contains only hex packets and comma separators.
      // BSDCONV decodes packets; ANY#DROP consumes the separating commas.
      const text=input ? convert('BSDCONV,ANY#DROP:ZH-COMP:UTF-8',input) : '';
      result={text,info:info(text)};
    } else throw new Error('不支援的操作。');
    postMessage({id,result});
  } catch(error) {postMessage({id,error:error.message});}
};
