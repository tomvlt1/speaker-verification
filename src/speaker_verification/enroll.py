"""Enroll speaker profiles against Azure text-independent verification API."""

from __future__ import annotations

import csv
import json
import pathlib

from .api import request
from .config import DATA_DIR, ENROLLMENT_DIR


def enroll_one(name: str, audio_path: pathlib.Path) -> dict | None:
    """Create a profile and upload enrollment audio. Returns profile record or None."""
    profile = request(
        "POST",
        "/speaker/verification/v2.0/text-independent/profiles",
        json.dumps({"locale": "en-us"}),
    )
    if not profile or "profileId" not in profile:
        print(f"[enroll] could not create profile for {name}")
        return None

    profile_id = profile["profileId"]
    with audio_path.open("rb") as f:
        resp = request(
            "POST",
            f"/speaker/verification/v2.0/text-independent/profiles/{profile_id}"
            f"/enrollments?ignoreMinLength=true",
            f.read(),
            content_type="audio/wav",
        )
    if not resp:
        print(f"[enroll] enrollment upload failed for {name}")
        return None

    return {
        "name": name,
        "profile_id": profile_id,
        "status": resp.get("enrollmentStatus", "Unknown"),
        "audio_length_s": resp.get("enrollmentsLength", 0),
        "speech_length_s": resp.get("enrollmentsSpeechLength", 0),
    }


def enroll_from_csv(input_csv: pathlib.Path, output_csv: pathlib.Path) -> None:
    """Read (name, filepath) rows, enroll each, and write the resulting profile table."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with input_csv.open() as f:
        rows = list(csv.DictReader(f))

    results = []
    for row in rows:
        audio = pathlib.Path(row["filepath"])
        if not audio.exists():
            print(f"[enroll] missing file: {audio} — skipping")
            continue
        rec = enroll_one(row["name"], audio)
        if rec:
            results.append(rec)
            print(
                f"[enroll] {rec['name']} → {rec['profile_id']} "
                f"({rec['status']}, {rec['speech_length_s']}s speech)"
            )

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "profile_id", "status", "audio_length_s", "speech_length_s"],
        )
        writer.writeheader()
        writer.writerows(results)
    print(f"[enroll] wrote {len(results)} profiles → {output_csv}")


def cmd_enroll(args) -> None:
    src = pathlib.Path(args.input).resolve() if args.input else DATA_DIR / "enrollment_data.csv"
    dst = pathlib.Path(args.output).resolve() if args.output else DATA_DIR / "profiles.csv"
    if not src.exists():
        raise SystemExit(
            f"enrollment CSV not found: {src}\n"
            "Run `convert --audio-dir audio/enrollment --build-csv enrollment_data.csv` first."
        )
    enroll_from_csv(src, dst)
