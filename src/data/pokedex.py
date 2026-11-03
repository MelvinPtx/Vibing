"""Données Pokémon : GÉNÉRÉ par tools/import_pokemon_data.py (ne pas modifier à la main).

Sources : pokemondb/database (types, stats, expérience de base, chiffres des capacités) et
PokeAPI/pokeapi (capacités apprises par niveau dans Écarlate/Violet, noms français, évolutions).
"""

# identifiant -> {nom FR, type, catégorie, puissance, précision (101 = ne rate jamais), PP, priorité, description FR}
MOVES = {
    'acrobatics': {"name": 'Acrobatie', "type": 'flying', "category": 'physical', "power": 55, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Attaque agile. Si le lanceur ne tient pas d'objet, l'attaque inflige davantage de dégâts."},
    'air-slash': {"name": "Lame d'Air", "type": 'flying', "category": 'special', "power": 75, "accuracy": 95, "pp": 15, "priority": 0, "desc": "Le lanceur attaque avec une lame d'air qui fend tout. Peut aussi apeurer l'ennemi."},
    'aqua-cutter': {"name": "Tranch'Aqua", "type": 'water', "category": 'physical', "power": 70, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Le lanceur projette de l'eau pressurisée qui entaille la cible comme une lame. Taux de critiques élevé."},
    'aqua-jet': {"name": 'Aqua-Jet', "type": 'water', "category": 'physical', "power": 40, "accuracy": 100, "pp": 20, "priority": 1, "desc": "Le lanceur fonce sur l'ennemi si rapidement qu'on parvient à peine à le discerner. Frappe en priorité."},
    'aqua-step': {"name": 'Danse Aquatique', "type": 'water', "category": 'physical', "power": 80, "accuracy": 100, "pp": 10, "priority": 0, "desc": 'Le lanceur se joue de la cible et lui inflige des dégâts avec ses pas de danse gracieux et légers. Cette capacité augmente la Vitesse du lanceur.'},
    'bite': {"name": 'Morsure', "type": 'dark', "category": 'physical', "power": 60, "accuracy": 100, "pp": 25, "priority": 0, "desc": "L'ennemi est mordu par de tranchantes canines. Peut l'apeurer."},
    'close-combat': {"name": 'Close Combat', "type": 'fighting', "category": 'physical', "power": 120, "accuracy": 100, "pp": 5, "priority": 0, "desc": 'Le lanceur combat au corps à corps sans se protéger. Baisse aussi sa Défense et sa Défense Spéciale.'},
    'double-hit': {"name": 'Coup Double', "type": 'normal', "category": 'physical', "power": 35, "accuracy": 90, "pp": 10, "priority": 0, "desc": "Le lanceur frappe l'ennemi deux fois d'affilée à l'aide de sa queue, de lianes ou d'un autre membre."},
    'ember': {"name": 'Flammèche', "type": 'fire', "category": 'special', "power": 40, "accuracy": 100, "pp": 25, "priority": 0, "desc": "L'ennemi est attaqué par une faible flamme. Peut aussi le brûler."},
    'energy-ball': {"name": 'Éco-Sphère', "type": 'grass', "category": 'special', "power": 90, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Utilise les pouvoirs de la nature pour attaquer l'ennemi. Peut aussi baisser sa Défense Spéciale."},
    'fire-blast': {"name": 'Déflagration', "type": 'fire', "category": 'special', "power": 110, "accuracy": 85, "pp": 5, "priority": 0, "desc": "Un déluge de flammes ardentes submerge l'ennemi. Peut aussi le brûler."},
    'flamethrower': {"name": 'Lance-Flammes', "type": 'fire', "category": 'special', "power": 90, "accuracy": 100, "pp": 15, "priority": 0, "desc": "L'ennemi reçoit un torrent de flammes. Peut aussi le brûler."},
    'flower-trick': {"name": 'Magie Florale', "type": 'grass', "category": 'physical', "power": 70, "accuracy": 101, "pp": 10, "priority": 0, "desc": "Le lanceur attaque en jetant un bouquet de fleurs piégé sur la cible. N'échoue jamais et inflige toujours un coup critique."},
    'hex': {"name": 'Châtiment', "type": 'ghost', "category": 'special', "power": 65, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Attaque acharnée qui cause davantage de dégâts à l'ennemi s'il a un problème de statut."},
    'hyper-voice': {"name": 'Mégaphone', "type": 'normal', "category": 'special', "power": 90, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Le lanceur pousse un cri dont l'écho terrifiant a le pouvoir d'infliger des dégâts à l'ennemi."},
    'incinerate': {"name": 'Calcination', "type": 'fire', "category": 'special', "power": 60, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Des flammes calcinent l'ennemi. S'il tient un objet, une Baie par exemple, celui-ci est brûlé et devient inutilisable."},
    'knock-off': {"name": 'Sabotage', "type": 'dark', "category": 'physical', "power": 65, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Fait plus de dégâts aux cibles qui tiennent un objet. De plus, fait tomber cet objet et empêche la cible de l'utiliser jusqu'à la fin du combat."},
    'leaf-storm': {"name": 'Tempête Verte', "type": 'grass', "category": 'special', "power": 130, "accuracy": 90, "pp": 5, "priority": 0, "desc": "Invoque une tempête de feuilles acérées. Le contrecoup réduit beaucoup l'Attaque Spéciale du lanceur."},
    'leafage': {"name": 'Feuillage', "type": 'grass', "category": 'physical', "power": 40, "accuracy": 100, "pp": 40, "priority": 0, "desc": "Le lanceur attaque l'ennemi avec des feuilles."},
    'lick': {"name": 'Léchouille', "type": 'ghost', "category": 'physical', "power": 30, "accuracy": 100, "pp": 30, "priority": 0, "desc": "Un grand coup de langue qui inflige des dégâts à l'ennemi. Peut aussi le paralyser."},
    'liquidation': {"name": 'Aqua-Brèche', "type": 'water', "category": 'physical', "power": 85, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Le lanceur utilise la force de l'eau pour attaquer. Peut aussi baisser la Défense de la cible."},
    'low-sweep': {"name": 'Balayette', "type": 'fighting', "category": 'physical', "power": 65, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Un coup rapide qui affecte la mobilité de l'ennemi et diminue sa Vitesse."},
    'magical-leaf': {"name": 'Feuille Magik', "type": 'grass', "category": 'special', "power": 60, "accuracy": 101, "pp": 20, "priority": 0, "desc": "Le lanceur disperse d'étranges feuilles qui poursuivent l'ennemi. N'échoue jamais."},
    'mega-kick': {"name": 'Ultimawashi', "type": 'normal', "category": 'physical', "power": 120, "accuracy": 75, "pp": 5, "priority": 0, "desc": "Un coup de pied surpuissant qui frappe l'ennemi."},
    'night-slash': {"name": 'Tranche-Nuit', "type": 'dark', "category": 'physical', "power": 70, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Le lanceur lacère l'ennemi à la première occasion. Taux de critiques élevé."},
    'overheat': {"name": 'Surchauffe', "type": 'fire', "category": 'special', "power": 130, "accuracy": 90, "pp": 5, "priority": 0, "desc": "Attaque l'ennemi à pleine puissance. Le contrecoup baisse beaucoup l'Attaque Spéciale du lanceur."},
    'play-rough': {"name": 'Câlinerie', "type": 'fairy', "category": 'physical', "power": 90, "accuracy": 90, "pp": 10, "priority": 0, "desc": "Attaque l'ennemi avec un câlin. Peut diminuer son Attaque."},
    'pound': {"name": "Écras'Face", "type": 'normal', "category": 'physical', "power": 40, "accuracy": 100, "pp": 35, "priority": 0, "desc": "Écrase l'ennemi avec les pattes avant ou la queue, par exemple."},
    'quick-attack': {"name": 'Vive-Attaque', "type": 'normal', "category": 'physical', "power": 40, "accuracy": 100, "pp": 30, "priority": 1, "desc": "Le lanceur fonce sur l'ennemi si rapidement qu'on parvient à peine à le discerner. Frappe en priorité."},
    'round': {"name": 'Chant Canon', "type": 'normal', "category": 'special', "power": 60, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Le lanceur attaque l'ennemi en chantant. Si plusieurs Pokémon déclenchent cette attaque à la suite, l'effet augmente."},
    'scratch': {"name": 'Griffe', "type": 'normal', "category": 'physical', "power": 40, "accuracy": 100, "pp": 35, "priority": 0, "desc": "Lacère l'ennemi avec des griffes acérées pour lui infliger des dégâts."},
    'seed-bomb': {"name": 'Canon Graine', "type": 'grass', "category": 'physical', "power": 80, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Le lanceur fait pleuvoir un déluge de graines explosives sur l'ennemi."},
    'shadow-ball': {"name": "Ball'Ombre", "type": 'ghost', "category": 'special', "power": 80, "accuracy": 100, "pp": 15, "priority": 0, "desc": "Projette une grande ombre sur l'ennemi. Peut aussi faire baisser sa Défense Spéciale."},
    'slash': {"name": 'Tranche', "type": 'normal', "category": 'physical', "power": 70, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Un coup de griffe ou autre tranche l'ennemi. Taux de critiques élevé."},
    'snarl': {"name": 'Aboiement', "type": 'dark', "category": 'special', "power": 55, "accuracy": 95, "pp": 15, "priority": 0, "desc": "Le lanceur hurle sur l'ennemi. Baisse l'Attaque Spéciale de l'ennemi."},
    'tackle': {"name": 'Charge', "type": 'normal', "category": 'physical', "power": 40, "accuracy": 100, "pp": 35, "priority": 0, "desc": "Le lanceur charge l'ennemi et le percute de tout son poids."},
    'torch-song': {"name": 'Chant Flamboyant', "type": 'fire', "category": 'special', "power": 80, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Le lanceur carbonise la cible en projetant sur elle de vives flammes créées par un chant. Cette capacité augmente l'Attaque Spéciale du lanceur."},
    'u-turn': {"name": 'Demi-Tour', "type": 'bug', "category": 'physical', "power": 70, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Après son attaque, le lanceur revient à toute vitesse et change de place avec un Pokémon de l'équipe prêt au combat."},
    'water-gun': {"name": 'Pistolet à O', "type": 'water', "category": 'special', "power": 40, "accuracy": 100, "pp": 25, "priority": 0, "desc": "De l'eau est projetée avec force sur l'ennemi."},
    'water-pulse': {"name": 'Vibraqua', "type": 'water', "category": 'special', "power": 60, "accuracy": 100, "pp": 20, "priority": 0, "desc": "Le lanceur envoie un puissant jet d'eau sur l'ennemi. Peut le rendre confus."},
    'wave-crash': {"name": 'Aquatacle', "type": 'water', "category": 'physical', "power": 120, "accuracy": 100, "pp": 10, "priority": 0, "desc": "Le lanceur se recouvre entièrement d'eau avant de charger sa cible. Cela blesse aussi gravement le lanceur."},
    'wing-attack': {"name": 'Cru-Ailes', "type": 'flying', "category": 'physical', "power": 60, "accuracy": 100, "pp": 35, "priority": 0, "desc": "L'ennemi est frappé par de larges ailes déployées pour infliger des dégâts."},
}

# n° national -> nom, types, stats de base, taux de croissance, expérience de base
POKEMON = {
    906: {"name": 'Sprigatito', "types": ('grass',), "stats": {"hp": 40, "attack": 61, "defense": 54, "spatk": 45, "spdef": 45, "speed": 65}, "growth": 'medium slow', "base_exp": 62},
    907: {"name": 'Floragato', "types": ('grass',), "stats": {"hp": 61, "attack": 80, "defense": 63, "spatk": 60, "spdef": 63, "speed": 83}, "growth": 'medium slow', "base_exp": 144},
    908: {"name": 'Meowscarada', "types": ('grass', 'dark'), "stats": {"hp": 76, "attack": 110, "defense": 70, "spatk": 81, "spdef": 70, "speed": 123}, "growth": 'medium slow', "base_exp": 265},
    909: {"name": 'Fuecoco', "types": ('fire',), "stats": {"hp": 67, "attack": 45, "defense": 59, "spatk": 63, "spdef": 40, "speed": 36}, "growth": 'medium slow', "base_exp": 62},
    910: {"name": 'Crocalor', "types": ('fire',), "stats": {"hp": 81, "attack": 55, "defense": 78, "spatk": 90, "spdef": 58, "speed": 49}, "growth": 'medium slow', "base_exp": 144},
    911: {"name": 'Skeledirge', "types": ('fire', 'ghost'), "stats": {"hp": 104, "attack": 75, "defense": 100, "spatk": 110, "spdef": 75, "speed": 66}, "growth": 'medium slow', "base_exp": 265},
    912: {"name": 'Quaxly', "types": ('water',), "stats": {"hp": 55, "attack": 65, "defense": 45, "spatk": 50, "spdef": 45, "speed": 50}, "growth": 'medium slow', "base_exp": 62},
    913: {"name": 'Quaxwell', "types": ('water',), "stats": {"hp": 70, "attack": 85, "defense": 65, "spatk": 65, "spdef": 60, "speed": 65}, "growth": 'medium slow', "base_exp": 144},
    914: {"name": 'Quaquaval', "types": ('water', 'fighting'), "stats": {"hp": 85, "attack": 120, "defense": 80, "spatk": 85, "spdef": 75, "speed": 85}, "growth": 'medium slow', "base_exp": 265},
    19: {"name": 'Rattata', "types": ('normal',), "stats": {"hp": 30, "attack": 56, "defense": 35, "spatk": 25, "spdef": 35, "speed": 72}, "growth": 'medium fast', "base_exp": 51},
    41: {"name": 'Zubat', "types": ('poison', 'flying'), "stats": {"hp": 40, "attack": 45, "defense": 35, "spatk": 30, "spdef": 40, "speed": 55}, "growth": 'medium fast', "base_exp": 49},
    74: {"name": 'Geodude', "types": ('rock', 'ground'), "stats": {"hp": 40, "attack": 80, "defense": 100, "spatk": 30, "spdef": 30, "speed": 20}, "growth": 'medium slow', "base_exp": 60},
    92: {"name": 'Gastly', "types": ('ghost', 'poison'), "stats": {"hp": 30, "attack": 35, "defense": 30, "spatk": 100, "spdef": 35, "speed": 80}, "growth": 'medium slow', "base_exp": 62},
    100: {"name": 'Voltorb', "types": ('electric',), "stats": {"hp": 40, "attack": 30, "defense": 50, "spatk": 55, "spdef": 55, "speed": 100}, "growth": 'medium fast', "base_exp": 66},
    95: {"name": 'Onix', "types": ('rock', 'ground'), "stats": {"hp": 35, "attack": 45, "defense": 160, "spatk": 30, "spdef": 45, "speed": 70}, "growth": 'medium fast', "base_exp": 77},
    94: {"name": 'Gengar', "types": ('ghost', 'poison'), "stats": {"hp": 60, "attack": 65, "defense": 60, "spatk": 130, "spdef": 75, "speed": 110}, "growth": 'medium slow', "base_exp": 250},
}

# n° national -> {identifiant de capacité: niveau d'apprentissage} (Écarlate/Violet, par niveau ; 0 = à l'évolution)
LEARNSET = {
    906: {'leafage': 1, 'scratch': 1, 'bite': 7, 'magical-leaf': 13, 'quick-attack': 15, 'seed-bomb': 17, 'u-turn': 21, 'slash': 28, 'energy-ball': 32, 'play-rough': 36},
    907: {'leafage': 1, 'scratch': 1, 'bite': 7, 'magical-leaf': 13, 'quick-attack': 15, 'seed-bomb': 20, 'u-turn': 24, 'slash': 33, 'energy-ball': 38, 'play-rough': 42, 'leaf-storm': 46},
    908: {'flower-trick': 0, 'leafage': 1, 'scratch': 1, 'bite': 7, 'magical-leaf': 13, 'quick-attack': 15, 'seed-bomb': 20, 'u-turn': 24, 'slash': 33, 'night-slash': 38, 'energy-ball': 42, 'play-rough': 47, 'knock-off': 52, 'leaf-storm': 64},
    909: {'ember': 1, 'tackle': 1, 'round': 7, 'bite': 12, 'incinerate': 15, 'snarl': 21, 'flamethrower': 28, 'hyper-voice': 32, 'fire-blast': 36},
    910: {'ember': 1, 'tackle': 1, 'lick': 7, 'round': 10, 'bite': 12, 'incinerate': 17, 'snarl': 24, 'flamethrower': 32, 'hyper-voice': 38, 'fire-blast': 47},
    911: {'torch-song': 0, 'ember': 1, 'tackle': 1, 'lick': 7, 'round': 10, 'bite': 15, 'incinerate': 17, 'snarl': 24, 'flamethrower': 32, 'shadow-ball': 38, 'hyper-voice': 42, 'hex': 47, 'fire-blast': 58, 'overheat': 64},
    912: {'pound': 1, 'water-gun': 1, 'wing-attack': 10, 'aqua-jet': 13, 'double-hit': 17, 'aqua-cutter': 21, 'air-slash': 24, 'acrobatics': 31, 'liquidation': 35},
    913: {'double-hit': 1, 'pound': 1, 'water-gun': 1, 'wing-attack': 10, 'aqua-jet': 13, 'water-pulse': 17, 'low-sweep': 19, 'aqua-cutter': 23, 'air-slash': 27, 'acrobatics': 38, 'liquidation': 43},
    914: {'aqua-step': 0, 'double-hit': 1, 'pound': 1, 'water-gun': 1, 'wing-attack': 10, 'aqua-jet': 13, 'low-sweep': 17, 'water-pulse': 17, 'aqua-cutter': 21, 'air-slash': 27, 'mega-kick': 38, 'acrobatics': 43, 'liquidation': 47, 'close-combat': 58, 'wave-crash': 64},
}

# forme -> (forme suivante, niveau d'évolution)
EVOLUTIONS = {906: (907, 16), 907: (908, 36), 909: (910, 16), 910: (911, 36), 912: (913, 16), 913: (914, 36)}
