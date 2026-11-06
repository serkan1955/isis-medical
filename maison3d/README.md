# Maison : maquette 3D et rendus photoréalistes

Ce dossier contient la maquette 3D de la maison, reconstruite à partir du plan du constructeur,
et les scripts qui produisent les rendus photoréalistes de l'intérieur (Blender 5.2 / Cycles).

## Respect des cotes

Toutes les dimensions viennent des cotes écrites sur le plan : `spec.py` cite la cote d'origine
à côté de chaque valeur.

- **Emprise hors tout** : 18,21 × 12,56 m. Le corps principal fait 8,26 m de profondeur, l'aile 4,50 m de large.
  La terrasse fait 13,09 × 4,20 m.
- **Murs extérieurs : 34 cm.** On le déduit du plan : 8,26 − 7,58 = 0,68, et 4,50 − 3,82 = 0,68.
- **Cloisons : 7 cm.** Là aussi c'est déduit : 1,90 + 0,07 + 1,90 = 3,87.
- **Fenêtres et baies** : largeur, hauteur et allège (1,10) sont celles du plan, toutes alignées à 2,15 m.
- **Surfaces** : celles de la maquette sont égales aux surfaces SH du plan (`python3 spec.py`).

| Pièce | Maquette | Plan |
|---|---|---|
| Pièce de vie | 62,48 | 62,51 |
| Chambre | 14,82 | 14,82 |
| Chambre | 11,69 | 11,69 |
| Chambre | 11,51 | 11,51 |
| Chambre | 10,62 | 10,62 |
| SDE | 5,36 | 5,36 |
| Pièce 1 | 5,07 | 5,07 |
| Cellier | 5,13 | 5,11 |
| WC | 1,98 | 1,98 |

`overlay_check.py` projette la maquette sur la photo du plan (par homographie) pour un contrôle visuel.
Le résultat est `controle/superposition_plan.png`.

Une relecture indépendante a comparé la maquette au plan et corrigé trois points :

- La cloison entre l'entrée et la chambre 11,69.
- La largeur du passage entre l'entrée et le séjour : 12,24 → 13,27.
- Deux portes coulissantes : chambre → pièce 3, et séjour → pièce 1.

## Hypothèses (non cotées sur le plan)

- La hauteur sous plafond est de 2,50 m, les portes intérieures font 83 × 204.
- L'orientation est relevée sur la rose des vents : la terrasse regarde l'Ouest-Sud-Ouest.
  Les rendus sont donc éclairés par un soleil de fin d'après-midi qui entre par les baies.
- Les volets roulants (VR MOT) ont des coffres invisibles, de type tunnel.
- Finitions, mobilier et décoration sont un choix contemporain neutre ; on peut les changer facilement.
  Le mobilier reprend les positions dessinées sur le plan, à deux écarts près :
  - Sur le plan, une colonne de cuisine est dessinée **devant la porte du cellier**. Elle a été retirée
    pour garder l'accès ; il reste seulement une colonne four à l'angle.
  - Le lit de la chambre 14,82 est posé contre le mur. Sur le plan il en est décollé d'environ 50 cm.
- La **pièce 2** n'a ni porte ni fenêtre sur le plan. Rien n'a été inventé, et elle n'est pas rendue.

## Utilisation

```bash
pip install bpy==5.2.3            # Blender en module Python
export MAISON_ASSETS=/chemin/assets   # textures.json, models.json, hdri/ (Poly Haven, CC0)
python build.py --views all --samples 128 --res 1600x1067 --out renders/
python build.py --views 03_cuisine --samples 32 --res 800x533   # aperçu rapide
```

Les points de vue sont définis dans `views.py` : position, direction, focale et exposition.

| Fichier | Rôle |
|---|---|
| `spec.py` | Relevé du plan : murs, ouvertures, pièces, mobilier |
| `archi.py` | Sols, murs percés, menuiseries alu, portes, toiture, terrasse |
| `interior.py` | Cuisine, séjour, chambres, salle d'eau, entrée, terrasse |
| `scene.py` | Réglages Cycles, éclairage HDRI orienté, portails de lumière, caméras |
| `assets/` | Manifestes des textures et modèles Poly Haven (CC0) et scripts de téléchargement |
