"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from tutti.core import ScoreError, load_score
from tutti.core.fleet import (
    DEFAULT_FLEET,
    LEGACY_CHANNELS,
    LEGACY_FLEET,
    LEGACY_NOTE_MAP,
    bind_score,
)
from tutti.core.player import play_plan
from tutti.core.plan import plan_score
from tutti.core.report import preflight
from tutti.core.selftest import build_test_score, describe
from tutti.core.ensemble import Ensemble


def cmd_score(args: argparse.Namespace) -> int:
    try:
        score = load_score(args.manifest)
    except ScoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"{score.name}: {len(score.events)} notes, {score.duration_s:.2f}s")
    if score.unassigned:
        print(f"warning: {score.unassigned} notes matched no part")

    for part in score.parts:
        events = score.for_part(part.part_id)
        print(f"  part {part.part_id} {part.role:<8} {len(events):>5} notes")

    if args.dump:
        print()
        for e in score.events[: args.dump]:
            print(f"  {e.time_s:8.3f}  part {e.part_id}  note {e.note:>3}  vel {e.velocity:>3}")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    try:
        score = load_score(args.manifest)
    except ScoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fleet = DEFAULT_FLEET
    binding = bind_score(fleet, score)
    for line in preflight(score, fleet, binding, args.tempo, args.tolerance_ms):
        print(line)
    return 0


def _open_transport(args, fleet):
    if args.transport == "null":
        from tutti.transports.loopback import NullTransport
        return NullTransport()
    if args.transport in ("legacy", "midi"):
        from tutti.transports.legacy_din import LegacyDinTransport
        legacy = args.transport == "legacy"
        # "midi" addresses each bot the way its board expects: General MIDI
        # on channel 10 for the ESP32 bots, and the old note numbers on the
        # old channel for any legacy board sharing the stage, so a xylophone
        # on an Arduino and two Bluetooth drums are one transport.
        return LegacyDinTransport(
            fleet,
            port_name=args.midi_port,
            note_map=LEGACY_NOTE_MAP,
            channels=LEGACY_CHANNELS if legacy else {b: LEGACY_CHANNELS.get(b, 9) for b in fleet},
            send_velocity=not legacy,
        )
    from tutti.transports.loopback import LoopbackTransport
    return LoopbackTransport(fleet)


def cmd_test(args: argparse.Namespace) -> int:
    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    fleet = {k: v for k, v in fleet.items() if v.role.lower() == args.role.lower()}
    if not fleet:
        known = ", ".join(sorted({i.role for i in DEFAULT_FLEET.values()}))
        print(f"error: no bot has role {args.role!r}. Known roles: {known}", file=sys.stderr)
        return 1

    score = build_test_score(role=args.role, note=args.note)
    binding = {1: list(fleet)}
    plan = plan_score(score, fleet, binding, args.tolerance_ms)

    for line in describe(score, fleet):
        print(line)
    print()
    nudged = plan.nudged
    if plan.drops or nudged:
        edge = min([d.requested_s for d in plan.drops] +
                   [h.requested_s for h in nudged])
        print(f"  From t={edge:.1f}s the ramp is past what this bot can sustain:")
        if nudged:
            print(f"    {len(nudged)} hits shifted late to fit "
                  f"(up to {max(h.nudge_ms for h in nudged):.0f}ms)")
        if plan.drops:
            print(f"    {len(plan.drops)} hits dropped outright")
        print("  So the ramp should stop accelerating near the end rather than "
              "getting faster.")
    else:
        print("  Every hit is inside the bot's limit; the ramp never outruns it.")
    print()

    transport = _open_transport(args, fleet)
    try:
        with transport:
            played = play_plan(plan, transport)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nstopped")
        return 0

    print(f"played {played} hits")
    if getattr(transport, "late", 0):
        print(f"note: {transport.late} went out late, worst {transport.worst_late_ms:.1f}ms")
    return 0


def cmd_gesture(args: argparse.Namespace) -> int:
    try:
        from tutti.sources.gesture import GestureSource
        source = GestureSource(
            model_path=args.model,
            camera_index=args.camera_index,
            latency_ms=args.latency_ms,
            detector=args.detector,
            mirror=not args.no_mirror,
            display=not args.no_display,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    if args.only:
        wanted = {r.strip().lower() for r in args.only.split(",")}
        fleet = {k: v for k, v in fleet.items() if v.role.lower() in wanted}
        if not fleet:
            print(f"error: no bot has role {args.only!r}", file=sys.stderr)
            return 1

    # The banner and the mapper must come from the same function, or the
    # screen says one layout and strikes follow another.
    from tutti.sources.gesture import zone_layout
    try:
        labels, _, notes = zone_layout(fleet)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    transport = _open_transport(args, fleet)
    try:
        with transport:
            ensemble = Ensemble(fleet, transport)
            print(f"On stage: {', '.join(sorted(fleet))}")
            print("Zones, left to right: "
                  + " | ".join(f"{l} (note {notes[l]})" for l in labels))
            print("Drum in the air. Closed fist mutes, open palm unmutes. "
                  "q in the preview window or Ctrl-C here to quit.")
            try:
                source.start(ensemble)
            except RuntimeError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

            # The preview window lives here, on the main thread. macOS
            # refuses UI from anywhere else, which is why the source only
            # composes frames and never shows them.
            show = not args.no_display
            cv2 = None
            if show:
                import cv2

            started = time.monotonic()
            next_status = started + 1.0
            try:
                while not source.stopped:
                    if args.duration and time.monotonic() - started >= args.duration:
                        break

                    if show:
                        frame = source.poll_display()
                        if frame is not None:
                            cv2.imshow("Tutti Gesture", frame)
                        if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                            break
                    else:
                        time.sleep(0.02)

                    now = time.monotonic()
                    if now >= next_status:
                        next_status = now + 1.0
                        s = ensemble.status()
                        line = (f"frames={source.frames} "
                                f"capture->strike={source.latency_ms_mean:.0f}ms "
                                f"hits={s['hits']} dropped={s['dropped']}")
                        if s["muted"]:
                            line += " MUTED"
                        if getattr(transport, "late", 0):
                            line += f" late={transport.late}"
                        print(line)
            except KeyboardInterrupt:
                pass
            finally:
                source.stop()
                if show and cv2 is not None:
                    cv2.destroyAllWindows()

            if source.error is not None:
                print(f"error: the gesture pipeline crashed: {source.error}",
                      file=sys.stderr)
                return 1

            s = ensemble.status()
            print(f"\nsession: {s['hits']} hits, {s['dropped']} dropped, "
                  f"{s['suppressed']} while muted")
            if s["drop_reasons"]:
                for reason, count in sorted(s["drop_reasons"].items()):
                    print(f"  {reason}: {count}")
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_jam(args: argparse.Namespace) -> int:
    from tutti.core.groove import parse_grouping
    from tutti.sources.jam import JamSource

    auto_meter = str(args.meter).strip().lower() == "auto"
    try:
        meter = 4 if auto_meter else int(args.meter)
    except ValueError:
        print(f"error: --meter wants a number of beats or 'auto', not {args.meter!r}",
              file=sys.stderr)
        return 1
    if not 1 <= meter <= 12:
        print("error: --meter must be between 1 and 12 beats", file=sys.stderr)
        return 1
    grouping = None
    if args.grouping:
        try:
            grouping = parse_grouping(args.grouping, meter)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    try:
        source = JamSource(
            input_port=args.input_port,
            fake_bpm=args.fake,
            fake_drift_pct_per_min=args.fake_drift,
            fake_meter=args.fake_meter,
            meter=meter,
            grouping=grouping,
            auto_meter=auto_meter,
            min_bpm=args.bpm_range[0],
            max_bpm=args.bpm_range[1],
            preferred_bpm=args.preferred_bpm,
            record_path=str(args.record) if args.record else None,
            tempo_hint=args.tempo,
            groove=args.groove,
            intensity=args.intensity,
            mode=args.mode,
            fill_every_bars=args.fill_every_bars,
            fill_probability=args.fill_probability,
            decoration=args.decoration,
            riffs=args.riffs,
            mutation=args.mutation,
            min_gap_ms=args.min_gap_ms,
            hold=args.hold,
            seed=args.seed,
            follow=not args.no_follow,
            infer_downbeat=not args.no_downbeat,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    if args.only:
        wanted = {r.strip().lower() for r in args.only.split(",")}
        fleet = {k: v for k, v in fleet.items() if v.role.lower() in wanted}
        if not fleet:
            print(f"error: no bot has role {args.only!r}", file=sys.stderr)
            return 1

    transport = _open_transport(args, fleet)
    try:
        with transport:
            ensemble = Ensemble(fleet, transport)
            try:
                source.start(ensemble)
            except RuntimeError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

            print(f"On stage: {', '.join(sorted(fleet))}")
            print(f"Listening to: {source.input_label}")
            print("Meter: " + ("auto, starting from " if source.auto_meter else "")
                  + _meter_label(source))
            if source.tempo_hint:
                print(f"Tempo: around {source.tempo_hint:.0f} BPM, following you from there; "
                      "the drums keep time through rests.")
            print("Play steadily and the drums join once the tracker locks. "
                  "Commands (press Enter):")
            print("  +/- intensity | mode groove|sparse|busy|auto | decor 0..1 | "
                  "riffs phrase|period|none | fill | mute | status | quit")

            # Commands arrive on stdin lines; the reader blocks in its own
            # daemon thread and the main loop drains a queue, so Ctrl-C and
            # --duration keep working.
            import queue as queue_mod
            import threading
            commands: queue_mod.SimpleQueue[str] = queue_mod.SimpleQueue()

            def _read_commands() -> None:
                try:
                    for line in sys.stdin:
                        commands.put(line.strip())
                except ValueError:
                    pass    # stdin closed under us; nothing left to read

            threading.Thread(target=_read_commands, name="jam-commands",
                             daemon=True).start()

            def _status_line() -> str:
                st = source.beat_state
                s = ensemble.status()
                bpm = f"{st.bpm:6.1f}" if st.bpm else "  --.-"
                auto = "*" if source.following else ""
                meter_mark = "*" if source.auto_meter else ""
                line = (f"bpm={bpm} conf={st.confidence:.2f} "
                        f"lock={'Y' if st.locked else 'n'} "
                        f"meter={_meter_label(source)}{meter_mark} "
                        f"bar={st.bar_index} beat={st.beat_in_bar} "
                        f"mode={source.mode}{auto} int={source.intensity}{auto} "
                        f"piano={source.piano_notes} hits={s['hits']} "
                        f"dropped={s['dropped']}")
                if st.alternatives:
                    line += " alt=" + "/".join(f"{b:.0f}" for b in st.alternatives[:2])
                if source.groove == "generative" and st.locked:
                    line += f" act={source.activity:.2f} decor={source.decoration:.1f}"
                    ctx = source.phrase_context
                    if ctx is not None:
                        line += f" sec={ctx.section} phr={ctx.bar_in_phrase + 1}/{ctx.bars_per_phrase}"
                    hs = source.harmony_state
                    if hs is not None and hs.chord is not None:
                        line += f" chord={hs.chord.name} key={hs.key_name}"
                    if st.swing >= 0.56:
                        line += f" swing={st.swing:.2f}"
                if st.rubato > 1.03:
                    line += f" rit=+{(st.rubato - 1) * 100:.0f}%"
                elif st.rubato < 0.97:
                    line += f" accel={(st.rubato - 1) * 100:.0f}%"
                feel = source.feel
                if feel is not None:
                    line += f" loud={feel.loudness:.2f} dens={feel.density:.1f}"
                    if feel.velocity_scale < 1.0:
                        line += f" fading={feel.velocity_scale:.2f}"
                if source.gap_fills:
                    line += f" fills={source.gap_fills}"
                if s["muted"]:
                    line += " MUTED"
                if getattr(transport, "late", 0):
                    line += f" late={transport.late}"
                return line

            started = time.monotonic()
            next_status = started + 1.0
            quitting = False
            try:
                while not source.stopped and not quitting:
                    if args.duration and time.monotonic() - started >= args.duration:
                        break
                    time.sleep(0.02)

                    while True:
                        try:
                            cmd = commands.get_nowait()
                        except queue_mod.Empty:
                            break
                        if cmd == "+":
                            source.set_intensity(source.intensity + 1)
                        elif cmd == "-":
                            source.set_intensity(source.intensity - 1)
                        elif cmd.lower().startswith("mode"):
                            try:
                                source.set_mode(cmd.split(None, 1)[1])
                            except (IndexError, ValueError) as exc:
                                print(f"? {exc}")
                        elif cmd.lower().startswith("decor"):
                            try:
                                source.set_decoration(float(cmd.split(None, 1)[1]))
                                print(f"decoration {source.decoration:.2f}")
                            except (IndexError, ValueError) as exc:
                                print(f"? decor 0..1 ({exc})")
                        elif cmd.lower().startswith("riffs"):
                            try:
                                source.set_riffs(cmd.split(None, 1)[1])
                                print(f"riffs {source.riffs}")
                            except (IndexError, ValueError) as exc:
                                print(f"? {exc}")
                        elif cmd.lower() == "fill":
                            source.request_fill()
                        elif cmd.lower() == "mute":
                            ensemble.command("ARM" if ensemble.muted else "STOP")
                        elif cmd.lower() == "status":
                            print(_status_line())
                        elif cmd.lower() in ("quit", "q", "exit"):
                            quitting = True
                        elif cmd:
                            print(f"? unknown command {cmd!r}")

                    now = time.monotonic()
                    if now >= next_status:
                        next_status = now + 1.0
                        print(_status_line())
            except KeyboardInterrupt:
                pass
            finally:
                source.stop()

            if source.error is not None:
                print(f"error: the jam pipeline crashed: {source.error}",
                      file=sys.stderr)
                return 1

            s = ensemble.status()
            print(f"\nsession: heard {source.piano_notes} piano notes, "
                  f"played {s['hits']} hits, {s['dropped']} dropped, "
                  f"{s['suppressed']} while muted")
            if source.meter_switches:
                print(f"  meter changed {source.meter_switches} time(s); "
                      f"ended in {_meter_label(source)}")
            if s["drop_reasons"]:
                for reason, count in sorted(s["drop_reasons"].items()):
                    print(f"  {reason}: {count}")
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_conduct(args: argparse.Namespace) -> int:
    from tutti.sources.conduct import ConductSource

    if args.improv == (args.manifest is not None):
        print("error: conduct a score manifest, or --improv for the old demo; "
              "one or the other", file=sys.stderr)
        return 1

    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    if args.only:
        wanted = {r.strip().lower() for r in args.only.split(",")}
        fleet = {k: v for k, v in fleet.items() if v.role.lower() in wanted}
        if not fleet:
            print(f"error: no bot has role {args.only!r}", file=sys.stderr)
            return 1
    accepts: set[int] = set()
    for inst in fleet.values():
        accepts |= set(inst.model.accepts)

    if args.improv:
        from tutti.core.improv import Improviser, SNARE_NOTE, TOM_NOTE, XYLO_LOW, XYLO_HIGH
        try:
            program = Improviser(
                scale=args.scale, tonic=args.key, xylo=args.xylo, snare=args.snare,
                tom=args.tom, harmony=args.harmony, seed=args.seed)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        wanted = {SNARE_NOTE, TOM_NOTE} | set(range(XYLO_LOW, XYLO_HIGH + 1))
        if not accepts & wanted:
            print("error: nothing on stage plays a snare, a tom or a xylophone note",
                  file=sys.stderr)
            return 1
        count_in = args.count_in or 2
        what = f"improvising in {program.key_name} {program.scale}"
    else:
        from tutti.core.conduct import ScoreProgram
        try:
            score = load_score(args.manifest)
        except ScoreError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        offset = "auto" if args.offset_beats is None else args.offset_beats
        try:
            program = ScoreProgram(score, beat_unit=args.beat_unit, offset_beats=offset,
                                   beats_per_bar=args.meter, accepts=accepts)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if program.notes == 0:
            print("error: no note in this score can be played by anything on stage",
                  file=sys.stderr)
            return 1
        count_in = args.count_in or 4
        what = f"{score.name}: {program.notes} notes, {program.describe()}"
        if program.unplayable:
            what += f" ({program.unplayable} notes nothing on stage plays are skipped)"

    try:
        source = ConductSource(
            program,
            count_in=count_in,
            camera=not args.no_camera and args.fake is None,
            model_path=args.model,
            camera_index=args.camera_index,
            latency_ms=args.latency_ms,
            detector=args.detector,
            mirror=not args.no_mirror,
            display=not args.no_display,
            tap_port=args.tap_port,
            fake_bpm=args.fake,
            fake_drift_pct_per_min=args.fake_drift,
            dynamics=not args.no_dynamics,
            coast=args.coast,
            min_bpm=args.bpm_range[0],
            max_bpm=args.bpm_range[1],
        )
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    transport = _open_transport(args, fleet)
    try:
        with transport:
            ensemble = Ensemble(fleet, transport)
            try:
                source.start(ensemble)
            except RuntimeError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

            print(f"On stage: {', '.join(sorted(fleet))}")
            ports = getattr(transport, "port_names", ())
            if ports:
                print(f"MIDI ports: {', '.join(ports)}")
            print(what)
            print(f"Beats from: {', '.join(source.input_labels)}")
            if args.improv:
                print(f"Count in {count_in} strokes and it plays; stop and it stops.")
            else:
                print(f"Count in {count_in} strokes; the piece starts on the next. "
                      "Stop conducting and it holds on the next beat; "
                      "start again and it carries on.")
            print("Commands (then Enter): Enter alone taps a beat | restart | mute | "
                  "status | quit")
            if args.improv:
                print("  xylo 0..1 | snare 0..1 | tom 0..1 | scale NAME | key NAME | harmony on|off")

            import queue as queue_mod
            import threading
            commands: queue_mod.SimpleQueue[str] = queue_mod.SimpleQueue()

            def _read_commands() -> None:
                try:
                    for line in sys.stdin:
                        commands.put(line.rstrip("\n"))
                except ValueError:
                    pass    # stdin closed under us; nothing left to read

            threading.Thread(target=_read_commands, name="conduct-commands",
                             daemon=True).start()

            show = source.poll_display is not None and not args.no_camera and \
                args.fake is None and not args.no_display
            cv2 = None
            if show:
                import cv2

            def _status_line() -> str:
                clock = source.clock
                s = ensemble.status()
                bpm = f"{clock.bpm:5.1f}" if clock is not None and clock.bpm else " --.-"
                line = f"bpm={bpm} {program.describe()}"
                if clock is not None:
                    line += f" strokes={clock.strokes}"
                    if clock.bounces:
                        line += f" bounces={clock.bounces}"
                    if source.last_stroke is not None:
                        line += f" last={source.last_stroke.kind}"
                    if clock.holding(ensemble.now_s()):
                        line += " HOLD"
                    if not args.no_dynamics:
                        line += f" dyn={clock.dynamics:.2f}"
                line += (f" sent={source.scheduled} dropped={s['dropped']} "
                         f"skipped={source.skipped}")
                if source.frames:
                    line += f" frames={source.frames} cam={source.latency_ms_mean:.0f}ms"
                if s["muted"]:
                    line += " MUTED"
                if getattr(transport, "late", 0):
                    line += f" late={transport.late}"
                return line

            started = time.monotonic()
            next_status = started + 1.0
            quitting = False
            try:
                while not source.stopped and not quitting:
                    if args.duration and time.monotonic() - started >= args.duration:
                        break
                    if show:
                        frame = source.poll_display()
                        if frame is not None:
                            cv2.imshow("Tutti Conduct", frame)
                        key = cv2.waitKey(1) & 0xFF
                        if key in (ord("q"), 27):
                            break
                        if key == ord(" "):
                            source.tap()
                        if key == ord("r"):
                            source.restart()
                    else:
                        time.sleep(0.02)

                    while True:
                        try:
                            cmd = commands.get_nowait()
                        except queue_mod.Empty:
                            break
                        word = cmd.strip().lower()
                        if word == "":
                            source.tap()
                        elif word in ("restart", "top"):
                            source.restart()
                            print("from the top: count in again")
                        elif word == "mute":
                            ensemble.command("ARM" if ensemble.muted else "STOP")
                        elif word == "status":
                            print(_status_line())
                        elif word in ("quit", "q", "exit"):
                            quitting = True
                        elif args.improv and word.split()[0] in ("xylo", "snare", "tom"):
                            try:
                                program.set_density(word.split()[0], float(word.split()[1]))
                                print(f"{word.split()[0]} density {program.density(word.split()[0]):.2f}")
                            except (IndexError, ValueError) as exc:
                                print(f"? {word.split()[0]} 0..1 ({exc})")
                        elif args.improv and word.startswith("scale"):
                            try:
                                program.set_scale(word.split(None, 1)[1])
                                print(f"scale {program.scale}")
                            except (IndexError, ValueError) as exc:
                                print(f"? {exc}")
                        elif args.improv and word.startswith("key"):
                            try:
                                program.set_tonic(cmd.strip().split(None, 1)[1])
                                print(f"key {program.key_name}")
                            except (IndexError, ValueError) as exc:
                                print(f"? {exc}")
                        elif args.improv and word.startswith("harmony"):
                            program.harmony = not word.endswith("off")
                            print(f"harmony {'on' if program.harmony else 'off'}")
                        else:
                            print(f"? unknown command {cmd!r}")

                    now = time.monotonic()
                    if now >= next_status:
                        next_status = now + 1.0
                        print(_status_line())
            except KeyboardInterrupt:
                pass
            finally:
                source.stop()
                if show and cv2 is not None:
                    cv2.destroyAllWindows()

            if source.error is not None:
                print(f"error: the conduct pipeline crashed: {source.error}",
                      file=sys.stderr)
                return 1

            s = ensemble.status()
            clock = source.clock
            print(f"\nsession: {clock.strokes if clock else 0} strokes, "
                  f"{s['hits']} hits, {s['dropped']} dropped, {source.skipped} skipped, "
                  f"{s['suppressed']} while muted")
            if s["drop_reasons"]:
                for reason, count in sorted(s["drop_reasons"].items()):
                    print(f"  {reason}: {count}")
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_latency(args: argparse.Namespace) -> int:
    from tutti.core.latency import MicCapture, run_probe

    if args.list_inputs:
        inputs = MicCapture.list_inputs()
        print("Audio inputs:" if inputs else "No audio inputs found (is sounddevice installed?).")
        for name in inputs:
            print(f"  {name}")
        return 0

    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    fleet = {k: v for k, v in fleet.items() if v.role.lower() == args.role.lower()}
    if not fleet:
        known = ", ".join(sorted({i.role for i in DEFAULT_FLEET.values()}))
        print(f"error: no bot has role {args.role!r}. Known roles: {known}", file=sys.stderr)
        return 1
    bot = next(iter(fleet.values()))

    transport = _open_transport(args, fleet)
    capture = MicCapture(device=args.input_device)
    try:
        with transport:
            ensemble = Ensemble(fleet, transport)
            capture.start()
            print(f"Striking {bot.bot_id} (note {args.note}) {args.hits} times, "
                  f"{args.gap:.2f}s apart, listening on the microphone. Keep quiet.")
            report = run_probe(ensemble, args.note, args.hits, args.gap, capture)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nstopped")
        return 0
    finally:
        capture.stop()

    print(f"{report.intended} hits: {report.matched} heard, {report.missed} missed, "
          f"{report.spurious} onsets that were not a hit")
    print(f"recording: peak {report.peak:.3f}, hits {report.snr_db:.0f} dB over the room")
    if not report.clean:
        print("That is not enough signal over noise to believe any number from it. "
              "Put the microphone at the drum (a laptop listening to its own "
              "speakers hears mostly itself), raise the input gain, and try again.")
        return 1
    if not report.usable:
        print("Not enough hits were heard to trust a number. Check that the bot "
              "is actually striking and that the gap leaves room for its ring.")
        return 1
    print(f"acoustic onset vs intended: median {report.median_ms:+.1f} ms, "
          f"mean {report.mean_ms:+.1f}, sd {report.stdev_ms:.1f}, "
          f"range {min(report.samples_ms):+.1f}..{max(report.samples_ms):+.1f}")
    current = bot.model.mech_latency_ms
    suggested = report.suggested_mech_latency_ms(current)
    print(f"fleet.py carries mech_latency_ms={current:.0f} for {bot.bot_id}; "
          f"what is left over is {report.median_ms:+.1f} ms, so set it to {suggested:.0f}.")
    if report.stdev_ms > 10.0:
        print(f"note: the spread ({report.stdev_ms:.1f} ms) is large; that is mech_jitter_ms, "
              "and worth recording too.")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from tutti.sources.jam import load_session
    from tutti.sources.replay import describe, replay_session

    try:
        events = load_session(args.session)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not events:
        print("error: the session has no notes", file=sys.stderr)
        return 1
    auto_meter = str(args.meter).strip().lower() == "auto"
    meter = 4 if auto_meter else int(args.meter)
    replay = replay_session(
        events, snapshot_every_s=args.every, meter=meter, auto_meter=auto_meter,
        preferred_bpm=args.preferred_bpm, tempo_hint=args.tempo, seed=1,
    )
    for line in describe(replay):
        print(line)
    return 0


def _meter_label(source) -> str:
    label = f"{source.meter}/4"
    if len(source.grouping) > 1:
        label += "(" + "+".join(str(g) for g in source.grouping) + ")"
    return label


def cmd_ports(args: argparse.Namespace) -> int:
    from tutti.sources.midi_in import MidiInput
    from tutti.transports.legacy_din import LegacyDinTransport

    outputs = LegacyDinTransport.list_ports()
    inputs = MidiInput.list_inputs()
    if not outputs and not inputs:
        print("No MIDI ports found.")
        return 0
    print("MIDI outputs:")
    for name in outputs or ():
        print(f"  {name}")
    if not outputs:
        print("  none")
    print("\nMIDI inputs:")
    for name in inputs or ():
        print(f"  {name}")
    if not inputs:
        print("  none")
    print("\nPass any part of an output name to --midi-port (repeat it for more "
          "ports), and of\nan input name to 'tutti jam --input-port'. Never an "
          "index: the number changes with\nthe laptop and the order things were "
          "plugged in.")
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    try:
        score = load_score(args.manifest)
    except ScoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fleet = LEGACY_FLEET if args.transport == "legacy" else DEFAULT_FLEET
    if args.only:
        wanted = {r.strip().lower() for r in args.only.split(",")}
        fleet = {k: v for k, v in fleet.items() if v.role.lower() in wanted}
        if not fleet:
            print(f"error: no bot has role {args.only!r}. Known roles: "
                  f"{', '.join(sorted({i.role for i in DEFAULT_FLEET.values()}))}",
                  file=sys.stderr)
            return 1
    binding = bind_score(fleet, score)
    scale = score.initial_bpm / args.tempo if args.tempo else 1.0
    plan = plan_score(score, fleet, binding, args.tolerance_ms, scale)

    bpm = args.tempo or score.initial_bpm
    print(f"{score.name}: {len(plan.hits)} hits at {bpm:.0f} BPM "
          f"on {', '.join(sorted(fleet))}")
    unplayable = [d for d in plan.drops if d.reason != "no_bot_for_part"]
    skipped = len(plan.drops) - len(unplayable)
    if skipped:
        print(f"  {skipped} notes belong to parts no connected bot plays; skipping them")
    if unplayable:
        print(f"  warning: {len(unplayable)} notes cannot be played; "
              f"run 'tutti preflight' to see why")

    if args.render:
        from tutti.transports.loopback import render_to_wav
        seconds = render_to_wav(plan.hits, args.render, fleet)
        print(f"wrote {args.render} ({seconds:.1f}s)")
        return 0

    transport = _open_transport(args, fleet)

    try:
        with transport:
            played = play_plan(plan, transport)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nstopped")
        return 0

    print(f"played {played} hits")
    if getattr(transport, "late", 0):
        print(f"note: {transport.late} hits went out late, worst "
              f"{transport.worst_late_ms:.1f}ms")
    mixer = getattr(transport, "mixer", None)
    if mixer is not None and mixer.clipped_blocks:
        print(f"note: {mixer.clipped_blocks} blocks clipped, "
              f"more voices landed together than the bots could sustain")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tutti", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("score", help="load a score manifest and summarise it")
    p.add_argument("manifest", type=Path)
    p.add_argument("--dump", type=int, default=0, metavar="N", help="print the first N events")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("preflight", help="check whether the fleet can actually play a score")
    p.add_argument("manifest", type=Path)
    p.add_argument("--tempo", type=float, default=None, metavar="BPM",
                   help="target tempo; defaults to the tempo written in the file")
    p.add_argument("--tolerance-ms", type=float, default=15.0,
                   help="how far a note may be shifted before it counts as moved")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("play", help="play a score, through the speakers by default")
    p.add_argument("manifest", type=Path)
    p.add_argument("--tempo", type=float, default=None, metavar="BPM")
    p.add_argument("--tolerance-ms", type=float, default=15.0)
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="loopback",
                   help="loopback: speakers. midi: bots that speak General MIDI, "
                        "which is every ESP32 bot. legacy: old Arduino boards that need "
                        "note numbers translated. null: dry run.")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME",
                   help="MIDI output for --transport midi/legacy, matched by substring; "
                        "every port matching is opened, and the flag may be repeated")
    p.add_argument("--only", type=str, default=None, metavar="ROLE",
                   help="use only bots with these roles, e.g. --only snare")
    p.add_argument("--render", type=Path, default=None, metavar="OUT.wav",
                   help="render to a WAV file instead of playing; needs no sound card")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("test", help="play a short bring-up pattern at one bot")
    p.add_argument("--role", type=str, default="snare")
    p.add_argument("--note", type=int, default=38, help="General MIDI note (38 = snare)")
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="loopback")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME")
    p.add_argument("--tolerance-ms", type=float, default=15.0)
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("gesture", help="drum in the air at the webcam")
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="loopback")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME")
    p.add_argument("--only", type=str, default=None, metavar="ROLE",
                   help="use only bots with these roles, e.g. --only snare")
    p.add_argument("--model", type=Path, default=None,
                   help="gesture_recognizer.task; defaults to DrumBot's copy")
    p.add_argument("--camera-index", type=int, default=0)
    p.add_argument("--latency-ms", type=int, default=90,
                   help="fire this far ahead of predicted impact; "
                        "run DrumBot/probe_latency.py to pick a value")
    p.add_argument("--detector", choices=("predictive", "legacy"), default="predictive")
    p.add_argument("--no-mirror", action="store_true")
    p.add_argument("--no-display", action="store_true")
    p.add_argument("--duration", type=float, default=0.0,
                   help="stop after this many seconds; 0 runs until quit")
    p.set_defaults(func=cmd_gesture)

    p = sub.add_parser("jam", help="improvise drums along with a piano")
    p.add_argument("--input-port", type=str, default=None, metavar="NAME",
                   help="MIDI input to listen to, matched by substring; "
                        "defaults to the first port that looks like a piano")
    p.add_argument("--fake", nargs="?", const=100.0, default=None, type=float,
                   metavar="BPM",
                   help="jam with a built-in fake pianist instead of a MIDI "
                        "input; needs no hardware at all")
    p.add_argument("--fake-drift", type=float, default=0.0, metavar="PCT",
                   help="fake pianist tempo drift, percent per minute")
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="loopback",
                   help="loopback: speakers. midi: ESP32 bots. legacy: old "
                        "Arduino boards. null: dry run.")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME",
                   help="MIDI output for --transport midi/legacy, matched by substring; "
                        "every port matching is opened, and the flag may be repeated")
    p.add_argument("--only", type=str, default="snare,tom", metavar="ROLES",
                   help="use only bots with these roles (default: snare,tom)")
    p.add_argument("--meter", type=str, default="4", metavar="N|auto",
                   help="beats per bar (default 4), or 'auto' to infer it from "
                        "the playing, starting from 4")
    p.add_argument("--grouping", type=str, default=None, metavar="A+B",
                   help="how the bar clumps, e.g. 3+2 or 2+3 for 5/4; "
                        "defaults per meter (5/4 is 3+2, 7/4 is 4+3)")
    p.add_argument("--fake-meter", type=int, default=None, metavar="N",
                   help="beats per bar the fake pianist plays in, if different "
                        "from --meter; pair with --meter auto to watch detection")
    p.add_argument("--bpm-range", nargs=2, type=float, default=(50.0, 180.0),
                   metavar=("LO", "HI"), help="tempo range the tracker considers")
    p.add_argument("--preferred-bpm", type=float, default=100.0, metavar="BPM",
                   help="where the beat usually lives; eighths at 80 and quarters "
                        "at 160 are the same pattern, and this decides which it is "
                        "(default 100: fast tunes read as half time)")
    p.add_argument("--tempo", type=float, default=None, metavar="BPM",
                   help="the tempo you mean to play at: locks in a beat or two, "
                        "follows you around it, never wanders to double or half "
                        "time, and keeps time through rests like a drummer who "
                        "knows the song")
    p.add_argument("--intensity", type=int, default=2, choices=range(0, 5))
    p.add_argument("--mode", choices=("groove", "sparse", "busy"), default="groove")
    p.add_argument("--fill-every-bars", type=int, default=8,
                   help="classic groove only: fill every N bars")
    p.add_argument("--fill-probability", type=float, default=0.30,
                   help="classic groove only")
    p.add_argument("--decoration", type=float, default=0.5, metavar="0..1",
                   help="how much optional playing goes around the beat: 0 is "
                        "the plain beat, 1 is everything the pianist's activity "
                        "can buy (default 0.5)")
    p.add_argument("--riffs", choices=("phrase", "period", "none"), default="phrase",
                   help="where fills go: every phrase end with a bigger one at a "
                        "period end (default), only period ends, or only the holes "
                        "the pianist leaves and the 'fill' command")
    p.add_argument("--mutation", type=float, default=0.25, metavar="0..1",
                   help="share of the optional hits re-rolled each bar; 0 repeats "
                        "the bar, 1 re-rolls it (default 0.25)")
    p.add_argument("--min-gap-ms", type=float, default=None, metavar="MS",
                   help="never ask one drum for two hits closer than this; the "
                        "default is what its model says it can do")
    p.add_argument("--hold", type=float, default=None, metavar="0..1",
                   help="how firmly the beat holds against stray notes and "
                        "pushes: 0 follows every onset (default), 1 is a "
                        "flywheel; try 0.5 if the beat gets pushed around")
    p.add_argument("--seed", type=int, default=None,
                   help="seed the groove and fake-piano randomness")
    p.add_argument("--groove", choices=("generative", "classic"), default="generative",
                   help="generative: grooves made up bar by bar from the playing "
                        "(default). classic: the three fixed patterns")
    p.add_argument("--no-follow", action="store_true",
                   help="do not follow the pianist's dynamics; intensity and "
                        "mode are manual only")
    p.add_argument("--no-downbeat", action="store_true",
                   help="do not infer where the bar starts from accents")
    p.add_argument("--record", type=Path, default=None, metavar="FILE.jsonl",
                   help="save every piano note-on so the session can be replayed "
                        "with 'tutti replay'")
    p.add_argument("--duration", type=float, default=0.0,
                   help="stop after this many seconds; 0 runs until quit")
    p.set_defaults(func=cmd_jam)

    p = sub.add_parser("conduct", help="conduct a piece, or the old improv demo, "
                                       "by beating time at the webcam")
    p.add_argument("manifest", type=Path, nargs="?", default=None,
                   help="a score manifest to conduct")
    p.add_argument("--improv", action="store_true",
                   help="the old InteractiveDemo music instead of a score: a "
                        "xylophone walk through a scale over snare and tom patterns")
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="loopback",
                   help="loopback: speakers. midi: ESP32 bots, plus any legacy "
                        "board on another port. legacy: old Arduino boards only. "
                        "null: dry run.")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME",
                   help="MIDI output, matched by substring; every matching port is "
                        "opened and the flag may be repeated, e.g. --midi-port "
                        "RobOrchestra --midi-port USB for the drums and the xylophone")
    p.add_argument("--only", type=str, default=None, metavar="ROLES",
                   help="use only bots with these roles, e.g. --only snare,tom")
    p.add_argument("--count-in", type=int, default=None, metavar="N",
                   help="strokes before the music starts (default 4 for a score, "
                        "2 for --improv)")
    p.add_argument("--meter", type=int, default=4, metavar="N",
                   help="beats per bar, for the bar count and for placing a pickup")
    p.add_argument("--beat-unit", type=float, default=1.0, metavar="QUARTERS",
                   help="quarter notes per stroke: 2 to conduct a fast 4/4 in two, "
                        "0.5 to beat eighths in a slow piece, 1.5 for 6/8 in two")
    p.add_argument("--offset-beats", type=float, default=None, metavar="BEATS",
                   help="shift the score so that this many beats come before the "
                        "first downbeat; by default a pickup lands inside the "
                        "count-in and the first downbeat is the first beat after it")
    p.add_argument("--coast", type=int, default=0, metavar="BEATS",
                   help="beats the orchestra may play past your last stroke before "
                        "holding (default 0: it holds on the next beat)")
    p.add_argument("--no-dynamics", action="store_true",
                   help="ignore stroke size; play the written velocities")
    p.add_argument("--bpm-range", nargs=2, type=float, default=(30.0, 240.0),
                   metavar=("LO", "HI"), help="tempi a stroke may set")
    p.add_argument("--scale", type=str, default="major",
                   help="--improv: major, minor, dorian, mixolydian, blues, "
                        "pentatonic, minor_pentatonic, whole_tone, chromatic, ...")
    p.add_argument("--key", type=str, default="C", help="--improv: the tonic, e.g. F#")
    p.add_argument("--xylo", type=float, default=0.55, metavar="0..1",
                   help="--improv: xylophone density")
    p.add_argument("--snare", type=float, default=0.70, metavar="0..1",
                   help="--improv: snare density")
    p.add_argument("--tom", type=float, default=0.45, metavar="0..1",
                   help="--improv: tom density")
    p.add_argument("--harmony", action="store_true",
                   help="--improv: add a third above every melody note")
    p.add_argument("--seed", type=int, default=None, help="--improv: seed the walk")
    p.add_argument("--no-camera", action="store_true",
                   help="beats from Enter, a MIDI pad or --fake only")
    p.add_argument("--tap-port", type=str, default=None, metavar="NAME",
                   help="also take beats from any note on this MIDI input")
    p.add_argument("--fake", nargs="?", const=110.0, default=None, type=float,
                   metavar="BPM",
                   help="a built-in metronome conducts instead of the webcam; "
                        "needs no hardware at all")
    p.add_argument("--fake-drift", type=float, default=0.0, metavar="PCT",
                   help="fake conductor tempo drift, percent per minute")
    p.add_argument("--model", type=Path, default=None,
                   help="gesture_recognizer.task; defaults to DrumBot's copy")
    p.add_argument("--camera-index", type=int, default=0)
    p.add_argument("--latency-ms", type=int, default=90,
                   help="fire this far ahead of the predicted landing of the hand")
    p.add_argument("--detector", choices=("predictive", "legacy"), default="predictive")
    p.add_argument("--no-mirror", action="store_true")
    p.add_argument("--no-display", action="store_true")
    p.add_argument("--duration", type=float, default=0.0,
                   help="stop after this many seconds; 0 runs until quit")
    p.set_defaults(func=cmd_conduct)

    p = sub.add_parser("replay", help="run a recorded piano session through the "
                                      "tracker offline and show what it believed")
    p.add_argument("session", type=Path, help="a .jsonl from 'tutti jam --record'")
    p.add_argument("--meter", type=str, default="4")
    p.add_argument("--preferred-bpm", type=float, default=100.0)
    p.add_argument("--tempo", type=float, default=None, metavar="BPM",
                   help="replay as if this tempo had been declared")
    p.add_argument("--every", type=float, default=1.0, metavar="SECONDS",
                   help="how often to report the tracker's state")
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("latency", help="measure a bot's real latency with a microphone")
    p.add_argument("--transport", choices=("loopback", "midi", "legacy", "null"),
                   default="midi",
                   help="midi: a real bot. loopback: the speakers, which checks the "
                        "probe itself against a known-good path")
    p.add_argument("--midi-port", type=str, action="append", default=None, metavar="NAME")
    p.add_argument("--role", type=str, default="snare")
    p.add_argument("--note", type=int, default=38, help="General MIDI note (38 = snare)")
    p.add_argument("--hits", type=int, default=12)
    p.add_argument("--gap", type=float, default=0.75, metavar="SECONDS",
                   help="time between hits; leave room for the ring to die")
    p.add_argument("--input-device", type=str, default=None, metavar="NAME",
                   help="microphone, matched by substring; default input otherwise")
    p.add_argument("--list-inputs", action="store_true", help="list audio inputs and exit")
    p.set_defaults(func=cmd_latency)

    p = sub.add_parser("ports", help="list MIDI inputs and outputs")
    p.set_defaults(func=cmd_ports)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
