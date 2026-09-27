"""
Effets sonores synthetises (aucun fichier audio externe necessaire) :
- decompte : 3 "bips" courts, un par seconde
- swoosh : un souffle d'air discret utilise quand un animal apparait a l'ecran
"""
import numpy as np
from moviepy import AudioClip

BEEP_TIMES = (0.0, 1.0, 2.0)
BEEP_FREQS = (700, 850, 1050)
BEEP_LEN = 0.14
DECAY = 22.0


def countdown_beep_audio(total_duration: float = 3.0, fps: int = 44100) -> AudioClip:
    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        signal = np.zeros_like(t_arr)
        for bt, freq in zip(BEEP_TIMES, BEEP_FREQS):
            local = t_arr - bt
            mask = (local >= 0) & (local < BEEP_LEN)
            if np.any(mask):
                env = np.exp(-local[mask] * DECAY)
                signal[mask] += 0.65 * np.sin(2 * np.pi * freq * local[mask]) * env
        stereo = np.stack([signal, signal], axis=-1)
        return stereo[0] if np.isscalar(t) else stereo

    return AudioClip(make_frame, duration=total_duration, fps=fps)


def _moving_average(x: np.ndarray, window: int) -> np.ndarray:
    window = max(1, int(window))
    kernel = np.ones(window) / window
    return np.convolve(x, kernel, mode="same")


def swoosh_audio(duration: float = 0.45, fps: int = 44100, volume: float = 0.045) -> AudioClip:
    """
    Souffle d'air discret (bruit filtre en "passe-bande", sans tonalite),
    beaucoup plus doux et plus "vente" qu'un swoosh electronique classique.
    Precalcule une fois en tableau numpy pour un rendu deterministe et rapide.
    """
    n = int(duration * fps)
    tt = np.linspace(0, duration, n, endpoint=False)
    envelope = np.sin(np.pi * np.clip(tt / duration, 0, 1)) ** 1.6

    noise = np.random.default_rng().uniform(-1, 1, n)
    # "passe-bande" approxime par difference de deux moyennes glissantes :
    # garde les frequences moyennes (souffle d'air), retire le grave sourd
    # et l'aigu type "static".
    narrow = _moving_average(noise, fps * 0.00025)
    wide = _moving_average(noise, fps * 0.0035)
    bandpassed = narrow - wide
    peak = np.max(np.abs(bandpassed)) + 1e-9
    bandpassed = bandpassed / peak

    signal = bandpassed * envelope * volume

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        idx = np.clip((t_arr * fps).astype(int), 0, n - 1)
        s = signal[idx]
        stereo = np.stack([s, s], axis=-1)
        return stereo[0] if np.isscalar(t) else stereo

    return AudioClip(make_frame, duration=duration, fps=fps)


def pop_audio(duration: float = 0.13, fps: int = 44100, volume: float = 0.16) -> AudioClip:
    """
    Petit "pop" percussif (frequence qui chute rapidement + decroissance
    nette), utilise quand un animal apparait a l'ecran. Precalcule une fois
    en tableau numpy pour un rendu deterministe et rapide.
    """
    n = int(duration * fps)
    tt = np.linspace(0, duration, n, endpoint=False)
    freq = 950 * np.exp(-tt * 16) + 90  # chute rapide de la frequence
    phase = 2 * np.pi * np.cumsum(freq) / fps
    tone = np.sin(phase)
    envelope = np.exp(-tt * 26)  # attaque immediate, decroissance rapide
    signal = tone * envelope * volume

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        idx = np.clip((t_arr * fps).astype(int), 0, n - 1)
        s = signal[idx]
        stereo = np.stack([s, s], axis=-1)
        return stereo[0] if np.isscalar(t) else stereo

    return AudioClip(make_frame, duration=duration, fps=fps)


def ding_audio(duration: float = 0.6, fps: int = 44100, volume: float = 0.22) -> AudioClip:
    """
    Petit "ding" (carillon a deux harmoniques, decroissance nette), joue au
    moment exact ou le pourcentage du vainqueur est revele.
    """
    n = int(duration * fps)
    tt = np.linspace(0, duration, n, endpoint=False)
    envelope = np.exp(-tt * 5.0)
    tone = 0.6 * np.sin(2 * np.pi * 880 * tt) + 0.4 * np.sin(2 * np.pi * 1318.5 * tt)
    signal = tone * envelope * volume

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        idx = np.clip((t_arr * fps).astype(int), 0, n - 1)
        s = signal[idx]
        stereo = np.stack([s, s], axis=-1)
        return stereo[0] if np.isscalar(t) else stereo

    return AudioClip(make_frame, duration=duration, fps=fps)


def impact_boom_audio(duration: float = 0.45, fps: int = 44100, volume: float = 0.32) -> AudioClip:
    """
    Petit "boom" percussif grave (choc/impact), joue au moment ou le second
    animal apparait dans l'intro, pour marquer la confrontation.
    """
    n = int(duration * fps)
    tt = np.linspace(0, duration, n, endpoint=False)
    freq = 95 * np.exp(-tt * 4.0) + 45  # descend rapidement vers le grave
    phase = 2 * np.pi * np.cumsum(freq) / fps
    tone = np.sin(phase)
    noise = np.random.default_rng().uniform(-1, 1, n) * np.exp(-tt * 35) * 0.35
    envelope = np.exp(-tt * 9.0)
    signal = (tone + noise) * envelope * volume

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        idx = np.clip((t_arr * fps).astype(int), 0, n - 1)
        s = signal[idx]
        stereo = np.stack([s, s], axis=-1)
        return stereo[0] if np.isscalar(t) else stereo

    return AudioClip(make_frame, duration=duration, fps=fps)
