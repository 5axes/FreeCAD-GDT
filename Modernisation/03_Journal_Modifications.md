# Journal des modifications : modernisation FreeCAD 1.x

Branche : `modernisation-fc1x`. Chaque lot correspond à un commit. Le diff complet d'un lot s'obtient avec `git show <commit>`, ou avec `git diff master..modernisation-fc1x -- <fichier>` pour l'ensemble. Les identifiants entre crochets (I-01, F-02…) renvoient au [rapport d'audit](01_Rapport_Audit.md).

---

## Lot 0 : référence et outillage

**Contenu :** aucun changement du code du MOD.

| Fichier | Rôle |
|---|---|
| `Modernisation/01_Rapport_Audit.md` | Rapport d'audit et liste des incompatibilités |
| `tools/install_mod.py` | Installe une copie filtrée du MOD dans `%APPDATA%\FreeCAD\v1-1\Mod\FreeCAD-GDT`, sans `Doc/`, `tools/`, `tests/`, `rcc.exe`, `*.sfd` ni `__pycache__`. Fonctionne sous Windows, Linux et macOS. |
| `tools/run_gui_tests.py` | Installe le MOD, lance `FreeCAD.exe tests/gui_test_gdt.py`, lit le rapport JSON, affiche la synthèse et renvoie un code de sortie 1 en cas d'échec |
| `tests/gui_test_gdt.py` | Test de bout en bout **dans l'interface réelle** : clics sur les boutons des panneaux, saisie du point d'ancrage par le rappel de saisie de coordonnées du Snapper Draft, capture de la vue Rapport (« Report view »), sauvegarde et réouverture, ouverture des `Doc/*.FCStd` |

Résultat de référence (MOD d'origine, FreeCAD 1.1.3) : `Modernisation/tests/lot0_results.json`. Les tests T12, T17, T18, T19, T20 et T21 échouent.

---

## Lot 1 : corrections bloquantes et majeures

### Raisonnement technique

1. **Plan de travail (I-01).** Le code source de Draft 1.1 montre que `FreeCAD.DraftWorkingPlane` est réécrit par `WorkingPlane.get_working_plane()` (`_update_old_plane`). Le test T19 l'a confirmé : avec le code d'origine, pendant la saisie du point, le plan actif restait le plan XY à l'origine (z=0), alors que l'AP est à z=10. Un clic dans la vue 3D plaçait donc l'annotation hors du plan d'annotation.
   → Nouveau helper `alignWorkingPlane()`. Il utilise `get_working_plane().align_to_point_and_axis()` (qui met aussi à jour la grille) et se replie sur l'ancienne API sous FreeCAD < 1.0.
2. **Géométrie dans les conteneurs (I-04).** La sélection mélangeait l'objet racine (mode 0, par ex. `Part`) et un nom de face relatif à la fonction résolue (mode 1, `Face6`). Une mesure sous `freecadcmd` montre qu'une fonction PartDesign a sa forme dans le repère du Body et que le placement du Part n'est jamais appliqué. Le test T20 renvoyait p1=(0, 200, 10) au lieu de (10, 210, 5).
   → Les faces sont désormais stockées comme `(objet racine, chemin complet)`, par ex. `(Part, "Body.Box.Face6")`, et évaluées par `Part.getShape(obj, sub, needSubElement=True)`, qui applique toute la chaîne de placements. Les fichiers historiques, qui stockent `(objet, "FaceN")`, passent par la même fonction sans changement de résultat. Le type des propriétés est inchangé, ce qui préserve la compatibilité.
3. **Couleur des faces (I-05).** Une mesure dans l'interface 1.1.3 montre que `DiffuseColor` avec alpha=0 donne `ShapeAppearance.Transparency = 1.0`. Le code d'origine rendait donc **invisibles** les faces porteuses d'un DF ou d'une GT. De plus, l'index de face était lu dans `SubElementNames[i]` avec `i` = index d'objet.
   → `setColor` réécrit : alpha 1.0 si `ShapeAppearance` existe (1.x), 0.0 sinon (0.2x). Il boucle sur chaque face de chaque objet. Pour une fonction PartDesign, il colore le Body seulement si la fonction est la Tip, car c'est la seule numérotation de faces valide.

### Modifications

| ID | Fichier | Modification |
|---|---|---|
| I-01 | GDT.py, inventory.py | `alignWorkingPlane()` remplace les 6 appels `FreeCAD.DraftWorkingPlane.alignToPointAndAxis` + `Snapper.grid.set()`. Le double-clic sur un AP renvoie `True` (événement traité) et ne force plus de recompute inutile. |
| I-04 | GDT.py | Nouveaux helpers `getSelectedFaces()`, `getFaceShape()`, `getAnnotatedFace()`, `isCircumferenceFace()` et `updateAnnotationAnchor()`. Ils sont utilisés par `ContainerOfData`, `_AnnotationPlane` (création et `execute`), `_Annotation.execute` et `makeAnnotation`. `_AnnotationPlane.__init__(obj, face=None)` peut maintenant être créé par script, sans sélection. |
| I-05 | GDT.py | `setColor` réécrit (voir le point 3 ci-dessus), avec la table `FACE_COLORS`. |
| P-01 | GDT.py | Tri des faces avec `key=(Name, subname)`. Avant, une sélection sur deux objets levait `TypeError: '<' not supported between DocumentObject` (T18). |
| P-02 | GDT.py | `prop in "selectedPoint"` remplacé par `prop == "selectedPoint"`. |
| F-01 | GDT.py | `ToleranceFontSize` était initialisé en écrasant `FontSize`. |
| F-02 | GDT.py | L'annotation est rangée dans le groupe parent de son AP (`AP.getParentGroup()`), et non plus cherchée sous un nom erroné (`"Plane " + AP.Name`). |
| F-03 | GDT.py | `uom == "mm"` remplacé par `uom = "mm"` (idem pour `in`). Une tolérance de 0,05 mm s'affichait « 0.050 µm ». |
| F-04 | datumFeature.py, GDT.py | `IsActive()` ne calcule plus de géométrie (`findAnnotation(getSelectedFaces())`). Le `print("ContainerOfData …")` exécuté à chaque rafraîchissement de l'interface est supprimé. |
| F-05 | annotationPlane.py, InitGui.py | Plus d'`IndexError` quand un objet est sélectionné sans sous-élément (`IsActive`, menu contextuel). |
| F-06 | GDT.py | `findAnnotation()` / `flattenLinkSubList()` normalisent `[(obj, ('Face1','Face2'))]` et `[(obj,'Face1'), (obj,'Face2')]`. Une GT posée sur la face d'un DF rejoint maintenant l'annotation existante (T17). |
| F-07 | inventory.py | `l.touch` remplacé par `l.touch()`. |
| F-08 | inventory.py | `pos` initialisé (`UnboundLocalError` quand une GT n'avait pas de caractéristique). |
| F-09 | GDT.py | `PointWithOffset` est recalculé quand `p1` change (et non plus sur une propriété « Point » inexistante). |
| (bonus) | GDT.py | Le compteur « 2x » compte toutes les faces liées (via `flattenLinkSubList`), et non plus `numpy.size()` du premier objet seul. `ContainerOfData` ne plante plus sur une face B-spline (pas d'`Axis`). `circumferenceBool` est calculé dans `makeAnnotation` sans dépendre du ViewProvider. |

### Tests (`Modernisation/tests/lot1_results.json`)

20 tests PASS. T16 est en WARN : `Assembly.FCStd` exige l'atelier externe Assembly4 (`Asm4_libs`), et `Pocket001` est invalide dans le fichier lui-même. C'est indépendant du MOD et cela se produisait déjà avec le code d'origine. Le banc de test a été complété : la couleur est mesurée juste après la création du DF, et les saisies de point sont tracées.
