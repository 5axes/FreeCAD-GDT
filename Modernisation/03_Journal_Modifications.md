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

---

## Lot 2 : modernisation Qt / PySide (Qt 6.8, PySide6 6.8.3)

### Raisonnement technique

Les mesures sous FreeCAD 1.1.3 montrent que :

- la couche `Ext/PySide/QtGui.py` de FreeCAD fusionne `PySide6.QtGui` et `PySide6.QtWidgets`. Les `QtGui.QComboBox`, etc. fonctionnent donc, mais uniquement grâce à cette fusion ;
- `QtCore.SIGNAL("valueChanged(double)")` (connexion de style ancien) fonctionne encore, alors que la connexion moderne `inputfield.valueChanged[float]` **échoue** : sous PySide6, `Gui::InputField` n'expose que `valueChanged(Base::Quantity)` ;
- **défaut réel découvert :** avec PySide6, `clicked.connect(lambda obj=obj, data=data: …)` reçoit `obj=False` (le paramètre `checked` du signal `clicked(bool)` prend la place du premier argument par défaut). Vérifié par un script isolé, puis par les tests T22 et T23 rejoués sur le code du lot 1 (`tests/lot1_inventaire_check.json` : T22 et T23 en FAIL). Les boutons **Modify** et **Delete** de l'inventaire étaient donc inopérants sous FreeCAD 1.x.

### Modifications

| ID | Fichier | Modification |
|---|---|---|
| Q-02 | GDT.py, inventory.py | `from PySide import QtCore, QtGui, QtWidgets`. Les 12 classes de widgets (`QWidget`, `QComboBox`, `QLabel`, `QLineEdit`, `QPushButton`, `QGroupBox`, `QCheckBox`, `Q[HV]BoxLayout`, `QLayout`, `QMessageBox`, `QApplication`) passent dans `QtWidgets`. `QtGui` ne sert plus qu'à `QIcon`, `QColor` et `QFontDatabase`. L'import inutilisé de `QtSvg` et le `try/except ImportError` inopérant sont supprimés. |
| Q-01 | GDT.py, inventory.py | Les 8 connexions `QtCore.QObject.connect(…, SIGNAL("valueChanged(double)"), …)` passent par le helper `connectValueChanged()`. Il se branche sur `valueChanged(Quantity)` et transmet `Quantity.Value` (unités internes, mm), ou la valeur flottante sous PySide2. |
| Q-03 | GDT.py, inventory.py | `getStandardButtons()` renvoie `QtWidgets.QDialogButtonBox.Close` au lieu de `0x00200000`, comme le fait le code de FreeCAD 1.1. |
| Q-04 | GDT.py, inventory.py | `QComboBox.SizeAdjustPolicy(2)` remplacé par `QComboBox.AdjustToMinimumContentsLengthWithIcon`. |
| Q-06 (nouveau) | inventory.py | `clicked.connect(lambda checked=False, obj=obj, data=…)` : les boutons Modify et Delete fonctionnent de nouveau. |
| Q-07 (nouveau) | GDT.py, inventory.py | Les lambdas inutiles sur `activated(int)` et `textChanged(str)` sont remplacées par une connexion directe au slot (même comportement, sans piège d'arguments par défaut). |

### Tests (`Modernisation/tests/lot2_results.json`)

23 tests : 22 PASS, plus T16 en WARN (Assembly4, inchangé). Deux nouveaux tests : **T22** (modifier la valeur d'une GT depuis l'inventaire) et **T23** (supprimer un DS depuis l'inventaire).

---

## Lot 3 : intégration du workbench FreeCAD 1.x

### Raisonnement technique

- **Chargement (W-01).** `InitGui.py` importait `GDT` au démarrage de FreeCAD. Cela chargeait Draft, Coin et les ressources Qt même si l'atelier n'était jamais utilisé. Par ailleurs, une exception dans `GDT` empêchait l'atelier d'apparaître. Désormais, tout est importé dans `Initialize()`. Le test T24 vérifie qu'aucun module du MOD n'est importé au démarrage.
- **Piège rencontré :** FreeCAD exécute `InitGui.py` par `exec()` *à l'intérieur d'une fonction* de `FreeCADGuiInit`. Les noms de niveau module y sont donc des variables locales, invisibles depuis le corps de la classe : le premier essai a échoué en T01 (atelier absent). Les déclarations `global` du code d'origine avaient précisément ce rôle. Elles sont rétablies et commentées.
- **Portée des liens (I-03).** Dans les fichiers historiques, les liens pointent sur une fonction *interne* à un Body (`(Pad, "Face12")`). Sous 1.1, `freecadcmd` affiche à l'ouverture de `cube.FCStd` 15 avertissements du type « Link(s) to object(s) 'Pad' go out of the allowed scope ». La migration `onDocumentRestored` → `migrateFaceLinks` réécrit ces liens par le chemin du conteneur, `(Body, "Pad.Face12")`. Le **même** élément est désigné, et la géométrie est inchangée : la dérive du point d'ancrage est nulle sur les 11 fichiers d'exemple. Elle est mesurée par `drift.py` sur le code d'origine et sur le nouveau code.
- **Constat hors MOD.** `Plaque.FCStd` présente une dérive de 40,4 mm sur `Annotation6` et de 2,3 mm sur `AP7` après recalcul. Le résultat est **identique avec le code d'origine** : la face `Chamfer001.Face2/Face3` n'a plus le même numéro sous FreeCAD 1.1 que sous la version qui a écrit le fichier. C'est le problème de nommage topologique (TNP). Il faut réaffecter ces deux éléments manuellement.
- **Ouverture sans interface (F-13).** Vérifiée sous `freecadcmd` : les objets sont restaurés et recalculés sans erreur. Le flag `gui` vaut maintenant `FreeCAD.GuiUp`, au lieu de `True` forcé, pour que les fonctions `make*` ne tentent pas de créer des ViewProviders sans interface.

### Modifications

| ID | Fichier | Modification |
|---|---|---|
| W-01 | InitGui.py | Réécriture. Imports différés dans `Initialize()`. Polices enregistrées à l'activation, avec un avertissement en cas d'échec, et non plus dans `__init__` au démarrage. Listes de commandes en attributs de classe (`CREATION_COMMANDS`, `INVENTORY_COMMANDS`), avec des noms `dd_*` inchangés. Menu contextuel sans `IndexError`. Docstrings. |
| W-03 | InitGui.py | `Msg()` / `Log()` remplacés par `FreeCAD.Console.PrintLog()`. Les messages d'activation passent en niveau Log, car ils polluaient la vue Rapport. |
| I-03 | GDT.py | `_GDTObject.onDocumentRestored` appelle `migrateFaceLinks()` (via `toRootLink()`). Après un réenregistrement, plus aucun avertissement de portée (T16). **Conséquence :** un fichier réenregistré par cette version n'est plus correctement interprété par l'ancien MOD (compatibilité ascendante uniquement). |
| I-06 | GDT.py | `dumps()` / `loads()` sur les proxys App et Vue, avec `__getstate__` / `__setstate__` conservés comme alias. Format de l'état inchangé. |
| F-13 | GDT.py | `gui = FreeCAD.GuiUp`. |
| I-07 | package.xml | Version 1.0.0, `freecadmin` 1.0.0, `pythonmin` 3.8, licence au format SPDX, dépendances `Draft` et `Part`, icône et nom au niveau du workbench, mots-clés. |

### Tests (`Modernisation/tests/lot3_results.json`)

25 tests : 24 PASS, plus T16 en WARN (Assembly4 seulement). Nouveau test **T24** (chargement différé). T16 mesure désormais aussi la dérive du point d'ancrage et l'absence d'avertissements de portée après réenregistrement.
