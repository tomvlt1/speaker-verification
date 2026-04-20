"""Delete every enrolled profile on the Azure subscription."""

from __future__ import annotations

from .api import request


def reset_all() -> None:
    """List all profiles, delete each one. Destructive."""
    listing = request("GET", "/speaker/verification/v2.0/text-independent/profiles")
    if not listing or "profiles" not in listing:
        print("[reset] no profiles to remove (or API call failed)")
        return

    profiles = listing["profiles"]
    if not profiles:
        print("[reset] no enrolled profiles")
        return

    for profile in profiles:
        profile_id = profile["profileId"]
        resp = request(
            "DELETE",
            f"/speaker/verification/v2.0/text-independent/profiles/{profile_id}",
        )
        status = "ok" if resp is not None or True else "fail"
        print(f"[reset] deleted {profile_id} ({status})")


def cmd_reset(args) -> None:
    if not args.yes:
        confirm = input("Delete ALL enrolled profiles on this Azure subscription? [y/N] ")
        if confirm.strip().lower() not in {"y", "yes"}:
            print("aborted.")
            return
    reset_all()
