"""Deploy polylang-translate with the Cloudflare API token in ~/.config/cloudflare/token. Usage: python3 deploy.py
Keeps the GOOGLE_KEY secret already set in Cloudflare (keep_bindings), and adds the PER_IP rate limit."""
import json, os, pathlib, urllib.request, uuid

HERE = pathlib.Path(__file__).parent
TOKEN = open(os.path.expanduser("~/.config/cloudflare/token")).read().strip()
API = "https://api.cloudflare.com/client/v4"


def call(method, path, data=None, content_type="application/json"):
    req = urllib.request.Request(API + path, data=data, method=method, headers={"Authorization": "Bearer " + TOKEN, "Content-Type": content_type})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


account = call("GET", "/accounts")["result"][0]["id"]
metadata = {"main_module": "worker.js", "compatibility_date": "2025-01-01", "keep_bindings": ["secret_text"],
            "bindings": [{"type": "ratelimit", "name": "PER_IP", "namespace_id": "1007", "simple": {"limit": 60, "period": 60}}]}
b = uuid.uuid4().hex
parts = [("metadata", "application/json", json.dumps(metadata)), ("worker.js", "application/javascript+module", (HERE / "worker.js").read_text())]
body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{n}"; filename="{n}"\r\nContent-Type: {t}\r\n\r\n'.encode() + c.encode() + b"\r\n"
                for n, t, c in parts) + f"--{b}--\r\n".encode()
r = call("PUT", f"/accounts/{account}/workers/scripts/polylang-translate", body, f"multipart/form-data; boundary={b}")
print("upload:", r.get("success"), r.get("errors") or "")
s = call("GET", f"/accounts/{account}/workers/scripts/polylang-translate/settings")["result"]
print("bindings:", [(x["type"], x["name"]) for x in s["bindings"]])
