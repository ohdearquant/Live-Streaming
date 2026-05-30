# Lion Saturday Live — Production Workflow

The repeatable runbook for each weekly episode. Two actors: **Ocean** (manual steps —
streaming, platforms) and **the agent** (Claude — turns the raw recording into the
committed episode docs).

> **Cadence:** every Saturday. Announce in the morning, stream at noon.

---

## At a glance

```
SAT morning   Ocean   announce on LinkedIn · set Restream YouTube event (title + base description)
SAT noon      Ocean   join Zoom → allow Restream → multistream to X + YouTube + LinkedIn
after stream  Ocean   download video + transcript from Fireflies → episode folder
              AGENT   read transcript → write README.md + SUMMARY.md + youtube.md → PR → merge
              Ocean   paste chapter-aligned description + final title into YouTube Studio
```

No video is ever re-uploaded — YouTube auto-archives the live stream as a VOD (see FAQ).

---

## 1 · Pre-stream (Ocean)

- [ ] **Morning:** announce on LinkedIn — "streaming at noon ET."
- [ ] **Set up the Restream event** with the YouTube destination:
  - Title (≤100 chars) and a **base description** (≤5000 chars). Click _Edit_ next to the
    YouTube channel for YouTube-specific text if needed.
  - Restream multistreams to **X, YouTube, LinkedIn** simultaneously (already configured).
- [ ] **Noon:** start the Zoom, allow Restream to capture, go live.

The base title/description set here is what the live broadcast and the initial VOD inherit.
Chapters come later (their timestamps must match the final VOD — see §4 + FAQ).

## 2 · Post-stream capture (Ocean)

- [ ] Create the episode folder: `episodes/NNN-YYYYMMDD/` (zero-padded number, e.g. `002-20260606`).
- [ ] From **Fireflies**, download:
  - the **meeting video** → save as `episodes/NNN-YYYYMMDD/<anything>.mp4`
  - the **transcript** → save as `episodes/NNN-YYYYMMDD/TRANSCRIPT.md`
- [ ] Drop in any artifacts shown on stream (demo scripts, etc.).
- [ ] Note the **YouTube VOD URL** (from your channel) for the agent to embed.

> `*.mp4` and `TRANSCRIPT.md` are **gitignored** — they stay local. The public record is the
> write-ups the agent produces.

## 3 · Episode docs (agent)

Hand it to the agent: _"process episode NNN-YYYYMMDD (YouTube: <url>)."_ The agent then:

- [ ] Reads `TRANSCRIPT.md` (and any artifacts).
- [ ] Writes, from `episodes/_templates/`:
  - **`SUMMARY.md`** — the canonical public write-up (full topic-by-topic walkthrough; replaces
    the transcript). Long is fine.
  - **`README.md`** — short hub: hook, metadata (incl. YouTube link), techniques demonstrated,
    issues opened live, technologies mentioned.
  - **`youtube.md`** — title options + description + **chapters** (timestamps from the transcript;
    flagged for VOD re-alignment).
- [ ] Branches `episode/NNN-YYYYMMDD`, commits (pre-commit runs deno fmt + ruff), opens a PR.
- [ ] On Ocean's go, merges with `gh pr merge --merge --admin --delete-branch`.
      _(Admin override is expected — `main` is branch-protected to stop random pushes, not to gate
      Ocean's own merges.)_

## 4 · Publish (Ocean)

- [ ] In **YouTube Studio**, open the VOD and paste from `youtube.md`:
  - final **title**,
  - **description** with **chapters re-aligned to the VOD timeline** (start at `0:00`).
- [ ] Optional: thumbnail.

Done. The committed `SUMMARY.md` is the durable public notes; the VOD is the video.

---

## FAQ — Restream → YouTube

**Does the video stay on YouTube after streaming via Restream?**
Yes. YouTube automatically archives every completed live stream (under 12 h) as a VOD on your
channel. Each weekly stream becomes a **new VOD with its own URL** — you never re-upload.
Restream only pushes the RTMP feed; YouTube records and keeps it.
([YouTube docs](https://support.google.com/youtube/answer/6247592?hl=en))

**Then why does Restream also "record"?**
Restream keeps its own downloadable copy in Restream Video Storage (15 days Standard/Pro,
30 days Business) — a backup for re-purposing, separate from the published YouTube VOD.

**How do I set title/description ahead of time?**
In the Restream event editor before going live (per-channel _Edit_ for YouTube-specific text).
The live broadcast + initial VOD inherit it. You can also edit the VOD's title/description/
chapters anytime afterward in YouTube Studio.
([Restream: titles & descriptions](https://support.restream.io/en/articles/837678-set-your-stream-title-and-description) ·
[Restream: create a YouTube event](https://support.restream.io/en/articles/10831162-create-a-youtube-live-event-with-restream))

**Why are chapters added _after_ the stream?**
YouTube chapters need timestamps that start at `0:00` and match the VOD timeline. The
Fireflies/Zoom transcript clock has a different start offset, so `youtube.md`'s chapter times
must be re-aligned to the VOD before pasting into the description.

---

## Folder convention

```
episodes/
  _templates/         _README.md · _SUMMARY.md   (copy these per episode)
  NNN-YYYYMMDD/
    README.md         short hub            (committed)
    SUMMARY.md        full write-up        (committed)
    youtube.md        title/desc/chapters  (committed)
    <demo>.py …       artifacts            (committed)
    TRANSCRIPT.md     raw transcript       (gitignored)
    *.mp4             session video        (gitignored)
```
