# FreeCAD-GDT : rapport d'audit initial

| | |
|---|---|
| Dépôt analysé | `C:\Users\lalliard\Documents\30_Devel\FreeCAD-GDT` (branche `master`, commit `d693e73`, copie de travail propre) |
| Amont | https://github.com/5axes/FreeCAD-GDT |
| Cible | FreeCAD 1.0 / 1.1, Python 3.x |
| Environnement de référence | FreeCAD **1.1.3** (R20260725) dans `C:\Logiciel_Cetim\FreeCAD 1.1`, Python **3.11.14**, Qt **6.8.3**, PySide **6.8.3**, numpy 1.26.4, pivy |
| Date | 2026-10-17 |
| Statut | Audit seul. **Aucun fichier de code n'a été modifié.** |

### Légende des niveaux de vérification

- **[V]** : vérifié, soit en lisant le code source de FreeCAD 1.1.3 installé, soit par une exécution sous `freecadcmd` 1.1.3.
- **[A]** : établi par lecture du code du MOD, sans exécution.
- **[NV]** : non vérifié. Il faut un test dans l'interface graphique, qui n'a pas encore été fait (aucune instance FreeCAD graphique n'était joignable pendant l'audit).

---

## 1. Fonction du MOD

Le MOD est un atelier (workbench) d'annotation **GD&T / ISO GPS 3D**, conforme à l'esprit de l'ISO 16792. Il pose directement sur les faces d'un modèle 3D :

1. des **plans d'annotation** (Annotation Plane) : un plan parallèle à une face, avec un décalage (offset) ;
2. des **éléments de référence** (Datum Feature) : lettres A à Z dans un cadre avec un triangle ;
3. des **systèmes de référence** (Datum System) : primaire, secondaire et tertiaire ;
4. des **tolérances géométriques** (Geometric Tolerance) : 14 caractéristiques, 11 modificateurs, valeur, option Ø et tolérance sur diamètre ;
5. un **inventaire** : un panneau qui liste tous les éléments et permet de les modifier ou de les supprimer.

Le rendu est fait en Coin3D, sous forme de lignes et de textes 3D (`SoAsciiText`) dans le plan d'annotation. La saisie du point d'ancrage passe par le Snapper de l'atelier Draft.

## 2. Structure du dépôt

```
FreeCAD-GDT/
├── InitGui.py               Déclaration du workbench (classe GDandTWorkbench)
├── GDT_locator.py           Astuce pour retrouver le dossier du MOD (__file__)
├── GDT.py           2366 l. Cœur du MOD : objets, view providers, rendu Coin, widgets
├── annotationPlane.py   56 l. Commande dd_annotationPlane
├── datumFeature.py      83 l. Commande dd_datumFeature
├── datumSystem.py       55 l. Commande dd_datumSystem
├── geometricTolerance.py 88 l. Commande dd_geometricTolerance
├── inventory.py        608 l. Commande dd_inventory et ses widgets *_inv
├── package.xml               Métadonnées de l'Addon Manager (format 1, FreeCAD min. 0.20)
├── Resources/
│   ├── dd_resources.rcc      Ressources Qt compilées (préfixe :/dd) : 38 SVG + 1 .ui
│   ├── compile_resources_pack.py  Script de génération du .rcc (nécessite `rcc`)
│   ├── rcc.exe (6,5 Mo)       Binaire Windows tiers, versionné dans le dépôt
│   ├── icons/ (38 SVG)        Sources des icônes (y compris Characteristic/ et FeatureControlFrame/)
│   ├── ui/preferences-gdt.ui  Page de préférences
│   └── fonts/                 osifont-lgpl3fe.ttf, Iso-Gps.ttf (+ sources .sfd)
└── Doc/ (7,5 Mo)              Fichiers d'exemple .FCStd, PDF de normes, captures,
                               FreeCAD-GDT-master.zip, RccExtended-v1.0.5-win32.zip, .docx
```

Il n'y a **aucun** dossier de traductions (`translations/`, `.ts` ou `.qm`), aucun test automatisé et aucun fichier `Init.py` (côté App).

## 3. Architecture

### 3.1 Chargement

```
FreeCAD (démarrage GUI)
 └─ exec InitGui.py
     ├─ import GDT            ← chargé dès le démarrage de FreeCAD, avant toute activation
     │   ├─ import Draft, DraftVecUtils, Draft_rc, WorkingPlane, Part, pivy, numpy
     │   ├─ QResource.registerResource(dd_resources.rcc) ; assert
     │   └─ définitions (objets, VP, widgets)
     ├─ import GDT_locator     → GDTWBpath
     └─ addWorkbench(GDandTWorkbench)
          __init__  : ajoute 2 polices à QFontDatabase
          Initialize: import datumFeature, datumSystem, geometricTolerance,
                      annotationPlane, inventory  (chacun : addCommand)
                      barre d'outils et menu "GD&T Tools", addIconPath(':/dd/icons'),
                      addPreferencePage(':/dd/ui/preferences-gdt.ui','GDT')
```

Chaque module de commande crée, au moment de son import, une instance `GDTWidget` globale. Cette instance porte une liste `dialogWidgets` qui est ensuite modifiée à chaque `Activated()`.

### 3.2 Commandes FreeCAD

| Nom de commande | Module | Action | `IsActive` |
|---|---|---|---|
| `dd_annotationPlane` | annotationPlane.py | Panneau : nom et offset, puis `makeAnnotationPlane` | 1 objet sélectionné dont le 1er sous-élément est une Face |
| `dd_datumFeature` | datumFeature.py | Panneau : lettre, plan et case « créer DS », puis `makeDatumFeature` et éventuellement `makeDatumSystem` | Au moins un AP, que des faces sélectionnées, et l'annotation n'a pas déjà de DF |
| `dd_datumSystem` | datumSystem.py | Panneau : primaire, secondaire et tertiaire, puis `makeDatumSystem` | Au moins un DF dans le document |
| `dd_geometricTolerance` | geometricTolerance.py | Panneau : caractéristique, valeur, modificateur, Ø, DS et plan, puis `makeGeometricTolerance` | Au moins un AP et que des faces sélectionnées |
| `dd_inventory` | inventory.py | Panneau multi-formulaires : modifier ou supprimer chaque élément | Document actif |

Ces commandes apparaissent dans la barre d'outils, dans le menu « GD&T Tools » et dans le menu contextuel. Le menu contextuel ne propose les quatre commandes de création que si toutes les sous-sélections sont des faces.

### 3.3 Objets créés dans le document

Ces noms sont **sérialisés dans les fichiers .FCStd** sous la forme `module=GDT`, `class=…`. Ils sont donc **intouchables** si l'on veut continuer à ouvrir les fichiers historiques.

| Objet | Type FreeCAD | Proxy / ViewProvider | Propriétés principales |
|---|---|---|---|
| Groupe racine `GDT` | `App::DocumentObjectGroupPython` | `_GDTObject` / `_ViewProviderGDT` | `Type` |
| Sous-groupe `DS` | idem | idem (`Type="DS"`) | |
| Groupe `Plane_<nom>` | idem | idem (`Type="Plane"`) | |
| AnnotationPlane | `App::FeaturePython` | `_AnnotationPlane` / `_ViewProviderAnnotationPlane` | `Offset`, `faces` (LinkSub), `p1`, `Direction`, `PointWithOffset` |
| DatumFeature | `App::FeaturePython` | `_DatumFeature` / `_ViewProviderDatumFeature` | (Label = lettre) |
| DatumSystem | `App::FeaturePython` | `_DatumSystem` / `_ViewProviderDatumSystem` | `Primary`, `Secondary`, `Tertiary` (Link) |
| GeometricTolerance | `App::FeaturePython` | `_GeometricTolerance` / `_ViewProviderGeometricTolerance` | `Characteristic(+Code,+Icon)`, `Circumference`, `ToleranceValue`, `FeatureControlFrame(+Code,+Icon)`, `DS` |
| Annotation | `App::DocumentObjectGroupPython` | `_Annotation` / `_ViewProviderAnnotation` (rendu Coin) | `AP`, `faces` (LinkSubList), `TED`, `DF`, `GT` (LinkList), `p1`, `Direction`, `selectedPoint`, `spBool`, `circumferenceBool`, `diameter`, `toleranceSelectBool`, `toleranceDiameter`, `lowLimit`, `highLimit` ; côté vue : `LineWidth`, `LineColor`, `LineScale`, `FontSize`, `ToleranceFontSize`, `FontName`, `FontColor`, `Decimals`, `ShowUnit` |

Les chemins d'icônes `:/dd/icons/...` sont **stockés comme valeurs** dans les propriétés `CharacteristicIcon` et `FeatureControlFrameIcon`. Le préfixe de ressource `:/dd` doit donc rester valide pour les anciens fichiers.

### 3.4 Interface (panneaux de tâches)

- `GDTWidget.activate()` construit un `GDTDialog`, dont le formulaire est un `GDTGuiClass(QWidget)`, à partir d'une liste de « widgets descripteurs » : `textLabelWidget`, `fieldLabelWidget`, `comboLabelWidget`, `groupBoxWidget`, `fieldLabelComboWidget` et `CheckBoxWidget`.
- L'état est partagé par un objet `ContainerOfData` et par une **variable globale** `checkBoxState`.
- Les saisies de longueur passent par `Gui::InputField`, créé avec `FreeCADGui.UiLoader().createWidget`.
- L'inventaire duplique la plupart des widgets (classes `*_inv`) et renvoie à `form` une **liste** de QWidget, ce qui donne un panneau multi-pages.

### 3.5 Préférences

Le fichier `preferences-gdt.ui` utilise `Gui::PrefDoubleSpinBox`, `PrefLineEdit`, `PrefColorButton`, `PrefCheckBox` et `PrefSpinBox`. Il écrit sous `User parameter:BaseApp/Preferences/Mod/GDT` les clés `textSize`, `tolerancetextSize`, `textFamily`, `textColor`, `showUnit`, `changeColor`, `lineWidth`, `lineColor`, `lineScale` et `alwaysShowGrid`. Le nom de classe racine (`Gui::Dialog::DlgSettingsDraft`) vient d'un copier-coller depuis Draft. Il est sans effet.

### 3.6 Dépendances

| Dépendance | Utilisation | État dans FreeCAD 1.1.3 |
|---|---|---|
| `Draft`, `DraftTools`, `DraftVecUtils`, `DraftGeomUtils`, `Draft_rc`, `WorkingPlane` | Snapper (`getPoint`), grille, plan de travail, `getRotation` | Présents **[V]**. L'API du plan de travail a changé (voir I-01). |
| `Part` | `Shape.getElement`, `normalAt`, `CenterOfMass` | OK **[V]** |
| `pivy.coin` | Rendu | Présent **[V]** |
| `numpy` | Sert **uniquement** à `numpy.size()` sur un tuple | Présent mais superflu |
| `PySide` (couche de compatibilité FreeCAD) | `QtGui` est utilisé pour **tous** les widgets | La couche `Ext/PySide/QtGui.py` fusionne `PySide6.QtGui` et `PySide6.QtWidgets`, donc cela fonctionne. C'est toutefois une dépendance implicite. **[V]** |

### 3.7 Ressources

- Le fichier `dd_resources.rcc`, compilé avec Qt5, **se charge correctement sous Qt 6.8.3** **[V]**. Les 42 entrées (38 SVG, le .ui et les dossiers) sont toutes résolues.
- FreeCAD 1.1 **ne fournit aucun outil `rcc` ni `pyside6-rcc`** **[V]**. Pour régénérer le .rcc, il faut aujourd'hui le `rcc.exe` tiers versionné dans le dépôt, qui ne fonctionne que sous Windows.
- Les polices sont enregistrées dans `QFontDatabase`. Or **Coin3D ne consulte pas la base de polices de Qt** : il résout `SoFont.name` à partir des polices installées dans le système. La police `Iso-Gps` n'est donc probablement **pas** utilisée par le rendu 3D si elle n'est pas installée dans Windows. **[NV]**

---

## 4. Incompatibilités et défauts détectés

Niveaux de sévérité :

- **B** : bloquant, provoque une exception ou rend la fonction inutilisable ;
- **M** : majeur, la fonction donne un résultat faux ou dégradé ;
- **m** : mineur ;
- **O** : API obsolète ou dette technique, sans effet immédiat.

### 4.1 FreeCAD 1.0 / 1.1 (API Draft et App)

| ID | Sév. | Fichier : ligne | Problème et cause | Correction proposée |
|---|---|---|---|---|
| I-01 | **B/M** | GDT.py:1055, 1998, 2013, 2110 ; inventory.py:331, 339 | `FreeCAD.DraftWorkingPlane.alignToPointAndAxis(...)`. Depuis la 1.0, le plan de travail existe **par vue 3D** (`WorkingPlane.get_working_plane()`). `FreeCAD.DraftWorkingPlane` n'est plus qu'une **copie de compatibilité**, que `get_working_plane()` réécrit (`_update_old_plane`) **[V]**. Conséquences : (a) `AttributeError` si Draft n'a encore rien initialisé ; (b) la grille bouge (`grid.set()` lit la copie), mais `Snapper.getPoint()` réaligne sur le vrai plan de la vue. Le point choisi n'est donc **pas** contraint au plan d'annotation. | Remplacer par `wp = WorkingPlane.get_working_plane(); wp.align_to_point_and_axis(point, axis, offset)`, puis `FreeCADGui.Snapper.setGrid()`. Regrouper le tout dans un helper `alignWorkingPlane()`. |
| I-02 | M | GDT.py:232, 240 | `FreeCADGui.Snapper.forceGridOff` n'est plus utilisé par Draft 1.x : l'attribut est écrit mais jamais lu. `grid.on()/off()/reset()` existent toujours **[V]**. | Supprimer `forceGridOff`. Utiliser `Snapper.show()` / `Snapper.hide()` ou `grid.on()/off()`. |
| I-03 | M | GDT.py:1026, 1355 | Les propriétés `App::PropertyLinkSub` / `PropertyLinkSubList` pointent depuis un groupe GDT situé hors du Body vers la face d'une fonction **interne** au Body. FreeCAD ≥ 0.19 et 1.x émettent alors l'avertissement « Link(s) go out of allowed scope », et le recalcul peut refuser le lien. **[NV]** | Nouveaux objets : `PropertyLinkSubGlobal` / `PropertyLinkSubListGlobal`. Fichiers existants : migration dans `onDocumentRestored` (changer le type ou fixer la portée avec `obj.setPropertyStatus`). |
| I-04 | M | GDT.py:300-302, 1026 | La sélection mélange `getSelectionEx("",0)` (objet racine, par ex. le Body ou un Part) et `getSelectionEx("",1)` (nom de face relatif à la fonction résolue). On calcule ensuite `Body.Shape.getElement('FaceN')`. C'est **faux** si la fonction sélectionnée n'est pas la Tip ou si un conteneur App::Part porte un placement. FreeCAD 1.0 a modifié la résolution des sous-éléments (TNP). | Utiliser uniquement `getSelectionEx("",0)` avec `obj.getSubObject(sub)` pour la géométrie, en coordonnées globales. Ou utiliser uniquement la résolution 1 (objet et face cohérents). |
| I-05 | M | GDT.py:266-295 | `setColor` écrit `ViewObject.DiffuseColor`. En 1.0, la couleur des faces passe par `ShapeAppearance`, et `DiffuseColor` n'est plus qu'une propriété de compatibilité. La sémantique du canal alpha a aussi évolué. De plus, l'index de face est pris dans `a[0].SubElementNames[i]` alors que `i` parcourt les **objets** sélectionnés : c'est un bogue quand plusieurs faces sont sélectionnées. **[NV pour l'alpha]** | Passer à `ShapeAppearance` quand elle existe, avec repli sur `DiffuseColor`, et corriger la double boucle. |
| I-06 | O | GDT.py:942-947, 967-971 | Les proxys utilisent `__getstate__` / `__setstate__`. Depuis Python 3.11, `object.__getstate__` existe par défaut, et FreeCAD ≥ 0.21 cherche d'abord `dumps` / `loads`. Comme les classes définissent explicitement `__getstate__`, cela fonctionne. | Ajouter `dumps` / `loads`, qui délèguent à l'existant. Le format du flux reste identique. |
| I-07 | m | package.xml | Version 0.20.1, `freecadmin` 0.20, pas de `pythonmin`, ni `freecadmax`, ni `<icon>` dans `<workbench>`, ni dépendances déclarées (Draft). | Version 1.0.0 (ou 0.21.0), `freecadmin` 1.0, `pythonmin` 3.8, `<depend>` vers Draft et Part. |

### 4.2 Qt / PySide (Qt 6.8, PySide6)

| ID | Sév. | Fichier : ligne | Problème et cause | Correction proposée |
|---|---|---|---|---|
| Q-01 | O | GDT.py:2005, 2198, 2212, 2232, 2236, 2240 ; inventory.py:316, 568 | Connexions de style ancien : `QtCore.QObject.connect(w, QtCore.SIGNAL("valueChanged(double)"), slot)`. PySide6 6.8 les **accepte encore** **[V]**, mais elles sont dépréciées. | `w.valueChanged[float].connect(slot)` (à valider sur `Gui::InputField`), ou bien `Gui::QuantitySpinBox` avec `.property('rawValue')`. |
| Q-02 | O | partout | Les widgets sont pris dans `QtGui` (`QtGui.QWidget`, `QComboBox`, `QMessageBox`…). Cela ne fonctionne que grâce à la fusion faite par la couche PySide de FreeCAD **[V]**. | Écrire `from PySide import QtCore, QtGui, QtWidgets` et utiliser `QtWidgets.*`. Ainsi le code fonctionne aussi avec Qt5 (FreeCAD 0.21 / 1.0 Linux) et avec Qt6. |
| Q-03 | m | GDT.py:1868 ; inventory.py:279 | `getStandardButtons` renvoie l'entier brut `0x00200000`. Sous PySide6, les enums ne sont plus des entiers. FreeCAD 1.x convertit probablement la valeur. **[NV]** | `QtWidgets.QDialogButtonBox.Close`. |
| Q-04 | m | GDT.py:2178, 2180 ; inventory.py:547, 549 | `QComboBox.SizeAdjustPolicy(2)` : on construit l'enum à partir d'un entier. C'est valide en Python (enum), mais illisible. | `QComboBox.AdjustToMinimumContentsLengthWithIcon`. |
| Q-05 | m | InitGui.py:49-56 | Des polices sont enregistrées dans `__init__` du workbench, donc au démarrage de FreeCAD, avant même que l'atelier soit choisi. Coin ne les utilise pas (voir 3.7). | Déplacer cet enregistrement dans `Initialize()` et documenter que la police Iso-Gps doit être installée dans le système pour le rendu 3D. **[NV]** |

### 4.3 Python 3.x

| ID | Sév. | Fichier : ligne | Problème et cause | Correction proposée |
|---|---|---|---|---|
| P-01 | **B** | GDT.py:304 (`faces.sort()`) | Le tri porte sur des tuples `(DocumentObject, str)`. Avec **deux objets différents** sélectionnés, Python 3 compare des `DocumentObject`, ce qui lève `TypeError: '<' not supported`. | `faces.sort(key=lambda f: (f[0].Name, f[1]))`. |
| P-02 | M | GDT.py:1549 | `if prop in "selectedPoint"` est un test de **sous-chaîne** : `"Point"`, `"Poi"`, `""`, etc. passent aussi. La mise à jour est donc déclenchée au mauvais moment. | `prop == "selectedPoint"`. |
| P-03 | m | GDT.py:1623, 1790, 2138, 2153 ; inventory.py:344, 509, 524 | Arguments par défaut mutables (`GT=[]`, `faces=[]`, `List=[]`). | `None`, puis initialisation dans le corps. |
| P-04 | m | GDT.py, 14 occurrences | `except:` nu : il masque toutes les erreurs, y compris `KeyboardInterrupt`, et rend le diagnostic impossible. | `except Exception as e:` avec journalisation `FreeCAD.Console.PrintLog`. |
| P-05 | m | GDT.py:763 | `if str(self.face[i].numVertices) != 0` compare une chaîne à un entier : c'est toujours vrai. | Comparer des entiers. |

### 4.4 Bogues fonctionnels (indépendants de la version)

| ID | Sév. | Fichier : ligne | Description | Correction proposée |
|---|---|---|---|---|
| F-01 | M | GDT.py:1436 | `addProperty(..., "ToleranceFontSize", ...).FontSize = getToleranceTextSize()` écrase **FontSize** avec la taille de tolérance, et `ToleranceFontSize` reste à 0. | `.ToleranceFontSize = …` |
| F-02 | M | GDT.py:1628 vs 1066 | Le groupe de plan est créé sous le nom `"Plane_" + Label`, mais `makeAnnotation` le cherche sous `"Plane " + AP.Name` : espace au lieu de `_`, et nom interne au lieu du label. `getObject` renvoie `None`, l'exception est avalée, et l'annotation n'est **jamais** rangée dans son groupe de plan, contrairement à ce que décrit le README. | Stocker le groupe dans une propriété de l'AP, ou le retrouver par `AP.InList`. |
| F-03 | M | GDT.py:898-905 | `uom == "mm"` est une comparaison et non une affectation. Avec le schéma d'unités µm, la valeur en mm s'affiche suivie de « µm ». Même erreur pour `thou`. | `uom = "mm"` / `uom = "in"`. |
| F-04 | M | datumFeature.py:52-73, geometricTolerance.py:69 ; GDT.py:1793 | `IsActive()` est appelé **à chaque rafraîchissement de l'interface**. Il appelle `makeContainerOfData()` (calculs de forme et `print("ContainerOfData …")`). Cela inonde la console et ralentit l'interface. | Rendre `IsActive` léger (sélection seule) et supprimer le `print`. |
| F-05 | M | annotationPlane.py:73-77 ; InitGui.py:111 | `getSelectionEx()[0].SubObjects[0]` lève `IndexError` quand un objet est sélectionné sans sous-élément. Dans `IsActive`, l'exception est répétée en boucle. | Vérifier la sélection avant d'indexer. |
| F-06 | M | GDT.py:308-313 | `getAnnotationObj` compare `l.faces` (`PropertyLinkSubList`, de la forme `[(obj, ('Face5',))]`) à `ContainerOfData.faces` (de la forme `[(obj, 'Face5')]`). Les formats diffèrent, donc la détection d'une annotation existante risque de ne jamais réussir. **[NV]** | Normaliser les deux côtés avant de comparer. |
| F-07 | m | inventory.py:169 | `l.touch` sans parenthèses : rien n'est exécuté. | `l.touch()` |
| F-08 | m | inventory.py:414-417 | `pos` n'est pas défini quand `Characteristic == ''`, ce qui provoque un `UnboundLocalError`. | Initialiser `pos = 0`. |
| F-09 | m | GDT.py:1048 | `updateData` teste `"Point"`, alors que la propriété s'appelle `p1`. `PointWithOffset` n'est donc pas recalculé quand la face bouge. | Tester `"p1"`. |
| F-10 | m | GDT.py:1031, 1267 | `setEditorMode` est appelé dans `onChanged` à chaque changement de propriété. C'est coûteux, et en 1.x c'est mieux placé dans `onDocumentRestored` ou après la création. | Déplacer ces appels. |
| F-11 | m | GDT.py:1700-1709 | Annulation de `getPoint` : on supprime « le dernier DatumSystem » quand la case est cochée. C'est fragile, car ce n'est pas forcément celui qui vient d'être créé. | Garder une référence à l'objet créé. |
| F-12 | m | GDT.py:1634 | `dictionaryAnnotation[len(...)]` : `IndexError` au-delà de 99 annotations. Même chose pour AP, DF, DS et GT (`Dictionary[NumberOfObjects]` est borné). | Générer les noms à la volée. |
| F-13 | m | GDT.py:44-48 | `gui = True` même sans interface. `GDT.py` importe sans condition `FreeCADGui`, `QtGui`, le Snapper, etc. Ouvrir un .FCStd contenant du GDT dans `FreeCADCmd` (sans interface) échoue donc probablement. **[NV]** | Séparer la partie App (proxys, sans Qt) de la partie Gui. |
| F-14 | O | GDT.py:737, 749, 824, 851 | `DraftGeomUtils.getRotation(v)` renvoie `None` quand `v` est parallèle à Z **[V]**. `.Q` lève alors une exception, avalée par le `except` nu. Par chance, le comportement visuel reste correct. | Tester `None` explicitement. |

### 4.5 Compatibilité Linux / Windows

| ID | Sév. | Constat |
|---|---|---|
| L-01 | m | Les chemins sont construits avec `os.path.join`, ce qui est correct. Les noms de modules et de fichiers ont une casse cohérente, ce qui est correct pour Linux. |
| L-02 | m | `compile_resources_pack.py` suppose un `rcc` dans le PATH, et le dépôt ne fournit qu'un `rcc.exe` Windows. Il n'existe pas de procédure de régénération multiplateforme. |
| L-03 | m | Polices : sous Linux, Coin résout les polices par fontconfig ; sous Windows, par `C:\Windows\Fonts`. Dans les deux cas, l'enregistrement Qt est inopérant pour la 3D (voir 3.7). **[NV]** |
| L-04 | – | Rien de propre à Windows dans le code Python. |

### 4.6 Intégration FreeCAD 1.x (structure)

| ID | Sév. | Constat | Recommandation |
|---|---|---|---|
| W-01 | M | `InitGui.py` importe `GDT` **au démarrage** de FreeCAD, ce qui charge Draft, WorkingPlane, pivy et enregistre le rcc, même si l'atelier n'est jamais utilisé. Cela ralentit le démarrage, et une exception dans `GDT` empêche l'atelier d'être enregistré. | Ne garder dans `InitGui.py` que le nécessaire (chemin et icône) et faire tous les imports dans `Initialize()`. |
| W-02 | m | Pas de traductions : chaînes en dur, pas de `QT_TRANSLATE_NOOP`, pas de `FreeCADGui.addLanguagePath`. `translate` est défini mais jamais utilisé. | Envelopper les chaînes d'interface, ajouter `translations/` (FR au minimum) et l'appel à `addLanguagePath`. |
| W-03 | m | `Msg()` et `Log()` sont des alias globaux hérités. Ils **existent encore** en 1.1.3 **[V]**, mais ne sont pas documentés. | `FreeCAD.Console.PrintMessage` / `PrintLog`. |
| W-04 | m | Une trentaine de `print()` de débogage (`"5@xes …"`, `"displacement …"`, `"ContainerOfData …"`) polluent la console. | Les supprimer, ou passer à `PrintLog`. |
| W-05 | m | `numpy` est importé pour `numpy.size()`. | `len()`. |
| W-06 | m | `Doc/` (7,5 Mo, dont des zip et le zip du dépôt lui-même) et `Resources/rcc.exe` (6,5 Mo) seraient copiés dans le dossier Mod. | Les exclure de la copie d'installation, et proposer de les retirer du dépôt. |

---

## 5. Contraintes de compatibilité avec les fichiers historiques

Pour que les .FCStd existants (par ex. `Doc/*.FCStd`) restent lisibles, il faut :

1. **Garder le module `GDT`** (fichier `GDT.py` à la racine) et **les noms de classes** `_GDTObject`, `_ViewProviderGDT`, `_AnnotationPlane`, `_ViewProviderAnnotationPlane`, `_DatumFeature`, `_ViewProviderDatumFeature`, `_DatumSystem`, `_ViewProviderDatumSystem`, `_GeometricTolerance`, `_ViewProviderGeometricTolerance`, `_Annotation` et `_ViewProviderAnnotation`. Si le code est réorganisé en sous-modules, `GDT.py` doit au minimum **ré-exporter** ces classes.
2. Garder le **format d'état** : le proxy sérialise `self.Type` (une chaîne), le VP sérialise `None`.
3. Garder les **noms des propriétés**, même mal nommées (`faces`, `p1`, `spBool`…). Toute nouvelle propriété doit être ajoutée de façon conditionnelle (`if not hasattr`) dans `onDocumentRestored`.
4. Garder le **préfixe de ressource `:/dd/icons/...`**, car il est stocké dans les propriétés.
5. Garder les **noms de commandes `dd_*`**, qui peuvent figurer dans des barres d'outils personnalisées des utilisateurs.

---

## 6. Synthèse

| Catégorie | Nombre | Dont bloquants |
|---|---|---|
| API FreeCAD / Draft 1.x (I-) | 7 | 1 (I-01) |
| Qt / PySide6 (Q-) | 5 | 0 |
| Python 3 (P-) | 5 | 1 (P-01) |
| Bogues fonctionnels (F-) | 14 | 0 (mais 6 majeurs) |
| Linux / Windows (L-) | 4 | 0 |
| Intégration workbench (W-) | 6 | 0 |

**Diagnostic.** Contrairement à ce que l'on pourrait craindre, la couche Qt **n'est pas** le point de rupture : la couche PySide de FreeCAD masque le passage de Qt5 à Qt6, et le .rcc Qt5 se charge sous Qt6. Les vrais risques sont :

1. la **refonte du plan de travail Draft** en 1.0 (I-01). Elle compromet la saisie du point d'ancrage sur le plan d'annotation, qui est le cœur du flux de travail ;
2. la **résolution des sous-éléments sélectionnés** (I-04, P-01) dans les Body et Part ;
3. une série de **bogues latents** (F-01, F-02, F-03, F-06, P-02) qui faussent le rendu ou le rangement ;
4. une **architecture fragile** au chargement (W-01) et l'absence de séparation App/Gui (F-13).

## 7. Plan de modernisation proposé (étapes 3 à 5)

| Lot | Contenu | Risque pour les fichiers historiques |
|---|---|---|
| 0 | **Test de référence** : installer le MOD d'origine dans `v1-1\Mod`, lancer FreeCAD 1.1 avec un script de test (chargement, création AP/DF/DS/GT, sauvegarde et réouverture des `Doc/*.FCStd`) et consigner l'état de départ. | aucun |
| 1 | Corrections bloquantes et majeures : I-01, I-04, P-01, P-02, F-01 à F-06. | aucun (logique interne) |
| 2 | Modernisation Qt : `QtWidgets`, nouvelles connexions de signaux, enums explicites, `getStandardButtons`. | aucun |
| 3 | Intégration du workbench : `InitGui` allégé, imports différés, `package.xml` 1.x, `Console` au lieu de `Msg`/`print`, `dumps`/`loads`, `onDocumentRestored` (migration des liens Global). | faible, avec migration à la volée |
| 4 | Nettoyage : code mort (blocs commentés, `stringencodecoin`, `numpy`), `except` nus, arguments mutables, doublons GDT.py/inventory.py (listes FCF et caractéristiques). | aucun |
| 5 | Traductions : `translate()`, `translations/GDT_fr.ts` / `.qm`, `addLanguagePath`. | aucun |
| 6 | Script d'installation (copie filtrée vers `v1-1\Mod\FreeCAD-GDT`) et script de test automatique dans l'interface, avec rapport. | aucun |

Chaque lot fera l'objet d'une entrée dans `Modernisation/03_Journal_Modifications.md` (diff commenté) et d'un passage de tests consigné dans `Modernisation/04_Rapport_Tests.md`.
