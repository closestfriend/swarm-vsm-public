"""Split a recording at real pauses (>= MIN s) and transcribe each chunk alone: exact phrase boundaries."""
import json, re, subprocess, sys
D = "/Users/hnsk/.claude/jobs/11e5705c/tmp/rec/"
src, MIN = D + sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-vn", "-af",
                      f"silencedetect=noise=-40dB:d={MIN}", "-f", "null", "-"], capture_output=True, text=True).stderr
S = [(float(s), float(e)) for s, e in zip(re.findall(r"silence_start: ([0-9.]+)", log), re.findall(r"silence_end: ([0-9.]+)", log))]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout)
edges, t = [], 0.0
for s, e in S:
    if s - t > 0.15:
        edges.append((t, s))
    t = e
if dur - t > 0.15:
    edges.append((t, dur))
out = []
for k, (a, b) in enumerate(edges):
    wav = f"{D}chunk_{k}.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}",
                    "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    subprocess.run(["rm", "-rf", f"{D}ck"]); subprocess.run(["mkdir", "-p", f"{D}ck"])
    subprocess.run(["npx", "--yes", "hyperframes", "transcribe", wav, "--dir", f"{D}ck", "--engine", "whisper",
                    "--model", "small.en", "--language", "en", "--json"], capture_output=True)
    try:
        W = json.load(open(f"{D}ck/transcript.json"))
        W = W if isinstance(W, list) else W["words"]
        txt = " ".join(w["text"] for w in W)
    except Exception:
        txt = "(none)"
    out.append({"k": k, "start": round(a, 3), "end": round(b, 3), "text": txt})
    print(f"{k:3d} [{a:7.2f}-{b:7.2f}] {txt}")
json.dump(out, open(D + sys.argv[1] + ".chunks.json", "w"), indent=1)
