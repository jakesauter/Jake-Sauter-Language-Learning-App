import base64
import re
import sys

src, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "file"

SITE = "https://jakesauter.github.io/Jake-Sauter-Language-Learning-App/"
DESC = "Polyling: everyday family sentences word by word in Taishanese, Cantonese, English, Mandarin, Spanish, French and German, with audio."

body = open(src, encoding = "utf-8").read()

title = re.search(r"<title>.*?</title>", body).group(0)
body = body.replace(title, "", 1)
body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">', "", 1)

b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

if mode == "site":
    icons = f"""<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:title" content="Polyling">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}og.png">"""
else:
    icons = f"""<link rel="icon" href="data:image/svg+xml;base64,{b64('icons/icon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="data:image/png;base64,{b64('icons/apple-touch-icon.png')}">"""

head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{title}
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#ffffff">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Polyling">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
{icons}
<style>
  :root {{ color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{ margin: 0; font: 14px/1.5 system-ui, -apple-system, sans-serif; }}
  img {{ max-width: 100%; }}
  [hidden] {{ display: none !important; }}
</style>
</head>
<body>
"""

open(out, "w", encoding = "utf-8").write(head + body.lstrip() + "\n</body>\n</html>\n")
print("wrapped", out, mode)
