"""
Fetch top-20 leaderboard from Kaggle for both tracks and write to leaderboard.json.
Runs daily via .github/workflows/update-leaderboard.yml.

Required env vars (set as GitHub Secrets):
  KAGGLE_USERNAME — your Kaggle username
  KAGGLE_KEY      — your Kaggle API token

Edit COMPETITION_SLUGS below once the actual Kaggle competition pages are created.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# === EDIT THESE WHEN KAGGLE COMPETITIONS ARE LIVE ===
# Find the slug in the competition URL: kaggle.com/competitions/<slug>
COMPETITION_SLUGS = {
    "small": "cuhk-x-competition-small-model-track",
    "large": "cuhk-x-competition-large-model-track",
}
TOP_N = 20

# === PUBLIC leaderboard only ===
# Kaggle's GetLeaderboard endpoint returns the PUBLIC leaderboard while a
# competition is running, but automatically switches to the PRIVATE leaderboard
# once it closes (the API has no public/private flag). The website must only ever
# show PUBLIC standings, and the public board is frozen at the submission deadline
# anyway — so we refuse to refresh past the freeze. Update this if the schedule moves.
PUBLIC_LB_FREEZE_UTC = datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc)  # Kaggle Leaderboard Freeze

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "leaderboard.json"


def fetch_track(api, slug):
    """Fetch top-N leaderboard entries for a single Kaggle competition."""
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
    # Safety: only ever publish the PUBLIC leaderboard. After the freeze the Kaggle
    # API would start returning private scores, so stop refreshing then.
    if datetime.now(timezone.utc) > PUBLIC_LB_FREEZE_UTC:
        print("Past the Kaggle Leaderboard Freeze; skipping refresh to keep the final "
              "PUBLIC standings and never publish the private leaderboard.")
        return

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: 'kaggle' package not installed. pip install kaggle", file=sys.stderr)
        sys.exit(1)

    api = KaggleApi()
    api.authenticate()

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    for track, slug in COMPETITION_SLUGS.items():
        print(f"Fetching '{track}' ({slug})…")
        track_data = fetch_track(api, slug)
        track_data["kaggle_url"] = f"https://www.kaggle.com/competitions/{slug}/leaderboard"
        payload[track] = track_data
        if "error" in track_data:
            print(f"  ! {track_data['error']}")
        else:
            print(f"  ✓ {len(track_data['entries'])} entries")

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
