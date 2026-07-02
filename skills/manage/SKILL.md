---
name: manage
description: Manage StatsOtter (statsotter.ai) through plain conversation — there are no slash commands. Use whenever the user mentions StatsOtter (in any language, e.g. 卡片/左边栏/发布) or wants to connect their StatsOtter account / API key; list their cards or drafts; turn a repo or tutorial into a card; view, edit, rename, retag or rewrite a card (any field, steps, figures, AI notes); publish or unpublish a card; delete a card; view or edit the site's left sidebar (fields and sub-categories); or inspect/restore sidebar history.
---

# StatsOtter — manage cards & the left sidebar from Claude Code

StatsOtter (https://statsotter.ai) is a community feed of statistics / causal
inference workflow **cards**. Everything a user can do on the website, you can
do here through natural language — the user should never need the web UI or
memorize commands.

The three objects you operate on:

- **Card** — one workflow page: title, summary, description, results, inputs,
  input example, figures, tags, ordered steps (stage + name + note + code +
  formula), plus a card-invisible `ai_notes` section. Cards are `draft`
  (private) or published (public feed).
- **Knowledge doc** — a strictly-templated markdown rendering of a card
  (grammar in [references/template.md](references/template.md)). Every edit
  records a new immutable version server-side.
- **Left sidebar** (a.k.a. taxonomy / left rail) — the site's browse tree:
  ordered **fields** (e.g. "DiD · panel") each with tag mappings and ordered
  **sub-categories**. Site-admin only; every change is snapshotted and
  restorable.

## The client

All server calls go through one stdlib script (never hand-write curl):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" <command> …
```

(If `CLAUDE_PLUGIN_ROOT` is unset, the script lives at `scripts/sotter.py`
two directories above this SKILL.md.)

| Command | Does |
|---|---|
| `setup KEY [URL] [--global]` | write `./.statsotter.json` (`--global`: `~/.statsotter.json`, all projects), gitignore it, verify the key |
| `me` | username, `is_site_admin`, card counts |
| `cards [--all]` | list own cards (`--all`: every card — site admins) |
| `card SLUG` | every field of one card, JSON — same shape `edit` accepts |
| `edit SLUG --json FILE\|-` | PATCH: send **only the fields to change** |
| `publish SLUG` / `unpublish SLUG` | flip draft ↔ public feed |
| `delete SLUG` | permanent removal |
| `validate FILE` | dry-run a knowledge doc against the server grammar |
| `upload FILE [--target SLUG] [--repo URL] [--force]` | create a card (no `--target`) or overwrite one from a doc |
| `doc SLUG [--save FILE]` | full knowledge markdown of a card |
| `tax get` | sidebar tree + `can_edit` + `head` revision id |
| `tax put --json FILE\|- [--label TEXT] [--expect-head N]` | replace the sidebar tree |
| `tax history` / `tax restore ID` | sidebar revision log / one-click rollback |
| `catalog` · `search QUERY` · `feedback KIND …` · `gaps` | discovery (used mostly by the tackle skill) |

Exit 0 = success; non-zero prints the server's JSON error body — read its
`errors` array and act on it. Write temp JSON payloads to a scratch file (or
pipe via stdin with `-`), never inline through shell quoting.

## First run — connecting the account

If any command fails with "No .statsotter.json found" (or `me` returns 401):

1. Ask the user for their StatsOtter API key: created on the website under
   **Settings → API keys → + New key** (starts with `sd_`, shown once).
2. Run `setup <key>` (add a base URL argument only if they run their own
   server). It writes `./.statsotter.json`, gitignores it at the repo root,
   and verifies. If the user works across many folders, use `--global` so the
   key lives in `~/.statsotter.json` once (the key is shown only once on the
   site — a per-folder config would strand them in the next project).
3. Report as `sd_…<last 4>`. **Never echo, log, or commit the full key.**

Run `me` once per session before admin-flavored requests — `is_site_admin`
tells you whether sidebar editing and editing other members' cards are
available. If a non-admin asks for those, explain that they are site-admin
features instead of attempting the call.

## Golden rules

1. **Natural language in, actions out.** Route by intent, not keywords; the
   user may write in any language. Reply in the user's language.
2. **Resolve cards by title, act by slug.** When the user names a card
   loosely, list their cards and match case-insensitively against titles and
   slugs. One match → proceed. Several or zero → show the candidates and ask.
3. **Show before you change.** For every write, present a compact
   before → after summary (only the fields that change) and get a yes before
   sending. One confirmation per change is enough — don't re-ask.
4. **Destructive or public-facing actions need an explicit yes**: delete
   (permanent — steps, votes, comments and every doc version go with it),
   publish/unpublish, overwriting a card via `upload --target`, any sidebar
   write, and `--force` past a duplicate warning.
5. **Site content is English.** Cards and sidebar labels on statsotter.ai are
   English-only; if the user drafts content in another language, offer a
   translation and confirm it before uploading. (Conversation with the user
   stays in their language.)
6. **Never invent APIs or figures.** Card content comes from real code and
   docs; figure URLs must be real, hot-linkable images — when unsure, none.

## Playbooks

### Who am I / account status
`me` → report username, role (member / site admin), card and draft counts.

### List cards — "我的卡片" / "show my drafts" / "what's on the site?"
`cards` (own), `cards --all` (site admin, everyone's), `catalog` (published
feed). Render a compact table: title (slug), draft/published, versions,
updated date, link. Offer next actions (open, edit, publish…).

### Read a card
`card SLUG` for the structured view, or `doc SLUG` for the full markdown.
Summarize; show the `card_url` link.

### Edit a card — rename, retag, fix a summary, tweak a step, rewrite AI notes
1. `card SLUG` — fetch the current state.
2. Build the patch with **only the fields being changed**. Field notes:
   - `title` (≤160 chars; renaming keeps the slug and URL stable — say so),
     `summary` (≤2000), `description`, `results`, `inputs`, `inputs_example`
     — plain replacement strings.
   - `tags` — the **complete** new list (≤12 names, e.g. `["DiD", "Event Study"]`).
   - `figures` — complete list of `{url, caption}`; `cover` — image URL or `""`.
   - `steps` — the **complete** step list `[{stage, name, url?, method?,
     note?, code?, formula?, depends_on?}, …]` (≤10; stage ∈ prep, diagnostic,
     estimation, inference, robustness, heterogeneity, reporting, other). To
     change one step: take `steps` from the GET, modify that entry, send the
     whole list back. Keep the `method` (platform-method slug) and
     `depends_on` values you fetched — they survive the roundtrip.
     `depends_on` lists prerequisite steps by their 1-based position in the
     list you send, so renumber it if you reorder or insert steps.
   - `ai_notes` — replaces the AI-only section wholesale.
3. Show the before → after diff, confirm, write the JSON to a scratch file,
   `edit SLUG --json <file>`.
4. Report what changed + the new doc version count + `card_url` (plus
   `doc_url` — the web doc editor with the full version history — when the
   user might want to inspect versions).

For a **big rewrite** ("restructure the whole card", "regenerate from the
repo"), prefer the doc roundtrip: `doc SLUG --save statsotter.md` (the client
strips the server's read-only `## Community signals` block so the file
validates as-is) → edit the file per
[references/template.md](references/template.md) → `validate` → confirm →
`upload statsotter.md --target SLUG`. Note: a doc upload rebuilds all steps
as external steps — platform-method links don't survive this path (use a
`steps` PATCH when those matter).

### Create a card from this repo — "publish this repo to StatsOtter" / "发布成卡片"
1. Scope: whole repo, or one tutorial/vignette the user names.
2. **Study the material seriously** — README, docs/vignettes/examples, and
   enough source to cite real function names, arguments and outputs.
3. Write `statsotter.md` at the repo root following
   [references/template.md](references/template.md) exactly. Card-facing
   sections stay concise; `## AI Notes` is exhaustive. The Description opens
   with a one-line unofficial-showcase attribution linking the repo.
4. `validate statsotter.md` — fix any listed errors and re-validate (≤3
   rounds; then show the errors and stop).
5. Show the title + summary, confirm, then `upload statsotter.md --repo <git
   remote URL>`.
6. On **409 duplicate**: show the existing card's title/url/reason. If
   `is_yours`, recommend updating it (`upload --target <slug>`); otherwise
   the user may confirm `--force` for a genuinely different card, or cancel.
7. On success: the card is a **draft**. Report the three links the server
   returns — `card_url` (preview), `session_url` (the web "My imports"
   chat-refine page), `doc_url` (web doc editor + version history) — and ask
   whether to publish to the public feed now; if yes, `publish SLUG`. (No
   website visit needed.)
8. Offer to overwrite the local file with the response's canonical
   `markdown` so local == server.

### Publish / unpublish
Confirm intent ("goes live on the public feed" / "hides it back to draft"),
then `publish SLUG` or `unpublish SLUG`; report the resulting state + link.

### Delete a card
State the exact title and that deletion is **permanent** (votes, comments,
all doc versions). On an explicit yes: `delete SLUG`. Mention that a local
`statsotter.md`, if present, could recreate it.

### View the sidebar — "左边栏现在长什么样?"
`tax get` → render the tree: each field with its blurb, tag mappings, live
card count, and its sub-categories indented. Note `can_edit` silently.

### Edit the sidebar — add/rename/move/remove fields or sub-categories, remap tags
Site admins only (`can_edit` from `tax get`; explain otherwise).

1. `tax get` — capture the current tree and `head`.
2. Apply the user's request to the JSON locally. Shape:
   `{"fields": [{"name", "slug"?, "blurb"?, "tags": [..],
   "subs": [{"name", "slug"?, "tags": [..]}, …]}, …]}`.
   - **Order = list position** — moving something means reordering the list.
   - Keep existing slugs when renaming (slug changes break bookmarked filter
     URLs); omit slug only for brand-new entries.
   - `tags` are tag slugs that place cards into that field/sub. `tax get`
     shows each entry's live card count — warn if an edit would orphan a
     populated field (its cards stay, they just leave the rail).
   - Deleting a field deletes its sub-categories with it — say so.
3. Show a before → after summary of exactly what changes, confirm.
4. `tax put --json <file> --label "<one-line change description>"
   --expect-head <head>` (pass `null` when `head` was null — a site with no
   revisions yet). On **409**: someone edited in between — refetch, reapply,
   show again. The label appears in the site's history page, so write it
   like a commit subject.
5. Report the new tree (and that history/rollback exists).

### Sidebar history / undo — "谁改了边栏?" / "roll it back"
`tax history` → table of id, date, author, label, one-line diff. Each
revision is a snapshot of the sidebar **after** its labelled change — so to
undo the change described in revision N, restore the revision listed *below*
it (the previous snapshot), not N itself. Confirm the target, then
`tax restore ID`. Restoring appends a new revision — nothing is lost.

### Most-wanted methods
`gaps` → what users searched for and did not find; useful when the user asks
"what card should I make next?".

## Errors

| Response | Meaning / action |
|---|---|
| 401 | key missing/expired/deactivated → re-run the first-run setup flow |
| 403 | site-admin feature; this account is a member — explain, don't retry |
| 404 on a card | not theirs / gone — refresh with `cards` and re-resolve |
| 409 on upload | duplicate card — see the create playbook |
| 409 on tax put | sidebar changed under you — refetch, reapply, reconfirm |
| 400 | validation errors — show each `errors[]` line verbatim, fix, retry |
| network error | say the server is unreachable; check `base_url` in `.statsotter.json` |
