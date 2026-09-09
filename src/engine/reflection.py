"""engine/reflection.py — Pure, Pygame-independent reflection math for Lumen Level 3.

Implements the locked reflection formula:
    reflected = incoming - 2 * dot(incoming, normal) * normal

Operates on 8 discrete orientation states. Fully deterministic with zero external dependencies.
"""

import math

# Discrete 8-way orientation normals (precomputed to eliminate precision drift)
SQRT2_2 = math.sqrt(2.0) / 2.0

ORIENTATION_NORMALS: list[tuple[float, float]] = [
    (1.0, 0.0),           # 0: 0°   (East)
    (SQRT2_2, SQRT2_2),   # 1: 45°  (South-East)
    (0.0, 1.0),           # 2: 90°  (South)
    (-SQRT2_2, SQRT2_2),  # 3: 135° (South-West)
    (-1.0, 0.0),          # 4: 180° (West)
    (-SQRT2_2, -SQRT2_2), # 5: 225° (North-West)
    (0.0, -1.0),          # 6: 270° (North)
    (SQRT2_2, -SQRT2_2),  # 7: 315° (North-East)
]


def dot_product(v1: tuple[float, float], v2: tuple[float, float]) -> float:
    """Computes the dot product of two 2D vectors."""
    return v1[0] * v2[0] + v1[1] * v2[1]


def normalize_vector(v: tuple[float, float]) -> tuple[float, float]:
    """Normalizes a 2D vector. Returns (0.0, 0.0) if magnitude is 0."""
    mag = math.hypot(v[0], v[1])
    if mag < 1e-9:
        return (0.0, 0.0)
    return (v[0] / mag, v[1] / mag)


def get_orientation_normal(orientation_index: int) -> tuple[float, float]:
    """Returns the unit normal vector for one of the 8 discrete orientation states."""
    return ORIENTATION_NORMALS[orientation_index % 8]


def calculate_reflection(
    incoming_dir: tuple[float, float],
    mirror_normal: tuple[float, float],
) -> tuple[float, float]:
    """Calculates the reflected direction vector using the approved reflection formula:

        reflected = incoming - 2 * dot(incoming, normal) * normal

    Args:
        incoming_dir: Normalized incoming beam velocity/direction (dx, dy).
        mirror_normal: Normalized mirror surface normal vector (nx, ny).

    Returns:
        Normalized, cleanly rounded reflected direction vector (rx, ry).
    """
    in_norm = normalize_vector(incoming_dir)
    n_norm = normalize_vector(mirror_normal)

    dot = dot_product(in_norm, n_norm)

    rx = in_norm[0] - 2.0 * dot * n_norm[0]
    ry = in_norm[1] - 2.0 * dot * n_norm[1]

    # Clean rounding to eliminate floating point imprecisions for cardinal/diagonal directions
    rx = round(rx, 6)
    ry = round(ry, 6)

    # Normalize result
    return normalize_vector((rx, ry))


# ---------------------------------------------------------------------------
# Analytical Ray-Geometry Intersections (pure math, no Pygame dependency)
# ---------------------------------------------------------------------------

class BeamSegment:
    """A single straight segment of a reflected light beam."""

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        direction: tuple[float, float],
        color: str,
        termination_type: str,
        hit_object=None
    ):
        self.start = (float(start[0]), float(start[1]))
        self.end = (float(end[0]), float(end[1]))
        self.direction = normalize_vector(direction)
        self.color = str(color)
        self.termination_type = str(termination_type)  # "wall", "mirror", "crystal", "none"
        self.hit_object = hit_object

    @property
    def length(self) -> float:
        return math.hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])


def ray_intersect_rect(
    origin: tuple[float, float],
    direction: tuple[float, float],
    rect_bounds: tuple[float, float, float, float]
) -> float | None:
    """Analytical ray-AABB slab intersection.

    Args:
        origin: Ray start (ox, oy).
        direction: Normalized direction (dx, dy).
        rect_bounds: (rx, ry, rw, rh).

    Returns:
        Smallest positive distance t > 0.001, or None if no hit.
    """
    ox, oy = origin
    dx, dy = direction
    rx, ry, rw, rh = rect_bounds

    tmin = -float("inf")
    tmax = float("inf")

    # X slab
    if abs(dx) > 1e-9:
        t1 = (rx - ox) / dx
        t2 = (rx + rw - ox) / dx
        tmin = max(tmin, min(t1, t2))
        tmax = min(tmax, max(t1, t2))
    else:
        if ox < rx or ox > rx + rw:
            return None

    # Y slab
    if abs(dy) > 1e-9:
        t1 = (ry - oy) / dy
        t2 = (ry + rh - oy) / dy
        tmin = max(tmin, min(t1, t2))
        tmax = min(tmax, max(t1, t2))
    else:
        if oy < ry or oy > ry + rh:
            return None

    if tmax >= tmin and tmin > 0.001:
        return tmin
    if tmax >= 0.001 and tmin <= 0.001 and tmax <= 1e8:
        # Ray origin inside the rect, hitting exit face
        return tmax
    return None


def ray_intersect_circle(
    origin: tuple[float, float],
    direction: tuple[float, float],
    center: tuple[float, float],
    radius: float
) -> float | None:
    """Analytical ray-circle intersection.

    Returns:
        Smallest positive distance t > 0.001, or None if no hit.
    """
    ox, oy = origin
    dx, dy = direction
    cx, cy = center

    vx = ox - cx
    vy = oy - cy

    b = 2.0 * (dx * vx + dy * vy)
    c = (vx * vx + vy * vy) - radius * radius

    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / 2.0
    t2 = (-b + sqrt_disc) / 2.0

    if t1 > 0.001:
        return t1
    if t2 > 0.001:
        return t2
    return None


def trace_beam(
    origin: tuple[float, float],
    direction: tuple[float, float],
    color: str,
    obstacles: list,
    mirrors: list,
    crystals: list,
    max_bounces: int = 4,
    max_range: float = 2400.0,
) -> list[BeamSegment]:
    """Deterministically traces a light beam through mirrors, obstacles, and crystals.

    Requirements:
    - Maximum 3 mirror bounces (internal limit, max 4 segments).
    - Color remains completely unchanged through every bounce.
    - Deterministic output for identical inputs.
    - Termination types: "wall", "mirror", "crystal", "none".

    Args:
        origin: Starting point (x, y).
        direction: Emission vector (dx, dy).
        color: Beam color ("white", "red", "blue", "green").
        obstacles: Wall/pillar Rects or (x, y, w, h) bounds.
        mirrors: Mirror entities.
        crystals: PuzzleCrystal entities.
        max_bounces: Maximum allowed mirror reflections (default 3).
        max_range: Maximum single-segment distance (default 2400.0).

    Returns:
        List of BeamSegment instances representing the beam path.
    """
    segments: list[BeamSegment] = []
    curr_origin = (float(origin[0]), float(origin[1]))
    curr_dir = normalize_vector(direction)
    ignore_mirror = None

    for _ in range(max_bounces + 1):
        closest_t = max_range
        hit_type = "none"
        hit_obj = None

        # 1. Obstacles / Walls
        for obs in obstacles:
            if hasattr(obs, "x"):
                bounds = (float(obs.x), float(obs.y), float(obs.width), float(obs.height))
            else:
                bounds = (float(obs[0]), float(obs[1]), float(obs[2]), float(obs[3]))
            t = ray_intersect_rect(curr_origin, curr_dir, bounds)
            if t is not None and 0.001 < t < closest_t:
                closest_t = t
                hit_type = "wall"
                hit_obj = obs

        # 2. Puzzle Crystals
        for crystal in crystals:
            t = ray_intersect_circle(
                curr_origin, curr_dir,
                (crystal.x, crystal.y),
                getattr(crystal, "radius", 24.0)
            )
            if t is not None and 0.001 < t < closest_t:
                closest_t = t
                hit_type = "crystal"
                hit_obj = crystal

        # 3. Mirrors (if bounce limit not exceeded on this step)
        if len(segments) < max_bounces:
            for mirror in mirrors:
                if mirror is ignore_mirror:
                    continue
                t = ray_intersect_circle(
                    curr_origin, curr_dir,
                    (mirror.x, mirror.y),
                    getattr(mirror, "radius", 24.0)
                )
                if t is not None and 0.001 < t < closest_t:
                    closest_t = t
                    hit_type = "mirror"
                    hit_obj = mirror

        # Construct segment
        end_pt = (
            curr_origin[0] + curr_dir[0] * closest_t,
            curr_origin[1] + curr_dir[1] * closest_t
        )
        segment = BeamSegment(
            start=curr_origin,
            end=end_pt,
            direction=curr_dir,
            color=color,
            termination_type=hit_type,
            hit_object=hit_obj
        )
        segments.append(segment)

        # Handle reflection if mirror was hit
        if hit_type == "mirror" and hit_obj is not None:
            new_dir = hit_obj.reflect_beam(curr_dir)
            curr_dir = new_dir
            if getattr(hit_obj, "refractor_color", None):
                color = hit_obj.refractor_color
            # Nudge origin forward slightly along reflected direction to avoid self-collision
            curr_origin = (end_pt[0] + curr_dir[0] * 1.0, end_pt[1] + curr_dir[1] * 1.0)
            ignore_mirror = hit_obj
        else:
            # Beam terminated at wall, crystal, or max range
            break

    return segments


def trace_multiple_beams(
    emitters: list,
    obstacles: list,
    mirrors: list,
    crystals: list,
    default_color: str = "white",
    max_bounces: int = 4,
    max_range: float = 2400.0,
) -> list[list[BeamSegment]]:
    """Deterministically traces multiple independent beam chains.

    Each emitter is a dictionary or object with:
        - 'x', 'y' (or 'origin'): starting point
        - 'dir' (or 'direction'): emission direction vector
        - optional 'color': str (overrides default_color if present)
        - optional 'active': bool (defaults to True)

    Each ray is an independent beam chain:
        - starts at its source
        - travels until wall/mirror/crystal/maximum bounce
        - reflects only when it hits a mirror
        - terminates when it hits a wall or crystal
        - cannot pass through a crystal or wall
        - no beam splitting

    Returns:
        List of beam segment chains (list[list[BeamSegment]]).
    """
    chains: list[list[BeamSegment]] = []
    for emitter in emitters:
        if isinstance(emitter, dict):
            if not emitter.get("active", True):
                continue
            ox = float(emitter.get("x", emitter.get("origin", (0.0, 0.0))[0]))
            oy = float(emitter.get("y", emitter.get("origin", (0.0, 0.0))[1]))
            direction = emitter.get("dir", emitter.get("direction", (0.0, -1.0)))
            col = emitter.get("color", default_color)
        else:
            if not getattr(emitter, "active", True):
                continue
            ox = float(getattr(emitter, "x", 0.0))
            oy = float(getattr(emitter, "y", 0.0))
            direction = getattr(emitter, "dir", getattr(emitter, "direction", (0.0, -1.0)))
            col = getattr(emitter, "color", default_color)

        chain = trace_beam(
            origin=(ox, oy),
            direction=direction,
            color=col,
            obstacles=obstacles,
            mirrors=mirrors,
            crystals=crystals,
            max_bounces=max_bounces,
            max_range=max_range,
        )
        chains.append(chain)

    return chains

