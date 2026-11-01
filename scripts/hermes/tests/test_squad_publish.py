"""Tests for scripts/hermes/squad_publish.py.

Hermetic: the only remote is a local bare repo, `gh` is a stub first on PATH, git ignores the
user's config, and HERMES_HOME points into the temp dir so no test reads the live boards.

Run from the repo root: python3 -m unittest discover -s scripts/hermes/tests -v
"""
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import squad_publish as sp  # noqa: E402

URL = "https://github.com/o/r/pull/7"

# Logs its argv to $GH_STUB_LOG. `pr list` prints $GH_STUB_EXISTING (empty by default), `pr create`
# prints URL, `repo view` prints main. $GH_STUB_FAIL makes every call fail with that message.
GH_STUB = f"""#!/bin/sh
echo "$*" >> "$GH_STUB_LOG"
if [ -n "$GH_STUB_FAIL" ]; then echo "$GH_STUB_FAIL" >&2; exit 1; fi
case "$1 $2" in
  "pr list") [ -n "$GH_STUB_EXISTING" ] && echo "$GH_STUB_EXISTING" ;;
  "pr create") echo "{URL}" ;;
  "repo view") echo main ;;
esac
exit 0
"""


class RepoCase(unittest.TestCase):
    """A bare remote, a clone with `main` and `origin/HEAD`, and `feat/x` checked out in .worktrees/t1."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "bin").mkdir()
        gh = self.root / "bin" / "gh"
        gh.write_text(GH_STUB)
        gh.chmod(0o755)
        (self.root / "gitconfig").write_text("")
        (self.root / "hermes").mkdir()
        self.gh_log = self.root / "gh.log"
        patcher = mock.patch.dict(os.environ, {
            "PATH": f"{self.root / 'bin'}{os.pathsep}{os.environ['PATH']}",
            "HERMES_HOME": str(self.root / "hermes"),
            "GH_STUB_LOG": str(self.gh_log),
            "GIT_CONFIG_GLOBAL": str(self.root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        for var in ("GH_STUB_EXISTING", "GH_STUB_FAIL", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            os.environ.pop(var, None)

        self.remote = self.root / "remote.git"
        self.repo = self.root / "repo"
        self.wt = self.repo / ".worktrees" / "t1"
        self.body = self.root / "body.md"
        self.body.write_text("body\n")
        self.git("init", "-q", "--bare", "-b", "main", str(self.remote))
        self.git("clone", "-q", str(self.remote), str(self.repo))
        self.git("-C", str(self.repo), "symbolic-ref", "HEAD", "refs/heads/main")
        self.commit(self.repo, "README", "init")
        self.git("-C", str(self.repo), "push", "-q", "origin", "main")
        self.git("-C", str(self.repo), "remote", "set-head", "origin", "main")
        # Keep the repo's own checkout clean, as it is wherever .worktrees is ignored.
        (self.repo / ".git" / "info" / "exclude").write_text(".worktrees/\n")
        self.git("-C", str(self.repo), "worktree", "add", "-q", "-b", "feat/x", str(self.wt))
        self.commit(self.wt, "feature.txt", "feature")

    def git(self, *args):
        r = subprocess.run(["git", *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"git {' '.join(args)}: {r.stderr}")
        return r.stdout.strip()

    def commit(self, where, name, message):
        (Path(where) / name).write_text(message + "\n")
        self.git("-C", str(where), "add", name)
        self.git("-C", str(where), "commit", "-q", "-m", message)

    def remote_refs(self):
        return self.git("-C", str(self.remote), "for-each-ref")

    def gh_calls(self):
        return self.gh_log.read_text().splitlines() if self.gh_log.exists() else []

    def created_prs(self):
        return [c for c in self.gh_calls() if c.startswith("pr create")]


class PublishTests(RepoCase):
    def publish(self, branch="feat/x"):
        return sp.publish(self.repo, branch, "T", self.body)

    def assert_refused(self, branch, expect=None):
        before = self.remote_refs()
        with self.assertRaises(sp.Refused) as cm:
            self.publish(branch)
        if expect:
            self.assertIn(expect, str(cm.exception))
        self.assertEqual(self.remote_refs(), before, "a refused publish must not change the remote")
        self.assertEqual(self.created_prs(), [])

    def test_publishes_feature_branch(self):
        main_before = self.git("-C", str(self.remote), "rev-parse", "main")
        self.assertEqual(self.publish(), URL)
        self.assertEqual(self.git("-C", str(self.remote), "rev-parse", "feat/x"),
                         self.git("-C", str(self.repo), "rev-parse", "feat/x"))
        self.assertEqual(self.git("-C", str(self.remote), "rev-parse", "main"), main_before)
        self.assertIn(f"pr create --base main --head feat/x --title T --body-file {self.body}", self.gh_calls())

    def test_push_is_a_plain_same_name_refspec(self):
        with mock.patch.object(sp, "git", wraps=sp.git) as git:
            self.publish()
        pushes = [c.args[1:] for c in git.call_args_list if c.args[1] == "push"]
        self.assertEqual(pushes, [("push", "origin", "refs/heads/feat/x:refs/heads/feat/x")])  # no +, -u, --force
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "config", "--get", "branch.feat/x.remote"],
                                        capture_output=True, text=True).stdout, "", "no upstream tracking")

    def test_pr_base_is_the_repos_default_branch(self):
        self.git("-C", str(self.repo), "push", "-q", "origin", "main:develop")
        self.git("-C", str(self.repo), "remote", "set-head", "origin", "develop")
        self.assert_refused("develop", "default branch")
        self.assert_refused("main", "default branch")  # main stays protected when it isn't the default
        self.assertEqual(self.publish(), URL)
        self.assertIn(f"pr create --base develop --head feat/x --title T --body-file {self.body}", self.gh_calls())

    def test_default_branch_falls_back_to_gh(self):
        self.git("-C", str(self.repo), "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
        self.assertEqual(self.publish(), URL)
        self.assertIn("repo view --json defaultBranchRef -q .defaultBranchRef.name", self.gh_calls())

    def test_refuses_when_default_branch_unknown(self):
        self.git("-C", str(self.repo), "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
        with mock.patch.dict(os.environ, {"GH_STUB_FAIL": "no auth"}):
            self.assert_refused("feat/x", "can't determine the default branch")

    def test_refuses_default_branch(self):
        # A real local `master`, so it can only be refused by the protection rule, not by "no local branch".
        self.git("-C", str(self.repo), "branch", "master", "main")
        for name in ("main", "MAIN", "master", "HEAD", "origin/main", "refs/heads/main",
                     "refs/remotes/origin/main"):
            with self.subTest(name):
                self.assert_refused(name, "default branch")

    def test_refuses_missing_body_file_before_pushing(self):
        before = self.remote_refs()
        with self.assertRaises(sp.Refused) as cm:
            sp.publish(self.repo, "feat/x", "T", self.root / "nope.md")
        self.assertIn("body file", str(cm.exception))
        self.assertEqual(self.remote_refs(), before)

    def test_refuses_refspec_like_names(self):
        for name in ("+feat/x", "feat/x:main", "feat/x:refs/heads/main", "-f", "", "feat x"):
            with self.subTest(name):
                self.assert_refused(name, "bad branch name")

    def test_refuses_missing_branch(self):
        self.assert_refused("nope", "no local branch nope")

    def test_refuses_detached_head(self):
        self.git("-C", str(self.repo), "checkout", "-q", "--detach")
        self.assert_refused("HEAD", "no local branch HEAD")

    def test_refuses_dirty_worktree(self):
        for name, edit in (("untracked", lambda: (self.wt / "scratch.txt").write_text("x")),
                           ("modified", lambda: (self.wt / "feature.txt").write_text("changed"))):
            with self.subTest(name):
                edit()
                self.assert_refused("feat/x", str(self.wt))
                self.git("-C", str(self.wt), "checkout", "-q", ".")
                (self.wt / "scratch.txt").unlink(missing_ok=True)

    def test_refuses_non_fast_forward(self):
        other = self.root / "other"
        self.git("clone", "-q", str(self.remote), str(other))
        self.git("-C", str(other), "checkout", "-q", "-b", "feat/x", "origin/main")
        self.commit(other, "theirs.txt", "someone else")
        self.git("-C", str(other), "push", "-q", "origin", "feat/x")
        theirs = self.git("-C", str(self.remote), "rev-parse", "feat/x")
        self.assert_refused("feat/x", "non-fast-forward")
        self.assertEqual(self.git("-C", str(self.remote), "rev-parse", "feat/x"), theirs)

    def test_republish_fast_forwards_and_reuses_the_pr(self):
        self.assertEqual(self.publish(), URL)
        self.commit(self.wt, "more.txt", "more")
        with mock.patch.dict(os.environ, {"GH_STUB_EXISTING": URL}):
            self.assertEqual(self.publish(), URL)
        self.assertEqual(self.git("-C", str(self.remote), "rev-parse", "feat/x"),
                         self.git("-C", str(self.repo), "rev-parse", "feat/x"))
        self.assertEqual(len(self.created_prs()), 1)

    def test_idempotent_when_pr_exists(self):
        existing = "https://github.com/o/r/pull/3"
        with mock.patch.dict(os.environ, {"GH_STUB_EXISTING": existing}):
            self.assertEqual(self.publish(), existing)
        self.assertEqual(self.created_prs(), [])

    def test_gh_failure_is_a_command_error(self):
        with mock.patch.dict(os.environ, {"GH_STUB_FAIL": "boom"}):
            with self.assertRaises(sp.CommandError) as cm:
                self.publish()
        self.assertIn("boom", str(cm.exception))

    def test_source_has_no_force_shell_or_merge(self):
        src = (SCRIPTS / "squad_publish.py").read_text()
        self.assertNotIn("--force", src)
        self.assertNotIn("shell=True", src)
        self.assertEqual(set(re.findall(r"merge[\w-]*", src)), {"merge-base"})


class PublishCliTests(RepoCase):
    def run_cli(self, *args, **env):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "squad_publish.py"), *args],
            capture_output=True, text=True, env={**os.environ, **env})

    def publish_args(self, branch="feat/x"):
        return ["publish", "--repo", str(self.repo), "--branch", branch, "--title", "T",
                "--body-file", str(self.body)]

    def test_success_prints_only_the_url(self):
        r = self.run_cli(*self.publish_args())
        self.assertEqual((r.returncode, r.stdout), (0, URL + "\n"), r.stderr)

    def test_relative_body_file_reaches_gh_as_an_absolute_path(self):
        # gh runs in the repo, so a path relative to the caller's directory would point nowhere.
        r = subprocess.run([sys.executable, str(SCRIPTS / "squad_publish.py"), "publish", "--repo", str(self.repo),
                            "--branch", "feat/x", "--title", "T", "--body-file", "body.md"],
                           capture_output=True, text=True, cwd=self.root)
        self.assertEqual((r.returncode, r.stdout), (0, URL + "\n"), r.stderr)
        body_arg = self.created_prs()[0].split("--body-file ")[1]
        self.assertTrue(os.path.isabs(body_arg), body_arg)
        self.assertEqual(os.path.realpath(body_arg), os.path.realpath(self.body))

    def test_refusal_exits_2(self):
        before = self.remote_refs()
        r = self.run_cli(*self.publish_args("main"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("refused:"), r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertEqual(self.remote_refs(), before)

    def test_gh_failure_exits_1(self):
        r = self.run_cli(*self.publish_args(), GH_STUB_FAIL="gh exploded")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("error:"), r.stderr)
        self.assertIn("gh exploded", r.stderr)


class CleanupTests(RepoCase):
    """`kanban_release_worktrees.task_rows` is patched, so no board is read."""

    def setUp(self):
        super().setUp()
        self.cards = [("t1", "done", str(self.wt), "feat/x")]  # (id, status, workspace_path, branch_name)
        patcher = mock.patch("kanban_release_worktrees.task_rows", side_effect=lambda: list(self.cards))
        self.task_rows = patcher.start()
        self.addCleanup(patcher.stop)

    def add_worktree(self, tid, branch="feat/y"):
        path = self.repo / ".worktrees" / tid
        self.git("-C", str(self.repo), "worktree", "add", "-q", "-b", branch, str(path))
        return path

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = sp.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def branches(self):
        return self.git("-C", str(self.repo), "branch", "--list", "--format=%(refname:short)").split()

    def test_releases_done_card_and_keeps_its_branch(self):
        for status in ("done", "archived"):
            with self.subTest(status):
                self.cards = [("t1", status, str(self.wt), "feat/x")]
                self.assertEqual(sp.cleanup(self.repo, ["t1"]), ["released t1 (branch feat/x)"])
                self.assertFalse(self.wt.exists())
                self.assertIn("feat/x", self.branches())
                self.git("-C", str(self.repo), "worktree", "add", "-q", str(self.wt), "feat/x")

    def test_branch_label_comes_from_the_worktree_not_the_card(self):
        self.cards = [("t1", "done", str(self.wt), "card/other")]
        self.assertEqual(sp.cleanup(self.repo, ["t1"]), ["released t1 (branch feat/x)"])

    def test_keeps_unfinished_card(self):
        for status in ("running", "review", "blocked", "todo"):
            with self.subTest(status):
                self.cards = [("t1", status, str(self.wt), "feat/x")]
                self.assertEqual(sp.cleanup(self.repo, ["t1"]), [f"kept t1: card is {status}"])
                self.assertTrue(self.wt.exists())

    def test_keeps_dirty_worktree(self):
        for name, edit in (("untracked", lambda: (self.wt / "scratch.txt").write_text("x")),
                           ("modified", lambda: (self.wt / "feature.txt").write_text("changed"))):
            with self.subTest(name):
                edit()
                (line,) = sp.cleanup(self.repo, ["t1"])
                self.assertTrue(line.startswith("kept t1: "), line)
                self.assertNotIn("\n", line)
                self.assertTrue(self.wt.exists())
                self.git("-C", str(self.wt), "checkout", "-q", ".")
                (self.wt / "scratch.txt").unlink(missing_ok=True)

    def test_continues_after_a_keep(self):
        t2 = self.add_worktree("t2")
        self.cards = [("t1", "running", str(self.wt), "feat/x"), ("t2", "done", str(t2), "feat/y")]
        self.assertEqual(sp.cleanup(self.repo, ["t1", "t2"]),
                         ["kept t1: card is running", "released t2 (branch feat/y)"])
        self.assertTrue(self.wt.exists())
        self.assertFalse(t2.exists())

    def test_keeps_card_with_no_row_or_no_worktree(self):
        self.cards = [("t5", "done", None, None)]
        self.assertEqual(sp.cleanup(self.repo, ["t9", "t5"]), [
            "kept t9: no such card",
            f"kept t5: no worktree at {self.repo.resolve() / '.worktrees' / 't5'}"])

    def test_keeps_worktree_another_unfinished_card_works_in(self):
        for status, expect in (("running", "kept t1: in use by card t3"),
                               ("done", "released t1 (branch feat/x)")):
            with self.subTest(status):
                # A dir-workspace card pointing at t1's worktree, spelled differently.
                self.cards = [("t1", "done", str(self.wt), "feat/x"),
                              ("t3", status, f"{self.wt}/../t1", None)]
                self.assertEqual(sp.cleanup(self.repo, ["t1"]), [expect])
                if status == "done":
                    self.git("-C", str(self.repo), "worktree", "add", "-q", str(self.wt), "feat/x")
                else:
                    self.assertTrue(self.wt.exists())

    def test_branch_falls_back_to_the_cards_branch_then_question_mark(self):
        for tid, row_branch, expect in (("t2", "card/branch", "card/branch"), ("t3", None, "?")):
            with self.subTest(tid):
                path = self.repo / ".worktrees" / tid
                self.git("-C", str(self.repo), "worktree", "add", "-q", "--detach", str(path))
                self.cards = [(tid, "done", str(path), row_branch)]
                self.assertEqual(sp.cleanup(self.repo, [tid]), [f"released {tid} (branch {expect})"])

    def test_accepts_a_relative_repo_path(self):
        old = os.getcwd()
        self.addCleanup(os.chdir, old)
        os.chdir(self.root)
        self.assertEqual(sp.cleanup(Path("repo"), ["t1"]), ["released t1 (branch feat/x)"])
        self.assertFalse(self.wt.exists())

    def test_rejects_path_like_ids_before_touching_anything(self):
        for bad in ("../x", "a/b", ".", "..", "", "t 1", "t1\n"):
            with self.subTest(repr(bad)):
                rc, out, err = self.run_main("cleanup", "--repo", str(self.repo), "t1", bad)
                self.assertEqual((rc, out), (2, ""))
                self.assertEqual(err, f"refused: bad task id {bad}\n")
                self.assertTrue(self.wt.exists(), "a bad id must stop the whole run, t1 included")
                self.task_rows.assert_not_called()

    def test_cli_prints_one_line_per_id(self):
        t2 = self.add_worktree("t2")
        self.cards = [("t1", "running", str(self.wt), "feat/x"), ("t2", "done", str(t2), "feat/y")]
        rc, out, err = self.run_main("cleanup", "--repo", str(self.repo), "t1", "t2", "t9")
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(out.splitlines(), ["kept t1: card is running", "released t2 (branch feat/y)",
                                            "kept t9: no such card"])

    def test_cli_runs_as_a_script_and_finds_its_sibling_module(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "squad_publish.py"), "cleanup",
                            "--repo", str(self.repo), "t1"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "kept t1: no such card\n", ""))
        self.assertTrue(self.wt.exists())
