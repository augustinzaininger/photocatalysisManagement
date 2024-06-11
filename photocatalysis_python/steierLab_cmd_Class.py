from serial import Serial
import serial.tools.list_ports
import re

from datetime import date
import time
import os
import shutil
import csv
import serial
from serial import Serial
import serial.tools.list_ports
import re

class cmd:
    def __init__(self):
        self.commandLength = 12
        self.cmdString = ""
        self.brackets = ['<' , '>']
        self.commandString = ""
        self.started = 0
        self.finished = 0
        self.type = 0
        self.subsystem = 0
        self.location = 0
        self.number = 0
        self.value = 0
        self.isValid = 0
        self.timeIn = 0
        self.timeOut = 0
        self.elapsedTime = 0
        self.returnValue = 0
        self.returnString = 0
        self.responseDelay = 0.005


    def logToFile(self , tempCurrentUser):
        tempCommandLogFilename = os.path.join(tempCurrentUser.baseDirectory, tempCurrentUser.name , tempCurrentUser.experimentDirectory , (tempCurrentUser.experimentDate + "_" + tempCurrentUser.experimentName + "_" + str(tempCurrentUser.experimentTime)), "commandLog.txt")
        #logic here maybe to create directory in case it doesnt exist?
        tempCommandLog = open(tempCommandLogFilename, "a+")
        tempCommandLog.write(str(time.time()) + "\t")
        tempCommandLog.write(str(self.commandString) + "\t")
        tempCommandLog.write(str(self.value) + "\t")
        tempCommandLog.write(str(self.returnString) + "\t")
        tempCommandLog.write(str(self.returnValue) + "\t")
        tempCommandLog.write(str(self.elapsedTime) + "\r\n")
