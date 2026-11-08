"""Build the removal list for cut 1: asides (by word index) + pauses shortened to 0.3 s."""
import json, re
D = "/Users/hnsk/.claude/jobs/11e5705c/tmp/rec/"
W = json.load(open(D + "transcript.json"))
W = W if isinstance(W, list) else W["words"]
# Asides to remove (inclusive word indices), checked against the printed transcript.
ASIDES = [(196, 199, "It was just noise."), (221, 235, "treasure map aside"),
          (250, 259, "garbled: which is where these agents were made into coordinating, that (pickup slot)"),
          (338, 367, "And I think that's because ... Beers point."), (395, 400, "So yeah, that was very helpful."),
          (424, 426, "It's just crazy."), (461, 463, "So I guess (keep: takeaway from this is)"),
          (482, 701, "white-collar crime analogy + repeated ending + 'Thank you' (end card closes instead)")]
# Hand-set edges where Whisper timing and the pause detector disagree (checked by re-transcribing the cut).
OVERRIDE = {461: (217.93, 218.57),  # remove "So I guess" only; end mid-pause (218.41-218.73) before "takeaway"
            482: (225.46, None)}    # start in the pause (225.41-225.52) before "which"
for a, b, label in ASIDES:
    print(f"remove words {a}-{b}: {' '.join(x['text'] for x in W[a:b+1])[:90]!r}")
log = open(D + "silence.log").read()
SIL = [(float(s), float(e)) for s, e in zip(re.findall(r"silence_start: ([0-9.]+)", log),
                                           re.findall(r"silence_end: ([0-9.]+)", log))]


flog = open(D + "silence_fine.log").read()
FINE = [(float(s), float(e)) for s, e in zip(re.findall(r"silence_start: ([0-9.]+)", flog),
                                            re.findall(r"silence_end: ([0-9.]+)", flog))]


def snap_start(t):
    """Removal begins at the middle of the micro-pause nearest t (Whisper word times drift ±0.5 s)."""
    c = [(abs(s - t), (s + e) / 2) for s, e in FINE if t - 0.6 <= s <= t + 0.9]
    return min(c)[1] if c else t + 0.15


def snap_end(t):
    """Removal ends at the middle of the micro-pause just before the next kept word."""
    c = [(abs(e - t), (s + e) / 2) for s, e in FINE if t - 1.6 <= e <= t + 0.4]
    return min(c)[1] if c else t - 0.3


ranges = []
for a, b, _ in ASIDES:
    t0 = snap_start(W[a]["start"])
    t1 = snap_end(W[b + 1]["start"]) if b + 1 < len(W) else W[b]["end"]
    o0, o1 = OVERRIDE.get(a, (None, None))
    t0, t1 = (o0 if o0 is not None else t0), (o1 if o1 is not None else t1)
    if t1 > t0:
        ranges.append((t0, t1))
# Pauses: keep 0.3 s of each silence longer than 0.45 s (centre trimmed).
sil = [(s + 0.2, e - 0.2) for s, e in SIL if e - s > 0.5]
for (a, b, label), (t0, t1) in zip(ASIDES, ranges):
    print(f"  cut {t0:7.2f}-{t1:7.2f}  {label[:50]}")
allr = sorted(ranges + sil)
merged = []
for s, e in allr:
    if merged and s <= merged[-1][1] + 0.02:
        merged[-1] = (merged[-1][0], max(merged[-1][1], e))
    else:
        merged.append((s, e))
removed = sum(e - s for s, e in merged)
total = W[-1]["end"]
print(f"\nranges {len(merged)}  removed {removed:.1f}s  kept {total - removed:.1f}s of {total:.1f}s")
open(D + "remove.txt", "w").write(",".join(f"{s:.2f}-{e:.2f}" for s, e in merged))
