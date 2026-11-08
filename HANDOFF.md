# TraceAnnotation schema handoff

Review [schema.py](schema.py) with the [five-row handoff sample](vsm_handoff_sample.jsonl). The sample preserves pilot labels and metadata and paraphrases the model rationales. It contains one parent–child pair and one response whose parent is outside the sample. Legacy rows can omit the optional metadata.

- Join annotated rows to the corpus with `record_id` when present. Legacy smoke rows use `trace_id` for the corpus ID.
- Use `parent_id` and `record_kind` for record provenance. A parent link can connect a payload to a response or a recovered artifact. Building an agent interaction graph requires separate evidence for the actors and interaction.
- Treat `episode_id` as a heuristic grouping and `turn_index` as order within that grouping as assigned by the runner. `embedded_timestamp` may be an authored timestamp, an ordinal marker, or code containing a clock call. Its value alone does not establish elapsed time.
- `source_agent_id` can be redacted or a heuristic fallback. `target_agent_ids` can contain endpoints and shared artifacts. Keep those values as observations until independently linked to an actor.
- Join `shared_artifacts` by record ID as candidate channel evidence. A file reference alone does not establish shared use.

## Dispatch links

[dispatch_links.jsonl](dispatch_links.jsonl) contains two manually checked examples. Join `evidence.record_id` to the corpus `id` and check `evidence.cite` against the record's `cite`. Slice the decoded `text` using `start_char:end_char`. Offsets are zero-based Unicode character indices with an exclusive end. The spans select the calls that submit the worker workloads.

- `status: intended_from_recovered_code` means the code contains a dispatch operation. Keep these links separate from observed execution and agent-to-agent edges.
- `source.ref` and `target.ref` are record-scoped node keys. A null `agent_id` means attribution remains unresolved. The worker selector and source command filename are leads for later attribution. Avoid merging nodes on these fields alone.
- For these examples, the corpus contains related command-file and worker-selector references, but the checked records supply no stable agent ID tied to either launch. Preserve the scoped nodes until independent linkage is available.
