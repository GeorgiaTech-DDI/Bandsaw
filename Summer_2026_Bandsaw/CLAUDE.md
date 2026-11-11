# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

This is a **Bandsaw Safety Monitoring System** running on a Raspberry Pi 5. It uses computer vision and an IMU sensor to detect when the bandsaw is running and alert the operator if a hand is dangerously close to the blade slit. The primary production entry point is `bandsaw_monitor.py`.

## Running the System

**Production (hardware required):**
```bash
source myenv/bin/activate
python bandsaw_monitor.py
```

**With debug flag (simulates vibration, still requires camera and LEDs):**
```bash
source myenv/bin/activate
python bandsaw_monitor.py --debug
```

**Autostart:** The system launches automatically on GUI login via `~/.config/autostart/bandsaw_monitor.desktop`, which calls `start_bandsaw.sh`. That script acquires a lock, activates the venv, and runs `bandsaw_monitor.py`. The lock file is `/tmp/bandsaw.lock`.

**Key runtime arguments:**
- `--video 0` — webcam index or video file path
- `--stabilization 5.0` — seconds to collect frames before finalizing slit position
- `--alert-interval 2.0` — minimum seconds between consecutive alerts
- Press `r` during runtime to re-trigger slit calibration; `q` to quit

**Mounting guideline (important):** mount the camera **roughly overhead** of the
blade so the kerf runs **vertically in the frame**, with the **blade roughly
centred** and the slit **not jammed against a frame edge**. The detector is built
on these as soft/hard conventions (see Architecture), so they apply to *any*
bandsaw, not just this one. A steep **oblique / side-on** view is **unsupported**
— the slit foreshortens and the lock is unreliable.

## Running Tests / Diagnostics

Individual component test scripts (all require the venv):
```bash
python test_slit_detection.py [--video 0] [--stabilization 5.0] [--debug]
python camera_test.py
python hand_test.py
python led_test.py
python mpu_camera_test.py
python alert_test.py
```

**Iterating on the slit detector against recorded clips** (no camera / MPU / LEDs
needed — these read `.mp4` files directly, ideal on the Pi or a laptop):
```bash
python test_slit_batch.py [clip.mp4 ...]   # headless: finalize each clip, print the
                                           # locked slit, write annot_out/*.annot.png
python render_annotated.py                 # burn the overlay into recordings_annotated/
                                           # *.mp4 (openable in any player, e.g. VLC)
python play_recordings.py [dir]            # on-screen playback through recordings/
                                           # (needs a display; on Wayland export
                                           #  QT_QPA_PLATFORM=xcb)
```
Note: `bandsaw_monitor.py` / `test_slit_detection.py` ignore their `--video` flag
(their `video_capture.py` is hardwired to Picamera2) — use the harnesses above for
file playback.

## Installing Dependencies

```bash
python setup.py          # installs requirements.sty, creates recordings/ dir
# or manually:
pip install -r requirements.sty
```

Note: `requirements.sty` is misnamed — it is a plain pip requirements file with comments.

## Version Control

This repo is git-tracked. `.gitignore` excludes the large/generated trees that should never be committed: `myenv/` (venv), `opencv/` and `opencv_contrib/` (vendored library source), `recordings/` and `*.mp4` (video output), and `__pycache__/`. Only first-party source, tests, configs, and notes are tracked (~37 files).

Note: the binary `cmake_3.25.1-1_arm64.deb` install package is intentionally committed, not ignored.

The initial commit is `Working baseline before slit detection experiments` — the reference point to restore to when slit-detection experiments go wrong (`git restore .`).

## Architecture

The system pipeline on every video frame:

```
MPU6050 (I2C) → mpu_camera.py:bandsaw_active()
                      ↓
             bandsaw_monitor.py (main loop)
             ├── video_capture.py   — Picamera2 capture + VideoRecorder
             ├── enhanced_slit_detection.py:SlitDetector — finds blade slit line
             ├── hand_detection.py:detect_hands — MediaPipe hand landmarks → bboxes
             └── alert.py           — Pi5Neo LED color states (software still uses SPI)
```

**`bandsaw_monitor.py`** — production main. Checks `bandsaw_active()` each frame to decide whether the camera should be on. When active: runs slit detection, hand detection, checks for convex-hull intersection, drives LEDs. When inactive for >10 s: turns camera off. While the slit detector is *calibrating*, MediaPipe hand detection runs only every 3rd frame (`HAND_DETECT_EVERY_N_CALIB`; cached boxes in between so alerts still fire) — MediaPipe is the heaviest stage of the loop and the calibration vote needs as many frames as possible. Full-rate once locked.

**`main.py`** — older alternative entry point that uses `VibrationDetector` (threaded) + `alert_system.py` (GPIO LED on pin 17) instead of the LED strip. Kept for reference.

**`enhanced_slit_detection.py:SlitDetector`** — the most complex module. It finds
the blade kerf as a **vertical** dark groove and locks a danger box on it. Pipeline:

1. **Per-frame candidate extraction.** Grayscale → adaptive threshold → a **vertical**
   morphology kernel to enhance top-to-bottom structure → Canny → `HoughLinesP`.
   Keep only **near-vertical** segments (`|angle|` near 90°), oriented top-to-bottom.
   For live fps this heavy stage runs on a **half-res copy** (`proc_scale=0.5`, spatial
   params scaled to match, line coords scaled back) — 2.2× faster; groove scoring and
   selection stay full-res, so quality is unchanged (regression-verified on the field clips).
2. **Scored selection** (`_select_slit_line` / `_groove_ratio`) — the key step. Instead
   of the longest line (which grabs the machine fence / a frame border), each candidate
   is scored by, in priority order:
   - **groove ratio** (PRIMARY): how much darker the line is than the table on **both**
     flanks. This is the one *universal physical* property of a kerf, so it is a
     **relative/contrast** measure — **no absolute gray threshold** — and rejects
     step-edges (a fence is dark on only one side).
   - **length** (mild boost), relative to frame height.
   - **center bias** (SOFT multiplier): a kerf is *usually* the more central line; this
     only breaks ties, it never hard-rejects an off-centre slit.
   - **frame-edge reject** (HARD): a line hugging the border is not the slit.
   None of these use absolute pixel positions, so the detector **ports across bandsaws
   / camera distances** (the center/edge cues are *mount conventions*, documented above).
3. **Stable finalize** (`_finalize_detection`). After `stabilization_time` seconds
   **and at least `min_calib_hits` (20) groove votes** — the window is wall-clock based,
   and at low live fps it self-extends until enough frames voted (hard-capped at
   `max_calib_factor`=3×, after which the fail-safe judges), so lock quality does not
   depend on frame rate. It then **clusters** the window's per-frame detections by
   center-x and locks the **medoid of the dominant cluster** — a *real observed* box
   nearest the cluster centre, robust to blur/occlusion/glare on any single frame. It
   **never averages across clusters**, so the box cannot land *between* a real kerf and
   a competing seam; it snaps to whichever slit the majority of frames saw. The lock is
   reproducible (a few px) instead of hostage to the last frame.
4. **Fail-safe.** If no groove-like candidate is found, it appears in too few frames
   (`min_hit_frac`), or the window is split ~50/50 between candidates with no clear
   winner, `final_slit` is set to `None`: `is_slit_missing()` is true, `detect_slit`
   draws a **"SLIT NOT FOUND — CHECK CAMERA MOUNT"** banner and returns `None`, and the
   caller should drive the **red** LED (we cannot protect what we cannot locate). The
   detector deliberately does **not** fall back to a low-confidence guess — a *loud*
   failure beats a confident wrong box.

Returns slit data as a 9-tuple `(cx, cy, width, height, angle, x1, x2, y1, y2)` — flat
format (not nested tuples). `smooth_data()` also handles legacy 5-tuple / nested formats.

**Known limit (oblique mounts):** a steep side-on view can still produce *a* confident
groove (e.g. a table-plate seam or the machine body) and lock a stably-wrong box; the
fail-safe only fires when the detector is genuinely undecided. The defense is the
**mounting guideline**, not a tuning knob — mount overhead. (History: a heavier
"smart" detector — central dark-blade-blob anchor + orientation search — was tried and
reverted; it overfit clean iPhone footage and failed on the cluttered Pi field clips.
That work is preserved at the `archive/smart-slit-detection` tag — `git switch -c <name> archive/smart-slit-detection` to revive it.)

**`mpu_camera.py`** — thin, module-level I2C read that initializes the MPU6050 immediately on import. `bandsaw_active()` detects motion via delta of acceleration magnitude vs `ACCEL_THRESHOLD=0.25` and considers the saw active for up to 30 s after the last motion event.

**`alert.py`** — three LED states currently driven by Pi5Neo over `/dev/spidev0.0`.
The strip's data wire is now connected to BCM GPIO18 (physical header pin 12), so
the current software backend does not match the wiring; replace it with a
Raspberry Pi 5-compatible GPIO18 driver before relying on LED alerts:
- `solid_white()` — bandsaw active, no hands visible
- `solid_green()` — hand detected, not near slit
- `solid_red()` — hand overlaps slit bounding box (danger)
- `turn_off_leds()` — bandsaw inactive

**`hand_detection.py`** — wraps MediaPipe Hands (static global instance). Returns a list of `(x, y, w, h)` bboxes expanded 1.2× from raw landmark bounds.

**`video_capture.py`** — wraps Picamera2 at 1280×720 RGB888. `open_video_source()` returns a dummy truthy value (Picamera2 is a module global); `get_frame()` ignores its argument. `VideoRecorder` writes mp4v-encoded `.mp4` files to `recordings/`.

## Hardware Peripherals

| Peripheral | Interface | Notes |
|---|---|---|
| MPU6050 accelerometer | I2C bus 1, addr 0x68 | Wake-up register 0x6B=0 on init |
| Raspberry Pi Camera | CSI / Picamera2 | 1280×720 preview config |
| LED strip | Data wired to BCM GPIO18 (physical header pin 12) | 144 LEDs; software currently configured for SPI `/dev/spidev0.0` |
| GPIO LED (legacy) | gpiochip4 line 17 | Used by `alert_system.py` / `main.py` only |

## Known Quirks

- `mpu_camera.py` executes I2C setup at module import time — importing it on a machine without the sensor will raise an exception immediately.
- `requirements.sty` uses a `.sty` extension (LaTeX style file extension) but is a plain pip requirements file.
- Large blocks of commented-out old code exist in `enhanced_slit_detection.py`, `mpu6050_sensor.py`, and `slit_detection.py` — these are prior implementations kept for reference.
- The `recordings/` directory accumulates `.mp4` files indefinitely; no rotation or cleanup logic exists.
