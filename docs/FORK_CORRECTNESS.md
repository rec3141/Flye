# Fork correctness investigation

Status: focused regression, scheduled production-like integration,
performance, serial cache-equivalence and serial reproducibility checks
have passed. These changes do **not** promise deterministic parallel assembly.
The unchanged current-HEAD baseline referenced below is revision `88a71ab0`.

## Corrections

| Problem | Correction | Regression evidence |
| --- | --- | --- |
| Seed screening caches a chimera verdict from the first 100, input-ID-ordered overlaps | Use complete overlap evidence; reuse existing cached overlaps and publish newly computed lists only for accepted seeds | Original Extender loses an entire supported 10 kb sequence in one input permutation; corrected Extender recovers it in both |
| Coverage-window rounding gives different chimera verdicts for opposite strands; the first caller determines the cached result | Bin in forward-read coordinates and use one cache entry per physical read | Both call orders and concurrent callers agree across 15 boundary cases; original fails six |
| Equal-length contained disjointigs delete one another when reciprocal overlaps are visited | Use a consistent, strand-normalized ID tie-break; ignore self-strand matches | Duplicate pairs, triples and reverse-complement duplicates retain one representative; original fails four of eight cases |
| Low-coverage tip pruning checks only the right end of an arbitrarily oriented path representative | Check both physical ends | 48 pruning cases pass, including 1.2 Mb tips and coverage-boundary controls; original fails two |

These defects are also present in the upstream-derived code; they are not
evidence that the fork's speedups introduced all the observed output changes.
Corrected tip pruning can remove additional unsupported sequence. More
contigs or bases alone is not a correctness criterion.

Overlap reuse preserves complete-evidence screening rather than replacing
it with a sampled approximation. Rejected uncached seeds do not retain
large overlap lists. Cache publication is first-writer-wins, preserves
references already returned to readers, and counts each cached list once.

## Reproducibility boundaries

Parallel extension still consults `_innerReads` while other workers update
it. A deterministic initial read ordering and a mutex around final acceptance
do not make those earlier decisions independent of scheduling. The existing
`--deterministic` option serializes the assembly stage; it is not a new
low-overhead parallel determinism implementation.

Input-order sensitivity is distinct from scheduling nondeterminism. The
100-overlap fixture fails even with one thread. Correcting that defect does
not promise byte-identical assemblies for every permutation of a read set.

## Evidence concerning issue 1

The production comparison is between `1d380176` and `1efed102`. On the same
saved snowball disjointigs and reads, two 8-thread repeat-stage runs of each
revision retain the same canonical sequence multiset: 5,283 paths and
51,562,567 bases. Old runtimes were 320.67 and 321.36 seconds; new runtimes
were 320.53 and 321.08 seconds. This does not reproduce a large repeat-stage
loss or slowdown, but is not proof of equivalence on every dataset.
Two single-thread repeats of each revision also match that same sequence
multiset; all eight historical repeat controls completed successfully.

The first full-pipeline pair (same reads, eight threads, final polishing
disabled) produced 52,566,076 versus 52,607,304 bases in 1,544.89 versus
1,549.57 seconds. Individual contigs differ; this pair does not reproduce
the historical large loss and does not establish deterministic assembly.
The second runs completed with 52,559,206 versus 52,523,905 bases. Two-run
mean lengths differ by only 0.0056%, and mean runtimes by 0.065%. Within
each revision, the full-run replicates have different canonical sequence
multisets: end-to-end nondeterminism remains in both historical revisions,
despite the reproducible repeat stage on fixed input.

The determinism diff does not edit `src/assemble`, but modifies shared
overlap and disjoint-set code used in contained-disjointig filtering after
extension. It is therefore incorrect to exclude all assembly-stage effects
merely from the directory names in the diff.

The old marine intermediate work directory is unavailable. Its final
megabase contigs remain largely detectable in the newer final assembly:
97.4% of their bases align at >=95% identity and MAPQ >=20, excluding
reference deletions. Most of those old contigs are now fragmented. This
observation concerns the 80 old megabase contigs, not the entire assembly.
MAPQ distinguishes alternatives within that reference subset only.

Equal input base totals also do not prove equal read identities or order.
The production pipeline's streaming target-base filter is order-sensitive;
that is a confounder, not a proven explanation of the historical difference.
No pipeline or production assembly changes are part of this patch.

## Validation

Run `make test THREADS=1` to build and execute all six focused suites.
Details are in [the test README](../tests/README.md).

The user-provided performance gates are approximately +15% maximum overhead
on the default path and +50% for optional determinism. The unoptimized
complete-overlap prototype exceeded the default budget in its two-run mean.
The cache-reuse candidate's two 16-thread assembly runs took 677.06 and
670.29 seconds, versus 774.56 and 777.72 seconds for the unchanged build:
13.2% faster on average, with comparable peak RAM. The corrected runs are
not identical: five versus seven canonical draft sequences differ, with a
34,495 bp difference in total length (~0.012%). This is not a guarantee of
parallel determinism. Serial reproducibility subsequently passed as
documented below.

The first complete candidate pipeline took 1,758.43 seconds versus 1,817.13
for unchanged current HEAD (3.2% faster), with similar peak RAM. Candidate
output has 4,988 contigs / 52,433,687 bases / N50 16,912; current HEAD has
5,034 / 52,665,936 / N50 16,668. The shorter maximum contig is not evidence
of deleting its entire length difference: 99.56% of the historical longest
contig aligns to candidate final contigs at >=95% identity and MAPQ >=20,
excluding reference deletions. Its sequence is largely retained but joined
differently; alignment alone cannot establish which joins are correct.
The candidate's second full run also succeeded: 1,673.94 seconds, 4,992
contigs / 52,442,751 bases / N50 16,941, maximum length 418,678. Its total
length differs from the first by 9,064 bases (0.0173%), but the canonical
sequence multisets differ and maximum contig length changes substantially.
This confirms remaining parallel variation, not sequence-loss equivalence
to the whole lengths of differing contigs. The baseline's second run also
succeeded in 1,752.00 seconds, with 5,021 contigs / 52,554,743 bases.
Two-run mean runtime is 1,716.185 seconds for the candidate versus 1,784.565
for unchanged current HEAD: 3.83% faster with comparable peak RAM. Mean
final sequence length is 0.3272% lower in the candidate; more or fewer bases
alone does not establish correctness. All ten full runs (five versions,
two replicates each) succeeded. Serial cache equivalence also passed:
optimized and unoptimized corrections produced identical canonical sequence
multisets (32,956 disjointigs / 286,298,387 bases). The candidate's second
serial replicate also passed with exactly the same canonical sequence
multiset: zero unique sequences on either side. Both baseline serial
replicates likewise match one another (32,775 / 285,720,932 bases), as do
the early uncapped-seed/tip-only prototype replicates (32,775 / 285,724,702
bases). Jobs 7590794, 7590795 and both 7590785 array tasks completed with
exit status 0. Candidate serial runtimes were 1:36:25 and 1:36:01 versus
baseline 1:52:42 and 1:52:53, with comparable peak RAM. These results
establish reproducibility for the tested serial input, not parallel or
universal determinism, and do not establish the historical marine cause.

On the fixed-input repeat-stage control, all four corrected outputs (two
single-thread and two eight-thread runs) have identical canonical sequence
multisets: 5,258 paths / 51,477,554 bases. This is evidence for that stage
and dataset, not for deterministic parallel assembly end to end.
