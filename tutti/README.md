# Tutti

Control software for the RoboOrchestra ensemble.

Runs on macOS, Windows and Linux. The test suite needs no hardware.

## Setup

    uv sync
    uv run pytest -q

## Usage

Summarise a score and show how its notes divide between parts:

    uv run tutti score scores/Route1.json --dump 8

Check whether the fleet can physically play it, and how fast it could go:

    uv run tutti preflight scores/ThinkingOutLoud.json
    uv run tutti preflight scores/ThinkingOutLoud.json --tempo 330

Every bot has a floor on how fast it can hit, set by how long a stick takes to
travel down and recover. Preflight walks the score against those limits before
anyone presses play, shifts notes slightly where that is enough, moves them to
another bot where it is not, and names a reason for every note it still cannot
place. The old firmware discovers the same limits at play time and silently
discards whatever it cannot manage.

    part 1 xylo    : 360 notes, 2 infeasible, 17 nudged
      t= 29.818s beat  164.00  sustainable cycle/voice is 55.0ms; next voice free in 19.1ms  -> DROP cycle_not_ready
      ...
    Max feasible tempo for this arrangement: 316 BPM

## Hearing it without hardware

    uv sync --extra audio
    uv run tutti play scores/ThinkingOutLoud.json

The loopback transport plays the plan through the speakers, so nobody needs to
be in the Roboclub room with a working MIDI chain to work on Tutti. Sounds are
generated rather than sampled, which keeps binaries out of the repo and covers
all 17 xylophone pitches without 17 files.

On a machine with no working audio, or in CI, render to a file instead:

    uv run tutti play scores/ThinkingOutLoud.json --render out.wav

Rendering runs about 300x faster than realtime.

Loopback is also the reference the real transports get measured against. The
mixer places every hit on an exact sample rather than rounding to an audio
block, so anything that sounds loose is the plan's fault, not the link's.

## Bringing up one bot

Find the port name, then play the bring-up pattern at it:

    uv run tutti ports
    uv run tutti test --transport midi --midi-port RobOrchestra_Snare

Three phases in about 12 seconds: separated single hits so you can see it
trigger, a steady rhythm so you can hear whether it is even, and a ramp that
speeds up past what the bot can physically do so you hear where its limit
really is. The ramp should stop accelerating near the end. If it stops earlier
than the printed rate, the servo probably needs recalibrating.

Use `--transport loopback` first to hear the pattern through the speakers with
no hardware at all.

`--role` and `--note` pick a different bot: `--role tom --note 45`.

## Drumming in the air

    uv sync --extra gesture --extra audio
    uv run tutti gesture

Opens the webcam and splits the screen into one zone per role on stage, left
to right. Strike downward in a zone and that instrument plays: through the
speakers by default, or at real bots with `--transport midi --midi-port
RobOrchestra`. A closed fist mutes the kit, an open palm brings it back.
`--only snare` puts a single bot on stage with the whole screen as its zone.

The detection pipeline is DrumBot's, imported from `../DrumBot`, and stays
there because that is where it is tuned against hardware. What changed is
where a strike goes: it now passes through the same physical model as score
playback, so a flurry faster than the sticks can move is counted and named
instead of silently swallowed. `--latency-ms` is the predictive lead; run
`DrumBot/probe_latency.py` to pick a value for your machine.

## Jamming with a piano

    uv sync --extra audio
    uv run tutti jam --fake

Drums improvise along with whoever is playing. `--fake` is a built-in pianist
so the whole pipeline runs with nothing plugged in: comped chords with a loud
low root on the downbeat, a little timing jitter, the occasional off-beat
push. Expect the tracker to lock within about two bars and the groove to come
in on the grid, through the speakers by default. `--fake 130` changes its
tempo, `--fake-drift 8` makes it speed up so you can hear the drums follow,
`--meter 3` makes it waltz.

With a real keyboard, plug it in over USB and:

    uv run tutti ports
    uv run tutti jam --input-port "Digital Piano"

The design rule is: predict the grid, don't react to notes. A stick takes
real time to swing, so reacting to a note that already sounded means playing
behind it forever. Note-ons feed a beat tracker (chords merge into one onset,
tempo comes from interval voting, phase from a nudged flywheel), and once it
locks, the groove engine writes the next beat's drums onto the predicted grid
via `Ensemble.strike_at()`, early enough for any transport to land them on
time. When the tracker is not confident the drums stay silent.

The drums also listen to *how* the piano is played, not just when. The
groove is made up bar by bar rather than looked up: a kick opens every
group of the bar and the snare answers it, and those never move, but
everything else — offbeat kicks, the push into the next group, ghost snares,
a tom before the backbeat — is a probability shaped by one knob, activity,
which the pianist's loudness raises and a piano flurry lowers. Each bar
re-rolls a quarter of those decisions, so the groove evolves without
churning. Every hit's velocity follows the pianist's gain continuously, and
the beats they lean on get leaned on. Swing is read from their offbeats and
the drums' offbeats go there too.

The piece's shape gets its due. Bars are counted into four-bar phrases and
eight-bar periods (a fill at a phrase end, a bigger one at a period end); a
phrase that sits well outside what the section has been doing — louder,
busier, an octave away, a modulation, not merely a chord held for four bars
— is a new section and opens with an accent; the chord is named every beat
and the rhythm of chord changes is learned and predicted, so a beat where
the harmony is about to move gets a kick. A hole in the phrase earns a fill
that answers the pianist's last bar's rhythm rather than a stock one. When
the pianist stops, the kit fades over about a bar — judged against their
own typical spacing, so someone padding whole notes is a style, not an
ending. Accents (velocity, bass depth, bass harmony changes) also feed
downbeat inference, which is what puts the backbeat on the pianist's 2 and
4. The bass is whatever drops under the register the hands were just in —
a left hand in F is the bass at F3 — not a note below a fixed line; the
first note of a stretch of playing is taken as beat 1, because that is how
people come in; and after that the bar only moves when another beat wins
the accent contest several bars running, a contest every bar gets to hold
however gently it was played. The status line shows the drummer's mind: `act=`, `sec=`,
`phr=`, `chord=`, `key=`, `swing=`. `--groove classic` brings back the
three fixed patterns; `--no-follow` and `--no-downbeat` switch the
listening off.

The knobs. `--decoration 0..1` is how much optional playing goes around the
beat — 0 is the plain beat (kick on one, snare on the backbeat, nothing
else), 1 is everything the pianist's activity can buy, and the default is
0.5 because a steady beat with riffs between is what most people mean by
drums. `--riffs phrase|period|none` is where the fills go: every phrase end
with a bigger one at a period end, only period ends, or nowhere but the
`fill` command. `--mutation 0..1` is how much of the optional playing is
re-rolled each bar (0 repeats the bar). `--min-gap-ms` keeps one drum from
being asked for two hits closer than that, for hardware that can do 50 ms
but not well. `--hold 0..1` is how firmly the beat stays put against pushes
and stray notes (0 follows every onset; try 0.5 if the beat gets shoved).
While playing, `decor 0.3` and `riffs period` change the first two on the
fly, and a hole in the playing is only answered with a fill once it is
clearly a hole — a beat and a half beyond the pianist's usual spacing, or
half a bar — so a fumble is not a cue.

Meters other than 4/4 get real patterns, not a 4/4 grid cycled round. A bar
is described by how its beats clump — `--meter 5 --grouping 3+2` is Take
Five, `2+3` is the other 5/4, `--meter 7` defaults to 4+3 — and the groove
rules (a kick opens every group, the snare answers inside it, the modes add
their pushes and ghosts around those snares) are the same ones that produce
the 4/4 patterns, which the tests hold byte for byte against the original
hand-tuned tables.

    uv run tutti jam --fake --fake-meter 3 --meter auto

`--meter auto` infers the meter from the playing. The listener's accents are
scored against strong-beat templates for every candidate bar length and
grouping at every offset, over the last few dozen beats; the declared meter
is the incumbent and only gives way when a challenger beats it clearly on
three consecutive bar lines. Expect a waltz to be recognised within about
ten seconds of locking. `--fake-meter` makes the fake pianist play in a
different meter from the one declared, so you can watch it happen.

Tempo is read from the whole recent pattern of onsets, not from the gaps
between neighbours. Candidate periods are scored on how many onsets sit on
their grid (a period twice the true one strands every other beat), how much
of their grid gets visited (a period half the true one has points nobody
plays), and a prior for where the beat usually lives. That is what lets
swing read as the beat rather than the long eighth, and eighth-note comping
at 80 read as 80 rather than 160. The runners-up stay alive (`alt=` in the
status line) and the tracker changes its mind only when one of them keeps
winning while the grid has stopped fitting; a ritardando bends the grid
instead (`rit=+8%`), following the playing without retuning the band. Note
the deliberate asymmetry: eighths at 80 and quarters at 160 are the *same*
onset pattern, so something has to choose, and a half-time feel on a fast
tune is musical where double-time drums on a ballad are not. Tunes above
about 150 BPM therefore read as half time unless `--preferred-bpm` says
otherwise (`--fake 160 --preferred-bpm 150` to hear the difference). The
range considered is 50 to 180 BPM (`--bpm-range`); the first real session
was a 66 BPM ballad, which the original 70 floor could not even see.

For a song you know the tempo of, say so:

    uv run tutti jam --input-port Piano --tempo 72

A declared tempo turns the tracker from a listener discovering the beat
into a drummer who knows the song. Two gaps at the tempo are a count-in and
the kit is in — no bars of evidence needed; the prior narrows around the
tempo so the reading never wanders to double or half time; the drums still
follow you around it (play at 80 and it reads 80, slow down and it comes
with you), and they keep time through rests for about two bars before
fading, instead of giving up at the first pause. This is the mode for
playing a piece with rests, fermatas and rubato rather than jamming.

Add `--record session.jsonl` to keep every note of a session, and
`uv run tutti replay session.jsonl` to run it back through the tracker in a
fraction of a second with a second-by-second account of what it believed.
Real hands are the only evidence that counts: `tests/sessions/` holds
recorded P-45 sessions as regression fixtures, each stating what was played
and what a listening drummer should have done with it.

Type `+`/`-` for intensity, `mode busy`, `fill`, `mute`, `status`, or `quit`
(then Enter) while it runs. While following, `+`/`-` becomes a standing
offset over the automatic level and a chosen mode pins until `mode auto`.
`--transport midi --midi-port RobOrchestra` sends the same groove to real
bots instead of the speakers.

## Conducting

    uv sync --extra gesture --extra audio
    uv run tutti conduct scores/Route1.json

Beat time at the webcam and the piece plays at your tempo. Count in four
strokes and it starts on the fifth; speed up and it follows; stop, and it
holds on the next beat until you move again; conduct bigger and it plays
louder. When the piece ends, the next count-in starts it over. A closed
fist mutes the kit, an open palm brings it back.

    uv run tutti conduct --improv

is the old InteractiveDemo, ported: a xylophone melody random-walking
through a scale over snare and tom patterns that fire by probability, the
sketch's own tables and its own rule for the walk. Two strokes set the tempo
and it plays for as long as you conduct. `--scale blues --key A` picks the
scale, `--xylo 0.3` and friends set the densities, and `xylo 0.3`, `scale
dorian`, `key F#` change them while it runs.

The old demo counted beats over a three-second window and turned the count
into a BPM, which is a tempo but not a phase: the notes never knew which
beat they were on. Here every stroke is a numbered beat. The clock predicts
one beat past your last stroke, which is how the notes *on* the next beat
get scheduled while your hand is still coming down (the detector fires
early and says when it expects the hand to land), and nothing beyond that
is predicted at all, which is why the orchestra stops when you do. A stroke
inside half a beat of the last is the camera seeing one gesture twice and
is ignored; a stroke about two beats out is one the camera missed, and the
count jumps so the orchestra stays with you rather than a beat behind.

Beats can also come from the Enter key (or the space bar in the preview
window), from any note on a MIDI pad with `--tap-port`, or from a built-in
metronome with `--fake 120` for hearing the whole thing with no camera and
nobody waving. `--no-camera` skips the webcam. `--coast 1` lets the
orchestra run one more beat past your last stroke before holding, for a
camera that drops the occasional stroke. `--beat-unit 2` conducts a fast 4/4
in two. A pickup lands inside the count-in and the first downbeat is the
first beat after it; `--offset-beats` overrides that.

More pieces to conduct: `scores/MistyMountainsCold.json`,
`scores/EyeOfTheTiger.json`, `scores/AxelF.json` and
`scores/NextEpisode.json`, the last two xylophone only.

## Measuring a bot's latency

    uv run tutti latency --transport midi --midi-port RobOrchestra_Snare

`mech_latency_ms` in `fleet.py` has always been a guess. This strikes the bot
a dozen times at known instants, listens on the microphone, finds the
acoustic onsets, and reports how far behind the intended time each landed:
median, spread, misses. Whatever is left over after what the fleet already
compensates is the number to write into `fleet.py`; a large spread is
`mech_jitter_ms`, worth recording too. The probe reports how far the hits
stood above the room and refuses to hand over a number when that is under
20 dB, because a bad recording reads its own noise as hits. Put the
microphone at the drum: a laptop listening to its own speakers
(`--transport loopback`) gets about 10 dB on a MacBook and is only good for
checking that the tool runs, not for a measurement. `--list-inputs` shows
the microphones; `--input-device` picks one.

## Live sources and the ensemble

Score playback plans the whole future; a camera cannot. Live sources call
`Ensemble.strike(note)`, which runs the planner's inner loop one strike at a
time on the same BotState objects: route to a bot that accepts the note,
nudge within tolerance, fall back to another bot, or drop with a reason.
However many sources are running, a bot has one view of its voices, so two
sources cannot overdrive one drum.

Transports answer one extra question for live use: `live_lead_s(bot_id)`, the
earliest honest play_at for a strike requested now. For loopback that is a few
audio blocks; for the old daisy chain it is one mechanical travel, not the
250ms batch planning window, which would otherwise become pure lag.

## Two ways to talk to bots over MIDI

| flag | for |
|---|---|
| `--transport midi` | bots that already speak General MIDI, which is every ESP32 bot |
| `--transport legacy` | the old Arduino boards, which need note numbers translated |

The ESP32 firmware triggers on GM notes directly, so it needs no translation
and gets velocity passed through. The old boards do: `snarebot_servo_midi.ino`
fires on note 36, which in General MIDI is the bass drum.

One stage can be several ports. Each ESP32 bot is its own Bluetooth MIDI
port on macOS, and Xylobot hangs off a USB adapter, so `--midi-port` opens
every port matching the name and may be repeated:

    uv run tutti conduct scores/Route1.json --transport midi \
        --midi-port RobOrchestra --midi-port "USB MIDI"

A hit goes to the ports whose name mentions its bot's role (the snare's to
`RobOrchestra_Snare`) and otherwise to all of them, which is safe because
every board ignores notes that are not its own. With `--transport midi` a
legacy board sharing the stage still gets its old note numbers on its old
channel; the xylophone on the Arduino and the two Bluetooth drums are one
transport.

## Driving the existing robots

    uv run tutti ports
    uv run tutti play scores/Route1.json --transport legacy --midi-port USB-MIDI

Sends plain MIDI down the Arduino daisy chain that already exists. No firmware
changes. The old bots have no clock and no buffer, so everything the design
normally pushes down to the bot happens here instead: the transport holds each
hit until it is time, subtracts that bot's mechanical latency itself, and
translates General MIDI note numbers into whatever each board was flashed to
listen for.

That translation is the point. `snarebot_servo_midi.ino` fires on note 36,
which in General MIDI is the bass drum, and the snare is 38. Scores stay in GM
and old boards keep working, with no reflashing and no folklore.

Ports are matched by name, never by index. `new MidiBus(this, 0, 3)` picks a
different device depending on the laptop and the order things were plugged in,
which is most of what the wiki's Debugging page is about. Run `tutti ports` to
see the names.

Measured over a virtual MIDI bus, 24 hits at 125 ms spacing:

| | |
|---|---|
| inter-onset gap | 125.01 ms against a wanted 125.00 |
| jitter | 0.49 ms standard deviation |
| hits sent late | 0 |

For comparison, the Processing sketches quantise to the frame at 60 fps, so
0 to 16.7 ms, and then add about 4 ms of deliberate skew with two `delay(2)`
calls. Real hardware will be worse than the figures above, because a USB host
stack and DIN serialisation sit between this and the drum, but the scheduling
half is no longer the problem.

## Actuator models

`src/tutti/core/fleet.py` holds one model per bot, with every number taken from
the firmware. Two kinds of instrument:

- **pooled**: any free voice plays any accepted note, like a drum with two sticks.
  The floor is `cycle_ms / voices`.
- **keyed**: the note picks the voice, like one solenoid per xylophone key.
  Different keys are independent, so the floor is per key.

That distinction matters more than it looks. On a dense arrangement the drums
are usually fine, because two sticks alternate, and the xylophone is the
bottleneck, because a repeated note has to wait for the same solenoid.

`mech_latency_ms` is the one figure nobody has measured. Until someone puts a
piezo on a drum head and records a couple of hundred hits, those are estimates.

## Score manifests

A manifest sits next to a MIDI file and says which track and channel belong to which
part. This replaces guessing from note numbers.

    {
      "song": "Route1",
      "midi": "../../Software/Songs/Route1.mid",
      "parts": [
        {"part_id": 1, "role": "xylo",  "track": 1, "note_range": [60, 76], "fold_octaves": true},
        {"part_id": 2, "role": "snare", "track": 2, "notes": [38]},
        {"part_id": 3, "role": "bass",  "track": 3, "notes": [35, 36]}
      ]
    }

Part fields:

| field | meaning |
|---|---|
| `part_id` | how the rest of the system refers to this line |
| `role` | what kind of instrument should play it, bound to a bot at run time |
| `track` | MIDI track index, optional |
| `channel` | MIDI channel 0-15, optional |
| `notes` | explicit list of accepted notes |
| `note_range` | inclusive low and high note |
| `fold_octaves` | move out-of-range notes into range by octaves, as Xylobot does |
| `transpose` | semitones, applied before folding |

Parts are tried in order and the first match wins. Notes no part claims are counted and
reported rather than dropped silently.

Note numbers follow General MIDI percussion: 35/36 bass drum, 38 snare, 41-50 toms.

## Layout

    src/tutti/core/        score, plan, fleet, report, player, beat, tempo, listen, meter,
                           phrase, harmony, generate, groove, latency, conduct, improv
    src/tutti/transports/  base interface, loopback, synth, legacy_din
    src/tutti/sources/     things that produce notes or tempo: gesture, baton, jam, conduct
    scores/                score manifests
    tests/

Two rules hold the layers apart:

- The player never decides when a note sounds. It only decides when to hand the
  note over, early enough that whatever is downstream can place it itself.
- Whatever makes the sound owns the clock. The player reads the transport's
  clock where it has one, because a sound card and the wall clock drift apart
  over a few minutes.

That split is why the same code will drive the speakers, the old daisy chain,
and eventually the bots over wifi.
