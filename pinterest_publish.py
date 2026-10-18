#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pinterest_publish.py — cron helper: pin the newest content/*.md not yet in pinterest_posted.txt
# Does NOT use USDC / Base / x402 / DESKCREW_WALLET_KEY — 100% free push via Upload-Post.
import os, re, json, urllib.request, urllib.error, sys

PROJ = r"C:\Users\User\blog-ia-produtividade"
CONTENT = os.path.join(PROJ, "content")
POSTED = os.path.join(PROJ, "pinterest_posted.txt")
KEY_PATH = r"C:\Users\User\OneDrive\Documentos\uploadpost_key.txt"
MCP_URL = "https://mcp.upload-post.com/mcp"
BOARD_ID = "1132514706237060775"
USER_NAME = "produtividade_IA"

def mcp_call(payload, sess=None):
    tok = open(KEY_PATH, encoding="utf-8").read().strip()
    auth = f"Apikey {tok}"
    hdr = {"Authorization": auth, "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if sess:
        hdr["mcp-session-id"] = sess
    data = json.dumps(payload).encode()
    req = urllib.request.Request(MCP_URL, data=data, headers=hdr, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        body = r.read().decode()
        ns = r.headers.get("mcp-session-id") or r.headers.get("Mcp-Session-Id")
        return r.status, ns, body

def init_mcp():
    s, sess, body = mcp_call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "hermes", "version": "1.0"}}})
    mcp_call({"jsonrpc": "2.0", "method": "notifications/initialized"}, sess)
    return sess

def find_boards(sess):
    s, ns, body = mcp_call({"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "get_pinterest_boards", "arguments": {"user": USER_NAME}}}, sess)
    import re as _re
    m = _re.search(r"data: (.+)", body)
    js = json.loads(m.group(1)) if m else {}
    try:
        ct = js["result"]["content"][0]["text"]
        d = json.loads(ct)
        return d.get("boards",[])
    except Exception:
        return []

def parse_frontmatter(p):
    raw = open(p, encoding="utf-8").read()
    fm = {}
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        block = raw[3:end] if end != -1 else ""
        for ln in block.splitlines():
            if ":" in ln:
                k,v = ln.split(":", 1)
                v = v.strip().strip('"').strip("'")
                fm[k.strip()] = v
    return fm

def pick_next():
    cfg = json.load(open(os.path.join(PROJ, "config.json"), encoding="utf-8"))
    site_url = cfg.get("site_url", "https://kauacezarr99-web.github.io/blog-ia-produtividade").rstrip("/")

    # collect content
    md_files = [os.path.join(CONTENT, f) for f in sorted(os.listdir(CONTENT)) if f.endswith(".md") and not f.startswith("_")]
    candidates = []
    for fn in md_files:
        fm = parse_frontmatter(fn)
        slug = fm.get("slug") or os.path.splitext(os.path.basename(fn))[0]
        title = fm.get("title","") or slug.replace("-"," ").title()
        desc = fm.get("description","") or title
        date = fm.get("date","")
        # use mtime as tie-breaker
        mtime = os.path.getmtime(fn)
        candidates.append((date or "", mtime, slug, title, desc, fn))

    # order: newest date/mtime first
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # posted set
    posted = set()
    if os.path.exists(POSTED):
        posted = {ln.strip() for ln in open(POSTED, encoding="utf-8").read().splitlines() if ln.strip()}

    for slug, title in []:
        pass

    next_item = None
    for date, mtime, slug, title, desc, fn in candidates:
        if slug not in posted:
            next_item = (slug, title, desc, site_url + "/" + slug + ".html")
            break

    return next_item, posted, site_url

def do_pin(sess, slug, title, description, link):
    img = "https://picsum.photos/1000/1500"
    import re as _re, time as _time
    s, ns, body = mcp_call({"jsonrpc":"2.0","id":20,"method":"tools/call","params":{"name":"upload_photos","arguments":{
        "user": USER_NAME,
        "platforms": ["pinterest"],
        "photosPathsOrUrls": [img],
        "title": title,
        "description": description + "\n\n" + link,
        "platformOptions": {"pinterestBoardId": BOARD_ID, "pinterestLink": link},
        "asyncUpload": True}}}, sess)
    import json as _J
    m = _re.search(r"data: (.+)", body)
    js = _J.loads(m.group(1)) if m else {}
    ct = ""
    try:
        ct = js.get("result",{}).get("content",[{}])[0].get("text","")
        _J.loads(ct)  # sanity
    except Exception as e:
        print("upload_photos raw:", body[:2000])
        print("err:", e)
        sys.exit(1)
    data = _J.loads(ct)
    if not data.get("success"):
        print("upload_photos failed:", _J.dumps(data, indent=2, ensure_ascii=False)[:4000])
        sys.exit(1)
    rid = data.get("request_id")
    print(f"upload_photos queued: request_id={rid} slug={slug}")
    # poll get_status (camelCase requestId)
    for i in range(18):
        _time.sleep(5)
        s2, ns2, body2 = mcp_call({"jsonrpc":"2.0","id":100+i,"method":"tools/call","params":{"name":"get_status","arguments":{"requestId": rid}}}, sess)
        m2 = _re.search(r"data: (.+)", body2)
        js2 = _J.loads(m2.group(1)) if m2 else {}
        ct2 = js2.get("result",{}).get("content",[{}])[0].get("text","")
        try:
            d2 = _J.loads(ct2)
        except Exception:
            print(f"poll {i}: raw", ct2[:800])
            continue
        stat = d2.get("status")
        print(f"poll {i}: status={stat} completed={d2.get('completed')}/{d2.get('total')}")
        if stat == "completed":
            res = (d2.get("results") or [{}])[0]
            if res.get("success"):
                print(f"SUCCESS: pin {res.get('post_title')} -> {res.get('platform')} board post_id={res.get('platform_post_id')}")
                return True, res
            else:
                print("FAILED:", _J.dumps(res, indent=2, ensure_ascii=False)[:4000])
                sys.exit(1)
        if stat in ("failed","error"):
            print("FAILED terminal:", _J.dumps(d2, indent=2, ensure_ascii=False)[:4000])
            sys.exit(1)
    print("timeout polling get_status")
    sys.exit(1)


def main():
    # Only this cron's board + free Upload-Post. Do NOT touch x402 / DESKCREW_WALLET_KEY.
    sess = init_mcp()
    boards = find_boards(sess)
    print(f"boards on {USER_NAME}:", boards)
    if not any(b.get("id")==BOARD_ID for b in boards):
        print(f"board {BOARD_ID} not found in account; abort. boards were: {boards}")
        sys.exit(1)

    next_item, posted, site_url = pick_next()
    if not next_item:
        print("all articles already posted (pinterest_posted.txt contains every slug). Nothing to do.")
        sys.exit(0)
    slug, title, desc, link = next_item
    print(f"next slug to publish: {slug}")
    print(f"  title: {title}")
    print(f"  desc: {desc[:120]}")
    print(f"  link: {link}")
    print(f"  posted contains: {len(posted)} slugs")

    ok, res = do_pin(sess, slug, title, desc, link)
    # append on success
    with open(POSTED, "a", encoding="utf-8") as f:
        f.write(slug + "\n")
    # commit
    import subprocess as sp, os as _os
    sp.run(["git","-C", PROJ, "add", POSTED], capture_output=True)
    # only commit if changed
    r = sp.run(["git","-C", PROJ, "diff","--cached","--quiet"])
    if r.returncode != 0:
        sp.run(["git","-C", PROJ, "commit","-m", f"pinterest: posted {slug}"], capture_output=True)
        sp.run(["git","-C", PROJ, "push","origin","main"], capture_output=True)
        print(f"updated {POSTED} and pushed")

if __name__ == "__main__":
    main()
