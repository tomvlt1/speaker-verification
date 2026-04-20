# speaker-verification

Identify speakers in an audio recording by comparing it against short enrollment clips. Wraps the [Azure Speaker Recognition](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speaker-recognition-overview) text-independent API.

Original use case: a classroom — enroll each student with a 30–45 s clip, then feed in a long lecture recording and get a per-speaker speaking-time breakdown.

> **Bring your own audio.** No voice samples are shipped with this repo (biometric data shouldn't live in a public repo). Drop your enrollment clips into `audio/enrollment/` and your verification clips into `audio/verification/` — both are gitignored.

## How it works

```
  audio/enrollment/*.m4a            audio/verification/*.wav
         │                                   │
         ▼                                   ▼
    convert  (pydub → 16 kHz mono wav)   convert
         │                                   │
         ▼                                   │
    enroll  ── POST profile  ──┐             │
    enroll  ── upload wav  ────┤             │
                              Azure          │
                               │             │
                               ▼             ▼
                           profiles.csv ──► verify
                                              │
                                              ▼
                                 verification_results.csv
                                 (name, score, audio_length)
```

- **enroll** creates one Azure profile per person, uploads their clip, and saves `(name, profile_id, status, audio_length_s, speech_length_s)` to `data/profiles.csv`.
- **verify** takes a folder of clips, queries each enrolled profile for a match, and keeps only `Accept` results with a score above Azure's threshold.

## Setup

Requires Python 3.10+ and [ffmpeg](https://ffmpeg.org/) on your path (pydub depends on it).

```bash
git clone https://github.com/<your-username>/speaker-verification.git
cd speaker-verification
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env           # then fill in your Azure key + region
```

Get an Azure Speech key: [portal.azure.com](https://portal.azure.com) → create a Speech resource → Keys and Endpoint. The free tier is fine for testing.

## Usage

Drop enrollment audio (one file per speaker) into `audio/enrollment/`, verification audio into `audio/verification/`. Filename stem becomes the speaker name (trailing `_p` is stripped).

```bash
# 1. normalize m4a/mp3/... → 16 kHz mono wav, then write an enrollment csv
python -m speaker_verification convert \
  --audio-dir audio/enrollment \
  --build-csv enrollment_data.csv

# 2. enroll each speaker against Azure
python -m speaker_verification enroll

# 3. verify a folder of new recordings against the enrolled profiles
python -m speaker_verification convert --audio-dir audio/verification
python -m speaker_verification verify
```

Results land in `data/verification_results.csv`.

```bash
# nuke all enrolled profiles on the Azure subscription (with a confirmation prompt)
python -m speaker_verification reset
python -m speaker_verification reset --yes   # skip prompt
```

## Output format

`data/profiles.csv`:

| name | profile_id | status | audio_length_s | speech_length_s |
|---|---|---|---|---|
| alice | 5e2a… | Enrolled | 37.9 | 34.9 |

`data/verification_results.csv`:

| audio_file | audio_length_s | name | profile_id | score |
|---|---|---|---|---|
| lecture_01.wav | 823.4 | alice | 5e2a… | 0.87 |
| lecture_01.wav | 823.4 | bob   | 88e7… | 0.77 |

Multiple accept rows per file are possible — Azure verifies independently against each profile, so in a lecture with four enrolled students you can get four matches on the same clip.

## Known limitations

- **Azure subscription required.** This is a thin client — the actual model is Microsoft's. Free tier is rate-limited (20 transactions per second, 10,000 per month at time of writing).
- **Text-independent verification needs ≥20 s of speech** per enrollment for reliable scores. Azure returns `Enrolling` rather than `Enrolled` if you're below that.
- **No per-speaker speaking time yet.** `verify` tells you *which* enrolled speakers appear in a clip but not *for how long*. To get that, you'd need to split the input into short segments and run `verify` on each (easy to add — happy to accept PRs).
- **Binary Accept/Reject.** Azure returns a confidence score 0–1, but there's no timestamp alignment — it's a global judgment on the whole clip.
- **Privacy.** Enrollment audio contains biometric data. Don't commit it; the `.gitignore` here already protects `audio/**/*`.

## Layout

```
src/speaker_verification/
  __main__.py   # argparse dispatcher
  api.py        # single HTTP helper for Azure calls
  config.py     # env vars (.env loader) + project paths
  convert.py    # ffmpeg → 16 kHz mono wav + enrollment csv builder
  enroll.py     # create profiles + upload enrollment clips
  verify.py     # verify unknown audio against all profiles
  reset.py      # delete every profile on this subscription
audio/
  enrollment/   # your clips go here (gitignored)
  verification/ # your clips go here (gitignored)
data/           # generated csvs land here (gitignored)
```
