"""Unit tests for the parts of agent-ext that do not touch this machine's config.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    spec = importlib.util.spec_from_loader("agent_ext", None)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["__name__"] = "agent_ext"
    with open(os.path.join(ROOT, "bin", "agent-ext"), encoding="utf-8") as fh:
        exec(compile(fh.read(), "agent-ext", "exec"), mod.__dict__)  # noqa: S102
    return mod


ax = load()


class Frontmatter(unittest.TestCase):
    def test_plain_scalar(self):
        fm = ax.parse_frontmatter_block("name: api-design\ndescription: REST patterns.")
        self.assertEqual(fm["name"], "api-design")
        self.assertEqual(fm["description"], "REST patterns.")

    def test_block_scalar_is_not_lost(self):
        """A line-oriented regex reports these skills as costing 2 tokens."""
        fm = ax.parse_frontmatter_block("name: omarchy\ndescription: >\n  First line.\n  Second line.")
        self.assertEqual(fm["description"], "First line. Second line.")

    def test_literal_block_keeps_newlines(self):
        fm = ax.parse_frontmatter_block("description: |\n  one\n  two")
        self.assertEqual(fm["description"], "one\ntwo")

    def test_continuation_lines_are_joined(self):
        fm = ax.parse_frontmatter_block("description: starts here\n  and continues\nname: x")
        self.assertEqual(fm["description"], "starts here and continues")
        self.assertEqual(fm["name"], "x")

    def test_nested_mapping(self):
        fm = ax.parse_frontmatter_block("metadata:\n  origin: ECC\n  other: 1")
        self.assertEqual(fm["metadata"], {"origin": "ECC", "other": "1"})

    def test_quotes_are_stripped(self):
        self.assertEqual(ax.parse_frontmatter_block('name: "quoted"')["name"], "quoted")

    def test_no_frontmatter(self):
        self.assertEqual(ax.parse_frontmatter("# just markdown"), {})


class Tokens(unittest.TestCase):
    def test_matches_javascript_half_up_rounding(self):
        """latex-engineer lands on exactly 66.5; Claude Code shows 67, not 66."""
        name, desc = "x" * 10, "y" * 255
        self.assertEqual(len(f"{name} {desc}"), 266)
        self.assertEqual(ax.token_estimate(name, desc, "", 4), 67)

    def test_divisor_three(self):
        self.assertEqual(ax.token_estimate("a" * 30, "", "", 3), 10)

    def test_empty_parts_are_skipped(self):
        self.assertEqual(ax.token_estimate("abcd", "", "", 4), 1)


class Classifier(unittest.TestCase):
    def test_negative_rule_keeps_api_design_out_of_design(self):
        got = ax.classify("api-design", "REST API design patterns including resource naming.",
                          "/s/api-design", None)
        self.assertNotEqual(got["category"], "design")

    def test_marketplace_category_wins(self):
        got = ax.classify("whatever", "", "/s/whatever", "database")
        self.assertEqual(got["category"], "data")
        self.assertEqual(got["confidence"], "high")

    def test_n8n_path_heuristic(self):
        got = ax.classify("n8n-agents", "", "/s/n8n-agents", None)
        self.assertEqual(got["category"], "automation")

    def test_unmatched_falls_to_agents_and_is_marked(self):
        got = ax.classify("zzz", "qqq", "/s/zzz", None)
        self.assertEqual(got["category"], "agents")
        self.assertEqual(got["confidence"], "unclassified")

    def test_every_category_has_a_glyph(self):
        for cat in ax.CATEGORIES:
            self.assertIn(cat, ax.GLYPH)

    def test_official_map_targets_are_real_categories(self):
        for target in ax.OFFICIAL_MAP.values():
            self.assertIn(target, ax.CATEGORIES)


class SafeRead(unittest.TestCase):
    def test_refuses_a_symlink_at_the_final_component(self):
        with tempfile.TemporaryDirectory() as d:
            real = os.path.join(d, "real")
            with open(real, "w", encoding="utf-8") as fh:
                fh.write("secret")
            link = os.path.join(d, "link")
            os.symlink(real, link)
            self.assertEqual(ax.safe_read(real), b"secret")
            self.assertIsNone(ax.safe_read(link))

    def test_refuses_an_oversized_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "big")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("x" * 100)
            self.assertIsNone(ax.safe_read(p, max_bytes=10))

    def test_missing_file_is_none_not_an_exception(self):
        self.assertIsNone(ax.safe_read("/nonexistent/nope"))

    def test_directory_is_refused(self):
        self.assertIsNone(ax.safe_read("/tmp"))


class Drift(unittest.TestCase):
    def _item(self, name, digest):
        return {"dirName": name, "contentHash": digest, "realPath": "/" + name + digest,
                "attention": []}

    def test_same_name_different_bytes_is_flagged(self):
        items = [self._item("omarchy", "a"), self._item("omarchy", "b")]
        ax._mark_drift(items)
        self.assertTrue(all("drift" in i["attention"] for i in items))
        self.assertEqual(len(items[0]["driftPeers"]), 1)

    def test_same_name_same_bytes_is_not_flagged(self):
        items = [self._item("omarchy", "a"), self._item("omarchy", "a")]
        ax._mark_drift(items)
        self.assertFalse(any("drift" in i["attention"] for i in items))

    def test_unique_name_is_not_flagged(self):
        items = [self._item("solo", "a")]
        ax._mark_drift(items)
        self.assertEqual(items[0]["attention"], [])


class Roots(unittest.TestCase):
    def test_opencode_sees_claude_and_agents_by_default(self):
        os.environ.pop("OPENCODE_DISABLE_EXTERNAL_SKILLS", None)
        roots = {r["path"].split("/")[-2] + "/" + r["path"].split("/")[-1]: r for r in ax.skill_roots()}
        claude = next(r for r in ax.skill_roots() if r["path"].endswith(".claude/skills"))
        self.assertIn("opencode", claude["tools"])

    def test_the_env_var_takes_opencode_out(self):
        os.environ["OPENCODE_DISABLE_EXTERNAL_SKILLS"] = "1"
        try:
            claude = next(r for r in ax.skill_roots() if r["path"].endswith(".claude/skills"))
            self.assertNotIn("opencode", claude["tools"])
        finally:
            os.environ.pop("OPENCODE_DISABLE_EXTERNAL_SKILLS", None)

    def test_claude_never_reads_the_shared_agents_dir(self):
        shared = next(r for r in ax.skill_roots() if r["path"].endswith(".agents/skills"))
        self.assertNotIn("claude", shared["tools"])


if __name__ == "__main__":
    unittest.main()


class InvalidYaml(unittest.TestCase):
    def test_bare_colon_in_a_plain_scalar_is_flagged(self):
        self.assertTrue(ax.has_unquoted_colon("description: Triggers on: n8n, workflows"))

    def test_quoted_scalar_may_contain_a_colon(self):
        self.assertFalse(ax.has_unquoted_colon('description: "Triggers on: n8n"'))

    def test_block_scalar_may_contain_a_colon(self):
        self.assertFalse(ax.has_unquoted_colon("description: >\n  Triggers on: n8n"))

    def test_ordinary_frontmatter_is_clean(self):
        self.assertFalse(ax.has_unquoted_colon("name: x\ndescription: A normal one."))

    def test_we_still_read_the_invalid_file(self):
        fm = ax.parse_frontmatter_block("description: Triggers on: n8n, workflows")
        self.assertEqual(fm["description"], "Triggers on: n8n, workflows")


class TieBreak(unittest.TestCase):
    def test_agents_loses_a_tie_to_a_real_domain(self):
        """A router skill for n8n names skills and MCP often enough to tie."""
        desc = ("Use when building, editing or debugging an n8n workflow through the n8n-mcp "
                "MCP server. The entry-point skill for the pack; routes you to the right "
                "specialist skill on any n8n, workflow, node or automation task.")
        got = ax.classify("using-n8n-mcp-skills", desc, "/s/using-n8n-mcp-skills", None)
        self.assertEqual(got["category"], "automation")

    def test_agents_still_wins_when_it_is_alone(self):
        got = ax.classify("prompt-lab", "Prompt and eval tooling for subagent tool use.",
                          "/s/prompt-lab", None)
        self.assertEqual(got["category"], "agents")


class AdversarialReads(unittest.TestCase):
    """The cases the marketplace reviewer names explicitly. Each one used to take
    the helper down with a traceback and an empty stdout."""

    def test_a_fifo_does_not_block_the_shell(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "fifo")
            os.mkfifo(p)
            self.assertIsNone(ax.safe_read(p))

    def test_a_hard_linked_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            real = os.path.join(d, "real")
            with open(real, "w", encoding="utf-8") as fh:
                fh.write("x")
            os.link(real, os.path.join(d, "second-name"))
            self.assertIsNone(ax.safe_read(real))

    def test_a_world_writable_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "loose")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("x")
            os.chmod(p, 0o666)
            self.assertIsNone(ax.safe_read(p))

    def test_deeply_nested_json_is_a_finding_not_a_crash(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "deep.json")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("[" * 200000 + "]" * 200000)
            value, err = ax.read_json(p)
            self.assertIsNone(value)
            self.assertIsInstance(err, str)

    def test_a_config_value_of_the_wrong_type_does_not_raise(self):
        self.assertEqual(ax.as_dict("a string"), {})
        self.assertEqual(ax.as_dict(None), {})
        self.assertEqual(ax.as_list({"not": "a list"}), [])

    def test_control_characters_are_stripped_before_they_reach_qml(self):
        self.assertEqual(ax.clip("a\x00b\x1bc"), "abc")

    def test_long_strings_are_capped(self):
        self.assertEqual(len(ax.clip("x" * 5000, 100)), 100)


class Redaction(unittest.TestCase):
    def test_an_api_key_flag_is_masked(self):
        self.assertNotIn("sk-live-DEADBEEF", ax.redact("npx pkg --api-key sk-live-DEADBEEF"))

    def test_a_url_query_string_is_dropped(self):
        self.assertEqual(ax.redact("https://h/mcp?token=abc"), "https://h/mcp?…")

    def test_an_env_assignment_is_masked(self):
        self.assertNotIn("sk-proj-XYZ", ax.redact("docker run -e OPENAI_API_KEY=sk-proj-XYZ img"))

    def test_a_benign_command_is_left_alone(self):
        cmd = "npx -y @modelcontextprotocol/server-filesystem /home/me"
        self.assertEqual(ax.redact(cmd), cmd)
