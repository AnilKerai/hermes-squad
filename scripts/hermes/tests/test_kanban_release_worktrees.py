"""Tests for how scripts/hermes/kanban_release_worktrees.py finds the kanban boards.

Hermetic: every test runs with HOME pointing into a temp dir and HERMES_HOME unset unless it sets
one, so nothing resolves to the live ~/.hermes. main() is never called (it scans ~/git).

Run from the repo root: python3 -m unittest discover -s scripts/hermes/tests -v
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import kanban_release_worktrees as krw  # noqa: E402

DEFAULT_ROW = ("a1", "done", "/w/a1", "feat/a1")
BOARD_ROW = ("b1", "running", "/w/b1", "feat/b1")
OTHER_ROW = ("c1", "archived", "/w/c1", "feat/c1")


def make_db(path, *rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE tasks (id TEXT, status TEXT, workspace_path TEXT, branch_name TEXT)")
    conn.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


class BoardsCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"  # stands in for $HOME
        self.home.mkdir()
        self.root = self.tmp / "hermes"  # a Hermes root with two boards
        make_db(self.root / "kanban.db", DEFAULT_ROW)
        make_db(self.root / "kanban" / "boards" / "x" / "kanban.db", BOARD_ROW)
        (self.root / "profiles" / "lead").mkdir(parents=True)

        env = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("HERMES_HOME", None)  # undone by env.stop()

    def rows_with(self, hermes_home):
        with mock.patch.dict(os.environ, {"HERMES_HOME": str(hermes_home)}):
            return set(krw.task_rows())


class TestFindsBoards(BoardsCase):
    def test_profile_home_finds_the_root_boards(self):
        self.assertEqual(self.rows_with(self.root / "profiles" / "lead"), {DEFAULT_ROW, BOARD_ROW})

    def test_root_home_finds_the_boards(self):
        self.assertEqual(self.rows_with(self.root), {DEFAULT_ROW, BOARD_ROW})

    def test_default_board_comes_first_then_boards_sorted(self):
        make_db(self.root / "kanban" / "boards" / "a" / "kanban.db")
        with mock.patch.dict(os.environ, {"HERMES_HOME": str(self.root / "profiles" / "lead")}):
            self.assertEqual(krw.kanban_dbs(), [
                self.root / "kanban.db",
                self.root / "kanban" / "boards" / "a" / "kanban.db",
                self.root / "kanban" / "boards" / "x" / "kanban.db",
            ])


class TestDefaultProfile(BoardsCase):
    def setUp(self):
        super().setUp()
        make_db(self.home / ".hermes" / "kanban.db", OTHER_ROW)

    def test_unset_home_is_dot_hermes_under_home(self):
        self.assertEqual(krw.hermes_root(), self.home / ".hermes")
        self.assertEqual(set(krw.task_rows()), {OTHER_ROW})

    def test_empty_home_behaves_like_unset(self):
        with mock.patch.dict(os.environ, {"HERMES_HOME": ""}):
            self.assertEqual(krw.hermes_root(), self.home / ".hermes")
            self.assertEqual(set(krw.task_rows()), {OTHER_ROW})

    def test_a_path_under_dot_hermes_is_not_mapped_to_it(self):
        # A worker's TMPDIR looks like this. Hermes itself would map it to ~/.hermes; we don't,
        # or a test that sets HERMES_HOME to a scratch dir would read the live boards.
        scratch = self.home / ".hermes" / "profiles" / "engineer" / "cache" / "scratch" / "tmpX"
        with mock.patch.dict(os.environ, {"HERMES_HOME": str(scratch)}):
            self.assertEqual(krw.hermes_root(), scratch)
            self.assertEqual(set(krw.task_rows()), set())


class TestCallTime(BoardsCase):
    def test_each_call_reads_the_current_hermes_home(self):
        other = self.tmp / "other"
        make_db(other / "kanban.db", OTHER_ROW)
        self.assertEqual(self.rows_with(self.root), {DEFAULT_ROW, BOARD_ROW})
        self.assertEqual(self.rows_with(other), {OTHER_ROW})


if __name__ == "__main__":
    unittest.main()
