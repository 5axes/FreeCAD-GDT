#! /usr/bin/env python
import os, glob

qrc_filename = 'gdt.qrc'
assert not os.path.exists(qrc_filename)

qrc = '''<RCC version="1.0">
    <qresource prefix="/dd">'''
for fn in glob.glob('icons/*.svg') + glob.glob('icons/Characteristic/*.svg') + glob.glob('icons/FeatureControlFrame/*.svg') + glob.glob('ui/*.ui'):
    qrc = qrc + '\n\t\t<file>%s</file>' % fn
qrc = qrc + '''\n\t</qresource>
</RCC>'''

print(qrc)

f = open(qrc_filename,'w')
f.write(qrc)
f.close()

os.system('rcc -binary %s -o dd_resources.rcc' % qrc_filename)
os.remove(qrc_filename)
