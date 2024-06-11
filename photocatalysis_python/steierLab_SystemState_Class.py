from steierLab_MFC_Class import MFC
from steierLab_Gauge_Class import Gauge
from steierLab_cmd_Class import cmd
from steierLab_Solenoid_Class import Solenoid
from steierLab_User_Class import User

from datetime import date
import time
import os
import shutil
import numpy as np

class SystemState:
    def __init__(self):
        self.logInterval = 1
        self.numGauges = 4
        self.numMFCs = 4
        self.numSolenoids = 12

        self.gauges = [Gauge() for _ in range(self.numGauges)]
        # populate gauge information here if necessary
        for i in range(0, self.numGauges):
            self.gauges[i].number = i
        self.MFCs = [MFC() for _ in range(self.numMFCs)]
        # populate MFC information here for use later if necessary
        for i in range(0, self.numMFCs):
            self.MFCs[i].number = i
        self.solenoids = [Solenoid() for _ in range(self.numSolenoids)]
        #populate solenoid information here for use later if necessary
        for i in range(0 , self.numSolenoids):
            self.solenoids[i].number = i

        self.currentSystemTime = time.time()
        #print(self.currentSystemTime) #debug output
        self.currentSystemElapsedTime = 0
        self.previousElapsedTime = 0
        self.processStartTime = 0
        self.checkStateElapsedTime = 0
        self.logProcessElapsedTime = 0
        #print(self.systemStateHistory)
        self.systemStateHistoryLength = 0

        self.solenoidLog = [0 for _ in range (self.numSolenoids)]
        self.gaugeLog = [0 for _ in range (self.numGauges)]
        self.MFC_setPointLog = [0 for _ in range (self.numMFCs)]
        self.MFC_actualLog = [0 for _ in range (self.numMFCs)]

    def check(self ,whichArduino , tempCurrentUser):
        functionStartTime = time.time()
        self.currentSystemTime = time.time()
        self.currentSystemElapsedTime = self.currentSystemTime - self.processStartTime
        for j in range(self.numSolenoids):
            pass
        for j in range(self.numGauges):
            self.gauges[j].getPressure(whichArduino , tempCurrentUser)
        for j in range(self.numMFCs):
            self.MFCs[j].getFlowrate(whichArduino , tempCurrentUser)

        self.checkStateElapsedTime = time.time() - functionStartTime

    def wreck(self):
        pass

    def checkNoLog(self ,whichArduino , tempCurrentUser):
        functionStartTime = time.time()
        self.currentSystemTime = time.time()
        self.currentSystemElapsedTime = self.currentSystemTime - self.processStartTime
        for j in range(self.numSolenoids):
            pass
        for j in range(self.numGauges):
            self.gauges[j].getPressureNoLog(whichArduino , tempCurrentUser)
        for j in range(self.numMFCs):
            self.MFCs[j].getFlowrateNoLog(whichArduino , tempCurrentUser)

        self.checkStateElapsedTime = time.time() - functionStartTime

    def updateHistory(self):
        #populate history array with solenoid positions etc
        #has same structure as whats in log file. Consider rewriting logging part to just use the self.systemStateHistory

        #generate temporary list of array elements, then append temporary list to systemStateHistory
        tempList = np.zeros((1 , 30))

        tempList[0][0] = self.currentSystemTime
        tempList[0][1] = self.currentSystemElapsedTime
        #increment through solenoids
        for j in range(self.numSolenoids):
            self.solenoidLog.append(self.solenoids[j].currentValue) #update solenoid positions
        for j in range(self.numGauges):
            self.gaugeLog.append(self.gauges[j].currentValue) #update gauge pressures/voltages
        for j in range(self.numMFCs):
            self.MFC_actualLog.append(self.MFCs[j].currentFlowRate) #update MFC actual flow rate
            self.MFC_setPointLog.append(self.MFCs[j].currentSetPoint) #update MFC set point flow rate

        self.currentSystemTime_log.append(self.currentSystemTime)
        self.currentSystemElapsedTime_log.append(self.currentSystemElapsedTime)

        self.systemStateHistoryLength += 1 #increment length of history array - ie dimension that stores the history thing

    def logToFile(self , tempCurrentUser):
        # open file
        tempFunctionStartTime = time.time()
        self.previousElapsedTime = self.currentSystemElapsedTime
        #check to see if directory/path exists
        tempSystemStateLogDirectory = os.path.join(tempCurrentUser.parentDirectory , tempCurrentUser.name , tempCurrentUser.experimentDirectory , (str(tempCurrentUser.experimentDate) + "_" + tempCurrentUser.experimentName +"_" + str(tempCurrentUser.experimentTime)) )
        if(os.path.exists(tempSystemStateLogDirectory) == 0):
            print("Path " + tempSystemStateLogDirectory + " does not exist")
            os.mkdir(tempSystemStateLogDirectory)
        tempSystemStateLogFilename = os.path.join(tempSystemStateLogDirectory , (tempCurrentUser.experimentName + "_log.txt"))
        #Write top line of csv file. Check if file exists, if does not exist, then make it and populate it. Otherwise, ignore
        if(os.path.isfile(tempSystemStateLogFilename) !=1):
            tempSystemLog = open(tempSystemStateLogFilename, "a+")
            #print("tempSystemLog does not exist. Gonna populate the top line with what the columns be")
            tempSystemLog.write("currentSystemTime" + "\t")
            tempSystemLog.write("currentElapsedTime" + "\t")
            for j in range(self.numSolenoids):
                tempSystemLog.write("Solenoid_" + str(j) + "\t")
            # write all gauge pressures - iterate through systemState.gaugePressures
            for j in range(self.numGauges):
                tempSystemLog.write("gaugeVoltage_" + str(j)  + "\t")
                tempSystemLog.write("gaugePressure_" + str(j) + "\t")
            for j in range(self.numMFCs):
                tempSystemLog.write("MFC_" + str(j) + "_currentVoltage" + "\t")
                tempSystemLog.write("MFC_" + str(j) + "_currentFlowRate" + "\t")
                tempSystemLog.write("MFC_" + str(j) + "_currentSetpoint" + "\t")

            tempSystemLog.write("logSaveTime" + "\r\n")  # prints elapsed time for writing system state to file, cant hurt to have this here and keep an eye on it
            tempSystemLog.close()#close file

        else:
            #print("systemLogFile exists, not gonna add what the columns do")
            pass
        
        tempSystemLog = open(tempSystemStateLogFilename, "a+")
        tempSystemLog.write(str(self.currentSystemTime) + "\t")
        tempSystemLog.write(str(self.currentSystemElapsedTime) + "\t")
        # tab delimited? Comma delimited?
        # write all solenoid positions - for loop and iterate through systemState.solenoids[]
        for j in range(self.numSolenoids):
            tempSystemLog.write(str(self.solenoids[j].currentValue) + "\t")
        # write all gauge pressures - iterate through systemState.gaugePressures
        for j in range(self.numGauges):
            tempSystemLog.write(str(self.gauges[j].currentVoltage) + "\t")
            tempSystemLog.write(str(self.gauges[j].currentPressure) + "\t")
        for j in range(self.numMFCs):
            tempSystemLog.write(str(self.MFCs[j].currentReadVoltage) + "\t")
            tempSystemLog.write(str(self.MFCs[j].currentFlowRate) + "\t")
            tempSystemLog.write(str(self.MFCs[j].currentSetPoint) + "\t")

        tempFunctionElapsedTime = time.time() - tempFunctionStartTime
        tempSystemLog.write(str(tempFunctionElapsedTime) + "\r\n")  # prints elapsed time for writing system state to file, cant hurt to have this here and keep an eye on it
        tempSystemLog.close()
        #self.updateHistory()
        self.logProcessElapsedTime = time.time() - tempFunctionStartTime

    def loadHistory(self , tempCurrentUser):
        #read in params from file to 2D array.
        #plot all different params in various matplotlib structures maybe have radio buttons for which thing I'm plotting. Turn on auto-range for all graphs.
        #radio button to select either whole timescale or just like last 5 mins or so.
        #MFC has liner vertical axis
        #gauge has logarithmic y axis
        #may have to move this to the tkinter processes in case I cant have it here. Would be sad :(
        tempLogFilename = os.path.join(tempCurrentUser.parentDirectory , tempCurrentUser.logDirectory , (tempCurrentUser.experimentName + "_log.txt") )
        #check to see if file exists. If does not, assign tempLogHistory to a row of zeroes, so can still graph but doesnt actually show anything. Once file is generated, will read from fiel and start plotting actual data.
        tempSystemLogFile = open(tempLogFilename)
        #read in file somehow. Have it so that it appends an array containing all the values for one specific time to a big array containing all previous values
        #Basically a 2D array that can be addressed as systemStateValues[i][j] - i describes which time/instance j describes which parameter.
        #tab delimited and newline denoted by \n
        tempLogHistory = np.loadtxt(tempLogFilename , delimiter= "\t")
        print(tempLogFilename[0][:])

        #once whole thing is read in, can plot. Introduce all sorts of switching behavior via radio buttons in GUI. Maybe have one tab to do all pressures, one tab to do all flow rates
        #buttons to change which one is displayed, with option to do all at once.

        return tempLogHistory