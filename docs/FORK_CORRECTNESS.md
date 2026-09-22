# Fork correctness investigation

Status: focused regression tests pass; production-like integration and
performance validation are still in progress. These changes do **not**
promise deterministic parallel assembly.

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
parallel determinism. Serial equivalence against the unoptimized correction
and complete pipeline validation remain required before final acceptance.
