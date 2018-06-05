"""
PyQt4 GUI program for Agilent E8257D Synthesizer
Send command to turn RF on/off, and change frequency
Created on Nov. 7, 2016

v1.0: Reads frequency and output state, changable by user via mouse scroll on slider, or text+enter
v1.1: Update slider size for easier use
v1.2: Resize GPIB inst. selector
v1.3: Resize widgets
v1.4: Add label at top for multiple inst. connections
v1.5: Add power control
@author: Daryl Spencer
"""

from PyQt4 import QtGui, QtCore, Qt
import sys
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyvisa as visa



__version__ = '1.5'

class color_QLineEdit(QLineEdit):

    def __init__(self, text):
        super(color_QLineEdit, self).__init__(text)

        self.textChanged.connect(self.change_my_color)
        self.returnPressed.connect(self.reset_my_color)
        
        self.reset_my_color()
        
    def change_my_color(self):
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor('black'))
        palette.setColor(self.foregroundRole(), QColor('white'))
        self.setPalette(palette)
        
    def reset_my_color(self):
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor('white'))
        palette.setColor(self.foregroundRole(), QColor('black'))
        self.setPalette(palette)
        

class FreqSynth(QMainWindow):
    
    def __init__(self):
        super(FreqSynth, self).__init__()
        
        self.conBool=False #Bool to show GPIB connection
        self.initUI()
        self.freqbox.setText("select GPIB # and input/scroll to desired freq")
        
    def initUI(self):      
        self.main_frame =QWidget()
        self.name = QLabel("")
        self.freqbox = color_QLineEdit("")
        self.freqbox.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Minimum)
        self.pwrbox = color_QLineEdit("")
        self.pwrbox.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Minimum)
        self.output = QCheckBox()
        self.output.setText("Output On/Off")
#        self.outputlbl = QLabel("Output On/Off", self)
        self.freqlbl = QLabel("Actual Frequency: ")
        self.freqtext = QLabel("")
        self.pwrlbl = QLabel("Actual Power: ")
        self.pwrtext = QLabel("")
        self.slider = QSlider()
        self.slider.setMinimum(-10)
        self.slider.setMaximum(10)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)
        self.slider.setToolTip("Scroll or Use Arrows (fine)")
        self.slider.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
#        print('%s' %self.slider.sizePolicy())
#        self.slider.resize(10,20)
        self.sliderres = QComboBox(self)
        for i in np.logspace(0,10,11):
#            print("%1.0e Hz" %i)
            self.sliderres.addItem("%1.0e Hz" %i)
        self.sliderres.setCurrentIndex(4)
        
        
        self.gpibInst = QComboBox(self)
        self.gpibInst.setMaximumWidth(400)
        self.gpibInst.setMinimumWidth(300)
        self.gpibInst.addItem('Select GPIB Instrument')
        self.gpibInst.addItems(self.gpibFind())
        self.inst = 'None'
        
        ## Signal/Slot connections
        self.freqbox.returnPressed.connect(self.freqChanged) #Send new freq. to instr.
        self.pwrbox.returnPressed.connect(self.pwrChanged) #Send new pwr. to instr.
        self.connect(self.gpibInst, SIGNAL('currentIndexChanged(QString)'),self.gpibConnect)
        self.connect(self.output, SIGNAL('stateChanged(int)'),self.outputChanged)
        self.slider.valueChanged.connect(self.sliderChanged) #Add slider value*resolution to current frequency
        self.sliderres.currentIndexChanged.connect(self.resetSlider) #reset slider to 0 when new resolution selected

        ## Layout widgets on screen
        hbox = QHBoxLayout()
        for w in [self.freqlbl, self.freqtext, self.output, self.pwrlbl, self.pwrtext]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
        hbox2 = QHBoxLayout()
        for w in [self.slider, self.sliderres]:
            hbox2.addWidget(w)
            hbox2.setAlignment(w, Qt.AlignVCenter)  
        hbox3 = QHBoxLayout()
        for w in [self.freqbox, self.pwrbox]:
            hbox3.addWidget(w)
            hbox3.setAlignment(w, Qt.AlignVCenter)
#        hbox4 = QHBoxLayout()
#        #for w in [self.gpibInst]:
#        hbox4.addWidget(self.gpibInst)
#        hbox4.setAlignment(w, Qt.AlignVCenter)  
        vbox = QVBoxLayout()
        vbox.addWidget(self.name)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        #vbox.addWidget(self.freqbox)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.gpibInst)
        vbox.setAlignment(self.gpibInst, Qt.AlignCenter)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)  
        
    def resetSlider(self):
        self.slider.setValue(0)
        
    def sliderChanged(self):
        print(self.slider.value(), float(self.sliderres.currentText()[:-2]))
        newfreq = self.freq +  self.slider.value()*float(self.sliderres.currentText()[:-2])
        self.freqbox.setText("%s" %newfreq)
        self.freqChanged()
        self.freqbox.reset_my_color()
        self.slider.setValue(0)
    def outputChanged(self, state=0):
        if state==2:
            self.func_write(':OUTPUT ON; *WAI')
        elif state==0:
            self.func_write(':OUTPUT OFF; *WAI')
            
    def freqChanged(self):
        self.func_write(':FREQ:FIXED %s; *WAI' %self.freqbox.text()); 
        print('Fixed freq: %s' %self.freqbox.text())
        self.freqRead()
        
    def freqRead(self):
        print('freq read')
        self.freq=self.func_read(':FREQ:FIXED?',ascii=1)[0]
        self.freqtext.setText("%s Hz" %self.freq)

    def pwrChanged(self):
        self.func_write(':POW %s; *WAI' %self.pwrbox.text()); 
        print('Fixed pwr: %s' %self.pwrbox.text())
        self.pwrRead()
        
    def pwrRead(self):
        print('pwr read')
        self.pwr=self.func_read(':POW?',ascii=1)[0]
        self.pwrtext.setText("%s dBm" %self.pwr)
        
    def outputRead(self):
        print('output read')
        self.out=(self.func_read(':OUTPUT?',ascii=0)[0])
        if self.out=='1':
            print("output on")
            self.output.setCheckState(2) #output is read to be on
        elif not(self.out)=='0':
            print("output off")
            self.output.setCheckState(0) #output is read to be off
#            self.output.set
    ## GPIB Functions
    def func_write(self,func):
        if self.conBool:
            self.inst.write(func)   
        else:
            print('not connected')
    def func_read(self,func,ascii=0):
        if self.conBool and ascii:
            result=self.inst.query_ascii_values(func)
            return result
        elif self.conBool and not(ascii):
            result=self.inst.query(func)
            return result
        else:
            print('not connected')
    def gpibDisconnect(self):
        self.inst.close()
        self.outputChanged(2) #turn off
        
    def gpibConnect(self,address):    
        rm = visa.ResourceManager()
        print(address);print(str(address))
        self.inst = rm.open_resource(str(address))
        self.instname = self.inst.query('*IDN?')
        print(self.instname)
        self.name.setText("%s" %self.instname)
#        if self.rstbox.checkState() ==2:
#            self.inst.write('*RST; *WAI') #reset instrument
#            self.inst.write('*CLS; *WAI') #clear instrument
        self.conBool=True
        self.inst.chunck_size = pow(2,20)
        self.freqRead()
        self.freqbox.setText("%s" %self.freq)
        self.pwrRead()
        self.pwrbox.setText("%s" %self.pwr)
        self.output.blockSignals(True)
        self.outputRead()
        self.output.blockSignals(False)

#        self.output.set
    def gpibFind(self):
        rm = visa.ResourceManager()
        devices=rm.list_resources()
        return devices
        
def main():
    app = QtGui.QApplication(sys.argv)
    form = FreqSynth()
    form.setWindowTitle("Agilent Freq. Controller")
    form.resize(365,190)
    form.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()        
