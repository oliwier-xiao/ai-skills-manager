# AI Skills Manager

An Omarchy bar widget for the skills, plugins and MCP servers behind your coding agents.

Three agents, three sets of config files, three ideas of where a skill lives. Claude Code keeps skills in
`~/.claude/skills`, plugins in a marketplace cache, and its connectors nowhere on disk at all. OpenCode
keeps skills in `~/.config/opencode/skills`, plugins as npm specifiers in `opencode.json`, and lets a
plugin inject MCP servers at runtime that never appear in any list. Codex keeps its own again. Some of it
is the same skill, symlinked into two places, and no view anywhere shows you that.

This widget is that view. One searchable list of everything all three agents can load, grouped so the
things wanting your attention are at the top, with the switch to turn any of it on or off, the command to
invoke it on your clipboard, and the upstream it came from when there is one to pull from.

## Status

Early. The design is settled and written down in [docs/DESIGN.md](docs/DESIGN.md); the decisions that
shaped it are in [docs/DECISIONS.md](docs/DECISIONS.md). The inventory backend works and is worth running
on its own — the panel is not built yet, so nothing is installable as a widget. This notice comes down
when it is.

```
$ bin/agent-ext doctor
agent-ext 0.1.0   scan 18.9 ms
skills            39
  claude          15   ~1179 tok always on
  codex            9   ~1035 tok always on
  opencode        33   ~4296 tok always on
mcp servers       7
claude plugins    1
categories        automation 16, agents 5, code 4, system 3, content 2, design 2, ...
```

`bin/agent-ext scan` prints the same inventory as one line of JSON. It needs python3 and nothing else.

## What it already finds

Three of these are on the author's own machine, and no other tool reports any of them:

- **The same skill loaded twice, differing.** `omarchy` exists as a real directory under
  `~/.claude/skills` and as a symlink to `/usr/share/omarchy` under `~/.codex/skills`. The two files are
  not the same. Claude Code and OpenCode read one, Codex reads the other, and nothing says so.
  Deduplicating on path alone calls them unrelated; on name alone, identical. Both are wrong.
- **One skill, three agents, five mount points.** `diagnose-crash` is a single `SKILL.md` reachable from
  `~/.claude/skills`, `~/.codex/skills` and `~/.agents/skills`. It is one row, not five.
- **Frontmatter that is not valid YAML.** `n8n-sdk-server` writes `Triggers on:` inside an unquoted
  scalar. A strict parser drops the entire frontmatter and reports a 162-token skill as costing 4.

## What it will do

- **Turn things on and off**, per agent, writing only the file that owns the setting.
- **Set a skill up for a project**, so it travels with the repo instead of following your home directory.
- **Pull upstream**, working out where a skill came from on its own where it can, and remembering the
  answer you give it where it cannot.
- **Put the invocation on your clipboard** — `/taste-skill` for the simple case, and for a plugin that
  takes arguments, a picker that assembles the whole line before it copies it.

## License

MIT
