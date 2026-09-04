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

Early. The research is done and the design is settled; the code is being written. Nothing here is
installable yet — this notice comes down when it is.

## What it will do

- **Turn things on and off**, per agent, writing only the file that owns the setting.
- **Set a skill up for a project**, so it travels with the repo instead of following your home directory.
- **Pull upstream**, working out where a skill came from on its own where it can, and remembering the
  answer you give it where it cannot.
- **Put the invocation on your clipboard** — `/taste-skill` for the simple case, and for a plugin that
  takes arguments, a picker that assembles the whole line before it copies it.

## License

MIT
