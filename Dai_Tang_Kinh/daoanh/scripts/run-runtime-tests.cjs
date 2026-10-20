// Mỗi runtime run có output riêng: tránh EPERM/race .last-run.json của session khác.
const fs=require('node:fs');
const path=require('node:path');
const cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
const parent=path.join(root,'docs','reports','runtime-tests');
fs.mkdirSync(parent,{recursive:true});
const output=fs.mkdtempSync(path.join(parent,'run-'));
console.log('Runtime artifacts: '+path.relative(root,output));
const cli=path.join(root,'node_modules','@playwright','test','cli.js');
const r=cp.spawnSync(process.execPath,[cli,'test','tests/e2e-runtime.spec.js','--reporter=list','--output='+output],{cwd:root,stdio:'inherit',env:process.env});
if(r.error){console.error(r.error.message);process.exit(1);}
process.exit(r.status===null?1:r.status);
