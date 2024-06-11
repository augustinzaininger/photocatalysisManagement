from steierLab_cmd_Class import cmd
from serial import Serial
import serial.tools.list_ports
import re

from datetime import date
import time
import os
import shutil
import csv

class Solenoid:
    def __init__(self):
        self.actionBrackets = ['<', '>']
        self.queryBrackets = ['?', '?']
        self.panicBrackets = ['!', '!']
        self.startBrackets = [self.actionBrackets[0], self.queryBrackets[0], self.panicBrackets[0]]
        self.endBrackets = [self.actionBrackets[1], self.queryBrackets[1], self.panicBrackets[1]]
        self.currentValue = 0
        self.outputPin = 0
        self.number = 0
        self.kineticsDelay = 0.1
        self.modelNumber = ""#not sure if I need this, might just keep it in as extra documentation and for debugging.

    def actuateSolenoid(self , value , whichArduino , tempCurrentUser):
        self.currentValue = value
        solenoidCommand = cmd()
        solenoidCommand.brackets = self.actionBrackets
        solenoidCommand.subsystem = "sol"
        solenoidCommand.location = self.number
        solenoidCommand.value = value
        solenoidCommand.commandString = solenoidCommand.brackets[0] + solenoidCommand.subsystem + '_' + str(solenoidCommand.location) + '_' + str(solenoidCommand.value) + solenoidCommand.brackets[1]
        # send command
        #print(solenoidCommand.commandString)
        whichArduino.send(solenoidCommand.commandString)
        #print("command sent")
        solenoidCommand.timeOut = time.time()
        # await response
        time.sleep(solenoidCommand.responseDelay)
        solenoidCommand.returnString = whichArduino.receive()
        #print(solenoidCommand.returnString)
        solenoidCommand.timeIn = time.time()
        solenoidCommand.elapsedTime = solenoidCommand.timeIn - solenoidCommand.timeOut
        # parse response, store data in systemState.solenoid.wherever
        returnedSegments = re.split('<|_|>', solenoidCommand.returnString)
        #print(returnedSegments)
        solenoidCommand.returnValue = float(returnedSegments[3])
        solenoidCommand.logToFile(tempCurrentUser)

    def actuateSolenoidNoLog(self, value, whichArduino, tempCurrentUser):
        #same as above, just doesnt log to file
        self.currentValue = value
        solenoidCommand = cmd()
        solenoidCommand.brackets = self.actionBrackets
        solenoidCommand.subsystem = "sol"
        solenoidCommand.location = self.number
        solenoidCommand.value = value
        solenoidCommand.commandString = solenoidCommand.brackets[0] + solenoidCommand.subsystem + '_' + str(
            solenoidCommand.location) + '_' + str(solenoidCommand.value) + solenoidCommand.brackets[1]
        # send command
        # print(solenoidCommand.commandString)
        whichArduino.send(solenoidCommand.commandString)
        # print("command sent")
        solenoidCommand.timeOut = time.time()
        # await response
        time.sleep(solenoidCommand.responseDelay)
        solenoidCommand.returnString = whichArduino.receive()
        # print(solenoidCommand.returnString)
        solenoidCommand.timeIn = time.time()
        solenoidCommand.elapsedTime = solenoidCommand.timeIn - solenoidCommand.timeOut
        # parse response, store data in systemState.solenoid.wherever
        returnedSegments = re.split('<|_|>', solenoidCommand.returnString)
        # print(returnedSegments)
        solenoidCommand.returnValue = float(returnedSegments[3])

