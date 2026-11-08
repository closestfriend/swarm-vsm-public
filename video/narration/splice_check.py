"""Re-hear one splice with a stronger model: extract ~3 s around a word in the cut and transcribe it alone."""
import json, subprocess, sys
D = "/Users/hnsk/.claude/jobs/11e5705c/tmp/rec/"
cut, qa, word = sys.argv[1], sys.argv[2], sys.argv[3].lower()
W = json.load(open(D + qa + "/transcript.json"))
W = W if isinstance(W, list) else W["words"]
hits = [x for x in W if x["text"].lower().strip(".,").startswith(word)]
x = hits[-1]
print("small.en heard:", x)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0, x['start'] - 1.2):.2f}", "-t", "3.2",
                "-i", D + cut, "-vn", "-ac", "1", "-ar", "16000", D + "splice.wav"], check=True)
subprocess.run(["rm", "-rf", D + "qs"]); subprocess.run(["mkdir", "-p", D + "qs"])
subprocess.run(["npx", "--yes", "hyperframes", "transcribe", D + "splice.wav", "--dir", D + "qs", "--engine", "whisper",
                "--model", "medium.en", "--language", "en", "--json"], capture_output=True)
S = json.load(open(D + "qs/transcript.json"))
S = S if isinstance(S, list) else S["words"]
print("medium.en on the 3.2 s clip:", " ".join(s["text"] for s in S))
