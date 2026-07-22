# StatsOtter Claude Code plugin

Talk to [StatsOtter](https://statsotter.ai) in plain language, straight from
Claude Code. **There are no slash commands** — just say what you want, in any
language (examples below in English; any language works):

```
"Publish this repo to StatsOtter."
"Show my cards."
"Rename my HonestDiD card to …"
"Make the summary more concise."
"Rewrite step 3's code to use att_gt()."
"Download the doc for my HonestDiD card so I can edit it."
"Push my edited statsotter.md back to that card."
"Which of my docs are too thin? Enrich the worst one."
"Publish the draft."  /  "Unpublish that card."  /  "Delete the test card."
"Show me the left sidebar."
"Add a 'Synthetic Control' sub-category under DiD, and move IV to the top."
"Who changed the sidebar last week? Roll it back."
"Find a workflow for this panel data and estimate the treatment effect."
```

What it covers:

- **Cards** — create one from a repo (or a single tutorial in it), list yours,
  read/edit every field (title, summary, description, results, inputs, tags,
  figures, steps, AI notes), publish/unpublish drafts, delete. Edits record
  knowledge-doc versions server-side, same as the web editor.
- **Knowledge docs, as files you own** — every card is also a strictly
  templated markdown document. Download it (`./<slug>.md`, or any earlier
  version from the history), edit it by hand or by asking Claude, and push it
  back: the plugin validates it, shows you exactly what will change on the
  card, waits for your yes, and reports the new version number. Nothing is
  lost — versions are immutable and append-only, so an old one can always be
  downloaded and re-uploaded. (Heads-up: an upload rewrites the card from the
  file, and steps come back as external steps — platform-method links survive
  only through a targeted step edit, which the plugin will offer instead.)
- **Docs are the AI's brain, so they have to be rich.** The card page is for
  humans; the doc is the corpus the platform's card-generation AI learns from
  today and the retrieval brain it will use tomorrow. So a bare URL never
  counts as knowledge here: whatever a linked paper or package page says is
  read and written *into* the document — assumptions and how to check them,
  every function argument, a runnable worked example with its real output,
  failure modes, and the provenance of every source actually read. Ask
  *"which of my docs are thin?"* and the plugin scores them 0-100, names what
  is missing, and offers to go research and fill the gaps.
- **Left sidebar** — view the browse rail from any account; site admins can
  reshape it (fields, sub-categories, tag mappings, ordering), with the full
  history and one-click rollback the website offers.
- **Site admins** (yiqingxu, tianzhuqin) can edit, publish and delete **every**
  card on the platform, not just their own — full moderation from the chat.
- **It learns.** When a site admin edits a card, the edit instruction is
  distilled into the guidelines the platform's card-generation AI reads — so
  every future card starts out closer to how you want it.
- **Tackle** — describe a goal, and the plugin finds the best-fitting
  published workflow, explains why, and (after your confirmation) runs it on
  the data in your folder. Your data never leaves the machine.

## Install

**The zero-effort way**: paste this into any Claude Code session and let it
install (or update) the plugin for you:

> Install or update the StatsOtter plugin for Claude Code. Run
> `claude plugin marketplace add TianzhuQin/statsotter-plugin`; if it says the
> marketplace already exists, run `claude plugin marketplace update statsotter`
> instead. Then run `claude plugin install statsotter@statsotter`; if it is
> already installed, run `claude plugin update statsotter` instead. Verify with
> `claude plugin list` (statsotter should be listed and enabled), then tell me
> to restart Claude Code — after that I can just talk to it in plain language
> ("publish this repo to StatsOtter", "show my cards", "edit the left
> sidebar"); it has no slash commands.

Manually, inside the Claude Code REPL:

```
/plugin marketplace add TianzhuQin/statsotter-plugin
/plugin install statsotter@statsotter
```

To update later: `claude plugin marketplace update statsotter` then
`claude plugin update statsotter` (or paste the prompt above again).

For local development, point Claude Code straight at the folder:

```
claude --plugin-dir /path/to/statsotter/statsotter-plugin
```

(Maintainers: sync this folder to the distribution repo with
`bash scripts/publish_plugin.sh git@github.com:TianzhuQin/statsotter-plugin.git`
from the statsotter repo root.)

## First run

1. On the website: **Settings → API keys → + New key** (label it, copy the
   `sd_…` key — it is shown once).
2. In Claude Code, just say *"connect my StatsOtter account"* (or paste the
   key when asked). The key is stored in `.statsotter.json` (gitignored
   automatically) and verified. The server defaults to
   `https://statsotter.ai`; mention a different URL only if you run your own
   copy.
3. That's it. Say what you want done.

Site admins (the accounts listed in the site's `community/perms.py`) also get
the moderation surface: editing any card and editing the left sidebar.

## How it works

- `skills/manage` — cards, docs, sidebar, account: intent playbooks, safety
  rules (every destructive or public-facing change is confirmed first), the
  knowledge-doc grammar (`skills/manage/references/template.md`) and the
  knowledge contract every rich doc follows
  (`skills/manage/references/knowledge-doc.md`, with a full worked
  `references/exemplar-doc.md`).
- `skills/enrich` — the research-and-rewrite pass: reads the sources a thin
  doc only linked to, and writes what they say into it.
- `skills/tackle` — find-introduce-confirm-run a published workflow on local
  data.
- `scripts/sotter.py` — the only thing that talks HTTP: a stdlib-only client
  for the site's `/api/v1/*` Bearer-key JSON API.

## Troubleshooting

- **401** — key wrong, expired or deactivated: create a new one on the site
  and say "reconnect my StatsOtter account".
- **403** — that action (sidebar editing, `--all` listings) is for site
  admins; your key belongs to a regular member account.
- **404 on a card** — it isn't under your account (or is gone); the API
  deliberately hides other members' cards rather than answering 403.
- **409 duplicate** on publishing — a similar card already exists; the plugin
  will suggest updating it instead, or you can insist it's different.
- **Validation errors** — the server names the exact lines; the plugin fixes
  `statsotter.md` and retries automatically (up to 3 rounds).
- **Warnings on a successful upload** — quality advice (thin AI notes, links
  without substance, a step with no note…). They never block; they are the
  list of things to fix to make the doc worth learning from. Say "fix those"
  and the plugin will.
- **A downloaded doc won't validate** — it was saved with `--with-signals`,
  which keeps the read-only community block for reading. Download it again
  without that flag for an upload-ready file.
