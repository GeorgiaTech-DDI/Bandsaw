# Bandsaw Safety Monitoring System

A computer-vision safety monitor for a bandsaw, running on a **Raspberry Pi 5**.
It watches the saw with an overhead camera and an IMU, detects when the saw is
running, locates the blade slit (kerf), and drives an LED strip **red** when a
hand comes dangerously close to the blade.

Production entry point: **`bandsaw_monitor.py`**.

---

## What it does

On every frame, while the saw is running:

```
MPU6050 IMU (I2C) ──► is the saw vibrating / active?
                            │
                            ▼
                   bandsaw_monitor.py
                   ├── video_capture.py         Picamera2 capture + recording
                   ├── enhanced_slit_detection  locate the blade kerf, lock a danger box
                   ├── hand_detection.py         MediaPipe hand bounding boxes
                   └── alert.py                  Pi5Neo LED strip: white / green / red
```

- **White** — saw active, no hands visible.
- **Green** — hand detected, clear of the slit.
- **Red** — hand overlaps the slit danger box **or** the slit could not be located.

## Hardware

| Peripheral | Interface | Notes |
|---|---|---|
| MPU6050 accelerometer | I2C bus 1, addr `0x68` | motion → "saw active" |
| Raspberry Pi Camera | CSI / Picamera2 | 1280×720 preview |
| LED strip | Data wired to BCM GPIO18 (physical header pin 12) | 144 LEDs; software backend still uses SPI |

> ⚠️ **Hardware/software mismatch:** the LED strip data wire is now connected to
> BCM GPIO18 (physical header pin 12), but the current LED backend still sends data
> over SPI `/dev/spidev0.0`. Update the backend to a Raspberry Pi 5-compatible
> GPIO18 driver before relying on the white/green/red LED alerts.

## Running

```bash
source myenv/bin/activate
python bandsaw_monitor.py            # production (hardware required)
python bandsaw_monitor.py --debug    # simulate vibration; camera + LEDs still required
```

Runtime keys: `r` re-runs slit calibration, `q` quits.
Useful flags: `--stabilization 5.0` (calibration seconds), `--alert-interval 2.0`.

### Mounting guideline (important)

Mount the camera **roughly overhead** of the blade so the kerf runs **vertically**
in the frame, with the blade **roughly centred** and the slit **not jammed against
a frame edge**. A steep **oblique / side-on** view is **unsupported** — the slit
foreshortens and the lock becomes unreliable. These are *mounting conventions* the
detector relies on, and they apply to **any** bandsaw, not just this one.

## The slit detector (`enhanced_slit_detection.py`)

Finding the kerf reliably is the hard part of this system, and is what the bulk of
this work addressed. The detector treats the kerf as a **vertical dark groove** and
locks a danger box on it:

1. **Candidate extraction** — grayscale → adaptive threshold → vertical morphology →
   Canny → Hough, keeping only near-vertical, top-to-bottom segments.
2. **Kerf-aware scored selection** *(the core idea)* — rather than picking the longest
   line (which grabs the machine fence or a frame border), each candidate is scored by:
   - **Groove contrast (primary)** — how much darker the line is than the table on
     **both** flanks. This is the one *universal physical* property of a kerf, measured
     as a **relative contrast ratio — no absolute brightness threshold** — so it ports
     across machines and lighting, and rejects step-edges like a fence (dark on one side).
   - **Center bias (soft)** — a kerf is usually the more central line; a tie-breaker only.
   - **Frame-edge reject (hard)** — a line hugging the border is not the slit.
3. **Stable lock (medoid finalize)** — over a few seconds of calibration it clusters the
   per-frame detections and locks the **medoid of the dominant cluster** — a real observed
   box, never an average. Reproducible to a few pixels, robust to a single blurred frame.
4. **Loud fail-safe** — if no groove is found, it appears in too few frames, or calibration
   is split ~50/50 with no winner, it shows **"SLIT NOT FOUND — CHECK CAMERA MOUNT"** and
   signals red instead of locking a confident wrong box. For a safety device, a loud failure
   beats a silent wrong one.
5. **Live-rate calibration (2026-07-28)** — a live field test showed locks that recordings
   didn't predict: the calibration window is *wall-clock* based, and on the live Pi the loop
   shares the CPU with MediaPipe/recording/GUI, so 5 s could mean only a handful of frames —
   a consensus vote starved of samples. Three fixes:
   - **Vote-gated finalize** — locking now also requires ≥ 20 groove votes; at low fps the
     window extends itself (capped at 3×, after which the fail-safe judges), so lock quality
     no longer depends on frame rate.
   - **Half-res candidate search** — the heavy threshold/morph/Canny/Hough stage runs at 0.5×
     scale (2.2× faster, 72 → 32 ms/frame); groove scoring and selection stay full-res, and
     locks were verified frame-for-frame unchanged against the field recordings.
   - **MediaPipe throttled during calibration** — hand detection runs every 3rd frame while
     calibrating (cached boxes in between, alerts still fire), full-rate once locked.

**Known limit:** a steep oblique mount can still produce *a* confident but wrong lock
(e.g. on a table seam); the defense is the mounting guideline, not a tuning knob.

## Testing against recorded clips (no hardware)

These read `.mp4` files directly, so they run on a laptop or the Pi without camera/IMU/LEDs:

```bash
python test_slit_batch.py [clip.mp4 ...]   # headless: lock each clip, write annot_out/*.png
python render_annotated.py                 # burn the overlay into recordings_annotated/*.mp4
python play_recordings.py [dir]            # on-screen playback (needs a display)
```

## Functional tests (no hardware)

Install the test extra and run the Robot Framework suite from the repository root:

```bash
pip install -e '.[test]'
robot --pythonpath . --pythonpath tests/robot --output NONE --log NONE --report NONE tests/robot/functional.robot
```

The suite covers CLI configuration, simulated IMU activity and timeout behavior,
hand/slit overlap, and hand bounding-box expansion. It uses a fake I2C bus and does
not start the camera, LEDs, or production monitor loop.

## Status

- **Working:** vertical kerf-aware detector with stable medoid lock and fail-safe. On
  top-down clips it reliably locks the central kerf — the cases the previous detector missed.
- **Validated** both **live on the bandsaw** and offline against 16 recorded field clips
  via the harnesses above.
- **2026-07-28 — live-rate calibration** (see detector §5 above): a live field test showed
  unreliable locks at low live fps; calibration is now vote-gated, the candidate search runs
  at half res, and MediaPipe is throttled during calibration. Offline validation: locks
  unchanged frame-for-frame on the stable field clips; the vote gate and the fail-safe cap
  unit-tested. **Live re-validation on the saw is the remaining step.**
- **Pending:**
  1. **Re-validate live** on the bandsaw with the 2026-07-28 live-rate changes.
  2. Wire the fail-safe into production — `bandsaw_monitor.py` should drive the red LED when
     `is_slit_missing()` is true (the detector already returns this; the main loop doesn't
     consume it yet).
    3. Update and test the LED backend for the strip's new BCM GPIO18 wiring; the current
      Pi5Neo software still sends LED data over SPI `/dev/spidev0.0`.

See [`HOW_SLIT_DETECTION_WORKS.md`](HOW_SLIT_DETECTION_WORKS.md) for a diagram-driven,
line-by-line walkthrough of the detector (pipeline flowcharts, the groove-ratio scoring,
clustering + medoid finalize, the fail-safe, and the tuning knobs) — start here if the
detector feels like a black box. See [`SLIT_DETECTION_SUMMARY.md`](SLIT_DETECTION_SUMMARY.md)
for the engineering write-up (problem, decisions and why, validation) and
[`CLAUDE.md`](CLAUDE.md) for the overall architecture.

## Dependencies

```bash
python setup.py                 # installs requirements + creates recordings/
# or: pip install -r requirements.sty   (a plain pip requirements file, despite the extension)
```
