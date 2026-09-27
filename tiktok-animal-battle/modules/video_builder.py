"""
Assemble une sequence d'ouverture (recap de tous les animaux, avec hook
immediat sur le combat le plus SERRE, dont l'animal vedette est detoure),
puis chaque round (transition en balayage rotatif avec un leger souffle de
vent / intro avec apparition animee et synchronisee / decompte anime (qui
s'accelere au fil de la video) / resultat / explication -- sauf pour les
rounds "express" qui l'ecourtent / sortie animee), puis un ecran de fin
(CTA), et concatene le tout en une seule video finale prete pour TikTok
(format 9:16), avec musique de fond optionnelle (choisie au hasard). Une
fine barre de progression reste visible en haut de l'ecran tout du long.
Le nombre de rounds est adapte automatiquement pour viser une duree totale
cible (target_duration_min/max dans config.json).
"""
import os
import re
import math
import random
import numpy as np
from PIL import Image
from moviepy import (
    ImageClip, VideoClip, AudioFileClip, AudioClip, CompositeAudioClip,
    concatenate_videoclips, concatenate_audioclips,
)

from modules.image_fetcher import get_animal_image, find_local_animal_image
from modules.tts import get_tts_audio, get_tts_audio_with_timings
from modules.colors import random_corner_pair, random_single_color
from modules.sound import countdown_beep_audio, pop_audio, ding_audio, swoosh_audio, impact_boom_audio
from modules.music import find_music_file
from modules.cutout import get_cutout
from modules.branding import find_logo_file
from modules.backgrounds import find_intro_background
from modules.animal_sounds import get_animal_sound
from modules.phrasing import (
    random_intro_sentence, random_result_sentence, random_cta_sentence,
    random_no_spoil_hook,
)
from modules.graphics import (
    build_stacked_base, draw_divider, draw_vs_badge, countdown_blink_color,
    WHITE, GOLD, BLACK,
    add_animal_silhouette, paste_cutout_in_box, add_cutout_outline, tint_silhouette, add_zone_caption,
    render_result_frame, build_explanation_base, draw_caption_chunk, add_zone_exit_fade,
    build_sweep_transition_frame, apply_punch_zoom,
    build_opening_base, add_opening_title,
    build_ending_base, _hex_to_rgb,
    draw_progress_bar,
)

CACHE_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "images")
COUNTDOWN_FILL_COLOR = (255, 214, 0)  # or
ENTRANCE_DURATION = 0.22
EXIT_DURATION = 0.30
SWEEP_DURATION = 0.7
AVG_ROUND_DURATION = 20.0  # estimation grossiere, sert juste a calibrer la barre de progression
EXPRESS_PROBABILITY = 0.30
WINNER_BLINK_DURATION = 1.0   # clignotement rapide puis fige a 100%
WINNER_BLINK_HZ = 9.0         # tres rapide
WINNER_BLINK_COLOR = (40, 200, 90)   # vert
LOSER_BLINK_COLOR = (0, 0, 0)         # noir
COUNTDOWN_MIN_SECONDS = 1.5
COUNTDOWN_START_SECONDS = 3.0
COUNTDOWN_STEP = 0.3
ANIMAL_SOUND_MAX_DURATION = 1.0
ANIMAL_SOUND_VOLUME = 0.55
PUNCH_ZOOM_DURATION = 0.35


def _silence(duration: float) -> AudioClip:
    def make_frame(t):
        if np.isscalar(t):
            return np.array([0.0, 0.0])
        return np.zeros((len(t), 2))
    return AudioClip(make_frame, duration=duration, fps=44100)


def _normalize_word(word: str) -> str:
    return re.sub(r"[^\wÀ-ÿ]", "", word).lower()


def _find_word_offset(boundaries, name: str, after: float = 0.0):
    """
    Cherche dans les timings de la voix (boundaries) l'instant (en secondes)
    ou 'name' commence a etre prononce, apres l'instant 'after'. Essaie
    d'abord le premier mot du nom (comparaison par prefixe dans les deux
    sens, car edge-tts peut decouper un nom compose/a trait d'union comme
    "Rat-taupe" en plusieurs mots-cles distincts), puis en repli n'importe
    quel autre mot du nom (utile si le premier mot est mal segmente par la
    voix -- source frequente de retard visible sur le DEUXIEME animal).
    Renvoie None si introuvable.
    """
    words = [w for w in re.split(r"[\s'\-]+", name) if w]
    targets = [t for t in (_normalize_word(w) for w in words) if t]
    if not targets:
        return None
    primary = targets[0]

    for b in boundaries:
        if b["offset"] < after:
            continue
        word = _normalize_word(b["text"])
        if word and (word == primary or primary.startswith(word) or word.startswith(primary)):
            return b["offset"]

    for b in boundaries:
        if b["offset"] < after:
            continue
        word = _normalize_word(b["text"])
        if word in targets:
            return b["offset"]

    return None


def _estimate_offset_by_position(full_text: str, name: str, total_duration: float, start_search: int = 0):
    """
    Repli quand aucun mot n'a pu etre retrouve dans les timings : estime
    l'instant a partir de la position du nom DANS LE TEXTE (proportion de
    caracteres avant lui), bien plus fiable qu'un pourcentage fixe.
    """
    if not full_text or total_duration <= 0:
        return None
    first_word = name.split()[0] if name.split() else name
    idx = full_text.lower().find(first_word.lower(), start_search)
    if idx == -1:
        return None
    ratio = idx / max(1, len(full_text))
    return total_duration * ratio


def _group_words_into_chunks(boundaries, words_per_chunk: int = 3):
    """Regroupe les timings mot-par-mot en petits paquets, pour un sous-titre style TikTok."""
    chunks = []
    current = []
    for b in boundaries:
        current.append(b)
        if len(current) >= words_per_chunk:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def _fallback_chunks_from_text(text: str, total_duration: float, words_per_chunk: int = 3):
    """
    Repli si edge-tts n'a renvoye AUCUN timing mot-par-mot exploitable
    (ca arrive) : reconstruit des paquets de mots repartis uniformement sur
    la duree de la voix, pour que le sous-titre s'affiche quand meme.
    """
    words = text.split()
    if not words or total_duration <= 0:
        return []
    groups = [words[i:i + words_per_chunk] for i in range(0, len(words), words_per_chunk)]
    chunk_dur = total_duration / len(groups)
    chunks = []
    for i, group in enumerate(groups):
        start = i * chunk_dur
        chunks.append([{"text": w, "offset": start, "duration": chunk_dur} for w in group])
    return chunks


def _current_chunk_text(chunks, t: float) -> str:
    """Le paquet de mots actif a l'instant t (sous-titre "auto-genere")."""
    if not chunks:
        return ""
    for chunk in chunks:
        start = chunk[0]["offset"]
        end = chunk[-1]["offset"] + chunk[-1].get("duration", 0.3)
        if start <= t < end:
            return " ".join(c["text"] for c in chunk).upper()
    last = chunks[-1]
    last_end = last[-1]["offset"] + last[-1].get("duration", 0.3)
    if t >= last_end:
        return " ".join(c["text"] for c in last).upper()
    return ""


def _animal_sound_clip(display_name: str, search_term: str):
    """
    Court extrait sonore de l'animal (best effort, cf. modules/animal_sounds.py) :
    renvoie None si aucun son exploitable n'a ete trouve (couverture inegale
    selon les especes) -- ne bloque jamais la generation.
    """
    path = get_animal_sound(search_term or display_name)
    if not path:
        return None
    try:
        clip = AudioFileClip(path)
        dur = min(ANIMAL_SOUND_MAX_DURATION, clip.duration)
        return clip.subclipped(0, dur).with_volume_scaled(ANIMAL_SOUND_VOLUME)
    except Exception:
        return None


def resolve_animal_visual(display_name: str, search_term: str, outline_thickness: int = 3,
                           outline_color=(0, 0, 0, 255)):
    """
    Renvoie une image PIL RGBA prete a l'emploi pour cet animal, avec un
    leger contour (couleur configurable -- noir pendant les manches,
    rouge/bleu en intro) : en priorite une image fournie par l'utilisateur
    dans banque_animaux/ (deja detouree ou non), sinon une photo Wikimedia
    detouree automatiquement par IA. Si le detourage echoue et qu'aucune
    image locale n'est fournie, se rabat sur la photo brute (le contour
    dessine alors un simple liseret rectangulaire autour de toute la photo).
    """
    local_path = find_local_animal_image(display_name)
    if local_path:
        img = Image.open(local_path).convert("RGBA")
    else:
        raw_path = get_animal_image(search_term)
        cutout = get_cutout(raw_path, search_term)
        img = cutout if cutout is not None else Image.open(raw_path).convert("RGBA")
    return add_cutout_outline(img, thickness=outline_thickness, color=outline_color)


def build_round_clip(round_cfg: dict, vcfg: dict, round_number: int, total_rounds_estimate: int,
                      top_color: str, bottom_color: str, countdown_seconds: float = 3.0,
                      express: bool = False, log=print):
    W, H = vcfg["width"], vcfg["height"]
    voice, rate, volume = vcfg["voice"], vcfg["voice_rate"], vcfg["voice_volume"]
    pitch = vcfg.get("voice_pitch", "+0Hz")
    font_regular, font_bold = vcfg["font_regular"], vcfg["font_bold"]
    name_a, name_b = round_cfg["animal_a"], round_cfg["animal_b"]
    pct_a, pct_b = int(round_cfg["percent_a"]), int(round_cfg["percent_b"])
    fps = vcfg["fps"]
    progress_value = min(1.0, round_number / max(1, total_rounds_estimate))

    log(f"  -> Round {round_number} : {name_a} vs {name_b}" + (" [express]" if express else ""))

    log("     - recuperation des images...")
    visual_a = resolve_animal_visual(name_a, round_cfg.get("search_a", name_a), outline_color=BLACK)
    visual_b = resolve_animal_visual(name_b, round_cfg.get("search_b", name_b), outline_color=BLACK)

    base_bg = build_stacked_base(W, H, top_color, bottom_color)

    clips = []

    # Etape "vide" (fond + VS uniquement), point de depart de l'intro.
    stage0 = base_bg.copy()
    draw_divider(stage0, 0.0, COUNTDOWN_FILL_COLOR)
    draw_vs_badge(stage0, font_bold)

    # ---- Phase 1 : intro, avec apparition ANIMEE (grossit + fondu) de
    #      chaque animal au moment ou son nom est prononce (+ pop) ----
    log("     - phase intro...")
    intro_text = random_intro_sentence(name_a, name_b)
    intro_audio_path, intro_boundaries = get_tts_audio_with_timings(intro_text, voice, rate, volume, pitch)
    intro_audio = AudioFileClip(intro_audio_path)

    offset_a = _find_word_offset(intro_boundaries, name_a)
    if offset_a is None:
        offset_a = _estimate_offset_by_position(intro_text, name_a, intro_audio.duration) or 0.15
    offset_b = _find_word_offset(intro_boundaries, name_b, after=offset_a)
    if offset_b is None:
        est_b = _estimate_offset_by_position(intro_text, name_b, intro_audio.duration,
                                              start_search=len(name_a))
        offset_b = est_b if est_b is not None and est_b > offset_a else offset_a + 0.6

    def make_intro_frame(t):
        frame = stage0.copy()
        if t >= offset_a:
            prog_a = min(1.0, (t - offset_a) / ENTRANCE_DURATION)
            add_animal_silhouette(frame, visual_a, "top", progress=prog_a)
            add_zone_caption(frame, name_a, "top", font_bold)
        if t >= offset_b:
            prog_b = min(1.0, (t - offset_b) / ENTRANCE_DURATION)
            add_animal_silhouette(frame, visual_b, "bottom", progress=prog_b)
            add_zone_caption(frame, name_b, "bottom", font_bold)
        draw_vs_badge(frame, font_bold)  # le VS doit toujours rester au-dessus des photos
        draw_progress_bar(frame, progress_value)
        return np.array(frame)

    intro_duration = intro_audio.duration + vcfg["intro_extra_seconds"]
    intro_clip = VideoClip(make_intro_frame, duration=intro_duration).with_fps(min(fps, 30))

    # Le pop demarre pile au meme instant que le debut de l'animation
    # d'entree, pour rester bien synchronise avec l'annonce orale. Le cri/
    # chant de l'animal (best effort) est joue juste apres, s'il existe.
    pop_a = pop_audio().with_start(max(0.0, offset_a))
    pop_b = pop_audio().with_start(max(0.0, offset_b))
    audio_layers = [intro_audio, pop_a, pop_b]
    sound_a = _animal_sound_clip(name_a, round_cfg.get("search_a", name_a))
    if sound_a is not None:
        audio_layers.append(sound_a.with_start(max(0.0, offset_a + 0.12)))
    sound_b = _animal_sound_clip(name_b, round_cfg.get("search_b", name_b))
    if sound_b is not None:
        audio_layers.append(sound_b.with_start(max(0.0, offset_b + 0.12)))
    intro_clip = intro_clip.with_audio(CompositeAudioClip(audio_layers))
    clips.append(intro_clip)

    # Base complete (les deux animaux deja reveles), reutilisee pour le
    # decompte et le resultat.
    base_no_divider = base_bg.copy()
    add_animal_silhouette(base_no_divider, visual_a, "top")
    add_animal_silhouette(base_no_divider, visual_b, "bottom")
    add_zone_caption(base_no_divider, name_a, "top", font_bold)
    add_zone_caption(base_no_divider, name_b, "bottom", font_bold)

    def compose(progress: float, outline_color=None, text_color=None):
        frame = base_no_divider.copy()
        draw_divider(frame, progress, COUNTDOWN_FILL_COLOR)
        draw_vs_badge(frame, font_bold, outline_color=outline_color, text_color=text_color)
        draw_progress_bar(frame, progress_value)
        return frame

    # ---- Phase 2 : decompte anime (barre gauche -> droite). Sa duree
    #      raccourcit progressivement au fil de la video (3s -> 1.5s) pour
    #      resserrer le rythme perçu. ----
    log(f"     - decompte ({countdown_seconds:.1f}s)...")

    def make_countdown_frame(t):
        progress = t / countdown_seconds
        blink_color = countdown_blink_color(t)
        return np.array(compose(progress, outline_color=blink_color, text_color=blink_color))

    countdown_clip = VideoClip(make_countdown_frame, duration=countdown_seconds).with_fps(min(fps, 30))
    countdown_clip = countdown_clip.with_audio(countdown_beep_audio(countdown_seconds))
    clips.append(countdown_clip)

    # ---- Phase 3 : resultat en pourcentage (le perdant est assombri, le
    #      vainqueur ET le perdant clignotent 1s (vert / noir) puis se
    #      figent a 100% -- sur la silhouette elle-meme, plus aucun
    #      cadre/rectangle ni nom d'animal -- + ding au moment du reveal) ----
    log("     - resultat...")
    winner, higher = (name_a, pct_a) if pct_a >= pct_b else (name_b, pct_b)
    loser, lower = (name_b, pct_b) if pct_a >= pct_b else (name_a, pct_a)
    winner_zone = "top" if pct_a >= pct_b else "bottom"
    winner_visual = visual_a if pct_a >= pct_b else visual_b
    loser_visual = visual_b if pct_a >= pct_b else visual_a

    winner_settled = tint_silhouette(winner_visual, WINNER_BLINK_COLOR, 1.0)
    loser_settled = tint_silhouette(loser_visual, LOSER_BLINK_COLOR, 1.0)

    def _build_result_base(top_img, bottom_img):
        frame = base_bg.copy()
        draw_divider(frame, 1.0, COUNTDOWN_FILL_COLOR)
        add_animal_silhouette(frame, top_img, "top")
        add_animal_silhouette(frame, bottom_img, "bottom")
        # Plus de nom d'animal une fois le decompte termine : juste l'image
        # et les pourcentages.
        draw_progress_bar(frame, progress_value)
        return frame

    if winner_zone == "top":
        bg_off = _build_result_base(winner_visual, loser_visual)
        bg_on = _build_result_base(winner_settled, loser_settled)
    else:
        bg_off = _build_result_base(loser_visual, winner_visual)
        bg_on = _build_result_base(loser_settled, winner_settled)

    result_img_off = render_result_frame(bg_off, pct_a, pct_b, font_bold, top_color, bottom_color)
    result_img_on = render_result_frame(bg_on, pct_a, pct_b, font_bold, top_color, bottom_color)

    result_text = random_result_sentence(winner, higher, loser, lower)
    result_audio = AudioFileClip(get_tts_audio(result_text, voice, rate, volume, pitch))
    result_duration = result_audio.duration + vcfg["result_display_seconds"]

    def make_result_frame(t):
        if t < WINNER_BLINK_DURATION:
            blink_on = int(t * WINNER_BLINK_HZ * 2) % 2 == 0
            frame = result_img_on if blink_on else result_img_off
        else:
            frame = result_img_on  # fige (vainqueur vert / perdant noir, 100%) jusqu'a la fin de la manche
        return np.array(frame)

    result_clip = VideoClip(make_result_frame, duration=result_duration).with_fps(min(fps, 30))
    result_clip = result_clip.with_audio(CompositeAudioClip([result_audio, ding_audio().with_start(0.0)]))
    clips.append(result_clip)

    # ---- Phase 4 : reveal -> la moitie du PERDANT est remplacee par le
    #      texte d'explication (MAJUSCULES, blanc/contour noir), sans zoom.
    #      La moitie du vainqueur reste affichee telle quelle (resultat).
    #      Les rounds "express" sautent cette phase pour casser le rythme. ----
    exit_source = result_img_on
    if not express:
        log("     - explication...")
        loser_zone = "bottom" if pct_a >= pct_b else "top"
        loser_color = bottom_color if pct_a >= pct_b else top_color
        explanation_base = build_explanation_base(result_img_on, loser_zone, loser_color, font_bold)

        explanation_audio_path, explanation_boundaries = get_tts_audio_with_timings(
            round_cfg["explanation"], voice, rate, volume, pitch)
        explanation_audio = AudioFileClip(explanation_audio_path)
        explanation_chunks = _group_words_into_chunks(explanation_boundaries, words_per_chunk=3)
        if not explanation_chunks:
            explanation_chunks = _fallback_chunks_from_text(round_cfg["explanation"], explanation_audio.duration)
        explanation_duration = explanation_audio.duration + vcfg["explanation_extra_seconds"]

        def make_explanation_frame(t):
            frame = explanation_base.copy()
            text = _current_chunk_text(explanation_chunks, t) if t <= explanation_audio.duration else ""
            draw_caption_chunk(frame, loser_zone, text, font_bold)
            draw_progress_bar(frame, progress_value)
            return np.array(frame)

        explanation_clip = VideoClip(make_explanation_frame, duration=explanation_duration).with_fps(min(fps, 30))
        explanation_clip = explanation_clip.with_audio(explanation_audio)
        clips.append(explanation_clip)
        exit_source = explanation_base
    else:
        log("     - (round express : explication sautee)")

    # ---- Phase 5 : sortie animee -> les deux zones se fondent dans leur
    #      couleur unie, pour preparer une transition propre vers le round
    #      suivant (balayage rotatif). ----
    def make_exit_frame(t):
        frame = exit_source.copy()
        alpha = min(1.0, t / EXIT_DURATION)
        # On fond vers le NOIR (pas vers la couleur de la zone elle-meme) :
        # fondre vers une couleur trop proche de celle du texte/de la photo
        # donnait un rendu "delave", peu lisible, juste avant la transition.
        add_zone_exit_fade(frame, "top", "#000000", alpha)
        add_zone_exit_fade(frame, "bottom", "#000000", alpha)
        # Le fondu peut chevaucher le bord du badge VS (qui deborde
        # legerement de la barre centrale) : on le redessine par-dessus
        # pour qu'il reste TOUJOURS au-dessus de tout calque, intact.
        draw_vs_badge(frame, font_bold, outline_color=WHITE, text_color=GOLD)
        draw_progress_bar(frame, progress_value)
        return np.array(frame)

    exit_clip = VideoClip(make_exit_frame, duration=EXIT_DURATION).with_fps(min(fps, 30))
    exit_clip = exit_clip.with_audio(_silence(EXIT_DURATION))
    clips.append(exit_clip)

    return concatenate_videoclips(clips, method="compose")


def build_sweep_transition_clip(prev_colors, next_colors, vcfg: dict):
    """Transition entre deux rounds : le VS/la barre tournent sur 360° pour balayer les couleurs."""
    W, H = vcfg["width"], vcfg["height"]
    font_bold = vcfg["font_bold"]
    fps = vcfg["fps"]
    old_top, old_bottom = prev_colors
    new_top, new_bottom = next_colors

    def make_frame(t):
        progress = t / SWEEP_DURATION
        frame = build_sweep_transition_frame(old_top, old_bottom, new_top, new_bottom, W, H, progress, font_bold)
        return np.array(frame)

    clip = VideoClip(make_frame, duration=SWEEP_DURATION).with_fps(min(fps, 30))
    # Leger souffle de vent, synchronise sur la rotation (discret, comme un
    # bruit de vent plutot qu'un effet sonore marque).
    clip = clip.with_audio(swoosh_audio(duration=SWEEP_DURATION))
    return clip


def build_opening_clip(selected_rounds: list, vcfg: dict, log=print):
    """
    Sequence d'ouverture jouee une seule fois au debut de la video : voix +
    titre "DUELS D'ANIMAUX" (ou logo utilisateur) sur un fond pastel
    aleatoire (ou une image fournie par l'utilisateur dans fond_intro/).
    Seul le combat le PLUS SERRE de la video (celui dont l'issue est la
    plus incertaine -- toujours place en dernier, cf. build_full_video) est
    teased ici, SANS reveler qui gagne : les deux animaux (et seulement
    eux, pas le reste du roster) apparaissent chacun au moment ou son nom
    est prononce dans une question qui ne spoile rien ("Si X croise Y dans
    la nature, qui ressort vivant ?").
    """
    W, H = vcfg["width"], vcfg["height"]
    font_bold = vcfg["font_bold"]
    fps = vcfg["fps"]
    voice = vcfg["voice"]
    rate, volume = vcfg["voice_rate"], vcfg["voice_volume"]
    pitch = vcfg.get("voice_pitch", "+0Hz")

    # Le round le plus SERRE (issue la plus incertaine) sert de hook -- pas
    # le plus ecrasant, pour ne pas spoiler un resultat evident.
    hero_round_idx = min(
        range(len(selected_rounds)),
        key=lambda i: abs(selected_rounds[i]["percent_a"] - selected_rounds[i]["percent_b"]),
    )
    hero_round = selected_rounds[hero_round_idx]
    name_a, name_b = hero_round["animal_a"], hero_round["animal_b"]
    search_a = hero_round.get("search_a", name_a)
    search_b = hero_round.get("search_b", name_b)

    log(f"  -> Ouverture : {name_a} vs {name_b} (sans reveler l'issue)...")
    visual_a = resolve_animal_visual(name_a, search_a, outline_color=(30, 80, 190, 255))   # bleu
    visual_b = resolve_animal_visual(name_b, search_b, outline_color=(190, 35, 30, 255))   # rouge

    hook_text = random_no_spoil_hook(name_a, name_b)
    intro_audio_path, boundaries = get_tts_audio_with_timings(hook_text, voice, rate, volume, pitch)
    voice_audio = AudioFileClip(intro_audio_path)

    offset_a = _find_word_offset(boundaries, name_a)
    if offset_a is None:
        offset_a = _estimate_offset_by_position(hook_text, name_a, voice_audio.duration) or 0.15
    offset_b = _find_word_offset(boundaries, name_b, after=offset_a)
    if offset_b is None:
        est_b = _estimate_offset_by_position(hook_text, name_b, voice_audio.duration, start_search=len(name_a))
        offset_b = est_b if est_b is not None and est_b > offset_a else offset_a + 0.6

    bg_image_path = find_intro_background(vcfg.get("intro_background_folder", "fond_intro"))
    bg_color = random_single_color()
    base = build_opening_base(W, H, bg_color, bg_image_path=bg_image_path)
    logo_path = find_logo_file(vcfg.get("logo_folder", "logo"))
    add_opening_title(base, font_bold, logo_path=logo_path)

    # Les deux animaux, cote a cote, sous le titre. Cote a cote, avec un
    # leger chevauchement au centre pour leur laisser plus de largeur (donc
    # plus gros) qu'un simple partage strict en deux.
    left_box = (0, int(H * 0.20), int(W * 0.62), int(H * 0.97))
    right_box = (int(W * 0.38), int(H * 0.20), W, int(H * 0.97))

    both_visible_at = max(offset_a, offset_b) + ENTRANCE_DURATION

    def make_frame(t):
        frame = base.copy()
        prog_a = min(1.0, max(0.0, (t - offset_a) / ENTRANCE_DURATION)) if t >= offset_a else 0.0
        prog_b = min(1.0, max(0.0, (t - offset_b) / ENTRANCE_DURATION)) if t >= offset_b else 0.0
        if prog_a > 0:
            paste_cutout_in_box(frame, visual_a, left_box, progress=prog_a)
        if prog_b > 0:
            paste_cutout_in_box(frame, visual_b, right_box, progress=prog_b)

        # Petit "punch" de camera au moment ou les deux animaux se retrouvent
        # enfin ensemble a l'ecran, pour marquer le choc de la rencontre.
        t_since_punch = t - both_visible_at
        if 0 <= t_since_punch < PUNCH_ZOOM_DURATION:
            punch_intensity = math.sin(min(1.0, t_since_punch / PUNCH_ZOOM_DURATION) * math.pi)
            frame = apply_punch_zoom(frame, punch_intensity)

        return np.array(frame)

    total_duration = voice_audio.duration + 0.8
    clip = VideoClip(make_frame, duration=total_duration).with_fps(min(fps, 30))

    pop_a = pop_audio().with_start(max(0.0, offset_a))
    pop_b = pop_audio().with_start(max(0.0, offset_b))
    # Petit "boom" d'impact au moment ou le second animal apparait, pour
    # renforcer la sensation de confrontation. Les cris/chants des animaux
    # (best effort) sont ajoutes juste apres leur apparition, s'ils existent.
    boom = impact_boom_audio().with_start(max(0.0, offset_b))
    audio_layers = [voice_audio, pop_a, pop_b, boom]
    sound_a = _animal_sound_clip(name_a, search_a)
    if sound_a is not None:
        audio_layers.append(sound_a.with_start(max(0.0, offset_a + 0.12)))
    sound_b = _animal_sound_clip(name_b, search_b)
    if sound_b is not None:
        audio_layers.append(sound_b.with_start(max(0.0, offset_b + 0.12)))
    clip = clip.with_audio(CompositeAudioClip(audio_layers))
    return clip


def build_ending_clip(vcfg: dict, log=print):
    """Ecran de fin (CTA) : fond pastel aleatoire, texte + voix."""
    W, H = vcfg["width"], vcfg["height"]
    font_bold = vcfg["font_bold"]
    fps = vcfg["fps"]
    voice = vcfg["voice"]
    rate, volume = vcfg["voice_rate"], vcfg["voice_volume"]
    pitch = vcfg.get("voice_pitch", "+0Hz")

    log("  -> Ecran de fin (CTA)...")
    cta_text = random_cta_sentence()
    voice_audio = AudioFileClip(get_tts_audio(cta_text, voice, rate, volume, pitch))

    bg_color = random_single_color()
    base = build_ending_base(W, H, bg_color, cta_text, font_bold)

    duration = voice_audio.duration + 1.0
    entrance_duration = 0.4

    def make_frame(t):
        if t < entrance_duration:
            progress = t / entrance_duration
            eased = 1 - (1 - progress) ** 3
            scale = 0.85 + 0.15 * eased
            scaled_w, scaled_h = max(1, int(W * scale)), max(1, int(H * scale))
            scaled = base.resize((scaled_w, scaled_h), Image.LANCZOS)
            frame = Image.new("RGB", (W, H), _hex_to_rgb(bg_color))
            frame.paste(scaled, ((W - scaled_w) // 2, (H - scaled_h) // 2))
        else:
            frame = base.copy()
        return np.array(frame)

    clip = VideoClip(make_frame, duration=duration).with_fps(min(fps, 30))
    clip = clip.with_audio(voice_audio)
    return clip


def _add_background_music(final_clip, music_folder: str, music_volume: float, log=print):
    music_path = find_music_file(music_folder)
    if not music_path:
        return final_clip

    log(f"Ajout de la musique de fond ({os.path.basename(music_path)})...")
    music = AudioFileClip(music_path)
    total_duration = final_clip.duration

    if music.duration < total_duration:
        loops_needed = int(total_duration // music.duration) + 1
        music = concatenate_audioclips([music] * loops_needed)
    music = music.subclipped(0, total_duration).with_volume_scaled(music_volume)

    combined_audio = CompositeAudioClip([final_clip.audio, music])
    return final_clip.with_audio(combined_audio)


def build_full_video(config: dict, log=print):
    vcfg = config["video"]
    candidates = config["rounds"]
    target_min = vcfg.get("target_duration_min", 80)
    total_rounds_estimate = max(1, round(target_min / AVG_ROUND_DURATION))

    # ---- Etape 1 : selection des rounds (on construit les clips au fur et
    #      a mesure, jusqu'a atteindre la duree cible). ----
    selected_rounds = []
    round_clips = []
    round_colors = []
    round_build_args = []  # (round_number, countdown_seconds, express) pour reconstruction eventuelle
    total_duration = 0.0
    for round_cfg in candidates:
        colors = random_corner_pair()
        round_number = len(selected_rounds) + 1
        countdown_seconds = max(COUNTDOWN_MIN_SECONDS,
                                 COUNTDOWN_START_SECONDS - COUNTDOWN_STEP * (round_number - 1))
        express = round_number > 1 and random.random() < EXPRESS_PROBABILITY

        round_clip = build_round_clip(round_cfg, vcfg, round_number, total_rounds_estimate,
                                       colors[0], colors[1], countdown_seconds=countdown_seconds,
                                       express=express, log=log)
        selected_rounds.append(round_cfg)
        round_clips.append(round_clip)
        round_colors.append(colors)
        round_build_args.append((round_number, countdown_seconds, express))
        total_duration += round_clip.duration
        if total_duration >= target_min:
            break

    log(f"{len(selected_rounds)} round(s) retenu(s), duree cumulee des rounds : ~{total_duration:.0f}s")

    # ---- Etape 2 : le combat le plus SERRE (issue la plus incertaine) est
    #      deplace en DERNIER (le garder pour la fin cree du suspense ; le
    #      montrer en premier tuerait la hype). Le hook visuel dans
    #      l'ouverture montre deja son vainqueur, mais sans reveler l'issue. ----
    if len(selected_rounds) > 1:
        hero_idx = min(
            range(len(selected_rounds)),
            key=lambda i: abs(selected_rounds[i]["percent_a"] - selected_rounds[i]["percent_b"]),
        )
        if hero_idx != len(selected_rounds) - 1:
            for lst in (selected_rounds, round_clips, round_colors, round_build_args):
                lst.append(lst.pop(hero_idx))

        # Le round final ne doit jamais etre "express" : c'est le climax de
        # la video, il merite son explication complete.
        round_number, countdown_seconds, express = round_build_args[-1]
        if express:
            log("     (le duel final etait 'express', reconstruction avec l'explication complete)")
            round_clips[-1] = build_round_clip(
                selected_rounds[-1], vcfg, round_number, total_rounds_estimate,
                round_colors[-1][0], round_colors[-1][1], countdown_seconds=countdown_seconds,
                express=False, log=log,
            )

    # ---- Etape 3 : assemblage avec les transitions en balayage rotatif
    #      entre chaque round (depuis le noir, cf. la sortie animee). ----
    all_clips = []
    for i, round_clip in enumerate(round_clips):
        if i > 0:
            black = ("#000000", "#000000")
            sweep_clip = build_sweep_transition_clip(black, round_colors[i], vcfg)
            all_clips.append(sweep_clip)
        all_clips.append(round_clip)

    opening_clip = build_opening_clip(selected_rounds, vcfg, log=log)
    all_clips.insert(0, opening_clip)

    ending_clip = build_ending_clip(vcfg, log=log)
    all_clips.append(ending_clip)

    log("Assemblage final de la video...")
    final = concatenate_videoclips(all_clips, method="compose")

    music_folder = vcfg.get("music_folder")
    if music_folder:
        final = _add_background_music(final, music_folder, vcfg.get("music_volume", 0.144), log=log)

    out_path = vcfg["output_file"]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    log(f"Export vers {out_path} (cela peut prendre plusieurs minutes)...")
    final.write_videofile(
        out_path,
        fps=vcfg["fps"],
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
    )
    total_duration_final = final.duration
    log(f"Termine ! Duree totale : {total_duration_final:.1f} secondes.")
    return out_path
