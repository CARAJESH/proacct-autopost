"""Publish the next carousel from posts.json to Instagram.

Runs once per day (GitHub Actions calls it). Uses Instagram's official API
(Instagram API with Instagram Login, graph.instagram.com).

Environment variables
  IG_ACCESS_TOKEN   required  long-lived Instagram user access token
  IG_USER_ID        optional  your Instagram professional account ID (looked up if missing)
  IMAGE_BASE_URL    optional  public URL of the images/ folder
                              (default: raw.githubusercontent.com URL of this repo)
  DRY_RUN           optional  "1" = show what would be posted, post nothing
  GH_PAT            optional  GitHub token allowed to update secrets, so a refreshed
                              access token can be saved back automatically
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://graph.instagram.com/v26.0"
ROOT = Path(__file__).parent
STATE_FILE = ROOT / "state.json"
POSTS_FILE = ROOT / "posts.json"


def log(msg):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC] {msg}", flush=True)


def api(method, path, token, **params):
    params["access_token"] = token
    url = f"{API}/{path.lstrip('/')}"
    r = requests.request(method, url, params=params if method == "GET" else None,
                         data=params if method != "GET" else None, timeout=60)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text}
    if r.status_code >= 400 or "error" in body:
        err = body.get("error", body)
        raise RuntimeError(f"Instagram API error on {method} {path}: {err}")
    return body


def wait_until_ready(container_id, token, label):
    # Meta recommends checking about once a minute for up to 5 minutes.
    for attempt in range(30):
        status = api("GET", container_id, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{label} container {container_id} failed with status {status}")
        time.sleep(10)
    raise RuntimeError(f"{label} container {container_id} was not ready after 5 minutes")


def image_base_url():
    base = os.environ.get("IMAGE_BASE_URL")
    if base:
        return base.rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        sys.exit("Set IMAGE_BASE_URL (or run inside GitHub Actions).")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/images"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"next": 1, "history": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def refresh_token(token):
    """Extend the long-lived token's 60-day life. Never fatal."""
    try:
        r = requests.get("https://graph.instagram.com/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30)
        data = r.json()
        new = data.get("access_token")
        if not new:
            log(f"Token refresh skipped: {data.get('error', data)}")
            return
        days = int(data.get("expires_in", 0)) // 86400
        log(f"Access token refreshed, valid for about {days} more days.")
        if new != token:
            if os.environ.get("GH_PAT") and os.environ.get("GITHUB_REPOSITORY"):
                subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", new,
                                "--repo", os.environ["GITHUB_REPOSITORY"]],
                               check=True, env={**os.environ, "GH_TOKEN": os.environ["GH_PAT"]})
                log("Saved the new token to the IG_ACCESS_TOKEN secret.")
            else:
                log("WARNING: Instagram issued a new token string. Add GH_PAT so it can be "
                    "saved automatically, or replace the IG_ACCESS_TOKEN secret before it expires.")
    except Exception as e:  # noqa: BLE001
        log(f"Token refresh failed (posting continues): {e}")


def main():
    dry = os.environ.get("DRY_RUN") == "1"
    posts = {p["id"]: p for p in json.loads(POSTS_FILE.read_text(encoding="utf-8"))}
    state = load_state()
    post = posts.get(state["next"])
    if post is None:
        sys.exit(f"All {len(posts)} posts have been published. Add more posts to posts.json, "
                 f"run render.py, and push. (state.json next = {state['next']})")

    folder = ROOT / "images" / f"day{post['id']:02d}"
    slides = sorted(folder.glob("slide*.jpg"), key=lambda p: int(p.stem[5:]))
    if not 2 <= len(slides) <= 20:
        sys.exit(f"{folder} must hold 2 to 20 slides, found {len(slides)}. Run render.py.")
    base = image_base_url()
    urls = [f"{base}/{folder.name}/{s.name}" for s in slides]
    caption = f"{post['caption']}\n\n{post['hashtags']}"

    log(f"Post {post['id']}: {post['topic']} ({len(urls)} slides)")
    if dry:
        log("DRY RUN, nothing will be published.")
        for u in urls:
            log(f"  image: {u}")
        log("  caption:\n" + caption)
        return

    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set.")
    user_id = os.environ.get("IG_USER_ID") or api("GET", "me", token, fields="user_id,username")["user_id"]

    # 1. One container per slide
    children = []
    for i, u in enumerate(urls, 1):
        cid = api("POST", f"{user_id}/media", token, image_url=u, is_carousel_item="true")["id"]
        wait_until_ready(cid, token, f"Slide {i}")
        children.append(cid)
        log(f"Slide {i} uploaded")

    # 2. Carousel container with caption
    carousel = api("POST", f"{user_id}/media", token, media_type="CAROUSEL",
                   children=",".join(children), caption=caption)["id"]
    wait_until_ready(carousel, token, "Carousel")

    # 3. Publish
    media_id = api("POST", f"{user_id}/media_publish", token, creation_id=carousel)["id"]
    link = api("GET", media_id, token, fields="permalink").get("permalink", "")
    log(f"Published: {link or media_id}")

    state["history"].append({"post": post["id"], "topic": post["topic"], "media_id": media_id,
                             "permalink": link, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    state["next"] = post["id"] + 1
    save_state(state)
    refresh_token(token)


if __name__ == "__main__":
    main()
