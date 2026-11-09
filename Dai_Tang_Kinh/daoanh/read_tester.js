#!/usr/bin/env node
// Quick read of tester-agent.mjs first lines
const fs = require('fs');
const content = fs.readFileSync('E:\\Backup 2025\\QuaiTieuTu\\Anan Son\\phatphaponline_gradio\\truyenthua\\visjs-app\\Dai_Tang_Kinh\\daoanh\\scripts\\tester-agent.mjs', 'utf-8');
const lines = content.split('\\n').slice(0, 30);
for (let i = 0; i < lines.length; i++) {
    console.log((i+1) + ': ' + lines[i]);
}
"