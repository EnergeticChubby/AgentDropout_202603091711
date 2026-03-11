# Test Record

- phase: phase0_agentdropout_baseline
- test_name: graph_smoke_v3
- utc_timestamp: 20260311T091413Z
- model_name: glm-4.5-flash
- base_url: https://llm.undefined.qzz.io/v1/chat/completions
- api_key: sk-pc8yOBXhAVOXEa38hpH1XBtuPwadnB1rLpNxHMS6grCuMrZh

## Command

```bash
python3 -c import\ AgentDropout.agents\,\ AgentDropout.llm\,\ AgentDropout.prompt\;\ from\ AgentDropout.graph.graph\ import\ Graph\;\ N=5\;\ agent_names=\[\'AnalyzeAgent\'\]\*N\;\ fixed_spatial=\[\[1\ if\ i\!=j\ else\ 0\ for\ j\ in\ range\(N\)\]\ for\ i\ in\ range\(N\)\]\;\ fixed_temporal=\[\[1\ for\ _\ in\ range\(N\)\]\ for\ _\ in\ range\(N\)\]\;\ g=Graph\(domain=\'mmlu\'\,\ llm_name=\'glm-4.5-flash\'\,\ agent_names=agent_names\,\ decision_method=\'FinalRefer\'\,\ fixed_spatial_masks=fixed_spatial\,\ fixed_temporal_masks=fixed_temporal\)\;\ assert\ g.num_nodes==N\;\ g.construct_spatial_connection\(\)\;\ assert\ g.num_edges==N\*\(N-1\)\;\ print\(\'phase0_agentdropout_graph_smoke_ok\'\,\ g.num_nodes\,\ g.num_edges\) 
```

## Result

- exit_code: 1
- record_dir: result/test_records/phase0_agentdropout_baseline/20260311T091413Z_graph_smoke_v3
