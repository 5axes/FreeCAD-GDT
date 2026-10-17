# FreeCAD-GDT : incompatibilités détectées et statut

Le détail de chaque point (cause, ligne d'origine, correction proposée) figure dans le [rapport d'audit](01_Rapport_Audit.md), § 4. Ce document en donne le **statut final** après les lots 1 à 5, ainsi que le **moyen de vérification**.

Environnement de vérification : FreeCAD 1.1.3, Python 3.11.14, Qt 6.8.3 / PySide6 6.8.3, Windows 11.

### Légende

- **Statut** : ✅ corrigé · 🔎 vérifié non bloquant, laissé en l'état · ⚠️ limitation documentée · ➕ défaut découvert pendant les travaux, absent de l'audit.
- **Preuve** : `Txx` = test automatique dans l'interface (voir [rapport de tests](04_Rapport_Tests.md)) ; *mesure* = mesure ponctuelle dans FreeCAD 1.1.3 ; *lecture* = vérification du code source de FreeCAD.

## API FreeCAD / Draft

| ID | Problème | Statut | Lot | Preuve |
|---|---|---|---|---|
| I-01 | `FreeCAD.DraftWorkingPlane` n'est plus qu'une copie : le point d'ancrage n'était pas pris dans le plan d'annotation | ✅ | 1 | T19 (❌ → ✅) |
| I-02 | `Snapper.forceGridOff` n'est plus lu par Draft | 🔎 | – | *lecture*. Attribut inoffensif, conservé avec la logique `hideGrid` / `showGrid` d'origine. |
| I-03 | Liens vers une fonction interne à un Body : « Link(s) go out of the allowed scope » | ✅ | 1 + 3 | T16 (0 avertissement après réenregistrement), *mesure* `freecadcmd` (15 → 0 avertissements sur `cube.FCStd`) |
| I-04 | Géométrie des faces fausse dans un Body ou App::Part (mélange des modes de sélection 0 et 1) | ✅ | 1 | T20 (❌ → ✅), T15 |
| I-05 | `DiffuseColor` alpha=0 : face **transparente** sous 1.x ; mauvais index de face | ✅ | 1 | T21 (❌ → ✅), *mesure* `ShapeAppearance.Transparency` |
| I-06 | `__getstate__` / `__setstate__` au lieu de `dumps` / `loads` | ✅ | 3 | T14, T16 |
| I-07 | `package.xml` obsolète (0.20) | ✅ | 3 | – |

## Qt / PySide6

| ID | Problème | Statut | Lot | Preuve |
|---|---|---|---|---|
| Q-01 | Connexions `SIGNAL("valueChanged(double)")` (style ancien) ; `valueChanged[float]` absent sous PySide6 | ✅ | 2 | *mesure*, T09, T22 |
| Q-02 | Widgets pris dans `QtGui` (ne fonctionnaient que grâce à la couche de compatibilité de FreeCAD) | ✅ | 2 | T06 à T13 |
| Q-03 | `getStandardButtons()` renvoyait l'entier `0x00200000` | ✅ | 2 | T13, T22 |
| Q-04 | `QComboBox.SizeAdjustPolicy(2)` | ✅ | 2 | T09 |
| Q-05 | Polices enregistrées dans Qt au démarrage ; Coin ne les voit pas | ✅ / ⚠️ | 3 | Enregistrement déplacé à l'activation. Pour le rendu 3D, voir la limitation L-05. |
| Q-06 ➕ | `clicked.connect(lambda obj=obj …)` reçoit `obj=False` sous PySide6 : boutons Modifier et Supprimer de l'inventaire **inopérants** | ✅ | 2 | *mesure*, T22 et T23 (❌ sur le code du lot 1 → ✅) |
| Q-07 ➕ | Lambdas inutiles sur `activated` / `textChanged` | ✅ | 2 | – |

## Python 3

| ID | Problème | Statut | Lot | Preuve |
|---|---|---|---|---|
| P-01 | `faces.sort()` sur des `DocumentObject` → `TypeError` dès que deux objets sont sélectionnés | ✅ | 1 | T18 (❌ → ✅) |
| P-02 | `prop in "selectedPoint"` (test de sous-chaîne) | ✅ | 1 | T11 |
| P-03 | Arguments par défaut mutables | ✅ | 4 | – |
| P-04 | 14 `except:` nus | ✅ | 4 | Il n'en reste aucun. |
| P-05 | `str(int) != 0` toujours vrai | ✅ | 4 | – |

## Bogues fonctionnels

| ID | Problème | Statut | Lot | Preuve |
|---|---|---|---|---|
| F-01 | `ToleranceFontSize` écrasait `FontSize` | ✅ | 1 | – |
| F-02 | Annotations jamais rangées dans le dossier de leur plan | ✅ | 1 | T12 (❌ → ✅) |
| F-03 | « 0.050 µm » affiché pour 0,05 mm (comparaison `==` au lieu d'une affectation) | ✅ | 1 | T11, captures avant et après |
| F-04 | `IsActive()` calculait la géométrie à chaque rafraîchissement de l'interface et écrivait dans la console | ✅ | 1 | – |
| F-05 | `IndexError` dans `IsActive` / menu contextuel (objet sélectionné sans sous-élément) | ✅ | 1 | – |
| F-06 | Annotation existante jamais retrouvée (formats de liens différents) | ✅ | 1 | T17 (❌ → ✅) |
| F-07 | `l.touch` sans parenthèses | ✅ | 1 | – |
| F-08 | `UnboundLocalError` dans l'inventaire (GT sans caractéristique) | ✅ | 1 | – |
| F-09 | `PointWithOffset` non recalculé quand la face bouge | ✅ | 1 | – |
| F-10 | `setEditorMode` appelé à chaque `onChanged` | 🔎 | – | Coût négligeable mesuré dans les tests. Conservé pour ne pas modifier le comportement de l'éditeur de propriétés. |
| F-11 | Échap pendant la saisie du point : suppression du « dernier DS du document » | ✅ | 4 | T25 |
| F-12 | `IndexError` au-delà de 99 annotations ou DS | ✅ | 4 | Les noms de commande (AP, DF, DS, GT) restent plafonnés à 99, sans erreur, comme à l'origine. |
| F-13 | Module inutilisable sans interface | 🔎 / ✅ | 3 | *mesure* `freecadcmd` : ouverture et recalcul OK, avant comme après. Le flag `gui` est corrigé. |
| F-14 | `getRotation()` renvoie `None`, exception masquée | ✅ | 4 | T11 |
| F-15 ➕ | Le champ « Name: » affichait la valeur (« AP1 ») au lieu de son libellé | ✅ | 5 | T27 (libellés), revue de code |

## Linux / Windows et intégration

| ID | Problème | Statut | Lot | Preuve |
|---|---|---|---|---|
| L-01 | Chemins et casse des fichiers | 🔎 | – | *lecture* : `os.path.join` partout. Aucun test effectué sous Linux (non disponible). |
| L-02 | Régénération du `.rcc` impossible sans le `rcc.exe` tiers ; FreeCAD 1.1 ne fournit pas `rcc` | ⚠️ | 5 | Contournement : la page de préférences est lue depuis le fichier `.ui`. Le `.rcc` existant (icônes) se charge sous Qt 6. Voir `Resources/ReadMe.txt`. |
| L-03 / L-05 | Polices Coin et **symboles GD&T Unicode non rendus** dans la vue 3D (glyphe manquant) | ⚠️ | – | T28 et captures. **Défaut préexistant**, reproduit avec le code d'origine (`gdt_render_top_code_origine.png`). |
| W-01 | `InitGui` chargeait tout le MOD au démarrage | ✅ | 3 | T24 |
| W-02 | Pas de traductions | ✅ | 5 | T26, T27 |
| W-03 | `Msg()` / `Log()` | ✅ | 3 | – |
| W-04 | Une trentaine de `print()` de débogage | ✅ | 4 | – |
| W-05 | `numpy` importé pour `size()` | ✅ | 1 + 4 | – |
| W-06 | `Doc/` et `rcc.exe` copiés dans le dossier Mod | ✅ | 0 | `tools/install_mod.py` les exclut. Leur retrait du dépôt est laissé à la décision du mainteneur. |

## Hors MOD (constatés, non corrigeables ici)

| Fichier | Constat |
|---|---|
| `Doc/Assembly.FCStd` | Exige l'atelier externe Assembly4 (`Asm4_libs`) ; `Pocket001` est invalide dans le fichier. Identique avec le code d'origine. |
| `Doc/Plaque.FCStd` | `Annotation6` dérive de 40,4 mm et `AP7` de 2,3 mm au recalcul : la face `Chamfer001` n'a plus le même numéro sous FreeCAD 1.1 (nommage topologique, TNP). Identique avec le code d'origine (*mesure* `drift.py`). Il faut réaffecter ces éléments à la main. |
