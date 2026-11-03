"""Génère src/data/pokedex.py à partir de données publiques sur GitHub :

- pokemondb/database : types, stats de base, taux de croissance, expérience de base, et chiffres
  de chaque capacité (type, catégorie, puissance, précision, PP, priorité) ;
- PokeAPI/pokeapi (CSV) : ce que la base pokemondb ne contient pas : capacités apprises par niveau
  dans Écarlate/Violet, noms français des capacités, leur description officielle française, niveaux d'évolution.

    python -m tools.import_pokemon_data

Le fichier généré est commité : le jeu n'a besoin ni de réseau ni de PyYAML pour tourner. Seul cet outil
a besoin de PyYAML. Note : pokemon-forms.yaml de pokemondb est mal formé à la ligne 31354 (YAML invalide) ;
l'outil n'analyse donc que les entrées utiles, bloc par bloc.
"""
import csv
import io
import re
import sys
import urllib.request
from pathlib import Path

import yaml

DB = "https://raw.githubusercontent.com/pokemondb/database/master/data"
API = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv"
OUT = Path(__file__).resolve().parents[1] / "src" / "data" / "pokedex.py"
VERSION_GROUP_SV, LANG_FR, METHOD_LEVEL_UP = 25, 5, 1

# Les 9 formes jouables, puis les ennemis / boss dont on a besoin de l'expérience de base.
PLAYABLE = ["sprigatito", "floragato", "meowscarada", "fuecoco", "crocalor", "skeledirge",
            "quaxly", "quaxwell", "quaquaval"]
OTHERS = ["rattata", "zubat", "geodude", "gastly", "voltorb", "onix", "gengar"]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read().decode("utf-8")


def lenient_blocks(text: str, wanted) -> dict:
    """Découpe un YAML à clés de premier niveau en blocs et n'analyse que ceux demandés."""
    blocks, key, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^([a-z0-9-]+):\s*$", line)
        if m:
            if key in wanted:
                blocks[key] = "\n".join(buf)
            key, buf = m.group(1), []
        elif key is not None:
            buf.append(line)
    if key in wanted:
        blocks[key] = "\n".join(buf)
    return {k: yaml.safe_load(v) for k, v in blocks.items()}


def main() -> None:
    forms = lenient_blocks(fetch(f"{DB}/pokemon-forms.yaml"), set(PLAYABLE + OTHERS))
    moves_db = yaml.safe_load(fetch(f"{DB}/moves.yaml"))
    pokemon_db = yaml.safe_load(fetch(f"{DB}/pokemon.yaml"))
    dex = {k: pokemon_db[k]["national"] for k in PLAYABLE + OTHERS}

    move_rows = {int(r["id"]): r["identifier"] for r in csv.DictReader(io.StringIO(fetch(f"{API}/moves.csv")))}
    fr = {int(r["move_id"]): r["name"].replace("’", "'")
          for r in csv.DictReader(io.StringIO(fetch(f"{API}/move_names.csv"))) if int(r["local_language_id"]) == LANG_FR}
    flavor = {}                                   # description officielle FR : Écarlate/Violet, sinon la plus récente
    for r in csv.DictReader(io.StringIO(fetch(f"{API}/move_flavor_text.csv"))):
        if int(r["language_id"]) == LANG_FR:
            mid, vg = int(r["move_id"]), int(r["version_group_id"])
            if mid not in flavor or vg > flavor[mid][0]:
                flavor[mid] = (vg, " ".join(r["flavor_text"].replace("\f", " ").split()).replace("’", "'"))
    playable_ids = {dex[k] for k in PLAYABLE}
    learnset = {d: {} for d in playable_ids}
    for r in csv.DictReader(io.StringIO(fetch(f"{API}/pokemon_moves.csv"))):
        d = int(r["pokemon_id"])
        if d in playable_ids and int(r["version_group_id"]) == VERSION_GROUP_SV and int(r["pokemon_move_method_id"]) == METHOD_LEVEL_UP:
            ident = move_rows[int(r["move_id"])]
            if moves_db.get(ident, {}).get("category") != "status":
                learnset[d][ident] = int(r["level"] or 0)
    evolutions = {}
    for r in csv.DictReader(io.StringIO(fetch(f"{API}/pokemon_evolution.csv"))):
        if r["minimum_level"] and int(r["evolved_species_id"]) in playable_ids and int(r["evolution_trigger_id"]) == 1:
            evolutions[int(r["evolved_species_id"])] = int(r["minimum_level"])
    evo_from = {}
    for r in csv.DictReader(io.StringIO(fetch(f"{API}/pokemon_species.csv"))):
        if r["evolves_from_species_id"] and int(r["id"]) in playable_ids:
            evo_from[int(r["id"])] = int(r["evolves_from_species_id"])
    chain = {evo_from[d]: (d, evolutions[d]) for d in evo_from if d in evolutions}

    used = sorted({m for ls in learnset.values() for m in ls})
    name_to_id = {v: k for k, v in move_rows.items()}
    lines = ['"""Données Pokémon : GÉNÉRÉ par tools/import_pokemon_data.py (ne pas modifier à la main).',
             "", "Sources : pokemondb/database (types, stats, expérience de base, chiffres des capacités) et",
             "PokeAPI/pokeapi (capacités apprises par niveau dans Écarlate/Violet, noms français, évolutions).",
             '"""', "", "# identifiant -> {nom FR, type, catégorie, puissance, précision (101 = ne rate jamais), PP, priorité, description FR}",
             "MOVES = {"]
    for m in used:
        d = moves_db[m]
        lines.append(f'    {m!r}: {{"name": {fr[name_to_id[m]]!r}, "type": {d["type"]!r}, "category": {d["category"]!r}, '
                     f'"power": {d["power"]}, "accuracy": {d["accuracy"]}, "pp": {d["pp"]}, "priority": {d["priority"]}, '
                     f'"desc": {flavor.get(name_to_id[m], (0, ""))[1]!r}}},')
    lines += ["}", "", "# n° national -> nom, types, stats de base, taux de croissance, expérience de base", "POKEMON = {"]
    for k in PLAYABLE + OTHERS:
        e, s = forms[k], forms[k]["stats"]
        types = tuple(t for t in (e["type1"], e.get("type2")) if t)
        lines.append(f'    {dex[k]}: {{"name": {pokemon_db[k]["name"]!r}, "types": {types!r}, '
                     f'"stats": {{"hp": {s["hp"]}, "attack": {s["attack"]}, "defense": {s["defense"]}, "spatk": {s["spatk"]}, '
                     f'"spdef": {s["spdef"]}, "speed": {s["speed"]}}}, "growth": {e["growth-rate"]!r}, "base_exp": {e["base-exp"]}}},')
    lines += ["}", "", "# n° national -> {identifiant de capacité: niveau d'apprentissage} (Écarlate/Violet, par niveau ; 0 = à l'évolution)",
              "LEARNSET = {"]
    for d in sorted(learnset):
        items = ", ".join(f"{m!r}: {l}" for m, l in sorted(learnset[d].items(), key=lambda kv: (kv[1], kv[0])))
        lines.append(f"    {d}: {{{items}}},")
    lines += ["}", "", "# forme -> (forme suivante, niveau d'évolution)", f"EVOLUTIONS = {dict(sorted(chain.items()))!r}", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT} : {len(used)} capacités, {len(PLAYABLE + OTHERS)} Pokémon, évolutions {chain}")


if __name__ == "__main__":
    sys.exit(main())
