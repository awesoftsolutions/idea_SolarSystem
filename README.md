# solar

Build an accurate, interactive 2D model of the solar system in Pygame. Bodies move on real elliptical orbits derived from published orbital elements and Kepler's laws, with the Sun anchored at the shared focus.

## Accuracy Model

The simulation implements a **heliocentric two-body Keplerian model**.

- **Kepler's 1st Law**: Each orbit is an ellipse with its primary at one focus.
- **Kepler's 2nd Law**: Equal areas are swept in equal simulation-time intervals.
- **Kepler's 3rd Law**: $T^2 \propto a^3$ holds across all modeled bodies.
- **Newton–Raphson Solver**: The transcendental Kepler equation $M = E - e \sin E$ is solved to a tolerance of $10^{-9}$ across the full range of mean anomaly.
- **Determinism**: Every body's position is a pure function of simulation time ($state\_at(t)$), ensuring perfect reproducibility and bidirectional time flow.

## Scaling Regime

To keep bodies resolvable at every level of the system (spanning five orders of magnitude), a **hierarchical logarithmic scaling** system is applied:

- **Distance — Logarithmic, Per Reference Frame**: A body's orbital semi-major axis is mapped through a `log` function *within the frame of its primary*. Orbit shapes stay exact (true ellipses) while spacing is compressed.
- **Bounded Neighborhoods**: Each body is allocated a display neighborhood whose radius is capped to prevent overlap with neighboring orbits, keeping local sub-systems (like moons) legible.
- **Size — Shared Logarithmic Law**: Every body's physical radius is mapped through a single `log` function onto a clamped $[2.0, 50.0]$ pixel range.

## Installation

1. Ensure Python 3.11+ is installed.
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Run Instructions

Launch the simulation from the root directory:
```bash
poetry run python -m src.main
```

To run the full test suite:
```bash
poetry run pytest
```

## Keyboard Interactions

- `SPACE`: Reverse the direction of simulation time.
- `P`: Toggle pause (freezes time; rendering continues).
- `+` / `-`: Raise and lower the simulation rate.
- `F`: Toggle predictive orbit previews.
- `D`: Toggle diagnostics overlay.
- `Escape`: Close the window gracefully.


# Favur Recording

[![Watch the demo](https://img.youtube.com/vi/tmjwE6Ax8Sc/maxresdefault.jpg)](https://www.youtube.com/watch?v=tmjwE6Ax8Sc)