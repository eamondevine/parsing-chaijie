import json
import os
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Toggle this to test with first 10 characters ---
TEST_MODE = False
# ----------------------------------------------------

BASE_URL = "https://dict.variants.moe.edu.tw"
CHAR_URL = BASE_URL + "/dictView.jsp?ID={}"
CSS_URLS = {
    "jjTool.css": BASE_URL + "/jjTool.css",
    "set.css":    BASE_URL + "/set.css",
}

OUTPUT_DIR = "dict_variant_site"
CSS_DIR = os.path.join(OUTPUT_DIR, "css")
IMG_DIR = os.path.join(OUTPUT_DIR, "img")

HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_ARGS = dict(headers=HEADERS, timeout=15, verify=False)

ROW_HEADERS = ["正　　字", "說文釋形", "字樣說明"]


def fetch(session, url):
    try:
        response = session.get(url, **REQUEST_ARGS)
        if response.status_code != 200:
            print(f"  HTTP {response.status_code}: {url}")
            return None
        return response
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return None


def setup_dirs():
    os.makedirs(CSS_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    print(f"Output dirs ready: {OUTPUT_DIR}/")


def download_css(session):
    for filename, url in CSS_URLS.items():
        out_path = os.path.join(CSS_DIR, filename)
        if os.path.exists(out_path):
            print(f"CSS already exists, skipping: {filename}")
            continue
        print(f"Fetching CSS: {url}")
        response = fetch(session, url)
        if not response:
            continue
        content = response.text
        if filename == "set.css":
            content = content.replace(
                "@import './webfont.css';",
                "/* @import './webfont.css'; */"
            )
            print("  Stripped @import webfont.css from set.css")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved: {out_path}")


def download_image(session, src_path):
    """
    Download an image from the site and save it preserving subdirectory structure.
    src_path is like /rbt/shuowen_a1.files/image040.jpg
    Returns the local relative path to use in the HTML, or None on failure.
    """
    # Strip leading slash
    rel_path = src_path.lstrip("/")
    local_path = os.path.join(IMG_DIR, rel_path)

    if os.path.exists(local_path):
        return f"img/{rel_path}"

    url = BASE_URL + src_path
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    response = fetch(session, url)
    if not response:
        print(f"  Could not download image: {url}")
        return None

    with open(local_path, "wb") as f:
        f.write(response.content)

    return f"img/{rel_path}"


def rewrite_images(session, td_html):
    """
    Find all <img src="/rbt/..."> in a td HTML string,
    download them, and rewrite src to local paths.
    base64 images are left untouched.
    """
    soup = BeautifulSoup(td_html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:"):
            continue  # base64, leave as-is
        if src.startswith("/"):
            local_src = download_image(session, src)
            if local_src:
                img["src"] = local_src
    return str(soup)


def extract_rows(soup):
    table = soup.find("table", id="view")
    if not table:
        return None
    rows = {}
    for tr in table.find_all("tr"):
        th = tr.find("th", scope="row")
        td = tr.find("td")
        if th and td:
            key = th.get_text(strip=True)
            if key in ROW_HEADERS:
                rows[key] = str(td)
    return rows


def build_html(char, link_id, rows):
    char_code = rows.get("正　　字", "<td></td>")
    shuowen = rows.get("說文釋形", "<td><p>（無）</p></td>")
    ziyang = rows.get("字樣說明", "<td><p>（無）</p></td>")
    source_url = CHAR_URL.format(link_id)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{char}</title>
<link rel="stylesheet" href="css/jjTool.css">
<link rel="stylesheet" href="css/set.css">
</head>
<body>
<main class="la0">
<div class="fme128">
<div class="view">

<h2 style="padding:1em 0;">{char} <small style="font-size:0.5em; color:#888;">ID={link_id}</small></h2>

<article id="content">
<table id="view" style="width:100%;">
<tbody>
<tr>
  <th scope="row">正　　字</th>
  {char_code}
</tr>
<tr>
  <th scope="row">說文釋形</th>
  {shuowen}
</tr>
<tr>
  <th scope="row">字樣說明</th>
  {ziyang}
</tr>
</tbody>
</table>
</article>

<p style="margin-top:2em; font-size:0.85em; color:#888;">
  來源：<a href="{source_url}">{source_url}</a>
</p>

</div>
</div>
</main>
</body>
</html>"""


def download_characters(session, characters):
    total = len(characters)
    for i, entry in enumerate(characters, 1):
        link_id = entry["linkId"]
        char = entry["officialChar"]
        out_path = os.path.join(OUTPUT_DIR, f"{link_id}.html")

        if os.path.exists(out_path):
            print(f"[{i}/{total}] Already exists, skipping: {link_id}.html ({char})")
            continue

        url = CHAR_URL.format(link_id)
        print(f"[{i}/{total}] Fetching {char} (ID={link_id})")

        response = fetch(session, url)
        if not response:
            print(f"  Skipping {link_id}")
            time.sleep(1)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        rows = extract_rows(soup)
        if not rows:
            print(f"  No table found for {char} (ID={link_id}), skipping")
            time.sleep(1)
            continue

        # Rewrite images in 說文釋形 and 字樣說明
        for key in ["說文釋形", "字樣說明"]:
            if key in rows:
                rows[key] = rewrite_images(session, rows[key])

        html = build_html(char, link_id, rows)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"  Saved: {out_path}")
        time.sleep(1)


def build_index(characters):
    char_map = {entry["officialChar"]: entry["linkId"] for entry in characters}
    char_map_json = json.dumps(char_map, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>異體字字典 正字查詢</title>
<link rel="stylesheet" href="css/jjTool.css">
<link rel="stylesheet" href="css/set.css">
<style>
  body {{ display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; margin:0; background:#f4f0e2; }}
  h1 {{ font-size:2em; margin-bottom:0.5em; color:#bc1928; }}
  .sub {{ color:#888; margin-bottom:2em; font-size:1em; }}
  .search-box {{ display:flex; gap:0.5em; }}
  input#charInput {{ font-size:3em; width:3em; text-align:center; border:2px solid #bc1928; padding:0.2em; font-family:'標楷體2', serif; }}
  button {{ font-size:1.2em; padding:0 1.5em; background:#bc1928; color:#fff; border:0; cursor:pointer; }}
  button:hover {{ background:#5f0c15; }}
  #msg {{ margin-top:1em; color:red; font-size:1em; min-height:1.5em; }}
</style>
</head>
<body>
<h1>異體字字典</h1>
<p class="sub">正字查詢</p>
<div class="search-box">
  <input id="charInput" type="text" maxlength="1" placeholder="字" autofocus>
  <button onclick="lookup()">查詢</button>
</div>
<div id="msg"></div>

<script>
const charMap = {char_map_json};

function lookup() {{
  const ch = document.getElementById('charInput').value.trim();
  const msg = document.getElementById('msg');
  if (!ch) {{
    msg.textContent = '請輸入一個字。';
    return;
  }}
  const id = charMap[ch];
  if (id === undefined) {{
    msg.textContent = '「' + ch + '」不在正字表中。';
    return;
  }}
  msg.textContent = '';
  window.location.href = id + '.html';
}}

document.getElementById('charInput').addEventListener('keydown', function(e) {{
  if (e.key === 'Enter') lookup();
}});
</script>
</body>
</html>"""

    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Index saved: {out_path}")


def main():
    with open("official_characters.json", "r", encoding="utf-8") as f:
        all_characters = json.load(f)

    if TEST_MODE:
        characters = all_characters[:10]
        print(f"TEST MODE: processing first {len(characters)} characters only\n")
    else:
        characters = all_characters
        print(f"Full run: processing {len(characters)} characters\n")

    session = requests.Session()
    print(f"Establishing session with {BASE_URL}...")
    try:
        session.get(BASE_URL, **REQUEST_ARGS)
        print("Session established.\n")
    except requests.RequestException as e:
        print(f"Warning: could not establish session: {e}\n")

    setup_dirs()
    download_css(session)
    print()
    download_characters(session, characters)
    print()
    build_index(all_characters)
    print(f"\nDone!")


if __name__ == "__main__":
    main()
