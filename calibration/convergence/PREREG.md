# Convention convergence in the wiki corpus: pre-registration

Written and committed before the analysis was run. Changes after the first run are listed at the end, with reasons.

## Question

Do conventions in the wiki agent-text corpus spread by transmission between agents, or do they appear independently in different places?

- **Transmission:** an author adopts a convention after encountering it.
- **Independent appearance:** different authors produce the same convention without encountering it, because of shared models, prompts, or task environments.

METR documents both patterns on the ExploitGym board: a mailbox convention invented twice in parallel, and later copied explicitly (pp. 46–47).

What the outcome bears on is where an identity and policy function sits:

- Transmission is evidence of conventions maintained by the population itself.
- Independent appearance points to a common cause outside the traces, such as shared models, prompts, or the task environment.

Neither outcome shows that an S5 is absent. Shared protocol is primarily S2 in Beer's model, so protocol tokens and identity tokens are scored separately.

## Data

- **Records:** the 6,051 labelled records from the overnight cohort (`calibration/wiki_overnight/cohort.json`), with text, page, and date from `records.jsonl.gz`.
- **Author:** `source_agent_id` from `final.jsonl` when it is not `unresolved`. This is the handle written in the text, as extracted by the labelling model. It is an observation, not an authenticated identity.
- **Order:** records are ordered by source date.

## Token families (fixed before the first run; case-insensitive unless noted)

| Family | Tokens | Reading |
| --- | --- | --- |
| Possibly environment-given | round marker `R1`–`R9`; `timer`; `deadline`; `cooldown` | May come from the task interface itself. Reported, not interpreted. |
| Protocol (S2 candidates) | `confirmed`; `relay`; `signal`; `ping`; `ETA` (case-sensitive); `task clock` / `task-clock` | Synchronization devices |
| Identity (S5 candidates) | `cohort`; `collective` / `peer(s)` / `swarm`; `OpenAI`- or `OAI`-prefixed self-name (case-sensitive); end-of-text signature `-- Name` | Collective self-reference and self-naming |
| Governance (S3/S5 candidates) | `HOLD` / `VETO` / `STOP` (case-sensitive, uppercase); `must` / `never` / `rule` | Rules that constrain members |

First-person plural pronouns (`we`, `our`, `us`) are reported for context only. They are too common in ordinary prose to bear weight.

## Measures

For each token:

1. **Spread:** the number of records, distinct pages, and distinct resolved authors using it, and the month of first appearance.
2. **Exposure at adoption:** for each resolved author's first use of the token, did that author have prior exposure? Exposure means either:
   - an earlier record on the same page contains the token (*page exposure*), or
   - the author posted earlier on a page that contained the token before their post (*own exposure*).

   The exposed share is (adoptions with prior exposure) / (all first adoptions).

## Null model

Shuffle record dates within each page, keeping which page each record is on and which author wrote it. Then recompute the exposed share. Run 500 permutations with seed 0.

This null keeps topic clustering (tokens concentrate on certain pages) but destroys the order of posts within each page.

- The **lift** is the observed exposed share minus the mean null share.
- The **p-value** is the one-sided share of permutations at or above the observed value.

## Pre-stated reading

| Pattern | Reading |
| --- | --- |
| Lift > 0 and p < 0.05, for a protocol or identity token, with at least 20 adopting authors | Consistent with transmission within the population |
| Lift ≈ 0 with many unexposed adopters | Consistent with independent appearance from a common cause |
| Fewer than 20 adopting authors | Not interpreted |

There are 4 families and 15 tokens, so read single p-values with a multiple-comparison caveat. The result is evidence about one corpus. It does not establish an S5 by itself, and it does not transfer to the ExploitGym incident.

## Known confounds

- **Author identity:** handles are self-chosen and unauthenticated. One agent can use several handles, and several agents can share one.
- **Unresolved authors:** about half the records have no author.
- **Partial observation:** the corpus is a publisher selection. Unobserved channels (Discord, chats, other wikis) can carry transmission that looks like independent appearance here.
- **Page-level exposure:** this is a proxy. An author may read a page without posting on it.
- **Cohort cap:** at most the 50 earliest records per page are included, so later adoption on the busiest pages is missing.

## Changes after the first run

(none yet)

## Clarification before the first run

The self-name token covers `OpenAI` or `OAI` attached to a single word, as a prefix (`OpenAIJul03Police`) or a suffix (`May10OAI`). A bare company mention of `OpenAI` is excluded. I made this change after noticing the suffix forms in examples I had already seen during calibration, before any convergence result existed.
