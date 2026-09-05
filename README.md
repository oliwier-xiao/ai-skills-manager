# Agent Extensions

An Omarchy bar widget for the skills, plugins and MCP servers behind your coding agents.

Three agents, three sets of config files, three ideas of where a skill lives. Claude Code keeps skills in
`~/.claude/skills`, plugins in a marketplace cache, and its connectors nowhere on disk at all. OpenCode
keeps skills in `~/.config/opencode/skills`, plugins as npm specifiers in `opencode.json`, and lets a
plugin inject MCP servers at runtime that never appear in any list. Codex keeps its own again. Some of it
is the same skill, symlinked into two places, and no view anywhere shows you that.

This widget is that view. One searchable list of everything all three agents can load, grouped by what the
thing is for, with what each one costs you in tokens on every single turn, which tool can see it, and the
command that invokes it — on your clipboard, in the spelling that particular agent expects.

## What it shows you

Three of these are true on the machine this was written on, and no other tool reports any of them.

**The same skill loaded twice, differing.** `omarchy` exists as a real directory under `~/.claude/skills`
and as a symlink to `/usr/share/omarchy` under `~/.codex/skills`. The two files are not the same. Claude
Code and OpenCode read one, Codex reads the other, and nothing says so. Deduplicating on path alone calls
them unrelated; on name alone, identical. Both are wrong, so the list deduplicates on the resolved path and
then compares content hashes, and marks the pair as drifted.

**One skill, three agents, five mount points.** `diagnose-crash` is a single `SKILL.md` reachable from
`~/.claude/skills`, `~/.codex/skills` and `~/.agents/skills`. It is one row carrying three tool badges, not
five rows repeating themselves.

**Frontmatter that is not valid YAML.** One skill here writes `Triggers on:` inside an unquoted scalar. A
strict parser drops the entire frontmatter rather than the one field and reports a 162-token skill as
costing 4. The reader is deliberately lenient, and the row is flagged so you know the file is one strict
parser away from vanishing.

## The token figure

Every skill a tool can see puts its name and description into the system prompt on every turn, whether or
not you ever use it. That is the number in each row, and the per-tool total in each group header.

It is computed the way Claude Code's own extensions browser computes it — the length of the name,
description and when-to-use joined together, divided by four, rounded half up. On this machine that
reproduces fourteen of the fifteen figures the browser shows, to the token. The setting offers a divisor of
three instead, which is closer to how newer models actually tokenise dense technical prose and therefore
closer to what you are really paying; the default matches the browser so the two agree.

## Requirements

Omarchy 4 with its Quickshell bar, and `python3`, which a stock Omarchy install already has — ten packages
in the base set depend on it. Nothing else. The widget reads your agent configuration and never writes to
it.

Whichever of the three agents you actually use is the one you get rows for. A tool that is not installed is
one quiet line saying so, not an error.

## Install

```
omarchy plugin add https://github.com/oliwier-xiao/ai-skills-manager.git --enable
```

`--enable` puts it straight on the bar and asks which side you want it on. Leave the flag off and it
installs disabled, so you can read the code first and turn it on later with `omarchy plugin enable
oliwier.ai-skills-manager`. Either way nothing runs until you open the panel for the first time.

## Removal

```
omarchy plugin remove oliwier.ai-skills-manager
```

That takes the widget off the bar and deletes the plugin. It is the whole footprint. The widget writes no configuration of its own, leaves nothing behind in
`~/.config`, `~/.cache` or `~/.local`, and has not modified any file belonging to Claude Code, OpenCode or
Codex.

## The command line behind it

The panel draws; `bin/agent-ext` does every byte of the reading. It is worth running on its own.

```
bin/agent-ext doctor
```

```
agent-ext 0.1.0   scan 19.9 ms
skills            39
  claude          15   ~1179 tok always on
  codex            9   ~1035 tok always on
  opencode        33   ~4296 tok always on
mcp servers       7
claude plugins    1
categories        automation 16, agents 5, code 4, system 3, content 2, design 2, ...
```

`bin/agent-ext scan` prints the same inventory as one line of JSON, which is what the panel reads.

## Development

Tests are plain `unittest` and need nothing that is not already here.

```
python3 -m unittest discover -s tests -v
```

`bin/preflight` checks this repository against the Omarchy plugin marketplace's published rules — the
structural validator, the automated security baseline, and the recurring demands of its manual review —
and exits non-zero on any violation. Run it before proposing a change.

The design and the reasoning behind it are in [docs/DESIGN.md](docs/DESIGN.md); the decisions that shaped
it, and what was deliberately left out, are in [docs/DECISIONS.md](docs/DECISIONS.md).

## License

MIT. See [LICENSE](LICENSE).
