# FreeCAD-GDT : état des fonctionnalités (FreeCAD 1.1.3)

Les identifiants entre crochets (I-01, F-02…) renvoient au [rapport d'audit](01_Rapport_Audit.md) et à la [liste des incompatibilités](02_Incompatibilites.md). Les tests (Txx) sont décrits dans le [rapport de tests](04_Rapport_Tests.md).

## ✅ Valides (fonctionnaient déjà avec le code d'origine sous 1.1 et fonctionnent toujours)

| Fonctionnalité | Tests |
|---|---|
| Apparition du workbench « GD&T », barre d'outils et menu « GD&T Tools » | T01 à T03 |
| Icônes des commandes et de l'arborescence (ressources `:/dd/icons`) | T04 |
| Création d'un plan d'annotation sur une face plane, avec décalage | T06 |
| Création d'un élément de référence (lettre A à Z), avec création automatique du système de référence | T07 |
| Création d'un système de référence primaire / secondaire / tertiaire | T08 |
| Création d'une tolérance géométrique : 14 caractéristiques, 11 modificateurs, système de référence | T09 |
| Tolérance sur une face cylindrique avec Ø et tolérance ± sur le diamètre | T10 |
| Rendu 3D : cadre, ligne de rappel, triangle du DF, valeur, lettres de référence, Ø, ± | T11, T28 |
| Ouverture de l'inventaire | T13 |
| Enregistrement et réouverture d'un document | T14 |
| Lecture des fichiers historiques (`Doc/*.FCStd`) | T16 |
| Page de préférences (taille et couleur des textes et des lignes, unités, grille, coloration des faces) | T27 |

## 🔧 Corrigées (défectueuses avec le code d'origine sous FreeCAD 1.1 ou Python 3)

| Fonctionnalité | Défaut d'origine | Tests |
|---|---|---|
| Saisie du point d'ancrage dans le plan d'annotation | Le plan de travail Draft restait le plan XY à l'origine : les clics tombaient hors du plan [I-01] | T19 |
| Annotation de faces dans un Body ou un App::Part | Géométrie évaluée dans le mauvais repère, ou sur la mauvaise forme [I-04] | T20 |
| Coloration des faces annotées | Les faces devenaient **transparentes** sous 1.x [I-05] | T21 |
| Sélection de faces sur plusieurs objets | `TypeError` en Python 3 [P-01] | T18 |
| Ajout d'une GT sur une face qui porte déjà un DF ou une GT | Une nouvelle annotation était créée au lieu de compléter l'existante [F-06] | T17 |
| Rangement des annotations dans le dossier de leur plan | Jamais effectué [F-02] | T12 |
| Affichage des valeurs en schéma d'unités µm / thou | « 0.050 µm » pour 0,05 mm [F-03] | T11 |
| Indication « Nx » sur une annotation multi-objets | Absente : seules les faces du premier objet étaient comptées (lot 1) | T28 |
| Inventaire : boutons Modifier et Supprimer | Inopérants sous PySide6 [Q-06] | T22, T23 |
| Annulation (Échap) pendant la saisie du point d'un DF | Pouvait supprimer un système de référence sans rapport [F-11] | T25 |
| Taille de police des tolérances | Écrasait la taille des textes [F-01] | – |
| Libellé du champ « Nom » | Affichait la valeur au lieu du libellé [F-15] | T27 |
| Avertissements « Link(s) go out of the allowed scope » sur les fichiers historiques | 15 avertissements sur `cube.FCStd` ; supprimés par migration [I-03] | T16 |
| Chargement de FreeCAD | Le MOD entier, Draft compris, était chargé au démarrage [W-01] | T24 |
| Console | ~30 traces de débogage, dont une à chaque rafraîchissement de l'interface [F-04, W-04] | console vide dans T01 à T28 |
| Interface en français | Aucune traduction [W-02] | T26, T27 |

## ◐ Partiellement fonctionnelles

| Fonctionnalité | Limitation | Cause | Piste |
|---|---|---|---|
| Symboles des caractéristiques dans la vue 3D (⏤, ⏥, ○, ⌭, ⌒, ⌓, ⟂, ∠, ∥, ⌯, ⌖, ◎, ↗, ⌰) et des modificateurs (Ⓜ, Ⓛ…) | La case du symbole affiche un glyphe manquant. Le symbole est néanmoins **stocké** (`CharacteristicCode`), affiché dans l'arborescence (icône) et dans les panneaux. **Défaut préexistant** (vérifié avec le code d'origine). | `SoAsciiText` (Coin3D) ne rend pas ces caractères Unicode. Changer `FontName` (nom ou chemin d'Iso-Gps, osifont) ne modifie pas le rendu (mesuré). | Dessiner le symbole autrement : géométrie Coin (lignes et arcs), texture issue des SVG `Resources/icons/Characteristic/` (le code de repli « anciens documents » existe déjà), ou `SoText2` / `SoFrameLabel`. |
| Mise en page du cadre | La valeur de tolérance chevauche le trait de séparation des cases, et la largeur des cases ne suit pas la taille de police. Défaut préexistant. | Largeurs calculées en nombre de caractères × `LineScale`, sans tenir compte de la taille réelle du texte. | Calculer la largeur avec `SoAsciiText.getBoundingBox` ou une métrique de police. |
| Documents historiques dont la topologie a changé (`Doc/Plaque.FCStd`) | 2 annotations se déplacent au recalcul (40,4 mm et 2,3 mm). | Renumérotation des faces de `Chamfer001` entre la version de FreeCAD d'origine et la 1.1 (TNP). Défaut préexistant. | Réaffecter manuellement. Les liens créés par la nouvelle version passent par le chemin du conteneur et bénéficient des noms topologiques de FreeCAD 1.x. |
| Compatibilité ascendante | Un fichier réenregistré par cette version a ses liens de faces exprimés par le conteneur (`Body`, `"Pad.Face5"`). **L'ancien MOD ne les interprète plus correctement.** | Migration I-03 (nécessaire pour supprimer les avertissements de portée et appliquer les placements des conteneurs). | Conserver une copie des fichiers si l'ancien MOD doit encore les ouvrir. |
| Noms par défaut des AP, DF, DS et GT dans les panneaux | Plafonnés à 99 (A à Z pour les DF) : au-delà, le nom proposé se répète. Pas d'erreur. | Dictionnaires des modules de commandes conservés. | Générer les noms à la volée, comme c'est déjà fait pour les annotations. |
| Plateformes | FreeCAD 1.0 et Linux non testés. | Non disponibles sur le poste. | Passer `tools/run_gui_tests.py` sur ces environnements. |

## ➕ Restant à développer (absent du MOD d'origine)

| Besoin | Commentaire |
|---|---|
| Rendu fiable des symboles GD&T (voir ci-dessus) | Priorité 1 pour un usage en production. |
| Dimensions théoriquement exactes (TED) | La propriété `Annotation.TED` existe depuis l'origine, mais aucune commande ni aucun rendu ne l'exploite. |
| Annotation d'arêtes ou de sommets | Seules les faces sont acceptées par les commandes. |
| Modification interactive du point d'ancrage | Après création, le point se modifie uniquement par la propriété `selectedPoint`. |
| Export PMI (STEP AP242) | Les documents de `Doc/GD&T_Pdf/` décrivent la cible ; rien n'est implémenté. |
| Régénération multiplateforme du `.rcc` | FreeCAD ne fournit pas `rcc`. Il faut soit un Qt complet, soit remplacer le `.rcc` par des chemins de fichiers, tout en gardant la résolution des chemins `:/dd/icons/...` stockés dans les documents. |
| Tests sans interface (CI) | Le banc actuel exige l'interface de FreeCAD (Windows). Une partie (géométrie, migration) peut tourner sous `freecadcmd`. |
