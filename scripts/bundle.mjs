import {build} from 'esbuild';
import fs from 'node:fs/promises';
import path from 'node:path';
import {decompress} from 'compress-utils/zstd/decompress';
import assert from 'node:assert/strict';

await build({entryPoints:['src/app.js', 'src/worker.js'], bundle:true, minify:true,
  format:'esm', platform:'browser', target:'es2022', outdir:'dist',
  external:['./bsdconv.mjs'], legalComments:'linked'});
const packageRoot = 'node_modules/compress-utils';
await fs.copyFile(`${packageRoot}/dist/algorithms/zstd/decompress/zstd.wasm`, 'dist/zstd.wasm');
for (const [folder, output] of [[packageRoot, 'COMPRESS-UTILS-LICENSE.txt'], ['node_modules/sortablejs','SORTABLE-LICENSE.txt']]) {
  const names=await fs.readdir(folder);
  const license=names.find(name=>/^licen[sc]e(\.|$)/i.test(name));
  if(!license) throw new Error(`Missing license in ${folder}`);
  await fs.copyFile(path.join(folder,license),`dist/${output}`);
}
// Validate the exact generated package with the browser's decoder and Wasm core.
const manifest=JSON.parse(await fs.readFile('dist/codecs.json','utf8'));
const data=await decompress(await fs.readFile(`dist/${manifest.archive}`));
assert.equal(data.length,manifest.size);
const {default:create}=await import('../dist/bsdconv.mjs');
const module=await create();
for(const file of manifest.files) {
  const target=`/usr/local/share/bsdconv/${file.path}`;
  module.FS.mkdirTree(target.slice(0,target.lastIndexOf('/')));
  module.FS.writeFile(target,data.subarray(file.offset,file.offset+file.length));
}
const convert=(chain,input)=>{
  const p=module.ccall('chicomp_convert','number',['string','string','number'],[chain,input,1]);
  assert.ok(p,`Conversion failed: ${chain}`);
  try{return module.UTF8ToString(p);}finally{module._bsdconv_free(p);}
};
assert.equal(convert('UTF-8:UTF-8','ASCII 測試𠮷'),'ASCII 測試𠮷');
assert.equal(convert('UTF-8:CNS11643:BSDCONV','測試'),'020160410201665C');
const parts=convert('UTF-8:ZH-DECOMP:SPLIT:BSDCONV-KEYWORD,BSDCONV','功夫不好不要艹我').replace(/,+$/,'');
assert.equal(convert('BSDCONV,ANY#DROP:ZH-COMP:UTF-8',parts),'巭孬嫑莪');
console.log('Compressed codec package and Wasm conversions verified.');
