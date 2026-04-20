"""Audio format conversion: normalize enrollment/verification clips to 16 kHz mono WAV."""

from __future__ import annotations

import csv
import pathlib

from pydub import AudioSegment

from .config import DATA_DIR

SUPPORTED_INPUTS = (".m4a", ".mp3", ".wav", ".ogg", ".flac")


def to_wav_16k_mono(source: pathlib.Path, dest: pathlib.Path) -> None:
    """Convert any audio file to 16 kHz mono WAV."""
    sound = AudioSegment.from_file(str(source))
    sound = sound.set_channels(1).set_frame_rate(16000)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sound.export(str(dest), format="wav", parameters=["-ac", "1", "-ar", "16000"])


def normalize_folder(folder: pathlib.Path) -> list[pathlib.Path]:
    """Normalize every audio file in a folder in-place to 16 kHz mono WAV.

    Files already at .wav are re-exported to guarantee the sample rate.
    Returns the list of normalized WAV paths.
    """
    wavs: list[pathlib.Path] = []
    for src in sorted(folder.iterdir()):
        if src.suffix.lower() not in SUPPORTED_INPUTS or src.name.startswith("."):
            continue
        dest = src.with_suffix(".wav")
        to_wav_16k_mono(src, dest)
        wavs.append(dest)
        print(f"normalized → {dest.name}")
    return wavs


def build_enrollment_csv(folder: pathlib.Path, out_csv: pathlib.Path) -> pathlib.Path:
    """Write a (name, filepath) CSV for every WAV in folder.

    Speaker name is derived from the filename stem (minus any trailing `_p`).
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "filepath"])
        for wav in sorted(folder.glob("*.wav")):
            name = wav.stem.removesuffix("_p")
            writer.writerow([name, str(wav.resolve())])
    print(f"wrote {out_csv}")
    return out_csv


def cmd_convert(args) -> None:
    source = pathlib.Path(args.audio_dir).resolve()
    if not source.is_dir():
        raise SystemExit(f"audio dir not found: {source}")
    wavs = normalize_folder(source)
    if args.build_csv:
        out_csv = DATA_DIR / args.build_csv
        build_enrollment_csv(source, out_csv)
    print(f"done. {len(wavs)} file(s) normalized.")
