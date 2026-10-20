/* Tests only Phase4 artifacts and eleven allowlisted upstream JSON files. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const crypto=require('node:crypto'),{pathToFileURL}=require('node:url');
const model=require('./model.js');
const HERE=__dirname,ANALYSIS=path.dirname(HERE),SURVEY=path.dirname(ANALYSIS);
const read=name=>JSON.parse(fs.readFileSync(path.join(HERE,name),'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const results=[];
async function check(name,fn) {
  try {await fn();results.push({name,status:'PASS'});}
  catch(e){results.push({name,status:'FAIL',error:e.stack||String(e)});}
}
const persons=read('source_person.json'),mappings=read('mapping_candidates.json');
const observations=read('source_observation.json'),fixtures=read('fixtures.json');
const manifest=read('phase4-manifest.json');
const inputPaths=manifest.source_inputs.map(i=>({
  ...i,absolute:i.path==='../../manifest.json'?path.join(SURVEY,'manifest.json'):path.join(ANALYSIS,i.path)
}));
const before=new Map(inputPaths.map(i=>[i.path,hash(fs.readFileSync(i.absolute))]));
async function run() {
  await check('15 source people; source labels/raw records unchanged',()=>{
    assert.equal(persons.length,15);
    const original=JSON.parse(fs.readFileSync(path.join(ANALYSIS,'phase3/source_person.json'),'utf8'));
    persons.forEach(p=>{const source=original.records.find(x=>x.id===p.source_external_id);assert.equal(p.source_label,source.source_label);assert.deepEqual(p.raw_source_record,source);});
  });
  await check('Mapping seven separate fields; proposed/unreviewed; no accepted target',()=>{
    assert.equal(mappings.length,15);
    const fields=['source_node_key','source_external_id','proposed_ptda_person_id','identity_status','vietnamese_label','vietnamese_label_source','review_status'];
    mappings.forEach(m=>{fields.forEach(k=>assert.ok(Object.hasOwn(m,k)));assert.equal(m.identity_status,'proposed');assert.equal(m.review_status,'unreviewed');assert.equal(m.proposed_ptda_person_id,null);});
  });
  await check('Observed snapshot has explicit recorded/observed integrity warning',()=>{
    assert.equal(manifest.input_integrity.upstream_chain_verified,false);
    assert.ok(manifest.input_integrity.records.some(i=>i.status==='recorded-hash-mismatch'));
    manifest.source_inputs.forEach(i=>assert.equal(i.sha256,before.get(i.path)));
    const version=read('source_versions.json')[0];assert.ok(version.input_set_sha256);assert.ok(version.dataset_version_id.includes(version.input_set_sha256));
  });
  await check('Both GEXF witnesses + CSV UUID/locator discrepancy preserved',()=>{
    const pair=observations.filter(o=>[o.source_node_key,o.target_node_key].sort().join('|')==='ztj:A000587|ztj:A004166');
    assert.equal(pair.length,3);assert.equal(pair.filter(o=>o.raw_source_record.format==='GEXF').length,2);
    assert.ok(pair.some(o=>o.source_reference_raw.includes('0300b07')));
    assert.ok(pair.some(o=>o.source_reference_raw.includes('0412a05')));
    assert.ok(pair.find(o=>o.raw_source_record.format==='CSV').warnings.includes('csv-uuid-locator-inconsistency'));
    const edge=model.compare(persons,pair).edges[0];assert.equal(edge.observation_ids.length,3);assert.equal(edge.work_ids.length,1);assert.equal(edge.representation_ids.length,2);
  });
  await check('Actual graph remains undirected and absence is not certainty',()=>{
    observations.forEach(o=>{assert.equal(o.direction,'undirected');assert.equal(o.relation_type,'source_graph_association');assert.equal(o.uncertainty.state,'not-encoded-in-graph');});
    model.compare(persons,observations).edges.forEach(e=>assert.equal(e.direction,'undirected'));
  });
  await check('All 41 low-cert linkGrp + entire 71 uncertainty records preserved',()=>{
    const actual=read('uncertainty-inventory.json');
    const upstream=JSON.parse(fs.readFileSync(path.join(ANALYSIS,'phase2/uncertainty-inventory.json'),'utf8')).data.all_tei_uncertainty_records;
    assert.equal(actual.linkgrp_low_records.length,41);assert.equal(actual.all_uncertainty_records.length,71);
    assert.deepEqual(actual.all_uncertainty_records,upstream);assert.equal(actual.absent_qualifier_is_certainty,false);
  });
  await check('Three 0/? generation cases kept as raw annotations; no conversion',()=>{
    const unknown=read('generation-unknowns.json');assert.equal(unknown.length,3);
    unknown.forEach(p=>{assert.equal(p.generation.csv_raw,'0');assert.equal(p.generation.workbook_raw,'?');assert.equal(p.generation.state,'unknown-encoding-disagreement');});
  });
  await check('Rights matrix and unresolved four-file declarations preserved',()=>{
    const rights=read('rights.json');
    const upstream=JSON.parse(fs.readFileSync(path.join(ANALYSIS,'phase2/rights-matrix.json'),'utf8')).data;
    assert.deepEqual(rights,upstream);assert.equal(rights.conflict_count,4);assert.equal(rights.not_legal_clearance,true);
    assert.equal(manifest.scope.rights_clearance,false);
  });
  const expected={'agreement':{nodes:2,edges:1},'different-path':{nodes:4,edges:4},'different-type':{nodes:2,edges:2},'undirected':{nodes:2,edges:2},'generation-system':{nodes:2,edges:1}};
  for(const scenario of fixtures.cases) await check('SIMULATED matrix: '+scenario.id,()=>{
    assert.equal(scenario.simulated,true);assert.equal(scenario.history_claim,false);
    const result=model.compare(scenario.source_person,scenario.observations);
    assert.equal(result.nodes.length,expected[scenario.id].nodes);assert.equal(result.edges.length,expected[scenario.id].edges);
    scenario.source_person.forEach(p=>assert.ok(p.source_label.startsWith('SIMULATED')));
    scenario.mapping_candidates.forEach(m=>{assert.equal(m.review_status,'unreviewed');assert.ok(m.vietnamese_label_source.includes('simulated'));});
    if(scenario.id==='agreement')assert.equal(result.edges[0].work_ids.length,2);
    if(scenario.id==='different-type')assert.equal(new Set(result.edges.map(e=>e.relation_type)).size,2);
    if(scenario.id==='undirected')assert.deepEqual(new Set(result.edges.map(e=>e.direction)),new Set(['directed','undirected']));
    if(scenario.id==='generation-system'){assert.equal(result.nodes[0].generations[0].raw,'1');assert.equal(result.nodes[0].generations[0].other_annotations[0].raw,'71');}
  });
  await check('Undefined direction never promoted; reverse directed stays separate',()=>{
    const s=fixtures.cases[0],a=s.observations[0],b=s.observations[1];
    assert.equal(model.effectiveDirection({...a,direction_evidence:null}),'undefined');
    const reversed={...b,source_node_key:b.target_node_key,target_node_key:b.source_node_key};
    assert.equal(model.compare(s.source_person,[a,reversed]).edges.length,2);
    assert.equal(model.compare(s.source_person,[a,{...b,direction_evidence:null}]).edges.length,2);
  });
  await check('Same external ID/proposed target does not merge real identities',()=>{
    const ps=[{source_node_key:'source-one:A',source_external_id:'A',simulated:false,fixture_equivalence_key:'same'},
      {source_node_key:'source-two:A',source_external_id:'A',simulated:false,fixture_equivalence_key:'same'}];
    assert.equal(model.compare(ps,[]).nodes.length,2);
  });
  await check('Derived output hashes match manifest; all evidence links resolve',()=>{
    manifest.output_files.forEach(f=>assert.equal(hash(fs.readFileSync(path.join(HERE,f.path))),f.sha256));
    const refs=new Set(read('source_evidence.json').map(e=>e.id));
    observations.forEach(o=>o.evidence_refs.forEach(ref=>assert.ok(refs.has(ref),ref)));
    assert.equal(read('source_identity.json').length,persons.length);
  });
  await check('UI/builder static safety: no fetch/storage/eval/HTML injection/CDN',()=>{
    const js=fs.readFileSync(path.join(HERE,'preview.js'),'utf8');
    assert.ok(!/\b(fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage|innerHTML|eval)\b/.test(js));
    const html=fs.readFileSync(path.join(HERE,'preview.html'),'utf8');
    assert.ok(html.includes("connect-src 'none'"));
    assert.ok(!/<(?:script|link|img)[^>]+(?:src|href)=["']https?:/i.test(html));
  });
  let browser;
  try {
    const {chromium}=require('@playwright/test');
    browser=await chromium.launch({headless:true});
    const context=await browser.newContext({viewport:{width:1280,height:900}});
    const page=await context.newPage(),errors=[],requests=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{requests.push(route.request().url());return route.request().url().startsWith('file:')?route.continue():route.abort();});
    await page.goto(pathToFileURL(path.join(HERE,'preview.html')).href);
    await page.waitForFunction(()=>document.body.dataset.ready==='true',{timeout:10000});
    await check('file:// opens real data, source graph has no directed arrows',async()=>{
      assert.equal(await page.locator('#persons tr').count(),15);
      assert.equal(await page.locator('#graph [data-directed-arrow]').count(),0);
      assert.ok((await page.locator('#guardMessage').innerText()).includes('hash'));
      assert.equal(await page.evaluate(()=>Object.isFrozen(PHASE4_DATA.data.source_person[0])),true);
      await page.screenshot({path:path.join(HERE,'desktop-preview.png'),fullPage:true});
    });
    await check('Three modes + all real witnesses/uncertainties/generation cases visible',async()=>{
      await page.locator('[data-mode=evidence]').click();
      assert.equal(await page.locator('#witnesses [data-witness]').count(),3);
      assert.equal(await page.locator('#unknownGenerations [data-unknown-generation]').count(),3);
      assert.equal(await page.locator('#uncertainties [data-tag=linkGrp][data-cert=low]').count(),41);
      assert.ok((await page.locator('#witnesses').innerText()).includes('0300b07'));
      assert.ok((await page.locator('#witnesses').innerText()).includes('0412a05'));
      await page.locator('#evidenceSelect').selectOption(read('source_evidence.json')[0].id);
      assert.ok((await page.locator('#evidenceDetail').innerText()).includes('source_file'));
    });
    await check('Comparison scenarios label SIMULATED and satisfy graph matrix',async()=>{
      await page.locator('[data-mode=compare]').click();
      for(const f of fixtures.cases) {
        await page.selectOption('#scenario',f.id);
        assert.ok((await page.locator('#simulationWarning').innerText()).includes('SIMULATED'));
        assert.equal(await page.locator('#comparisonSummary').getAttribute('data-nodes'),String(expected[f.id].nodes));
        assert.equal(await page.locator('#comparisonSummary').getAttribute('data-edges'),String(expected[f.id].edges));
      }
      assert.ok((await page.locator('#generationAnnotations').innerText()).includes('71'));
    });
    await check('375px keyboard navigation and bounded page width',async()=>{
      await page.setViewportSize({width:375,height:812});
      await page.locator('[data-mode=source]').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#sourcePanel').isVisible(),true);
      const widths=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
      assert.ok(widths.scroll<=widths.client+1,JSON.stringify(widths));
      await page.locator('#search').fill('A004166');assert.equal(await page.locator('#persons tr').count(),1);
      await page.locator('#search').fill('');
      await page.screenshot({path:path.join(HERE,'mobile-preview.png'),fullPage:true});
    });
    await check('No page errors, API/remote request or browser storage mutation',async()=>{
      assert.deepEqual(errors,[]);
      assert.ok(requests.every(url=>url.startsWith('file:')));
      assert.equal(await page.evaluate(()=>localStorage.length),0);
    });
    await check('Untrusted source labels display as literal text',async()=>{
      const contextX=await browser.newContext();
      await contextX.addInitScript(()=>{
        let payload;
        Object.defineProperty(globalThis,'PHASE4_DATA',{configurable:true,get(){return payload;},set(value){
          value.data.source_person[0].source_label='<img src=x onerror="globalThis.phase4Xss=1">';payload=value;
        }});
      });
      const x=await contextX.newPage();
      await x.goto(pathToFileURL(path.join(HERE,'preview.html')).href);
      await x.waitForFunction(()=>document.body.dataset.ready==='true');
      assert.equal(await x.locator('#persons img,#graph img').count(),0);
      assert.equal(await x.evaluate(()=>globalThis.phase4Xss),undefined);
      assert.ok((await x.locator('#persons').innerText()).includes('<img src=x'));
      await contextX.close();
    });
    await check('Non-local mocked origin is denied without production transport',async()=>{
      const remote=await browser.newContext(),p=await remote.newPage();
      const allowed=new Set(['preview.html','preview.css','preview.js','preview-data.js','model.js']);
      await p.route('**/*',route=>{
        const name=new URL(route.request().url()).pathname.split('/').pop();
        if(!allowed.has(name))return route.abort();
        return route.fulfill({status:200,contentType:name.endsWith('.js')?'application/javascript':name.endsWith('.css')?'text/css':'text/html',body:fs.readFileSync(path.join(HERE,name),'utf8')});
      });
      await p.goto('https://phase4-fixture.invalid/preview.html');
      await p.waitForFunction(()=>document.getElementById('main').hidden===true);
      assert.ok((await p.locator('#guardMessage').innerText()).includes('Chỉ mở tại máy'));
      await remote.close();
    });
    await context.close();
  } catch(e) {results.push({name:'Browser execution',status:'FAIL',error:e.stack||String(e)});}
  finally {if(browser)await browser.close();}
  await check('All eleven Phase1–3 inputs unchanged after tests',()=>{
    inputPaths.forEach(i=>assert.equal(hash(fs.readFileSync(i.absolute)),before.get(i.path),i.path));
  });
  const report={definition_version:'phase4-tests-v1',generated_at_utc:new Date().toISOString(),
    passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,
    results,scope:'Technical preview only; no historical/identity/rights certification.',
    production_access:false,upstream_inputs_unchanged:true,committed:false};
  fs.writeFileSync(path.join(HERE,'test-results.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));if(report.failed)process.exitCode=1;
}
run().catch(e=>{console.error(e);process.exitCode=1;});
