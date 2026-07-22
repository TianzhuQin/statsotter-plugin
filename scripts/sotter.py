#!/usr/bin/env python3
"""sotter.py — StatsOtter API client for the Claude Code plugin.

Standard library only. Prints JSON to stdout; exit 0 = ok, 1 = API error
(the error body is still printed), 2 = usage/config error. The API key is
never printed — errors redact it.

Config: .statsotter.json, searched in this order:
  $STATSOTTER_CONFIG (explicit path) → ./.statsotter.json → ~/.statsotter.json
Shape: {"base_url": "https://statsotter.ai", "api_key": "sd_..."}

Usage:
  sotter.py setup KEY [URL] [--global]   write ./.statsotter.json (+ gitignore);
                                         --global writes ~/.statsotter.json instead
  sotter.py me                           who am I / am I a site admin
  sotter.py validate FILE                dry-run a knowledge doc
  sotter.py upload FILE [--target SLUG] [--repo URL] [--force]
  sotter.py cards [--all]                my cards (site admins: --all = everyone's)
  sotter.py card SLUG                    every field of one card (JSON)
  sotter.py edit SLUG (--json FILE | -)  PATCH: send only the fields to change
  sotter.py publish SLUG                 draft → public feed
  sotter.py unpublish SLUG               public feed → draft
  sotter.py delete SLUG                  permanent!
  sotter.py doc SLUG [--save [FILE]] [--version N] [--versions] [--with-signals]
                                         download a knowledge doc; bare --save
                                         writes ./<slug>.md, upload-ready
  sotter.py audit [--all]                docs that are too thin to teach an AI
  sotter.py catalog                      every published card (title/summary/tags)
  sotter.py search QUERY [-k N]          rank published cards for a goal
  sotter.py feedback KIND [--slug S] [--query Q] [--note N]
  sotter.py gaps                         most-wanted methods
  sotter.py lesson --instruction TEXT [--slug S] [--context TEXT]
                                         teach the card-generation AI from an
                                         edit instruction (site admins)
  sotter.py tax get                      the left-rail sidebar tree
  sotter.py tax put (--json FILE | -) [--label TEXT] [--expect-head N|null]
                                         replace the tree (admins)
  sotter.py tax history                  sidebar revision log (admins)
  sotter.py tax restore ID               roll the sidebar back (admins)
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://statsotter.ai"
CONFIG_NAME = ".statsotter.json"

# `--save` with no value means "pick the filename for me" (./<slug>.md); a
# sentinel keeps that distinguishable from `--save ""`.
SAVE_DEFAULT = object()


def die(msg, code=2):
    print(json.dumps({"ok": False, "errors": [msg]}, indent=2))
    sys.exit(code)


def find_config():
    explicit = os.environ.get("STATSOTTER_CONFIG")
    if explicit:
        p = pathlib.Path(explicit)
        if not p.is_file():
            die(f"$STATSOTTER_CONFIG points at {explicit}, which does not exist.")
        return p
    for p in (pathlib.Path.cwd() / CONFIG_NAME, pathlib.Path.home() / CONFIG_NAME):
        if p.is_file():
            return p
    return None


def load_config():
    p = find_config()
    if p is None:
        die(f"No {CONFIG_NAME} found (looked in the current folder and your home "
            "directory). Ask the user for their StatsOtter API key — created on "
            "the website under Settings → API keys — then run: sotter.py setup <key>")
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        die(f"{p} is not valid JSON — re-run: sotter.py setup <key>")
    if not cfg.get("api_key"):
        die(f"{p} has no api_key — re-run: sotter.py setup <key>")
    cfg["base_url"] = (cfg.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    return cfg


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: following one would forward the Authorization header
    (the API key) to whatever host the redirect names."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def request(method, path, body=None, cfg=None):
    cfg = cfg or load_config()
    req = urllib.request.Request(
        cfg["base_url"] + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Bearer " + cfg["api_key"],
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
        method=method,
    )
    try:
        with _OPENER.open(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except ValueError:
                return resp.status, {"ok": False, "errors": [
                    f"HTTP {resp.status} but the response is not JSON — is "
                    f"base_url ({cfg['base_url']}) really a StatsOtter server?"]}
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return e.code, {"ok": False, "errors": [
                f"The server answered with a redirect (HTTP {e.code}), which this "
                f"client refuses to follow with credentials. Check base_url "
                f"({cfg['base_url']}) — e.g. use https:// and the canonical host."]}
        try:
            payload = json.loads(e.read().decode("utf-8", "replace"))
            if not isinstance(payload, dict):
                payload = {"ok": False, "errors": [f"HTTP {e.code}: {payload!r}"]}
        except Exception:
            payload = {"ok": False, "errors": [f"HTTP {e.code} (non-JSON response)"]}
        return e.code, payload
    except urllib.error.URLError as e:
        die(f"Cannot reach {cfg['base_url']} — {getattr(e, 'reason', e)}", 1)


def quality_hint(quality):
    """One human line for a QUALITY block, so the score and the actionable
    warning codes are visible without reading the whole payload. Returns None
    when the response carries no quality block (e.g. an older server)."""
    if not isinstance(quality, dict) or "score" not in quality:
        return None
    codes = [w.get("code") for w in (quality.get("warnings") or [])
             if isinstance(w, dict) and w.get("code")]
    return " · ".join([
        f"score {quality.get('score')}/100",
        f"doc {quality.get('doc_chars')} chars",
        f"AI Notes {quality.get('ai_notes_chars')} chars",
        "warnings: " + (", ".join(codes) if codes else "none"),
    ])


def emit(status, payload):
    payload = dict(payload)
    payload.setdefault("http_status", status)
    hint = quality_hint(payload.get("quality"))
    if hint:
        payload.setdefault("quality_hint", hint)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0 if 200 <= status < 300 else 1)


def quoted(slug):
    import urllib.parse
    return urllib.parse.quote(str(slug), safe="")


def default_doc_path(slug):
    """./<slug>.md for a bare `--save`. The slug comes from the server, but
    sanitise anyway so a hand-typed one can never escape the working folder."""
    safe = "".join(c if (c.isalnum() or c in "-_") else "-" for c in str(slug))
    return pathlib.Path.cwd() / ((safe.strip("-") or "card") + ".md")


def read_file(path):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as e:
        die(f"Cannot read {path}: {e}")


def read_json_arg(value):
    """--json FILE, or '-' for stdin."""
    raw = sys.stdin.read() if value == "-" else read_file(value)
    try:
        return json.loads(raw)
    except Exception as e:
        die(f"Invalid JSON in {'stdin' if value == '-' else value}: {e}")


def _git_root(start):
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return None


def cmd_setup(args):
    key = args.key.strip()
    if not key.startswith("sd_"):
        die("That does not look like a StatsOtter API key (they start with sd_). "
            "Create one on the website: Settings → API keys → + New key.")
    base = (args.url or DEFAULT_BASE_URL).strip().rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = "https://" + base

    explicit = os.environ.get("STATSOTTER_CONFIG")
    if explicit:
        cfg_path = pathlib.Path(explicit)
    elif getattr(args, "global_config", False):
        cfg_path = pathlib.Path.home() / CONFIG_NAME
    else:
        cfg_path = pathlib.Path.cwd() / CONFIG_NAME
    try:
        cfg_path.write_text(
            json.dumps({"base_url": base, "api_key": key}, indent=2) + "\n",
            encoding="utf-8")
    except OSError as e:
        die(f"Cannot write {cfg_path}: {e}")

    # The key must never be committed: gitignore the config at the enclosing
    # repo's ROOT (a .gitignore next to a config written in a subdirectory
    # would not exist / not match otherwise).
    gitignored = False
    root = _git_root(cfg_path.resolve().parent)
    if root is not None:
        gi = root / ".gitignore"
        try:
            lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
            if CONFIG_NAME not in [ln.strip() for ln in lines]:
                with gi.open("a", encoding="utf-8") as f:
                    if lines and lines[-1].strip():
                        f.write("\n")
                    f.write(CONFIG_NAME + "\n")
            gitignored = True
        except OSError:
            pass

    status, payload = request("GET", "/api/v1/me", cfg={"base_url": base, "api_key": key})
    emit(status, {
        "ok": payload.get("ok", False),
        "config": str(cfg_path),
        "gitignored": gitignored,
        "base_url": base,
        "key_last4": key[-4:],
        "me": payload if payload.get("ok") else None,
        "errors": payload.get("errors", []),
    })


def main():
    ap = argparse.ArgumentParser(prog="sotter.py", add_help=True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("setup", help="store and verify the API key")
    p.add_argument("key")
    p.add_argument("url", nargs="?")
    p.add_argument("--global", dest="global_config", action="store_true",
                   help="write ~/.statsotter.json (all projects) instead of ./")

    sub.add_parser("me", help="who am I / am I a site admin")

    p = sub.add_parser("validate", help="dry-run a knowledge doc (never writes)")
    p.add_argument("file")

    p = sub.add_parser("upload", help="create a card from a doc, or overwrite one")
    p.add_argument("file")
    p.add_argument("--target", default="",
                   help="slug of the card to overwrite (omit to create a new one)")
    p.add_argument("--repo", default="")
    p.add_argument("--force", action="store_true",
                   help="import anyway past a 409 duplicate warning")

    p = sub.add_parser("cards", help="list my cards")
    p.add_argument("--all", action="store_true",
                   help="every member's cards (site admins)")

    p = sub.add_parser("card", help="every field of one card")
    p.add_argument("slug")

    p = sub.add_parser("edit", help="PATCH one card's fields")
    p.add_argument("slug")
    p.add_argument("--json", dest="json_src", required=True,
                   help="path to a JSON file with the fields to change, or - for stdin")

    for name, blurb in (("publish", "draft → public feed"),
                        ("unpublish", "public feed → draft"),
                        ("delete", "permanent removal")):
        p = sub.add_parser(name, help=blurb)
        p.add_argument("slug")

    p = sub.add_parser("doc", help="download a card's knowledge document")
    p.add_argument("slug")
    p.add_argument("--save", nargs="?", const=SAVE_DEFAULT, default=None,
                   metavar="FILE",
                   help="write the markdown to FILE; bare --save writes ./<slug>.md")
    p.add_argument("--version", type=int, default=None, metavar="N",
                   help="fetch stored version N instead of the live render")
    p.add_argument("--versions", action="store_true",
                   help="list the version history only, without the markdown "
                        "(nothing is written, so --save is ignored)")
    p.add_argument("--with-signals", dest="with_signals", action="store_true",
                   help="keep the read-only '## Community signals' block "
                        "(reading only — such a file is NOT upload-ready)")

    p = sub.add_parser("audit", help="my docs that are too thin to teach an AI")
    p.add_argument("--all", action="store_true",
                   help="every member's thin docs (site admins)")

    sub.add_parser("catalog", help="every published card (title/summary/tags)")

    p = sub.add_parser("search", help="rank published cards for a goal")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=8)

    p = sub.add_parser("feedback", help="log how a workflow went")
    p.add_argument("kind", choices=["picked", "ran_ok", "ran_fail", "gap"])
    p.add_argument("--slug", default="")
    p.add_argument("--query", default="")
    p.add_argument("--note", default="")

    sub.add_parser("gaps", help="most-wanted methods")

    p = sub.add_parser("lesson", help="teach the card-generation AI (site admins)")
    p.add_argument("--instruction", required=True,
                   help="the user's edit request, in their own words")
    p.add_argument("--slug", default="")
    p.add_argument("--context", default="",
                   help="one line on what changed as a result")

    p = sub.add_parser("tax", help="the site's left sidebar (site admins)")
    tax = p.add_subparsers(dest="tax_cmd", required=True)
    tax.add_parser("get", help="the sidebar tree + can_edit + head revision id")
    def head_arg(value):
        if str(value).strip().lower() in ("null", "none", ""):
            return "null"
        try:
            return int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("expected a revision id or 'null'")

    tp = tax.add_parser("put", help="replace the sidebar tree")
    tp.add_argument("--json", dest="json_src", required=True,
                    help="path to a JSON file with {fields:[...]}, or - for stdin")
    tp.add_argument("--label", default="")
    tp.add_argument("--expect-head", dest="expect_head", type=head_arg, default=None,
                    help="head from `tax get`; pass null on a site with no revisions yet")
    tax.add_parser("history", help="sidebar revision log")
    tr = tax.add_parser("restore", help="roll the sidebar back to a revision")
    tr.add_argument("id", type=int)

    args = ap.parse_args()

    if args.cmd == "setup":
        return cmd_setup(args)
    if args.cmd == "me":
        return emit(*request("GET", "/api/v1/me"))
    if args.cmd == "validate":
        return emit(*request("POST", "/api/v1/validate", {"content": read_file(args.file)}))
    if args.cmd == "upload":
        body = {"content": read_file(args.file)}
        if args.target:
            body["target_slug"] = args.target
        if args.repo:
            body["repo"] = args.repo
        if args.force:
            body["force"] = True
        return emit(*request("POST", "/api/v1/imports", body))
    if args.cmd == "cards":
        return emit(*request("GET", "/api/v1/cards" + ("?all=1" if args.all else "")))
    if args.cmd == "card":
        return emit(*request("GET", f"/api/v1/cards/{quoted(args.slug)}"))
    if args.cmd == "edit":
        patch = read_json_arg(args.json_src)
        if not isinstance(patch, dict) or not patch:
            die("edit expects a JSON object with the fields to change, e.g. "
                '{"summary": "…"} — start from `card <slug>` output.')
        return emit(*request("PATCH", f"/api/v1/cards/{quoted(args.slug)}", patch))
    if args.cmd in ("publish", "unpublish"):
        return emit(*request("POST", f"/api/v1/cards/{quoted(args.slug)}/publish",
                             {"publish": args.cmd == "publish"}))
    if args.cmd == "delete":
        return emit(*request("DELETE", f"/api/v1/cards/{quoted(args.slug)}"))
    if args.cmd == "doc":
        query = []
        if args.version is not None:
            if args.version < 1:
                die("--version takes a version number (1 or higher) from "
                    f"`doc {args.slug} --versions`.")
            query.append(f"version={args.version}")
        # raw=1 asks the server for the doc alone; without it the response
        # carries an appended read-only community block, so a saved file
        # would not validate. Opt back in only with --with-signals.
        if not args.with_signals:
            query.append("raw=1")
        status, payload = request(
            "GET", f"/api/v1/cards/{quoted(args.slug)}/doc"
                   + ("?" + "&".join(query) if query else ""))
        if args.versions and payload.get("ok"):
            # History only — drop the body so the version table stays readable.
            payload = {k: v for k, v in payload.items() if k != "markdown"}
            return emit(status, payload)
        if args.save is not None and payload.get("ok"):
            markdown = payload.get("markdown", "")
            # Fallback for a server that ignores raw=1: the "## Community
            # signals" block is read-only and the knowledge-doc grammar
            # rejects it, so a saved file must never carry it.
            if not args.with_signals:
                cut = markdown.find("\n## Community signals")
                if cut != -1:
                    markdown = markdown[:cut].rstrip() + "\n"
            dest = (default_doc_path(payload.get("slug") or args.slug)
                    if args.save is SAVE_DEFAULT else pathlib.Path(args.save))
            try:
                dest.write_text(markdown, encoding="utf-8")
            except OSError as e:
                die(f"Cannot write {dest}: {e}")
            # Report what the FILE is, not what was asked for: a stored
            # version never carries signals, so `--version N --with-signals`
            # still lands an upload-ready file.
            payload = dict(payload, saved_to=str(dest), saved_chars=len(markdown),
                           upload_ready="\n## Community signals" not in markdown,
                           markdown=f"(saved to {dest})")
        return emit(status, payload)
    if args.cmd == "audit":
        return emit(*request("GET", "/api/v1/cards?thin=1"
                             + ("&all=1" if args.all else "")))
    if args.cmd == "catalog":
        return emit(*request("GET", "/api/v1/catalog"))
    if args.cmd == "search":
        return emit(*request("POST", "/api/v1/search", {"query": args.query, "k": args.k}))
    if args.cmd == "feedback":
        body = {"kind": args.kind, "source": "plugin"}
        if args.slug:
            body["slug"] = args.slug
        if args.query:
            body["query"] = args.query
        if args.note:
            body["note"] = args.note
        return emit(*request("POST", "/api/v1/feedback", body))
    if args.cmd == "gaps":
        return emit(*request("GET", "/api/v1/gaps"))
    if args.cmd == "lesson":
        body = {"instruction": args.instruction}
        if args.slug:
            body["slug"] = args.slug
        if args.context:
            body["context"] = args.context
        return emit(*request("POST", "/api/v1/lessons", body))
    if args.cmd == "tax":
        if args.tax_cmd == "get":
            return emit(*request("GET", "/api/v1/taxonomy"))
        if args.tax_cmd == "put":
            body = read_json_arg(args.json_src)
            if not isinstance(body, dict) or "fields" not in body:
                die("tax put expects JSON shaped {\"fields\": [...]} — "
                    "start from `tax get` output.")
            if args.label:
                body["label"] = args.label
            if args.expect_head is not None:
                body["expect_head"] = None if args.expect_head == "null" else args.expect_head
            return emit(*request("PUT", "/api/v1/taxonomy", body))
        if args.tax_cmd == "history":
            return emit(*request("GET", "/api/v1/taxonomy/history"))
        if args.tax_cmd == "restore":
            return emit(*request("POST", "/api/v1/taxonomy/restore", {"id": args.id}))


if __name__ == "__main__":
    main()
