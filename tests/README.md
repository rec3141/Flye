# C++ regression tests

Run all regression suites with `make test THREADS=1`.

For individual suites, build Flye with `make THREADS=1`, then run
`bash tests/run_tip_pruning.sh`.
The test links the production objects and checks 48 paired-strand graphs:
both numerical strand assignments, terminal and internal branches, 10 kb
and 1.2 Mb lengths, below/at/above the coverage cutoff, and both pruning
modes. Both strands must be removed together, and high-coverage edges must
survive. The test fails on the unpatched revision 88a71ab0.

`bash tests/run_seed_coverage.sh` exercises the overlap detector and chimera
cache with identical named reads in two different input orders. Complete
uncached seed evidence must agree with cached extension evidence in both
orders and either call order. The fixture also demonstrates why the former
100-overlap prefix is unsafe. This is a coverage-contract test; it does not
by itself detect changes to the Extender caller or establish end-to-end
assembly equivalence. Use controlled assemblies for that integration gate.

`bash tests/run_seed_assembly.sh` also exercises the actual Extender and
consensus generator. In one input permutation, all 31 copies of a valid
10 kb sequence have 100 partial overlaps ahead of their complete overlaps.
The original build emits no disjointigs in that permutation, but recovers
the sequence in the other order. The fix must recover the exact complete
sequence in either order. This is a small assembly-level regression, not a
production-scale performance or quality test.

`bash tests/run_contained_disjointigs.sh` exercises the production final
assembly filter. Duplicate pairs/triples and reverse-complement duplicates
must retain one representative; unrelated sequences and ordinary unequal-
length containment retain their expected behavior. The original build
fails four of eight cases by deleting every duplicate; the patch passes.

`bash tests/run_chimera_strands.sh` checks 15 read-length/coverage-window
boundary cases in both strand call orders, including eight concurrent
callers on a fresh cache repeated ten times. The original build fails six
cases; the patch passes all cases. Full-coverage controls remain non-chimeric.

`bash tests/run_overlap_cache.sh` checks complete-overlap reuse, concurrent
first-writer-wins publication, stable references, reverse-strand lookup,
empty cached results, and rejection of reverse-strand publication. No
overlap index is built: cached lazy lookups must not recompute overlaps.
