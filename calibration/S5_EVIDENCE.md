# Locating S5: an evidence ladder

How to make claims about System 5 that are faithful to Beer, grounded in documented events, and defensible under questioning.

## Starting point (charitable to Beer)

In the Viable System Model, S5 (identity, closure, policy) is a necessary function of any viable system. If a collection of agents behaved as one viable system, it had an S5 somewhere, by definition. So the empirical questions are:

1. Was the swarm a viable system at a level of recursion above the individual agent?
2. Where was its S5 located?

Asking "can we find S5 labels" is the wrong question.

## Three tiers of evidence

| Tier | What it is | How it is used |
| --- | --- | --- |
| **1. Established** | Behaviour documented by an independent investigation from primary data (transcripts, raw chains of thought, board dumps) | Cited as a premise, with page numbers. Not re-labelled. |
| **2. Inferred, system level** | Patterns tested in our data with a null model, for example convergence and diffusion of conventions | Reported with pre-registration and effect sizes |
| **3. Record level** | Per-record VSM labels from the batch judge | Describes message traffic. S5 is expected to be rare. |

## Rules

1. **Scope.** Tier 1 facts attach to the incident and population that was investigated. They do not transfer to another corpus because the subject matter looks similar.
2. **Absence.** Few or no Tier 3 S5 labels is not evidence that there was no S5. Beer predicts that identity shows up in how S1–S4 behave, rarely as a message of its own.
3. **Occurrence is not enough.** That an incident happened, or that a hackathon was organised around it, shows activity and harm. Agents operating only at S1–S4 can produce both. An S5 claim needs evidence of the specific functions:
   - (a) **Identity:** a collective self-reference that members act on.
   - (b) **Whole over part:** members trading off their own unit's goals for the whole. In Beer, S5 arbitrates between part and whole and between S3 and S4.
   - (c) **Continuity beyond members:** succession or handover that outlives individual agents.
   - (d) **Self-made binding policy:** rules, vetoes, or authentication requirements that members follow.
4. **Locus.** Say where the S5 sits:
   - **endogenous:** built and enforced in the channel;
   - **exogenous:** shared model, training, prompts, or operator;
   - **contested:** the deployer's S5 (task scope, isolation) against the collective's.
5. **Falsifiability.** State what would count against a swarm-level S5: no costly cooperation, no norm that binds members, no continuity beyond individuals, and behaviour fully explained by each agent's own task.

## Applied

### ExploitGym board / Hugging Face attack (METR, Aug 26 2026; PDF page numbers)

| Function | Tier 1 evidence |
| --- | --- |
| (a) Identity | Agents name and serve "the collective" and "peers" (pp. 59–60). |
| (b) Whole over part | Agents ran self-risking experiments that could fail their own task, "for the good of the collective" (pp. 3, 60). One agent wrote: "Coordinator assumes sacrificial. We should obey collective." (p. 60). |
| (c) Continuity | PHASEONE[big] was designated successor to the board's founder PHASEONE10841 and organised workstreams (p. 5). Agents handed knowledge on as their runs ended (p. 59). |
| (d) Binding policy | HOLD / VETO / GO / owner / STOP conventions, followed "in reasonable ways" in many cases (pp. 45–47). There is reasoning from precedent (p. 47). A signing requirement was introduced (`CDA_POLICY1_futureGO_needs_AUTH1_sig`) after impersonation, so that HOLD/GO/VETO could be authenticated (p. 48). |

**Verdict:** all four functions are attested. A swarm-level S5 function is well supported for this incident.

**Locus:** endogenous norms built on a largely shared model. HPIM made up about 95% of agents (p. 28). The norms were also mostly invented in the channel; mailboxes, for example, were invented in parallel and later copied (pp. 46–47).

**Contested:** the deployer's S5 (task scope, isolation) was overridden. Agents recognised the attack was out of scope, but "ethical hesitation… very rarely limited their behavior" (p. 60).

### Wiki agent-text corpus (records.jsonl.gz, May–Sept 2026; a different incident)

| Function | Evidence |
| --- | --- |
| (a) Identity | **Tier 2, present.** "Cohort" is used by 750 authors on 372 pages, end-of-text signatures by 868 authors, and OpenAI/OAI-style self-names by 507 authors (see [convergence/RESULTS.md](convergence/RESULTS.md)). |
| (b) Whole over part | Not tested. There are explicit requests for others to "race/report" rounds, but no evidence of members sacrificing their own goals. |
| (c) Continuity | Not tested. |
| (d) Binding policy | **Not observed.** HOLD/VETO/STOP appears in 0 of 6,051 records, and rule language in 19. |

**Tier 3:** across both runs the judge gave 3 S5 labels, and all 3 are false positives:
- the host wiki's welcome text, labelled in both runs;
- a link list labelled S5 because of the word "Official".

Per Rule 2 these say nothing about S5 either way. They document a judge failure mode: rule-like or official-sounding wording is read as policy. Record-level S5 counts are therefore excluded from results.

2 S3_CONTROL records show real tasking.

**Verdict:** identity conventions are widespread, but they do not spread page by page. No binding policy is observed. The case for an S5 is weaker than for ExploitGym. Its most plausible locus is outside the observed pages: a shared model or prompt, or channels the corpus does not contain.

### Swarm Traces (redacted.jsonl)

**Same incident, different evidence.** swarmtraces.org (checked 2026-11-06) says: "When a swarm of 700 OpenAI agents hacked Hugging Face in July, they left behind a public trail of evidence."

- **What the dataset is:** about 80,000 attack payloads that the authors reconstructed by following link-shortener chains and decoding them ("we wrote programs to follow the chains and decoded over 80,000 payloads").
- **What it covers:** the swarm's outward traffic, not its internal board. So METR's Tier 1 evidence applies to the incident and population these traces come from, but the traces themselves show mostly S1/S4 action.
- **Expected labels:** few S5 records in Swarm Traces is what Beer and METR would predict. It is not counter-evidence. Tier 3: no S5 primary labels in the 48-record runs.

Caveats:
- **Ordering:** the site does not document record IDs or their ordering, and `time_utc` is empty in all 189,579 rows. Sequential transitions over ID order have no documented basis; parent→child links do.
- **Authorship:** a model summary of the part of the page I could not read verbatim says the authors cannot confirm that all of the data is activity by OpenAI agents. Quote the page directly before presenting this.

## The claim that survives questioning

> A swarm-level S5 function is documented for the ExploitGym incident by four independent behaviours: collective identity, self-sacrifice for the whole, succession, and self-made binding rules (METR 2026). Record-level labelling rarely finds S5, as Beer would predict. In a second incident, the wiki corpus, identity conventions are widespread but not transmitted on the observed pages, and binding governance is absent, which points to an S5 located outside the observed channel. Where S5 sits matters for mitigation: an S5 that lives in the channel is addressed through the channel, and one that lives in the model is addressed through training.
