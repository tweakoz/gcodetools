#!/usr/bin/env python3
# Facing generator
# Copyright 2017 - Michael T. Mayers
# Licensed under the GPLV3 - see https://www.gnu.org/licenses/gpl-3.0.html

import os,sys, string, math

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QWidget, QComboBox
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtGui import (QPalette, QPixmap)

#############################################################################

def frange(start, stop, step):
    i = 0
    while start + i * step <= stop:
        yield start + i * step
        i += 1
def invfrange(start, stop, step):
    i = 0
    while start + i * step > stop:
        yield start + i * step
        i += 1


#############################################################################

sfmtable = { # mtl, sfm
    "Aluminum, 7075": { "sfm": 300, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Aluminum, 6061": { "sfm": 280, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Aluminum, 2024": { "sfm": 200, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Aluminum, Cast": { "sfm": 134, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Brass": { "sfm": 400, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Bronze": { "sfm": 150, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Copper": { "sfm": 100, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Cast Iron (soft)": { "uhp": .25, "sfm": 80, "intooth": { "min": 0.005, "max": 0.01 } },
    "Cast Iron (hard)": { "uhp": .25, "sfm": 50, "intooth": { "min": 0.005, "max": 0.01 } },
    "Copper": { "sfm": 100, "uhp": .25, "intooth": { "min": 0.005, "max": 0.01 } },
    "Mild Steel": { "sfm": 90, "uhp": 1.4, "intooth": { "min": 0.005, "max": 0.01 } },
    "Cast Steel": { "sfm": 80, "uhp": 2.5, "intooth": { "min": 0.005, "max": 0.01 } },
    "Alloy Steels (hard)": { "sfm": 40, "uhp": 2.5, "intooth": { "min": 0.005, "max": 0.01 } },
    "Tool Steel": { "sfm": 50, "uhp": 2.5, "intooth": { "min": 0.005, "max": 0.01 } },
    "Stainless Steel": { "sfm": 60, "uhp": 2.5, "intooth": { "min": 0.005, "max": 0.01 } },
}

#############################################################################

class FacerWindow(QWidget):

    ###################################

    def __init__(self):
        super(FacerWindow, self).__init__()
        mainLayout = QGridLayout()
        #####################
        self.z1 = 1.0
        self.z2 = 1.5
        self.safeZ = 1.75
        self.x1 = 1.0
        self.x2 = 2.0
        self.y1 = 1.0
        self.y2 = 2.0
        self.docZ = 1/16.0
        self.docXY = 0.1
        self.feedRate = 6.0
        self.toolDiam = 0.25
        self.flutes = 2
        self.row = 0
        self.mrr = 0

        self.docXY = self.toolDiam*0.33

        #####################
        def rowpp():
            rv = self.row
            self.row = self.row+1
            return rv
        #####################
        def makeNumEdit(var,label,row):
            numlabl = QLabel(label)
            numedit = QLineEdit( )
            numedit.setMaxLength(10)
            numedit.setText("%g"%getattr(self,var))
            def numeditchanged(text):
              print( "labl<%s> var<%s> val<%s>"% (label,var,text) )
              try:
                if var=="toolDiam":
                  self.docXY = float(text)*0.33
                setattr(self,var,float(text))
              except:
                None
              self.refresh()
            numedit.textChanged.connect(numeditchanged)
            mainLayout.addWidget(numlabl, row, 0)
            mainLayout.addWidget(numedit, row, 1, 1, 1)
            return numedit
        #####################

        makeNumEdit("x1","x1",rowpp())
        makeNumEdit("x2","x2",rowpp())
        makeNumEdit("y1","y1",rowpp())
        makeNumEdit("y2","y2",rowpp())
        makeNumEdit("z1","z1",rowpp())
        makeNumEdit("z2","z2",rowpp())
        makeNumEdit("safeZ","safeZ",rowpp())
        makeNumEdit("flutes","flutes",rowpp())
        makeNumEdit("feedRate","Feed Rate (in/min)",rowpp())
        makeNumEdit("toolDiam","Tool Diam (in)",rowpp())

        self.docXYedit = makeNumEdit("docXY","Radial(XY) DOC (in)",rowpp())

        docZrow = rowpp()
        self.cbox_docZ = QComboBox()
        self.cbox_docZ.addItem('1/16 in', 1.0/16.0)
        self.cbox_docZ.addItem("1/32 in", 1.0/32.0)
        self.cbox_docZ.addItem("1/64 in", 1.0/64.0)
        self.cbox_docZ.setCurrentIndex(self.cbox_docZ.findText("1/16 in"))
        doczlabl = QLabel("docZ(select)")
        def docZchanged():
            data = self.cbox_docZ.itemData(self.cbox_docZ.currentIndex())
            setattr(self,"docZ",data)
            self.refresh()
        self.cbox_docZ.activated.connect(docZchanged)
        mainLayout.addWidget(doczlabl, docZrow, 0, 1, 1)
        mainLayout.addWidget(self.cbox_docZ, docZrow, 1, 1, 1)

        #####################

        mtlrow = rowpp()
        self.cbox_mtl = QComboBox()

        for k in sfmtable:
            v = sfmtable[k]
            sfm = v["sfm"]
            self.cbox_mtl.addItem(k, v)

        self.cbox_mtl.activated.connect(self.refresh)

        sfmlabl = QLabel("Material (SFM)")
        mainLayout.addWidget(sfmlabl, mtlrow, 0, 1, 1)
        mainLayout.addWidget(self.cbox_mtl, mtlrow, 1, 1, 1)
        self.cbox_mtl.setCurrentIndex(0)

        #####################

        sfmrow = rowpp()
        sfmlabl = QLabel("Material SFM (Surface-Ft/Min)")
        self.sfmvalu = QLineEdit()
        self.sfmvalu.readOnly = True
        self.sfmvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(sfmlabl, sfmrow, 0, 1, 1)
        mainLayout.addWidget(self.sfmvalu, sfmrow, 1, 1, 1)

        #####################

        rpmrow = rowpp()
        rpmlabl = QLabel("Material RPM (SFM * DIA * 12 / \N{GREEK SMALL LETTER PI} )")
        self.rpmvalu = QLineEdit()
        self.rpmvalu.readOnly = True
        self.rpmvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(rpmlabl, rpmrow, 0, 1, 1)
        mainLayout.addWidget(self.rpmvalu, rpmrow, 1, 1, 1)

        #####################

        iptrow = rowpp()
        iptlabl = QLabel("Material FEED (in-tooth)")
        self.iptvalu = QLineEdit()
        self.iptvalu.readOnly = True
        self.iptvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(iptlabl, iptrow, 0, 1, 1)
        mainLayout.addWidget(self.iptvalu, iptrow, 1, 1, 1)

        #####################

        ipmrow = rowpp()
        ipmlabl = QLabel("Material FEED (in/min)")
        self.ipmvalu = QLineEdit()
        self.ipmvalu.readOnly = True
        self.ipmvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(ipmlabl, ipmrow, 0, 1, 1)
        mainLayout.addWidget(self.ipmvalu, ipmrow, 1, 1, 1)

        #####################

        mrrrow = rowpp()
        mrrlabl = QLabel("Material RR (in^3/min)")
        self.mrrvalu = QLineEdit()
        self.mrrvalu.readOnly = True
        self.mrrvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(mrrlabl, mrrrow, 0, 1, 1)
        mainLayout.addWidget(self.mrrvalu, mrrrow, 1, 1, 1)

        #####################

        uhprow = rowpp()
        uhplabl = QLabel("Material UHP (unit-hp)")
        self.uhpvalu = QLineEdit()
        self.uhpvalu.readOnly = True
        self.uhpvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(uhplabl, uhprow, 0, 1, 1)
        mainLayout.addWidget(self.uhpvalu, uhprow, 1, 1, 1)

        #####################

        hprrow = rowpp()
        hprlabl = QLabel("Material HP (required)")
        self.hprvalu = QLineEdit()
        self.hprvalu.readOnly = True
        self.hprvalu.setStyleSheet("background-color: rgb(32,32,32); color: rgb(128,128,128); ")
        mainLayout.addWidget(hprlabl, hprrow, 0, 1, 1)
        mainLayout.addWidget(self.hprvalu, hprrow, 1, 1, 1)

        #####################

        self.outedit = QTextEdit( )
        self.outedit.setStyleSheet("background-color: rgb(96, 32, 96); color: rgb(255,255,0); ")
        mainLayout.addWidget(self.outedit, 0, 2, hprrow-1, 1)

        outgen = QPushButton("Generate GCode" )
        outgen.setStyleSheet("background-color: rgb(192, 184, 192); border-radius: 1; ")
        mainLayout.addWidget(outgen, hprrow-1, 2, 1, 1)
        outgen.pressed.connect(self.generate)

        outwri = QPushButton("Write GCode" )
        outwri.setStyleSheet("background-color: rgb(208, 176, 208); border-radius: 2; ")
        mainLayout.addWidget(outwri, hprrow, 2, 1, 1)
        outwri.pressed.connect(self.write)

        #####################
 
        self.setLayout(mainLayout)
        self.setWindowTitle("Facing GCode Generator \N{COPYRIGHT SIGN} 2017 - TweakoZ")
        self.refresh()

    ###################################

    def refresh(self):
        try:
          V = self.cbox_mtl.itemData(self.cbox_mtl.currentIndex())
          #print( "V<%s>"%V)
          SFM = V["sfm"]
          INT = V["intooth"]
          setattr(self,"sfm",SFM)
          RPM = (SFM*12/math.pi)/self.toolDiam

          IPTmin = INT["min"]
          IPTmax = INT["max"]
          IPMmin = RPM*IPTmin*self.flutes
          IPMmax = RPM*IPTmax*self.flutes

          MRRmin = IPMmin*self.docZ*self.docXY
          MRRmax = IPMmax*self.docZ*self.docXY

          UHP = V["uhp"]
          HPRmin = UHP*MRRmin
          HPRmax = UHP*MRRmax

          self.sfmvalu.setText("%d"%SFM)
          self.rpmvalu.setText("%d"%RPM)
          self.iptvalu.setText("%g ... %g" % (IPTmin,IPTmax))
          self.ipmvalu.setText("%0.1f ... %0.1f" % (IPMmin,IPMmax))
          self.mrrvalu.setText("%0.1f ... %0.1f" % (MRRmin,MRRmax))
          self.uhpvalu.setText("%f" % UHP)
          self.hprvalu.setText("%0.3f ... %0.3f" % (HPRmin,HPRmax))

          self.docXYedit.setText("%g"%self.docXY)

        except:
          None
    ###################################

    def generate(self):
        self.gcode = "(Generated by facing generator, yo..)\n"
        self.gcode = "G20\n"
        #print("x1<%f> x2<%f> y1<%f> y2<%f>"%(self.x1,self.x2,self.y1,self.y2))
        done = False
        xa = self.x1
        xb = self.x2
        xa, xb = xb, xa
        if self.z1<self.z2:
            self.z1,self.z2 = self.z2,self.z1
        print( "Z1<%f> Z2<%f>"%(self.z1,self.z2))
        for z in invfrange(self.z1,self.z2,-self.docZ):
          self.gcode += "G00 Z%g (move to safeZ)\n" % (self.safeZ)
          self.gcode += "G00 X%g Y%g (move to startXY)\n" % (xa, self.y1)
          self.gcode += "G00 Z%g (move to startZ)\n" % (z)
          for y in frange(self.y1,self.y2,self.docXY):
            self.gcode += "G01 X%g Y%g F%g (sweep)\n" % (xa,y,self.feedRate)
            self.gcode += "G00 Y%g (move to next)\n" % (y+self.docXY)
            xa, xb = xb, xa
        self.gcode += "M2\n"
        self.outedit.setText(self.gcode)

    def write(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        savename = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","GCode Files (*.ngc)", options=options )
        print(savename)
        f = open(savename[0], 'wb')
        f.write(self.gcode.encode('utf-8'))
        f.close()

#############################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = FacerWindow()
    win.setStyleSheet("background: rgb(160,160,174)")
    win.show()
    sys.exit(app.exec_())
