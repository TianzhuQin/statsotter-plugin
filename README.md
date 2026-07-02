# StatsOtter Claude Code plugin

Talk to [StatsOtter](https://statsotter.ai) in plain language, straight from
Claude Code. **There are no slash commands** — just say what you want, in any
language:

```
"Publish this repo to StatsOtter."            "发布这个仓库到 StatsOtter"
"Show my cards."                              "我有哪些卡片？"
"Rename my HonestDiD card to …"               "把摘要改得更简洁一点"
"Rewrite step 3's code to use att_gt()."      "把这张卡片下架"
"Publish the draft."                          "删掉那张测试卡片"
"Show me the left sidebar."                   "左边栏加一个 'Synthetic Control' 分类，放在 DiD 下面"
"Who changed the sidebar last week? Roll it back."
"Find a workflow for this panel data and estimate the treatment effect."
```

What it covers:

- **Cards** — create one from a repo (or a single tutorial in it), list yours,
  read/edit every field (title, summary, description, results, inputs, tags,
  figures, steps, AI notes), publish/unpublish drafts, delete. Edits record
  knowledge-doc versions server-side, same as the web editor.
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

- `skills/manage` — cards, sidebar, account: intent playbooks, safety rules
  (every destructive or public-facing change is confirmed first), and the
  knowledge-doc grammar (`skills/manage/references/template.md`).
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
