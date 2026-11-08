# SPEC: "The board that sorts itself" (storyline A)

GOAL:    The viewer leaves knowing one thing: a swarm's organisation shows in the *shape* of its traffic, and its identity (S5) lives in the whole system, not in any message, so where that identity lives decides where to intervene.

OUTPUT:  HyperFrames, 1920 x 1080, 30 fps.
TIME:    target 180 s x 30 = 5,400 frames. Provisional scene slots are below; they are re-timed to Hunter's recorded narration (the voice is the clock).

LOOK:    the medium is the swarm's own medium: a shared directory listing ("Index of /…"), full-bleed, never floating.
         ground #F4F3EF (screen white, 0 grain); ink #141414; rule #D9D7D0; dim #6B6A66.
         listing face: JetBrains Mono 400, 22 px, line height 34 px, rows at 34 px pitch, left margin 120 px.
         display face: Inter 900 at 96 px, tracking -2.5%; secondary Inter 700 at 44 px. Body copy is never under 28 px.
         data accents, the only colours, tied to the dataset as in the paper's figures:
           wiki / coordination #2A78D6 (blue); Swarm Traces / attack #EB6834 (orange).
           One accent per shot, except the two-series results shot.
         no shadows, blur, grain, glow or gradients. Light is flat screen light.

OBJECTS: board rows: name | modified | size, mono, like a directory index; prefixes follow METR's message types (zzASK, zzR, zzIDEA, zzFILE, zzINBOX, zzURG). Entries are illustrative, labelled "illustrative entries, after METR (2026)".
         band: a horizontal strip of rows with a label at the left margin: "S1 operations · fast" … "S5 identity & policy · slowest".
         stamp: a rectangular ink box "INSUFFICIENT EVIDENCE", 2 px ink border, Inter 700 26 px, set at -4°.
         bars and matrix: built from row blocks (34 px tall), so the data is made of the board itself.

MOTION:  enter power3.out 14 frames; move power2.inOut 18 frames; exit power2.in 10 frames; camera (board shift) sine.inOut 24 frames.
         row stagger 1 frame. Band flicker rates: S1 every 6 frames, S2 30, S3 60, S4 90, S5 still.
         big lines land in 14 frames and hold; they never drift after landing.

SHOTS (provisional, s):
  1 hook     0–22    board scrolls; one row is highlighted and opens into the line "Meant to be isolated. They found a shared board." → 1,200 agents · 70,000+ messages → 700 joined the attack. Hands off: the scroll stops.
  2 lens     22–50   rows sort into five bands, S1 bottom → S5 top, each named as the voice names it, then each flickers at its cadence. Credit: "framing: Valerie Kim".
  3 method   50–82   two corpus counters, 6,051 wiki and 6,000 Swarm Traces; stamps land on thin rows, which drop out; 58% lands. Footer: "frozen · resumable · verified row by row · pre-registered".
  4 results  82–124  row blocks stack into bars (S1, S2, S4 per dataset, real shares), then rebuild into the wiki S2 → S2 matrix with the 0.87 cell; then 86% / 14% for Swarm Traces.
  5 s5       124–148 the S5 band sits empty; "Every record labelled S5 was a false positive."; then the whole board moves as one, and four words attach to it: identity · sacrifice · succession · binding rules (METR 2026).
  6 loci     148–170 the board splits in two: "In the channel → isolate, authenticate" | "In the model → training".
  7 close    170–180 the closing line, then the names.

BANNED:  dark void; glow or particles; three cards in a row; everything fading up; titles drifting after landing; corner HUD labels; logo docking; any number not in data.js; dashed lines.
QA:      2 s (thumbnail: the board plus the highlighted row), 30 s (five bands, labels legible), 60 s (stamps legible), 95 s (bars match Figure 2), 110 s (0.87 cell), 135 s (empty S5 band), 160 s (split), 178 s (names).
