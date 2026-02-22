#!/usr/bin/env python3
"""
HTB Dynamic SVG Card Generator — Base64 Image Embedding & Auto-Centering
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time
import base64
from datetime import datetime, timezone

STATE_FILE = "assets/htb_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

HTB_USER_ID = os.environ.get("HTB_USER_ID", "2013859")
HTB_TOKEN   = os.environ.get("HTB_TOKEN", "")
HTB_AVATAR_URL = os.environ.get(
    "HTB_AVATAR_URL",
    "https://account.hackthebox.com/storage/users/d60954c2-1ab5-4a68-8148-8aa0f9dd8c78-avatar.png",
)

OUTPUT_FILE = "assets/htb-stats.svg"
BASE_V4     = "https://labs.hackthebox.com/api/v4"
BASE_V5     = "https://labs.hackthebox.com/api/v5"

FIELD_SPEC = {
    "name":              (True,  "Profile name"),
    "rank":              (True,  "HTB rank"),
    "user_owns":         (False, "Machine user owns"),
    "root_owns":         (False, "Machine root owns"),
    "challenges_solved": (False, "Challenges solved"),
    "rank_pos":          (True,  "Global ranking position"),
    "season_rank":       (False, "Season rank"),
    "season_league":     (False, "Season league"),
}

def get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print(f"  [✓] {url.split('hackthebox.com')[-1]}")
            return data
    except urllib.error.HTTPError as e:
        print(f"  [✗] {url.split('hackthebox.com')[-1]} → HTTP {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"  [✗] {url.split('hackthebox.com')[-1]} → {e}")
        return None

def fetch_base64_image(url):
    """Downloads an image and converts it to a base64 string to bypass GitHub Camo."""
    if not url: return ""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            img_data = r.read()
            b64 = base64.b64encode(img_data).decode('utf-8')
            mime = "image/svg+xml" if url.endswith(".svg") else "image/png"
            return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"  [✗] Failed to fetch base64 image: {url} → {e}")
        return ""

def fetch_all(user_id, token):
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    print("\n[*] Fetching endpoints...")
    return {
        "basic":      get(f"{BASE_V4}/user/profile/basic/{user_id}", h),
        "machines":   get(f"{BASE_V4}/user/profile/progress/machines/{user_id}", h),
        "challenges": get(f"{BASE_V4}/user/profile/progress/challenges/{user_id}", h),
        "season":     get(f"{BASE_V4}/season/user/{user_id}/ranks", h),
    }

def parse_stats(raw):
    p = (raw.get("basic") or {}).get("profile", {})
    m_profile    = (raw.get("machines") or {}).get("profile", {})
    user_owns    = m_profile.get("machine_owns", {}).get("solved")
    root_owns    = p.get("system_owns")

    ch_owns      = (raw.get("challenges") or {}).get("profile", {}).get("challenge_owns", {})
    ch_solved    = ch_owns.get("solved")

    sea_data      = (raw.get("season") or {}).get("data", [])
    sea           = sea_data[0] if isinstance(sea_data, list) and sea_data else {}

    return {
        "name":              p.get("name"),
        "rank":              p.get("rank"),
        "user_owns":         user_owns,
        "root_owns":         root_owns,
        "challenges_solved": ch_solved,
        "rank_pos":          p.get("ranking"),
        "season_rank":       sea.get("rank"),
        "season_league":     sea.get("league"),
        "updated":           datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

def validate_stats(stats):
    warnings, errors = [], []
    print("\n[*] Validating fields...")
    ok = True
    for field, (critical, label) in FIELD_SPEC.items():
        value   = stats.get(field)
        missing = value is None
        symbol  = "✓" if not missing else ("✗" if critical else "⚠")
        display = repr(value) if not missing else "NOT FOUND"
        print(f"  [{symbol}] {label:<30} = {display}")
        if missing:
            msg = f"{label} ({field!r}) not found in API response"
            if critical:
                errors.append(msg)
                ok = False
            else:
                warnings.append(msg)
    return ok, warnings, errors

def rank_color(rank):
    return {
        "Noob":          "#9E9E9E",
        "Script Kiddie": "#B04A2F",
        "Hacker":        "#FF7A45",
        "Pro Hacker":    "#FF9800",
        "Elite Hacker":  "#FF5C3A",
        "Guru":          "#D97706",
    }.get(rank or "", "#FF7A45")

def safe(value, fallback="N/A"):
    return value if value is not None else fallback

def generate_svg(s):
    rc         = rank_color(s["rank"])
    ch_label   = f'{safe(s["challenges_solved"],0)}'
    
    # 1. Fetch images as Base64 to bypass GitHub security
    print("\n[*] Encoding images to base64...")
    b64_avatar = fetch_base64_image(HTB_AVATAR_URL)
    b64_logo = fetch_base64_image("https://www.hackthebox.com/images/logo-htb.svg")
    
    b64_season = ""
    if s.get("season_league"):
        league_sanitized = str(s["season_league"]).replace(" ", "-").lower()
        season_icon_url = f"https://app.hackthebox.com/images/competitive/tier-icons-rewards/tier-{league_sanitized}.svg"
        b64_season = fetch_base64_image(season_icon_url)

    bg_fill = "#000000"
    panel_fill = "#0A0A0A"
    stroke_dark = "#2A0F0F"
    muted = "#C48A6A"
    small = "#4A1B1D"
    gold = "#FFD700"
    red = "#AA0A0A"

    sword_glow_layer = f'<text x="80" y="38" font-size="14" fill="{gold}" filter="url(#edgeGlow)">⚔️</text>' if s.get("league_entered") else ''

    ranked_up_badge = ""
    if s.get("league_entered"):
        ranked_up_badge = f'''
  <g>
    <rect x="58" y="167" width="76" height="22" rx="4" fill="{gold}" fill-opacity="0.1" stroke="{gold}" stroke-width="1"/>
    <text x="96" y="182" text-anchor="middle" font-size="9" fill="{gold}" font-family="monospace" font-weight="bold">RANKED UP!</text>
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </g>'''

    return f'''<svg width="480" height="240" viewBox="0 0 480 240" fill="none" xmlns="http://www.w3.org/2000/svg">

  <rect width="480" height="240" rx="14" fill="{bg_fill}"/>
  <rect width="480" height="240" rx="14" stroke="{stroke_dark}" stroke-width="1.5"/>
  <rect width="4" height="240" rx="2" fill="{rc}"/>

  <defs>
    <clipPath id="avatarClip"><circle cx="48" cy="28" r="18"/></clipPath>
    
    <filter id="edgeGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feMorphology in="SourceGraphic" operator="dilate" radius="1.2" result="expanded"/>
      <feGaussianBlur in="expanded" stdDeviation="1.5" result="blur"/>
      <feComponentTransfer in="blur">
        <feFuncA type="linear" slope="0">
          <animate attributeName="slope" values="0; 4; 0" dur="1.8s" repeatCount="indefinite"/>
        </feFuncA>
      </feComponentTransfer>
    </filter>
  </defs>
  <image href="{b64_logo}" x="380" y="12" width="80" height="25" opacity="0.8"/>
  <image href="{b64_avatar}" x="30" y="10" width="36" height="36" clip-path="url(#avatarClip)"/>

  <text x="80" y="23" font-size="15" font-weight="bold" fill="white" font-family="'Segoe UI', Arial, sans-serif">{safe(s["name"])}</text>
  
  {sword_glow_layer}
  <text x="80" y="38" font-size="14" fill="{rc}">⚔️</text>
  <text x="100" y="38" font-size="11" fill="{rc}" font-family="monospace">{safe(s["rank"])}</text>
  
  <text x="460" y="18" text-anchor="end" font-size="9" fill="{small}" font-family="monospace">{s["updated"]}</text>

  <line x1="20" y1="52" x2="460" y2="52" stroke="{stroke_dark}" stroke-width="1"/>

  <rect x="97"  y="62" width="82" height="66" rx="8" fill="{panel_fill}" stroke="{stroke_dark}" stroke-width="1"/>
  <text x="138" y="79"  text-anchor="middle" font-size="8"  fill="{muted}" font-family="monospace">USER OWNS</text>
  <text x="138" y="103" text-anchor="middle" font-size="21" fill="{red}" font-family="monospace" font-weight="bold">{safe(s["user_owns"],0)}</text>
  <text x="138" y="118" text-anchor="middle" font-size="7"  fill="{small}" font-family="monospace">flags</text>

  <rect x="199" y="62" width="82" height="66" rx="8" fill="{panel_fill}" stroke="{stroke_dark}" stroke-width="1"/>
  <text x="240" y="79"  text-anchor="middle" font-size="8"  fill="{muted}" font-family="monospace">ROOT OWNS</text>
  <text x="240" y="103" text-anchor="middle" font-size="21" fill="{red}" font-family="monospace" font-weight="bold">{safe(s["root_owns"],0)}</text>
  <text x="240" y="118" text-anchor="middle" font-size="7"  fill="{small}" font-family="monospace">shells</text>

  <rect x="301" y="62" width="82" height="66" rx="8" fill="{panel_fill}" stroke="{stroke_dark}" stroke-width="1"/>
  <text x="342" y="79"  text-anchor="middle" font-size="8"  fill="{muted}" font-family="monospace">CHALLENGES</text>
  <text x="342" y="103" text-anchor="middle" font-size="21" fill="{red}" font-family="monospace" font-weight="bold">{ch_label}</text>
  <text x="342" y="118" text-anchor="middle" font-size="7"  fill="{small}" font-family="monospace">solved</text>

  <line x1="20" y1="140" x2="460" y2="140" stroke="{stroke_dark}" stroke-width="1"/>

  {ranked_up_badge}

  <rect x="148" y="150" width="82" height="58" rx="8" fill="{panel_fill}" stroke="{stroke_dark}" stroke-width="1"/>
  <text x="189" y="165" text-anchor="middle" font-size="8"  fill="{muted}" font-family="monospace">SEASON</text>
  {f'<image href="{b64_season}" x="152" y="170" width="18" height="18"/>' if b64_season else ''}
  <text x="195" y="186" text-anchor="middle" font-size="16" fill="{red}" font-family="monospace" font-weight="bold">#{safe(s["season_rank"])}</text>
  <text x="189" y="200" text-anchor="middle" font-size="7"  fill="{small}" font-family="monospace">{safe(s["season_league"])}</text>

  <rect x="250" y="150" width="82" height="58" rx="8" fill="{panel_fill}" stroke="{stroke_dark}" stroke-width="1.5"/>
  <text x="291" y="165" text-anchor="middle" font-size="8"  fill="{rc}" font-family="monospace">GLOBAL</text>
  <text x="291" y="186" text-anchor="middle" font-size="16" fill="{red}" font-family="monospace" font-weight="bold">#{safe(s["rank_pos"])}</text>
  <text x="291" y="200" text-anchor="middle" font-size="7"  fill="{small}" font-family="monospace">rank</text>

  <line x1="20" y1="220" x2="460" y2="220" stroke="{stroke_dark}" stroke-width="1"/>

</svg>'''


def main():
    print(f"[*] HTB Stats Card Generator — red theme")
    print(f"[*] User ID: {HTB_USER_ID}")

    if not HTB_TOKEN:
        print("[!] HTB_TOKEN not set — using demo fallback stats.")
        sys.exit(1)
        
    raw   = fetch_all(HTB_USER_ID, HTB_TOKEN)
    stats = parse_stats(raw)
    state = load_state()
    
    prev_league = state.get("season_league")
    curr_league = stats.get("season_league")
    now_ts = time.time()

    if prev_league and curr_league and prev_league != curr_league:
        state["league_changed_at"] = now_ts

    changed_at = state.get("league_changed_at", 0)
    stats["league_entered"] = (now_ts - changed_at) < 259200

    state["season_league"] = curr_league
    save_state(state)

    ok, warnings, errors = validate_stats(stats)

    if warnings:
        print(f"\n[!] {len(warnings)} warning(s) — card generates with fallback values:")
        for w in warnings:
            print(f"    ⚠  {w}")

    if errors:
        print(f"\n[✗] {len(errors)} critical error(s) — cannot generate card:")
        for e in errors:
            print(f"    ✗  {e}")
        sys.exit(1)

    print(f"\n[*] Generating SVG card...")
    svg = generate_svg(stats)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[✓] SVG saved → {OUTPUT_FILE}")
    print(f"[✓] Done!")


if __name__ == "__main__":
    main()
