"""
Compresse la banque d'images (banque_animaux/) pour qu'elle prenne beaucoup
moins de place, sans perte visible dans la video : chaque animal est affiche
au maximum sur ~1080 px, donc une photo de 4000 px (plusieurs Mo) est inutile.

Pour chaque image :
- redimensionnee pour que son plus grand cote fasse au maximum 1200 px
- convertie en WebP (garde la transparence des images deja detourees)

Les originaux ne sont JAMAIS modifies : le resultat est ecrit dans un
nouveau dossier "banque_animaux_compressee/". Verifie le resultat, puis
remplace l'ancien dossier par le nouveau (renomme-le en "banque_animaux").

Usage (PowerShell, dans le dossier du projet) :
    python compresser_banque.py
    python compresser_banque.py --taille 1000 --qualite 80   # encore plus leger
"""
import argparse
import os
import sys

from PIL import Image, ImageOps

EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def _mo(n_bytes: int) -> str:
    if n_bytes < 1024 * 1024:
        return f"{n_bytes / 1024:.0f} Ko"
    return f"{n_bytes / (1024 * 1024):.1f} Mo"


def compress_image(src: str, dst: str, max_side: int, quality: int):
    img = Image.open(src)
    img = ImageOps.exif_transpose(img)  # respecte l'orientation des photos de telephone
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    img = img.convert("RGBA" if has_alpha else "RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)  # ne fait que reduire, jamais agrandir
    img.save(dst, "WEBP", quality=quality, method=6)


def main():
    parser = argparse.ArgumentParser(description="Compresse la banque d'images des animaux")
    parser.add_argument("--source", default="banque_animaux", help="Dossier des images d'origine")
    parser.add_argument("--destination", default="banque_animaux_compressee", help="Dossier de sortie")
    parser.add_argument("--taille", type=int, default=1200, help="Plus grand cote maximum, en pixels")
    parser.add_argument("--qualite", type=int, default=85, help="Qualite WebP (0-100)")
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        print(f"Dossier introuvable : {args.source}", file=sys.stderr)
        sys.exit(1)
    os.makedirs(args.destination, exist_ok=True)

    files = sorted(f for f in os.listdir(args.source) if f.lower().endswith(EXTENSIONS))
    total_before = total_after = 0
    seen = set()
    for i, name in enumerate(files, 1):
        base = os.path.splitext(name)[0]
        if base.lower() in seen:
            print(f"[{i}/{len(files)}] {name} : ignore (un autre fichier porte deja le nom '{base}')")
            continue
        seen.add(base.lower())

        src = os.path.join(args.source, name)
        dst = os.path.join(args.destination, base + ".webp")
        try:
            compress_image(src, dst, args.taille, args.qualite)
        except Exception as e:
            print(f"[{i}/{len(files)}] {name} : ECHEC ({e})")
            continue
        before, after = os.path.getsize(src), os.path.getsize(dst)
        total_before += before
        total_after += after
        print(f"[{i}/{len(files)}] {name} : {_mo(before)} -> {_mo(after)}")

    print()
    print(f"Total : {_mo(total_before)} -> {_mo(total_after)}")
    print(f"Images compressees dans '{args.destination}/'.")
    print(f"Si tout est bon, supprime (ou deplace) '{args.source}/' et renomme "
          f"'{args.destination}/' en '{args.source}/'.")


if __name__ == "__main__":
    main()
