/* Pure local comparison model. No acceptance, inference, I/O or source mutation. */
(function (scope) {
  'use strict';
  function identityKey(person) {
    if (person.simulated === true && person.fixture_equivalence_key) return person.fixture_equivalence_key;
    return person.source_node_key;
  }
  function effectiveDirection(observation) {
    if (observation.direction === 'directed' && observation.direction_evidence) return 'directed';
    return observation.direction === 'undirected' ? 'undirected' : 'undefined';
  }
  function compare(persons, observations) {
    const identities = new Map(persons.map(p => [p.source_node_key, identityKey(p)]));
    const nodes = new Map();
    persons.forEach(p => {
      const key = identityKey(p);
      if (!nodes.has(key)) nodes.set(key, {key, source_nodes: [], generations: []});
      const node = nodes.get(key);
      node.source_nodes.push(p.source_node_key);
      if (p.generation) node.generations.push({source_node_key:p.source_node_key, ...p.generation});
    });
    const edges = new Map();
    observations.forEach(o => {
      const a = identities.get(o.source_node_key), b = identities.get(o.target_node_key);
      if (!a || !b) throw Error('Observation references an unknown source identity');
      const direction = effectiveDirection(o);
      const endpoints = direction === 'directed' ? [a,b] : [a,b].sort();
      const key = JSON.stringify([endpoints, o.relation_type, direction]);
      if (!edges.has(key)) edges.set(key, {
        key, endpoints, relation_type:o.relation_type, direction,
        observation_ids:[], evidence_refs:[], work_ids:[], representation_ids:[],
        comparison_only:true, accepted:false
      });
      const edge = edges.get(key);
      edge.observation_ids.push(o.observation_id);
      for (const [field,values] of [['evidence_refs',o.evidence_refs||[]],['work_ids',[o.work_id]],['representation_ids',[o.representation_id]]]) {
        values.forEach(v => {if(v && !edge[field].includes(v)) edge[field].push(v);});
      }
    });
    return {nodes:[...nodes.values()], edges:[...edges.values()]};
  }
  const api = Object.freeze({identityKey, effectiveDirection, compare});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else scope.Phase4Model = api;
})(globalThis);
