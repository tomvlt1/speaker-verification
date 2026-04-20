"""CLI entry point. Run with `python -m speaker_verification <command>`."""

from __future__ import annotations

import argparse

from .convert import cmd_convert
from .enroll import cmd_enroll
from .reset import cmd_reset
from .verify import cmd_verify


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="speaker_verification",
        description="Identify speakers in an audio file via Azure Speaker Recognition.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # convert
    c = sub.add_parser("convert", help="Normalize audio to 16 kHz mono WAV.")
    c.add_argument("--audio-dir", required=True, help="Folder of source audio files (m4a/wav/mp3/ogg/flac).")
    c.add_argument(
        "--build-csv",
        help="Optional: also build a (name, filepath) enrollment CSV at data/<name>.",
    )
    c.set_defaults(func=cmd_convert)

    # enroll
    e = sub.add_parser("enroll", help="Create profiles and upload enrollment audio to Azure.")
    e.add_argument("--input", help="Enrollment CSV (default: data/enrollment_data.csv).")
    e.add_argument("--output", help="Output profiles CSV (default: data/profiles.csv).")
    e.set_defaults(func=cmd_enroll)

    # verify
    v = sub.add_parser("verify", help="Score verification audio against enrolled profiles.")
    v.add_argument("--audio-dir", help="Folder of WAVs to verify (default: audio/verification).")
    v.add_argument("--profiles", help="Enrolled profiles CSV (default: data/profiles.csv).")
    v.add_argument("--output", help="Output results CSV (default: data/verification_results.csv).")
    v.set_defaults(func=cmd_verify)

    # reset
    r = sub.add_parser("reset", help="Delete ALL enrolled profiles on this Azure subscription.")
    r.add_argument("-y", "--yes", action="store_true", help="Skip the confirmation prompt.")
    r.set_defaults(func=cmd_reset)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
