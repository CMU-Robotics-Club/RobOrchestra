"""Measure where the gesture pipeline's latency actually goes.

Guessing at this is how you end up tuning --latency-compensation-ms by feel.
The three terms below are measurable on the machine you are demoing from, and
two of them turn out to be worth more than any code change.

What it will not measure is BLE and servo travel, because those need a
microphone next to the drum. Those two are the remaining ~40ms.
"""

from __future__ import annotations

import argparse
import statistics as st
import time

import cv2
import numpy as np

CANDIDATE_MODES = [
    (640, 480),
    (1280, 720),
    (1920, 1080),
    (960, 540),
]


def probe_camera(index: int, modes=None, frames: int = 90, mjpg: bool = True):
    """Time how long read() actually blocks in each mode.

    Cameras lie about frame rate. A device that reports 30 fps may deliver 23,
    and asking for a mode it does not have gets you a different one without
    saying so. What matters is the interval between delivered frames, because
    that is the latency floor for everything downstream.
    """
    results = []
    for width, height in modes or CANDIDATE_MODES:
        cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION if hasattr(cv2, "CAP_AVFOUNDATION") else cv2.CAP_ANY)
        if not cap.isOpened():
            cap.release()
            continue
        if mjpg:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, 60)

        for _ in range(12):
            cap.read()

        intervals = []
        for _ in range(frames):
            start = time.perf_counter()
            ok, _ = cap.read()
            if not ok:
                break
            intervals.append((time.perf_counter() - start) * 1000.0)

        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        claimed = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        if len(intervals) > 2:
            p50 = st.median(intervals[1:])
            results.append({
                "requested": (width, height),
                "actual": (actual_w, actual_h),
                "claimed_fps": claimed,
                "interval_ms": p50,
                "fps": 1000.0 / p50,
            })
    return results


def probe_inference(model_path: str, frames: int = 40, num_hands: int = 2):
    """Time submit to callback for the MediaPipe stage."""
    import threading

    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    done = threading.Event()
    latencies: list[float] = []
    sent: dict[int, float] = {}

    def on_result(result, image, timestamp_ms):
        latencies.append((time.perf_counter() - sent[timestamp_ms]) * 1000.0)
        if len(latencies) >= frames:
            done.set()

    options = vision.GestureRecognizerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=num_hands,
        result_callback=on_result,
    )
    recognizer = vision.GestureRecognizer.create_from_options(options)

    frame = np.full((480, 640, 3), 40, np.uint8)
    cv2.ellipse(frame, (320, 240), (64, 80), 0, 0, 360, (150, 140, 130), -1)

    for i in range(frames):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        sent[i] = time.perf_counter()
        recognizer.recognize_async(image, i)
        time.sleep(1 / 120)

    done.wait(20)
    recognizer.close()
    return latencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--model", default="models/gesture_recognizer.task")
    parser.add_argument("--skip-camera", action="store_true")
    parser.add_argument("--skip-inference", action="store_true")
    parser.add_argument("--ble-ms", type=float, default=20.0,
                        help="assumed BLE MIDI delay, measure it with a mic")
    parser.add_argument("--servo-ms", type=float, default=22.0,
                        help="assumed servo travel, measure it with a mic")
    args = parser.parse_args()

    camera_ms = None
    if not args.skip_camera:
        print("Camera modes (what the device actually delivers, not what it claims):\n")
        results = probe_camera(args.camera_index)
        if not results:
            print("  no camera found\n")
        else:
            for r in sorted(results, key=lambda r: r["interval_ms"]):
                asked = "x".join(map(str, r["requested"]))
                got = "x".join(map(str, r["actual"]))
                note = "" if asked == got else f"  (asked {asked}, got {got})"
                print(f"  {got:<10} {r['interval_ms']:5.1f}ms  {r['fps']:5.1f} fps"
                      f"  claims {r['claimed_fps']:.0f}{note}")
            # Break ties toward the smaller frame: same latency, less USB
            # bandwidth and less work for the colour conversion.
            best = min(results, key=lambda r: (round(r["interval_ms"], 1),
                                               r["actual"][0] * r["actual"][1]))
            camera_ms = best["interval_ms"]
            w, h = best["actual"]
            print(f"\n  Fastest: {w}x{h} at {best['fps']:.1f} fps.")
            print(f"  Use --camera-width {w} --camera-height {h}")
            print("  Resolution does not change inference cost, so prefer whichever "
                  "mode\n  the camera delivers fastest even if it is larger.\n")

    inference_ms = None
    if not args.skip_inference:
        print("MediaPipe inference:\n")
        latencies = probe_inference(args.model)
        if latencies:
            inference_ms = st.median(latencies)
            print(f"  p50 {inference_ms:.1f}ms  mean {st.mean(latencies):.1f}ms  "
                  f"p95 {sorted(latencies)[int(len(latencies) * 0.95)]:.1f}ms")
            print("  This does not change with camera resolution or hand count.\n")

    if camera_ms and inference_ms:
        total = camera_ms + inference_ms + 1.0 + args.ble_ms + args.servo_ms
        print("Budget:\n")
        print(f"  camera            {camera_ms:5.1f}ms   measured")
        print(f"  mediapipe         {inference_ms:5.1f}ms   measured")
        print(f"  python              1.0ms   measured")
        print(f"  BLE MIDI          {args.ble_ms:5.1f}ms   assumed, measure with a mic")
        print(f"  servo travel      {args.servo_ms:5.1f}ms   assumed, measure with a mic")
        print(f"  {'-' * 34}")
        print(f"  total             {total:5.1f}ms")
        print(f"\n  Set --latency-compensation-ms {round(total / 5) * 5:.0f}")
        print("  If hits still feel late, the assumed terms are too low. Record a "
              "slow\n  motion video of a hand and the drum and count frames between them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
