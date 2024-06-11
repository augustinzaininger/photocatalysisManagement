from steierLab_MFC_Class import MFC
from steierLab_Gauge_Class import Gauge
from steierLab_cmd_Class import cmd
from steierLab_Solenoid_Class import Solenoid
from steierLab_User_Class import User
from steierLab_SystemState_Class import SystemState

from tkinter import messagebox


class FillToPressure_process:
    def __init__(self , inputSystemState , tempCurrentUser):
        #self.__init__(self)
        self.isMFC_flowGood = 0
        self.referenceMFC = 0
        self.fillPressure = 0
        self.referenceGauge = 0
        self.ventSolenoid = 0
        self.MFC_ratios = []
        self.stopConditionTripped = 0





    def processRun(self , inputSystemState , tempArduino , tempCurrentUser):
        #set MFC flow rates
        for i in range(inputSystemState.numMFCs):
            inputSystemState.MFCs[i].setFlowRate(inputSystemState.MFCs[i].percentFlowRate , tempArduino , tempCurrentUser)

        #await for user input to say that MFC flows are good
        while(self.isMFC_flowGood == 0):
            pass

        #close vent Solenoid
        if(self.isMFC_flowGood == 1):
            pass

        #poll gauge pressure every 100ms

        #Trip stop condition
        if(inputSystemState.gauges[self.referenceGauge] >= self.fillPressure):
            stopConditionTripped = 1

        #close solenoids on MFCs
        for i in range(inputSystemState.numSolenoids):
            inputSystemState.solenoids[i].actuateSolenoid(0 , tempArduino , tempCurrentUser)

        #write zero to all MFCs

        for i in range(inputSystemState.numMFCs):
            inputSystemState.MFCs[i].setFlowRate(0 , tempArduino , tempCurrentUser)

        messagebox.showinfo("System Filled" , "System has been filled to set pressure")

        