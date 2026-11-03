"""Télécharge les sprites PMDCollab/SpriteCollab utilisés par le jeu dans assets/sprites/.

    python -m tools.fetch_sprites            # toutes les espèces de src/species.py
    python -m tools.fetch_sprites 25 6       # ajoute/force d'autres n° de Pokédex
    python -m tools.fetch_sprites --force    # retélécharge même si déjà présent

Source : https://github.com/PMDCollab/SpriteCollab (les mêmes fichiers que sprites.pmdcollab.org).
Licence des sprites : CC BY-NC 4.0 (non commercial, attribution obligatoire) ->
le script génère aussi assets/sprites/CREDITS.md à partir des credits.txt de chaque espèce.
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

from src.species import ALL_DEX, NAMES

RAW = "https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master"
OUT = Path(__file__).resolve().parents[1] / "assets" / "sprites"
ANIMS = ("Idle", "Walk", "Attack", "Swing", "Shoot", "Hurt")   # planches utilisées par le jeu


def get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch_species(dex: int, force: bool) -> list[str]:
    d = OUT / f"{dex:04d}"
    d.mkdir(parents=True, exist_ok=True)
    got = []
    files = ["AnimData.xml", "credits.txt"] + [f"{a}-Anim.png" for a in ANIMS]
    for name in files:
        target = d / name
        if target.exists() and not force:
            got.append(name)
            continue
        data = get(f"{RAW}/sprite/{dex:04d}/{name}")
        if data is None:
            if name == "AnimData.xml":
                raise SystemExit(f"Pas de sprite pour le n° {dex}")
            continue
        target.write_bytes(data)
        got.append(name)
    return got


def write_credits(dexes) -> None:
    names = {}
    raw = get(f"{RAW}/credit_names.txt") or b""
    for line in raw.decode("utf-8", "replace").splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 3:
            names[p[1]] = (p[0], p[2])
    lines = [
        "# Crédits des sprites",
        "",
        "Sprites issus de [PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab) "
        "(https://sprites.pmdcollab.org/), sous licence "
        "[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) : usage **non commercial** "
        "uniquement, avec attribution. Les Pokémon sont © Nintendo / Creatures Inc. / GAME FREAK inc. ; "
        "ce projet est un prototype de fan, sans but lucratif.",
        "",
    ]
    for dex in sorted(dexes):
        f = OUT / f"{dex:04d}" / "credits.txt"
        authors = []
        if f.exists():
            for row in f.read_text(encoding="utf-8", errors="replace").splitlines():
                p = row.split("\t")
                if len(p) >= 3 and p[2] == "CUR" and p[1] not in authors:
                    authors.append(p[1])
        shown = []
        for a in authors:
            n, contact = names.get(a, (a, ""))
            shown.append(f"{n} ({contact})" if contact.startswith("http") else n)
        lines.append(f"- **#{dex:04d} {NAMES.get(dex, '?')}** : " + (", ".join(shown) or "non renseigné"))
    (OUT / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv) -> None:
    force = "--force" in argv
    extra = [int(a) for a in argv if a.isdigit()]
    dexes = sorted(set(ALL_DEX) | set(extra))
    for dex in dexes:
        got = fetch_species(dex, force)
        print(f"#{dex:04d} {NAMES.get(dex, ''):<10} {len(got)} fichiers")
    write_credits(dexes)
    print(f"Crédits : {OUT / 'CREDITS.md'}")


if __name__ == "__main__":
    main(sys.argv[1:])
