# Working context for Sascha (@wolfcast91)

This file auto-loads at session start. It is the standing brief — read it before
asking questions that it already answers.

Timezone is **Europe/Berlin**. German and English are both fine; the NOAH docs are German.

## Harness setup (persistent)

`.claude/settings.json` in this repo declares:

- **ECC** (`ecc@ecc`, from `affaan-m/ECC`) as an enabled plugin via `extraKnownMarketplaces`.
  Claude Code installs it from GitHub at session start — 288 skills, 67 agents, 94 commands,
  plugin-managed hooks. It tracks upstream; nothing is vendored into this repo.
- **`.claude/statusline.sh`** — Berlin clock + model + dir + git branch.

Rules for ECC, because they are easy to get wrong:

- **Never stack install methods.** The plugin install and `./install.sh --profile full`
  both write skills/commands/hooks. Running both duplicates all three. Plugin only.
- **Never copy ECC's `hooks/hooks.json` into `settings.json`** when installed as a plugin —
  Claude Code v2.1+ auto-loads plugin hooks, and duplicating them double-fires every hook.
- Plugin commands are namespaced: `/ecc:plan`, not `/plan`.
- ECC cannot ship `rules/` via the plugin system. If rule packs are wanted, copy
  `rules/common` plus one stack pack manually into `~/.claude/rules/ecc/`.
- To undo a manual install: `node scripts/uninstall.js` from an ECC clone. It only removes
  paths recorded in its own install-state.

This setup only applies to sessions working in **this** repo. Other repos need their own
`.claude/settings.json` (see "Open items").

## Repo map

| Repo | Vis | Stack | What it is |
|---|---|---|---|
| `NOAH` | private | Python | Self-hosted multi-agent stack. `docker-compose.yml` runs an openclaw gateway + `nousresearch/hermes-agent`. Model aliases route to local `gemma4` (Ollama on host), Gemini flash/pro, Claude sonnet/opus. Large skill library under `config/hermes/skills/` across 19 categories. Branding work in progress (`SOUL.md`, `zaphnat-*`). |
| `NOAH-Brain` | private | Markdown | Shared memory between two physically separated Hermes instances (homeserver + MacBook, no common mount). `mission-reports.md` uses a strict FRAME schema (Soll-Zustand, Motivation, Ist-Zustand, Constraints) with a dedup/merge rule; instances commit nightly ~03:00. HA helper `input_text.noah_brain_sync` is a pointer/trigger only, never storage. Each instance uses its own fine-grained PAT. |
| `EVA_brain` | private | Python | "Personal AI agent system v2". BR-01 Signal Extractor with JSON schema, `.jsonl` eval set, `make eval` as a hard ship gate. Three paths: Claude Code / plain Python / n8n. Stalled right after setup — last commit is `test: post-push hook`. |
| `kehrwoche-ai` | **public** | HTML | Single-page German landing site, "KI-Audit für den Mittelstand". Hand-rolled, ~1200 lines, dark + gold, Fraunces/Outfit. Impressum and Datenschutz done. The only customer-facing asset. |
| `wolfcast91` | **public** | — | This repo. GitHub profile repo; README still the untouched template. Now also the harness-config home. |
| `sentience-synth` | private | TypeScript | Dormant since Aug 2025. |
| `homeserver` | private | Shell | Dormant since Jul 2025. |
| `deutschlanddigital` | private | Dockerfile | Dormant since 2020. |

Only `wolfcast91/wolfcast91` is attached to a fresh session by default. Others need
`add_repo` (they exist and are reachable — do not report them as inaccessible).

## Open items

1. **NOAH has live credentials committed to git.** Unresolved as of 2026-08-04.
   No `.gitignore`; tracked files include `.env` (`CLAUDE_CODE_OAUTH_TOKEN`, `GOOGLE_API_KEY`,
   `DISCORD_BOT_TOKEN`, `NOAH_ARK_DISCORD_BOT_TOKEN`), `config/hermes/.env`, and
   `config/hermes/auth.json`. The whole live runtime state is committed too — `state.db`,
   `kanban.db`, 13 session files, 10 logs, 4 memory files, 226 files under `config/hermes/home/`
   including pip's HTTP cache — plus a 19 MB binary and ~40 MB of MP3s (199 MB / 1590 files total).
   Private repo, so not a public leak, but the tokens are in immutable history.
   **Rotation must happen before any history purge, and only Sascha can rotate.**
   Offered and not yet accepted: `.gitignore` + untrack + `git-filter-repo` purge.
2. **ECC config is not yet replicated to the other repos.** `NOAH`, `EVA_brain`, and
   `kehrwoche-ai` have no `.claude/settings.json`. NOAH also has `hermes` and `openclaw`
   install targets available (`./install.sh --target hermes --profile full`).
3. **Profile README is still the GitHub template** (`👋 Hi, I'm @wolfcast91`, all placeholders)
   while `kehrwoche-ai` is public and polished.

## Working preferences

- Verify before claiming. Say plainly when something is unverified, blocked, or skipped.
- Do not spawn subagents unless asked.
- Do not create pull requests unless asked.
- Secrets are never printed, echoed, or committed — inspect key *names* and shapes only.
- Destructive or irreversible work (history rewrites, force pushes, deletions) is confirmed
  first, even when a general go-ahead was given earlier.
