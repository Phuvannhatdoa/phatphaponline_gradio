/* Only declared survey JSON inputs are read; all writes are allowlisted in this directory. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ANALYSIS = path.dirname(HERE), SURVEY = path.dirname(ANALYSIS);
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const inputNames = [
  'phase3/source_person.json','phase3/source_relation.json','phase3/source_evidence.json',
  'phase3/phase3-manifest.json','phase2/edge-diff.json','phase2/generation-inventory.json',
  'phase2/person-id-audit.json','phase2/relation-direction-audit.json',
  'phase2/rights-matrix.json','phase2/uncertainty-inventory.json'
];
const inputs = {}, inputManifest = [];
function readInput(relative, filename) {
  const stat = fs.statSync(filename);
  if (stat.size > 8*1024*1024) throw Error('Bounded input exceeded: '+relative);
  const bytes = fs.readFileSync(filename);
  inputManifest.push({path:relative, bytes:bytes.length, sha256:hash(bytes)});
  return JSON.parse(bytes);
}
inputNames.forEach(n => {inputs[n] = readInput(n,path.join(ANALYSIS,n));});
const p1 = readInput('../../manifest.json',path.join(SURVEY,'manifest.json'));
const persons = inputs['phase3/source_person.json'];
const relations = inputs['phase3/source_relation.json'];
const evidence = inputs['phase3/source_evidence.json'];
const p3 = inputs['phase3/phase3-manifest.json'];
const upstreamIntegrity = [];
for (const ref of persons.metadata.input_manifest) {
  const observed = inputManifest.find(i => i.path === ref.path.replace(/^analysis\//,''));
  if (!observed) throw Error('Missing declared Phase2 input: '+ref.path);
  upstreamIntegrity.push({path:ref.path,recorded_sha256:ref.sha256,observed_sha256:observed.sha256,
    status:observed.sha256===ref.sha256?'byte-match':'recorded-hash-mismatch'});
}
for (const name of ['source_person.json','source_relation.json','source_evidence.json']) {
  const recorded = p3.files.find(f => f.path === name);
  const observed = inputManifest.find(i => i.path === 'phase3/'+name);
  if (!recorded || !observed) throw Error('Missing Phase3 manifest entry: '+name);
  upstreamIntegrity.push({path:'analysis/phase3/'+name,recorded_sha256:recorded.sha256,
    observed_sha256:observed.sha256,status:recorded.sha256===observed.sha256?'byte-match':'recorded-hash-mismatch'});
}
const byId = new Map(persons.records.map(p => [p.id,p]));
const selectedIds = ['A004166','A000587','A027200','A027195','A027242'];
for (let i=0; i<selectedIds.length && selectedIds.length<15; i++) {
  for (const r of relations.records) {
    const next = r.source_id === selectedIds[i] ? r.target_id : (r.target_id === selectedIds[i] ? r.source_id : null);
    if (next && byId.has(next) && !selectedIds.includes(next)) selectedIds.push(next);
    if (selectedIds.length === 15) break;
  }
}
for (const p of persons.records) {
  if (selectedIds.length === 15) break;
  if (!selectedIds.includes(p.id)) selectedIds.push(p.id);
}
const chosen = selectedIds.map(id => {
  if (!byId.has(id)) throw Error('Required person absent: '+id);
  return byId.get(id);
});
const rawRelations = relations.records.filter(r => selectedIds.includes(r.source_id) && selectedIds.includes(r.target_id));
const qualifiers = inputs['phase2/uncertainty-inventory.json'].data.all_tei_uncertainty_records;
const lowLinkGroups = qualifiers.filter(q => q.record.tag === 'linkGrp' && q.record.attributes.cert === 'low');
if (lowLinkGroups.length !== 41) throw Error('Expected all 41 low-certainty linkGrp records');
const pair = rawRelations.filter(r => [r.source_id,r.target_id].sort().join('|') === 'A000587|A004166');
if (pair.length !== 3 || pair.filter(r=>r.format==='GEXF').length !== 2) throw Error('Parallel witness selection failed');
const refs = new Set(evidence.records.filter(e=>e.kind==='tei-uncertainty').map(e=>e.id));
for (const row of [...chosen,...rawRelations]) {
  for (const field of ['evidence_refs','rights_refs','tei_case_evidence_refs']) (row[field]||[]).forEach(id=>refs.add(id));
}
/* Follow evidence-to-rights references only, never file paths from input records. */
let changed = true;
while (changed) {
  changed = false;
  evidence.records.filter(e=>refs.has(e.id)).forEach(e => (e.rights_refs||[]).forEach(id => {
    if (!refs.has(id)) {refs.add(id); changed=true;}
  }));
}
const selectedEvidence = evidence.records.filter(e=>refs.has(e.id));
if (selectedEvidence.length !== refs.size) throw Error('Missing evidence reference');
const inputSetHash = hash(JSON.stringify(inputManifest.map(i=>({path:i.path,sha256:i.sha256}))));
const versionId = 'ztj-observed-phase4-snapshot:'+inputSetHash;
const rawSourceHashes = new Map(p3.upstream_source_hashes_as_reported.files.map(f=>[f.path,f]));
const fileNames = [...new Set([
  ...rawRelations.map(r=>r.source_location.file),
  ...selectedEvidence.map(e=>e.source_file).filter(Boolean)
])].sort();
const representationId = name => 'representation:'+name;
const sourcePersons = chosen.map(p => ({
  source_node_key:'ztj:'+p.id, source_external_id:p.id, source_label:p.source_label,
  dataset_version_id:versionId, identity_status:'source_identity_only',
  generation:{system_id:'ztj-source-raw-unconverted',...p.generation},
  evidence_refs:p.evidence_refs, rights_refs:p.rights_refs,
  simulated:false, raw_source_record:p
}));
const mappings = sourcePersons.map(p => ({
  source_node_key:p.source_node_key, source_external_id:p.source_external_id,
  proposed_ptda_person_id:null, identity_status:'proposed',
  vietnamese_label:null, vietnamese_label_source:null, review_status:'unreviewed',
  note:'Chưa có ứng viên PTDA hoặc nhãn Việt được cung cấp; ID nguồn không chứng minh đồng nhất.'
}));
const observations = rawRelations.map(r => ({
  observation_id:r.id, source_node_key:'ztj:'+r.source_id, target_node_key:'ztj:'+r.target_id,
  dataset_version_id:versionId, representation_id:representationId(r.source_location.file),
  work_id:'work:ztj-source-complex', relation_type:'source_graph_association',
  direction:'undirected', direction_evidence:r.direction_basis,
  source_location:r.source_location, source_reference_raw:r.source_reference_raw,
  evidence_refs:[...new Set([...(r.evidence_refs||[]),...(r.tei_case_evidence_refs||[])])],
  warnings:r.warnings, uncertainty:r.uncertainty, rights_refs:r.rights_refs,
  simulated:false, raw_source_record:r
}));
const generationUnknowns = sourcePersons.filter(p=>p.generation.state==='unknown-encoding-disagreement');
if (generationUnknowns.length !== 3 || generationUnknowns.some(p=>p.generation.csv_raw!=='0'||p.generation.workbook_raw!=='?')) throw Error('Unknown generation encodings changed');
const realData = {
  definition_version:'phase4-local-comparison-v1',
  input_integrity:{records:upstreamIntegrity,
    upstream_chain_verified:upstreamIntegrity.every(r=>r.status==='byte-match'),
    policy:'Pin current bytes as a distinct local snapshot. Preserve older recorded hashes and mismatch; do not repair upstream or claim historical chain verification.'},
  scope:{local_only:true, public_release:false, accepted_mapping:false, production_access:false,
    generation_inference:false, rights_clearance:false, source_labels_immutable:true},
  work_identity:[{work_id:'work:ztj-source-complex',source_title:'祖堂集',
    independence_note:relations.review.independence_warning}],
  datasets:[{dataset_id:'dataset:zenodo:10004109',record_id:10004109,
    source_record:p3.source_record,attribution:inputs['phase2/rights-matrix.json'].data.attribution}],
  source_versions:[{dataset_version_id:versionId,dataset_id:'dataset:zenodo:10004109',
    input_set_sha256:inputSetHash,
    snapshot_manifest_sha256:inputManifest.find(i=>i.path==='../../manifest.json').sha256,
    input_artifacts:inputManifest, version_semantics:'Frozen survey snapshot, not a new upstream release'}],
  representations:fileNames.map(file => ({
    representation_id:representationId(file),dataset_version_id:versionId,
    work_id:'work:ztj-source-complex',source_file:file,
    format:path.extname(file).slice(1).toUpperCase(),
    source_hash_as_reported:rawSourceHashes.get(file)||null,
    independence:'same-work-representation-not-independent-source'
  })),
  source_identity:sourcePersons.map(p=>({source_node_key:p.source_node_key,
    source_external_id:p.source_external_id,dataset_version_id:versionId,status:'source_identity_only'})),
  source_person:sourcePersons, mapping_candidates:mappings,
  source_relation:observations.map(o=>({
    relation_observation_id:o.observation_id,source_node_key:o.source_node_key,
    target_node_key:o.target_node_key,relation_type:o.relation_type,direction:o.direction,
    observation_ref:o.observation_id,accepted:false
  })),
  source_observation:observations, source_evidence:selectedEvidence,
  uncertainty:{linkgrp_low_records:lowLinkGroups,all_uncertainty_records:qualifiers,
    scope:'Full Phase2 inventory; may reference people outside the 15-person sample.',
    absent_qualifier_is_certainty:false},
  generation_unknowns:generationUnknowns.map(p=>({source_node_key:p.source_node_key,generation:p.generation})),
  rights:inputs['phase2/rights-matrix.json'].data,
  warnings:relations.review.warnings,
  selection:{rule:'Required pair plus three 0/? cases, then deterministic adjacent source nodes; no identity or lineage inference.',
    selected_ids:selectedIds,source_person_total:persons.records.length}
};
function scenario(id, title, rawEdges, generations={}) {
  const personKeys = [...new Set(rawEdges.flatMap(e=>[e[0],e[1]]))];
  const ps = personKeys.map(k=>({
    source_node_key:'simulated:'+id+':'+k,source_external_id:'SIMULATED-'+k,
    source_label:'SIMULATED PERSON '+k,simulated:true,
    fixture_equivalence_key:'simulated-person:'+k,
    generation:generations[k]||{system_id:'simulated-system',raw:null}
  }));
  return {id,title,simulated:true,history_claim:false,
    source_person:ps,
    mapping_candidates:ps.map(p=>({source_node_key:p.source_node_key,source_external_id:p.source_external_id,
      proposed_ptda_person_id:'simulated:PTDA-'+p.source_external_id,identity_status:'proposed',
      vietnamese_label:'Nhân vật giả lập '+p.source_external_id.replace('SIMULATED-',''),
      vietnamese_label_source:'simulated UI fixture only',review_status:'unreviewed'})),
    observations:rawEdges.map((e,i)=>({
      observation_id:'simulated:'+id+':'+i,source_node_key:'simulated:'+id+':'+e[0],
      target_node_key:'simulated:'+id+':'+e[1],relation_type:e[2],direction:e[3],
      direction_evidence:e[3]==='directed'?'simulated explicit direction fixture':null,
      work_id:'simulated-work:'+e[4],representation_id:'simulated-representation:'+e[4],
      evidence_refs:['simulated-evidence:'+id+':'+i],simulated:true
    }))};
}
const fixtures = {definition_version:'phase4-simulated-fixtures-v1',simulated:true,
  availability:{DILA:'No independent DILA relation dataset supplied to Phase4.',
    Marcus:'No independent Marcus relation dataset supplied; the archiving attribution is not another source.'},
  warning:'SIMULATED — fictional people and works; no historical or authority claims.',
  cases:[
    scenario('agreement','Giả lập: cùng quan hệ, hai tác phẩm',[['A','B','dharma_transmission','directed','one'],['A','B','dharma_transmission','directed','two']]),
    scenario('different-path','Giả lập: đường nối khác',[['A','B','dharma_transmission','directed','one'],['B','C','dharma_transmission','directed','one'],['A','D','dharma_transmission','directed','two'],['D','C','dharma_transmission','directed','two']]),
    scenario('different-type','Giả lập: loại quan hệ khác',[['A','B','dharma_transmission','directed','one'],['A','B','ordination','directed','two']]),
    scenario('undirected','Giả lập: vô hướng không thành có hướng',[['A','B','association','undirected','one'],['A','B','association','directed','two']]),
    scenario('generation-system','Giả lập: hai hệ số đời, một nhân vật',[['A','B','association','undirected','one'],['A','B','association','undirected','two']],{
      A:{system_id:'simulated-system-one',raw:'1',other_annotations:[{system_id:'simulated-system-two',raw:'71'}]}
    })
  ]};
const outputs = {
  'datasets.json':realData.datasets,'source_versions.json':realData.source_versions,
  'representations.json':realData.representations,'source_identity.json':realData.source_identity,
  'source_person.json':realData.source_person,'mapping_candidates.json':realData.mapping_candidates,
  'source_relation.json':realData.source_relation,'source_observation.json':realData.source_observation,
  'source_evidence.json':realData.source_evidence,'uncertainty-inventory.json':realData.uncertainty,
  'generation-unknowns.json':realData.generation_unknowns,'rights.json':realData.rights,
  'fixtures.json':fixtures,
  'preview-data.js':'globalThis.PHASE4_DATA = '+JSON.stringify({data:realData,fixtures}).replace(/</g,'\\u003c')+';\n'
};
const encoded = Object.fromEntries(Object.entries(outputs).map(([name,value])=>[name,
  typeof value==='string'?value:JSON.stringify(value,null,2)+'\n']));
const args = process.argv.slice(2);
if (args.length!==1 || !['--write','--verify'].includes(args[0])) throw Error('Use --write (Phase4 only) or --verify (no writes)');
const manifest = {
  definition_version:'phase4-local-preview-manifest-v1',scope:realData.scope,
  input_integrity:realData.input_integrity,
  source_inputs:inputManifest,counts:{selected_persons:sourcePersons.length,observations:observations.length,
    linkgrp_cert_low:lowLinkGroups.length,all_uncertainty_records:qualifiers.length,
    unknown_generations:generationUnknowns.length,rights_conflicts:realData.rights.conflict_count,
    special_pair_observations:pair.length,special_pair_gexf_witnesses:2},
  output_files:Object.entries(encoded).map(([name,content])=>({path:name,bytes:Buffer.byteLength(content),sha256:hash(content)})),
  exclusions:'Manifest excludes itself and UI/test/docs, which are listed in README. No circular hash or assertion of production state.',
  input_policy:'Only the eleven declared JSON inputs read; no production/DB/TTL/legacy paths opened.'
};
encoded['phase4-manifest.json']=JSON.stringify(manifest,null,2)+'\n';
const allowed = new Set(Object.keys(encoded));
for (const [name,content] of Object.entries(encoded)) {
  const destination=path.resolve(HERE,name);
  if (!allowed.has(name)||path.dirname(destination)!==HERE) throw Error('Write escaped Phase4');
  if (args[0]==='--write') fs.writeFileSync(destination,content,'utf8');
  else if (!fs.existsSync(destination)||fs.readFileSync(destination,'utf8')!==content) throw Error('Derived output mismatch: '+name);
}
for (const ref of inputManifest) {
  const original=ref.path==='../../manifest.json'?path.join(SURVEY,'manifest.json'):path.join(ANALYSIS,ref.path);
  if (hash(fs.readFileSync(original))!==ref.sha256) throw Error('Upstream input changed during run: '+ref.path);
}
console.log(JSON.stringify({status:'PASS',mode:args[0],counts:manifest.counts,inputs_unchanged:true,writes_outside_phase4:false}));
