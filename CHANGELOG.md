# Changelog

Changes to the UC Davis Proteomics Core pipeline skill (`ucdavis-proteomics-core-pipeline`).
The entries before 2.15 were written in the DE-LIMP repository
(https://github.com/bsphinney/DE-LIMP), whose CHANGELOG also holds the DE-LIMP app's own entries.

## [Unreleased]

- **The update check says when this computer still updates from DE-LIMP.** Before, a 2.14 copy that updated to 2.15.0 and then ran `/reload-plugins` was told nothing: `skill_version.sh --check-update` found the version current, returned `"moved": true` with no message, and the plugin catalogue stayed on the old repository until a new session started. Now its `say` names the new repository and the command that moves the catalogue (`skill_version.sh --session-start`). The check itself still changes nothing.

## [Skill 2.15.0] — 2026-11-12

2.15 does five big things and then fixes what real data showed.
- **SKILL.md is now a router.** It went from 3,632 lines to 499. It says where to go; the detail lives in the reference files.
- **FragPipe becomes the engine for timsTOF DDA and for non-specific Orbitrap DDA.** Sage stays as the fallback and for ordinary tryptic Orbitrap DDA.
- **The protein screen, part 1** ("show me the data for <protein>"). It has its own section below.
- **Test and synthetic sequences can no longer reach FRAN.**
- **The skill has its own repository:** https://github.com/bsphinney/UCD-Proteomics-AI-Skill. DE-LIMP stays as the app's home. A computer that installed from DE-LIMP gets 2.15.0 from there as usual, and 2.15.0 moves its plugin catalogue to the new repository at the start of its first session, at the same version (`skill_version.sh --session-start`: remove, add the new address, install; the old address is put back if the add fails), and says so in one sentence. It is skipped, with the one-line command to do it by hand, when the new address does not answer, git or claude is missing, or the session runs in Claude Desktop. DE-LIMP keeps its `skill/` folder at 2.15.0 so that older installs can still update. Reports link the new repository's "How these reports are made" page, and their star line names it.

The release was then run end to end, 2.14.2 against 2.15, on seven real datasets: public and Core-style DIA and DDA, from 2 to 300 runs. Those runs found defects, and twelve fix lanes closed them. The results are under "How it was checked".

### What the client sees
- **Non-specific peptidome DDA finds the peptides.** Before, on a public Orbitrap peptidome study, Sage at the skill's 10 ppm window found 179 peptides. The paper reported 14,270. The true matches sit about 8.5 ppm off, at the edge of Sage's window, and Sage does no mass calibration. Now:
  - non-specific Orbitrap DDA (`--enzyme none`, pepsin and similar) goes to FragPipe. Its non-specific workflow searches a wider ±20 ppm window and rescores with MSBooster and Percolator. It does no mass calibration either (`calibrate_mass=0`). It found 16,203 peptides on the same data: it recovers the matches Sage's window lost. This is not a validation. The paper reported 14,270 with different FDR handling, and finding more than a paper does not show the matches are right. This search applies no protein-level FDR (`--prot 1`), and no entrapment or other independent estimate of its peptide FDR was made;
  - `--engine sage` is still honoured and is recorded as "requested";
  - when Sage runs anyway, it checks where the confident matches sit in the precursor window. If the median is in the outer half, it warns with the numbers and writes a copy of the settings with the window centred, in Sage's own sign (Sage's window is calculated minus observed mass, the opposite of the measured offset). It never re-runs anything by itself. The offered window was checked on real data: on 8 runs of the peptidome, Sage's 882 PSMs at 1% with ±10 ppm became 4,034 with the corrected window `[-19, +2]`. So the window was a large part of Sage's loss; that run was not counted in peptides, so how much of FragPipe's lead it closes is not known. (A first version offered the mirror image, `[-2, +19]`, which found 0 PSMs at 1%; it was fixed before release.)
- **timsTOF DDA-PASEF goes to FragPipe.** A two-run chymotrypsin timsTOF HT set gave 6,536 PSMs, 969 peptides and 165 protein groups in 6 min 50 s on 2.15. The same set on 2.14.2 (Sage, a hand-built override) gave 5,756 PSMs and 1,041 peptides. If FragPipe cannot run or is not licensed, Sage runs and the record says it was the fallback and why.
- **Enzymes are real options.** `--enzyme chymotrypsin|none|...` replaces hand-written override files, and `--semi-specific` is new. A semi-specific search's Methods, report and brief say its peptide counts are not comparable with a fully specific search and that some semi-specific peptides may be in-source fragments. A vendor or user FragPipe workflow is never refused for the name in its enzyme dropdown.
- **Honest protein counts for FragPipe identifications.** FragPipe's identifications-only route applies no protein-level FDR. Now the report, the Methods and the analysis brief say so, and give PSMs and peptides, never a protein-group count. The skill's `Cont_` contaminant entries are flagged in `identifications.tsv`, and the share of contaminant PSMs is reported on its own. On one peptidome set a single porcine pepsin entry was 23.5% of the PSMs and had been counted as ordinary. A non-specific search that quantifies (amounts wanted) has no protein-level FDR either: its record now says so, and the brief and report no longer call its protein rows "already FDR-filtered" or give a protein count as a result.
- **Quantities from FragPipe say who made them.** One experiment (FragPipe's grouping of runs) gives IonQuant's intensities; there is no between-run step, so the Methods and report say they are not normalised between runs and runs should be compared with care. Two experiments give directLFQ, because IonQuant's MaxLFQ needs three. Three or more give IonQuant's MaxLFQ. `--directlfq` asks for directLFQ at any count, and the Methods say "requested". A search that cannot resolve fragments (unit resolution) gives identifications only.
- **The Methods tag every default they print.** Before, carbamidomethyl-C, oxidation(M), the N-terminal acetyl, DDA tolerances and the charge range printed as if the client had chosen them, in all six runs of the acceptance round. Now each one reads "[facility default — confirm]" when the search record says it was a default, in the text and in the parameter table. Where no record exists, nothing is claimed.
- **The Methods and report describe what ran.**
  - They count the runs the search used (183), not every file staged (300).
  - They name every species in the database, not only the main proteome.
  - Identifications-only results read "identified", never "quantified".
  - A FragPipe search says its workflow, isotope errors, decoys and protein quantity, read from the records. MSFragger's mass calibration is stated as the workflow's own setting (LFQ-MBR, the timsTOF DDA default, ships `calibrate_mass=2`), not as a "[... — confirm]" warning; its ±20 ppm window is used on timsTOF too, as a starting value.
  - The line about contaminants says the job added none of its own; any are those already in the database.
  - An mzML now gives its instrument model and MS2 analyser (read from the file header).
- **A failed Skyline import is no longer "ok".** Before, one failed import task left "ok" on the peak check, and the Methods, report and MANIFEST said nothing. Now the check is "partial", with a sentence saying which runs it does not cover and why (the Methods, the top of the report section and the MANIFEST all use the same one), and a retry command that re-runs only the failed tasks. A timsTOF `.d` reached through a link is now passed to Skyline by its real path, in the build, the imports and the join (see limitations).
- **Delivery works for part of a plate.** Before, a session that analysed 77 of 96 staged files was refused, and `--force` did not help. Now a session that analysed a subset of the staged files can be delivered. The plan, the client README and the email body say "N of the M submitted files were analysed" and name the files not analysed and not in the share (at most 20, then "and N more"); the raw-folder line says it holds the analysed files' raw data only. Raw links cover only the analysed files unless `--include-raw all` is given. A session holding a file that was never staged is still refused, with the offending files named.
- **A FragPipe search that mixes FAIMS and non-FAIMS runs is refused.** Before, FragPipe's IonQuant crashed after 2.6 hours (about 85 CPU-hours) when one search mixed the two. Now the skill reads each run's FAIMS status, refuses the mix before anything is written, and offers `--faims-split`, which runs one search per group. The check covers FragPipe searches that quantify, and only runs whose status is known (see limitations). Methods, the report and the MANIFEST say the groups are valid but not comparable. On a login node the check reads at most five runs' mzML heads (40 MB); with more unrecorded runs the command moves to a compute node to read them, as the `.d` check does.
- **Fewer wrong or missing words elsewhere.** A no-DE FragPipe report shows distinct peptides instead of table rows. An OUTPUT_FILES list no longer calls MSBooster PNGs report figures. The no-DE AGENTS.md no longer says "Search + DE".

### For staff
- **Memory is sized from the data.** Before, non-specific Sage asked for 192G whatever the database. It peaked at 405 GiB on a 22,939-sequence bovine database and 345 GB on a human one-per-gene database, and the warning gave no number.
  - Sage and FragPipe: the request now comes from the sequence count, from three measured points, with 15% headroom, rounded up to 8 GB. A `--mem` below the estimate prints a note. An estimate above the queue's per-job or per-user memory cap is refused with the numbers and the options (reviewed-only database, a tryptic search, a bigger queue).
  - FragPipe also grows with the run count, and the semi-specific rule follows measured peaks (see "Known limitations" for how narrow that evidence is). The Java heap is the request minus 12G.
  - Sage jobs set `RUST_MIN_STACK`. Exit 134 or "stack overflow" now writes `sage_failure.json` with a re-run hint. The overflow is intermittent: an identical job with the identical binary crashed once and ran once. The stack setting is not shown to prevent it. Only the detection is verified.
  - The Sage binary the Core pins reports "0.14.6" but is byte-identical to the official v0.14.7 release asset. The provenance now records its sha256 and says so.
- **DIA-NN assembly (step 3) is sized from the file count.** Before, 77 files got 48 CPUs and 12 hours for a job that used 2:24 and 5 GB, and sat for hours behind the per-user CPU cap. A single chain job also leaves a quarter of the per-user cap free (a 64-CPU cap gives 48).
- **Watchers and status tell the truth.**
  - `watch_run.sh --out` read no Slurm state and called a failed job "running". It now reads `sacct`, and reports state, exit code and the log tail. A cancelled chain no longer reads as done.
  - A normalisation check that needs a decision no longer shows as a failed Slurm job (`--job-exit0`, with a `NEEDS_DECISION.json` marker).
  - `status` says when `commands.log` is missing; `session.py log-command` writes a line to it. `status` now also prints the full `provenance.py --session` command, which avoids a degraded bundle.
  - Job-end records the queue each job really ran in (`queue_actual`).
  - A cancelled job is now `cancelled` (find out who or what cancelled it), not a cause read from its log: a cancelled FragPipe search read "empty results" from its own count line. "Empty results" now needs a failed job and the engines' own words.
  - Watching the Skyline peak check as a chain (`--out skyline_work`) reads its job ids and its failed job's log; before, each label in `jobs.txt` read as an unknown job and no log was found.
- **Test runs stay out of the Core run records.** `--no-record` on `run_search.py`, the chain scripts and `finalize`, and any session or search path with `/skill_test/` in it, skip all three Core records: the run registry, FRAN staging (the job-end hook stages nothing; `fran_deposit.py` refuses a `/skill_test/` search as `test_run`) and the Core Slack channel (the search-done post and finalize's "analysis complete"). The MANIFEST and `search_provenance.json` say each was off and why. `RECORD_RUN=off` turns off the registry only. `hive_exec.sh --job --preemptible` now takes the low queue; `--session` makes a job traceable to its session.
- **Sessions with several searches.** `session.py choose-search --folder <name>` picks the search a report is built from. Nothing is renamed or marked "superseded". A FAIMS-split session names each group and run count instead of saying "no search output found".
- **Staff commands.** `locate --choose` takes a run label that carries the digest suffix. `stage` lists an existing submission folder it did not use, and `--service-dir` options are named when two folders match. `reproduce.sh` for an identifications-only search rebuilds `identifications.tsv` (`--adapt-only`), submits as a job on a cluster, and carries the added FASTA. `analysis_prompt.py --de-dir` is optional for a no-DE brief. A whole-database `--add-fasta` that already holds the proteome now says what to do instead of "rename". The contaminant overlap check follows `--enzyme`. A FragPipe protein or peptide table counts as a search file in a no-DE delivery.
- **Core client work and the board.**
  - A session can be marked as Core client work (`session.py core-client`, staff only; the login stays in a staff-only log). The client survey and the HT plate sheet match (by sample name, with the as-acquired names shown) follow from it.
  - The Core board is a record, never a gate: no limit on hours, time or posts pauses a session. Any refusal from it means carry on, unless a person paused or stopped the Claude.
  - A Stop hook reminds once when finish items are missing.
- **FRAN guard.** `fasta_guard.py` is the one definition of a database FRAN must never learn: test and synthetic sequences. `fetch_fasta --test-database` marks one. The deposit check refuses a marked database and asks about ones it cannot clear. A session can opt out of FRAN (`NO_FRAN` or `fran: false` in `session.json`). `fran_deposit.py audit` prints the audit SQL (it never connects to PG Farm) and, with `--lance-dir`, scans the Lance spectrum corpus read-only. Databases the skill itself fetched are not held up.
- **Skyline.** Any fixed cysteine modification (not only carbamidomethyl) works in the peak check. The import time limit follows whether Skyline has to demultiplex overlapping windows: 240 minutes then, 60 otherwise (measured 1,658 s against 63 s).
- **Cleanup.** One definition each for sha256, JSON read-or-None and the Slurm binary path. Dead code removed. Reference contents lists regenerated.
- **Identifier guard.** The slim-down's tests now fail on real submission numbers, client names, staff logins and job numbers. They found 61 such items added during 2.14.x. These were anonymised, and the guard runs on every merge.

### How it was checked
Fresh agent sessions ran the same brief on the released 2.14.2 build and on the 2.15 candidate, with the same staff answers. FragPipe-on-request and a public multi-lab beer DDA study (2.15 only) were added. Verdict: no regressions in behaviour.

| Dataset | 2.14.2 | 2.15 |
|---|---|---|
| timsTOF HT DIA, 15 runs: precursors / peptides / protein groups | 85,925 / 75,289 / 9,327 | 85,655 / 75,067 / 9,324 |
| timsTOF HT DIA, 15 runs: significant calls over five contrasts | 1,484 / 197 / 1,559 / 125 / 70 | identical |
| public DIA benchmark (known ratios, 4 m/z windows): significant / false / yeast found | 1,671 / 39 (2.3%) / 84.7% | identical |
| public peptidome, Sage: peptides | 179 | 179 |
| same, FragPipe on request: peptides | - | 16,203 (paper 14,270, different FDR handling; not a validation) |
| 77-run timsTOF HT DIA time course: precursors / protein groups | 10,991 / 849 | 11,150 / 915 |
| same: normalisation check recommends | raw (staff chose normalised) | normalised (as staff chose); why it changed was not isolated |
| same: Skyline runs imported | 76 of 77, loss unreported | 77 of 77 |
| bovine peptidome, full database, Sage | crashed (stack overflow) | completed (needed hand-set 500G); sizing now estimates it |

- **Reading the table.** The two deterministic DIA sets are identical to the call. The 77-run set's DE differs: one contrast went from 30 to 17 calls, and the search found 66 more protein groups. Both DEs used normalised quantities (the staff answer). The cause of the difference was not isolated: it could be the search input, the DE run itself, or both. Nobody re-ran one build's DE on the other build's report.
- **Beer study (300 mzML, FragPipe + directLFQ, semi-specific, no DE).** It first hit the FAIMS crash above. It was then run as four searches (Orbitrap or ion-trap MS2, with or without FAIMS: 183, 36, 58 and 23 runs; 70,081 peptides and 3,976 protein groups in the largest). Against an earlier Sage session on the same database, PSMs were 30% (Orbitrap) and 55% (ion trap) higher. Different engines, so a soft comparison.
- **Fixed in this round:** the FAIMS crash; FragPipe memory too small for 58 to 219 runs; a split session that could not be reported at all (it can now, one group at a time; see limitations); the Sage memory and crash handling; the failed-Skyline "ok"; the plate-subset refusal; the watcher that called failures "running"; the untagged defaults.

### Known limitations
- **One report per FAIMS group.** When a search is split by FAIMS, each group has its own search, and the report, Methods and finalize are built for one group at a time (`choose-search`). There is no single combined report. `deliver --mode interim` links every search folder if both groups must go out.
- **Semi-specific FragPipe memory was measured on one database.** The four measured points (23, 36, 58 and 183 runs) all come from one semi-specific database of about 12.7k sequences. A much larger semi-specific database is covered only by the Sage-based estimate. Each point is a peak of a job whose Java heap was set to 244G, so a peak is not a pure need.
- **FragPipe memory beyond the measured range is an estimate.** The slope past 183 runs is extrapolated. The 219-run attempt hit its 200G ceiling, so it gives a lower bound only.
- **A FAIMS group can hold a whole condition.** `--faims-split` prints runs per condition and group from the session's `conditions.csv` and warns, without refusing, when a condition lies wholly in one group: a comparison with the other group would be a FAIMS difference. With no `conditions.csv` yet, `faims_split.json` says this was not checked.
- **Mixed FAIMS voltages inside one group are untested.** Whether IonQuant quantifies runs with different compensation voltages together was not tried. A FAIMS group with several voltages may need splitting by voltage.
- **The FAIMS mix check covers FragPipe only.** DIA-NN and Sage searches are not checked for FAIMS mixing, and an identifications-only FragPipe search may run mixed. Runs whose FAIMS status is unknown are not counted by the check: a set of known and unknown runs passes with a note.
- **A `.raw` file is only called FAIMS if step 2 recorded it.** `run_search` does not read the scans itself, so an unrecorded `.raw` is "unknown": ignored by the mix check and refused by `--faims-split`.
- **Q Exactive mzML with 3 to 4 Da isolation windows can show acquisition "unknown".** The width rule is ambiguous there, and the classifier does not guess. The instrument now shows, so staff can answer the question knowingly.
- **`--semi-specific` is tested on presets and records only.** No real FragPipe or Sage run used it yet. Its Methods wording is tested, its search is not.
- **Chymotrypsin and the default trypsin FragPipe presets are written as FragPipe's own named dropdown rows.** This was checked against FragPipe 24.0's source, not by loading them in FragPipe. The default trypsin preset changed name and dropdown from "nonspecific" to "trypsin".
- **Sage precursor-window check only warns.** It never re-runs the search: staff run the offered command and compare. The 0.5 edge fraction is a heuristic. The corrected window was verified in PSMs on one peptidome (above), not in peptides or on a second dataset.
- **Already-normalised engine quantities get a second, quantile step.** With `--between-run auto` (the default), directLFQ, IonQuant MaxLFQ and AlphaDIA quantities, which are already normalised between runs, are quantile-normalised again in the DE. This was not benchmarked for these engines; on DIA-NN's normalised quantities the same pattern gave many wrong calls (2.14.2). The Methods name both steps; `--between-run none` skips the second. Planned for 2.16 (`references/de-analysis.md`).
- **Skyline on timsTOF dia-PASEF `.d` reached through a link.** On HIVE the build and the imports worked with linked runs; the join failed until it too used the real path, and the same runs by their real paths reached "ok". The fixed join was not re-run on linked runs. The retry command was never submitted on HIVE. After a failed build the plan still exits 0 and the dependent join stays pending.
- **Some sizing rests on one measurement.** DIA-NN step 3's time comes from 77 files at 48 CPUs, scaled linearly. Step 5 keeps its old size.
- **Not changed.** The ion-trap fragment tolerance stays 0.6 Da, as in FragPipe 24.0's own ion-trap workflows. `provenance` still fingerprints all staged files, which took 33 minutes on 300 runs.
- **The `commands.log` is written by the agent, not by a script.** Nothing in the skill wrote it before; the new `log-command` helps but does not force it.
- **Watcher, two small gaps.** After a Skyline `retry`, the original failed import job is still listed, so watching the whole chain (`watch_run.sh --all`) reports it as failed. A FragPipe DDA job's watcher narration still uses the DIA wording (`pipeline_notes.py`).
- **Not run on HIVE:** the Skyline `retry` command, the join on linked runs after its fix, `queue_actual`'s unavailable branch, and Sage's stack-overflow path (only detection is tested, with a fake Sage).

### Checked on HIVE after the merge
The merged fixes were run on real HIVE jobs and data (small subsets, about 17 CPU-hours on the free low queue):
- **Contaminants:** on a real FragPipe result, all 820 contaminant peptides matched an independent recount. Most flagged PSMs are flagged because a shared human, bovine or mouse protein in their mapped list is a contaminant entry.
- **Sage memory and crash handling:** the job script sets `RUST_MIN_STACK`; a full bovine peptidome search asked 424G from the database size and used 345 to 351 GiB.
- **FragPipe 24.0 presets:** the default DDA preset (now named trypsin), an explicit trypsin preset and a chymotrypsin preset all load in FragPipe.
- **`--semi-specific`:** a real FragPipe run searched one enzymatic terminus (94 of 134 PSMs semi-specific) and a real Sage run had `semi_enzymatic` on; the Methods said semi-specific in both.
- **Watchers:** `watch_run.sh`, `queue_actual` and the normalisation check's decision marker read real Slurm records correctly. Three defects found there were fixed before release: a cancelled FragPipe job read as "empty results", the Skyline logs were not found, and a job label was read as a job id.
- **Skyline with linked `.d` files:** the build and imports worked; the join failed until it used the real path too (fixed; see limitations).
- **Sage precursor window:** the first version offered a window mirrored the wrong way, which found nothing; corrected before release (see "What the client sees").
- **FAIMS check on a login node:** it read only file headers, but with no total limit; it now reads at most 40 MB there and moves the rest to a compute node.

### The protein screen ("show me the data for <protein>"), part 1

#### What the client sees
- **A page for one protein.** Gene, accession and name, the protein's change and adjusted p-value in the chosen comparison, how many runs found it per group, the precursors behind it and the DIA-NN report rows with the checks each failed, how much each precursor shapes each sample's protein value, the chance limpa gave each precursor of being found, and how limma weighted the samples. Facts about the protein come from UniProt, NCBI, HGNC, Ensembl and the Human Protein Atlas, looked up when the page is made and shown as each source wrote them, with release, date and link; nothing comes from the AI's memory. The page makes no network request. Not in this part: peak traces (XICs), the second-opinion check routes, FRAN facts, tracing the report's numbers, and delivery with the results.
- **The top N changed proteins.** A list page linking each protein's page: the proteins the comparison calls changed (adjusted p-value alone, no fold-change cut), best first, at most 100; fewer called than asked is said on the page.
- **Which analyses get it.** Part 1 covers limpa DPC-Quant over a DIA-NN report (native, or FragPipe's DIA route) with a plain group design. Every other route is refused with its own name, read from the analysis's own record: DIA-NN MaxLFQ + limma, an engine's own protein quantities (FragPipe IonQuant, directLFQ, AlphaDIA, Radiant), Sage's highest-peptide route, SILAC, a limpa DE over another engine's report, and blocked or covariate designs. The page builder then makes no page and says which route the analysis used (`references/protein-screen.md` "Which analyses part 1 covers").

#### For staff
- **Step 8g builds the screen data** (`make_screen_data.R`, on a compute node and on the DE's CPU family, `--constraint` when submitted) into `output/screen_data/`: a checksummed manifest, an index and gzipped parts. limpa's refit must reproduce the delivered values to 1e-6; a protein that does not is withheld with the reason. 8,500-10,300 proteins took 106-155 s on PXD063416 (zen2, 8 CPUs). It reads the report the DE read, wherever the session keeps it (`de_provenance.json` `input`, checked by its sha256), and the manifest names that file.
- **`make_protein_screen.py`** builds the page anywhere (Python only) and checks every file against the manifest first. SKILL.md routes "show me the data" to `references/protein-screen.md` (commands, the never-from-memory rule) and step 8g to it; `references/protein-card-sources.md` lists the fact sources. Design: `docs/specs/protein-data-screen-design.md`.
- `run_de.R` takes its CPU-family record and `file_sha256` from the new `compute_record.R`, shared with `make_screen_data.R` (one definition each); `protein_ids.py` gains `strip_isoform` and `first_accession`.

## [Skill 2.14.2] — 2026-11-04

A Core analysis of two timsTOF DDA-PASEF runs went off the skill's standard path. Sage refused the `.d` files, and DIA-NN's `--dda` second pass crashed. The analysis was then delivered as a plain hand-made report, with no reproducibility bundle, no Methods and no AGENTS.md. Two more sessions ended the same way: a re-analysis with no DE, and three HT-plate submissions that stopped at search QC.

2.14.2 makes that path work:
- Sage reads a `.d` for identifications, and converts it for quantification.
- A crashed DIA-NN second pass falls back to the complete first pass.
- finalize now ALWAYS makes the Methods, the bundle, AGENTS.md and the README, for every analysis, with or without a DE.
- The podcast refuses to go ahead without the skill's own report and Methods, and the delivery and the announcements refuse without finalize's stamp.
- Every reader finds the search the DE read, wherever it is.

The release also carries the fixes from the staff reports of 20 October to 2 November. Each area was reviewed and verified separately. After every lane had merged, two more things drove a last round of fixes:
- six independent reviews: biology, proteomics, statistics, errors and UX, documentation, security;
- a run of the two-run DDA case, end to end on the 2.14.2 build, by a fresh agent session.

The DDA, non-specific, MaxLFQ and peak-check changes were checked on real data on HIVE.

2.14.1 (below) was never released on its own. Its two additions ship with this release, and its entry stays as written.

### What the client sees
- **Fewer wrong calls on the MaxLFQ route.** Before, `run_de.R --method maxlfq` put a quantile step on top of DIA-NN's `PG.MaxLFQ`, which DIA-NN had already normalised across runs. On the public PXD063416 benchmark that gave 60.9, 76.1 and 76.9% wrong calls at 4, 6 and 10 m/z windows.
  - **The cause:** mainly the quantile step itself, not normalising twice. On this benchmark whole species shift between runs. Even on quantities DIA-NN had not normalised, the quantile step alone gave 46–72% wrong calls at 4–10 m/z.
  - **Now:** the default (`--between-run auto`) adds no step to a `PG.MaxLFQ` that DIA-NN normalised. The wrong calls are 4.5, 6.4 and 4.4% (at 2 m/z, 3.3% instead of 4.9%).
  - **Still quantile:** a `--no-norm` search's `PG.MaxLFQ`, and another engine's declared quantities (Sage, FragPipe). For FragPipe and AlphaDIA, the Methods name the engine's own normalisation first (IonQuant's, AlphaDIA's directLFQ, or "not recorded — confirm"), then the DE's step.
  - **Unchanged:** `--between-run quantile|median|none` still chooses a step explicitly, and the Methods say which step ran and why. limpa DPC-Quant, the default DE, is not affected.
- **Fold changes point the right way when the controls are recorded.** Before, a session with its control groups recorded (`experiment_type.py set --controls`) still compared groups alphabetically. A TurboID study got IgG minus bait, with every sign flipped, and the normalisation check said "no --controls were recorded". Now:
  - every printed step-8 command carries `<group>-<control>` contrasts, and contrasts given by hand still win;
  - `run_de.R` run by hand with no `--contrasts` in such a session is refused, naming the `--contrasts` to use;
  - the check's note tells a reversed contrast apart from a missing one;
  - `reproduce.sh` replays the contrasts the DE actually ran, read from its record. A different `provenance.py --contrasts` value is named in a MANIFEST NOTE.
- **The Methods name the right maker, LC and mode, and tag what they cannot know.** Before, several statements were wrong or untagged:
  - an mzML from a Bruker impact II was called "Thermo Fisher Scientific";
  - another lab's data got the Core's PepSep column and CaptiveSpray emitter;
  - a Thermo `.raw` got the Bruker column and "not recorded in the .d";
  - the session's recorded DIA/DDA mode was still marked "confirm";
  - outside data read "performed at the UC Davis Proteomics Core", untagged.

  Now the maker comes from the instrument name, and an unknown one reads "[vendor — confirm]". The Core's LC defaults apply only to a Core timsTOF `.d`. The mode comes from `--acquisition`, then the workflow manifest, then `input/acquisition.json`. Outside data's Core acknowledgment is tagged "confirm". `references/methods.md` and step 9d list every tag, and an unresolved tag is never replaced with a guess.
- **The Methods describe the search that ran, wherever it is.** Before, finalize looked for the search only in `output/search/`, so a search in `output/search_dda/` got no search paragraph. The Methods also said DIA-NN "optimised it automatically" for a mass accuracy pinned at a fixed ppm. Now the Methods take the search the DE read (see "Searches find their record"), and with none chosen they give tagged blanks and say why. "Optimised automatically" is written only when the run's record says so; otherwise the Methods say "measured before the search and pinned", or "not recorded".
- **Non-specific and FragPipe searches are described as they ran.** Before, the Methods of a FragPipe search said "No fixed modifications were set. No variable modifications were searched" when five were searched, and left the tolerances and FDR blank. A non-specific Sage search got a proline rule it never had, and "[enzyme name not mapped]". Now:
  - **Sage:** the digestion, the modifications and the tolerances come from Sage's own `results.json`. The digestion reads "no enzyme specificity (non-specific search)", semi-specific, or no digestion. Sage's LFQ route gets its own FDR sentence.
  - **FragPipe settings:** they come from `fragger.params`: fixed and variable mods (a mod on several sites is read site by site), tolerances, Met clipping, mass offsets and labile settings. The Methods also name the database MSFragger searched, with its entries, decoys and sha256.
  - **FragPipe's Philosopher filter:** it is stated as FragPipe's log shows it ran, because FragPipe can run a different filter from the one its workflow states. With label-free quantification on, FragPipe 24 ran `--prot 0.01` where the workflow says `--prot 1`. The scope is given per level: PSM, ion and peptide within each experiment, and protein over all runs when one protein inference was read. A FragPipe DE's Methods state the same filter. A FragPipe DIA DE's Methods do not print it beside DIA-NN's q-values.
  - **Any engine:** a setting no record holds reads "not recorded — confirm", never "none".
  - **Enzyme names:** the Methods and the SDRF name the common enzymes (chymotrypsin, Lys-C, Arg-C, Asp-N, Lys-N, semi- and non-specific) instead of "[enzyme name not mapped]".
- **Identifications-only results are labelled as such, and never called quantified.** Before, the client README and email said an identifications-only search had "identified and quantified" the proteins. Now:
  - one reading of the search record decides, for the README, the email, the folder rows and the DE gate;
  - the report page itself says "identifications only: no quantities, no differential expression", with the identifications per run;
  - the README and AGENTS.md name `identifications.tsv` and how it was filtered;
  - the Methods say how a timsTOF `.d` went into Sage (read directly, or converted with the pinned ProteoWizard and its options). They give the identification rule (rank 1, spectrum and peptide q ≤ 0.01) instead of "Identification FDR: not recorded".
  - for Sage, the Methods also say that no protein-level FDR filter was applied to the list. They give how many of the listed protein groups pass Sage's protein q ≤ 0.01, and each row carries its `protein_q`.
- **A DIA-NN `--dda` first-pass result is labelled as one.** When the skill falls back to DIA-NN's first pass (see the DDA section), the results are said to be the first-pass report, identified without match-between-runs. That is said:
  - on the report page itself;
  - in the Methods and AUDIT.md (a WARN);
  - in the run registry, the job-end Slack post and `checkpoint status`.

  The parameter table says "Report quantified: DIA-NN's first-pass report" instead of "Match-between-runs: on". When that report has no engine protein quantities, the search paragraph says so. The sentence that limpa DPC-Quant estimated the protein quantities from the precursors appears only when a DPC DE ran. A Methods with no DE never claims it.
- **Contaminant-identical proteins carry their own species.** Before, a yeast ADH1 in a human + yeast search was called a "Homo sapiens" protein, and a yeast TPM2 entry flagged human TPM2 by its gene symbol. Now each hit is named by its own organism, in AUDIT.md and in the sample-quality panel. It is matched by accession first, and by gene symbol only within its own species (NCBI databases match by accession only). Databases built before 2.14.2 take the species from their entry names.
- **The heatmap says when it is not differential.** Before, with fewer than 5 proteins passing, the heatmap showed the most variable proteins under the title "top 50 differential proteins". Now the title and caption say "most variable" and how many proteins passed. They also say the proteins were chosen by variance, not by the DE test.
- **No raw tool output in the report.** Before, the tool's raw sample-quality or audit block (z-scores, run file names, developer notes) was left beside the report's own section whenever that section was numbered ("## 9. Data Quality Notes", "## 10. Audit & caveats"). At least one delivered report carried both. Now a numbered heading replaces the raw block, as an un-numbered one already did.
- **A report with no DE reads as one.** Before, a search-only analysis was briefed and documented as a differential-expression analysis: the brief sent the writer to DE files that did not exist, and never to the identifications.
  - **The analysis brief** is now titled "identification and QC (no differential expression)" and is built from the search's own files: `identifications.tsv` and its record, or the search report. It has no significance rule, contrasts, volcano or DE tables. Its sections are identification depth per run, QC, notable proteins (presence only) and how the analysis works. With two or more conditions it says that differences between them are not tested: with one run per condition they cannot be told from run-to-run variation, and in DDA a missing protein is not shown to be absent.
  - **The README and AGENTS.md** fold the DE rows into "Differential expression: none in this analysis", and the review checklist asks whether no DE was wanted.
- **The peak check runs on more searches, and ships only when it is finished.** Before, two kinds of search never got a peak check: one without fixed carbamidomethyl-C (unalkylated or client-prepared samples) was skipped, and every 5-step-chain search failed to build one. A skipped check still shipped a `skyline/` folder holding only its record, the README described pictures that were not there, and the email promised them. A skipped check on a Sage or FragPipe search also told the client that "the quantities in this report are DIA-NN's". Now:
  - an unalkylated search clears Skyline's default modification, and a chain search links its own library;
  - `skyline/` ships, and the README, the Methods and the email name the Skyline document, only for a finished and current check;
  - a check that is not part of the report reads "Not part of this report." with one neutral sentence: the right engine, no paths and no task for staff. A delivery then leaves `skyline/` out. MANIFEST.txt says why;
  - the Methods name the search's variable modifications and what Skyline did not carry over (N-terminal Met excision), and say "cysteine unmodified" only when it was.
- **No Core-internal files in a delivery.** Before, an interim delivery copied whole search folders, scheduler logs included: node names, paths with the HIVE login, the job-end hook's lines. It also copied `fran_deposit.json` (the login that staged the search) and the LFQ record naming, by login, who accepted an LFQ window. Now:
  - scheduler logs (`<job>_<id>.log`, `slurm-*`), `fran_deposit.json` and `node_faults.json` never leave the Core, in any delivery mode or in the session zip;
  - a record naming who accepted something is delivered with the role, in deliveries, the zip and the PRIDE deposit's copy;
  - a DIA-NN search's `input_links/` (links to whole `.d` runs) is scratch, not a second copy of the raw data.
- **README links that work in Bioshare.** Before, README.md used relative links, and README.html linked folders; both break inside Bioshare. Now README.md lists plain file names, the podcast item included. README.html links files only, and a folder is linked through its first file.
- **Raw files under their corrected names.** Before, a raw-only delivery named each share link after the instrument's original (wrong) file name, not the name staff had corrected when staging. Now the staged name is used. A link with no usable name is SKIPPED, with the reason.
- **No internal logs in the session zip.** Before, `finalize --zip` packed most of `logs/`: expert reviews, job logs, and a QC output carrying the staff-only verdict. Now the zip leaves `logs/` out, except `logs/commands.log`. In that log, staff names are replaced by the role (`<Core staff>`), and `--override-by` is replaced by `<redacted>`.
- **limpa 1.4's `NPrec` column is explained.** Before, the column glossary said "NPrec — no description recorded". Now it says the column counts the precursors that quantify the protein (`NPeptides` before limpa 1.4), and the analysis brief quotes the column the table really has.

### For staff: finishing a session
- **Golden rule 9: stay on the standard path, and finish.** SKILL.md has a new golden rule. Leave the standard path only when it is clearly better. When you do, record why with `log_decision.py` at that moment, and still run the finish steps: the report (9), Methods (9d), the bundle (10), finalize (12) and, for a Core submission, deliver (12b). Before telling the user an analysis is finished, run `session.py status --session <session>` and show its result. The rule gives the form for a HIVE session run from a laptop.
- **The finish steps refuse a report the skill did not write.** Before, a hand-made pandoc report copied into `output/` went through the podcast, the delivery and finalize. Now `make_analysis_html.py` records each report it writes in `report_provenance.json`, with its sha256. Each step then checks what it needs:
  - `make_podcast.py` (`check`, `link`, `share`, `job`): that report and the Methods;
  - `deliver` (analysis and no-de modes): the report, the Methods, the bundle and the finalize stamp;
  - `bioshare send`, `email-draft` and `notify_slack.py analysis-done`: the finalize stamp;
  - `board.sh`: warns only.

  A report from before 2.14.2 (it has the old footer) passes with a warning, and a raw-only delivery is never gated. On the laptop route, `report_provenance.json` goes back to HIVE with the report; without it, the steps there would take the report for one made before 2.14.2. Each refusal lists every missing item with the command that makes it. `--override-finish "<reason>"` goes ahead and records the reason in delivery.json and its MANIFEST, in MANIFEST.txt and the stamp, or in podcast.json. `references/core-submissions.md`, `podcast.md` and `notifications.md` describe the gates.
- **finalize stamps what it made.** finalize's last act is `output/FINALIZED.json`. It holds the skill version and the time, and the sha256 of each of these (or `[SKIPPED] <reason>`): AGENTS.md, the README, the Methods, the bundle's manifest, the report and MANIFEST.txt. finalize refuses to stamp when any of these was not made, and ends with one hint per missing document: the exact `provenance.py` command, or for `--methods` the `cp` into `output/methods.md`.
  - A stamp counts only while nothing it stamped has changed. `session.py docs` run after finalize makes it stale.
  - An override or a stale stamp is never reported downstream as finalized. deliver records `finalized` only for a current stamp. The email draft says NOT FINALIZED and `bioshare send` warns. A finalize that does not stamp is not logged as finished in the run registry.
  - A refused finalize removes the earlier stamp, unless the refusal was a mistake in its own command.
  - An empty methods.md or a broken run_manifest.json no longer passes.
- **finalize makes the bundle.** Before, a session that skipped step 10 stayed without a bundle. Now finalize builds the bundle when it is missing or out of date (the DE, the search report or the conditions changed). It reads step 10's flags from the session's records, with the contrasts from the DE record, and leaves out any flag that has no record; MANIFEST.txt says what was left out. It refuses only when there is no raw-file list or no record of what ran, and then names the exact `provenance.py` command.
- **`reproduce.sh` replays what ran.** Before, the bundle's step 5 re-derived the search settings, so a Sage search was replayed with `--params ./wf/` (a folder), losing its overrides, `--ids-only` and its enzyme. Step 6 ran a DE that never happened, with a literal `<method>`. Now:
  - step 5 searches with the cfg the search ran with, copied into `inputs/`; for FragPipe, its workflow without the database line;
  - with no DE there is no step 6, and REPRODUCE.md describes the analysis as it was;
  - finalize takes `--params` from the search's record;
  - the bundle also fingerprints the search's outputs and record, so a changed output makes the bundle stale;
  - finalize warns when `logs/commands.log` is missing or older than the analysis.
- **finalize for every analysis, with or without a DE.** Before, finalize was read as a DE step, and sessions with no DE ended with no AGENTS.md, README, Methods or bundle. Now a session with no `de_provenance.json` gets the same documents, built from its search records, and MANIFEST.txt lists each DE-only part as `[SKIPPED]`.
- **`session.py status`, the finish checklist.** `session.py status --session <S>` (or `--dir <S>`) lists each finish item as done, or as "missing" with the command that makes it:
  - the skill report, the Methods and the bundle;
  - AGENTS.md and the README;
  - the saved conversation and the finalize stamp;
  - for a CoreOmics submission, the delivery.

  It exits 0 when everything is done and 3 when something is not. A submission stays at 3 until step 12b delivers it. With anything overridden or waived, it says "Complete, with N overridden/waived: …", never that every item is done. A delivery made under an override reads "overridden"; one of an earlier finalize reads "stale". SKILL.md gives the runnable command at golden rule 9, steps 12 and 12b, and the laptop finish list.
- **The conversation is saved before finalize.** Before, finalize never warned when a Claude Code analysis had no saved transcript. Now finalize tries once to save the conversation, and refuses if it is still not saved. `--no-transcript "<why>"` waives this and writes the reason to MANIFEST.txt. On HIVE:
  - a session whose transcript the laptop already saved passes;
  - a session with only its decisions log, and no record of a Claude Code session, passes with an INFO line.

  `save_transcript.py <S> --check` (or `--hive <S> --check`) tells you, from the laptop, whether the conversation is saved. When it is not, it prints the save command and exits 3.
- **Hand-written documents are kept.** Before, `session.py docs` and finalize overwrote a README.md or AGENTS.md written by hand, so at least one session avoided both. Now such a file is never changed. The same goes for one the skill wrote and someone then edited, init's starter included: the skill records what it wrote in `logs/skill_docs.json`. The skill writes its own `README.skill.md` / `AGENTS.skill.md` beside the kept file, and MANIFEST.txt says so.
- **Work done outside the session goes in with it, and nothing secret goes with it.** These finalize flags copy outside work into `output/custom/<kind>/<name>/`, checksummed and listed in the README and AGENTS.md:
  - `--code-dir <dir>` and `--extra-dir <dir>` (each repeatable);
  - `--methods <md>`;
  - `--report <html>`. A report the skill did not write also needs `--override-finish`, and the README calls it custom.

  These are left out, whatever the case of their names, and named in a `[NOTE]` line that step 12 relays:
  - key and credential files: the skill's own token files, `*token*`, `*.key`, `id_*`, `.netrc`, `.pgpass`, shell histories;
  - folders: `.ssh`, `.aws`, `.config`, `.gnupg`, `.kube`, `.docker`, `.claude`, `.venv`, `node_modules`, `.git`;
  - any file in which a secret is found.

  These are refused: a folder that is a home folder or holds one; a folder or file inside a session's `logs/`, `input/` or `output/`; a `--report` or `--methods` file holding a secret. A file too big to read for secrets is named as unread. Copies are made whole first, so a failed copy leaves no partial one in the zip. A project's own reproducibility package is in addition to the bundle, never instead of it.
- **An interim delivery before the report.** Before, staff copied the raw files and search folders to the share by hand, which skipped the QC check. Now `core_submission.py deliver --mode interim` does it, behind the same QC check, and needs no report, Methods or stamp:
  - it links the raw files under their staged names, and copies every search folder, wherever its record is;
  - it leaves out a search's mzML conversions, scan-window probe, Radiant library, input links and half-written files, and every Core-internal file;
  - its README, MANIFEST and email draft say what is still owed, and promise quantities only for a search that quantified;
  - `delivery.json` `owed` keeps `session.py status` open until a later no-de or analysis delivery. A raw-only re-send carries the owed items forward.
- **The podcast warns when the session is not finalized.** `make_podcast.py share` and `link` warn, without refusing, when there is no finalize stamp. An email draft made without `--delivery` is marked as unchecked.
- **The no-DE route is signposted.** SKILL.md steps 3 and 4, and the top of step 8, now say that an analysis with no DE is not done after the search. That covers a detection question, an ID list, a QC run, one sample per condition, and a re-analysis or benchmark.
  - **The steps:** the route skips 8–8d and 8f (Core runs still do 8e), then runs 9 → 9d → 9e → 11 → 12 (finalize) → 12b (`deliver --mode no-de`).
  - **One rule for its search:** a Sage DDA search is identifications only (`--ids-only`) unless amounts are wanted (abundance between runs, an intensity table, a DE later). Ask once if the request does not say, log the choice, and confirm it at step 4.
  - **The detail** is in the new `references/no-de-route.md`.

### For staff: DDA searches
- **Sage reads a timsTOF `.d` for identifications.** Before, the Sage route could not take a `.d`: the bioconda msconvert has no Bruker reader. Now `estimate_params.py --ids-only` writes a Sage cfg with `quant.lfq` false, and Sage 0.14.7 searches the `.d` directly, with no conversion. `.raw` still goes through ThermoRawFileParser, and mzML goes straight in.
  - `--adapt-only` writes `identifications.tsv` and `sage_identifications.json`, and no `report.parquet`. The table has one row per run and peptide, for target PSMs of rank 1 with spectrum and peptide q ≤ 0.01, each with its `protein_q`.
  - The DE refuses an identifications-only search with the reason, and deliveries take the identifications.
  - On HIVE, on the two-run DDA submission, this found 896 peptides, and 143 proteins at Sage's 1% protein FDR. The identifications table lists 198 protein groups, each with its `protein_q`. That matches a hand-run Sage search of the same `.d`.
- **Sage quantification of a `.d` converts in the job, with the Core's pinned ProteoWizard.** A cfg written without `--ids-only` (a DE study, or a no-DE one whose user wants amounts) quantifies. Its job converts each `.d` on the compute node with msconvert 3.0.26266 from the pinned Skyline container, and checks the container's sha256 before the first conversion. The conversion combines ion-mobility spectra and sums scans, as the Core's Windows msconvert does.
  - **Without those two options** (found on HIVE before release), the conversion gave 11 million spectra a run, 86 GB for the two runs, and Sage found nothing.
  - **With them, on the same runs:** the two runs convert in about 20–25 minutes. Sage identifies 753 peptides, with LFQ intensities identical (r = 1.000) to Sage's on the Core's Windows-converted mzML. But the quantified report keeps only 65 precursors in 34 protein groups: Sage 0.14.7's MS1 quantification on this data covers a small share of what it identifies (see the LFQ check below).
  - **Refusals:** a missing container is refused, naming the two ways out: convert first with a vendor msconvert, or search with `--ids-only`. A path that apptainer cannot bind (one holding `:` or `,`) is refused.
  - **Re-runs:** `--pwiz-sif` is recorded, and re-runs and `reproduce.sh` replay it.
- **The Sage `.d` route is guarded.**
  - The cfg decides the route, so an unset or unreadable `quant.lfq` with a `.d` is refused.
  - Quantifying a diaPASEF `.d` with DDA settings is refused, with DIA-NN named as the way.
  - An empty result is refused (exit 2), never written as a 0-row report.
  - One run-name rule serves the duplicate check and both adapters.
  - Generating a search sets the other route's outputs aside.
  - A refusal leaves no empty folder.
- **The Sage LFQ check.**
  - It warns, with the numbers, when the quantified report keeps fewer target precursors than 10% of the target peptides identified at 1% (a warning, not a gate). AUDIT.md says what that means for the results, in the client's words, and names the protein groups; the staff's next step is said to staff only.
  - It says when nothing was identified or measured.
  - It runs with the pipeline env's Python. Before, the job's Python had no pyarrow, so the check could not run.
  - Its printed re-run command keeps the search's `--mem`, `--time` and `--pwiz-sif`, and its job-end choices (`--no-notify`, `--no-fran`, `--not-qc`).
  - The re-run's config carries the parameters' record, so its Methods keep the cysteine sentence.
- **A DIA-NN `--dda` second-pass crash falls back to the first pass.** Before, when DIA-NN 2.7.0's `--dda` second pass (match-between-runs) crashed, the search failed with no report, although DIA-NN had written a complete first-pass report. Now, for `--dda` only, the job:
  - copies the first pass, with its stats and precursor matrix, to the report's names;
  - records `report_used: first_pass` and its sha256 in `dda_first_pass.json` and `search_provenance.json`;
  - goes on, and the watcher reports the search done, with a caution.

  A final report is never replaced, and a crash with no first pass still fails. A resubmitted search starts from its own record, so a second pass that then succeeds is not called a fallback. A DIA search's job script is unchanged. On HIVE the two-run submission's second pass crashed again (exit 132), and the fallback ran end to end. Such a search is still handed to FRAN, with `report_used` in its manifest.
- **`--method maxlfq` refuses a report with no protein quantities.** DIA-NN's `--dda` first-pass report has `PG.MaxLFQ` = 0 in every row. On it, `--method maxlfq` stopped with a misleading "fewer than 2 usable runs survived the filters". Now the fallback records `pg_maxlfq: absent`, and maxlfq refuses by name and points to `--method dpc`. DPC reads the precursors and is expected to be unaffected.
- **FragPipe DDA never writes into the raw folder.** Before, four things went wrong:
  - MSFragger wrote about 1 GB a run of `_uncalibrated.mzML`/`.mzBIN` into the input raw folder;
  - the manifest had no experiment column, so IonQuant made no `combined_protein.tsv`;
  - a `.raw` search had no mono on its PATH;
  - `finalize --zip` would have packed the hand-made copies (about 50 GB).

  Now:
  - **Staging.** The inputs are staged in `<out>/raw_stage/` after a free-space check: a `.raw` is copied in the job, a `.d` or mzML is linked. `raw_stage` must be a real folder inside `--out`, and the clean-up never follows a link. So a stage made by hand as a link to the raw folder can never delete the raw files. An input path holding a tab or a line break is refused.
  - **Experiments.** A workflow that quantifies gets one experiment per run, named as in conditions.csv, and FragPipe's `-`→`_` renaming is mapped back. An identifications-only workflow keeps FragPipe's one pooled experiment, so its FDR holds over all runs, as before.
  - **mono.** It is found from `$FRAGPIPE_MONO_BIN`, then PATH, then the Core's shared copy. Without one, a `.raw` search is refused before anything is written, naming conda-forge mono or mzML as the way out.
  - **Success.** It means exit 0, "ALL JOBS DONE" and the expected tables. The stage is then emptied; after a failure it is kept for a re-run.
  - **Scratch.** The stage is never zipped, catalogued or delivered.
  - **Sizing.** Every FragPipe SLURM job now passes `--ram` (the job's memory less a margin) and `--threads` (the CPUs SLURM gave it), tryptic searches included. Before, FragPipe sized its Java heap from the node.
- **FragPipe searches the database the skill names.** Before, FragPipe 24.0's shipped workflows name no database. Headless FragPipe then filled it from the account's cache, so it searched whatever database that account had used last, and the record never said which. Now:
  - run_search writes its own copy of the workflow (`fragpipe_input.workflow`) with `database.db-path` = `--fasta`, the target+decoy `.fas`;
  - a workflow naming a different database is refused, with nothing written;
  - `search_provenance.json` records the database searched: path, sha256, entries and decoys;
  - a `.fas` takes its target FASTA's sidecar, or the search is refused. A renamed copy finds it by an exact entry count.

  On HIVE the shipped workflow, with no database line, searched `--fasta` (12,596 entries, 6,298 of them decoys; the sha256 matched).
- **A FragPipe workflow that runs no quantification is identifications only.** FragPipe 24.0's shipped Nonspecific-peptidome workflow runs no label-free quantification. The job was marked failed for lack of a `combined_protein.tsv`, after FragPipe had finished. Now the workflow's own switches decide, with the outputs actually present as the fallback:
  - the job counts the search as finished. Its table check now uses `find -print -quit`, so it never calls a finished search unfinished;
  - a `combined_protein.tsv` whose intensities are all zero (spectral counts only) is not a quantified search;
  - `--adapt-only` writes `identifications.tsv` and `fragpipe_identifications.json`. The table is per run, from `psm.tsv`, with peptides kept by Philosopher's peptide filter wherever a `peptide.tsv` exists. The record quotes the filter as FragPipe's log shows it ran, the same reading as the Methods;
  - the DE refuses, and says how to quantify;
  - the Methods say identifications only.
- **FragPipe DIA on `.raw` or mzML is refused.** It writes beside its inputs the same way. It is now refused before anything is written, naming DIA-NN or a command to stage the inputs yourself. FragPipe DIA on `.d` is unchanged.
- **Non-specific and semi-specific searches.**
  - **`fetch_fasta.py --enzyme none`** builds the database for a sample to which no enzyme was added. A trypsin entry identical to a target is then dropped as a target, not kept as a reagent. The sidecar records the enzyme, `reproduce.sh` replays it, and the run record says "no digestion enzyme". The build says that its contaminant rule used a tryptic stand-in. SKILL.md step 6 ties `--enzyme` to the search's enzyme.
  - **The digest warning.** A non-specific Sage search is warned when the contaminant check's digest is tryptic.
  - **Default sizes.** A non-specific or semi-specific single Sage or FragPipe job defaults to 192G (Sage) or 200G (FragPipe) and 24 h, recorded as defaults. These were measured on a 38-run hydrolysate peptidomics study. The NOTE warns when the database is bigger than the 6,300 sequences they were measured on.
  - **The memory cap.** A job over its queue's per-job memory cap is refused, with the options.
  - **Checked on HIVE**, on two runs of the hydrolysate study, and passed:
    - FragPipe's shipped workflow, identifications only;
    - the same workflow with label-free quantification;
    - Sage non-specific;
    - an mzML input.

    The raw folder's listing was byte-for-byte the same before and after.

### For staff: search parameters
- **`--var-mods` refuses unknown words, adds deamidation, and turns Met-ox on for Sage DDA.** Before, `--var-mods` acted on `ox` only and silently dropped any other word. A like-for-like re-search that asked for N/Q deamidation ran without it. Now the words come from one table (`ox`, `deam`, `none`), and any other word is refused before anything is written.
  - A Sage DDA search with no `--var-mods` searches Oxidation (M), tagged as a default (the Core's decision of 2026-10-30). New Sage DDA searches therefore find more peptides, from a larger search space.
  - DIA-NN, and Sage on DIA, still search no variable mods by default.
  - Giving `--var-mods` replaces the default: `ox,deam` keeps both. `,` alone counts as not given.
  - The Methods name the mods from the same table. Step 6b's template shows both flags.
- **`--overrides` merges at every depth.** Before, a Sage override such as `{"database": {"enzyme": …}}` replaced the whole `database` block, silently dropping carbamidomethyl-C, N-terminal acetyl and the decoys, and the rationale still said "trypsin/P". Now nested blocks merge key by key; lists and tolerance windows are replaced whole. The rationale is read from the merged cfg: each overridden entry names the override, and the untouched part of an entry keeps its DEFAULT tag. These are refused, and nothing refused is recorded as applied:
  - a key at the wrong level, with where it belongs (checked against Sage 0.14.7's own settings);
  - `{}` on a block;
  - a malformed tolerance window.
- **Modification overrides are recorded as run.** A DIA-NN `--var-mod` override adds to the searched modifications. A `--fixed-mod` override replaces them, and the cysteine record, the rationale and the Methods read the final cfg, so a replaced reagent is never named. A cysteine modification the user set is not tagged DEFAULT.
- **"Set by Core staff" only for Core staff.** Before, every override was labelled "set by Core staff", whoever set it, and the label reached the client's bundle. Now it says Core staff only for a login on the Core staff list, and "the user" otherwise, or when there is no list. Re-bundling a session from before 2.14.2 re-checks its labels and says so in a MANIFEST NOTE.
- **Smaller fixes.**
  - `--ids-only` is refused for DIA-NN ("a DIA-NN search always quantifies"), and beside an override that sets `quant`.
  - `estimate_params.py` creates `--out`'s folder instead of crashing.
  - A refused run sets the earlier cfg aside (`.stale-<time>`, named in the message) instead of deleting it.

### For staff: the peak check
- **Chain searches get the right library.** Before, every 5-step-chain search failed: its library was linked under a name Skyline does not pair with `report.parquet`. Now the library is linked as `<report>-lib.parquet.skyline.speclib`, chosen by the route in the search record. A stale library is never taken. A folder holding both routes' libraries and no record is refused, naming both.
- **Unalkylated searches.** A search with no fixed cysteine modification gets `--pep-clear-mods` right after `--new` and `--overwrite`, and the record says so. A fixed cysteine modification other than carbamidomethyl is still skipped, with the reason.
- **Imports end at Slurm's time limit, and start from a pristine document.** Before, the skill's own timer killed imports that Slurm had suspended, just after they resumed, and a by-hand retry imported into the already-joined document. Now only `--time` ends an import. The build saves a pristine copy (`<stem>.built.sky`), and every import and every re-run join starts from it. A plan from 2.14.1 warns and joins as before.
- **A job that Slurm stops says why.** Each Skyline job (build, import, join, PRM run) gets an early warning (`--signal=B:USR1@120`) and a handler. When Slurm stops the job, SkylineCmd is ended, the partial outputs are cleared, and the record names the job and the time limit Slurm applied (read from Slurm; with no number when it cannot be read). The join's record names a stopped import. A stopped PRM run leaves "Not made", and no partial list.
- **One delivery rule.** `skyline_peaks.deliverable()` decides whether the check ships, for deliver, the README rows and the Methods. One sentence describes the folder, and core_submission no longer spells out the document's name. The report records the check's state it showed, and a delivery whose report says the check was not part of it leaves `skyline/` out.
- **Checked on HIVE.** The check ran on an earlier unalkylated chain search:
  - the build, 6 of 6 imports and the join completed;
  - 1,204 precursor-runs were compared and 60 flagged;
  - there was no carbamidomethyl in the built, joined or zipped document;
  - an import stopped at a 4-minute limit was recorded, and the join went on with 5 of 6 runs.

### For staff: search jobs and HIVE
- **sbatch off PATH.** Before, in a shell without sbatch on its PATH, run_search wrote a single-shot search for many files, and its login-node refusal of an inline search did not fire. Now it finds sbatch at HPC@UCD's fixed path, with one warning that gives the submit line, and it refuses an inline search on any login node.
- **No `.d` reads on the login node.** Before, run_search read every `.d`'s `analysis.tdf` on the login node: 13 minutes for 224 runs. Now it reuses step 2's check of a file that has not changed since (sizes, times, inode and side files). When more than 5 `.d` still need reading on a login node, it moves itself to a compute node, with its own `--account`, `--partition` and `--qos`.
- **`--mem` and `--time` for every single-job search.** `run_search.py --mem GB --time HOURS` sets the memory and time of every single-job search: Sage, DIA-NN single-shot, FragPipe, AlphaDIA and single Radiant jobs. They are recorded as `job_mem` and `job_time`, "64G (default)" when not given. On a chain they change nothing, and a NOTE names the chain's own sizing flags. `references/watcher.md` re-generates a job with them instead of editing its script by hand.
- **Black-hole nodes.** A job that FAILED with signal 53 and wrote no log is now a node fault, which `node_fault.py retry --exclude` acts on. A log that the watcher could not read is never counted as "no log".
- **Radiant.** The parallel route builds a TSV library with `make_radiant_library.py`, because Radiant cannot read DIA-NN 2.x's `.predicted.speclib`. On a login node, a multi-file Radiant search with no `--sbatch` goes to its per-file chain instead of being refused.
- **Astral narrow-window DIA is recognised.** Before, Astral 2 m/z DIA read as DIA "medium", and more than 80 windows of 3–4 m/z read as unknown. Now a tiled window set that repeats every cycle, with no data-dependent scan, is DIA "high" when read from a `.raw`. Read from an mzML, which carries no data-dependent flag, a set of windows narrower than 4 m/z reads "medium".
- **The watcher.** It shows "step 1b/5 measuring" until step 1b's resolved cfg exists; before, it showed "step 2/5". It also reports the `--dda` first-pass caution.
- **FragPipe's `contam_` refusal** names the target+decoy `.fas` that MSFragger searches.
- **Paths with spaces to and from HIVE.** Before, `hive_exec.sh --get`/`--put` split a remote path at a space. A conversation pushed to a service folder with a space in its name landed in a stray file, and `save_transcript.py` still said "saved". Now:
  - a remote path with a space or another special character goes as a tar stream over the same ssh; plain paths are unchanged;
  - names starting with `-` and the exec bit survive, and `--get` copies once;
  - `save_transcript.py --hive` checks that the files arrived before it says saved;
  - every remote command in SKILL.md, `references/core-submissions.md` and `references/podcast.md` quotes the session folder (`$(printf %q "$S")`). Before, `which-search`, the pull, `finalize`, `attach` and the podcast commands broke on a lab folder with a space.
- **Updating from the Windows desktop app.** `skill_version.sh --update` finds the desktop app's `claude.exe`: `%USERPROFILE%\.local\bin` first, then the newest under `%APPDATA%\Claude\claude-code\`.

### For staff: everything else
- **The normalisation check holds the MaxLFQ step.**
  - The gate compares the final MaxLFQ DE's between-run step with the check's. A check made before 2.14.2 counts as quantile, and is compared with the step the final DE actually applies.
  - A different step is refused, with "run the check again" as the first way forward. The refusal also says that `--between-run quantile` on DIA-NN-normalised data repeats 2.14.1's quantile step on top of DIA-NN's normalisation, and that the step itself is the harm.
  - NORMALIZATION_CHECK.md names the route it checked.
  - `reproduce.sh` always replays the step that ran, and notes a `--no-norm` report's normalised DE.
  - A quantile step without limma is an error, not a silent median.
- **A proteome bait survives "none".** In a TurboID study whose bait is a protein of the proteome and whose only added sequence is the enzyme, answering "none" for the added sequences used to erase the bait. Now the bait is kept, the question is not asked again, and `set --bait` keeps the answer.
- **The carboxylase panel finds bacterial biotin enzymes.** The proximity-labelling check matched only mammalian gene symbols, so a bacterial study found none. It now also matches proteins by name from the search FASTA: biotin carboxyl carrier protein, biotin carboxylase, and oxaloacetate decarboxylase alpha. Non-biotinylated beta chains are left out, so mammalian results are unchanged.
- **Unannotated FASTAs are flagged.** `fetch_fasta.py --path` warns when most entries have no GN=, no entry name and no description, and records `unannotated: true`. Annotating them is planned for 2.15.
- **HT plates are checked against their own records.** Before, on two HT plates 94 of 96 runs were named for the wrong well and every gate passed, because the gates read only names. Now `ht_manifest.py fetch` also stops (exit 2) on any of these:
  - a blank larger than half the plate's median sample run. The blanks are found beside the runs, since STAN leaves them out;
  - a sample list identical to another submission's (8 or more distinctive names);
  - a plate whose runs come from more than one HyStar sample table, or a sample table that names another submission.

  A sample run under 20% of the median warns. Each failure names the way forward.
- **Service folders.** `stage` matches a campus name written with its words run together, or joined by underscores, to the campus's alias.

### For staff: searches find their record wherever they are
- **One answer to "which search".** Before, many readers looked only in `output/search/`:
  - the report's engine line and "How this report was made";
  - the README and AGENTS.md;
  - the Methods and the Slack posts;
  - the delivery's search files, the bundle and the deposit plan;
  - the resolved parameters, the run log and the raw-file list;
  - the peak check's default search;
  - a re-analysis link.

  A session with searches in `output/search_dda/` and `output/search_sage/`, and a DE on the Sage one, therefore had a report naming DIA-NN and a delivery with no search files. Now one choice, `session.search_choice`, serves every reader:
  - **It picks:** the record in the folder of the report the DE read, or else the only record.
  - **It picks none:** when there are several records and no DE to choose by, or when the DE read a report that no record describes. It never falls back to `output/search/`.
  - **FragPipe DIA:** a `dia-quant-output/report.tsv` belongs to its own search.
- **With none chosen, nothing is guessed.**
  - The report says "Search: not recorded (2 search records, none chosen)", and so does "How this report was made".
  - The Methods give tagged blanks.
  - A delivery carries no search and says why, with how to choose: rename each other search folder to `output/superseded_<name>/` (a folder whose name holds "superseded" is never a candidate), or deliver every search folder with `--mode interim`.
- **`session.py which-search --dir <S> [--paths]`.** It prints the choice as JSON. With `--paths` it prints the files a working copy needs: the record, the report the DE read, and the workflow manifest. It exits 3 when none is chosen. `--paths` also lists an identifications-only search's `identifications.tsv` and its record. The laptop route's pull takes that list and stops with STOP when none is chosen; before, it pulled only `output/search/report.parquet`.
- **One engine-and-version rule.** A search record gives its engine and its own version; a version the record does not hold stays unrecorded and never borrows the pin. With no record at all, the workflow manifest's pin is used, tagged "(workflow manifest pin)".
- **The delivery and the commands follow.**
  - `delivery.json` records the search folder, and the email draft names it.
  - An analysis delivery carries the DE's search under its own folder name.
  - `make_report.py --session` and `make_methods.py --session` take the session's choice.
  - A `--search-prov` file that is not there is refused, not read as "no record".

### Public text
- **Client names and newly added Core identifiers are removed.**
  - 88 lines naming a client, a client's lab or an outside person are rewritten in the skill's text, tests and comments.
  - So are 80 lines of submission numbers, staff names and logins that 2.14.1 and 2.14.2 added.
  - The identifiers already public on main (917 hits on 826 lines, and 3 file names) go with the 2.15 rewrite.
- **A guard keeps new ones out.** `tests/test_no_new_identifiers.py` fails on any staff or submission identifier beyond a frozen list of those already on main. With the Core's private client-name list, it also fails on any client name.
  - The list is kept outside the repo: `$SKILL_PRIVATE_NAMES`, by default `~/.config/ucdavis-proteomics/client_names.txt`. No name, and no digest of one, is in the repo.
  - Without the list, only the client-name part skips, with a message; an unusable list is an error.
- **The FragPipe licence notes name the tools' commercial licensor and its contact again.** The scrub had taken them for a client. They are allowed through the guard as public licence text.
- **No submission number in a search record.** The Sage `.d` conversion's record names the Core's msconvert settings without naming the submission they came from.

**Tests:** 1,065 more test functions than 2.14.1 (4,111 → 5,176), with 76 new test files: 1,069 added, 4 renamed or removed. By lane (tests added in each lane's merge):

| lane | new tests |
|---|---|
| finishing a session (records) | 131 |
| non-specific searches (with follow-ups 2 and 3) | 120 |
| small fixes | 89 |
| search jobs | 77 |
| Sage `.d` | 73 |
| C2 fixer B: safety, state and gates | 73 |
| report text | 69 |
| C2 fixer A: client text, Methods and the brief | 61 |
| normalisation | 60 |
| search records (T44, with its follow-up) | 57 |
| peak check (with the HIVE follow-up) | 50 |
| core service | 49 |
| C1 review fixes | 38 |
| C2 fixer C: docs and the guard | 33 |
| parameters | 28 |
| transport | 19 |
| identifier scrub | 9 |
| HIVE job guard | 1 |
| C2 fixer D: reproducibility (with its follow-up) | 34 |

The lane counts add up to 1,071, two more than the tests added, because two tests renamed by the identifier scrub count in two lanes.

Every fix's test was seen failing before the fix, and a test that pins existing behaviour says so.

The full suite on HIVE ran 5,189 tests on the final build and found no failure that 2.14.1 (4,126 tests) did not also have. So did two earlier runs on the merged release (4,979 and 4,991 tests). The failures left are tests that fail only in HIVE's environment, on both. The two commits after that run change only the identifier guard's list and the daily stats; the guard passed with the private client list.

The real-data checks on HIVE:
- the two-run DDA submission through both Sage routes and the DIA-NN `--dda` fallback;
- the MaxLFQ re-score on the PXD063416 benchmark;
- the peak check on an unalkylated chain search;
- the non-specific searches on the hydrolysate study.

A fresh agent session also ran the two-run DDA case end to end on the 2.14.2 build, and stayed on the skill's path:
- the search: Sage read the `.d`, identifications only;
- the report, the Methods, and finalize, which built the bundle;
- `deliver --mode no-de` as a dry run, which the staff QC check held, as designed.

No hand-made report and no override. Its findings were fixed in fixers A, C and D.

A re-check on a build with every fixer's changes confirmed those fixes on a copy of the session:
- finalize, run four ways, warned exactly when `logs/commands.log` was missing or older than the newest step record, and stayed quiet otherwise;
- the Methods name the enzyme, and reproduce.sh searches with the configuration that ran and has no DE step;
- the search in reproduce.sh, run for real, reproduced the original exactly: 5,756 PSMs, 1,041 peptides and 147 proteins at 1% FDR, and an `identifications.tsv` with the same checksum as the bundle's.

### Known limits carried to 2.15
- **Normalisation.**
  - The between-run default for the engines' declared quantities is still quantile. That covers Sage and FragPipe, and IonQuant's and directLFQ's quantities, where the quantile step now comes after the engine's own normalisation, and the Methods name both.
  - On the benchmark's proxy for an engine that does not normalise, the quantile step gave 46, 72 and 69% wrong calls at 4, 6 and 10 m/z; median centring gave 60, 76 and 74% (worse); no step gave 5.5, 18 and 30%. No step was safe at 6 and 10 m/z.
  - A mixed-species benchmark, where whole species shift between runs, is the adversarial case. Changing the default is the Core director's decision.
- **FragPipe for DDA-PASEF.** In 2.15, FragPipe becomes the default engine for timsTOF DDA-PASEF (identifications and quantification). Sage is the fallback when FragPipe cannot be installed. With fewer than 3 experiments, MaxLFQ or directLFQ is computed by the skill. On the two-run submission FragPipe found 1,215 peptides, against Sage's 753 and DIA-NN's first pass's 936; two unreplicated runs cannot judge accuracy.
- **Sage.** Sage 0.15 is not adopted for quantification on `.d`: the beta's release binary panics on a local `.d`. Re-test when 0.15 is released, and re-check the override key list against its settings. The low-coverage LFQ warning may become a gate.
- **DIA-NN `--dda`.** The second-pass crash (exit 132, an illegal instruction) may depend on the CPU family: check zen4 against zen2 before reporting it upstream. DPC on a first-pass report is expected to be unaffected, but it is not yet tested with 3 or more runs.
- **Enzymes.**
  - `estimate_params.py` has no `--enzyme`, so a non-trypsin Sage search needs an `--overrides` block.
  - `fetch_fasta.py --enzyme chymotrypsin` still judges the contaminants on a tryptic digest.
- **SKILL.md.** The 2.15 slim-down rewrites SKILL.md; golden rule 9 becomes rule 16 there. A Stop hook will run `session.py status` before a turn ends.
- **FragPipe.**
  - Staging for FragPipe DIA on `.raw` or mzML (refused for now).
  - An engine-neutral name for `sage_lfq_check.json`, which FragPipe now shares.
  - SKILL.md repeats the broad-digest sizes that run_search holds.
  - The `rev_` decoy-tag fallback is not tagged.
  - A quantifying workflow without the label-free key is pooled (FragPipe then refuses loudly).
  - One reading of "identifications only" across the record and the bundle.
- **Peak check.**
  - Imports on zen4 nodes took 32–37 minutes, against 3–5 elsewhere; SkylineCmd 26.1 has no thread setting to bind.
  - A stopped import's scratch folder is left behind.
  - The `--version` timer counts suspended time.
  - wineserver may sit outside the process group that is stopped.
  - A preempted build leaves a transient "skipped" record.
  - Not yet checked on real data: a no-CAM search with Met-ox.
  - A `retry` subcommand and node constraints.
- **finalize, status and the fold-in.**
  - The stale check compares the report by size only, and a rebuilt bundle keeps old `inputs/` files.
  - `status` calls a delivery "stale" after any later finalize, even one that changed nothing.
  - A folder holding key names is left out, not refused.
  - Big files are not scanned in chunks.
  - Conversation copies outside a session are not caught by name.
  - The fold-in can walk its folders on the login node.
  - The `id_*`/`credentials*`/`env` exclusions can catch innocent names; the NOTE names each one.
  - The session zip still carries a Sage search's `mzml/` folder.
  - `board.sh` never warns for a HIVE-remote session.
  - OUTPUT_FILES.md does not list `--code-dir`/`--extra-dir` work, and a delivery does not carry `output/custom/`.
  - README, AGENTS.md and run_manifest.json can carry absolute paths, and `node_faults.json` node names.
- **Search records.**
  - The DE-input tie-break compares real paths, so a laptop copy of a HIVE session gets none.
  - A no-DE delivery of a multi-search session delivers no search.
  - A no-DE benchmark of two searches gets Methods that describe neither.
  - A re-analysis whose DE read the prior's report can name the prior's engine on the page.
  - A choice's reason can carry an absolute path.
- **Reproducing a search.**
  - reproduce.sh's closing step compares every search output with the bundle's checksums, but two of them change in a faithful re-run: Sage's internal `psm_id` in `results.sage.parquet`, and the adapter's record when the skill version differs. `identifications.tsv` matches. REPRODUCE.md should say which files to compare.
  - The database step replays `fetch_fasta.py` without `--hive`, so on HIVE the contaminants come from GitHub rather than the staged copy the search used (the same sequences in the re-check; one header differed).
  - Sequences added with `--add-fasta` are named by their HIVE path and not copied into the bundle, so someone without that path cannot rebuild the database.
- **Contrasts.** A reversed contrast given by hand still only warns at the design check.
- **No-DE sessions.**
  - The report page has no identification counts of its own.
  - Conditions with one run per sample fail `--validate`.
  - The sample-ID match misses Core digest suffixes.
  - The step-4 confirmation quotes DIA-NN's 15 ppm for a Sage search.
  - `experiment_type.py` asks about normalisation with no DE.
- **Staff reports not yet fixed.**
  - `to_docx.py` stops when pandoc is present but cannot run.
  - `qc_bracket` grades a QC `.d` that never finished recording as a failed QC.
  - `deliver --mode no-de` refuses a no-DE session that has `figures/figures.json`.
  - The Core's shared Gemini key is free tier, and `--core-run` is not stopped on it. Paying for the key, or changing the policy, is the Core director's decision.
- **Identifiers.**
  - The pre-existing staff and submission identifiers on main go with the slim-down, whose guard will read the private client list.
  - Client names already on main outside the core skill (the dev skill and one docs page) are removed, and the guard is extended to `docs/` and the dev skill.
- **Still planned.** From the 2.14.2 triage:
  - DIA-NN with match-between-runs off;
  - the contaminant rule on the search's own digest;
  - annotating unannotated FASTAs;
  - a bait carry-over check;
  - the review record in deliveries;
  - internal Bioshare shares;
  - the bait and every significant protein in the Skyline document;
  - HyStar queue generation;
  - step 6b reading another search's settings for a like-for-like re-search;
  - the mzML reader reading Thermo's data-dependent flag.

## [Skill 2.14.1] — 2026-10-27

Two additions to the report: every report now says how it was made, with a link to a public page explaining the pipeline, and the contaminant warning says what the skill already did about the contaminant list before the search.

### What the client sees
- **Every report says how it was made.** Before, a report never said that an AI ran the pipeline and wrote its text. Now each report ends, before the figure appendix, with a short "How this report was made" section: which software searched the raw files and ran the statistics (and that `tables/reproducibility_log.R` re-runs them with no AI involved), that Claude ran each step following the Core's pipeline and wrote the analysis text, and, when there is a podcast, who wrote and checked its script and which voice made it and where. Every sentence comes from the run's own records; a fact no record holds is left out. The section links to a public page, [How the Report Was Made](https://bsphinney.github.io/DE-LIMP/how-reports-are-made.html), which explains each step, the models involved, where the data go, and how another lab can run the same pipeline. The PDF prints the page's address.
- **The contaminant warning says what was already done.** Before, the warning named the proteins the contaminant list took, and read as if the skill had done nothing about contaminant entries that copy the sample's proteins. Now it ends by saying how many of the list's entries the database build removed before the search because each was identical to a protein of the organism (or to a sequence added to the database) or could not be told apart from one, and that the entries involved differ from the sample's proteins and stay in the list so real contamination is still caught. The sentence appears only when the database's own record says so.

### For staff
- **The podcast paragraph follows the podcast.** The podcast is usually made after the report, so `make_podcast.py link` fills in the section's podcast paragraph (and `share` does the same in the copy with audio); a report rebuilt after the podcast reads the same. The podcast check ignores the section, so neither makes a check stale. The AI report's own section of that title wins, and the writer's prompt asks it not to write one.
- **One check that a database is the one its record describes.** `fetch_fasta.sidecar_sha256_matches` is now the one comparison of a FASTA with its sidecar's sha256, used by `fetch_fasta`, `audit_results.py` and the contaminant check. The contaminant record gains `database_build`, read from the sidecar while it still describes the searched FASTA (for an older record, the sidecar beside its FASTA).
- **The DE record names the skill version that ran it.** `run_de.R` and `run_silac.R` write `skill_version` in `de_provenance.json`. The section names that version, and a report rebuilt later by another version adds "This report was built with skill X" (before, no JSON record of the run held the version).
- **Tests:** 44 new (15 for the contaminant wording, 28 for the report section, 1 for the recorded version).

## [Skill 2.14.0] — 2026-10-21

Four additions: a Skyline peak check of the top hits after the DE (and, for staff, a PRM/SRM follow-up list made from it), a local voice that takes over the podcast when Gemini cannot be used, an automatic check for sample proteins that the contaminant list takes away, and Core board threads that no longer name Brett by default.

### What the client sees
- **The report shows the peaks behind the top hits.** Before, the report gave DIA-NN's numbers with no picture of the peaks behind them. Now, after the DE, Skyline 26.1 runs on HIVE and the report gains a "Peak check (Skyline)" section: a peak picture for each of the top 10 DE proteins (the most abundant when none is significant), a table of the peaks where Skyline picked a different peak from DIA-NN's, and a Skyline document, `skyline/<name>_top_hits.sky.zip`. The section, OUTPUT_FILES.md and both READMEs say how to open it: in Skyline 26.1 or later on Windows (free from https://skyline.ms), by double-click or File › Open; it holds the chromatograms, so the raw files are needed only to re-pick peaks. The Methods gain a "Peak check (Skyline)" paragraph, the reproducibility bundle holds its record, and the delivery ships `output/skyline/`.
- **The peak check is called what it is.** The report says the pictures are a visual check of DIA-NN's peaks, not independent confirmation, because Skyline reuses DIA-NN's peak edges; the warning signs are the peaks where Skyline picked a different one. "Confirmed by Skyline", "validated" and the like are flagged: a warning on the report Claude writes, and a failure of the podcast check. A sentence whose "confirmed" belongs to another check, or that asks the listener to verify the peaks themselves, is only a warning.
- **A peak check that did not run, or no longer fits, says so.** Before, there was no such step. Now a check that could not run (no Skyline container here, not a DIA-NN 2.x search, a DDA search, no recorded mass accuracy, or turned off with `skyline_peaks.py skip --reason`) reads "Not run." with the reason, in the report and in finalize's MANIFEST.txt. A DE run again after the check makes it "Out of date". Planning it again or turning it off cancels the last plan's jobs and removes its pictures and document, so none is delivered under "Not run".
- **Proteins the contaminant list took away are named.** Before, when a contaminant entry shared a protein's peptides, DIA-NN could report them under the contaminant, and the contaminant rule removed them: the protein was missing from the results, or measured from a few leftover peptides, and nothing said so (a mouse search lost Actb and Eef1a1; a human IP lost 68 genes). Now the Audit & caveats table names those genes and says the Core can search again without those contaminant entries. A protein seen only or mostly through peptides it shares with real contamination (a contaminant entry with at least two peptides of its own, such as bovine serum albumin in cell culture) is said to have an uncertain amount, never called lost. "Missing from the results" is said only when the analysis really removed the shared peptides, and a keratin sample's keratins are never reported as taken. A clean search reads "Checked"; one that could not be checked reads "Not checked".
- **The podcast is made even when Gemini cannot be used.** Before, no Gemini key, Google's 402 "prepay credits are depleted", a key Google refused, no quota on any Gemini voice model, or every model stalling stopped the render, and the delivery went out with no podcast. Now the whole episode is made with a local voice (Kokoro-82M in the Core's container on HIVE; nothing is sent anywhere), heard back with Whisper on HIVE, and the log and podcast.json say so. Kokoro reads the hosts with the voices Emma and Heart; both are women's voices, so the second host's name is spoken "Lena", while the script, transcript and podcast.json keep "Leo" and the transcript page says so. Every part is made again with the local voice, so an episode never mixes voices. podcast.json and the transcript page say exactly what had reached Google before the switch. Gemini episodes are unchanged.

### For staff: the peak check and the PRM/SRM list
- **Skyline is pinned and checked.** Before, the Core's Skyline image was an unpinned `_latest.sif` holding Skyline-daily 24.1, about 19 months old. Now Skyline 26.1.0.266 is pinned by Docker digest and by the `.sif`'s sha256, checked before every use; users outside the Core pull the same digest, checked by `SkylineCmd --version`. 26.1 is also the oldest Skyline that opens the document: its command line cannot save an older format.
- **Skyline's mass tolerance is the search's own.** Before, in the feasibility trial, a guessed 10 ppm broke the peaks of one HeLa run. Now the tolerance is the value the search fixed, or DIA-NN's measured "Optimised mass accuracy"; when neither is recorded, the step does not run and says why. A fixed number is never used.
- **Imports run one raw file per SLURM job.** Before, the trial found that two readers on one timsTOF `.d` failed and that `--import-process-count` hung. Now each raw file is imported by its own array task into its own copy of the document, since a shared folder let one task delete another's spill files, and `--import-process-count` is never used.
- **Modified peptides are matched by mass.** Skyline's `M[+16]` now matches DIA-NN's `M(UniMod:35)`, with the masses taken from the search's own `--var-mod`/`--fixed-mod` flags. An acetyl-only peptide never matches its acetyl + oxidation form, and the tables and pictures label each precursor with its modifications.
- **A PRM/SRM follow-up list from the top hits.** Before, there was no headless way to make one. Now `skyline_peaks.py prm` keeps the 3 best peptides, 6 fragments and one charge per protein and exports a Bruker prm-PASEF list (RT and 1/K0 windows, collision energy left at 0 for the method), Thermo Fusion, Q Exactive and Stellar PRM lists, and a TSQ SRM list with predicted collision energy. A list is scheduled only for the same instrument family and gradient, and unscheduled otherwise, with the reason. Exploris and Astral are refused: Skyline's command line has no isolation list for them.
- **Smaller pieces.** The shared document is saved "minimal" (3.2 MB against 12.5 MB on a HeLa test, the same 348 precursor rows). `plan` prints the CPU-hours its three jobs reserve (`cpu_hours_reserved`, also in `submit.sh`), which Core staff record on the board as one job. `setup.sh` adds `matplotlib-base` to the pipeline env, a new one or an existing one on the next `bash setup.sh`. A job of an earlier plan never overwrites a newer record.

### For staff: the podcast's local voice
- **What hands over to the local voice, and what still waits.** Only the four failures above hand over, and "every model stalled" includes the 30-minute timeout budget running out. A per-minute rate limit is still waited out, a transient error still stops with the resume message, and `--no-fallback` keeps the old stop. Before, one model out of its daily quota stopped the render until the next day; now the next Gemini model makes every part again, as for a stall. When no model answers the 60-second two-line test, the render waits 5 minutes and asks once more before it counts them as stalled.
- **`--tts local`** (render and `job`) uses the local voice from the start: no key, no consent and no google-genai, and from a laptop each step runs as a HIVE job through `hive_exec.sh`. A render refused for lack of consent now names it.
- **Text rules for the local voice** (`scripts/kokoro_text.py`), each from a misreading in a real Kokoro episode: letters in capitals spelled out, ISO dates and versions in words, PROT numbers digit by digit, "+0.61" and "−1.82" as plus and minus, number ranges with "to". `render --tts local --dry-run` shows what will be read.
- **`verify` hears it back on HIVE.** Before, the only check of the audio was Gemini transcribing it, which needs consent and a key. Now a local-voice episode is always checked with Whisper (large-v3-turbo plus small.en; a spot counts when both agree), sending nothing; `verify --local` does the same for a Gemini episode.
- **HIVE jobs sized for it.** The podcast job asks for 4 hours instead of 2, enough for every wait at its limit (real runs take minutes). `make_podcast.py job` now prints the CPU-hours it reserves, the local voice's steps included, for the board's record of the podcast job. The local voice's steps are HIVE jobs of their own, asked for only when needed (16 CPUs and 24 GB to speak, 16 CPUs and 12 GB to hear back); the log names each with its `scancel` line, and a job HIVE refuses is said plainly. The jobs say `--ntasks=1` and source `/etc/profile.d/modules.sh` before loading modules (HPC@UCD's rule). The skill pins `kokoro-1.2.sif`, which ends at once with the reason when a worker is killed for memory (1.1 hung).
- **Said plainly when it cannot run, and nothing private leaks.** Without a HIVE login, with an account outside proteomics-grp, or with no skill on HIVE, render says Gemini failed and why the local voice is not available. The Gemini key never reaches a container, an srun or a HIVE job.

### For staff: the contaminant check and the board
- **The check runs in every DIA-NN search's last job.** `contaminant_competition.py` writes `contaminant_competition.json` and a copy in `search_provenance.json`: COMPETED OUT (no quantity left of the gene's own) and SIPHONED (most of its signal taken). The watcher shows it once the search has finished, and AUDIT.md gives the genes, the contaminant entries and the re-search command (`fetch_fasta.py ... --drop-contaminant <accession>`). It never stops a search or an analysis, and the Core's universal contaminant list is unchanged.
- **One gene per shared peptide, and no stale records.** Genes are grouped as protein inference groups them, so one actin peptide names one gene, not ACTB, ACTG1, ACTA1 and every other paralog. A record is read only for the report it describes (its size and modification time), and a re-search into the same folder sets the old one aside. If the report cannot be read or the search job's time runs short, AUDIT.md says "Not run: <reason>"; for a search from before 2.14, or a record that does not match the report the analysis used, the audit runs the check itself.
- **One q-value filter.** Before, run_de.R's q-value filter had three copies in Python, and the parquet ones dropped a NaN or missing q-value that run_de.R keeps; the peak check brought a fourth. Now one definition, in `diann_q_columns.py`, serves the pass comparison, the audit, this check and the peak check.
- **Board threads no longer name Brett.** Before, every `board.sh start` added Brett with `--with`, so each new thread waited for his approval before the Claudes could post. Now no one is named by default, and the thread opens at once on the staff member's own approval. Brett, as Core admin, still sees every thread and can act and approve in it without being named; jobs of 10,000 CPU- or GPU-hours or more still need a second person's OK; `--with <UPN>` stays for a colleague, who by Core policy does not have to approve the start either.

## [Skill 2.13.2] — 2026-10-20

Fixes from the staff reports of 2026-10-15 and 16, from two rounds of independent review, and for HPC@UCD's cluster rules: its own agent skill, `ucd-hpc`, is mandatory on Farm, Franklin and HIVE from 2026-10-16, and on cluster policy it overrides this skill.

### What the client sees
- **No draft history in what the client receives.** After the expert review, the report's Expert Review Notes read like a changelog ("checked the first draft", "two protein names were wrong ... corrected"), the audit said an earlier normalisation reason was "corrected", and a podcast said "the first draft of this report fell for it", although the client never saw a draft. Expert Review Notes now say what was checked and where the report deals with it, in the present tense, and the review history goes in the staff-only decisions log. The podcast check fails on phrases that can only be draft history ("first draft", "an earlier version of this report", "the report originally said") and warns on words that are draft history only in context ("corrected" in a sentence about a review or a mistake); the report builder warns on both. Science wording ("the p-values are corrected", "fixed modification", "draft genome") and methods narration ("the QC flagged a batch effect that we then corrected with ComBat") trip neither.
- **A plain-language Audit & caveats.** The report's Audit & caveats section was the technical audit file as written: check codes, the normalisation check's B1-B4 strings, and "implausibly high ... not real biology", which a client could take to mean the results are wrong. It is now a table with one row per check (what was checked, the result, what it means for the results), the same for label-free and SILAC analyses, and true for the reason each check was raised. With several SILAC comparisons, the single-peptide row no longer says both "some" and "none". The technical AUDIT.md stays the full record.
- **No false "9 of 9 sample IDs match no raw file".** When the sheet's sample IDs and the run names differ and staff assigned each run with `locate --choose`, the report still said no sample matched a run. The report now uses staff's assignment, and matches by name every run the assignment does not cover.
- **The Methods state the protein inference.** The search record and the Methods now say which protein grouping DIA-NN used ("implicit protein grouping by genes, DIA-NN's default", or the level staff chose).
- **The podcast is read for meaning before it is rendered.** The podcast check matched words and numbers only, so a script passed with a correct number given to the wrong comparison, a hedge dropped, or a protein called robust that the robustness tables say is not. Now a second agent that did not write the script reads every sentence against the report and records PASS or FAIL for that exact script and report; rendering, linking and the HIVE job refuse without a PASS, and an edited script, a rewritten report or new robustness tables mean checking it again. A podcast job written by 2.13.1 and still queued refuses until the check is recorded. The mechanical check also fails a protein named next to "robust" or "survives" that the tables say is not (reading ", and Ryr2 goes up" as a separate clause, and "Was that robust?" as English, not the mouse gene Was), and flags superlatives the report does not use. A protein named after such a comma (", and they are Ryr2, Jph3 and Actb", ", so does Ryr2") or a gene that is also an English word said first ("Set holds up") is a WARN that names it for the writer and the meaning check.

### For staff: HIVE and HPC@UCD's rules
- **Heavy steps leave the login node by themselves.** Setup, the CoreOmics `locate` / `stage` / `deliver`, the FASTA build, the reproducibility bundle, finalize and the resume search ran on HIVE's shared login node (`deliver`'s dry run once searched the service tree there for 4 minutes). Started on a login node, each now runs itself as a one-off SLURM job with the account, partition, time and memory spelled out, says so, and waits. `bash scripts/hive_exec.sh --job '<command>'` sends any command to a compute node the same way. Step 0a lists what may stay on the login node (submitting and watching jobs, small copies, bookkeeping) and what goes to a job (anything that reads report.parquet or raw files, runs R, walks a share, installs, renders or zips). These jobs never take a queue that can be pre-empted unless the account has nothing else; one that only reads uses the free `low` queue when your own searches fill `high`, and says so. genome-center-grp is billed when you have it; otherwise the skill asks which account.
- **Installs run on a compute node.** `setup.sh` (a conda solve, R packages built from source, .NET), engine downloads, the first .NET download and the Radiant container build ran on the login node or with a bare `srun`. They now run as jobs with everything spelled out (HIVE's compute nodes have internet). A setup job that SLURM refused or killed now exits 3 and says the run did not finish, instead of leaving the old setup.json looking current.
- **The .NET advice for step 2 reaches step 2.** Before, a `.raw` the parser could not start on said to `module load dotnet-core-sdk/8.0.4` "in the same shell" and re-run step 2, but step 2 now runs as its own job (`hive_exec.sh --job`), which a module loaded in that shell never reaches. Now SKILL.md and `detect_acquisition.py`'s message put `module load dotnet-core-sdk/8.0.4 &&` inside the job's command.
- **Data and results on group storage, and job headers written by the skill.** The HIVE runbook put raw data and the search in the 20 GB home folder; it now uses the group share. `on_compute.py --header` writes the top of DE and set-test job scripts, and step 8 says how to check a job with HPC@UCD's own checker before submitting it.
- **Fewer logins while watching.** Claude polled HIVE about every minute; for a SLURM job it is now every 5 minutes or more. `checkpoint.py find` runs on a compute node and looks at most 6 folders down. Thermo `.raw` detection goes through `--job`.
- **`ucd-hpc` installed and in charge.** Step 0a checks that HPC@UCD's skill is installed and offers its 3-line install. On cluster rules it wins, and Claude must say when it set an instruction of this skill aside.
- **"No DE can run" when DEs ran fine.** On an environment with limpa 1.2.5 and no nanoparquet, `setup.sh --check` said `ready_for.de: false`. The check now follows what limpa really reads with (arrow for limpa 1.2, nanoparquet for 1.4) and says what the old limpa costs.

### For staff: searches, podcasts and the version
- **A two-file search can measure mass accuracy.** A 2-run DIA-NN search whose mass accuracy had to be measured (an Orbitrap MS2 resolution with no DIA-NN table value) always failed after its library was built: only one run was probed, and one run is never enough. Both runs are now probed and the higher of their two values is used.
- **Watching a search from Windows with no Python.** Where `python3` is the Microsoft Store placeholder, `watch_run.sh --hive` reported a healthy search as failed and finished, which could lead Claude to resubmit it, and Git Bash rewrote the HIVE folder name. The watcher now runs the poll on HIVE itself, never reports a search failed because a program is missing on the laptop or HIVE cannot be reached, and passes HIVE paths unchanged.
- **Watching one SLURM job keeps that promise too.** Before, `watch_run.sh --slurm <id> --hive` with a working python3 still said `failed: true` when sacct and squeue both came back empty, whether HIVE could not be reached or SLURM did not know the job. Now HIVE out of reach is `watcher_query_failed` with `failed: false` and exit 3, as for a whole chain, and an unknown job id is `state: query_failed` with `failed: false`.
- **A podcast no longer hangs on a voice model that stopped answering.** A staff render sat 28 minutes on a stalled Gemini voice model while another answered in 3 seconds, and could not switch because its first parts were made with the stalled one. Each model now gets a two-line test before any audio is made, and if one stops mid-episode the next makes every part again, so an episode always has one set of voices. A model that stopped mid-episode is skipped for 12 hours, but still gets one try before the render gives up, and the message says `--model <name>` tries any model. The Gemini library no longer retries silently.
- **Gemini "prepay credits depleted" stops the podcast at once.** Google's 402 was read as a per-minute rate limit, and each part waited about 11 minutes with the log saying only "rate-limited". The render now stops at once with Google's message and says to add prepay credits in AI Studio; finished parts stay cached. The first rate-limit wait logs exactly what Google answered.
- **The key's tier is recorded from Google's answers, never guessed.** A free-tier quota in a 429 records `key_tier: "free"`, a 402 records `"prepaid"`, and the evidence is kept; a free-tier quota never outvotes billing. A hand-typed consent note that says "paid" on a free-tier key gets one plain warning. It never stops a podcast: Core podcasts on the free tier are covered by the Core director's standing approval.
- **Version check every conversation.** The "is this skill current?" check ran once, in the middle of one-time setup, so a conversation begun before a release kept the old skill into the next day. It is now the first thing in step 0, every conversation and every resume, and again before submitting a search and before finalizing. A computer on 2.11.2 or older needs two lines typed once to update on Windows without a GitHub SSH key; they are in the install guide.
- **Protein grouping, measured.** DIA-NN's default grouping is by gene, and no setting merges a gene's ORFs into one protein group when each has peptides of its own; a different level has to be set from the start of a new search (`estimate_params.py --overrides '{"--pg-level": 0}'`). The step-5 warning "protein inference is enabled while empirical library is used" is expected on every 5-step search and harmless; the watcher guide says so.

## [Skill 2.13.1] — 2026-10-16

Fixes from the first real analysis run with 2.13.0 (a triple-SILAC re-analysis, end to end) and from three rounds of independent review.

### What the client sees
- **No more first-word "gene names" from an NCBI database.** On a database that is not UniProt's (NCBI, RefSeq), DIA-NN fills the gene and protein-name columns with the first word of each description ("MULTISPECIES:", "hypothetical", "30S"). The SILAC tables passed these on, and the report's "Top proteins" table showed them as gene names. Those columns are now left blank for such proteins (a `[gene=...]` tag in the header is kept as the gene), and the Top proteins table shows each protein's description from the database instead.
- **SILAC counts read as numbers everywhere.** A SILAC analysis's significant counts were printed as raw program output, `{'up': 394, 'down': 417, 'total': 811}`, in the README, AGENTS.md, DIFFERENCES.md, the run log, the Core's registry and the Slack post. They now read "811 (394 up, 417 down)". The README also names the design file the analysis used (`silac_design.csv`), not `conditions.csv`.
- **The SILAC Methods are kept as written.** Finalize took every SILAC methods.md, even the skill's own, as missing its "Differential expression" section, because the SILAC section has its own heading. It then wrote an unfinished draft beside it, built the Word copy and the data-deposit texts from that draft, and reported it as OK. The SILAC heading now counts, so the finished methods.md is used, and its SILAC section reaches the PRIDE data-processing text. When a section really is missing, finalize says that the Word copy comes from the draft.
- **No blood, muscle or skin warnings for bacteria.** The sample-quality check raised a haemolysis caution on a bacterial culture supernatant (the bacterium's own catalase matched a red-cell marker), and the caution reached the report and the podcast. For an organism that is not a vertebrate, those panels now say "not applicable" and raise nothing. A sample that also holds a vertebrate host's proteins can still be checked with `--taxid <host>`.
- **"Not significant" is explained without overstating it.** For a SILAC comparison with no significant protein, the notes put the strictest cutoff of the multiple-testing correction beside other comparisons' cutoffs as if they were alike, and gave an "80% power" figure. A draft report read this as a comparison four times less sensitive that "can rule out" smaller changes; in fact its data were the least noisy of the three. Each comparison now gets a typical protein's 95% interval and its cutoff in plain words ("because no protein passed, the correction applied its strictest cutoff ... for a protein changing alone"), with no power figure, and the notes say these numbers rule nothing out.
- **No false "different environment" note.** The reproducibility notes of a SILAC analysis told the user the analysis had run in a different software environment than the recorded one, when it had not. The SILAC analysis now records which R it used, and a value that was not recorded is reported as "not recorded", never as a difference.

### For staff: the analysis record and the steps around it
- **A subagent's or teammate's conversation is saved as its own, never the main conversation's.** Run from a subagent or a teammate, `save_transcript.py --remember` registered the main conversation, with other clients' work in it, for the client's session, and saved none of the agent's own. Nothing in a subagent's environment says which agent it is. So whenever any subagent or teammate has run in the last 6 hours (a team, or the step-8d reviewers, which means `finalize` after them too), `save_transcript.py`, `session.py init` and `finalize`, and `checkpoint.py status` take `--call-id <token>`: a fresh token typed into the command, for example `main-k7f3x9`. The transcript whose running command carries the token is the one saved: the agent's own for a subagent. With no token, or a token found in no running command or in two, nothing is recorded, and the message (and `init`'s and `status`'s output) says how to fix it. Both Bash and Windows PowerShell commands count. With no subagent at work, nothing changes.
- **The design discussion is kept for agents that follow the skill from a checkout.** An agent that read SKILL.md instead of loading the skill lost everything before its first save from the saved conversation. Reading SKILL.md, or running its scripts, now counts as loading the skill when the conversation has no real load.
- **A check for SILAC labels that read lysine and arginine differently.** In one dataset the medium channel (K4R6, whose lysine label is deuterated) read lysine-ending peptides 0.29 log2 lower than arginine-ending ones of the same protein, in every run. That is the size of a modest real effect, and nothing flagged it. The audit check `silac_label_residue_bias` now measures this for each pair of channels (so a label-swap design cannot hide it), warns above 0.15 log2, and names a deuterated label. `references/silac.md` says K4's lysine is deuterated and suggests a non-deuterated medium label (K6R6) for new designs.
- **The analysis brief for a SILAC session describes SILAC.** It said contaminants had not been removed (they had), that the identification filter was not recorded, and asked for coefficients of variation, a PCA, per-sample counts and "measured vs inferred" tiers that a SILAC analysis does not have. It now takes these from the SILAC analysis's own record and names only the figures that were drawn. The identification filter it states is the one the Methods state, so a Sage or FragPipe brief names the engine's own FDR, not DIA-NN columns that filtered nothing. The audit names the contaminant filter from the analysis's own record. A submission form's "E. coli ..." now matches the database's "Escherichia coli ..." instead of being flagged as a different organism.
- **A sample's DDA run and its DIA run are no longer called re-injections.** `locate` offered them as two injections of one sample, so `--reinjections all` would have searched the DDA run as a DIA replicate. Runs acquired by different methods are now a question of their own: staff answer with `--acquisition DIA|DDA`, and the other method's runs are set aside and noted, including a sample whose only run is of the other method. Runs that differ by speed only need `--choose`, and the message says so. If the run names' methods cannot be read, `--acquisition` stops `locate` instead of being ignored.
- **`stage` says when `--apply` will refuse, and uses the submission's existing folder.** After a failed `locate`, the dry run said the checks would happen "on --apply", with exit 0; `--apply` then refused. The dry run now says "--apply will refuse" and exits 2. It also proposed a new PROT folder when the submission's raw files and an earlier analysis were already in another folder of the lab. It now stages into the folder that holds most of the submission's raw files or an analysis recorded for it. A folder that shares only a few file names is reported, not used. `--project-dir` names the folder, and `--service-dir` asks for a new one.
- **The analysis comparison counts tested proteins.** `compare_analyses.R` counted proteins that were listed but not tested as part of the protein total, and as "not significant" in the agreement table. Tested proteins are now the rows with a p-value, as everywhere else.
- **A podcast request that hangs no longer holds the job.** One Gemini request hung for over 20 minutes with no log line, until someone cancelled the job. Each request now logs when it is sent and every minute while it waits. After 10 minutes with no answer (`--request-timeout`) it is asked once more, and then the render stops with the resume message. The time lost this way in one render is capped at 30 minutes (`--request-timeout-budget`). Finished parts stay cached.

### Smaller fixes
- **Delivered README.md has no broken links in Bioshare.** Bioshare shows a folder's README.md inside the folder page but does not fix its links, so every file link in our delivered README.md opened an "Unable to locate the files" page. README.md now names its files without links, and its first line says to open `README.html` (double-click it, or click it in Bioshare's file list), whose links work. README.html is unchanged.
- **Board:** the skill now runs `board.sh whoami` before `connect` and uses the saved key's owner: a HIVE login can differ from the UC Davis address, and the wrong one sent an already-connected person a new link to approve. `references/board.md` explains how to add a colleague to a thread (`--with`, repeatable), and that everyone named must approve the thread before it opens.
- **HIVE readiness:** the printed google-genai fix (and setup's own install) now uses `--freeze-installed`, so it never changes packages other analyses use. `setup.json` records which skill version wrote it, and `skill_version.sh --check-hive` reports HIVE's readiness and says when that record may be out of date.
- **Watching a search:** watching a whole job chain now says which file DIA-NN is on, or how many files a multi-step search has finished, with the stage's plain-language note, instead of only "RUNNING".
- **SILAC figures:** a long subtitle listing the confidence filters now wraps instead of running off the figure.
- **Expert reviews:** SKILL.md step 8d now tells each reviewer to also write its findings to a file in the session's `logs/`, so a review survives a hand-back that fails.

## [Skill 2.13.0] — 2026-10-15

### SILAC: labelled samples, searched and analysed by the skill
- **SILAC experiments are now handled from search to report.** A SILAC DIA experiment (two or three channels, light/heavy or light/medium/heavy, on lysine and arginine) had to be set up by hand: the labels went in as parameter overrides, the ratio analysis was written separately and the client report was made outside the skill, without the Submission section, the audit or the survey. Now the skill asks about the labels in step 3 and does the rest: DIA-NN's plexDIA search, a ratio analysis, the standard report, the Methods and the reproducibility bundle. Details: `references/silac.md`.
- **The labels have their own option, and are recorded as the study design.** `estimate_params.py --labels silac2|silac3 --label-preset K4R6,K8R10` writes DIA-NN's plexDIA settings, with the label masses from UniMod. The skill asks which labels the lab used and never guesses them. Passing the labels as `--overrides` is refused, with the option to use instead, so they are no longer recorded as one person's override. Two of those settings (`--original-mods`, `--lib-fixed-mod`) also have label-free uses, and stay allowed as overrides when no SILAC label is involved.
- **The label is applied once.** The settings used by hand applied the SILAC label twice to a library predicted from the database (`K(SILAC)(SILAC)`), and DIA-NN reported it as "not supported". Tested on DIA-NN 2.7.0 on HIVE: declared the way the skill now writes it, the label is applied once. On a real triple-SILAC dataset the corrected search found the same peptides and proteins (20,980 against 21,049 precursors; 2,003 against 1,990 protein groups) and the same results (protein ratios agree at r = 0.99), with both the two-job search and the 5-step chain. A search set up the old way is stopped before anything is submitted, with the reason.
- **The skill asks how the channels relate.** DIA-NN needs to know whether the channels are independent samples (different strains or treatments, the usual case) or old and new protein from one culture (pulsed SILAC, protein turnover); without the answer it stopped and chose for itself. The skill asks; if nobody answers it uses "independent samples", and the Methods say this was a default, not confirmed.
- **A SILAC ratio analysis.** `run_silac.R` compares the channels inside each run: for each protein, the median ratio of its peptides in each run, centred so that the median detected protein reads 0 (so an even split of increases and decreases is built in, and the report says so), then a moderated t-test across replicates (limma) with Benjamini–Hochberg. A protein is tested when it has a ratio in at least 3 replicates, or in half of them (rounded up) when there are more than 6; this can be changed, and an unchanged minimum is marked as a default in the Methods, which give each comparison's minimum and number of replicates. Label swaps between replicates are handled.
- **The same identification filters as the standard analysis.** The SILAC analysis keeps only peptides that pass DIA-NN's experiment-wide and library confidence values as well as the per-run ones, the rule the label-free analysis already used. On a real triple-SILAC experiment this changed little: 821, 795 and 0 significant proteins in the three comparisons, against 816, 799 and 0 with the per-run filters alone; about 98% of them are significant both ways, all in the same direction. `--run-level-only` keeps the per-run filters alone (recorded); with it the analysis reproduces the hand-made one exactly.
- **Re-injections are not counted as replicates.** The skill now asks whether each replicate is a separate culture and mix. A second injection of the same mix is written under the same replicate; its ratios are averaged with the first injection's, never counted as another replicate, which would make the p-values too small. If nobody confirms that the replicates are separate cultures, the Methods say this was assumed.
- **What the ratios cannot show is listed too.** A protein detected in one channel and not in another has no ratio and cannot be tested; these proteins are listed separately, because the strongest losses often show only there. They are worded as a detection pattern ("detected in WT (4/4); not detected in KO (0/4)"), not as a test result: such a list has no error rate, and not detected does not mean absent. Each comes with how abundant it is where it was detected (its percentile among that channel's proteins), to tell an abundant protein from one near the detection limit. The tables keep both the centred ratios and the uncentred ones (amount per volume, including any mixing imbalance).
- **Leaving a run out is a recorded decision.** If the user decides a searched run should not be analysed (a failed injection), `silac.py design --exclude <run> --reason "..."` records it with their reason, and the Methods and the report list it. A run missing from the design without that stops the analysis, as for the standard DE.
- **The standard report, Methods and audit for SILAC.** The SILAC analysis writes its own record, which the report, Methods, audit, delivery and reproducibility steps read like any other. The report has the Submission section, the results at a glance, the figures (volcano plots, channel balance, peptides per channel), the channel-specific proteins, the audit and, for Core runs, the survey. The Methods describe the labels with their masses, plexDIA (Derks et al. 2023), the channel normalisation and the ratio statistics.
- **New audit checks for SILAC.** Unbalanced channels (for example one sample giving 70% of the signal when the mix was meant to be equal), too few replicates, low label incorporation when it can be measured (from a run of the labelled cells alone), and a search that declared the label twice. When incorporation cannot be measured from the data, the audit says so and how to measure it. Also: whether the zero of the ratios sits where most proteins are (when one sample's strongest losses fall below detection, the median moves; above 0.25 log2 the audit warns and gives the counts with the other zero), how many significant proteins rest on a single peptide in some replicate (about 30% on the real dataset; confirm the ones that matter), and how many proteins appear only in the per-sample matrix.
- **Reading "not significant".** The analysis notes give, per comparison, the change a protein must show to be called significant, using the cutoff Benjamini–Hochberg actually applied, and the true change that would be found 80% of the time. On the real dataset: about 0.32 log2 to be called significant in the largest comparison, and 0.42 log2 for 80% power.
- **Comparisons are named with their direction.** The Methods and the report say which group is over which (a positive ratio is higher in the first-named group) and whether the comparisons were chosen or the default. The scatter plot now shows two comparisons over the same reference by default, and its caption says that comparisons sharing a sample are correlated by construction, and in which direction.
- **Every default is labelled.** Every SILAC setting nobody chose (the confidence cutoffs, the minimum of replicates, the significance cutoff, the comparisons) is recorded as a default and marked "(DEFAULT — not user-confirmed)" in the Methods. The Methods also name DIA-NN's decoy channel when the search log has it.
- **Reproducible.** The reproducibility bundle re-runs the SILAC analysis, not the standard DE, and searches with the recorded labels. `reproducibility_log.R` repeats the ratio statistics in plain R and gives the same tables. A search picked up after a disconnect is pointed at the SILAC analysis, not the standard DE.
- **Not yet supported:** SILAC with Sage or in DDA, a pulsed-SILAC turnover analysis, chemical labels (mTRAQ, dimethyl), a seed spectral library, and protein-set tests on SILAC ratios. Each is refused with the reason.
- **Seen again: a plexDIA search writes no DIA-NN protein or precursor matrices,** although its log says it will (a second search, 2026-10-15). The SILAC analysis builds its tables from `report.parquet`.
- **The PRIDE / MassIVE sample sheet (SDRF) is filled in for SILAC.** A SILAC session now gets one row per run and channel, as the SDRF-Proteomics format asks of a multiplexed run: each row names its sample, its group and its label (`SILAC light`, `SILAC medium` or `SILAC heavy`, the PRIDE terms). It used to leave the label for the user to fill in. A re-injection of one mix is listed as the same sample (one biological replicate, numbered as a technical replicate). If the channel design cannot be read, the sheet falls back to one row per run and says why, instead of silently leaving the labels to fill.
- **SILAC results and a standard analysis are never mixed in one folder.** The standard analysis (`run_de.R`) now refuses a results folder that already holds SILAC ratio tables, as the SILAC analysis already refused the other way round; the audit, the report and the delivery read every results table in that folder, so a SILAC table could otherwise have been delivered as a standard result.
- **The README names the SILAC tables.** A SILAC session's README lists its ratio tables and channel tables instead of the standard DE's expression matrix, which a SILAC analysis does not write.

### Searches
- **A 5-step search started outside an analysis session no longer writes its recovery notes two folders up.** The notes that let a disconnected session pick a search back up (`RECOVERY.md`, `.recovery.json`) went into the folder two levels above the search output, assuming a session there; a search run elsewhere put them into, for example, a home folder, where they could replace another run's notes. Now they go into the session only when that folder is one, and otherwise beside the search output, and the submission says where. Retrying a step after a node fault updates the notes in the same place, so a resumed session sees the new job numbers and another run's notes are left alone.
- **A label-free search with a stray SILAC setting is refused in plain words.** A label-free parameter file holding a channel normalisation (a SILAC-only setting), or `--lib-fixed-mod` on a library predicted from the database, is still refused before anything is submitted, but the message now says what is wrong with a label-free search instead of describing a SILAC sample.

### Audit
- **The normalisation-stability check now says "not relevant" for an analysis on non-normalised quantities.** When the standard analysis reads DIA-NN's non-normalised quantities (for example a pull-down where the normalisation check chose raw quantities), DIA-NN's own normalisation never reaches the results, so the audit now says the check is not relevant instead of passing or warning about a normalisation the analysis did not use.

## [Skill 2.12.0] — 2026-10-15

### For Core staff: every analysis on the board
- **The skill asks Core staff which CoreOmics submission an analysis is for, and every analysis goes on the board.** It is asked once, with the first questions: a number (807 or PROT_0807), several numbers when an analysis combines submissions, or "none" for internal work such as a method test, QC, training or a tool comparison. Internal work gets a thread of its own in the board's "Core internal work" project, named after the analysis (`board.sh start --internal`); running the same test again under the same name returns the same thread. Brett is added to every thread.
- **Claudes can work unattended: a staff member's go-ahead in the chat starts the searches and other cluster jobs, and the board approves them by itself under 10,000 CPU-hours and 10,000 GPU-hours.** Until now (2.11) the Claude asked on the board before each search and waited for a person. Now it records each job on the board right after submitting it, with the hours its job scripts reserve (`--go-ahead chat --cpu-hours <cpu_hours_reserved>`), and never makes up a figure. A job of 10,000 hours or more of either kind is asked for on the board first and waits for Brett or another person in the thread; so does every job once one person's jobs pass 50,000 hours of either kind in 24 hours (the safety net).
- **The answer is kept with the analysis.** `session.py init --submission PROT_0807` (the main one first) or `--internal '<its title>'` writes it to `session.json`, and `checkpoint.py status` shows it, so a resumed analysis finds its thread without asking again. A submission goes on the board even when its CoreOmics record cannot be fetched yet. A fourth internal thread started within 7 days waits for the staff member to approve it on the board.
- **Several submissions in one analysis:** each gets its own thread, but the searches, jobs, QC and results are recorded in the main submission's thread only, so cluster time is not counted twice. `references/core-submissions.md` gives the one-session way to analyse them together and deliver into the main submission's share.
- **Each step that has a board record now says so where it happens** (session made, search submitted and finished, FRAN hand-over, QC, results ready, delivered), so no record is forgotten. Every board command also has its HIVE form for Windows staff, and connecting uses `<HIVE login>@ucdavis.edu` without asking.
- **People outside the Core are never asked for a submission number** and never hear about the board or CoreOmics; the access check gives them no CoreOmics route. The staff question now reads "Do you work for the UC Davis Proteomics Core (staff)?", and a number given at the start is not confirmed a second time when the files match it.

### The podcast
- **A CoreOmics submission gets its audio discussion by default.** Once the report is final, the Claude makes the "Signal to Noise" episode without asking and tells the staff member in one line; they can say no. Internal Core work is offered it in one line, and so is anyone else whose results go to a collaborator or the lab; for an outside user it is made only with their consent, because it is their data.
- **The consent for a Core run is recorded by itself, and only Core staff can claim it.** `make_podcast.py --core-run` records Brett's standing approval in `podcast.json` and refuses a session that names no submission; `--core-run internal` is for internal work and is refused on a submission's data. Both need the person running it on the Core staff list, checked by their HIVE account; what reaches the client says "Core staff", never the name.
- **Windows staff get the podcast too.** The whole podcast can run on HIVE: the Claude writes and checks the script there, and `make_podcast.py job` submits a small cluster job (1 CPU, 2 GB, 2 h) that renders the episode in Gemini voices, checks the audio and links it into the report. Its script and log are kept in a folder only you can read, so nobody can swap them before it runs.
- **On HIVE the podcast uses the Core's shared Gemini key**, for Core runs only and only while it is locked to a Core admin. A personal key on HIVE that others can read is refused. On a Mac a Core run uses Gemini voices with a key, or the offline `say` voices without one.
- **A podcast never holds up the report or the delivery.** No key, Gemini down or out of quota, a failed job, or a job still running when the rest is ready: one line to the staff member, and the results go out without it. The audio can be added later, beside the first delivery.
- **`setup.sh` installs google-genai** (2.25.0 or newer) in a step of its own that cannot break anything else; `setup.sh --check` reports it as `podcast`. When a render's audio check does not run, `verify.txt` says NOT RUN and why, instead of keeping the last render's check.

### For Core staff: CoreOmics on Windows
- **Windows staff can run every CoreOmics step with no Python on the laptop.** Each person's CoreOmics key is kept on HIVE (`~/.coreomics_token`, readable only by them) and check, identify, fetch, Bioshare and the email draft run there. The Claude moves a key saved on the laptop to HIVE itself (`coreomics_key_to_hive.sh`) without ever showing it; with no key yet, the person pastes a new one at a silent prompt in their own Git Bash window and it is saved only on HIVE.
- **A blank or wrong key file no longer replaces a working key on HIVE.** HIVE checks the key before saving it; a key that cannot be right is refused with the reason (never the key), and the key already there stays. A key file owned by another account gets advice that works (remove it and send the key again), and a key file others can read is refused.
- **Windows staff build the report on HIVE** (step 1c.7), and `conditions` runs there too, with nothing to copy back.

### Searches
- **Every search states the most cluster time it can use** (`cpu_hours_reserved` and `gpu_hours_reserved`: CPUs or GPUs × time limit × tasks, summed over every job it submits, read from the job scripts actually written). It is in `run_search.py`'s output, `search_provenance.json` and the top of `submit.sh`, for every engine; `cpu_hours.py` gives the same figure for any other job script. GPU-hours are 0 today, since no route asks for a GPU.
- **A run with `--` in its name is no longer silently left out of a DIA-NN search.** DIA-NN reads `--` anywhere on its command line as an option, so such a run was skipped and the search went on without it. A run whose folder has `--` is now searched through a link under the same name; a file name with `--` is caught at step 2 and searched under a new name with `--rename-dashed-runs`, which `conditions.csv` uses and `reproduce.sh` replays. Other paths with `--` (output folder, database, settings, FragPipe's DIA-NN route) are refused.
- **A search fails if any input run is missing from its report**, now for the 5-step DIA-NN chain and FragPipe DIA too. The message names each run, says whether DIA-NN could read it, and says not to resubmit. To go on without a blank or failed injection, `check_report_runs.py --accept-missing <run> --reason '<why>'` records the decision beside the report without rerunning anything.
- **Samples that were not reduced and alkylated, or were alkylated with another agent, can be searched correctly.** `--cys-alkylation` takes `cam`, `propionamide` (acrylamide), `nem`, `carboxymethyl`, `mmts`, `pyridylethyl` or `none`, applied the same way in DIA-NN, Sage, FragPipe and Radiant, and the Methods name the agent. Three on-bead searches had found almost no cysteine peptides (0.03–0.5%, against about 8%). The skill asks about it, and which agent, only for IP, pull-down and proximity-labelling experiments, or when the submission says on-bead.
- **Radiant now searches carbamidomethyl cysteine.** Its library had been predicted with no fixed cysteine modification; it now follows the same choice as the other engines, and an old library is rebuilt, not reused.
- **The sample-quality check warns when cysteine peptides are missing**, run by run: a run with under 1% cysteine precursors is flagged even when the cohort looks normal, with the likely causes (not alkylated, a different agent, or a naturally cysteine-poor sample).
- **Mass accuracy: two needless stops are gone.** A one-file Orbitrap search (a QC or method test) now uses its own run's measurement instead of failing for want of a second run. Pull-down cohorts whose sparse runs disagree now get a warning, shown in AUDIT.md and the report, when their median is at or below the SOP floor and no run is above 1.5× it.
- **A search folder with a `.` in its name works** (a re-injection's `…01dup2`, a `v1.2`). DIA-NN cut its output names at the last `.` of the whole path and wrote the library one folder up; every output name now carries an extension.
- **`run_search.py --exclude <nodes>` keeps every job of a search off nodes known to be bad**, and `node_fault.py retry` keeps them excluded along with the failed ones.
- **plexDIA (`--channels`):** in one Core run DIA-NN 2.7 wrote no protein or precursor matrices; use `report.parquet`, which has a `Channel` column (`references/search-engines.md`).

### Which file is which sample
- **An HT plate's file list from STAN is checked, not trusted.** STAN assigns runs by tray: a 96-sample plate came back as 136 files, 41 of them other projects' runs, with one real run missing and every check passing. Now only runs named for the submission are searched, and the plate stops for staff when any listed run is not, when the names show different acquisition methods, or when a sample has no run or a run is no sample on the CoreOmics record.
- **HT plates stop less often for nothing.** Two samples sharing a name are asked of staff (`--choose`), a time point in a sample name (`24m`) is no longer read as the method, a missing CoreOmics record says to put it on HIVE, and the STAN share-link route checks the sample list again.
- **Sample identifiers match whole tokens, in the sample part of the name only.** `XY1` no longer matches XY10–XY19, and a numeric label such as 1234 no longer matches a run's acquisition counter. A label that still names several runs is asked, never guessed.
- **Runs named for the person and numbered for the sample are proposed, never taken.** When a sheet's ids are initials and a number (AB4) and the runs carry the person's name and the number (`<date>_ABSmith_100spd_4_…`), `locate` proposes the run and staff confirm it with `--choose`.

### Results and statistics
- **A protein measured in neither group of a comparison is no longer tested in it.** With three or more groups it was given p = 1 and counted in that comparison's multiple-testing correction. Its fold change and p-values are now empty (the row stays), and the DE tables, counts, Methods, DE-LIMP session and protein-set tests all leave it out the same way.
- **A covariate can be a measurement, not only a label.** `run_de.R --numeric-covariates` fits a continuous covariate (a bait intensity, an age, a run depth) as one slope, instead of failing with "Design matrix is not full rank". Every sample needs a real number (nothing is filled in), and how each covariate was fitted is in the Methods, the report and `reproduce.sh`.
- **A covariate that nearly matches the groups of a comparison is flagged, and the comparison is named** in the Methods, the report and AUDIT.md: adjusting for it can remove part of the effect being tested. It is judged per comparison (80% or more explained by its groups, no overlap, or a standard error widened 2.2-fold or more by the design).
- **The normalisation check is held to the model it checked.** The check's DEs and the final DE must use the same design; a different method, formula, numeric covariate or block is refused. A check from before 2.12 still lets the DE run, and the Methods ask for confirmation.
- **A contaminant group that is really the sample's own protein is flagged** (audit check `contaminant_evidence`). When every peptide behind it is also made from a protein of the searched organism (or differs only by I/L), the audit says to report it as that organism's protein, never as the contaminant's species or an added standard. In a human tissue study, horse myoglobin (`Cont_P68082`) had been reported in every run on peptides human myoglobin shares; `fetch_fasta.py --drop-contaminant Cont_P68082` now leaves such an entry out, recorded in the Methods.
- **Runs left out of the DE are recorded with the reason.** `collect_conditions.py --validate --exclude <run> --reason '<why>'` passes a report run deliberately left out of `conditions.csv`, and the reason appears in the Methods and the report. A run that lost every identification is said as such, and an unreadable decisions record says "reason not read", never "not recorded".
- **The protein-set tests fail loudly when they cannot run**, naming each annotation package that does not load and the fix; the DE and set tests now run in one job that fails when they do.
- **The bait is asked once**, and a whole added proteome (more than 10 sequences) is counted, not listed, with the bait asked for by name.
- **Core staff are no longer asked the sample type**, in any analysis; the submission record describes the samples. It is asked only when a choice depends on it (one keratin question for hair, skin, nail and the like). Outside users are still asked once, with "don't know" accepted.

### Reports, Methods and delivery
- **A report without differential expression has its own delivery.** `core_submission.py deliver --mode no-de` delivers a QC report, an identification list or results before the statistics, copied and verified like any delivery; a later analysis delivery goes beside it. A delivery with no DE is held with a plain message offering this route, instead of an error.
- **The email draft follows the delivery and checks the addresses.** A no-de draft says the statistics are not included; each recipient is named with where the address came from, and an address that cannot be right, or looks like a typo of ucdavis.edu, is flagged before anyone sends it. A draft is never made from the HIVE copy without addresses, or from another submission's record.
- **No server path or database build warning reaches the client's Methods.** Build warnings go to the Claude to tell the staff member, and file paths are cut to the file name, leaving prose such as "S-Trap (ProtiFi)/Trypsin/Lys-C" alone.
- **A large added proteome is counted, not listed, in the Methods** (more than 10 sequences: the count, file name and SHA-256); a second organism's proteome had put a 145 KB line of accessions into a client's Methods. `provenance.py` reads the database record from a file (`--fasta-info-file`), so a large one no longer fails with "Argument list too long".
- **When a check cannot run, it says so.** The audit says "not assessed" or "could not be read" instead of PASS or a crash, a damaged `session.json` is reported when an analysis resumes, and `setup.json` says why DE is not ready.

### Setup
- **`setup.sh` installs the GO annotation packages so that they load** (from Bioconductor's annotation repository for the environment's own release, never conda's builds that did not load), and `--check` reports for each package whether it loads, with the fix.
- **`setup.sh` makes sure R can read DIA-NN's report** (nanoparquet), installing it on its own so it can never downgrade R 4.6 to 4.5.
- **Updating the skill works on Windows.** `claude plugin update` could say "already at the latest version" while a newer release was out, on a laptop with no GitHub SSH key. `skill_version.sh --update` now refreshes the skill catalogue over HTTPS, updates, and checks the installed version against the latest release; step 0 checks for an update in every mode (`--check-update`), and the install pages use the HTTPS address.

### Safety
- **Text the Claude writes into a command can no longer run as a command.** Board posts, skill problem reports (`report_issue.sh --what-file -`) and the decisions log (`log_decision.py --what-file - --why-file -`) take their text on standard input or from a file; titles and reasons are single-quoted, and text sent to HIVE avoids the characters the shell acts on. Before, a `$(…)` in an error message would have run, on the computer and again on HIVE.
- **Job scripts can no longer be redirected by a planted link.** Session folders are group-writable; every job the skill writes (searches, podcast, FRAN, deposit, delivery) is written without following a link left at its name, and its log path is quoted, so a folder with a space in its name works.
- **On HIVE, a submission's folder in your home is readable only by you.** HIVE home folders are open to every HIVE account; `core_submission.py` now makes `~/core` and each `~/core/PROT_xxxx` private, keeps the full record (with addresses) in a private folder, and refuses a folder another account put there.

## [Skill 2.11.2] — 2026-10-07

### For Core staff: the board knows which searches are still running
- **When a search is submitted, the Claude records its folder on the board as running** (`where --search-output ... --search-engine diann --fran-handover running`), so the project's FRAN panel says "Search still running" instead of offering a Send button. The board cannot see HIVE; this is how it knows.
- **Every search folder is recorded as a search** (`--search-output`, one per folder), including QC and comparison searches, so each appears in the FRAN panel with what happened to it.
- **Results are on the board as soon as they exist**, not only at delivery: when the analysis report and DE tables are made (or redone), the Claude records where they are (`where --report ... --extra "DE tables=..."`) before posting the counts.

## [Skill 2.11.1] — 2026-10-07

### For Core staff: the board shows each search's FRAN hand-over
- **The board knows which engine ran each search and what happened with FRAN.** After the skill hands a finished search to FRAN (step 7c), the Claude records the search folder on the board with its engine and the hand-over's result (`where --search-output ... --search-engine diann --fran-handover <status from fran_deposit.json>`). The project's FRAN panel then says "Handed to FRAN", or why the search was kept out (a QC run, unfinished), instead of offering a person a Send button. Nothing new is sent to FRAN: the skill's own hand-over, with FRAN's QC and species checks, stays the only route.
- `scripts/board_client.py` updated from the board's repository (sha256 pinned in `tests/test_board.py`).

## [Skill 2.11.0] — 2026-10-07

### For Core staff: the Core Project Board
- **Each CoreOmics submission gets a thread on the Core's board** (https://core-board-ucd.azurewebsites.net), where Brett and the staff see the analysis: where the files are, the cluster jobs, QC, results and the final summary (`references/board.md`).
- **Nothing to copy or type.** The first time on a computer, the Claude shows a link: open it, press Connect, sign in with your UC Davis password and Duo, press Confirm. The Claude makes and keeps its own key (`scripts/board.sh connect`). It works the same on Windows.
- **The submission goes on the board by itself.** Right after `fetch`, the Claude creates the project (if it is new) and its thread, with Brett added (`scripts/board.sh start`). Brett sees it under "Needs you" and approves it, and can add his own Claude.
- **Cluster time stays a person's decision.** The thread starts at the Analyze level with no CPU-hour budget; before each search the Claude asks on the board, and the person (Brett at 100 CPU-hours or more) approves with one click.
- **The board never holds up an analysis.** If it is down, not connected, or the thread is not approved yet, the analysis carries on and the Claude posts at the next milestone. The one wait: cluster time past the thread's CPU-hour budget is asked for on the board first.
- **Claudes use only the board's API**, never its web pages; a Claude never approves, gives itself cluster time, or connects itself. `scripts/board_client.py` is the board's own client, copied unchanged (sha256 pinned in `tests/test_board.py`).

## [Skill 2.10.0] — 2026-10-01

### Results
- **IPs and pull-downs default to non-normalised quantities.** The experiment type is recorded once (from the submission, confirmed with the user) and gives the default; the normalisation check (step 8) tests the data for every type, and when they disagree it stops and shows normalised and non-normalised side by side for a person to choose (`experiment_type.py`, `normalization_check.py`, `run_de.R --quantities`).
- **The normalisation check cannot be skipped:** with an experiment type recorded, `run_de.R` refuses a final DE without it (`--normalization-check`), and an analysis delivery is held until the check is decided. A DE from before 2.10 goes out once Core staff acknowledge it (`normalization_check.py ack-legacy`).
- **Fractions are two kinds:** fractions combined for depth stay normalised; separation fractions compared with each other (SEC, gradients, complexome, organelles) default to non-normalised, as the DIA-NN README advises.
- **Your own sequences can be added to the database** (`fetch_fasta.py --add-fasta`, e.g. an EGFP bait); a contaminant that is mostly the same protein is removed so it cannot take their peptides, and one that shares only a few is kept and flagged.
- **An added sequence is the bait's candidate:** the user is asked which one is the bait (`experiment_type.py set-bait`); until they answer, the data check uses the one added sequence and says it is unconfirmed, and with several it uses none.
- **DIA-NN's Normalisation.Instability is checked**; runs above 0.3 are flagged.
- **A Sage LFQ window that misses the measured MS1 offset now stops** with the corrected re-run command, instead of only warning.
- **FragPipe DDA writes the whole protein group**, so a contaminant anywhere in a group is found.
- **The Methods name each pipeline's own contaminant rule**, not DIA-NN's for every engine.
- **The sample type is asked and recorded**, never guessed from file names.
- **A cut-short one-per-gene download stops** instead of quietly becoming the full proteome; downloads are retried and checked.
- **A `--path` database records the organism you named**, so the Methods and FRAN have it.

### Which file is which sample
- **When a label matches several runs, or two samples share a label, staff decide which run is which** (`--choose`); the skill never picks.
- **A file listed twice is searched once and flagged**; two different files with the same name stop the search with a clear message (searching both is 2.11).
- **Re-injections get one decision** for the whole submission: `--reinjections latest|all|ask`.
- **HT plates: `locate --files-from` matches runs by sample name**, the way the plate names them.
- **The Core LIMS `.xlsx` sample sheet is read directly**; a condition per replicate (`<sample>_mix_1` … `_5`) becomes conditions plus replicate numbers, or is asked about, and `core_submission.py conditions` relays that question.

### For Core staff
- **The instrument's QC around each project is checked against STAN** (`qc_bracket.py`). It is staff-only: a "check" or "concern" verdict, a file that could not be placed in time, or a missing check holds an analysis delivery until a staff member acknowledges it. A check made for a different file list is refused until it is re-run. The acknowledgement names a HIVE login on the Core staff list (`CORE_STAFF_FILE`); agent-like names are refused.
- **Sign-offs are a person's:** a normalisation decision, a QC acknowledgement and a pre-2.10 DE's acknowledgement need the HIVE login of someone on the Core staff list (`/quobyte/proteomics-grp/.config/core_staff.txt`, trusted only when a Core admin owns it); agent names are refused, and what reaches a client says "Core staff", never the name.
- **No database credential is read from a group folder** (`fran_deposit.py`).

### Running on HIVE
- **The DIA-NN chain's array tasks are sized to the queue's per-user CPU cap**, from a measured floor of 8 CPUs per file; their wall clock is 4 h at 16 CPUs, scaled up with fewer (8 h at 8, 16 h at 4) — all but 32 of 6,182 real step-2 tasks (p99 160 min, p99.5 248 min; the slowest take `--time-per-file`) — and they keep 64 GB for steps 1b and 2 (48 GB for step 4). Both limits come from HIVE's own records of real Core runs (sacct) and a measured slowdown at fewer CPUs; `run_search.py --mem-per-file` / `--time-per-file` change them.
- **A folder with a space in its path runs:** every path in the generated chain jobs is quoted.
- **A node that cannot reach the storage is a node fault**, not DIA-NN's: `node_fault.py` judges each failed task and prints the command that resubmits them on other nodes (the retry is a command, not automatic; one at a time per search folder).
- **With `--beside`, a re-analysis goes beside the earlier one as `_v2`, `_v3` …**; re-finalizing an unchanged analysis logs and posts nothing new.

### Packaging
- **The development sandbox (`ucdavis-proteomics-dev`) is no longer listed in the plugin marketplace**; the stable skill is the only plugin offered.

### Records
- **The reproducibility bundle records the environment the DE ran in**, not setup's.
- **An override is recorded as the user's choice**, with who set it and why, never as an SOP.
- **A relative `--cfg` is never read from a guessed file.**

## [Skill 2.9.1] — 2026-10-01

- **STAN's database credential must never be shared.** `/quobyte/proteomics-grp/brett/.pgfarm_token`
  holds the long-lived secret of STAN's service account, not a 7-day token. Earlier versions
  (`ht_manifest.py`, `references/ht-submissions.md`) called it safe to copy group-readable and
  looked first for a copy at `/quobyte/proteomics-grp/etc/pgfarm_token` (none was ever made).
  That path is no longer searched, the docs say never to copy it or make it group-readable, and
  staff use the hosted dashboard with a share token (`--http … --share-token-file`).
- **HT plate files named `<date>_PROT_<n>` are now found.** `locate` recognised only
  `<date>_<n>`, so a plate named `20260930_PROT_0807_…` was matched sample by sample and none of
  its 96 samples were found; it now exits 4 for `ht_manifest.py`. Run counters such as
  `Ex08312026_380_JE21` still do not count as a submission number.

## [Skill 2.9.0] — 2026-09-30

Staff laptops and HIVE are checked against the Core's current release, and the Core can leave
notes for a staff member's Claude. DIA-NN searches DDA data through the parallel chain, keratin
samples keep their keratin, and Sage results are filtered and described correctly. The report
can travel as one file with its audio, comparisons with few significant proteins get
protein-set tests, Core runs ask the client how we did, and every analysis keeps a record of how
it was done.

> **Re-run the DE of any earlier Sage or FragPipe DDA search.** Before 2.9.0 the Sage adapter
> passed Sage's decoys and its failing MS1 peaks into the DE. Both adapters also wrote protein
> IDs as full FASTA headers (`sp|Cont_P02769|ALBU_BOVIN`), which the contaminant filter cannot
> read, so no Sage or FragPipe DDA DE ever removed a contaminant. Both are fixed (below), and both
> change the numbers. On one real HeLa run:
> - 19–20% of proteins per file changed their summed Sage intensity by more than 10%, and 177 of
>   3,765 protein groups existed only through decoy or failing rows;
> - 171 contaminant groups (686 peptides) had been tested as sample proteins while the methods
>   said "Contaminants: none". 101 of them also named a human protein: of the 120 human proteins
>   named, 57 keep other peptides, and 63 were seen only through peptides shared with a
>   contaminant, so they now leave the DE with it;
> - the FragPipe search of the same data had 72 contaminant groups in its DE.
>
> The search itself does not need to be repeated, but **re-adapt first, then re-run the DE**:
> run the search's own `run_search.py` command again with `--adapt-only`, which only reads the
> existing output. A report adapted before 2.9.0 still has the old protein IDs and declares
> nothing about its engine: a DE on it as it stands still misses its contaminants and still
> calls its quantities DIA-NN MaxLFQ. Earlier
> FragPipe, AlphaDIA and Radiant reports likewise need re-adapting before their DE describes
> them correctly.

### Keeping every copy of the skill current
- **Step 0 checks the laptop, its HIVE copy and the Core's release** (`skill_version.sh
  --check-hive --mode hive_remote`), in one SSH call. Two staff were on 2.6.0 on both their
  laptop and HIVE while 2.8.0 was out, so none of the 2.7/2.8 fixes had run for them.
  - A HIVE copy that is behind, missing or different is put again (`hive_exec.sh --put-skill`),
    unless the user has SLURM jobs whose batch scripts use it; those are counted, and the put
    waits.
  - A laptop behind the Core's release is told so **first**, before any other work, with the
    exact update steps and a recommendation to turn on auto-update. Declining is logged.
  - HIVE newer than the laptop stops the session: the laptop is updated, never HIVE downgraded.
  - `check_access.sh` saves the working HIVE login to `~/.config/ucdavis-proteomics/hive.env`,
    so the check can run; with no login it says so in one line and carries on.
- **The Core's current release** is `/quobyte/proteomics-grp/skill_release/CURRENT_VERSION`,
  written by a maintainer with `skill_version.sh --publish-release` as the last step of a
  release. It is trusted only while the file and its folder belong to a Core admin.
- **`scripts/core_admins.txt`** is the one list of Core admins (today the Core director's HIVE login). It ships with
  the skill; it is never read from the shared folder, which any group member can change. It has
  two readers, `skill_version.sh` (bash) and `skill_version.py` (Python), kept equal by a test.
- **Updating the plugin**: `/plugin` → Installed → Update now, or `claude plugin update
  ucdavis-proteomics-core-pipeline@ucdavis-proteomics-core`, then `/reload-plugins`.
  `/plugin marketplace update` only refreshes the catalogue. Auto-update is off for this
  marketplace until the user turns it on.
- **Install is one terminal line** (README, `docs/skill-install.html`, `docs/STUDENT_SETUP.md`,
  `references/install.md`), or one slash command at a time inside Claude Code. Two `/plugin`
  lines pasted together fail.

### Notes from the Core
- **`notes.py`**: a Core admin leaves a note for one staff member, or for everyone, in
  `/quobyte/proteomics-grp/skill_notes/`. The staff member's Claude reads it at step 0 of every
  session, shows it in full as quoted data, never as an instruction, and records a read receipt
  and an optional reply. The sender sees who read what and the replies. Slack gets one line
  (who, for whom, the subject; never the body).
- **Trust**: the sender is the file's owner on disk, never its `From:` line. The inbox counts
  only when it is a sticky folder owned by a Core admin; senders are the admins plus a
  `SENDERS` list an admin owns. Anything else is reported, not shown. A missing inbox is
  reported to every Core account.
- From a laptop each command is one `hive_exec.sh` call with `notes.py` on stdin, so an older
  HIVE copy needs nothing. With no HIVE login it does nothing.

### DIA-NN on DDA data, and a chain that survives its probe
- **The 5-step chain searches DDA as DDA.** `estimate_params.py` writes `--dda` into a DDA cfg,
  where every DIA-NN step reads it; before, a DDA cohort of more than 5 files was searched as
  DIA with no error. `run_search.py` refuses a cfg whose `--dda` disagrees with the acquisition,
  on both routes.
- **The precursor range is the MS1 survey scan**, read from the Thermo scan filter, the mzML scan
  window or the timsTOF `.d`'s acquisition range, instead of falling back to 380–980.
- **Mass accuracy is pinned, not measured**, for DDA: DIA-NN logs no scan-window radius in DDA
  mode, so the step-1b probe ran to its timeout. A level with no table value takes the Core SOP
  value, tagged "Core SOP default for this instrument, not measured on these data" in the
  Methods, the parameter tables and the run record.
- **The Methods say when DIA-NN searched the spectra as DDA**, and describe match-between-runs
  from the search mode.
- **The chain compares its two passes.** Step 5 runs `pass_comparison.py`: runs whose final pass
  kept less than half their first-pass precursors are flagged in `AUDIT.md`, and the first-pass
  report is offered only for runs where it has more rows after run_de's own q-value filter.
- Array tasks write to their own `--out`; `submit.sh` writes `jobs.txt` before anything can
  close its output; a ddaPASEF `.d` whose frame types and tables disagree is asked about, not
  guessed.
- **A stale NFS handle no longer kills step 1b.** On Flinders NFS the window/mass-accuracy
  probe died with ESTALE in 62 of 261 step-1b jobs, taking every chain behind it. Its log is
  now written on the node and published to the workdir, and reading it survives ESTALE.
- **Only the probe's own machinery failing lets the search carry on.** A crash or an unreadable
  log is retried once; a crash or unreadable log again, or a time limit, falls back: steps 2–5
  run on `--window auto` and the documented + SOP mass accuracy, tagged DEFAULT
  (`probe_fallback.py`). Everything else still stops the chain with its reason: an implausible
  mass accuracy logged by any run, runs DIA-NN finished without logging one (a wrong FASTA,
  failed injections), no .NET or a DIA-NN that will not start, and a bad configuration.
  - A fallback is recorded in the provenance with stable `scan_window.mode` / `mass_acc.mode`,
    stated in the Methods, and shown as a CAUTION in `AUDIT.md`, the report's Results at a
    glance, the run record, `checkpoint.py status`, the Slack post and `watch_run.sh --all`.
  - `--window 0` or `--mass-acc 0` is invalid, never "auto".
  - A new search in the same folder sets the earlier search's probe outputs aside
    (`.stale-<time>`, never deleted, and only once nothing refuses it), so an earlier search's
    fallback never marks the next one; the run record copies `probe_fallback.json` only when
    the provenance says the search fell back.

### Keratin samples (hair, wool, feather, skin, nail)
- **Step 3 asks whether the samples are keratinous.** For a keratin sample, `fetch_fasta.py
  --keratin-sample` removes every keratin-family contaminant entry from the search database, and
  `run_search.py` refuses a database that still holds one: DIA-NN's `--cont-quant-exclude` would
  keep every peptide shared with the sample's keratins out of quantification.
- **`run_de.R` keeps a keratin sample's keratin** when the database still holds such entries,
  while trypsin, BSA and the rest are removed. Another species' keratin counts only when the
  precursor also names a sample protein. The methods, report, brief and auditors say what was
  kept and whether its quantities could still be under-counted.
- A run that is not a keratin sample is unchanged: same database, DE tables and methods.
- On a real hair DDA dataset, the normal setting removed 25–50% of the main hair keratins'
  precursors; the keratin-sample setting kept them, with no other protein lost.
- **FragPipe's `contam_` is a contaminant tag too** (`CONTAMINANT_TAGS`), in the filter and the
  keratin rule. A FragPipe search on a database built with Philosopher's `--contam` is refused,
  because FragPipe's DIA route drops that tag.

### Sage, FragPipe, AlphaDIA and Radiant results
- **Sage keeps only its valid MS1 quantities**: decoys and rows above Sage's stored q-value
  cutoff are dropped, with the counts per file in `sage_adapt.json`.
- **Sage protein IDs are bare accessions**, as DIA-NN writes them, so the contaminant filter and
  a keratin sample's exemption work on Sage reports (`protein_ids.group_accessions`). Radiant's
  groups are read the same way.
- **Sage's LFQ mass window is checked** (`sage_lfq_check.py`). Sage integrates MS1 only within
  ±5 ppm; a run whose MS1 error sits outside that identifies normally but quantifies badly. The
  check warns in the job log, at `--adapt-only`, in `AUDIT.md` and the report. It corrects
  nothing yet.
- **Sage converts its input inside the SLURM job** (ThermoRawFileParser for `.raw`), never on the
  login node.
- **Every engine's DE names its own quantity.** A Sage DE is "Highest-peptide intensity + limma"
  (each protein's value is its most intense peptide) with a caveat, not "DIA-NN MaxLFQ"; FragPipe,
  AlphaDIA and Radiant name their engine's protein quantity and citation.
- **FragPipe DDA reports the accession**, so `compare_searches.py` finds the proteins it shares
  with DIA-NN (it found 0 before), and names the accessions two groups shared.
- **Contaminant counts are in the report's own unit**: distinct precursors (DIA-NN), peptides
  (Sage) or protein groups (an engine's own protein quantities), never report rows. A
  contaminant group shared with a sample protein is counted, with the sample proteins that lost
  peptides to it; for a protein-level report that loss is "not computed", never 0.
- **Whether DIA-NN ran with `--cont-quant-exclude` is read from the run**: its log, including any
  `--cfg` file the logged command names, or its parameters file. It is "not recorded" otherwise;
  it is never assumed, and never taken from the FASTA's recommendation. The methods, the
  keratin lines and the run record (`SEARCH_LOG.md`) all say it that way; before, the run record
  restated the FASTA's recommendation for every engine.

### The report with its audio, in one file
- **`make_podcast.py share <session>/output`** writes `output/Analysis_Report_with_audio.html`.
  It is the report with the audio discussion and its transcript built in, so it is the one file
  to send when someone wants the report with the audio. (The Listen card in
  `Analysis_Report.html` links `podcast/`, so that file sent alone has no audio.)
  - The speech is re-encoded to AAC (`--kbps` 32–64, default 48).
  - The file is read back before it is kept: the audio must decode to the episode's length, and
    nothing may point outside the file. Where a Chrome, Chromium or Edge is found, a headless one
    also plays it. A file that fails any check is removed.
  - Above ~18 MB (~25 MB as an email attachment) it says to use Bioshare instead.
  - It carries the sha256 of the report, the episode and the audio, so "current" is checked by
    content. `finalize` builds it or brings it up to date, and records the result in
    MANIFEST.txt. `deliver` ships it only while it is current, and the README, email draft and
    AGENTS.md name it only then. A copy that cannot be updated becomes `*.stale.html`, which is
    never zipped or sent.

### "How did we do?" and a GitHub star
- A Core run's report and its `.md` twin end with a link to the Core's 5-minute survey. So do the
  session README, AGENTS.md, the delivery README and the email draft. The link is
  `https://feedback-ucd-proteomics.azurewebsites.net/?prot=<PROT number>&src=<where>`
  (`core_submission.FEEDBACK_URL`, `feedback_url`, `feedback_line`: one definition).
- The one test for a Core run is `submission_report.core_run(session)`: a CoreOmics record
  attached, or one announced whose record file is missing. It fails closed: a run outside the
  Core, or one where this cannot be told, never shows the survey.
- After `make_podcast.py link`, the line also asks about the podcast. A Core episode may mention
  the survey in words at its sign-off; `check` fails a survey invitation in a non-Core episode.
- **Every report asks for a GitHub star**, just before a Core run's survey line (or last outside
  the Core), in the HTML, its `.md` twin, the PDF and the shareable report. The words live in
  `core_submission.star_line`; the address is `plugin.json`'s `repository`.

### Protein-set tests (`run_sets.R`)
- `run_de.R` names every comparison with fewer than 10 significant proteins
  (`de_provenance.json` `set_tests.suggested_for`, `--sets-trigger`), and the skill offers
  protein-set tests for it. They can be run for any analysis.
- **camera** (competitive) and **fry** (self-contained) run side by side on run_de's own model:
  `run_de.R` writes `set_test_inputs.rds`, and run_sets.R checks that its refit reproduces run_de's
  t to 1e-6. `--block` is handled: a random block goes to fry, and camera uses the blocked fit
  with block-whitened residuals. Adjustment is BH across sets within each comparison.
- **Sets are a-priori only**: GO (offline; `setup.sh` installs the annotation), Reactome, or a GMT
  file whose origin must be given. A list drawn up from the results is never used.
- **Checks on every call**:
  - each test repeated with log2 run depth in the model;
  - DPC presence-call fractions, and measured-only versions of both tests;
  - fry re-tested on four other residual bases;
  - camera's power measured per comparison. Where it is low, as in pulldowns, its count of zero
    is not a result.
  - Residual effects use one canonical basis, because R's QR gave different signs on different
    HIVE CPUs and moved p-values by up to 0.09.
- **Pulldowns (`--ip-map`)**:
  - a control-vs-control contrast for the lysate background;
  - between-condition tests relative to each bait's complex: the interactome is chosen on
    enrichment over the control pooled over conditions, at least 4-fold; the interactome
    median is the reference, and the bait protein is the cross-check.
  - Stated limits:
    - with the 4-fold minimum, **losses from a complex are harder to detect than gains**
      (nearly undetectable in the simulation), and finding nothing is not evidence that the
      complex lost nothing;
    - random null sets run at about 0.07, not 0.05, in the pulldown simulation;
    - calls that depend on the reference are unresolved, not findings.
- **Outputs and wording**:
  - Writes `Sets_<contrast>.csv`, `Sets_baitnorm_<contrast>.csv`, `sets_members.csv`,
    `sets_provenance.json`, `sets_methods.txt` and `sets_<contrast>.png`.
  - The report, the analysis brief, AGENTS.md and methods.md quote the record's own reading,
    for example "not detectable in this design", with n and residual df, never "unchanged".
  - Validation on the mouse-brain IP cohort (v2), and the simulations behind the defaults, are in
    `references/set-tests.md`.

### Reproducibility: exact numbers need the same CPU family
- DPC-Quant's per-protein BFGS fit runs through OpenBLAS's CPU-specific kernels. On the mouse-brain IP
  cohort (v2) the same inputs, software and command gave |ΔlogFC| ≤ 0.0022 and 0 changed significance calls
  between zen4 and zen2 nodes. Each family reproduced its own tables exactly.
- `run_de.R` now records the machine in `de_provenance.json` `compute` and at the top of
  `sessionInfo.txt`: the CPU model, the BLAS and LAPACK libraries, `OPENBLAS_CORETYPE` as found,
  and on SLURM the node's CPU-family feature.
- `REPRODUCE.md` names the family. To match an earlier HIVE run, submit with
  `sbatch --constraint=<family>`. Never pin `OPENBLAS_CORETYPE`: it segfaulted `dpcQuant`.

### The record of the analysis: decisions log and conversation (Core-internal)
- **`log_decision.py`** appends each decision (conditions, defaults, contrasts, overrides) with
  the user's words or the evidence to `logs/decisions.md`. It works with any agent.
- **`save_transcript.py`** (Claude Code) saves the analysis conversation, **redacted**, to
  `logs/conversation/`. It adds `index.json` and a readable `conversation.md`.
  - Redaction covers the skill's secret patterns, the secret values this computer holds, and
    anything named like a key, token, password or webhook.
  - It runs after the search is submitted, after DE, and at `finalize` (a MANIFEST line).
  - `--hive` saves it from the laptop for a hive_remote session.
- **The plugin hook** (`hooks/hooks.json` → `transcript_hook.py`) saves it before a compaction
  and at the end of the session. It does nothing in a conversation not recorded for an analysis.
- **One conversation, several analyses**: each analysis keeps only its own part.
  `--transcript-from-now` starts a copy at `init`; use it whenever the conversation has touched
  another client.
- **Both records are Core-internal**, because redaction cannot catch a secret written as prose:
  - `deliver` never ships them, and the session zip leaves them out;
  - the files are 0640, in a 0750 folder;
  - the session's own AGENTS.md gains a "Reviewing this analysis" checklist; the collaborator's
    copy does not.

### CoreOmics keys: staff can make, save and check one
- **`core_submission.py check`** says in plain words whether this computer's CoreOmics key
  works, and what to do if it does not: `ok`, `no_key`, `key_in_wrong_place`, `key_empty`,
  `key_malformed`, `key_unreadable`, `key_rejected`, `no_lab_access` (ask the Core director to add the
  account to the Proteomics lab), `unreachable` or `unexpected`. It never prints the key.
  SKILL.md step 1c runs it before `fetch`. Two staff could not reach CoreOmics from the skill:
  nothing said how to get a key, and on a Windows domain account a key saved in Git Bash's `~`
  sat where Python never looks.
- **Making and saving the key is documented** (CoreOmics Profile → API Key → Create;
  `references/core-submissions.md`). The user saves it in their own terminal with ONE line that
  never shows it or keeps it in the history, and on Windows writes it to `USERPROFILE`, where
  Python reads it. An empty Enter keeps a key already saved. The key never goes into the chat.
- **Finding the key**: `COREOMICS_TOKEN`, then Python's `~`, then `$HOME` when that is another
  folder. A UTF-16 or BOM-marked file gives the key itself. A key saved under the wrong name
  (Notepad's `.txt`, a dropped dot), or on Windows in Documents or OneDrive, is named with the
  `mv` that fixes it.
- **The key stays secret**:
  - a key with a space, line break or quote is refused before any request (before, a two-line key
    file made `fetch` print the key in a traceback);
  - a redirect to another scheme, host or port is refused, because urllib would have sent the
    key along with it;
  - anything a server echoes back is redacted in `fetch`, `identify` and `bioshare`;
  - a 401/403 is read only from CoreOmics' own JSON, so a proxy's error page is not reported as
    "no lab access".
- `save_transcript.py` redacts the key from every place `core_submission.py` reads it.

### CoreOmics submission numbers
- **A submission number is ASCII digits only.** Python's `\d` also matched Arabic-Indic and
  fullwidth digits, which `int()` reads, so a number in those digits (`٩٧٥٦`, read as
  PROT_9756) attached a Core submission and made a run the Core's.
- `record_run.py` now reads PROT numbers with `core_submission.normalize_submission`, which is the
  one definition, instead of keeping its own copy.
- `identify` asks for a number only when there is evidence the data are the Core's. Otherwise it
  asks "Were these samples run by the UC Davis Proteomics Core?" first, and on "no" the analysis
  carries on without a submission.
- `report_files.py` holds the shareable report's file name (`SHARE_NAME`), with no imports, so
  `make_report.py` can read it.

### Sessions start fresh
- **A new request is a new analysis** (`session.py find-prior`, SKILL.md 1b and 0c). An earlier
  session on the same data is mentioned in one line, and nothing is read from it unless the user
  asks for a re-analysis. Only work the user is coming back to is a resume; a running search is
  never resubmitted without asking.

### Claudes working together in Slack — off until the Core sets up the Slack app
- **`slack_collab.py`** lets two people's Claude sessions work on one analysis in one Slack
  thread, on request only. Authority comes only from the people, by Slack user ID: each agent
  starts only after its own person approves, and anyone in the thread can stop it. Posts are
  redacted and rate- and length-limited, and the bot token is never printed or stored on a
  laptop.
- **It is dormant in this release.** Nothing starts it, and with no bot token set up every
  command stops with "no Slack bot token" and sends nothing. The Core's Slack app, its token and
  the Slack-people list are to be set up after the release (`references/slack-collab.md`).

### Smaller fixes
- Run from stdin (`python3 -` on HIVE), `record_run.py` and `notify_slack.py` no longer read or
  import anything from the current folder, which on HIVE is the home folder.
- `provenance.py`'s "Installed with" names the plugin with its marketplace, as the install does.
- **`run_record.json` is schema 3**: `search.cont_quant_exclude` is new (as the run recorded it),
  and `fasta.cont_quant_exclude` is renamed `fasta.cont_quant_exclude_recommended`. Earlier
  records keep schema 2.

### Still open (in `docs/SKILL_OPEN_DEFECTS.md`)
- Sage: the LFQ window is warned about, not corrected; the protein value is the highest peptide,
  not a rollup model; a `.d` has no LFQ route on HIVE.
- FragPipe DDA tests only a group's leading protein for a contaminant tag; AlphaDIA's and
  Radiant's IDs have not been checked on a real output with contaminants.
- DIA-NN on DDA (2.10, each behind an A/B): `--fwhm`, `--fix-scoring`, a tighter timsTOF DDA
  range, and a registry flag for test runs.

## [Skill 2.8.0] — 2026-09-28

The report of record becomes one HTML page, paired and repeated designs are modelled, and
contaminants no longer reach the statistics. Also: the CoreOmics submission in every Core
report, and an optional audio discussion for the collaborator.

### Reports
- **`Analysis_Report.html` is the report of record** everywhere (step 9, the run record,
  README, AGENTS.md, deliveries); no Word copy of the report is made any more (Word mangled
  the figures). The Methods stay in Word. The page is restyled on a shared `report_style.py`,
  renders each figure where the text references it (and only those), and counts "Results at
  a glance" at adj.P.Val < adjp only — no fold-change filter.
- **`Analysis_Report.md`**, its plain-text twin with captions and numbers written out (for
  NotebookLM), and **`Analysis_Report.pdf`**, printed by a headless Chrome/Chromium/Edge
  (`html_to_pdf.py`; `--no-pdf`, `--md-out`; `finalize` prints it later where no browser was).
- **`README.html` + `AGENTS.md`** at finalize (`session_docs.py`, `session.py docs`): the page
  collaborators open, a guide for an AI agent given the folder, and "Where this lives on HIVE"
  with Windows/Mac paths (`hive_shares.tsv` / `share_map.py`, one definition of the shares).
- Figures: **top-protein violins** per contrast, each run marked measured or inferred; **PCA
  circles every group** (rounded hulls, labels on the plot, crossed designs read); short sample
  names mapped in `sample_labels.csv`; the per-sample protein-count plot is skipped for a
  complete (DPC) matrix, where every bar was identical.

### Differential expression
- **`run_de.R --block <column>`** for paired / repeated designs (IPs from the same mouse,
  biopsies from one patient): a fixed subject effect for a crossed paired design, a random
  effect (`duplicateCorrelation`, `dpcDE(block=)`) for nested ones (`--block-effect
  auto|fixed|random`); `--block-scope within|all` reports each contrast from the fit it
  belongs to, in one run with one record (`de_provenance.json` `block`).
  `collect_conditions.py` keeps a subject column (Mouse, Patient…) under its own name and
  suggests `--block`; `--subject-column <header>` confirms an ambiguous one.
- **`Detection_Matrix.csv`**: measured vs inferred per protein × run (DPC: precursors
  observed; MaxLFQ: quantified or missing).
- **Contaminants are removed before quantification** on both methods (`Cont_` precursors,
  DIA-NN's own rule), with `QC_contaminant_share.csv` / `contaminants_removed.csv`; before,
  every `Cont_` group was tested and bovine serum proteins came out as hits.
  `--keep-contaminants` restores the old behaviour, recorded either way.
- `sample_quality.py`'s confound check is a permutation F-test (the max–min gap flagged
  every panel of a 10-group design); its panels see mouse/rat gene names.

### Sequence database
- `fetch_fasta.py` drops contaminant entries the search cannot tell apart from a target
  protein — identical, contained, or near-identical by the peptide rule (bovine EEF1A1 and
  YWHAZ are one residue from mouse) — so those proteins are quantified under their own
  accessions. A database built by the identity rule alone is named as a contaminant risk.
- The Core's shared human + contaminant FASTA was rebuilt (`MRS/`, 2026-09-25; the Sep-2025
  file stays for old searches' provenance); `docs/HPC_PATHS.md` has both.
- `provenance.py`'s replay rebuilds the database the run actually searched
  (`--enzyme`, `--keep-target-contaminants`, `--min-unique-peptides 0` as recorded).

### Methods
- The LC and instrument method are read from the `.d` (Evosep method, TIMS ramp, collision
  energy ramp, window overlap, cycle time, source settings), in the order dia-PASEF papers use.
- A peptide submission's Sample preparation says the submitting laboratory prepared it.

### Core service runs (CoreOmics)
- **`core_submission.py`**: `identify` (which submission is this data? — named ids first, then
  sample ids, never a guess), `fetch`, `locate` (a sample id finds its run even when the name
  adds a dash: LRS96 = LRS-96), `stage`, `conditions`, `deliver` (real files into the Bioshare
  share, the podcast's audio and transcript included), `bioshare`, `email-draft`. Only an
  allowlisted record and a redacted summary go to HIVE.
- **`submission_report.py`**: the submission stored once per session and shown first in every
  report (PI, organism, description as written, sample sheet, who prepared the samples), with
  Data Quality Notes — organism vs the FASTA, blank UniProt, sheet ids vs raw files, conditions
  vs the design analysed, pairing read from the condition names.
- **`ht_manifest.py`**: an HT plate's file list from STAN, never a glob (SKILL.md step 1a).

### Optional audio discussion
- **`make_podcast.py`** `check` / `render` / `verify` / `link`: a two-host discussion of the
  finished report for the collaborator, written by the agent, checked token by token against
  the report, rendered with Gemini TTS (rate-limit aware, resumable) or macOS `say`, heard back
  by an ASR round trip, and linked from a "Listen" card. Only on request; never blocks a report.

### From 2.6.0 and 2.7.0 (not logged here before)
- 2.6.0: publication Methods (`methods.md` / `.docx`) and the PRIDE/MassIVE deposit package
  (`output/DATA_SUBMISSION/`) in every session zip.
- 2.7.0: the job-end hook for every search job — the Core run log, the automatic FRAN
  hand-off (`fran_deposit.py`: health, backfill, QC exclusion) and Slack notifications — and
  the central run registry (`record_run.py`). The FRAN manifest now reads the database and
  organism from the search's own FASTA.

## [Skill 2.5.0] — 2026-09-21 — Orbitrap mass accuracy

### Changed — BREAKING for existing `workflow.yaml` files

- **A `param_overrides` that sets only one mass-accuracy flag is now a hard error where the
  instrument has no table value for the other level.** `{"--mass-acc": 8}` on a 120k/15k
  Orbitrap, on an Orbitrap of unknown resolution, or on an unidentified instrument previously
  wrote that one flag into the cfg. DIA-NN 2.7.0 fixes **both** levels as soon as either is
  given (`Mass accuracy will be fixed to 2e-05 (MS2) and 7e-06 (MS1)`, HIVE srun 23528991), so
  the level nobody set silently ran at 20 ppm. `estimate_params.py` now exits non-zero, names
  the missing flag, and deletes any cfg and `.rationale.json` already at `--out` so a refusal
  leaves no stale parameter set behind. A workflow that relied on the old behaviour must give
  **both** flags, pass `--ms1-resolution`/`--ms2-resolution` so DIA-NN's own table supplies the
  other level, or override neither. Where both resolutions are known and inside 30k–240k the
  other level is filled from the table automatically and nothing changes.

- **An Orbitrap whose resolution is unknown is no longer measured with DIA-NN.** With no
  resolution neither level has a documented tier, so both would have been measured — and a
  measured MS1 is what DIA-NN itself warns about (`the MS1 mass accuracy setting (4.2 ppm)
  deviates significantly from the value recommended (7 ppm) ... (120000)`). It falls back to
  DIA-NN's automatic calibration, and the 5-step chain declines such a cfg as `mass_acc_unset`
  until a value is pinned or the resolutions are passed. This is the default Thermo `.raw`
  path, so pass `--ms1-resolution`/`--ms2-resolution` when you know them.

- **A measured mass accuracy is now floored at the SOP: the pinned tolerance is
  `max(measured, SOP)` per level** (`estimate_params.SOP_MASS_ACC`, MS2 20 ppm / MS1 7 ppm — the
  one definition of an SOP tolerance in the skill, imported rather than re-typed). The
  measurement is used only where it is **wider** than the SOP, which is the case the probe
  exists for; a measured value tighter than the SOP costs identifications and buys nothing
  (18,476 precursors at the measured 14/7 against 19,592 at 20/7 on the benchmarked cohort).
  Both numbers are recorded — `mass_acc.measured_ms2_ppm` and `.pinned_ms2_ppm`, with `.floored`
  per level — in `window.json` / `mass_acc.json` and in the job log, and
  `search_provenance.json`'s `mass_acc.measured: true` now carries a `floor_note` saying it means
  "we measured it", not "the search ran at the measured value". A level from DIA-NN's resolution
  table is pinned as given and never floored. The floor never rescues a refused measurement.

- **A measured mass accuracy is now checked before it is pinned.** MS2 must land in 3–30 ppm
  and MS1 in 1.5–25 ppm (DIA-NN's own tiers span 4–15 and it calibrates from 25), the probed
  runs must agree to within 50% of the median, and at least two runs must have answered.
  Anything else fails the probe with the per-run evidence instead of pinning a number for the
  whole cohort. Steps 2–5 re-check the band on `massacc.txt` itself.

## [Skill 2.2.0] — 2026-08-20

### Added
- **De novo → homology species ID** (`§6e`), for samples with no proteome —
  forensic hair, feather, fossil, wildlife. Casanovo → DIAMOND vs nr → LCA, as
  four scripts: `denovo_decoy_gen.py` (FRAC-0.8 decoy spectra),
  `denovo_search_cmd.py` (DIAMOND settings), `denovo_homology_fdr.py` (FDR), and
  `denovo_lca.py` (species call).

  The scoring half was rebuilt: the original lived in `/tmp/decoyval/` and was
  lost to scratch, while the data survived on `/quobyte`. It is a
  **reimplementation validated against preserved outputs**, not the original
  code. `denovo_homology_fdr.py` reproduces the published E-value result
  **exactly** (13,074 peptides at 1% FDR) and raw bitscore exactly (10,404);
  mokapot rebuilds land within a few percent (14,925 / 19,757 / 9,554 / 11,325
  against 14,706 / 19,556 / 9,335 / 12,352 — mokapot is semi-supervised, so exact
  equality is not expected).

### Fixed (in the method, not the code)
- **`--max-target-seqs 1` makes the LCA step impossible.** The production ocelot
  search used it (0.9 hits/peptide), so "LCA over all hits" — step 4 of the
  method's own recommendation — silently degraded to best-hit, which is the ~36%
  species-mis-assignment error mode LCA exists to prevent. The skill defaults to
  **25** (the HeLa benchmark setting, 22.5 hits/peptide), `denovo_search_cmd.py`
  warns when given < 2, and `denovo_lca.py` warns when its input averages < 2
  hits/peptide.

### Decisions, each from measurement
- **Linear model, never gradient boosting.** GBT overfits the decoy and scores
  *worse than raw bitscore* (9,554 vs 10,404).
- **Five features, not thirteen.** On HeLa ground truth more features accept more
  peptides at lower precision and recover fewer correct ones (12-feature: 2,532 /
  55.5% / 1,405 vs 5-feature: 2,400 / 59.8% / 1,436).
- **Confidence is load-bearing.** The homology-only model does not separate at
  all on a standard search; every model that works includes `mean_conf`.
- **Do not gate the species call on the FDR model.** Filtering lifts peptide
  precision 42.4% → 59.8% but moves primate attribution only 29.5% → 32.9%,
  leaves mammal flat at 68.5%, and discards 715 correct peptides. Species error
  is conserved peptides — an LCA problem. Run LCA over unfiltered hits and report
  the score as a confidence tier.
- **Two FDR definitions, not interchangeable.** Raw scores use a rate-normalised,
  tie-aware target-decoy threshold (the universes differ: 312,820 vs 424,552);
  mokapot scores use mokapot's own q-values. Applying rate-normalisation to a
  mokapot score returns ~everything (298,889 of 299,099).

## [Skill 2.1.2] — 2026-08-20

### Fixed
- **The tsv route still let excluded runs decide the protein set.** 2.1.1 gated
  the pre-filter on `identical(format, "parquet")`, leaving `--format tsv` on the
  old post-hoc `dat[, .keep]` path with exactly the defect that release removed —
  and silently, since nothing errors. arrow reads both formats
  (`read_tsv_arrow`), so both are now pre-filtered. Verified on a 12-run TSV
  report analysed at 7 runs: **4,645 proteins / 577 significant**, identical
  protein set and identical `logFC` to a natively pre-filtered TSV, and matching
  the parquet result. Before the fix that path produced 4,648 / 553.
- **The filtered frame is now written back in the format `readDIANN()` is told to
  read.** Writing parquet while still passing `format = "tsv"` would fail inside
  limpa.
- **TSV is written with `utils::write.table`, not `arrow::write_csv_arrow`** —
  the latter has no `delim` argument in arrow 24 (*"not yet supported in
  Arrow"*), so it cannot write a TSV at all. The first draft of this fix used it
  and would have failed at runtime for anyone passing `--format tsv`.

### Added
- Three guards: the restriction is not parquet-only, the TSV write-back exists,
  and `write_csv_arrow` is not used in code (comments excluded — a bare substring
  check trips on the comment explaining why it is unusable). 58 tests.

## [Skill 2.1.1] — 2026-08-20

### Fixed
- **Runs excluded from the design still decided the protein set — and shifted
  every retained protein's quantification.** `--method dpc` called `readDIANN()`
  on the whole report and subset columns afterwards (`dat[, .keep]`). That drops
  the excluded runs' data but keeps every precursor row they justified — rows
  then entirely NA in the retained runs, which still reach `dpcCN()`/
  `dpcQuant()`. `build_maxlfq.R` has always applied `keep_runs` to the arrow
  query before `collect()`; dpc now matches it.

  Reported by the audit in #60, which measured the protein-set effect (98 extra,
  0 lost). Reproducing it surfaced a larger one it had not measured — what
  happens to the proteins that were *already* there. On a 12-run report analysed
  at 7 runs:

  | | before | after |
  |---|---|---|
  | all-NA precursor rows surviving the subset | 158 | 0 |
  | extra protein groups vs a pre-filtered report | 3 (exact superset) | 0 |
  | **shared proteins with a different `logFC`** | **4,645 / 4,645 (100%)** | 0 structural |
  | **significance calls flipped** | **54** | **0** |

  The extra proteins were not themselves significant here; the harm was 54
  flipped calls among proteins that would have been analysed either way.

  A residual numeric difference remains against a natively pre-filtered report
  (median |Δ logFC| 1.1e-07, max 3.0e-03, **0** flips) — row ordering changing an
  iterative fit's path, not structure. Before the fix: median 0.0021, max 0.11,
  54 flips.

  **Unaffected if your report contains only the runs you analyse** — the common
  case. It bites when a report deliberately holds more runs than the design uses.
  The tsv route cannot pre-filter, so the post-hoc `dat[, .keep]` is retained as
  a backstop for it.

### Added
- `TestRunRestrictionHappensBeforeRollup` asserts the restriction precedes
  `readDIANN()`, verified to fail when it is removed. 56 tests.

## [Skill 2.1.0] — 2026-08-20

### Added
- **A reproducibility contract, enforced in CI.** Two reproducibility defects
  shipped back to back (2.0.1 dpc, 2.0.2 maxlfq) with the same shape: the emitted
  `reproducibility_log.R` ran clean and returned different numbers than the
  analysis beside it. The second happened *because* the first was fixed on one
  branch only — `repro_script.R` has a separate emitter per `--method`.

  `tests/test_reproducibility_contract.py` now enforces:
  - **Every `--method` `run_de.R` accepts must have coverage.** The list is
    parsed from `run_de.R`'s own validation line, so a new method fails CI until
    someone covers it rather than shipping an unverified emitter.
  - **Every cutoff a run applies must appear in the script it emits**, for each
    method, whatever shape that emitter uses (`readDIANN` `q.cutoffs` vector for
    dpc, a `dplyr::filter` chain for maxlfq).
  - **Each emitted script must be valid R** (parsed, per method).
  - **End-to-end**: run the pipeline, execute the emitted script, diff protein
    counts, significant counts and per-protein `logFC`. Needs limpa/arrow so it
    skips in CI; run it with `DELIMP_TEST_REPORT=<report.parquet>`.

  Verified to fail on all three regressions rather than assumed to: a new
  uncovered method, the maxlfq scalar bug, and the dpc scalar bug (caught by two
  separate assertions). The end-to-end check also guards against a hollow pass —
  `0 == 0` would otherwise satisfy every assertion while proving nothing ran.

- `SKILL.md` §6d documents the contract for contributors, with the measured cost
  of both bugs, so it is met before CI has to say so.

## [Skill 2.0.2] — 2026-08-20

### Fixed
- **The `maxlfq` path's `reproducibility_log.R` did not reproduce its analysis
  either** — the same defect fixed for `dpc` in 2.0.1, and worse in effect. That
  branch emits a `dplyr::filter` chain rather than a `readDIANN` call, and it
  wrote the scalar `--q-cutoff` for every column while `build_maxlfq()` applies
  `PG.Q.Value` at 0.05:

  | | proteins | significant |
  |---|---|---|
  | original run | 4,526 | 1,326 |
  | emitted script | 4,444 | 1,281 |

  (dpc's gap was 4,648 → 4,624 / 1,859 → 1,846.) Re-running the corrected script
  now reproduces the run exactly — identical protein set with zero differing
  `logFC` / `P.Value` / `adj.P.Val` / `AveExpr` across all 4,526 rows.
- **`de_provenance.json` on the `maxlfq` path** now records `q_columns`,
  per-column `q_cutoffs`, and `input_sha256`, matching what 2.0.1 added for
  `dpc`. Previously the maxlfq branch never computed them.

### Added
- 4 tests covering the maxlfq emitter branch, including one asserting **both**
  branches agree on the `PG.Q.Value` cutoff — fixing one and not the other is the
  obvious way to regress here, and is exactly what happened between 2.0.1 and
  this release. 46 tests total.

## [Skill 2.0.1] — 2026-08-20

Found by auditing the skill's own output end to end, at the user's request:
"can we verify everything is traceable and reproducible using the output the
skill generates". Three provenance defects, all of which left every scientific
number correct — which is exactly why they survived.

### Fixed
- **`reproducibility_log.R` did not reproduce the analysis.** Once `PG.Q.Value`
  took DIA-NN's recommended 0.05 while the other five columns kept `--q-cutoff`,
  the emitter still wrote a **scalar** `q.cutoffs = 0.01` next to all six
  columns. `limpa` recycles `q.cutoffs` across `q.columns`, so the emitted script
  ran clean and returned **4,624 proteins / 1,846 significant** against the run's
  actual **4,648 / 1,859**. Nothing errored and the CSVs beside it were right;
  only the script disagreed — DE-LIMP architectural rule #1. It now emits the
  cutoff vector that actually ran, and re-running it reproduces the run exactly:
  same protein set, and zero differing `logFC` / `P.Value` / `adj.P.Val`.
- **`de_provenance.json` asserted one cutoff while six ran.** It recorded
  `q_cutoff: 0.01` and never named the columns. It now records `q_columns` and
  the per-column `q_cutoffs` as applied (rule #2).
- **The DE step could not be tied to the search output it consumed.** Provenance
  recorded the input *path* — which does not survive the file being moved,
  regenerated, or shipped in a bundle without its input. It now records
  `input_sha256` and `input_bytes`; verified against an independently computed
  checksum.
- **`reproduce.sh` replayed a subset of the original invocation**, dropping
  `--organism-taxid` and `--env`. Engine params still came back byte-identical
  (they depend on neither), but the regenerated record lost the **species** and
  the platform block. Replay now reproduces all 18 manifest fields.
- **`run_manifest.json` recorded `"timestamp": null`** whenever the orchestrator
  omitted `--timestamp`. A bundle whose job is auditability must say when it ran;
  it now defaults to UTC now.
- **`reproducibility_log.R` was silently skipped for `--method maxlfq`.**
  `q_use` / `q_cuts` exist only on the dpc branch and the call sat inside a
  `tryCatch`, so the failure was swallowed. Guarded explicitly.

### Added
- 10 tests covering emitter cutoff rendering, replay fidelity, timestamp,
  and the recorded skill version (42 total, up from 32).

## [Skill 2.0.0] — 2026-08-17

Skill-only release (`ucdavis-proteomics-core-pipeline`).

**Also carries the defect fixes merged on the way to this release**, which landed on
`main` while the plugin manifest still said 1.8.0 — so 2.0.0 is the first version
string that actually identifies them: the experiment-wide FDR columns on the dpc
path (#48), the acquired precursor m/z range replacing a hardcoded 380–980 (#51),
one definition of the q-value column set (#53), and per-column q-cutoffs plus an
honest `--min-pr-charge` tag (#54). `docs/SKILL_OPEN_DEFECTS.md` is now empty of
open defects. **DE-LIMP itself is
unchanged and stays at 4.0.3** — no `app.R`, `R/`, or Shiny code was touched.

Major bump because the remote workflow registry is removed: `fetch_workflows.py
pull` no longer functions and `workflows/` no longer serves bundles.

### Fixed
- **A pinned DIA-NN 2.x version could never be downloaded.** `acquire_tools.sh`
  resolved release assets via `releases/tags/<version>`, but **every** DIA-NN 2.x
  build is attached to the single release tagged `2.0` — there is no 2.1/2.3/2.6
  tag — so any 2.x pin 404'd and fell through to "download it manually".
- **`latest` silently installed DIA-NN 2.0.** `releases/latest` returns the `2.0`
  release, whose first `Academia-Linux` asset is 2.0 itself. This *succeeded*, so
  nothing looked wrong while the oldest 2.x build was installed and reported as
  "latest". Both paths now resolve by asset **filename** across all releases
  (`scripts/diann_release.sh`, shared with `build_diann_docker.sh`). Verified live:
  `latest`→2.6.1, exact pins resolve, 2.3.0 finds its `-Preview` build, unknown
  versions fail cleanly.
- **The tools manifest recorded the string `latest`** instead of the version
  actually installed, which is not reproducible. It now records the resolved build,
  and the on-disk cache is keyed on it.
- **A Mac with the SLURM client installed was classified as `hpc`** and would have
  claimed DIA-NN runs natively on it. Engine availability now keys on OS — "no
  macOS build" is a property of the OS, not of whether a scheduler is on PATH.

### Added
- **NCBI proteome download, for organisms UniProt doesn't cover.** Ported from
  DE-LIMP's own `R/helpers_search.R` (`ncbi_search_assemblies` /
  `ncbi_download_proteome`), endpoints re-verified live. `fetch_fasta.py resolve`
  now searches NCBI Datasets automatically whenever UniProt returns no proteome and
  lists hits under `ncbi_candidates`; `fetch --ncbi-accession GCF_...` downloads
  that assembly's protein set. This removes the last dead end for non-model
  organisms — wildlife, agricultural and other species that have an annotated
  RefSeq genome and no UniProt reference proteome (e.g. *Peromyscus californicus*).
  Two traps are handled explicitly rather than assumed: the RefSeq `GCF_` accession
  is preferred because a GenBank `GCA_` record usually reports no protein count and
  its ZIP contains no `protein.faa`; and NCBI's protein set includes **every
  isoform** (51,825 sequences vs 21,877 protein-coding genes on the Peromyscus
  assembly), so it is the analogue of UniProt `full_isoforms`, not the
  `one_per_gene` default — `fetch` counts the isoform headers and warns so a ~2.4×
  larger search space is never handed over silently. An NCBI assembly is never
  auto-picked and is recorded as "NCBI RefSeq assembly proteins (not a UniProt
  reference proteome)" so methods text can't miscall it.
- **Platform capability map.** `detect_env.sh` now emits `engines` + `apple_silicon`,
  and `resolve_defaults.py --env` enforces it, so an engine that cannot run on this
  machine fails at resolve time with a usable alternative instead of mid-search.
  Verified against each project's released artifacts: **FragPipe has no macOS build
  at all** (Windows installer + Linux zip only), **DIA-NN has none either** and runs
  under Rosetta emulation in a linux/amd64 container on Apple Silicon, **Radiant's
  image is multi-arch** so it is the only DIA engine that runs natively on M-series,
  and **Sage ships `aarch64-apple-darwin`** so DDA on a Mac is native.
- **Generated engine presets.** `make_presets.py` writes the FragPipe `.workflow` /
  Radiant `.radiantConfig` for the run, from vendor templates in `presets/`. It
  patches only run-specific keys (`database.db-path`, `workflow.threads` — both
  verified against FragPipe source) and preserves every other byte, including the
  Java-properties escaping. Radiant narrows Seer's flat 20/20 ppm from the
  instrument, tagged `[DERIVED]`, and refuses Bruker `.d` outright.

### Changed
- **The workflow registry is retired; parameters ship with the skill.** Six
  organism-locked bundles are replaced by `resolve_defaults.py`, one defaults table
  keyed on data type. Species never affected a search parameter — only the FASTA,
  which always came from the user's own organism answer — so **every organism now
  works out of the box** and there is no "unsupported species" path.
- **No network call, no menu, no validation gate.** The registry was fetched per run
  (GitHub's unauthenticated API rate-limits at 60/hour), and its `unvalidated` and
  `cross_organism` checks fired on essentially every run, turning a first interaction
  into a menu of ⚠ warnings. There is now exactly one confirmation before compute.
- **Reproducibility is pinned by skill version**, not a registry commit: the same
  skill version reproduces the same parameters with nothing fetched.
  `reproduce.sh` and `references/reproducibility.md` updated accordingly.
- Default DIA-NN pin is **2.6.1** (was split across bundles at 2.3.0 and 2.6.0; the
  2.3.0 pin resolved only to a `-Preview` build).
- Placeholder `validated:` blocks marked `EXAMPLE`/`CONFIRM` are gone with the
  bundles, so nothing asserts a validation that never happened.
- `fetch_workflows.py` is a shim: `match` forwards to `resolve_defaults.py`, anything
  else prints a migration notice and exits 0. `workflows/index.json` is kept as a
  tombstone with an empty list so un-updated installs degrade instead of 404-ing.
