"""
Maquette numerique de la maison -- relevee sur le plan du constructeur.

Repere : x vers la droite du plan, y vers le haut du plan (cote terrasse),
origine = angle exterieur bas-gauche de la maison. Unites : metres.
z = 0 au sol fini interieur.

Toutes les valeurs ci-dessous proviennent des cotes ecrites sur le plan
(voir les commentaires "PLAN:"). Les rares valeurs deduites (non cotees)
sont marquees "DEDUIT:" avec le raisonnement.
"""

# ---------------------------------------------------------------- hauteurs
CEILING = 2.50          # HYPOTHESE: hauteur sous plafond standard (non cotee sur le plan)
LINTEL = 2.15           # PLAN: baies 2.00/2.15, 3.00/2.15 ; fenetres 1.05 de haut + allege 1.10 = 2.15
SILL = 1.10             # PLAN: "1.10" sous chaque fenetre = allege
DOOR_H = 2.04           # HYPOTHESE: bloc-porte interieur standard 83 x 204
DOOR_W = 0.83
PASSAGE_H = 2.15        # passages libres (sans porte) arases au linteau des baies

EXT_T = 0.34            # DEDUIT: 8.26 (ext) - 7.58 (int) = 0.68 = 2 x 0.34 ; et 4.50 - 3.82 = 0.68
PART_T = 0.07           # DEDUIT: 1.90 + 0.07 + 1.90 = 3.87 ; 3.83 + 0.07 + 3.68 = 7.58

# ---------------------------------------------------------------- emprise
# PLAN: 18.21 x 12.56 hors tout ; corps principal 8.26 de profondeur ;
#       aile droite 4.50 de large ; terrasse 13.09 x 4.20 (SA 54.97 m2)
TOTAL_W = 18.21
TOTAL_D = 12.56
MAIN_D = 8.26
WING_X0 = 13.71         # PLAN: 0.62 + 13.09 = 13.71 (= 18.21 - 4.50)
PORCH_X0 = 10.99        # PLAN: "11.00" arrondi : 98+60+4.01+1.80+2.05+60+95 = 10.99 (et 10.99+2.72+4.50 = 18.21)
PORCH_DEPTH = 0.95      # PLAN: "95" de part et d'autre du porche

FOOTPRINT = [  # contour exterieur (sens trigo)
    (0.00, 0.00), (10.99, 0.00), (10.99, 0.95), (13.71, 0.95), (13.71, 0.00),
    (18.21, 0.00), (18.21, 12.56), (13.71, 12.56), (13.71, 8.26), (0.00, 8.26),
]

TERRACE = (0.62, 13.71, 8.26, 12.46)   # PLAN: 0.62 + 13.09 ; 4.20 de profondeur (0.10 en retrait du pignon)

# ---------------------------------------------------------------- murs
# (nom, x0, x1, y0, y1, type)
WALLS = [
    # --- murs exterieurs (0.34)
    ("ext_gauche",        0.00,  0.34,  0.00,  8.26, "ext"),
    ("ext_avant",         0.34, 10.65,  0.00,  0.34, "ext"),
    ("ext_porche_g",     10.65, 10.99,  0.00,  1.29, "ext"),
    ("ext_porche_fond",  10.99, 13.71,  0.95,  1.29, "ext"),
    ("ext_aile_o_bas",   13.71, 14.05,  0.00,  1.29, "ext"),  # mur hachure = joue droite du porche seulement
    ("ext_aile_avant",   14.05, 18.21,  0.00,  0.34, "ext"),
    ("ext_aile_droite",  17.87, 18.21,  0.34, 12.56, "ext"),
    ("ext_aile_arriere", 13.71, 17.87, 12.22, 12.56, "ext"),
    ("ext_aile_o_haut",  13.71, 14.05,  7.92, 12.22, "ext"),
    ("ext_terrasse",      0.34, 13.71,  7.92,  8.26, "ext"),
    # --- cloisons (0.07)
    ("c_ch1_pieces",      0.34,  4.21,  4.02,  4.09, "int"),  # PLAN: ch. 3.83 / pieces 3.68
    ("c_p3_p2",           2.24,  2.31,  0.34,  4.02, "int"),  # PLAN: 1.90 | 1.90
    ("c_gauche_sejour",   4.21,  4.28,  0.34,  7.92, "int"),  # PLAN: 3.87 ; cuisine 4.55 a partir d'ici
    ("c_cuisine_cellier", 8.83,  8.90,  0.34,  3.27, "int"),  # PLAN: 4.55 ; cellier 1.75
    ("c_cellier_wc",     10.65, 10.72,  1.29,  3.27, "int"),
    ("c_wc_entree",      11.72, 11.79,  1.29,  3.27, "int"),  # PLAN: WC "100" de large
    ("c_nord_cellier_wc", 8.83, 12.24,  3.27,  3.34, "int"),  # DEDUIT: cellier 5.11/1.75 = 2.92 ; WC 1.98/1.00
    ("c_nord_entree_d",  13.27, 13.98,  3.27,  3.34, "int"),  # retour de mur cote aile (passage 12.24-13.27)
    ("c_entree_ch4",     13.98, 14.05,  1.29,  3.40, "int"),  # cloison entree / chambre 11.69
    ("c_ch4_sde",        13.98, 17.87,  3.40,  3.47, "int"),  # PLAN: ch. 3.06
    ("c_sejour_couloir", 13.98, 14.05,  3.47,  7.92, "int"),
    ("c_couloir_est",    15.05, 15.12,  3.47,  9.35, "int"),  # DEDUIT: 3.82 - 2.75 - 0.07 = 1.00 de couloir
    ("c_sde_ch3",        15.12, 17.87,  5.42,  5.49, "int"),  # PLAN: SDE 1.95
    ("c_ch3_ch2",        15.05, 17.87,  9.35,  9.42, "int"),  # PLAN: ch. 3.86
    ("c_couloir_nord",   14.05, 15.05,  8.54,  8.61, "int"),  # DEDUIT: Piece 1 = 5.07 m2 / 1.00
]

# ---------------------------------------------------------------- ouvertures
# (mur, axe, a0, a1, z0, z1, type, info)
#   axe 'x' => a0/a1 sont des abscisses x ; axe 'y' => ordonnees y
OPENINGS = [
    # facade avant (PLAN: 98 | 60/1.05 | 4.01 | 1.80/1.05 | 2.05 | 60/1.05 | 95)
    ("ext_avant", "x", 0.98, 1.58, SILL, LINTEL, "fenetre", "Piece 3 60/1.05"),
    ("ext_avant", "x", 5.59, 7.39, SILL, LINTEL, "fenetre", "Cuisine 1.80/1.05"),
    ("ext_avant", "x", 9.44, 10.04, SILL, LINTEL, "fenetre", "Cellier 60/1.05"),
    # fond du porche (PLAN: 15 | 40/1.05 | 78 | 90/2.15 | 49 = 2.72)
    ("ext_porche_fond", "x", 11.14, 11.54, SILL, LINTEL, "fenetre_depolie", "WC 40/1.05"),
    ("ext_porche_fond", "x", 12.32, 13.22, 0.0, LINTEL, "porte_entree", "Entree 90/2.15"),
    # aile, facade avant (PLAN: 1.87 | 1.20/1.05 | 1.43)
    ("ext_aile_avant", "x", 15.58, 16.78, SILL, LINTEL, "fenetre", "Chambre 11.69 1.20/1.05"),
    # aile, pignon droit (PLAN depuis le haut: 4.40 | 1.20/1.05 | 2.33 | 60/1.05 | 4.03)
    ("ext_aile_droite", "y", 6.96, 8.16, SILL, LINTEL, "fenetre", "Chambre 10.62 1.20/1.05"),
    ("ext_aile_droite", "y", 4.03, 4.63, SILL, LINTEL, "fenetre_depolie", "SDE 60/1.05"),
    # aile, facade arriere (PLAN: 1.80 | 1.20/1.05 | 1.50)
    ("ext_aile_arriere", "x", 15.51, 16.71, SILL, LINTEL, "fenetre", "Chambre 11.51 1.20/1.05"),
    # facade terrasse (PLAN: 62 | 94 | 2.00/2.15 | 1.72 | 3.00/2.15 | 1.71 | 3.00/2.15 | 73)
    ("ext_terrasse", "x", 1.56, 3.56, 0.0, LINTEL, "baie", "Chambre 14.82 2.00/2.15"),
    ("ext_terrasse", "x", 5.28, 8.28, 0.0, LINTEL, "baie", "Sejour 3.00/2.15"),
    ("ext_terrasse", "x", 9.99, 12.99, 0.0, LINTEL, "baie", "Sejour 3.00/2.15"),
    # portes interieures (positions relevees au plan, largeur standard 83)
    ("c_gauche_sejour", "y", 4.17, 5.00, 0.0, DOOR_H, "porte", "Chambre 14.82"),
    ("c_ch1_pieces", "x", 1.17, 1.98, 0.0, DOOR_H, "coulissante", "Chambre -> Piece 3"),
    ("c_cuisine_cellier", "y", 1.01, 1.84, 0.0, DOOR_H, "porte", "Cellier"),
    ("c_wc_entree", "y", 2.11, 2.94, 0.0, DOOR_H, "porte", "WC"),
    ("c_nord_cellier_wc", "x", 12.24, 13.27, 0.0, PASSAGE_H, "passage", "Entree -> sejour"),
    ("c_sejour_couloir", "y", 3.65, 4.55, 0.0, DOOR_H, "coulissante_ouverte", "Sejour -> Piece 1"),
    ("c_couloir_est", "y", 4.47, 5.30, 0.0, DOOR_H, "porte", "SDE"),
    ("c_couloir_est", "y", 5.79, 6.62, 0.0, DOOR_H, "porte", "Chambre 10.62"),
    ("c_couloir_nord", "x", 14.12, 14.95, 0.0, DOOR_H, "porte", "Chambre 11.51"),
    ("c_ch4_sde", "x", 14.12, 14.95, 0.0, DOOR_H, "porte", "Chambre 11.69"),
]

# ---------------------------------------------------------------- pieces (controle des surfaces)
ROOMS = {
    "Chambre 14.82":  [(0.34, 4.21, 4.09, 7.92)],
    "Piece 3 (6.97)": [(0.34, 2.24, 0.34, 4.02)],
    "Piece 2 (6.95)": [(2.31, 4.21, 0.34, 4.02)],
    "Cellier 5.11":   [(8.90, 10.65, 0.34, 3.27)],
    "WC 1.98":        [(10.72, 11.72, 1.29, 3.27)],
    "Chambre 11.69":  [(14.05, 17.87, 0.34, 3.40)],
    "SDE 5.36":       [(15.12, 17.87, 3.47, 5.42)],
    "Chambre 10.62":  [(15.12, 17.87, 5.49, 9.35)],
    "Chambre 11.51":  [(14.05, 17.87, 9.42, 12.22), (14.05, 15.05, 8.61, 9.42)],
    "Piece 1 (5.07)": [(14.05, 15.05, 3.47, 8.54)],
}

PLAN_AREAS = {
    "Chambre 14.82": 14.82, "Piece 3 (6.97)": 6.97, "Piece 2 (6.95)": 6.95,
    "Cellier 5.11": 5.11, "WC 1.98": 1.98, "Chambre 11.69": 11.69, "SDE 5.36": 5.36,
    "Chambre 10.62": 10.62, "Chambre 11.51": 11.51, "Piece 1 (5.07)": 5.07,
}

# ---------------------------------------------------------------- mobilier (positions du plan)
# Le plan du constructeur donne du mobilier indicatif ; on le reprend tel quel
# (centre x, centre y, largeur selon x, profondeur selon y, rotation deg).
FURNITURE = {
    "table_repas":   (6.67, 6.05, 2.00, 1.05, 0),
    "canape_L":      dict(x0=9.85, x1=12.24, y0=4.62, y1=7.70, depth=0.90),
    "fauteuil":      (11.85, 7.25, 0.85, 0.85, 45),
    "table_basse":   (11.33, 6.27, 0.70, 0.70, 0),
    "meuble_tv":     (13.73, 6.60, 0.45, 1.80, 0),
    "ilot":          (7.37, 2.72, 2.56, 1.10, 0),     # PLAN: ilot 6.09 -> 8.65, 2.17 -> 3.27
    "plan_travail":  dict(x0=4.28, x1=8.83, depth=0.65),  # le long de la facade, evier sous la fenetre 1.80
    "colonne_four_frigo": (8.53, 0.66, 0.60, 0.65, 0),  # NB: le plan dessine aussi une colonne DEVANT la
                                                          # porte du cellier ; elle est retiree pour garder l'acces
    "lit_ch1":       (1.34, 6.00, 2.00, 1.60, 0),     # tete de lit contre le mur gauche
    "lit_ch2":       (16.87, 10.95, 2.00, 1.60, 0),   # chambre 11.51, tete contre le pignon droit
    "placard_ch2":   (14.33, 11.40, 0.55, 1.60, 0),
    "lit_ch3":       (16.45, 8.35, 1.60, 2.00, 0),    # chambre 10.62, tete contre la cloison nord
    "placard_ch3":   (17.07, 5.79, 1.60, 0.60, 0),
    "lit_ch4":       (16.60, 2.40, 1.60, 2.00, 0),    # chambre 11.69, tete contre la cloison nord
    "placard_ch4":   (14.35, 1.15, 0.60, 1.50, 0),
}

LIVING_POLY = [  # piece de vie (sejour + cuisine + entree), faces interieures
    (4.28, 0.34), (8.83, 0.34), (8.83, 3.34), (11.79, 3.34), (11.79, 1.29), (13.98, 1.29), (13.98, 7.92), (4.28, 7.92),
]


def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


if __name__ == "__main__":
    # controle rapide des surfaces
    for name, rects in ROOMS.items():
        a = sum((x1 - x0) * (y1 - y0) for x0, x1, y0, y1 in rects)
        print(f"{name:18s} modele {a:6.2f} m2   plan {PLAN_AREAS[name]:6.2f} m2   ecart {a - PLAN_AREAS[name]:+.2f}")
    a = poly_area(LIVING_POLY) - 0.07 * (12.24 - 11.79) - 0.07 * (13.98 - 13.27)
    print(f"{'Piece de vie':18s} modele {a:6.2f} m2   plan  62.51 m2   ecart {a - 62.51:+.2f}")
