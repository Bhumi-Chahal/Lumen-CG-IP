"""Procedural Level 1 effects, with a silent fallback when audio is unavailable."""
import math
import struct
import pygame
SAMPLE_RATE=22050
class AudioManager:
    def __init__(self):
        self.enabled=False
        self.sounds={}
        self._init_audio()
    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():pygame.mixer.init(frequency=SAMPLE_RATE,size=-16,channels=1,buffer=512)
            self.enabled=True
            self._generate_sounds()
        except pygame.error:
            self.enabled=False

    def _build_sound(self, samples: list[float]) -> pygame.mixer.Sound | None:
        """Converts floating point samples (-1.0 to 1.0) into a 16-bit mono Sound."""
        if not self.enabled:
            return None
        try:
            raw_bytes = bytearray()
            for s in samples:
                val = max(-32767, min(32767, int(s * 32767)))
                raw_bytes.extend(struct.pack("<h", val))
            return pygame.mixer.Sound(buffer=raw_bytes)
        except Exception:
            return None

    def _generate_sounds(self):
        # 1. Footstep (soft low stone friction tap)
        duration = 0.08
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            env = (1.0 - (i / n_samples)) ** 2
            # low frequency thud with noise
            tone = math.sin(2 * math.pi * 90 * t) * 0.6
            noise = ((i * 37) % 100 / 50.0 - 1.0) * 0.4
            samples.append((tone + noise) * env * 0.25)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["footstep"] = snd

        # 2. Lantern toggle (click + flame resonance)
        duration = 0.18
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 18)
            freq = 520 - t * 1200
            tone = math.sin(2 * math.pi * max(80, freq) * t)
            click = 1.0 if i < 15 else 0.0
            samples.append((tone * 0.6 + click * 0.4) * env * 0.4)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["lantern_toggle"] = snd

        # 3. Clue discovery / inspect (mystic bell chime)
        duration = 0.65
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        freqs = [440, 660, 880]
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 4.5)
            val = sum(math.sin(2 * math.pi * f * t) * (1.0 / (idx + 1)) for idx, f in enumerate(freqs))
            samples.append(val * env * 0.3)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["clue"] = snd

        # 4. Key pickup (bright metallic sparkle chord)
        duration = 0.45
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        chords = [(0.0, 587.33), (0.08, 880.0), (0.16, 1174.66)]  # D5, A5, D6
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            val = 0.0
            for start_t, f in chords:
                if t >= start_t:
                    local_t = t - start_t
                    env = math.exp(-local_t * 8.0)
                    val += math.sin(2 * math.pi * f * local_t) * env
            samples.append(val * 0.28)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["pickup"] = snd

        # 5. Wrong key (dull stone clank / rejection)
        duration = 0.25
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 12)
            tone = math.sin(2 * math.pi * 130 * t) + math.sin(2 * math.pi * 95 * t)
            noise = ((i * 47) % 80 / 40.0 - 1.0) * 0.3
            samples.append((tone * 0.5 + noise) * env * 0.35)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["door_locked"] = snd

        # 6. Door open / Level complete fanfare
        duration = 1.4
        n_samples = int(SAMPLE_RATE * duration)
        samples = []
        notes = [(0.0, 392.0), (0.2, 523.25), (0.4, 659.25), (0.6, 783.99), (0.8, 1046.5)]
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            val = 0.0
            # rumbling opening stone
            rumble = math.sin(2 * math.pi * 55 * t) * max(0.0, 1.0 - t * 0.8) * 0.2
            for start_t, f in notes:
                if t >= start_t:
                    local_t = t - start_t
                    env = math.exp(-local_t * 3.2)
                    val += (math.sin(2 * math.pi * f * local_t) +
                            0.3 * math.sin(4 * math.pi * f * local_t)) * env * 0.25
            samples.append((val + rumble) * 0.35)
        snd = self._build_sound(samples)
        if snd:
            self.sounds["door_open"] = snd


    def play(self, sound_name: str):
        """Plays a one-shot sound effect by name."""
        if not self.enabled or not pygame.mixer.get_init():
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

audio=AudioManager()
