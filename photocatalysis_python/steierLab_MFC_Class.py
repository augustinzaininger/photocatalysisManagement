from steierLab_cmd_Class import cmd
from steierLab_Parameter_Class import Parameter
import time
import serial
from serial import Serial
import serial.tools.list_ports
import re

class MFC:
    def __init__(self):
        self.actionBrackets = ['<', '>']
        self.queryBrackets = ['?', '?']
        self.panicBrackets = ['!', '!']
        self.startBrackets = [self.actionBrackets[0], self.queryBrackets[0], self.panicBrackets[0]]
        self.endBrackets = [self.actionBrackets[1], self.queryBrackets[1], self.panicBrackets[1]]
        self.inputPin = 0
        self.outputPin = 0
        self.number = 0
        self.solenoidNumber = 0
        self.currentReadVoltage = 0
        self.currentFlowRate = 0
        self.currentSetPoint = 0
        self.currentSetPointVoltage = 0
        self.currentPercentSetPoint = 0
        self.currentSetPointFlowRateParam = Parameter("Set Point Flow Rate")
        self.currentSetPointFlowRateParam.value = 0.0
        self.manufacturer = ""
        self.modelNumber = ""
        #info for setting the flow rate - currently will be hard coded into the arduino. Evenutally may pass it to the arduino in arduino.configure()
        self.inputResponseGradient = 0
        self.inputResponseTurnOnVoltage = 0
        self.inputResponseBaseValue = 0
        self.inputResponseMaxValue = 0
        #info for decoding output of the MFC
        self.outputResponseGradient = 0
        self.outputResponseTurnOnVoltage = 0
        self.outputResponseBaseValue = 0
        self.outputResponseMaxValue = 0

    def setFlowrate(self , tempPercentFlowrate, whichArduino , tempCurrentUser):
        # initialise command
        setMFC = cmd()
        # populate command
        setMFC.brackets = self.actionBrackets
        setMFC.subsystem = "mfc"
        setMFC.location = self.number
        setMFC.value = tempPercentFlowrate  # float
        setMFC.commandString = setMFC.brackets[0] + setMFC.subsystem + '_' + str(setMFC.location) + '_' + str(setMFC.value) + setMFC.brackets[1]
        # send command
        #print(setMFC.commandString)
        whichArduino.send(setMFC.commandString)
        setMFC.timeOut = time.time()
        time.sleep(setMFC.responseDelay)
        # await response
        setMFC.returnString = whichArduino.receive()
        #print(setMFC.returnString)
        setMFC.timeIn = time.time()
        setMFC.elapsedTime = setMFC.timeIn - setMFC.timeOut
        # parse response and store in systemState.MFCs[wherever]
        returnedSegments = re.split('<|_|>', setMFC.returnString)
        # print(returnedSegments)
        setMFC.returnValue = float(returnedSegments[3])
        self.currentSetPointFlowRate = setMFC.returnValue
        # save value to appropriate struct in array MFCs
        # logCommandToFile(setMFC)
        # testing/debugging
        # print(setMFC.commandString)
        # print(setMFC.returnString)
        # print(setMFC.returnValue)
        # print(setMFC.elapsedTime)
        setMFC.logToFile(tempCurrentUser)

    def getFlowrate(self , whichArduino , tempCurrentUser):
        # initialise command
        getMFC = cmd()
        # populate command
        getMFC.brackets = self.queryBrackets
        getMFC.subsystem = "mfc"
        getMFC.location = self.number
        getMFC.value = 0
        getMFC.commandString = getMFC.brackets[0] + getMFC.subsystem + '_' + str(getMFC.location) + '_' + str(getMFC.value) + getMFC.brackets[1]
        # send command
        #print(getMFC.commandString)
        whichArduino.send(getMFC.commandString)
        getMFC.timeOut = time.time()
        time.sleep(getMFC.responseDelay)
        # await response
        getMFC.returnString = whichArduino.receive()
        #print(getMFC.returnString)
        getMFC.timeIn = time.time()
        getMFC.elapsedTime = getMFC.timeIn - getMFC.timeOut
        # parse response and store in systemState.MFCs[wherever]
        returnedSegments = re.split('\?|_', getMFC.returnString)
        #print(returnedSegments)
        getMFC.returnValue = float(returnedSegments[3])
        self.currentReadVoltage = getMFC.returnValue
        # logCommandToFile(getMFC)
        # testing/debugging
        # print(getMFC.commandString)
        # print(getMFC.returnString)
        # print(getMFC.returnValue)
        # print(getMFC.elapsedTime)
        getMFC.logToFile(tempCurrentUser)

    def getFlowrateNoLog(self , whichArduino , tempCurrentUser):
        #identical to above, just doesn't log to file. Mainly for updating within GUI
        # initialise command
        getMFC = cmd()
        # populate command
        getMFC.brackets = self.queryBrackets
        getMFC.subsystem = "mfc"
        getMFC.location = self.number
        getMFC.value = 0
        getMFC.commandString = getMFC.brackets[0] + getMFC.subsystem + '_' + str(getMFC.location) + '_' + str(getMFC.value) + getMFC.brackets[1]
        # send command
        #print(getMFC.commandString)
        whichArduino.send(getMFC.commandString)
        getMFC.timeOut = time.time()
        time.sleep(getMFC.responseDelay)
        # await response
        getMFC.returnString = whichArduino.receive()
        #print(getMFC.returnString)
        getMFC.timeIn = time.time()
        getMFC.elapsedTime = getMFC.timeIn - getMFC.timeOut
        # parse response and store in systemState.MFCs[wherever]
        returnedSegments = re.split('\?|_', getMFC.returnString)
        # print(returnedSegments)
        getMFC.returnValue = float(returnedSegments[3])
        self.currentReadVoltage = getMFC.returnValue
        # logCommandToFile(getMFC)
        # testing/debugging
        # print(getMFC.commandString)
        # print(getMFC.returnString)
        # print(getMFC.returnValue)
        # print(getMFC.elapsedTime)

