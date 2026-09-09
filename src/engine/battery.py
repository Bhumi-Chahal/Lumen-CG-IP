"""engine/battery.py — Battery/Energy resource and Lantern Meter HUD widget (Level 2+). 
 
Per architecture.md §3, rules.md §1.4, and design.md §6: 
----------------------------------------------------------------------------- 
DESIGN SPECIFICATION FOR LEVEL 2 (DO NOT BUILD INVERTED): 
- In Level 1, the tutorial does NOT include battery or energy limits (design.md §5). 
- In Level 2, energy is introduced as a 0-100 resource (rules.md §1.4). 
- RULE: Energy drains WHILE THE LANTERN IS ACTIVE (light costs energy). 
  When the lantern is toggled OFF, energy does NOT drain. 
- Reaching 0 energy is an independent, mandatory death condition in Level 2 
  (locked design decision — see docs/memory.md session log). It does not 
  merely represent "the Shadow is now at contact range"; it kills the player 
  outright even if the Shadow itself hasn't touched them yet. 
- Energy can be restored to 100% at Energy Crystal stations. There is no 
  passive recharge. 
----------------------------------------------------------------------------- 
""" 
 
import math 
import pygame 
 
 
class BatterySystem: 
    """Manages lantern battery/energy resource for Level 2+. 
 
    Follows rules.md §1.4: 
    - Max energy: 100.0 
    - Drains while the lantern is active. 
    - Recharged at Energy Crystal stations. 
    - Reaching 0 is an independent death condition (checked by the caller 
      via `is_depleted`). 
    """ 
 
    MAX_ENERGY = 100.0 
    ACTIVE_DRAIN_RATE = 2.8      # Energy drained per second while lantern is lit 
    LOW_THRESHOLD = 30.0 
    CRITICAL_THRESHOLD = 10.0 
 
    def __init__(self, drain_rate: float | None = None): 
        self.drain_rate = float(drain_rate) if drain_rate is not None else BatterySystem.ACTIVE_DRAIN_RATE
        self.energy = BatterySystem.MAX_ENERGY 
 
    def update(self, dt: float, is_lantern_active: bool): 
        """Drains energy while the lantern is actively shining. 
 
        Lantern OFF pauses drain entirely (matches the locked design: turning 
        the lantern off is a deliberate tradeoff — you stop losing energy but 
        you also lose almost all visibility and the Shadow keeps closing 
        in based on your last-known battery percentage). 
        """ 
        if is_lantern_active: 
            self.energy = max(0.0, self.energy - self.drain_rate * dt) 
 
    def recharge(self, amount: float = 100.0): 
        """Restores battery energy up to MAX_ENERGY.""" 
        self.energy = min(BatterySystem.MAX_ENERGY, self.energy + amount) 
 
    def reset(self): 
        """Resets energy to full — used on Level 2 death/restart.""" 
        self.energy = BatterySystem.MAX_ENERGY 
 
    @property 
    def ratio(self) -> float: 
        return self.energy / BatterySystem.MAX_ENERGY 
 
    @property 
    def is_low(self) -> bool: 
        return self.energy < BatterySystem.LOW_THRESHOLD 
 
    @property 
    def is_critical(self) -> bool: 
        return self.energy < BatterySystem.CRITICAL_THRESHOLD 
 
    @property 
    def is_depleted(self) -> bool: 
        """True once energy has hit 0 — an independent Level 2 death condition.""" 
        return self.energy <= 0.0 
 
 
class LanternMeter: 
    """Pixel-art lantern energy meter for the Level 2 HUD. 
 
    Deliberately NOT a heart/HP-styled bar (see docs/memory.md — the old 
    EnergyBar read as a health bar and was replaced by locked decision). 
    This widget reads as "how much light is left in the lantern", not 
    "how much health remains": 
 
    - A small brass lantern icon with a flickering flame sits to the left. 
    - The fill is a warm amber "fuel" that recedes as energy drains. 
    - As energy drops below LanternMeter.WARN_RATIO the fill shifts from 
      amber toward orange/red and a soft warning glow pulses around the 
      frame — faster and stronger the closer energy gets to empty. 
    - No crumbling stone, no damage-flash, no heart icon. 
    """ 
 
    WARN_RATIO = 0.30 
    CRITICAL_RATIO = 0.10 
 
    def __init__(self): 
        self.flicker_phase = 0.0 
        self.pulse_phase = 0.0 
 
    def update(self, dt: float, energy_ratio: float): 
        """Advances flame-flicker and warning-pulse animation timers.""" 
        self.flicker_phase = (self.flicker_phase + dt * 9.0) % (2 * math.pi) 
 
        if energy_ratio < LanternMeter.CRITICAL_RATIO: 
            pulse_speed = 9.0 
        elif energy_ratio < LanternMeter.WARN_RATIO: 
            pulse_speed = 5.5 
        else: 
            pulse_speed = 2.5 
        self.pulse_phase = (self.pulse_phase + dt * pulse_speed) % (2 * math.pi) 
 
    def _fill_color(self, ratio: float) -> tuple[int, int, int]: 
        """Amber (healthy) -> orange (warn) -> pulsing red (critical).""" 
        if ratio > LanternMeter.WARN_RATIO: 
            return (235, 175, 70) 
        elif ratio > LanternMeter.CRITICAL_RATIO: 
            t = (ratio - LanternMeter.CRITICAL_RATIO) / (LanternMeter.WARN_RATIO - LanternMeter.CRITICAL_RATIO) 
            return ( 
                int(255 * (1 - t) + 235 * t), 
                int(70 * (1 - t) + 175 * t), 
                int(40 * (1 - t) + 70 * t), 
            ) 
        else: 
            flicker = 0.5 + 0.5 * math.sin(self.pulse_phase) 
            return (255, int(50 + 30 * flicker), int(35 + 15 * flicker)) 
 
    def draw(self, surface: pygame.Surface, x: int, y: int, 
             energy_ratio: float, font_small: pygame.font.Font | None = None): 
        """Draws the lantern meter with its top-left corner at (x, y).""" 
        ratio = max(0.0, min(1.0, energy_ratio)) 
        vial_w, vial_h = 150, 22 
        fill_color = self._fill_color(ratio) 
 
        # --- Small lantern icon (cap + glass body + flame) --- 
        icon_cx, icon_cy = x + 12, y + vial_h // 2 
        pygame.draw.rect(surface, (110, 85, 40), (icon_cx - 7, icon_cy - 9, 14, 4), border_radius=1) 
        pygame.draw.rect(surface, (55, 48, 32), (icon_cx - 6, icon_cy - 5, 12, 12), border_radius=2) 
        flame_alpha = 0.5 + 0.5 * math.sin(self.flicker_phase) 
        flame_color = ( 
            min(255, fill_color[0] + 10), 
            min(255, int(fill_color[1] + 50 * flame_alpha)), 
            fill_color[2], 
        ) 
        pygame.draw.circle(surface, flame_color, (icon_cx, icon_cy + 1), 3) 
 
        # --- Vial frame --- 
        frame_x = x + 30 
        frame_rect = pygame.Rect(frame_x, y, vial_w, vial_h) 
        pygame.draw.rect(surface, (35, 30, 42), frame_rect, border_radius=6) 
        pygame.draw.rect(surface, (90, 78, 55), frame_rect, width=2, border_radius=6) 
 
        # --- Fill --- 
        inner = frame_rect.inflate(-6, -6) 
        fill_w = max(0, int(inner.width * ratio)) 
        if fill_w > 0: 
            fill_surf = pygame.Surface((fill_w, inner.height), pygame.SRCALPHA) 
            fill_surf.fill((*fill_color, 235)) 
            pygame.draw.line(fill_surf, (255, 255, 255, 70), (0, 1), (fill_w, 1), 1) 
            surface.blit(fill_surf, (inner.x, inner.y)) 
 
        # --- Low-energy warning pulse (frame glow, not a bar-fill flash) --- 
        if ratio <= LanternMeter.WARN_RATIO: 
            pulse_alpha = int(60 + 55 * math.sin(self.pulse_phase)) 
            glow = pygame.Surface((frame_rect.width + 12, frame_rect.height + 12), pygame.SRCALPHA) 
            pygame.draw.rect(glow, (255, 60, 40, max(0, pulse_alpha)), 
                             glow.get_rect(), width=3, border_radius=8) 
            surface.blit(glow, (frame_rect.x - 6, frame_rect.y - 6)) 
 
        # --- Percentage label --- 
        if font_small is not None: 
            pct_txt = font_small.render(f"{int(ratio * 100)}%", True, (235, 225, 210)) 
            surface.blit(pct_txt, (frame_rect.right + 8, y + (vial_h - pct_txt.get_height()) // 2)) 
