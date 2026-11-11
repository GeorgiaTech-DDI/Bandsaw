# Slit Detection Rework — Engineering Summary (2026-06-24, updated 2026-07-28)

> Briefing for documenting the slit-detection work. Written to be self-contained:
> it carries the problem, the decisions and *why*, what was built, how it was
> validated, and what's left — so a project manager (or a Claude project) can turn
> it into a status report, slide, or design note.

## 1. Context

The **Bandsaw Safety Monitoring System** (Raspberry Pi 5 + camera + IMU) watches
the bandsaw and alerts the operator when a hand gets dangerously close to the
blade. To do that it must first **locate the blade slit (kerf)** in the camera
view and place a "danger box" on it. This work was entirely about making that
**slit detection** reliable. (Hand detection, vibration sensing, and the LED
alerts were already working and were not changed.)

## 2. The problem we started with

A previous **"smart" detector** (anchored on the central dark blade "blob", with
an orientation search) was **field-tested by the user and failed** — it located
roughly **1 of 14** slits correctly, even with the user trying to help it. We
reproduced the failure on the recorded clips: it latched onto table seams and
frame edges with incoherent results.

**Root cause we found:** the blob approach worked on a clean iPhone test clip
(2 dark regions, blade dominates) but the real Pi field footage has lots of dark
clutter (cables, a mouse, shadows, the operator) — 3–8 competing dark regions —
and the "nearest-center dark blob" rule picked the wrong one about half the time.
It overfit the clean clip.

## 3. The decision

**Revert to the simple baseline detector and rebuild the selection logic** on
cues that generalize, rather than chase the complex blob approach. Guiding
principle agreed with the user: **don't rely on properties of this one bandsaw** —
the detector must port to other machines.

## 4. What we built (`vertical-slit-detection` branch)

A vertical, kerf-aware detector. Four changes, each independently tested:

1. **Vertical orientation.** The Pi camera mounts show the kerf running
   top-to-bottom, so the detector now finds **vertical** dark lines (was tuned
   for horizontal).

2. **Kerf-aware scored selection (the core fix).** Instead of picking the
   *longest* line (which grabs the machine fence or frame border), each candidate
   is scored, in priority order:
   - **Groove contrast (PRIMARY)** — how much darker the line is than the table
     on *both* sides. This is the one *universal physical* property of a kerf, so
     it is measured as a **relative contrast ratio, not an absolute brightness** —
     this is what lets it work on different machines/lighting. It also rejects the
     machine body/fence (those are dark on only one side).
   - **Center bias (soft)** — a kerf is *usually* the more central line; used only
     as a tie-breaker, never a hard rule (so an off-center slit on another saw
     still works).
   - **Frame-edge reject (hard)** — a line against the image border isn't the slit.
   - No absolute pixel positions or brightness thresholds anywhere → **ports
     across bandsaws and camera distances.** The center/edge cues are documented
     **mounting conventions**, not machine assumptions.

3. **Stable lock (medoid finalize).** During a ~3-second calibration the detector
   collects a detection every frame, then **clusters them and locks the
   representative ("medoid") of the largest cluster** — a real observed box, never
   an average. This means: it can't land *between* a real kerf and a competing
   seam, it's robust to a single blurred/occluded frame, and the result is
   **reproducible** (locks to within a few pixels run-to-run, vs. jumping
   hundreds of pixels before).

4. **Loud fail-safe.** If no slit-like groove is found, it appears in too few
   frames, or the calibration is split ~50/50 between two candidates with no clear
   winner, the system shows **"SLIT NOT FOUND — CHECK CAMERA MOUNT"** and signals
   red, rather than locking a confident *wrong* box. For a safety device, a loud
   failure is far better than a silent wrong one.

## 5. Validation

Validated both **live on the bandsaw** and **offline against the 16 recorded field
clips** (plus a reference clip) using headless harnesses (no hardware needed):
- **Field-tested live on the bandsaw** with an overhead mount — the detector locks
  the central kerf in real time, confirming the offline top-down results hold on the
  actual machine.
- **On the top-down clips it reliably locks the central kerf** (e.g. clips
  142010, 142209, 142312, 142447) — the cases the old detector missed.
- **Oblique / steep side-on mounts remain unreliable** (~7 clips). This is a
  *visibility* limit — the slit foreshortens — and is treated as a **mounting
  requirement (mount overhead)**, not something to over-tune for (over-tuning
  those is exactly what sank the previous approach).
- The fail-safe was unit-verified (blank input → red; clean groove → lock;
  50/50 split → red).

## 6. Engineering hygiene

- All work isolated on the `vertical-slit-detection` branch; the **baseline is
  untouched** and one command away.
- The failed "smart/blob" approach was **archived as a git tag**
  (`archive/smart-slit-detection`) — removed from the active branches but fully
  recoverable, not deleted.
- Architecture doc (`CLAUDE.md`) updated to match the new pipeline.

## 7. Current state & next steps

**State:** working vertical detector on its branch (4 commits), documented,
baseline preserved, old approach archived, repo cleaned up.

**Next steps:**
1. **Wire the fail-safe into production** — `bandsaw_monitor.py` should drive the
   red LED when the detector reports "slit not found" (the detector already
   returns this signal via `is_slit_missing()`; the main loop doesn't consume it
   yet).
2. **Update the LED backend** — the strip data wire is now on BCM GPIO18 (physical
  header pin 12), while the software still uses SPI `/dev/spidev0.0`. Use and test a
  Raspberry Pi 5-compatible GPIO18 driver before relying on LED alerts.
3. Optionally revisit oblique mounts only if a real deployment can't be mounted
   overhead.

*(The earlier "pending live field test" is now done — the detector has been
field-tested live on the bandsaw; see Validation above.)*

## 8. Live-fps hardening (2026-07-28)

A second live field test exposed a gap the recordings could not show: the detector
locked correctly **less than half the time live**, while the same scenes worked
fine when replayed from `.mp4`.

**Root cause.** The calibration window is *wall-clock* based (5 s), but live the
main loop shares the Pi's CPU with MediaPipe hand detection, video recording and
the GUI — so 5 s of live capture yields only a handful of frames, and the
consensus vote (clustering + medoid) was being decided on a starved, noisy sample
where one blurry/sawdust frame carries real weight. The offline harnesses replay
frames as fast as they decode, so the same 5 s collects many times more votes —
which is exactly why recordings looked reliable and live didn't.

**Fixes (all offline-validated):**

1. **Vote-gated finalize** — locking now requires the time window *and* ≥ 20 groove
   votes (`min_calib_hits`). At low fps calibration extends itself (the monitor
   shows *"CALIBRATING (gathering frames)"*), hard-capped at 3×
   (`max_calib_factor`), after which the fail-safe judges whatever evidence
   exists — a slit-less scene still fails loud, never hangs. Lock quality is now
   independent of live frame rate.
2. **Half-res candidate search** — the heavy threshold/morph/Canny/Hough stage runs
   at 0.5× scale (`proc_scale`) with spatial params scaled to match and line
   coordinates scaled back; groove scoring/selection stay full-res. 2.2× faster
   (72 → 32 ms/frame on the Pi 5).
3. **MediaPipe throttled during calibration** — `bandsaw_monitor.py` runs hand
   detection every 3rd frame while calibrating (cached boxes in between, so alerts
   still fire), full-rate once the slit is locked. MediaPipe is the loop's
   heaviest stage; this buys the calibration vote several times more frames.

**Validation (offline, no hardware):**
- Deterministic A/B (identical frames, full-res vs half-res) across all 27
  readable field clips: **22/27 locks identical within ~7 px**; the 5 that differ
  are the inherently ambiguous clips where even full-res flip-flops between vote
  windows — and on those, half-res did as well or better (one turned a weak
  18/30 off-position lock into a unanimous 30/30 lock on the kerf; one correctly
  fail-safed instead of taking a weak 14/30 lock).
- Vote gate unit-tested: window elapses early → keeps collecting until 20 votes,
  then locks at the same cx as baseline; blank scene → extends to exactly the 3×
  cap, then fires the fail-safe (`is_slit_missing()` true).
- Annotated field frames visually confirmed the locked box on the kerf.

**Remaining:** re-validate live on the saw with these changes in place.

## 9. Key files (for reference / for a Claude project)

| File | What it is |
|---|---|
| `enhanced_slit_detection.py` | The detector (`SlitDetector`): selection scoring, medoid finalize, fail-safe. |
| `CLAUDE.md` | System architecture + the slit-detection pipeline, mounting guideline, limits. |
| `bandsaw_monitor.py` | Production main loop (consumes the detector; fail-safe wiring still TODO). |
| `test_slit_batch.py` / `render_annotated.py` / `play_recordings.py` | File-based test harnesses (no hardware) used to validate against the recordings. |
