# Posting helper for the Composio workbench. Usage (two short cells):
#   import urllib.request; exec(urllib.request.urlopen(RAW + "post.py").read().decode())
#   cid = prepare("R1_FRI13_ssfn_tiffin")      # creates the Reel container, waits until Instagram has processed it
#   publish("R1_FRI13_ssfn_tiffin", cid)       # publishes it and prints the permalink
import json, time, urllib.request
RAW = "https://raw.githubusercontent.com/adharshkumarmoogala-cmd/milk-tracker/instagram-reels/reels/"
CAPS = json.loads(urllib.request.urlopen(RAW + "captions.json").read().decode())

def _d(r):
    d = r.get("data", r) if isinstance(r, dict) else {}
    return d.get("data", d) if isinstance(d, dict) and isinstance(d.get("data"), (dict, list)) and "id" not in d else d

def already_posted(key):
    """Returns the permalink if a Reel with this caption is already on the account."""
    head = CAPS[key]["caption"][:60]
    r, e = run_composio_tool("INSTAGRAM_GET_IG_USER_MEDIA", {"ig_user_id": "me", "limit": 30, "fields": "id,caption,media_product_type,permalink,timestamp"})
    if e: raise RuntimeError("cannot list media: " + str(e))
    items = _d(r); items = items.get("data", items) if isinstance(items, dict) else items
    for m in items or []:
        if m.get("media_product_type") == "REELS" and (m.get("caption") or "").startswith(head): return m.get("permalink")
    return None

def status(cid):
    r, e = run_composio_tool("INSTAGRAM_GET_POST_STATUS", {"creation_id": cid})
    if e: return "ERR " + str(e)[:200]
    d = _d(r); return d.get("status_code") or d.get("status") or str(d)[:200]

def prepare(key, wait=130):
    p = already_posted(key)
    if p: print("ALREADY_POSTED", p); return None
    r, e = run_composio_tool("INSTAGRAM_POST_IG_USER_MEDIA", {"ig_user_id": "me", "media_type": "REELS", "share_to_feed": True,
        "video_url": RAW + key + ".mp4", "caption": CAPS[key]["caption"]})
    if e: raise RuntimeError("container failed: " + str(e))
    cid = _d(r).get("id"); print("CONTAINER", cid)
    t = time.time(); s = ""
    while time.time() - t < wait:
        s = status(cid)
        if s in ("FINISHED", "ERROR", "EXPIRED"): break
        time.sleep(8)
    print("STATUS", s); return cid

def publish(key, cid):
    p = already_posted(key)
    if p: print("ALREADY_POSTED", p); return p
    s = status(cid)
    if s != "FINISHED": print("NOT_READY", s); return None
    r, e = run_composio_tool("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {"ig_user_id": "me", "creation_id": cid, "max_wait_seconds": 60})
    if e: print("PUBLISH_ERROR", str(e)[:300])
    time.sleep(6); p = already_posted(key); print("POSTED", p, _d(r) if r else None); return p
