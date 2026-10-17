# GeometricDimensioningAndTolerancing gui init module
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 Juan Vañó Cerdá <juavacer@inf.upv.es>              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
"""GD&T workbench registration.

This file is executed when FreeCAD starts: it must stay light. Everything
else (Draft, Coin, Qt resources, commands) is imported in Initialize(), i.e.
the first time the workbench is activated.
"""

import os

import FreeCAD
import FreeCADGui

# InitGui.py is exec'd by FreeCAD without __file__: locate the module folder
# through a regular module of the workbench.
import GDT_locator

# exec() runs this file inside a function of FreeCADGuiInit: module-level
# names are local to that function and invisible from the class body and
# methods unless they are declared global.
global GDTWB_PATH, GDTWB_ICON
GDTWB_PATH = os.path.dirname(GDT_locator.__file__)
GDTWB_ICON = os.path.join(GDTWB_PATH, "Resources", "icons", "GDT.svg")


class GDandTWorkbench(Workbench):
    "Geometric Dimensioning & Tolerancing workbench"
    MenuText = "GD&T"
    ToolTip = "Geometric Dimensioning & Tolerancing"
    Icon = GDTWB_ICON

    # Command names are stored in user toolbars: they must not change.
    CREATION_COMMANDS = ["dd_datumFeature", "dd_datumSystem",
                         "dd_geometricTolerance", "dd_annotationPlane"]
    INVENTORY_COMMANDS = ["dd_inventory"]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        "Executed the first time the workbench is activated"
        import GDT  # registers the Qt resources (:/dd/...) used by the commands
        import datumFeature
        import datumSystem
        import geometricTolerance
        import annotationPlane
        import inventory

        self.registerFonts()

        commands = self.CREATION_COMMANDS + self.INVENTORY_COMMANDS
        self.appendToolbar("GD&T Tools", commands)
        self.appendMenu("GD&T Tools", commands)

        FreeCADGui.addIconPath(":/dd/icons")
        FreeCADGui.addPreferencePage(":/dd/ui/preferences-gdt.ui", "GDT")
        FreeCAD.Console.PrintLog("Loading Geometric Dimensioning & Tolerancing... done\n")

    @staticmethod
    def registerFonts():
        """Make the GD&T fonts available to the Qt widgets.

        Note: the 3D annotations are drawn by Coin3D, which only sees the fonts
        installed in the operating system.
        """
        from PySide import QtGui
        fonts_path = os.path.join(GDTWB_PATH, "Resources", "fonts")
        for name in ("osifont-lgpl3fe.ttf", "Iso-Gps.ttf"):
            font_id = QtGui.QFontDatabase.addApplicationFont(os.path.join(fonts_path, name))
            if font_id < 0:
                FreeCAD.Console.PrintWarning("GD&T: cannot load font {}\n".format(name))

    def Activated(self):
        "Executed when the workbench is activated"
        FreeCAD.Console.PrintLog("Geometric Dimensioning & Tolerancing workbench activated\n")

    def Deactivated(self):
        "Executed when the workbench is deactivated"
        FreeCAD.Console.PrintLog("Geometric Dimensioning & Tolerancing workbench deactivated\n")

    def ContextMenu(self, recipient):
        "Right click in the 3D view or the tree ('view' or 'tree')"
        # The creation commands are offered only when faces are selected
        selection = FreeCADGui.Selection.getSelectionEx()
        showCmdList = bool(selection) and bool(selection[0].SubObjects) and all(
            sub.ShapeType == 'Face' for sub in selection[0].SubObjects)
        if showCmdList:
            self.appendContextMenu("", "Separator")
            self.appendContextMenu("", self.CREATION_COMMANDS)
        self.appendContextMenu("", self.INVENTORY_COMMANDS)
        self.appendContextMenu("", "Separator")


FreeCADGui.addWorkbench(GDandTWorkbench)
