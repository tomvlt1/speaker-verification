"""Verify enrolled speakers against new audio clips."""

from __future__ import annotations

import csv
import pathlib

from pydub import AudioSegment

from .api import request
from .config import DATA_DIR, VERIFICATION_DIR


def load_profiles(profiles_csv: pathlib.Path) -> dict[str, str]:
    """Return {profile_id: name} from the enrollment output."""
    with profiles_csv.open() as f:
        return {row["profile_id"]: row["name"] for row in csv.DictReader(f)}


def verify_audio(audio: pathlib.Path, profiles: dict[str, str]) -> list[dict]:
    """For each enrolled profile, ask Azure: does this audio match? Return accepted matches."""
    audio_bytes = audio.read_bytes()
    duration_s = len(AudioSegment.from_file(str(audio))) / 1000.0

    accepts: list[dict] = []
    for profile_id, name in profiles.items():
        resp = request(
            "POST",
            f"/speaker/verification/v2.0/text-independent/profiles/{profile_id}/verify",
            audio_bytes,
            content_type="audio/wav",
        )
        if resp and resp.get("recognitionResult") == "Accept":
            accepts.append(
                {
                    "audio_file": audio.name,
                    "audio_length_s": round(duration_s, 3),
                    "name": name,
                    "profile_id": profile_id,
                    "score": resp.get("score", 0.0),
                }
            )
    return accepts


def verify_folder(folder: pathlib.Path, profiles_csv: pathlib.Path, out_csv: pathlib.Path) -> None:
    profiles = load_profiles(profiles_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for wav in sorted(folder.glob("*.wav")):
        rows = verify_audio(wav, profiles)
        all_rows.extend(rows)
        if rows:
            best = max(rows, key=lambda r: r["score"])
            print(f"[verify] {wav.name} → {best['name']} (score {best['score']:.3f})")
        else:
            print(f"[verify] {wav.name} → no match")

    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["audio_file", "audio_length_s", "name", "profile_id", "score"],
        )
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"[verify] wrote {len(all_rows)} match(es) → {out_csv}")


def cmd_verify(args) -> None:
    folder = pathlib.Path(args.audio_dir).resolve() if args.audio_dir else VERIFICATION_DIR
    profiles_csv = pathlib.Path(args.profiles).resolve() if args.profiles else DATA_DIR / "profiles.csv"
    out_csv = pathlib.Path(args.output).resolve() if args.output else DATA_DIR / "verification_results.csv"
    if not profiles_csv.exists():
        raise SystemExit(f"profiles CSV not found: {profiles_csv}. Run `enroll` first.")
    if not folder.is_dir():
        raise SystemExit(f"verification dir not found: {folder}")
    verify_folder(folder, profiles_csv, out_csv)
