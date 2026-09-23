"""Trigger an Apify actor, wait for it to finish, and save its results as JSON.

This is the "ingestion" half of the scraping pipeline described in the
research-app outline. It deliberately stops at "fetch the raw scrape and save
it to a file" -- it does NOT synthesize results into ad angles / pain themes
or post them into Pipeline. That next step is done by Claude (in a Claude
Code / Claude Desktop session connected to Pipeline's MCP server), reading
the saved JSON and calling the research-app MCP tools (create_competitor_ad,
upsert_keyword, upsert_pain_theme) or the contact tools (create_contact) by
hand. Keeping synthesis out of this script keeps a human/Claude review step
between "scraped data" and "what lands in the CRM."

Setup:
    1. Add your Apify API token to .env (not .env.example):
           APIFY_API_TOKEN=apify_api_xxxxxxxx
       Find it in the Apify console under Settings -> Integrations.
    2. Pick an actor from the Apify Store for the job you want (a Meta/Google
       ad library scraper, a Trustpilot/G2/Reddit review scraper, a
       keyword/SERP tool, ...). Note its actor ID -- shown in the console URL
       or as "username/actor-name" under the actor's title.
    3. Build that actor's input as JSON, either inline or as a file. Each
       actor defines its own input schema (see its README / Input tab in the
       Apify console) -- this script does not know or care what shape it is,
       it just passes your JSON straight through.

Usage:
    python scripts/apify_pipeline.py --actor apify/web-scraper \\
        --input-file scripts/example_input.json \\
        --out scripts/last_run.json

    python scripts/apify_pipeline.py --actor username/actor-name \\
        --input-json '{"startUrls": [{"url": "https://example.com"}]}' \\
        --out scripts/last_run.json
"""
import argparse
import json
import sys
import time
from pathlib import Path

import environ
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
API_ROOT = "https://api.apify.com/v2"

# How often to poll a running actor, and how long to wait before giving up.
POLL_INTERVAL_SECS = 5
DEFAULT_MAX_WAIT_SECS = 600

TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


def _load_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    env = environ.Env()
    environ.Env.read_env(BASE_DIR / ".env")
    token = env("APIFY_API_TOKEN", default="")
    if not token:
        sys.exit(
            "No Apify API token found. Add APIFY_API_TOKEN=... to .env "
            "(Apify console -> Settings -> Integrations), or pass --token."
        )
    return token


def _actor_path(actor: str) -> str:
    """Apify's REST API wants 'username~actor-name' in the URL path; the
    console shows it as 'username/actor-name'. Accept either."""
    return actor.replace("/", "~")


def run_actor(actor: str, run_input: dict, token: str, max_wait_secs: int = DEFAULT_MAX_WAIT_SECS) -> list[dict]:
    """Start an actor run, poll until it finishes, and return its dataset
    items. Raises RuntimeError if the run fails, aborts, times out, or does
    not finish within max_wait_secs."""
    headers = {"Authorization": f"Bearer {token}"}
    actor_path = _actor_path(actor)

    with httpx.Client(timeout=30) as client:
        start = client.post(f"{API_ROOT}/acts/{actor_path}/runs", headers=headers, json=run_input)
        start.raise_for_status()
        run = start.json()["data"]
        run_id = run["id"]
        print(f"Started run {run_id} for actor '{actor}'...")

        waited = 0
        while run["status"] not in TERMINAL_STATUSES:
            if waited >= max_wait_secs:
                raise RuntimeError(
                    f"Run {run_id} did not finish within {max_wait_secs}s "
                    f"(last status: {run['status']}). Check it in the Apify console."
                )
            time.sleep(POLL_INTERVAL_SECS)
            waited += POLL_INTERVAL_SECS
            status_resp = client.get(f"{API_ROOT}/actor-runs/{run_id}", headers=headers)
            status_resp.raise_for_status()
            run = status_resp.json()["data"]
            print(f"  ...status: {run['status']} ({waited}s elapsed)")

        if run["status"] != "SUCCEEDED":
            raise RuntimeError(
                f"Run {run_id} ended with status {run['status']}. "
                f"Check it in the Apify console for details."
            )

        dataset_id = run["defaultDatasetId"]
        items_resp = client.get(f"{API_ROOT}/datasets/{dataset_id}/items", headers=headers)
        items_resp.raise_for_status()
        return items_resp.json()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--actor", required=True, help="Actor ID, e.g. 'apify/web-scraper' or 'username/actor-name'")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input-file", help="Path to a JSON file with the actor's run input")
    input_group.add_argument("--input-json", help="The actor's run input as an inline JSON string")
    parser.add_argument("--out", required=True, help="Where to save the resulting dataset as JSON")
    parser.add_argument("--token", help="Apify API token (defaults to APIFY_API_TOKEN in .env)")
    parser.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT_SECS, help="Max seconds to wait for the run to finish")
    args = parser.parse_args()

    if args.input_file:
        run_input = json.loads(Path(args.input_file).read_text())
    else:
        run_input = json.loads(args.input_json)

    token = _load_token(args.token)

    try:
        items = run_actor(args.actor, run_input, token, max_wait_secs=args.max_wait)
    except (httpx.HTTPStatusError, RuntimeError) as exc:
        sys.exit(f"Apify run failed: {exc}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2))
    print(f"Saved {len(items)} item(s) to {out_path}")


if __name__ == "__main__":
    main()
