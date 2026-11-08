# Narration cut

The source recording is Hunter's take 1: 5:27, Photo Booth, 2026-11-07. It is never committed; it lives in `video/recordings/` (gitignored).

**Current rough cut:** `video/recordings/rough_cut_2.mp4`, 2:56.

## Method (reproducible)

1. **Transcribe** with `npx hyperframes transcribe take1.mov --engine whisper --model small.en --language en`. This gives word timestamps. Whisper drops "um"/"uh" and leaves no gaps between words, so the transcript can't find pauses on its own.
2. **Detect silences** with ffmpeg `silencedetect` twice:
   - a coarse pass (-38 dB, ≥ 0.45 s) to shorten pauses: each pause over 0.5 s is cut down, keeping 0.2 s at each edge;
   - a fine pass (-40 dB, ≥ 0.1 s) to place cut edges.
3. **Cut the asides** by word index (`plan_cut.py`). Each cut edge snaps to the middle of the nearest micro-pause, because Whisper word times drift by ±0.5 s. A few edges are set by hand (the `OVERRIDE` table), with the reason noted.
4. **Encode** with `node ~/.claude/skills/media-use/scripts/transcript-cut.mjs --remove "<ranges>"`.
5. **QA:** re-transcribe the cut, and check doubtful joins with `splice_check.py`, which re-hears about 3 s around a join with `medium.en`.

## Removed (take 1)

- "It was just noise." It also overstates: fragments are not noise.
- The "treasure map within the treasure" aside.
- The garbled half of the wiki sentence (a pickup slot).
- "And I think that's because … Beer's point." The next sentence says it.
- "So yeah, that was very helpful." / "It's just crazy."
- "So I guess".
- The white-collar crime analogy (3:46–5:12). It is **kept for the live talk and Q&A**: look at the shape of the communication, not the individual emails.
- The repeated ending, and "Thank you" (the end card closes the video).

## Final narration (2026-11-07): `video/recordings/narration_final.wav`, 2:52

Built by `build_narration.py`: take 1 with asides removed and pauses tightened, plus three lines from the pickup clip (Photo Booth, 4:34 PM):

- "Seven hundred of them went on to attack Hugging Face." replaces the original line, which Whisper heard as "her base" and which included "presumably a few other places".
- "On the wiki pages, the agents mostly coordinate. And once they start, they keep going. Nine times out of ten, the next message is coordination also." "So like" is cut at 6.80 s; checked by re-transcription.
- "Swarms don't hide their organization in their messages. They show it in their shape." Starts at 13.30 s so the soft 'S' survives; confirmed with medium.en.

The pickup's phrase boundaries came from splitting it at real pauses and transcribing each piece alone (`chunks.py` logic), because Whisper's in-clip timestamps were off by more than 1 s. Loudness is normalised to -16 LUFS.

## Pickups (recorded)

1. "On the wiki pages, the agents mostly coordinate. And once they start, they keep going: nine times out of ten, the next message is coordination too."
2. "Swarms don't hide their organisation in their messages. They show it in their shape."
3. Optional: "Seven hundred of them went on to attack Hugging Face." Whisper heard "Hugging Face" as "hiring base"; listen to 0:06 and decide.
