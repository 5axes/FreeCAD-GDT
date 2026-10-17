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
_characteristics = makeCharacteristics()  # single source of the 14 characteristics
gdt.dialogWidgets.append( comboLabelWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Characteristic:'), List=_characteristics.Label, Icons=_characteristics.Icon) )
gdt.dialogWidgets.append( fieldLabelComboWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Tolerance value:'), Circumference = [], List=[], Icons=[], ToolTip=[]) )
gdt.dialogWidgets.append( comboLabelWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Datum system:'), List=[]) )
gdt.dialogWidgets.append( comboLabelWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Active annotation plane:'), List=[]) )

class GeometricToleranceCommand:
    def __init__(self):
        self.iconPath = ':/dd/icons/geometricTolerance.svg'
        self.Dictionary = []
        for i in range(1,100):
            self.Dictionary.append('GT'+str(i))
        self.idGDT = 3
        self.FeatureControlFrame = makeFeatureControlFrame()

    def Activated(self):
        ContainerOfData = makeContainerOfData()
        if getAnnotationObj(ContainerOfData):
            annotation = getAnnotationObj(ContainerOfData)
            title = translate("GDT", 'Add Geometric Tolerance to {}').format(annotation.Label)
            gdt.dialogWidgets[3] = None
            if annotation.GT == []:
                gdt.dialogWidgets[1] = fieldLabelComboWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Tolerance value:'), Circumference = ['',':/dd/icons/diameter.svg'], Diameter = ContainerOfData.diameter, List=self.FeatureControlFrame.Label, Icons=self.FeatureControlFrame.Icon, ToolTip=self.FeatureControlFrame.toolTip)
            else:
                if annotation.toleranceSelectBool:
                    gdt.dialogWidgets[1] = fieldLabelComboWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Tolerance value:'), Circumference = ['',':/dd/icons/diameter.svg'], Diameter = annotation.diameter, tolerance = annotation.toleranceDiameter, List=self.FeatureControlFrame.Label, Icons=self.FeatureControlFrame.Icon, ToolTip=self.FeatureControlFrame.toolTip)
                else:
                    gdt.dialogWidgets[1] = fieldLabelComboWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Tolerance value:'), Circumference = ['',':/dd/icons/diameter.svg'], Diameter = annotation.diameter, toleranceSelect=False, lowLimit = annotation.lowLimit, highLimit = annotation.highLimit, List=self.FeatureControlFrame.Label, Icons=self.FeatureControlFrame.Icon, ToolTip=self.FeatureControlFrame.toolTip)
        else:
            title = translate("GDT", 'Add Geometric Tolerance')
            showGrid()
            gdt.dialogWidgets[3] = comboLabelWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Active annotation plane:'), List=getAllAnnotationPlaneObjects())
            gdt.dialogWidgets[1] = fieldLabelComboWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Tolerance value:'), Circumference = ['',':/dd/icons/diameter.svg'], Diameter = ContainerOfData.diameter, List=self.FeatureControlFrame.Label, Icons=self.FeatureControlFrame.Icon, ToolTip=self.FeatureControlFrame.toolTip)
        gdt.dialogWidgets[2] = comboLabelWidget(Text=QT_TRANSLATE_NOOP("GDT", 'Datum system:'), List=[None]+getAllDatumSystemObjects())
        gdt.activate(idGDT = self.idGDT, dialogTitle=title, dialogIconPath=self.iconPath, endFunction=self.Activated, Dictionary=self.Dictionary)

    def GetResources(self):
        return {
            'Pixmap' : self.iconPath,
            'MenuText': QT_TRANSLATE_NOOP("dd_geometricTolerance", 'Add Geometric Tolerance'),
            'ToolTip':  QT_TRANSLATE_NOOP("dd_geometricTolerance", 'Add a geometric tolerance on the selected faces')
            }

    def IsActive(self):
        if len(getObjectsOfType('AnnotationPlane')) == 0:
            return False
        if getSelection():
            for i in range(len(getSelectionEx())):
                if len(getSelectionEx()[i].SubObjects) == 0:
                    return False
                for j in range(len(getSelectionEx()[i].SubObjects)):
                    if getSelectionEx()[i].SubObjects[j].ShapeType == 'Face':
                        pass
                    else:
                        return False
        else:
            return False
        return True

FreeCADGui.addCommand('dd_geometricTolerance', GeometricToleranceCommand())
