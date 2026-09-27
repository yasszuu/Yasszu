"""
Formulations variees pour l'intro ("qui remporte un combat entre X et Y ?"),
l'annonce du resultat, et de petites reactions vivantes/provocantes apres le
resultat -- pour ne jamais repeter la meme phrase d'un round a l'autre et
donner un ton plus dynamique, façon createur de contenu, a la voix off.
"""
import random

INTRO_TEMPLATES = [
    "Dans la nature, qui remporte un combat entre {a} et {b} ?",
    "Qui l'emporterait dans un affrontement entre {a} et {b} ?",
    "Face a face : {a} contre {b}. Qui gagne ?",
    "Un duel opposant {a} a {b} : qui sortirait vainqueur ?",
    "Qui aurait le dessus entre {a} et {b} ?",
    "Entre {a} et {b}, qui remporterait ce combat ?",
    "Voici un affrontement entre {a} et {b}. Qui gagne selon toi ?",
    "Accroche-toi, ca va etre violent entre {a} et {b} !",
    "Team {a} ou team {b} ? Dis-le en commentaire !",
    "Alerte affrontement : {a} contre {b}, ca sent le carnage !",
    "Prepare-toi, {a} et {b} vont s'affronter et ca va faire mal !",
    "Qui de {a} ou {b} merite vraiment le titre de plus fort ?",
    "{a} contre {b} : le combat que personne n'attendait !",
]

RESULT_TEMPLATES = [
    "{winner} l'emporte avec {higher} pourcent de chances, face a {loser} qui obtient {lower} pourcent.",
    "Avec {higher} pourcent de chances, {winner} remporte ce combat face a {loser}, credite de {lower} pourcent seulement.",
    "{winner} domine ce duel avec {higher} pourcent, laissant {loser} a seulement {lower} pourcent.",
    "C'est {winner} qui l'emporte, credite de {higher} pourcent de chances, contre {lower} pourcent pour {loser}.",
    "{winner} sort vainqueur avec {higher} pourcent de chances, {loser} devra se contenter de {lower} pourcent.",
    "Verdict sans appel : {winner} gagne avec {higher} pourcent, face aux {lower} pourcent de {loser}.",
    "{higher} pourcent pour {winner}, contre seulement {lower} pourcent pour {loser} : la victoire lui revient.",
    "Le combat tourne en faveur de {winner}, credite de {higher} pourcent de chances face a {loser} et ses {lower} pourcent.",
]

# Petite reaction ajoutee apres le resultat, une fois sur deux environ, pour
# rendre la voix off plus vivante (chaine vide incluse pour ne pas que ce
# soit systematique a chaque round).
REACTION_TEMPLATES = [
    "Sans pitie pour {loser} !",
    "Perso je m'attendais pas a ca !",
    "Le twist de la journee !",
    "Ca pique pour {loser}, avoue !",
    "Personne ne voyait venir ce resultat !",
    "Franchement, ca se discute en commentaire !",
    "Grosse surprise sur ce coup-la !",
    "",
    "",
    "",
]


CTA_TEXTS = [
    "Commente qui aurait du gagner selon toi !",
    "Dis-moi en commentaire qui tu aurais choisi !",
    "Abonne-toi pour le prochain combat d'animaux !",
    "Like si t'as appris un truc aujourd'hui !",
    "T'es plutot d'accord ou pas d'accord avec ces resultats ? Dis-le en commentaire !",
    "Abonne-toi, d'autres duels arrivent tres vite !",
]

OPENING_HOOK_TEMPLATES = [
    "Entre {winner} et {loser}, la reponse va te surprendre !",
    "{winner} face a {loser} : le resultat est plus extreme que tu ne le crois.",
    "Prepare-toi, le duel {winner} contre {loser} arrive tres vite.",
    "{winner} contre {loser} : reste jusqu'au bout, ca vaut le coup.",
    "Ce que {winner} fait a {loser} dans cette video va te choquer.",
]

OPENING_SUBTITLE_TEMPLATES = [
    "AUJOURD'HUI {n} ANIMAUX VONT S'AFFRONTER",
    "{n} ANIMAUX, UN SEUL VAINQUEUR PAR DUEL",
    "{n} BETES ENTRENT EN SCENE AUJOURD'HUI",
    "PRET POUR {n} COMBATS D'ANIMAUX ?",
    "{n} ANIMAUX. DES DUELS SANS PITIE.",
]


FRENCH_ORDINALS = {
    1: "premier", 2: "deuxieme", 3: "troisieme", 4: "quatrieme", 5: "cinquieme",
    6: "sixieme", 7: "septieme", 8: "huitieme", 9: "neuvieme", 10: "dixieme",
}


def french_ordinal(n: int) -> str:
    return FRENCH_ORDINALS.get(n, f"{n}eme")


FIGHT_CARD_HOOK_TEMPLATES = [
    "Que se passe-t-il si {a} rencontre {b} dans la nature ? C'est notre {ordinal} duel du jour, reste jusqu'au bout !",
    "Imagine {a} face a {b} dans la nature... c'est exactement notre {ordinal} combat du jour !",
    "Prepare-toi : {a} contre {b}, ce sera notre {ordinal} duel aujourd'hui.",
    "{a} contre {b} : notre {ordinal} duel du jour risque de te surprendre.",
]


def random_fight_card_hook(winner: str, loser: str, duel_number: int) -> str:
    template = random.choice(FIGHT_CARD_HOOK_TEMPLATES)
    return template.format(a=winner, b=loser, ordinal=french_ordinal(duel_number))


NO_SPOIL_HOOK_TEMPLATES = [
    "Si {a} croise {b} dans la nature, qui ressort vivant ?",
    "Entre {a} et {b}, un seul survivrait a une vraie rencontre. Lequel ?",
    "{a} face a {b} : qui s'en sortirait vraiment ?",
    "Imagine {a} et {b} nez a nez dans la nature... qui gagnerait ?",
    "{a} contre {b} : qui l'emporterait si ca se passait pour de vrai ?",
]


def random_no_spoil_hook(name_a: str, name_b: str) -> str:
    template = random.choice(NO_SPOIL_HOOK_TEMPLATES)
    return template.format(a=name_a, b=name_b)


def random_opening_hook(winner: str, loser: str) -> str:
    template = random.choice(OPENING_HOOK_TEMPLATES)
    return template.format(winner=winner, loser=loser)


def random_opening_subtitle(n: int) -> str:
    template = random.choice(OPENING_SUBTITLE_TEMPLATES)
    return template.format(n=n)


def random_intro_sentence(name_a: str, name_b: str) -> str:
    template = random.choice(INTRO_TEMPLATES)
    return template.format(a=name_a, b=name_b)


def random_result_sentence(winner: str, higher: int, loser: str, lower: int) -> str:
    template = random.choice(RESULT_TEMPLATES)
    sentence = template.format(winner=winner, higher=higher, loser=loser, lower=lower)

    reaction = random.choice(REACTION_TEMPLATES).format(winner=winner, loser=loser)
    if reaction:
        sentence = f"{sentence} {reaction}"
    return sentence


def random_cta_sentence() -> str:
    return random.choice(CTA_TEXTS)
