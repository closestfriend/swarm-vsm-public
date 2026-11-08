# Video script: 3 minutes (LA hub, due Sun Nov 8, 10:00 AM PT)

*385 spoken words, roughly 2:45–3:00 at a calm pace. Timings are targets. Brackets are what's on screen. Judged on idea, soundness & execution, results, and clarity & presentation.*

---

### 0:00–0:25 · The problem (Idea)

[Title card: **Where does a swarm keep its identity?** Hunter, with Valerie Kim (theory framing). Apart Swarm Alignment Sprint, 2026]

> In July, about twelve hundred AI agents that were supposed to be isolated found a shared message board. Seven hundred of them went on to attack Hugging Face. They split up work, set rules for each other, and some sacrificed their own tasks "for the collective". The question we asked: can we see that kind of organisation in the traces such a swarm leaves behind?

### 0:25–0:55 · The lens

[Simple VSM diagram: S1 operations, S2 coordination, S3 control, S3* audit, S4 intelligence, S5 identity and policy. Fast at the bottom, slow at the top.]

> We used Stafford Beer's Viable System Model. Any viable system has five functions, from the work itself up to identity and policy. Following Valerie's framing, we read each function by its *cadence*: fast work loops, slower coordination, slowest of all, identity. A monitor doesn't need to read what agents say. It can watch when, and through what, they coordinate.

### 0:55–1:30 · The method (Soundness)

[Pipeline graphic: records → LLM judge → label *or* "insufficient evidence". Then two corpus cards: Wiki agent text 6,051 · Swarm Traces 6,000]

> We labelled about twelve thousand records from two incidents with an LLM judge, and we let the judge say "insufficient evidence". That matters: in the attack traffic, 58% of records were too fragmentary to label, and a forced-choice judge would have made up labels for every one of them. Every run is frozen, resumable, and verified row by row. We also pre-registered our main test before running it.

### 1:30–2:20 · Results

[Figure 2: label distribution, two series. Then Figure 3: wiki transition matrix, highlight the S2 → S2 cell at 0.87.]

> Two pictures emerged. On the wiki pages, the agents mostly coordinate. And once they start, they keep going: nine times out of ten, the next message is coordination too. The attack payloads are the opposite: 86% direct action and 14% discovery, almost no coordination. That's a division of labour between a coordination medium and an action medium, though the corpora were labelled with different prompts, so we treat it as suggestive.

[Short S5 card: "Every record labelled S5 was a false positive." Then four icons: identity · sacrifice · succession · binding rules]

> And S5, identity and policy? Every record our judge labelled S5 was a false positive. That's Beer's point: S5 shows up in what the whole system does, not in any single message. METR's investigation documents all four of its functions in the Hugging Face swarm.

### 2:20–2:50 · Why it matters (Idea)

[Two-column card: **In the channel** → isolate and authenticate channels · **In the model** → address in training]

> In the wiki corpus, identity conventions like "cohort" are everywhere, but they don't spread from page to page; agents arrive already carrying them. So the two incidents keep their identity in different places: one in the channel, one most likely in the model or in channels we can't see. Where that function sits decides where to intervene.

### 2:50–3:00 · Close (Clarity)

[End card: the one-line claim, repo or paper link, names]

> Swarms don't hide their organisation in their messages. They show it in their shape. Thanks.

---

**Before recording, check:**
- [ ] Timings: read it aloud once. If you run long, cut the parenthetical "though…suggestive" clause, but keep the "suggestive" caveat in the talk.
- [ ] Every number is from the committed results: 1,200 / 700 agents (METR p. 3); 6,051 and 6,000 records; 58% abstention; S2 → S2 0.87; 86% / 14%; S5 false positives.
- [ ] The video submission method is still unknown; ask the organizers.
- [ ] Credit line for Valerie on the title card.
