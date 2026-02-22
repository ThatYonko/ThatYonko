import urllib.request
import os
import re
import base64
from bs4 import BeautifulSoup

BADGE_URL = "https://tryhackme.com/api/v2/badges/public-profile?userPublicId=2807022"
OUTPUT_FILE = "assets/thm-stats.svg"

def fetch_base64_image(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            img_data = r.read()
            b64 = base64.b64encode(img_data).decode('utf-8')
            mime = "image/svg+xml" if url.endswith(".svg") else "image/png"
            return f"data:{mime};base64,{b64}"
    except:
        return ""

def update_thm():
    req = urllib.request.Request(BADGE_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        soup = BeautifulSoup(response.read().decode(), 'html.parser')

    name = soup.find(class_="user_name").get_text(strip=True)
    rank_title = soup.find(class_="rank-title").get_text(strip=True)
    
    details = soup.find_all(class_="details-text")
    trophies = details[0].get_text(strip=True)
    streak   = details[1].get_text(strip=True)
    awards   = details[2].get_text(strip=True)
    rooms    = details[3].get_text(strip=True)

    style_content = soup.find('style').string
    avatar_url = re.search(r'url\((https://tryhackme-images.*?)\)', style_content).group(1)
    
    b64_avatar = fetch_base64_image(avatar_url)
    b64_bg = fetch_base64_image("https://tryhackme.com/img/thm_public_badge_bg.svg")

    svg = f'''<svg width="327" height="84" viewBox="0 0 327 84" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="avatarClip"><circle cx="40" cy="42" r="30"/></clipPath>
    <linearGradient id="avatarBorder" x1="10" y1="72" x2="70" y2="12" gradientUnits="userSpaceOnUse">
      <stop stop-color="#a3ea2a"/><stop offset="1" stop-color="#2e4463"/>
    </linearGradient>
  </defs>

  <image href="{b64_bg}" width="327" height="84" preserveAspectRatio="xMidYMid slice"/>
  
  <circle cx="40" cy="42" r="32" fill="url(#avatarBorder)"/>
  <circle cx="40" cy="42" r="30" fill="#121212"/>

  <image href="{b64_avatar}" x="10" y="12" width="60" height="60" preserveAspectRatio="xMidYMid slice" clip-path="url(#avatarClip)"/>
  <text x="82" y="28" font-family="Ubuntu, Arial, sans-serif" font-size="14" font-weight="500" fill="#f9f9fb">{name}</text>
  <text x="150" y="28" font-family="Ubuntu, Arial, sans-serif" font-size="12" font-weight="500" fill="#ffffff">{rank_title}</text>

  <g transform="translate(82, 54)">
    <text font-size="11" fill="#9ca4b4">🏆</text> <text x="16" font-family="Ubuntu" font-size="11" fill="white">{trophies}</text>
    <text x="44" font-size="11" fill="#a3ea2a">🔥</text> <text x="60" font-family="Ubuntu" font-size="11" fill="white">{streak}</text>
    <text x="108" font-size="11" fill="#d752ff">🏅</text> <text x="124" font-family="Ubuntu" font-size="11" fill="white">{awards}</text>
    <text x="146" font-size="11" fill="#719cf9">🚪</text> <text x="162" font-family="Ubuntu" font-size="11" fill="white">{rooms}</text>
  </g>

  <text x="82" y="74" font-family="Ubuntu" font-size="11" fill="#f9f9fb" opacity="0.6">tryhackme.com</text>
</svg>'''

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    update_thm()
