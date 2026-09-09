"""Wall/obstacle collision resolution for the Level 1 prototype (FR-002).

Movement is resolved one axis at a time so the player slides along walls
instead of getting stuck when moving diagonally into a corner.
"""

import pygame


def move_with_collision(player, dx: float, dy: float, walls: list[pygame.Rect], dt: float,
                        jumpable_gaps: list = None):
    """Moves the player by (dx, dy) * speed * dt, blocked by any rect in walls.

    If player.is_jumping is True, obstacles explicitly specified in jumpable_gaps
    are temporarily ignored, allowing the player to hop across specifically designated
    decorative terrain gaps.
    All other obstacles (normal walls, pillars, doors, clues) remain fully solid.
    """
    move_x = dx * player.speed * dt
    move_y = dy * player.speed * dt

    # Normalize jumpable_gaps to a list of pygame.Rect objects
    gap_rects = []
    if jumpable_gaps:
        for g in jumpable_gaps:
            if hasattr(g, "rect"):
                if g.rect not in gap_rects:
                    gap_rects.append(g.rect)
            elif isinstance(g, pygame.Rect):
                if g not in gap_rects:
                    gap_rects.append(g)

    # Filter active walls: if jumping, ignore explicitly flagged jumpable gaps
    if getattr(player, "is_jumping", False) and gap_rects:
        active_walls = [w for w in walls if w not in gap_rects]
    else:
        active_walls = list(walls)
        for gr in gap_rects:
            if gr not in active_walls:
                active_walls.append(gr)

    # Resolve X axis
    player.x += move_x
    player_rect = player.rect
    for wall in active_walls:
        if player_rect.colliderect(wall):
            if move_x > 0:
                player.x = wall.left - player.width
            elif move_x < 0:
                player.x = wall.right
            player_rect = player.rect

    # Resolve Y axis
    player.y += move_y
    player_rect = player.rect
    for wall in active_walls:
        if player_rect.colliderect(wall):
            if move_y > 0:
                player.y = wall.top - player.height
            elif move_y < 0:
                player.y = wall.bottom
            player_rect = player.rect
