# FreeCAD-GDT : rapport de tests

## Environnement

| | |
|---|---|
| FreeCAD | 1.1.3 (R20260725), `C:\Logiciel_Cetim\FreeCAD 1.1` |
| Python / Qt / PySide | 3.11.14 / 6.8.3 / PySide6 6.8.3 |
| Langue de l'interface | Français (`Gui.getLocale()` = `French`) |
| Système | Windows 11 Enterprise 10.0.26200 |
| Installation testée | `C:\Users\lalliard\AppData\Roaming\FreeCAD\v1-1\Mod\FreeCAD-GDT`, copie filtrée par `tools/install_mod.py` |
| **Non testé** | FreeCAD 1.0 et Linux / macOS (non disponibles sur ce poste). Le code n'utilise que des API présentes depuis la 1.0, et prévoit un repli vers les API 0.2x pour le plan de travail et les couleurs, mais **cela n'a pas été vérifié par exécution**. |

## Méthode

Une seule commande installe le MOD, lance FreeCAD avec l'interface graphique et exécute le scénario :

```
"C:\Logiciel_Cetim\FreeCAD 1.1\bin\python.exe" tools\run_gui_tests.py --freecad "C:\Logiciel_Cetim\FreeCAD 1.1\bin\FreeCAD.exe" --label <nom> --out Modernisation\tests\<nom>_results.json
```

`tests/gui_test_gdt.py` s'exécute **dans FreeCAD** :

- il pilote les vraies commandes et les vrais panneaux de tâches : sélection de faces, clic sur le bouton de création, choix dans les listes ;
- il fournit le point d'ancrage par le rappel de saisie de coordonnées du sélecteur de points Draft (`draftToolBar.pointcallback`), comme si l'utilisateur tapait les coordonnées ;
- il capture la vue Rapport (« Report view ») à chaque étape. Toute ligne `Traceback`, `Error` ou `Exception` fait passer un test réussi en WARN.

Un test est en **SKIP** si son prérequis a échoué, et en **WARN** s'il réussit avec des messages en console.

Des mesures ponctuelles ont complété ces tests : scripts sous `freecadcmd` pour l'ouverture sans interface, les placements dans un Body ou un Part et la dérive de `Plaque.FCStd`, et scripts dans l'interface pour les couleurs, les signaux `InputField`, les lambdas PySide6, les polices et le rendu du code d'origine. Ils sont décrits dans le [journal](03_Journal_Modifications.md).

## Catalogue des tests

| Test | Vérifie | Exigence du cahier des charges |
|---|---|---|
| T24 | Aucun module du MOD n'est importé au démarrage de FreeCAD | Chargement du workbench |
| T01 à T03 | Workbench enregistré, activable, barre d'outils et menu « GD&T Tools » présents | Présence dans l'interface |
| T04 | Les 5 commandes sont enregistrées et 12 icônes `:/dd/icons/...` se chargent | Chargement des icônes |
| T05 à T10 | Création AP, DF (+ DS automatique), DS, GT, GT sur cylindre avec Ø | Exécution des commandes, création des objets |
| T17 | Une GT posée sur la face d'un DF rejoint son annotation | Création des objets |
| T18 | Sélection de faces sur deux objets différents | Python 3 |
| T19 | Le plan de travail Draft est le plan d'annotation pendant la saisie du point | FreeCAD 1.x |
| T21 | La face annotée est colorée et reste opaque | FreeCAD 1.x |
| T25 | Échap pendant la saisie : aucun élément orphelin | Robustesse |
| T11 / T28 | Rendu Coin (points, textes, « 2x ») et captures PNG (vues de dessus et isométrique) | Création des objets GDT |
| T12 | Annotations rangées dans le dossier de leur plan | Arborescence |
| T13, T22, T23 | Inventaire : ouverture, modification d'une GT, suppression d'un DS | Exécution des commandes |
| T26, T27 | Traduction française (fichier `.qm`, menus), page de préférences | Traductions |
| T14 | Enregistrement, fermeture, réouverture : mêmes objets, ViewProviders restaurés, aucun objet invalide | Sauvegarde et réouverture |
| T15, T20 | Face d'une fonction dans un Body ; face non-Tip dans un App::Part déplacé | FreeCAD 1.x |
| T16 | Les 12 fichiers `Doc/*.FCStd` : ouverture, recalcul, dérive des points d'ancrage, réenregistrement puis réouverture sans avertissement de portée | Compatibilité avec les fichiers historiques |

## Résultats par lot

Fichiers bruts : `Modernisation/tests/lot<N>_results.json`.

| Test | Lot 0 (origine) | Lot 1 | Lot 2 | Lot 3 | Lot 4 | Lot 5 | Lot 6 (final) |
|---|---|---|---|---|---|---|---|
| T01 Workbench enregistré | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T02 Activation du workbench | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T03 Barre d'outils et menu | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T04 Commandes et icônes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T05 Document de test | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T06 Création Annotation Plane | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T07 Création Datum Feature (+DS auto) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T08 Création Datum System | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T09 Création Geometric Tolerance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T10 Tolérance sur cylindre (Ø) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T11 Rendu Coin des annotations | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T12 Rangement dans le dossier du plan | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T13 Inventaire | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T14 Sauvegarde / réouverture | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T15 Face d'une fonction dans un Body | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T16 Fichiers historiques | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| T17 GT ajoutée à l'annotation existante | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T18 Sélection multi-objets | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T19 Plan de travail aligné sur l'AP | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T20 Face non-Tip dans un App::Part déplacé | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T21 Couleur de face opaque | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T22 Inventaire : modification | – | ❌¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T23 Inventaire : suppression | – | ❌¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| T24 Chargement différé | – | – | – | ✅ | ✅ | ✅ | ✅ |
| T25 Annulation de la saisie (Échap) | – | – | – | – | ✅ | ✅ | ✅ |
| T26 Traductions (fr) | – | – | – | – | – | ✅ | ✅ |
| T27 Page de préférences | – | – | – | – | – | ✅ | ✅ |
| T28 Capture du rendu 3D | – | – | – | – | – | – | ✅ |
| **Réussis / exécutés** | **14/21** | 20/21 | 22/23 | 23/24 | 24/25 | 26/27 | **27/28** |

¹ Tests créés au lot 2, puis rejoués sur le code du lot 1 pour preuve (`tests/lot1_inventaire_check.json`).

Les tests marqués « – » n'existaient pas encore à ce lot. Ils ont été ajoutés au fur et à mesure que l'audit ou les mesures révélaient un risque.

## Détail des résultats finaux (lot 6)

- **Console.** Aucune erreur ni traceback dans la vue Rapport pendant les tests T01 à T28, chargement compris.
- **T16 (WARN).** 11 fichiers sur 12 sont « OK » : ouverture et recalcul sans objet invalide, aucun avertissement de portée après réenregistrement, dérive du point d'ancrage nulle (< 1e-13 mm), sauf `Plaque.FCStd`. `Assembly.FCStd` est « PB » parce que l'atelier Assembly4 est absent et que `Pocket001` est invalide dans le fichier. C'est indépendant du MOD : le résultat est identique avec le code d'origine. Pour `Plaque.FCStd`, la dérive de 40,6 mm est préexistante et due à la renumérotation des faces (TNP).
- **T28 (rendu).** `Modernisation/tests/gdt_render_top.png` et `gdt_render_iso.png` (version modernisée), à comparer avec `gdt_render_top_code_origine.png` (même document rendu par le code d'origine sous FreeCAD 1.1).

| Constat visuel | Code d'origine | Version modernisée |
|---|---|---|
| Cadres, lignes de rappel, triangle et lettre du DF | OK | OK |
| Valeur de tolérance 0,02 mm | « Ø.020 µm » ❌ | « Ø0.020 mm » ✅ |
| Annotation sur 2 faces | « 2x » absent ❌ | « 2x » ✅ |
| Faces annotées | transparentes ❌ | colorées et opaques ✅ |
| Symbole de caractéristique (⏤, ⌖…) | glyphe manquant ❌ | glyphe manquant ❌ (limitation L-05) |
| Valeur de tolérance chevauchant le trait de séparation des cases | oui | oui (mise en page d'origine conservée) |

## Couverture et limites des tests

- **Saisie du point.** Elle passe par la saisie de coordonnées de Draft, et non par un clic de souris dans la vue 3D. T19 vérifie cependant que le plan utilisé pour projeter les clics est bien celui de l'AP.
- **Non couverts automatiquement :** double-clic dans l'arborescence, menu contextuel, bouton « Visualiser » de l'inventaire, mode « limites mini / maxi » de la tolérance de diamètre, modification d'un AP ou d'un DF depuis l'inventaire. Ces chemins de code ont été revus et modifiés de façon minimale.
- **FreeCAD 1.0, Linux :** non testés (voir l'environnement).
