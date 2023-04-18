#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 Juan Vanyo Cerda <juavacer@inf.upv.es>             *
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

from GDT import *

gdt = GDTWidget()
gdt.dialogWidgets.append( groupBoxWidget(Text='Constituents', List=[comboLabelWidget(Text='Primary:',List=[]),comboLabelWidget(Text='Secondary:',List=[]), comboLabelWidget(Text='Tertiary:',List=[]), comboLabelWidget(Text='Feature Control:',List=[])]) )


class DatumSystemCommand:
    def __init__(self):
        self.iconPath = ':/dd/icons/datumSystem.svg'
        self.toolTip = 'Add Datum System'
        self.Dictionary = []
        for i in range(1,100):
            self.Dictionary.append('DS'+str(i))
        self.idGDT = 2

    def Activated(self):
        listDF = [None] + getAllDatumFeatureObjects()
        print("listDF {}".format(listDF))
        # A C F G L M P S T U X
        Code = ['', '\u24B6', '\u24B8', '\u24BB', '\u24BC','\u24C1', '\u24C2', '\u24C5', '\u24C8', '\u24C9', '\u24CA', '\u24CD']
        Icon = ['', ':/dd/icons/FeatureControlFrame/derivedFeature.svg', ':/dd/icons/FeatureControlFrame/minimaxFeature.svg', ':/dd/icons/FeatureControlFrame/freeState.svg', ':/dd/icons/FeatureControlFrame/leastSquares.svg', ':/dd/icons/FeatureControlFrame/leastMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/maximumMaterialCondition.svg', ':/dd/icons/FeatureControlFrame/projectedToleranceZone.svg', ':/dd/icons/FeatureControlFrame/regardlessOfFeatureSize.svg',
        ':/dd/icons/FeatureControlFrame/tangentPlane.svg', ':/dd/icons/FeatureControlFrame/unequalBilateral.svg', ':/dd/icons/FeatureControlFrame/maximumInscribed.svg']
        ToolTip = ['Feature control frame', 'Derived feature', 'Minimax (Chebyshev) feature', 'Free state', 'Least squares (Gaussian) feature', 
        'Least material condition', 'Maximum material condition', 'Projected tolerance zone', 'Regardless of feature size', 'Tangent plane', 'Unequal Bilateral', 'Maximum inscribed feature']
        # Don't forget to dimmension the Label to the same size as Icon / ToolTip
        # Used to define the size of the Combo list in the UI
        Label = ['','','','','','','','','','','','']        
        gdt.dialogWidgets[0] = ( groupBoxWidget(Text='Constituents', List=[comboLabelWidget(Text='Primary:',List=listDF),comboLabelWidget(Text='Secondary:',List=listDF),comboLabelWidget(Text='Tertiary:',List=listDF), comboLabelWidget(Text='Feature Control:',List=Code)]) )
        gdt.activate(idGDT = self.idGDT, dialogTitle=self.toolTip, dialogIconPath=self.iconPath, endFunction=self.Activated, Dictionary=self.Dictionary)

    def GetResources(self):
        return {
            'Pixmap' : self.iconPath,
            'MenuText': self.toolTip,
            'ToolTip':  self.toolTip
            }

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return len(getAllDatumFeatureObjects()) > 0
        else:
            return False

FreeCADGui.addCommand('dd_datumSystem', DatumSystemCommand())
