#!/usr/bin/env python3
"""
Bulk name availability check: GitHub user/organization logins and .com domains.

  python3 check_names.py names.txt              # name.com + GitHub
  python3 check_names.py names.txt --labs       # also namelabs.com
  python3 check_names.py names.txt -o out.csv   # custom results file

names.txt holds one word per line (blank lines and # comments are ignored).

GitHub: needs a token (free, no scopes required). It is read from the
GITHUB_TOKEN environment variable, or from `gh auth token` if the GitHub CLI
is installed. Without a token the script uses REST, which GitHub limits to
60 requests per hour.

Domains are checked directly in the .com registry (Verisign RDAP), with no
middlemen. Python 3.8+ standard library only.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "name-availability-check"}
GH_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


def http(url, data=None, headers=None, tries=5):
    """Return (status, body). Retry on rate limits and network errors."""
    for i in range(tries):
        req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            limited = e.code in (429, 502, 503) or (
                e.code == 403 and b"rate limit" in body.lower())
            if limited and i < tries - 1:
                time.sleep(5 * 2 ** i)
                continue
            return e.code, body
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
    return None, b""


def gh_token():
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True,
                              text=True, check=True).stdout.strip() or None
    except Exception:
        return None


def github_graphql(names, token, batch=50):
    """Up to 50 names per request; repositoryOwner covers both users and organizations."""
    out = {}
    for i in range(0, len(names), batch):
        chunk = names[i:i + batch]
        q = "query{" + " ".join(
            f"a{j}: repositoryOwner(login: {json.dumps(n)}) {{ login }}"
            for j, n in enumerate(chunk)) + "}"
        status, body = http("https://api.github.com/graphql",
                            json.dumps({"query": q}).encode(),
                            {"Authorization": f"bearer {token}",
                             "Content-Type": "application/json"})
        if status != 200:
            out.update({n: f"error {status}" for n in chunk})
            continue
        data = (json.loads(body) or {}).get("data")
        if data is None:
            out.update({n: "error" for n in chunk})
            continue
        for j, n in enumerate(chunk):
            out[n] = "taken" if data.get(f"a{j}") else "free?"
        time.sleep(1)
    return out


def github_rest(names):
    out = {}
    for n in names:
        status, _ = http(f"https://api.github.com/users/{n}")
        out[n] = {200: "taken", 404: "free?"}.get(status, f"error {status}")
        time.sleep(1)
    return out


def check_com(domain):
    status, _ = http(f"https://rdap.verisign.com/com/v1/domain/{domain}",
                     headers={"Accept": "application/rdap+json"})
    return {200: "taken", 404: "free"}.get(status, f"error {status}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--labs", action="store_true", help="also check <name>labs.com")
    ap.add_argument("-o", "--out", default="results.csv")
    a = ap.parse_args()

    seen, names = set(), []
    with open(a.file, encoding="utf-8") as f:
        for line in f:
            n = line.strip().lower()
            if n and not n.startswith("#") and n not in seen:
                seen.add(n)
                names.append(n)
    if not names:
        sys.exit("No names found in the file.")

    valid = [n for n in names if GH_RE.match(n)]
    gh = {n: "invalid" for n in names if n not in valid}
    token = gh_token()
    if token:
        print(f"GitHub: checking {len(valid)} names via GraphQL…", file=sys.stderr)
        gh.update(github_graphql(valid, token))
    else:
        print("GitHub: no token, using REST (limited to 60 requests per hour).", file=sys.stderr)
        gh.update(github_rest(valid))

    rows = []
    for k, n in enumerate(names, 1):
        row = {"name": n, "github": gh[n], "com": check_com(f"{n}.com")}
        if a.labs:
            row["labs_com"] = check_com(f"{n}labs.com")
        rows.append(row)
        print(f"[{k}/{len(names)}] {n}: " + ", ".join(
            f"{key}={v}" for key, v in row.items() if key != "name"), file=sys.stderr)
        time.sleep(0.3)

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    best = [r["name"] for r in rows if r["com"] == "free" and r["github"] == "free?"]
    print(f"\nDone: {a.out}. Free on both .com and GitHub: {len(best)}", file=sys.stderr)
    for n in best:
        print("  " + n, file=sys.stderr)


if __name__ == "__main__":
    main()