"""
Fetch the top-20 PUBLIC leaderboard from Kaggle for both tracks and write
leaderboard.json. Runs daily via .github/workflows/update-leaderboard.yml.

Required env vars (set as GitHub Secrets):
  KAGGLE_USERNAME — a Kaggle username
  KAGGLE_KEY      — that account's Kaggle API token

PUBLIC-LEADERBOARD SAFETY
-------------------------
The website must NEVER display the private leaderboard. Kaggle's API has no
public/private flag: it returns the PUBLIC board while a competition is open and
silently switches to the PRIVATE board once the competition closes. Two
independent layers keep us on the public board only:

  1. Hard backstop — never refresh after PUBLIC_LB_FREEZE_UTC (the published
     Leaderboard Freeze). Update that constant if the schedule moves.
  2. Live deadline check — before fetching a track we read its real Kaggle
     deadline and skip the fetch if that deadline has already passed (catches an
     early close). If the deadline can't be read we fall back to layer 1, so the
     board still updates during the competition but never past the freeze.

A skipped track keeps its last published PUBLIC snapshot; private data is never
fetched or written.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Slugs from the competition URL: kaggle.com/competitions/<slug>
COMPETITION_SLUGS = {
    "small": "cuhk-x-competition-small-model-track",
    "large": "cuhk-x-competition-large-model-track",
}
TOP_N = 6

# Hard backstop — never refresh past the published Leaderboard Freeze, even if
# the live deadline check below fails. Update this if the schedule changes.
PUBLIC_LB_FREEZE_UTC = datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "leaderboard.json"


def competition_deadline(api, slug):
    """Real submission deadline (aware UTC) for `slug`, or None if it can't be
    confirmed. Used only to TIGHTEN the freeze (catch an early close); when it
    returns None we fall back to the PUBLIC_LB_FREEZE_UTC backstop."""
    try:
        resp = api.competitions_list(search=slug)
        comps = resp if isinstance(resp, list) else (getattr(resp, "competitions", None) or [])
        for c in comps:
            ref = str(getattr(c, "ref", "")).rstrip("/")
            if ref.split("/")[-1] == slug:
                dl = getattr(c, "deadline", None)
                if not isinstance(dl, datetime):
                    return None
                return dl if dl.tzinfo else dl.replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"  ! deadline lookup failed for {slug}: {type(e).__name__}: {e}")
    return None


def fetch_track(api, slug):
    """Fetch top-N PUBLIC leaderboard entries for one open competition."""
    try:
        result = api.competition_leaderboard_view(slug)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "entries": []}

    entries = []
    for i, item in enumerate(result[:TOP_N], start=1):
        # Kaggle's leaderboard objects expose: teamName, score, submissionDate, etc.
        team = getattr(item, "teamName", None) or getattr(item, "team_name", None) or "—"
        score = getattr(item, "score", "—")
        sub_count = getattr(item, "submissionCount", None) or getattr(item, "submission_count", None)
        sub_date = getattr(item, "submissionDate", None) or getattr(item, "submission_date", None)
        if hasattr(sub_date, "strftime"):
            sub_date = sub_date.strftime("%Y-%m-%d")
        entries.append({
            "rank": i,
            "team": str(team),
            "score": str(score),
            "submissions": sub_count if sub_count is not None else "—",
            "last_submission": str(sub_date) if sub_date else "—",
        })
    return {"entries": entries}


def main():
    now = datetime.now(timezone.utc)

    # Layer 1 — hard backstop. After the freeze do nothing at all, so the file is
    # left frozen at its last PUBLIC snapshot and private data is never fetched.
    if now > PUBLIC_LB_FREEZE_UTC:
        print("Past the Kaggle Leaderboard Freeze; not refreshing (public-only safeguard).")
        return

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: 'kaggle' package not installed. pip install kaggle", file=sys.stderr)
        sys.exit(1)

    api = KaggleApi()
    api.authenticate()

    # Keep the last published snapshot so a closed track retains its final PUBLIC
    # board instead of being wiped (and never gets overwritten with private data).
    try:
        previous = json.loads(OUTPUT_PATH.read_text())
        if not isinstance(previous, dict):
            previous = {}
    except Exception:
        previous = {}

    tracks_out = {}
    any_fetched = False

    for track, slug in COMPETITION_SLUGS.items():
        kaggle_url = f"https://www.kaggle.com/competitions/{slug}/leaderboard"
        deadline = competition_deadline(api, slug)
        # Layer 2 — only skip when we can POSITIVELY confirm the deadline has passed.
        if deadline is not None and now >= deadline:
            print(f"Skipping '{track}' ({slug}) — competition closed {deadline.isoformat()}; "
                  f"keeping last public snapshot (no private fetch).")
            prev = previous.get(track)
            prev = prev if isinstance(prev, dict) else {}
            tracks_out[track] = {
                "entries": prev.get("entries", []),
                "kaggle_url": kaggle_url,
                "frozen": True,
                "note": "Not refreshed — competition closed (public-only safeguard).",
            }
            continue

        print(f"Fetching '{track}' ({slug})…")
        track_data = fetch_track(api, slug)
        track_data["kaggle_url"] = kaggle_url
        any_fetched = True
        if "error" in track_data:
            print(f"  ! {track_data['error']}")
        else:
            print(f"  ✓ {len(track_data['entries'])} entries")
        tracks_out[track] = track_data

    # Advance the timestamp only when something was actually fetched, so a fully
    # frozen run produces no spurious change/commit.
    updated_at = (now.isoformat().replace("+00:00", "Z") if any_fetched
                  else previous.get("updated_at") or now.isoformat().replace("+00:00", "Z"))

    payload = {"updated_at": updated_at, **tracks_out}
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
