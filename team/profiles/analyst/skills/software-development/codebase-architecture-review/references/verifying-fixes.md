# Verifying a Fix Before Claiming It

Passing tests prove the fix compiles against the tests you wrote. These checks prove the
tests would catch the bug coming back, and that the claims in your commit message hold.

## 1. Mutation-check the fix

Break the fix on purpose, one way at a time, and confirm each break fails at least one test.
Pick mutations that match the bug's history: the original defect, your own first
(incomplete) fix, and each adapter- or caller-level gap.

```bash
S=/abs/path/to/scratch/mut && mkdir -p "$S"     # absolute path, not a shell $TMPDIR guess
F=src/.../Loop.cs; cp "$F" "$S/loop.bak"
run() { <test command> 2>&1 | grep -E "Passed!|Failed!|^\s+Failed " | head -8; }

perl -0pi -e 's/<fixed construct>/<buggy construct>/s' "$F"
grep -c "<buggy construct>" "$F"   # prove the mutation applied; 0 means the regex missed
run; cp "$S/loop.bak" "$F"

diff -q "$F" "$S/loop.bak" && echo restored
```

- **Confirm the mutation applied** (`grep -c`) before trusting a green run — a regex that
  matches nothing produces "all tests pass" and a false sense of a gap.
- **Never run two mutation scripts against the same files at once**, including a stale
  background run you have lost track of: each restores from its own backup and they can
  restore a mutated copy. If it may have happened, check the commit, not the working tree:
  `git grep -n "<buggy construct>" HEAD -- <path>` must be empty.
- A mutation that fails *no* test is a finding: add the test, then re-run the mutation.
- Only write "mutation-checked" in a commit or PR body with this output behind it, and list
  the mutations.

## 2. Cover the line that feeds a pure mapper

Extracting wire-format logic into a pure, tested function leaves the client line that calls
it untested — a reviewer will point at it. Add a seam and drive the real client with a
recorded response body:

- An `internal` constructor taking an `HttpMessageHandler` (public constructor chains to it
  with `null`), visible to the test project.
- A canned handler returning the provider's real response shape, including omitted fields
  (model `omitempty` by leaving the key out, not by writing `null`).
- **Minify fixtures for line-delimited readers.** SDKs for NDJSON-streaming APIs read the body
  line by line even for non-streamed requests; a pretty-printed fixture fails with a JSON
  depth error that looks like a client bug. `JsonNode.Parse(raw)!.ToJsonString()` keeps the
  fixture readable in source.
- Mutation-check it: make the client ignore the field and confirm these tests fail.

## 3. Pin anything persisted

When an enum or record is persisted (checkpoints, caches, queues), adding members is a data
migration in disguise.

- Give members explicit values; append only, never reorder.
- One test per value pinning its integer, plus a count test that fails when a member is added
  unpinned.
- One round-trip test through the *real* serializer that asserts the representation (e.g.
  `"StopReason": 5`), so the pins fail loudly if the serializer ever switches to strings and
  stops depending on order.

## 4. Formatter and linter baselines

A repo-wide `--verify-no-changes` run on a mature project often flags dozens of files on
`main` already. Compare against a stashed baseline and check only the lines you changed
(map flagged line numbers against `git diff -U0` hunks); report pre-existing violations as
pre-existing, and note whether CI gates on the tool at all.

## 5. Claims about upstream behaviour

```bash
# file at a tag
gh api -H "Accept: application/vnd.github.raw" "repos/O/R/contents/<path>?ref=<tag>"
# when did a field first appear: bisect tags
for t in v1 v2 v3; do printf "%s: " $t; gh api -H "Accept: application/vnd.github.raw" \
  "repos/O/R/contents/<path>?ref=$t" | grep -c "<field>"; done
# is a declared constant ever assigned
gh search code "<ConstantName>" --repo O/R --json path --jq '.[].path'
```

Prefer the source at the version your project pins; a docs page or `main` may have moved.
