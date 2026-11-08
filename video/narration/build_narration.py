"""Assemble the final narration: take 1 (asides removed, pauses tightened) + three pickup lines.

Inputs (local, gitignored; pass the folder holding take1.mov, pickup1.mov, transcript.json,
silence.log and silence_fine.log):  python3 build_narration.py <dir>
Output: <dir>/narration.wav (mono 48 kHz, loudness-normalised to -16 LUFS) and narration_plan.json.
Every boundary below was checked by re-transcribing the joins (see README.md).
"""
import json, re, subprocess, sys
D = sys.argv[1].rstrip("/") + "/"
W = json.load(open(D + "transcript.json")); W = W if isinstance(W, list) else W["words"]


def sil(path):
    log = open(path).read()
    return [(float(s), float(e)) for s, e in zip(re.findall(r"silence_start: ([0-9.]+)", log),
                                                re.findall(r"silence_end: ([0-9.]+)", log))]


SIL, FINE = sil(D + "silence.log"), sil(D + "silence_fine.log")
TOTAL = W[-1]["end"]


def mid_fine(t, before=0.6, after=0.9):
    c = [(abs(s - t), (s + e) / 2) for s, e in FINE if t - before <= s <= t + after]
    return min(c)[1] if c else t


# Take-1 removals (seconds). Replaced passages first, then asides (word ranges snapped to micro-pauses).
REMOVE = [
    (7.70, 14.00),     # "700 of them ... as well."      -> pickup 'Seven hundred ... Hugging Face.'
    (112.95, 129.20),  # garbled wiki sentence            -> pickup 'On the wiki pages ...'
    (217.93, TOTAL),   # 'So I guess ... shape.' + rest   -> pickup 'Swarms don't hide ...'
    (87.96, 89.12),    # 'It was just noise.' (overstates; edges checked by re-transcription)
]
for a, b in [(221, 235), (338, 367), (395, 400), (424, 426)]:   # treasure, Beer aside, 'that was helpful', 'crazy'
    t0 = mid_fine(W[a]["start"])
    c = [(abs(e - W[b + 1]["start"]), (s + e) / 2) for s, e in FINE if W[b + 1]["start"] - 1.6 <= e <= W[b + 1]["start"] + 0.4]
    REMOVE.append((t0, min(c)[1] if c else W[b + 1]["start"] - 0.3))
REMOVE += [(s + 0.2, e - 0.2) for s, e in SIL if e - s > 0.5]   # tighten pauses, keep 0.2 s each side
REMOVE.sort()
merged = []
for s, e in REMOVE:
    if merged and s <= merged[-1][1] + 0.02:
        merged[-1] = (merged[-1][0], max(merged[-1][1], e))
    else:
        merged.append((s, e))
kept, t = [], 0.0
for s, e in merged:
    if s > t + 0.05:
        kept.append((t, s))
    t = max(t, e)
if TOTAL > t + 0.05:
    kept.append((t, TOTAL))


def take(lo, hi):
    return [("T", max(a, lo), min(b, hi)) for a, b in kept if b > lo and a < hi]


P = "P"
pieces = (take(0, 7.70)
          + [(P, 24.00, 27.72)]                                   # Seven hundred of them went on to attack Hugging Face.
          + take(14.00, 112.95)
          + [(P, 1.13, 6.20), (P, 6.80, 10.60)]                   # On the wiki pages ... coordination also. ('So like' cut)
          + take(129.20, 217.93)
          + [(P, 13.30, 18.93)])                                  # Swarms don't hide ... their shape. (starts in the pause: soft 'S')
pieces = [p for p in pieces if p[2] - p[1] > 0.04]

FADE = 0.012
parts, labels = [], []
for i, (src, a, b) in enumerate(pieces):
    inp = 0 if src == "T" else 1
    d = b - a
    parts.append(f"[{inp}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},"
                 f"afade=t=out:st={max(0, d - FADE):.3f}:d={FADE}[p{i}]")
    labels.append(f"[p{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11[out]"
open(D + "narration_filter.txt", "w").write(fc)
# ffmpeg 8 reads a filter graph from a file with "-/filter_complex <file>".
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", D + "take1.mov", "-i", D + "pickup1.mov",
                "-/filter_complex", D + "narration_filter.txt", "-map", "[out]", "-ac", "1", "-ar", "48000",
                D + "narration.wav"], check=True)
dur = sum(b - a for _, a, b in pieces)
json.dump({"pieces": pieces, "duration_s": round(dur, 2)}, open(D + "narration_plan.json", "w"), indent=1)
print(f"pieces {len(pieces)}  narration {dur:.1f}s  -> {D}narration.wav")
