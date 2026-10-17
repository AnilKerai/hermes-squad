# Reviewing a Project's Documentation

Docs are part of the codebase and almost never measured. "Too long" is an opinion;
words-per-line, cross-file duplication, and inventory drift are findings an author can
act on. Run the commands, then report numbers.

## 1. Size and density

Density matters more than size. A file with a high words-per-line ratio is not a document,
it is a wall — one "line" is a 500-word paragraph nobody can skim or diff.

```bash
for f in README.md CLAUDE.md CHANGELOG.md docs/*.md; do
  printf "%-28s %7s B  %6s words  %5s lines\n" "$f" \
    "$(wc -c <"$f"|tr -d ' ')" "$(wc -w <"$f"|tr -d ' ')" "$(wc -l <"$f"|tr -d ' ')"
done
echo "TOTAL doc words: $(cat README.md CLAUDE.md docs/*.md | wc -w)"
echo "TOTAL src lines: $(git ls-files 'src/*' | xargs cat | wc -l)"
```

Compare total doc words against production source lines. Docs approaching the same order
of magnitude as the code is a maintenance load worth naming.

## 2. Longest blocks

Finds the walls. Paragraph-mode `awk` treats a blank-line-separated block as one record.

```bash
for f in CLAUDE.md README.md docs/*.md; do
  awk -v F="$f" 'BEGIN{RS=""} {gsub(/\n/," "); n=split($0,w," ");
    if(n>150) printf "%6d words  %-22s  %.100s...\n", n, F, $0}' "$f"
done | sort -rn | head -15
```

Two blocks of 1000+ words on the *same subject* in different files is the duplication
finding below, already visible.

## 3. Cross-file duplication

The real cost of large docs is not length, it is the same fact maintained in several
places. Pick distinctive technical phrases and count the files carrying each.

```bash
for p in "<DistinctiveTypeName>" "<characteristic phrase>" "<flag or setting name>"; do
  printf "%-46s " "$p"
  grep -rlE "$p" README.md CLAUDE.md CHANGELOG.md docs/*.md 2>/dev/null | tr '\n' ' '
  echo
done
```

Any fact in three or more files means one change costs three or four edits, so drift is
structural rather than unlucky. This is the finding that justifies a restructure — lead
with it, not with the word counts.

## 4. Inventory drift

Any prose that mirrors a directory listing decays, because no compiler checks it and
nobody consults it to learn what exists — they use the IDE. Prove it:

```bash
# types named in the doc's inventory section
sed -n '<LINE>p' CLAUDE.md | grep -o '`[A-Za-z][A-Za-z0-9]*`' | tr -d '`' | sort -u > /tmp/claimed.txt
# types actually present
git ls-files 'src/<Project>/*' | sed 's|.*/||;s|\.[a-z]*$||' | sort -u > /tmp/actual.txt
comm -13 /tmp/claimed.txt /tmp/actual.txt     # present but undocumented
```

Report as a ratio ("names 22 of 33 public types") and name the notable omissions.

## 5. Churn as a readership proxy

```bash
for f in README.md CLAUDE.md docs/*.md; do
  printf "%-24s %4s commits\n" "$f" "$(git log --oneline -- "$f" | wc -l | tr -d ' ')"
done
git log -40 --numstat --format="" -- '*.md'   | awk '{a+=$1;d+=$2} END {print "md:  +"a" -"d}'
git log -40 --numstat --format="" -- 'src/*'  | awk '{a+=$1;d+=$2} END {print "src: +"a" -"d}'
```

Doc lines approaching or exceeding source lines over recent history quantifies the tax.
Files with near-zero churn next to a heavily-churned README are usually unread, not stable.

## 6. Cross-check the changelog against breaking changes

When a project's convention promises a changelog entry for every breaking change, verify
it instead of trusting it. Grep the changelog for the *old* and *new* names of renamed
extension-point members:

```bash
grep -c "OldMethodName\|NewMethodName\|NewRequestType" CHANGELOG.md
```

A zero count where the rename is described only in a roadmap narrative is a real gap: the
rationale went where the story lives and the one file a consumer checks never got it.
This is the most actionable documentation finding available, because it has a victim.

## 7. Backfilling the entry — verify every claim against git

A retrospective changelog entry is guesswork unless each claim is checked, and guesswork
is how the original gap happened. Establish the history before writing a word.

```bash
git log -S "OldSymbolName" --oneline --reverse -- src/   # commits that added/removed it
git show -s --format="%ad %s" --date=short <sha>
git tag --contains <sha> | head -3                       # first release carrying the change
git show <sha>^:<path/to/Interface.cs>                   # the signature before
git show <sha>:<path/to/Interface.cs>                    # and after
```

- **Ask first whether the old API ever shipped.** `git show <earliest-tag>:<path>` for the
  pre-change signature. If it was never public in a tagged release, nobody was broken and
  the entry is unnecessary — this single check decides whether the finding is real, and it
  can flip either way. Only after it confirms a published break is the migration guide worth
  writing.
- **`git log -S` is a pickaxe, not a definition site.** It reports every commit where the
  occurrence count changed, so unrelated early commits surface above the real one. Confirm
  the candidate with `git show <sha>:<path>` before trusting it.
- **Verify each claim against the commit that actually made it.** Changes that shipped in one
  release are frequently separate commits; one commit's `--stat` is no evidence for a
  sibling's rename. Check the file at that commit rather than attributing everything to the
  commit you happened to find first.
- **Write it for the consumer, not the historian:** the before/after signature diff, one
  worked example per usage mode (the behaviour-preserving port *and* the recommended one),
  and the old-to-new parameter mapping. Call out any parameter whose *type* changed, not just
  its name — that is the one that breaks a mechanical rename.
- **Label it as retrospective** in the entry itself and point at the ADR for the reasoning.
  Silently backdating a record makes the changelog's own guarantee untrustworthy, which is
  the problem you are fixing.

When one unrecorded break turns up, assume siblings: audit the remaining extension-point
interfaces the same way, and offer the audit rather than performing it unasked.

## The restructure shape

When the findings above land, propose this rather than "shorten the docs":

- **Separate invariants from archaeology.** An always-loaded instruction file should carry
  only what must stay true, one imperative line per rule, each ending in a pointer. The
  *story* of how a rule was discovered is valuable but must not be resident — an
  always-loaded file is a per-session token cost on every task in the repo.
- **ADRs under `docs/decisions/NNN-topic.md`** for the reasoning: Context / Decision /
  Consequences / Alternatives rejected. Existing long-form prose is **moved, not
  rewritten** — say so explicitly, because an author who spent real effort on that prose
  will resist anything that sounds like deletion.
- **Define Consequences as *costs*, not invariants.** A template that says "Consequences:
  what a maintainer must keep true" asks every ADR to restate the instruction file's
  invariants, breaking the one-fact-one-file rule by construction. Consequences record what
  the decision costs and makes harder; the invariants section points at the instruction
  file. When existing ADRs already duplicate invariants, move the history-of-why into
  Context and cut the rules to a pointer.
- **Verify every version claim in an ADR Status line against the changelog** before writing
  it (`grep -n` the topic, map each hit to its `## [x.y.z]` heading). "Tightened in 2.4 and
  2.5" written from memory is the same guesswork as an unchecked backfill.
- **A roadmap holds forward-looking work only.** Done items with full implementation
  narratives belong in the changelog or an ADR; a roadmap that mostly describes finished
  work cannot answer the question a roadmap exists for.
- **Delete type inventories**, keep the one-sentence role and the dependency rule.
- **A `docs/README.md` index table** — "if you want to X, open Y". Several files with no
  index means the entry point is prose in the root README, which nobody parses.
- **One rule going forward: every fact lives in exactly one file.** Changelog owns *what
  changed and when*; ADRs own *why*; the instruction file owns *what must stay true*; the
  extending guide owns *how do I*. A pointer is cheaper than a copy, and a copy is what
  goes stale. A code comment may carry the one-line why for the line it sits on; anything
  longer goes to the ADR. Check your own new changesets against the rule before committing
  — grep the rationale's distinctive phrase across docs and count files.
- **Moving rationale out of an instruction file can delete a fact.** Diff the old section
  against its new homes and confirm each sentence landed somewhere; "same facts,
  reorganised" is a claim to verify, not assume.
- **An unreleased changelog entry that turned out wrong is rewritten in place**, not
  corrected underneath — nobody has consumed it yet, and a correction appendix leaves the
  wrong instruction first.

Sequence it so the additive files (ADRs, index) land first and independently. Edits to
agent-instruction files need explicit approval and can be refused, so a restructure that
depends on them landing atomically will stall half-done.

## Tone finding, if it applies

Reference prose that argues with an invisible opponent ("every framework surveyed fails
to...", "which is the part not to copy") embeds facts inside advocacy, so a reader
skimming for one behaviour has to read a defence of the design. Separating the claim from
its defence makes both stronger. Raise this last and lightly — it is the softest finding
and the easiest to over-weight.
