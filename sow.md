# Solar System Simulation — Favur Visual Test

## Overview
Build an accurate, interactive 2D model of the solar system in Pygame. Bodies move on real elliptical orbits derived from published orbital elements and Kepler's laws, the Sun anchored at the shared focus. The app is scene-managed, every orbiting body leaves a fading trail, and pressing `SPACE` reverses the direction of simulation time so the whole system runs backward.

The model must be **deterministic**: every body's position is a pure function of simulation time, so the simulation is exactly reproducible and unit-testable. Accuracy is defined precisely by the method below, not by visual approximation.

## The Model
Implement the **heliocentric two-body Keplerian model**.

### Orbital motion
- Each orbit is an ellipse with its primary at one focus (Kepler's 1st law). Mean anomaly advances linearly with simulation time, `M = 2π·t/T`.
- Recover the eccentric anomaly `E` from `M = E − e·sin(E)` by **Newton–Raphson** to a configurable tolerance, convert to true anomaly, and compute the radius `r = a(1 − e·cos E)`.
- Position is exposed as `state_at(t)` — a pure function of simulation time — so motion can run forward or backward and is fully reproducible.

### Reference frames
A body may orbit the central star, **or it may orbit another body.** Positions compose by frame: a body's absolute position is its primary's position plus its own orbital offset relative to that primary. The same Kepler solver serves at every level of the hierarchy; only the parent frame changes.

### Populated regions
Some regions of the system are occupied by many small bodies rather than a single one. Such a region is generated **procedurally from a fixed seed**: each member is a real Keplerian body whose elements are sampled across the region's stated range, with the region's documented internal structure (density variations, depletions) reproduced by the sampling. Seeded generation keeps the result deterministic and reproducible.

### Simulation clock
Time is a controllable simulation clock (days per real second), never wall-clock. The clock supports a direction (+1 / −1) and an adjustable rate. The model layer contains **no Pygame import** so it can be exercised headlessly.

## Requirements

### Functional Requirements
- A single window with a deterministic title and fixed size renders the solar system: the central star, the bodies in orbit around it, and any bodies in orbit around those.
- Each orbiting body leaves a fading trail backed by a fixed-capacity ring buffer of recent positions.
- `SPACE` reverses the direction of simulation time.
- `P` toggles pause (time freezes; rendering continues).
- `+` / `-` raise and lower the simulation rate, clamped to sane bounds.
- A scene state machine manages Title → Simulation → Paused; events dispatch to the active scene.
- `Escape` on any scene closes the window gracefully.

### Technical Requirements
- Python 3.11+
- Pygame 2.x (only external runtime dependency)
- Window title: exactly `Favur Visual Test`
- Window size: 1440×1080, non-resizable
- The model layer is deterministic and free of any Pygame import.

### Display Scaling
The system spans roughly five orders of magnitude in both orbital distance and body size — at a literal common scale the widest orbits leave the view while the smallest bodies fall below a single pixel, so a "close to scale" view must be **logarithmically compressed**. To keep bodies resolvable at *every* level of the system, apply that compression **hierarchically, within each body's own reference frame**:

- **Distance — logarithmic, per reference frame.** A body's orbital semi-major axis is mapped through `log` *within the frame of its primary*, and the orbit is drawn as a *true ellipse* at that mapped size using its real eccentricity — so orbit **shape stays exact** while spacing is compressed. A body orbiting the central star is scaled in the star's frame; a body orbiting another body is scaled in *that body's* frame. Orbits at any depth in the hierarchy thus become resolvable regardless of their physical scale.
- **Bounded neighborhoods.** Each body is allocated a display neighborhood whose radius is capped so it cannot overlap neighboring orbits (the display analog of a sphere of influence). Anything orbiting within that neighborhood is scaled to fit inside it, so local sub-systems remain legible and self-contained.
- **Size — one shared logarithmic law, clamped.** Every body's physical radius is mapped through a single `log` function onto a clamped `[min, max]` pixel range, so the largest body fits the view and the smallest still renders as a visible disk.

All mappings are strictly monotonic: a larger true value always yields a larger-or-equal screen value. Distances and sizes are not to literal scale, but ordering, orbit geometry, and rough log-proportionality are preserved at every level. The viewport may optionally support zoom to move continuously between scale regimes. Document the scaling regime and its limits in the README.

## Solar System Reference Data
Authoritative J2000-epoch reference values. `a` = semi-major axis, `e` = eccentricity, `T` = orbital period, radius = mean physical radius. For bodies orbiting a primary other than the Sun, `a` is given as distance from that primary.

Central star — Sun: radius 696,340 km.

**Bodies orbiting the Sun**

| Body    | a (AU) | e      | T (yr) | radius (km) |
|---------|--------|--------|--------|-------------|
| Mercury | 0.387  | 0.2056 | 0.241  | 2,440       |
| Venus   | 0.723  | 0.0068 | 0.615  | 6,052       |
| Earth   | 1.000  | 0.0167 | 1.000  | 6,371       |
| Mars    | 1.524  | 0.0934 | 1.881  | 3,390       |
| Jupiter | 5.203  | 0.0484 | 11.86  | 69,911      |
| Saturn  | 9.537  | 0.0539 | 29.45  | 58,232      |
| Uranus  | 19.19  | 0.0473 | 84.02  | 25,362      |
| Neptune | 30.07  | 0.0086 | 164.8  | 24,622      |

**Bodies orbiting a primary**

| Body     | Primary | a (km)    | e        | T (days)      | radius (km) |
|----------|---------|-----------|----------|---------------|-------------|
| Moon     | Earth   | 384,400   | 0.0549   | 27.32         | 1,737       |
| Io       | Jupiter | 421,700   | 0.0041   | 1.77          | 1,822       |
| Europa   | Jupiter | 671,000   | 0.0094   | 3.55          | 1,561       |
| Ganymede | Jupiter | 1,070,000 | 0.0013   | 7.15          | 2,634       |
| Callisto | Jupiter | 1,883,000 | 0.0074   | 16.69         | 2,410       |
| Titan    | Saturn  | 1,222,000 | 0.0288   | 15.95         | 2,575       |
| Phobos   | Mars    | 9,376     | 0.0151   | 0.319         | 11          |
| Deimos   | Mars    | 23,460    | 0.0002   | 1.26          | 6           |
| Triton   | Neptune | 354,800   | 0.000016 | 5.88 (retro.) | 1,353       |

**Minor bodies**

| Body   | a (AU) | e      | T (yr) | radius (km) |
|--------|--------|--------|--------|-------------|
| Ceres  | 2.77   | 0.0758 | 4.60   | 473         |
| Vesta  | 2.36   | 0.0887 | 3.63   | 263         |
| Pallas | 2.77   | 0.2306 | 4.62   | 256         |
| Hygiea | 3.14   | 0.1125 | 5.56   | 217         |

**Long-period / high-eccentricity bodies**

| Body         | a (AU) | e     | T (yr) | radius (km) |
|--------------|--------|-------|--------|-------------|
| 1P/Halley    | 17.8   | 0.967 | 75.3   | 5.5         |
| 2P/Encke     | 2.22   | 0.848 | 3.30   | 2.4         |
| Hale–Bopp    | 186    | 0.995 | 2,533  | 30          |

**Main-belt distribution (reference).** The principal minor-body region occupies roughly **2.1–3.3 AU**. Its density is not uniform: it is depleted at orbital-resonance locations with Jupiter (the Kirkwood gaps), with notable depletions near **2.50 AU (3:1)**, **2.82 AU (5:2)**, **2.96 AU (7:3)**, and **3.27 AU (2:1)**. Eccentricities are typically modest (≈0.05–0.30) and longitudes are distributed around the full circle.

## Project Structure
```
├── src/
│   ├── __init__.py
│   ├── vector.py        # Vec2 value type and 2D math
│   ├── orbital.py       # Kepler equation solver + anomaly conversions
│   ├── frames.py        # reference-frame composition (primary + relative offset)
│   ├── bodies.py        # body definitions sourced from the reference data
│   ├── trail.py         # fixed-capacity ring-buffer trail with alpha decay
│   ├── simulation.py    # deterministic model: state_at(t), direction, rate
│   ├── scaling.py       # hierarchical logarithmic display scaling (distance + size)
│   ├── scenes.py        # Scene base, Title/Simulation/Paused, SceneManager (FSM)
│   ├── render.py        # draws background, bodies, orbit paths, trails
│   └── main.py          # Pygame init, window, loop, event dispatch, Escape-to-quit
├── tests/
│   ├── __init__.py
│   ├── test_vector.py
│   ├── test_orbital.py      # solver, third law, perihelion/aphelion, equal-area
│   ├── test_frames.py       # frame composition correctness
│   ├── test_trail.py        # ring-buffer capacity and eviction order
│   ├── test_simulation.py   # determinism, time reversal
│   ├── test_scaling.py      # monotonicity, bounds, viewport containment
│   └── test_scenes.py       # FSM transitions
├── pyproject.toml
└── README.md
```

## Implementation Details
- `src/vector.py`: Immutable `Vec2` with add, subtract, scalar multiply, magnitude, rotation, and equality.
- `src/orbital.py`: Newton–Raphson solver for `M = E − e·sin(E)`, anomaly conversions, and the heliocentric `(x, y)` of a body given its elements and mean anomaly. No rendering.
- `src/frames.py`: Composes a body's absolute position from its primary's position and its own orbital offset, supporting bodies that orbit the star and bodies that orbit another body.
- `src/bodies.py`: Body definitions (name, color, physical radius, orbital elements, primary) built from the reference data.
- `src/trail.py`: Fixed-capacity ring buffer of recent positions; oldest-first eviction; per-point alpha decaying with age.
- `src/simulation.py`: Owns the simulation clock, direction, and rate; exposes `state_at(t)` as a pure function of simulation time. No Pygame import.
- `src/scaling.py`: The logarithmic display mappings — distance applied within each body's reference frame with bounded, non-overlapping display neighborhoods, and size via a single shared clamped law. Monotonic throughout.
- `src/render.py`: Draws the black background, the central star, each body, its faint orbit path, and its fading trail, applying the scaling.
- `src/scenes.py`: `Scene` base plus `TitleScene`, `SimulationScene`, `PausedScene`, coordinated by a `SceneManager` finite state machine.
- `src/main.py`: Initializes Pygame, creates the 1440×1080 window with the exact title, runs the loop, dispatches events through the `SceneManager`, and handles `SPACE`, `P`, `+`/`-`, and the global `Escape`-to-quit.
- `README.md`: Title, overview, the accuracy model, the scaling choice, installation, run instructions, and the keyboard interactions.

## Visual Layout Requirements
- Black background (space) with the central star rendered at the shared focus.
- Orbiting bodies of differing sizes and colors, each on a visibly elliptical path, sized per the display-scaling method (larger physical bodies render larger).
- Each orbit's ellipse drawn faintly, with a fading trail tracing the actual path.
- All rendered content remains within the 1440×1080 viewport.

## Acceptance Criteria
1. The project is generated with the specified file structure.
2. The window opens with the exact title `Favur Visual Test` at 1440×1080 and is not resizable.
3. Pressing `SPACE` reverses the direction of simulation time, reversing all motion.
4. `P` toggles pause; `Escape` on any scene closes the window without errors.
5. The Kepler solver satisfies `M = E − e·sin(E)` within 1e−9 across the full range of mean anomaly.
6. Kepler's third law holds across the modeled bodies: `T² ∝ a³` within 1% tolerance.
7. Computed perihelion and aphelion distances match `a(1 − e)` and `a(1 + e)` within tolerance.
8. Kepler's second law is verified numerically: equal areas are swept in equal simulation-time intervals within tolerance.
9. The trail ring buffer respects its fixed capacity and evicts oldest-first.
10. The display scaling is strictly monotonic in both distance and size, and all rendered content stays within the viewport.
11. The scene state machine transitions correctly between Title, Simulation, and Paused.
12. The simulation is deterministic: `state_at(t)` is reproducible, and reversing time twice returns every body to its original trajectory.
13. `poetry run pytest` passes with 0 failures — mandatory.
14. `poetry run python -m src.main` launches the simulation.
15. Visual proof tested and verified using screenshots and key presses.