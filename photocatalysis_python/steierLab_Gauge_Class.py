from steierLab_cmd_Class import cmd
import time
import re

class Gauge:
    def __init__(self):
        self.actionBrackets = ['<', '>']
        self.queryBrackets = ['?', '?']
        self.panicBrackets = ['!', '!']
        self.startBrackets = [self.actionBrackets[0], self.queryBrackets[0], self.panicBrackets[0]]
        self.endBrackets = [self.actionBrackets[1], self.queryBrackets[1], self.panicBrackets[1]]
        self.number = 0
        self.outputPin = 0
        self.gaugeEnablePin = 0
        self.currentValue = 0
        self.currentVoltage = 0
        self.currentPressure = 0
        self.manufacturer = ""
        self.modelNumber = ""
        self.outputResponseGradient = 0
        self.outputResponseTurnOnVoltage = 0
        self.ouptutResponseBaseValue = 0
        self.outputResponseMaxValue = 0
        self.isEnabled = 0

    def enable(self , whichArduino , tempCurrentUser):
        enableGauge = cmd()
        enableGauge.brackets = self.actionBrackets
        enableGauge.subsystem = "gaj"
        enableGauge.location = self.number
        enableGauge.value = 100
        enableGauge.commandString = enableGauge.brackets[0] + enableGauge.subsystem + '_' + str(enableGauge.location) + '_' + str(enableGauge.value) + enableGauge.brackets[1]
        whichArduino.send(enableGauge.commandString)
        enableGauge.timeOut = time.time()
        time.sleep(enableGauge.responseDelay)
        # await response
        enableGauge.returnString = whichArduino.receive()
        print(enableGauge.returnString)
        enableGauge.timeIn = time.time()
        enableGauge.elapsedTime = enableGauge.timeIn - enableGauge.timeOut
        # parse response and store in systemState.gauges[wherever]
        returnedSegments = re.split('<|_|>', enableGauge.returnString)
        print(returnedSegments)
        enableGauge.returnValue = float(returnedSegments[2])
        self.isEnabled = 1



    def getPressure(self , whichArduino , tempCurrentUser):
        #initialise command
        readGauge = cmd()
        #populate command
        readGauge.brackets = self.queryBrackets
        readGauge.subsystem = "gaj"
        readGauge.location = self.number
        readGauge.value = 0
        readGauge.commandString = readGauge.brackets[0] + readGauge.subsystem + '_' + str(readGauge.location) + '_' + str(readGauge.value) + readGauge.brackets[1]
        #send command
        whichArduino.send(readGauge.commandString)
        readGauge.timeOut = time.time()
        time.sleep(readGauge.responseDelay)
        #await response
        readGauge.returnString = whichArduino.receive()
        readGauge.timeIn = time.time()
        readGauge.elapsedTime = readGauge.timeIn - readGauge.timeOut
        #parse response and store in systemState.gauges[wherever]
        returnedSegments = re.split('\?|_' , readGauge.returnString)
        #print(returnedSegments)
        readGauge.returnValue = float(returnedSegments[3])
        self.currentVoltage = readGauge.returnValue
        #save value to appropriate struct in array gauges
        #logCommandToFile(readGauge)
        #testing/debugging
        #print(readGauge.commandString)
        #print(readGauge.returnString)
        #print(readGauge.returnValue)
        #print(readGauge.elapsedTime)
        readGauge.logToFile(tempCurrentUser)
        return readGauge.returnValue

    def getPressureNoLog(self , whichArduino , tempCurrentUser):
        #identical to above command, just doesnt log to file. Mainly for updating within GUI
        # initialise command
        readGauge = cmd()
        # populate command
        readGauge.brackets = self.queryBrackets
        readGauge.subsystem = "gaj"
        readGauge.location = self.number
        readGauge.value = 0
        readGauge.commandString = readGauge.brackets[0] + readGauge.subsystem + '_' + str(
            readGauge.location) + '_' + str(readGauge.value) + readGauge.brackets[1]
        # send command
        whichArduino.send(readGauge.commandString)
        readGauge.timeOut = time.time()
        time.sleep(readGauge.responseDelay)
        # await response
        readGauge.returnString = whichArduino.receive()
        readGauge.timeIn = time.time()
        readGauge.elapsedTime = readGauge.timeIn - readGauge.timeOut
        # parse response and store in systemState.gauges[wherever]
        returnedSegments = re.split('\?|_', readGauge.returnString)
        # print(returnedSegments)
        readGauge.returnValue = float(returnedSegments[3])
        self.currentPressure = readGauge.returnValue
        # save value to appropriate struct in array gauges
        # logCommandToFile(readGauge)
        # testing/debugging
        # print(readGauge.commandString)
        # print(readGauge.returnString)
        # print(readGauge.returnValue)
        # print(readGauge.elapsedTime)
        return readGauge.returnValue