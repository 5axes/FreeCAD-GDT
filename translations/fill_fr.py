#!/usr/bin/env python3
"""Fill translations/GDT_fr.ts with the French texts below.

Workflow (Qt tools are shipped with FreeCAD in <FreeCAD>/lib/qt6/bin):

    lupdate GDT.py InitGui.py annotationPlane.py datumFeature.py datumSystem.py \\
            geometricTolerance.py inventory.py Resources/ui/preferences-gdt.ui \\
            -ts translations/GDT_fr.ts -target-language fr_FR -no-obsolete
    python translations/fill_fr.py
    lrelease translations/GDT_fr.ts

Only entries still marked "unfinished" are filled; texts missing from the
table are reported so that they can be added.
"""

import os
import sys
import xml.etree.ElementTree as ET

FR = {
    # task panels
    "Name:": "Nom :",
    "Offset:": "Décalage :",
    "Datum feature:": "Élément de référence :",
    "Active annotation plane:": "Plan d'annotation actif :",
    "Create corresponding Datum System": "Créer le système de référence correspondant",
    "Constituents": "Constituants",
    "Primary:": "Primaire :",
    "Secondary:": "Secondaire :",
    "Tertiary:": "Tertiaire :",
    "Characteristic:": "Caractéristique :",
    "Tolerance value:": "Valeur de tolérance :",
    "Datum system:": "Système de référence :",
    "In annotation:": "Dans l'annotation :",
    "Diameter:": "Diamètre :",
    "Limit": "Limites",
    "Low": "Mini",
    "High": "Maxi",
    "Indicates whether the tolerance applies to a given diameter":
        "Indique si la tolérance s'applique à un diamètre donné",
    "Add Annotation Plane": "Ajouter un plan d'annotation",
    "Add Datum Feature": "Ajouter un élément de référence",
    "Add Datum Feature to {}": "Ajouter un élément de référence à {}",
    "Add Datum System": "Ajouter un système de référence",
    "Add Geometric Tolerance": "Ajouter une tolérance géométrique",
    "Add Geometric Tolerance to {}": "Ajouter une tolérance géométrique à {}",
    # command tool tips
    "Add an annotation plane on the selected face": "Ajoute un plan d'annotation sur la face sélectionnée",
    "Add a datum feature on the selected faces": "Ajoute un élément de référence sur les faces sélectionnées",
    "Add a datum system made of existing datum features":
        "Ajoute un système de référence composé d'éléments de référence existants",
    "Add a geometric tolerance on the selected faces": "Ajoute une tolérance géométrique sur les faces sélectionnées",
    "Inventory of the elements of GD&T": "Inventaire des éléments GD&T",
    "List, modify and delete the GD&T elements of the document":
        "Liste, modifie et supprime les éléments GD&T du document",
    # inventory
    "Modify": "Modifier",
    "Delete": "Supprimer",
    "Visualize": "Visualiser",
    "Error": "Erreur",
    "You can not change the DF to an annotation where one already exists":
        "Impossible de déplacer l'élément de référence vers une annotation qui en possède déjà un",
    "You can not delete AP in use": "Impossible de supprimer un plan d'annotation utilisé",
    # characteristics (ISO 1101)
    "Straightness": "Rectitude",
    "Flatness": "Planéité",
    "Circularity": "Circularité",
    "Cylindricity": "Cylindricité",
    "Profile of a line": "Forme d'une ligne",
    "Profile of a surface": "Forme d'une surface",
    "Perpendicularity": "Perpendicularité",
    "Angularity": "Inclinaison",
    "Parallelism": "Parallélisme",
    "Symmetry": "Symétrie",
    "Position": "Localisation",
    "Concentricity": "Concentricité",
    "Circular run-out": "Battement circulaire",
    "Total run-out": "Battement total",
    # feature control frame modifiers
    "Feature control frame": "Modificateur",
    "Derived feature": "Élément dérivé",
    "Minimax (Chebyshev) feature": "Élément minimax (Tchebychev)",
    "Free state": "État libre",
    "Least squares (Gaussian) feature": "Élément des moindres carrés (gaussien)",
    "Least material condition": "Minimum de matière",
    "Maximum material condition": "Maximum de matière",
    "Projected tolerance zone": "Zone de tolérance projetée",
    "Regardless of feature size": "Indépendamment de la taille",
    "Tangent plane": "Plan tangent",
    "Unequal Bilateral": "Zone de tolérance décalée",
    "Maximum inscribed feature": "Élément inscrit maximal",
    # preferences page
    "General settings": "Paramètres généraux",
    "Text": "Texte",
    "Size": "Taille",
    "Default size for texts": "Taille par défaut des textes",
    "Tolerance Size": "Taille des tolérances",
    "Default size for tolerance texts": "Taille par défaut des textes de tolérance",
    "Family": "Police",
    "Text family": "Police des textes",
    "Iso-Gps": "Iso-Gps",
    "Color": "Couleur",
    "This is the default color text": "Couleur par défaut des textes",
    "Lines": "Lignes",
    "Width": "Épaisseur",
    "This is the default color for objects being drawn while in construction mode.":
        "Couleur par défaut des lignes d'annotation",
    "Grid": "Grille",
    "Always show the grid": "Toujours afficher la grille",
    "mm": "mm",
    "Show the unit suffix in dimensions": "Afficher l'unité dans les cotes",
    "Change Face Color": "Colorer les faces annotées",
    "The number of horizontal or vertical lines of the grid": "Nombre de lignes horizontales ou verticales de la grille",
    "Scaling factor applied to lines:": "Facteur d'échelle des lignes :",
    "If checked, the Draft grid will always be visible when the GDT workbench is active. Otherwise only when the annotation plane is needed.":
        "Si coché, la grille Draft reste visible tant que l'atelier GDT est actif. Sinon, elle n'apparaît que lorsque le plan d'annotation est nécessaire.",
}


def main(path):
    tree = ET.parse(path)
    missing = []
    for message in tree.iter("message"):
        source = message.findtext("source")
        translation = message.find("translation")
        if translation is None or translation.get("type") != "unfinished":
            continue
        if source in FR:
            translation.text = FR[source]
            del translation.attrib["type"]
        else:
            missing.append(source)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    for source in missing:
        print("missing translation:", source)
    return 1 if missing else 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "GDT_fr.ts")))
