Qt resources of the GD&T workbench
==================================

dd_resources.rcc holds the icons under the ":/dd/icons/..." prefix. Keep this prefix:
the paths of the characteristic / modifier icons are stored in the documents
(properties CharacteristicIcon and FeatureControlFrameIcon).

The file loads under Qt 5 and Qt 6 (checked with FreeCAD 1.1.3, Qt 6.8.3).

Regenerating dd_resources.rcc (only needed when an icon is added or changed):
  FreeCAD does not ship the "rcc" tool. Use the rcc of a Qt installation, or RCC Extended
  (Windows: https://github.com/zedxxx/rccextended/releases/tag/v1.0.5, rcc.exe in this folder),
  then run from this folder:
      python compile_resources_pack.py

The preference page (ui/preferences-gdt.ui) is loaded from the file itself since
version 1.0.0: it can be edited without regenerating the .rcc.
