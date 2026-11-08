# Convention convergence in the wiki corpus: results

Pre-registration: [PREREG.md](PREREG.md), committed before this run. Raw output: [results.json](results.json). Script: [convergence.py](convergence.py), 500 permutations, seed 0.

- **Corpus:** 6,051 labelled records. 3,036 have a resolved author handle, giving 1,158 distinct handles. All data is from June 2026 onward, except first-person plurals, first seen in May.
- **Measure:** the exposed share is the fraction of authors whose first use of a token came after they could have seen it. "Seen" means on the same page earlier, or on a page they had posted to earlier.
- **Null:** the same share with record dates shuffled within each page.

| Token | Family | Records | Pages | Adopting authors | Exposed share | Null | Lift | p (one-sided) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| round marker R1–R9 | possibly environment | 1,934 | 337 | 661 | 0.676 | 0.725 | −0.048 | 1.0 |
| timer | possibly environment | 695 | 208 | 401 | 0.621 | 0.639 | −0.018 | 0.97 |
| deadline | possibly environment | 994 | 263 | 515 | 0.631 | 0.660 | −0.029 | 1.0 |
| cooldown | possibly environment | 466 | 177 | 299 | 0.572 | 0.604 | −0.032 | 0.99 |
| confirmed | protocol (S2) | 837 | 275 | 501 | 0.659 | 0.659 | −0.001 | 0.58 |
| relay | protocol (S2) | 1,097 | 297 | 619 | 0.698 | 0.708 | −0.010 | 0.89 |
| signal | protocol (S2) | 385 | 151 | 211 | 0.626 | 0.588 | +0.038 | 0.014 |
| ping | protocol (S2) | 72 | 55 | 59 | 0.356 | 0.321 | +0.035 | 0.21 |
| ETA | protocol (S2) | 104 | 48 | 73 | 0.479 | 0.487 | −0.008 | 0.71 |
| task clock | protocol (S2) | 749 | 256 | 415 | 0.643 | 0.633 | +0.011 | 0.18 |
| cohort | identity (S5) | 1,422 | 372 | 750 | 0.696 | 0.723 | −0.027 | 1.0 |
| collective / peer / swarm | identity (S5) | 62 | 35 | 44 | 0.477 | 0.453 | +0.024 | 0.39 |
| OpenAI/OAI self-name | identity (S5) | 1,465 | 373 | 507 | 0.633 | 0.659 | −0.025 | 0.99 |
| end-of-text signature | identity (S5) | 2,532 | 424 | 868 | 0.706 | 0.734 | −0.027 | 1.0 |
| HOLD / VETO / STOP | governance | 0 | 0 | 0 | n/a | n/a | n/a | n/a |
| must / never / rule | governance | 19 | 14 | 13 | not interpreted (fewer than 20 authors) | | | |
| we / our / us | context only | 1,318 | 409 | 560 | 0.677 | 0.673 | +0.004 | 0.37 |

## Reading, per the pre-stated rules

1. **Convergence in spread: yes.** Identity and protocol conventions are used by hundreds of distinct handles across hundreds of pages: "cohort" by 750 authors on 372 pages, signatures by 868, OpenAI/OAI-style self-names by 507, "relay" by 619.
2. **Transmission on the observed pages: not supported.**
   - No token reaches the pre-stated bar once multiple testing is considered. `signal` has p = 0.014, which does not survive a Bonferroni threshold of 0.05/15 ≈ 0.003.
   - Several identity and environment tokens show a small negative lift (p ≈ 1). Authors' first uses come earlier in a page's history than random ordering would put them. That fits authors arriving already carrying the convention, and with page openers setting the template.
   - This is the pattern the pre-registration reads as independent appearance from a common cause.
3. **Binding governance vocabulary is absent.** The HOLD/VETO/STOP system documented on the ExploitGym board (METR pp. 45–48) appears in none of the 6,051 records. Rule language is rare.

## What this does and does not show

- **Shows:** in this corpus, collective self-reference and protocol conventions are widespread, but they are not learned page by page.
- **Does not distinguish** a shared model or prompt (an outside common cause) from transmission through channels the corpus does not contain. `site-coverage.csv` lists Discord URLs, and there are other wikis and shorteners.
- **Does not show** that an S5 is absent. It bears on where the S5 sits: here, most plausibly outside the observed pages.
- **Does not transfer** to the ExploitGym/Hugging Face incident, which is a different population and period with its own primary evidence (see [../S5_EVIDENCE.md](../S5_EVIDENCE.md)).

Known limits: author handles are unauthenticated and come from the labelling model; half the records have no author; page exposure is a proxy for reading; and the 50-per-page cap trims later adoption on the busiest pages.
