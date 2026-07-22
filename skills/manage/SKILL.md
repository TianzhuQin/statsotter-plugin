---
name: manage
description: Manage StatsOtter (statsotter.ai) through plain conversation — there are no slash commands. Use whenever the user mentions StatsOtter (in any language) or wants to connect their StatsOtter account / API key; list their cards or drafts; turn a repo or tutorial into a card; view, edit, rename, retag or rewrite a card (any field, steps, figures, AI notes); download a card's knowledge document as a markdown file (latest or an older version), edit that file and push it back; check which of their docs are thin or low quality; publish or unpublish a card; delete a card; view or edit the site's left sidebar (fields and sub-categories); or inspect/restore sidebar history.
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
  records a new immutable version server-side. The card page is for humans;
  **the doc is the corpus the platform's AI learns from**, so it must carry
  the actual knowledge, not links to it (see Golden rule 7). Users can
  download a doc as a file, edit it, and push it back — see the doc-roundtrip
  playbooks below.
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
| `validate FILE` | dry-run a knowledge doc against the server grammar (returns blocking `errors[]`, non-blocking `warnings[]` and a `quality` score) |
| `upload FILE [--target SLUG] [--repo URL] [--force]` | create a card (no `--target`) or overwrite one from a doc |
| `doc SLUG [--save [FILE]] [--version N] [--versions] [--with-signals]` | read or download a knowledge doc — bare `--save` writes `./<slug>.md` |
| `audit [--all]` | the thin-doc worklist: cards scoring under 60 (`--all`: everyone's — site admins) |
| `tax get` | sidebar tree + `can_edit` + `head` revision id |
| `tax put --json FILE\|- [--label TEXT] [--expect-head N]` | replace the sidebar tree |
| `tax history` / `tax restore ID` | sidebar revision log / one-click rollback |
| `lesson --instruction "…" [--slug S] [--context "…"]` | teach the card-generation AI from an edit instruction (site admins) |
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
tells you whether the site-admin surface is available: sidebar writes, editing
other members' cards, the `--all` listings (`cards --all`, `audit --all`), and
`lesson`. If a non-admin asks for any of those by name ("teach the AI from
this edit", "show everyone's thin docs"), say plainly that it is a site-admin
feature on this platform instead of firing a call that will 403.

## Golden rules

1. **Natural language in, actions out.** Route by intent, not keywords; the
   user may write in any language. Reply in the user's language.
2. **Resolve cards by title, act by slug.** When the user names a card
   loosely, list their cards and match case-insensitively against titles and
   slugs. One match → proceed. Several or zero → show the candidates and ask.
   **Site admins (yiqingxu, tianzhuqin) may edit, publish, unpublish and
   delete EVERY card on the platform** — when the card isn't under their own
   account, resolve it with `cards --all` (or `catalog`); the API allows it
   with the same key.
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
   Anything you could not verify from a real source is omitted, or written
   down explicitly as unverified under `### Open questions`.
7. **A URL may accompany knowledge, never replace it.** The knowledge doc is
   what the platform's AI reads and learns from, so it must stand alone when
   the link rots: whatever a linked page says has to be read, understood and
   written *into* `## AI Notes`. Follow the outline in
   [references/knowledge-doc.md](references/knowledge-doc.md) for every doc you
   write or edit, and read
   [references/exemplar-doc.md](references/exemplar-doc.md) once per session
   before authoring a doc for the first time, so you know what "rich" means
   here. A doc whose AI Notes are empty or a handful of bare links is a bug,
   not a style choice.

## Playbooks

### Who am I / account status
`me` → report username, role (member / site admin), card and draft counts.

### List cards — "show my cards" / "show my drafts" / "what's on the site?"
`cards` (own), `cards --all` (site admin, everyone's), `catalog` (published
feed). Render a compact table: title (slug), draft/published, versions,
updated date, link. Offer next actions (open, edit, publish…).

### Read a card
`card SLUG` for the structured view, or `doc SLUG` for the full markdown
(add `--with-signals` to see the read-only community block — votes, comments —
appended to it). Summarize; show the `card_url` link. Both responses carry a
`quality` block; mention a weak score only when it is relevant or asked for.

### Download a card's doc — "give me the markdown", "save that doc as a file"
1. Resolve the card to a slug (Golden rule 2).
2. `doc SLUG --save` writes **`./<slug>.md`** in the current folder. Pass a
   path to choose the name: `doc SLUG --save notes/honestdid.md` (the folder
   must already exist).
3. The saved file is **upload-ready**: the client requests the raw document
   and strips the server's read-only `## Community signals` block, so the file
   validates and can go straight back with `upload --target SLUG`. Only add
   `--with-signals` when the user wants to *read* the community block — such a
   file will not validate.
4. **Older versions**: `doc SLUG --versions` lists the history (version
   number, date, source, author, chars — newest first) and writes nothing.
   Then `doc SLUG --version 3 --save old-v3.md` downloads that stored version.
   Give an explicit filename for an old version — a bare `--save` always
   writes `./<slug>.md` and would overwrite the copy of the latest.
5. Report the path, the version number returned, and the `quality_hint` line
   (score + warning codes). If the score is low, offer to enrich it. When the
   user is downloading in order to *edit* ("so I can edit it"), read them the
   two consequences from "Edit the doc file directly" now — an upload rewrites
   the card from the file, and steps come back as external steps — so the
   decision is made before they start typing.

### Edit the doc file directly — the round-trip
Use this whenever the user wants to work on the markdown itself ("let me edit
the doc", "restructure the whole card", "regenerate it from the repo"), or
when the change is large enough that field-by-field patching would be clumsy.

**State the consequence before starting** — the user must understand both of
these:
- Uploading a doc **rewrites the card's fields from that markdown**. Anything
  you delete from the file is deleted from the card; the file is the new
  truth, not a patch.
- **Steps become external steps.** A doc upload rebuilds every step from the
  markdown, so platform-method links (the `method` slug on a step) do **not**
  survive this path. If the card has method-linked steps and those matter, do
  a `steps` PATCH instead (see "Edit a card") — or accept the loss knowingly.

Then:
1. `doc SLUG --save` → `./<slug>.md`. Tell the user the exact path so they can
   open it in their editor.
2. Edit the markdown — by hand, or by asking Claude ("make AI Notes cover the
   assumptions and the API"). Keep it legal against
   [references/template.md](references/template.md) (section order and
   headings are strict) and make `## AI Notes` follow
   [references/knowledge-doc.md](references/knowledge-doc.md); read
   [references/exemplar-doc.md](references/exemplar-doc.md) first if you have
   not authored a doc yet this session. Never let a bare URL stand in for the
   knowledge behind it (Golden rule 7).
3. `validate <file>` — fix every line in `errors[]` and re-validate (≤3
   rounds, then show the errors and stop). `warnings[]` never block an upload;
   surface them and offer to fix them, because they are exactly what makes the
   doc worth training on. The response also carries the `quality` score.
4. **Show the diff before sending**: compare the edited file against the card
   as it is now — `card SLUG`, or a fresh `doc SLUG --save <scratch>.md` with
   an **explicit** filename. Never re-run a bare `doc SLUG --save` here: it
   writes `./<slug>.md`, which is the very file the user just edited, and
   their work would be gone. Present a compact before → after of the fields
   that change — title, summary, tags, step count/names, AI Notes size. Call
   out anything being *removed*.
5. Confirm, then `upload <file> --target SLUG`.
6. Report the score before → after (the response carries the saved doc's
   `quality`), any remaining `warnings[]`, and `card_url` + `doc_url` (the web
   doc editor, where the full version history lives). The upload response does
   **not** carry a version number — never invent one; read it from
   `doc SLUG --versions` (top row, writes nothing) or `card SLUG`
   (`doc_versions`). Nothing is lost: every previous version stays retrievable
   with `doc SLUG --version N`.
7. Feed the lesson back (site admins) exactly as in "Edit a card" step 5.

To restore an older version: `doc SLUG --version N --save restore-N.md` →
`validate` → confirm → `upload restore-N.md --target SLUG`. That lands as a
*new* version on top; the history is append-only, so nothing is overwritten.

### Which of my docs are thin? — "audit my docs", "what needs work?"
1. `audit` (site admins: `audit --all`) returns only the cards scoring **under
   60**, most recently updated first, each with `doc_chars`, `ai_notes_chars`
   and `quality_score`. An empty list is good news — say so.
2. Render a table: title (slug), score, doc size, AI-Notes size. Explain the
   score in one line: **0-100, deterministic** — up to 40 points for the sheer
   volume of AI Notes, 20 for covering the expected subsections (assumptions,
   API/parameters, worked example, failure modes, provenance), 20 for every
   step having a note plus at least one code block, and the rest for Results,
   Inputs, the input example and a substantial description.
3. Translate the warning codes the payload carries — each `message` is already
   one actionable sentence, so quote it rather than paraphrasing:

   | Code | What it means |
   |---|---|
   | `ai_notes_missing` | `## AI Notes` is empty — the AI learns nothing from this card |
   | `ai_notes_thin` | under 1500 chars of notes |
   | `ai_notes_sections_missing` | none of the expected subsections (assumptions, API, worked example, failure modes, provenance) |
   | `url_without_substance` | 3+ links but almost no distilled knowledge — read those pages and write down what they say |
   | `step_without_note` | at least one step has no `- Note:` |
   | `no_code_example` | no fenced code block anywhere in Steps |
   | `results_empty` / `inputs_empty` / `input_example_empty` | that card section is blank |
   | `description_thin` | description under 400 chars |

4. Offer the hand-off: **"want me to enrich these?"** — the `enrich` skill
   (`skills/enrich/SKILL.md`) does the research-and-rewrite pass; this skill
   does the plumbing (download, validate, diff, upload). Work one card at a
   time and confirm each upload.

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
   - `ai_notes` — replaces the AI-only section wholesale. Whatever you send
     must follow [references/knowledge-doc.md](references/knowledge-doc.md)
     (the `###` outline: method identity, assumptions and how to check them,
     API reference, worked example, failure modes, provenance…) and obey
     Golden rule 7 — no bare URL standing in for the knowledge behind it.
     Read [references/exemplar-doc.md](references/exemplar-doc.md) before
     writing AI Notes for the first time in a session. When appending rather
     than replacing, fetch the current `ai_notes` first and send back the
     merged text.
3. Show the before → after diff, confirm, write the JSON to a scratch file,
   `edit SLUG --json <file>`.
4. Report what changed + the new doc version count + `card_url` (plus
   `doc_url` — the web doc editor with the full version history — when the
   user might want to inspect versions).
5. **Feed the lesson back** (site admins only — skip silently otherwise):
   after a successful edit, teach the card-generation AI so future cards
   start out right:
   `lesson --instruction "<the user's request, verbatim in their own words>"
   --slug SLUG --context "<one line on what changed>"`.
   The server distils it into the guidelines every future AI import reads
   (one-off facts and duplicates are dropped automatically). Non-blocking:
   a failure here never affects the edit — just mention it briefly. Skip it
   for pure housekeeping (delete, publish/unpublish, undo) where there is
   no content preference to learn.

For a **big rewrite** ("restructure the whole card", "regenerate from the
repo"), or any time the user would rather work in the markdown, switch to
"Edit the doc file directly" above — it covers the download, the validate,
the diff and the consequences of an `upload --target`.

### Create a card from this repo — "publish this repo to StatsOtter"
1. Scope: whole repo, or one tutorial/vignette the user names.
2. **Study the material seriously** — README, docs/vignettes/examples, and
   enough source to cite real function names, arguments and outputs. Follow
   the links that matter (papers, package docs, the reference manual) and read
   them; what they say goes into the doc, not the link (Golden rule 7).
3. Write `statsotter.md` at the repo root following
   [references/template.md](references/template.md) exactly. Card-facing
   sections stay concise; **`## AI Notes` is exhaustive and follows
   [references/knowledge-doc.md](references/knowledge-doc.md)** — read
   [references/exemplar-doc.md](references/exemplar-doc.md) first if this is
   the session's first doc, then work down that outline: method identity and
   key papers, when to use it, each assumption with how to check it, the
   estimand, every function's full signature and arguments, data
   requirements, a runnable worked example with its real output, how to read
   that output, diagnostics, failure modes with verbatim error messages,
   alternatives, performance, provenance (every source you actually read),
   open questions. Never invent an argument, number or citation. The
   Description opens with a one-line unofficial-showcase attribution linking
   the repo.
4. `validate statsotter.md` — fix any listed errors and re-validate (≤3
   rounds; then show the errors and stop). Read the non-blocking
   `warnings[]` and the `quality` score too: below ~60 the doc is not yet
   worth training on — fill the gaps the warnings name before uploading.
5. Show the title + summary, confirm, then `upload statsotter.md --repo <git
   remote URL>`.
6. On **409 duplicate**: show the existing card's title/url/reason. If
   `is_yours`, recommend updating it (`upload --target <slug>`); otherwise
   the user may confirm `--force` for a genuinely different card, or cancel.
7. On success: the card is a **draft**. Report the three links the server
   returns — `card_url` (preview), `session_url` (the web "My imports"
   chat-refine page), `doc_url` (web doc editor + version history) — plus the
   saved doc's `quality` score and any `warnings[]`, and ask whether to
   publish to the public feed now; if yes, `publish SLUG`. (No website visit
   needed.)
8. Offer to overwrite the local file with the response's canonical
   `markdown` so local == server.

### Publish / unpublish
Confirm intent ("goes live on the public feed" / "hides it back to draft"),
then `publish SLUG` or `unpublish SLUG`; report the resulting state + link.

### Delete a card
State the exact title and that deletion is **permanent** (votes, comments,
all doc versions). On an explicit yes: `delete SLUG`. Mention that a local
`statsotter.md`, if present, could recreate it.

### View the sidebar — "what does the left sidebar look like?"
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

### Sidebar history / undo — "who changed the sidebar?" / "roll it back"
`tax history` → table of id, date, author, label, one-line diff. Each
revision is a snapshot of the sidebar **after** its labelled change — so to
undo the change described in revision N, restore the revision listed *below*
it (the previous snapshot), not N itself. Confirm the target, then
`tax restore ID`. Restoring appends a new revision — nothing is lost.

### Most-wanted methods
`gaps` → what users searched for and did not find; useful when the user asks
"what card should I make next?". Pair it with `audit`: `gaps` says what is
missing, `audit` says what already exists but teaches the AI nothing yet.

## Errors

| Response | Meaning / action |
|---|---|
| 401 | key missing/expired/deactivated → re-run the first-run setup flow |
| 403 | site-admin feature; this account is a member — explain, don't retry |
| 404 on a card | not theirs / gone — refresh with `cards` and re-resolve |
| 404 on `doc --version N` | no such version — run `doc SLUG --versions` and pick from the list |
| 409 on upload | duplicate card — see the create playbook |
| 409 on tax put | sidebar changed under you — refetch, reapply, reconfirm |
| 400 | validation errors — show each `errors[]` line verbatim, fix, retry |
| `warnings[]` in a 200 | quality advice, never blocking — report them and offer to fix; do not treat them as failures |
| network error | say the server is unreachable; check `base_url` in `.statsotter.json` |
