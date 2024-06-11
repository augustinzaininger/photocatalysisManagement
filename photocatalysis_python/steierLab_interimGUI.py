import tkinter as tk
import tkinter.messagebox
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter import Menu
from tkinter import messagebox
from tkinter import filedialog


import random
import array
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import serial
from serial import Serial
import serial.tools.list_ports
import re

from datetime import date
import time
import os
import shutil
import csv
import multiprocessing
import threading
import logging



from steierLab_Arduino_Class import ArduinoObject
from steierLab_searchForAvailableSerial import searchForAvailableSerial
from steierLab_SystemState_Class import SystemState
from steierLab_Gauge_Class import Gauge
from steierLab_Solenoid_Class import Solenoid
from steierLab_cmd_Class import cmd
from steierLab_MFC_Class import MFC
from steierLab_User_Class import User
from steierLab_FillToPressure_process_Class import FillToPressure_process



##### define any global variables for system



class MainWindow(tk.Tk):
    #define window and any other objects GUI will need.
    def __init__(self):
        super().__init__()
        self.processStarted = 0
        self.processStopped = 0
        #self.master = Tk()
        #self.master.title("Interim System Control")
        self.tempFrame = ttk.Frame(self)
        self.tempFrame.grid()

        #define tabs
        self.tabList = ttk.Notebook(self.tempFrame)
        self.tab_systemSetup = ttk.Frame(self.tabList)
        self.tab_fillToPressure = ttk.Frame(self.tabList)
        self.tab_realTimeControl = ttk.Frame(self.tabList)
        self.tab_debugging = ttk.Frame(self.tabList)
        self.tab_realTimeControl = ttk.Frame(self.tabList)
        self.tabList.add(self.tab_systemSetup , text = 'System Setup')
        self.tabList.add(self.tab_fillToPressure, text='Fill To Pressure')
        self.tabList.add(self.tab_realTimeControl , text = 'Real Time Control')
        self.tabList.add(self.tab_debugging , text = 'Debugging')

        #self.tabList.add(self.tab_graphs , text = 'Graphs')

        #define system variables
        self.systemState = SystemState()
        self.currentUser  = User()
        self.arduinoSerialPort = ""
        self.arduinoBaudRate = 2000000
        self.arduino = ArduinoObject(self.arduinoSerialPort , self.arduinoBaudRate)
        self.baseDirectory = "/" #hard code a default directory?

        self.fillToPressure = FillToPressure_process(self.systemState , self.currentUser)
        self.fillPressure = 10

        self.availableSerialPorts = searchForAvailableSerial()

        self.isRunning = tk.BooleanVar(value=False)
        self.isFillToPressure = tk.BooleanVar(value=False)

        #self.solenoidState_0 = tk.BooleanVar(value=False)
        #self.solenoidState_1 = tk.BooleanVar(value=False)
        #self.solenoidState_2 = tk.BooleanVar(value=False)
        #self.solenoidState_3 = tk.BooleanVar(value=False)



        #print(self.systemState.numSolenoids)
        self.solenoidCheckbuttonStates = []
        for i in range(self.systemState.numSolenoids):
            self.solenoidCheckbuttonStates.append(tk.BooleanVar(value=False))
            #print(self.solenoidCheckbuttonStates[i])

        #### System Setup Tab Layout

        #System Directory
        def browseDirectory():
            directoryName = filedialog.askdirectory(initialdir="/")
            baseDirectory = directoryName + "/"
            print(baseDirectory) #debug
            entry_baseDirectory.delete(0,END)
            entry_baseDirectory.insert(END, baseDirectory)
            self.currentUser.baseDirectory = baseDirectory
        #username
        def loginAsUser():
            self.currentUser.name = entry_username.get()
            print(self.currentUser.name)#debugOutput
            #put in other stuff to enable buttons when logged in - maybe have flags and do this in GUI update function

        # Serial Port definition
        def imSuperCereal():
            cerealPortToUse = combo_availableSerial.get()
            print(cerealPortToUse)
            self.arduinoSerialPort = cerealPortToUse
            self.arduino.comms.port = cerealPortToUse
            self.arduino.comms.baudrate = self.arduino.baudrate
            self.arduino.initialise()

        def updateCerealList():
            self.availableSerialPorts = searchForAvailableSerial()
            print(self.availableSerialPorts)
            combo_availableSerial["values"] = self.availableSerialPorts[0]
            print("I'm super cereal")

        lbl_systemDirectory = Label(self.tab_systemSetup , text="System Directory")
        lbl_systemDirectory.grid(column=0,row=1)
        btn_exploreDirectory = Button(self.tab_systemSetup, text="Browse Directory", command=browseDirectory)
        btn_exploreDirectory.grid(column=2,row=1)
        entry_baseDirectory = Entry(self.tab_systemSetup)
        entry_baseDirectory.insert(END , self.baseDirectory)
        entry_baseDirectory.grid(column=1,row=1)

        entry_username = Entry(self.tab_systemSetup)
        entry_username.grid(column=0, row=0)
        btn_enterUsername = Button(self.tab_systemSetup , text = "Login as User", command = loginAsUser)
        btn_enterUsername.grid(column=1, row=0)

        lbl_arduinoSerial = Label(self.tab_systemSetup, text="Arduino Serial Port")
        lbl_arduinoSerial.grid(column=0, row=3)
        combo_availableSerial = Combobox(self.tab_systemSetup)
        combo_availableSerial.grid(column=1, row=3)
        combo_availableSerial["values"] = self.availableSerialPorts[0]
        btn_useSelectedPort = Button(self.tab_systemSetup, text="Use Selected", command=imSuperCereal)
        btn_useSelectedPort.grid(column=2, row=3)
        btn_updateSerialPortList = Button(self.tab_systemSetup, text="Update List", command=updateCerealList)
        btn_updateSerialPortList.grid(column=2, row=4)




        #### System Control Tab Layout

        def update_flowRate_MFC():
            isEntryBox_number = 0
            tempEntryBox_value = 0
            for i in range(self.systemState.numMFCs):
                tempMFC_number=i
                string_MFC_flowRate = self.MFC_GUI_setpointEntries[tempMFC_number].get()
                isEntryBox_number = string_MFC_flowRate.replace(".", "").isnumeric() #checks to see if string is numerical, isnumeric() can't deal with decimal points for whatever reason so need to use .replace("." , "") to remove
                #print(isEntryBox_number)#debug output

                if(isEntryBox_number == 1):
                    tempEntryBox_value = float(string_MFC_flowRate)

                if(isEntryBox_number == 1 and tempEntryBox_value <= 50 and tempEntryBox_value>=0):
                    self.systemState.MFCs[tempMFC_number].currentSetPoint = tempEntryBox_value
                    self.systemState.MFCs[tempMFC_number].currentPercentSetPoint = (self.systemState.MFCs[tempMFC_number].currentSetPoint/50)*100
                    self.systemState.MFCs[tempMFC_number].setFlowrate(self.systemState.MFCs[tempMFC_number].currentPercentSetPoint , self.arduino , self.currentUser)
                    print(string_MFC_flowRate)#debug output
                    #something here for setting MFC flow rate
                    self.MFC_GUI_setpointActuals[tempMFC_number].configure(text=str(self.systemState.MFCs[tempMFC_number].currentSetPoint))

                elif (isEntryBox_number==0):
                    tkinter.messagebox.showerror("Set MFC Error" , "Ensure entry is a number")

                elif(tempEntryBox_value > 50):
                    tkinter.messagebox.showerror("Set MFC Error", "MFC Cannot be set higher than 50SSCM - please enter smaller number")

                else:
                    pass


        def systemRun():
            print("System Start")
            self.systemState.processStartTime = time.time()
            #print(self.systemState.processStartTime)
            self.currentUser.name = entry_username.get()
            self.currentUser.baseDirectory=entry_baseDirectory.get()
            self.currentUser.parentDirectory=self.currentUser.baseDirectory
            self.currentUser.experimentName = "testing"
            self.currentUser.experimentDate = date.today().strftime("%Y%m%d")
            self.currentUser.experimentTime = int(time.time())
            userDirectory = os.path.join(self.currentUser.baseDirectory, self.currentUser.name)
            processDirectory = os.path.join(self.currentUser.baseDirectory , self.currentUser.name , "processes")
            #check to see if user directory exists
            if (os.path.exists(userDirectory) != 1):
                os.mkdir(userDirectory)
            else:
                print("User path already exists")
            #check to see if Experiment directory exits
            if(os.path.exists(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.experimentDirectory))!=1):
                os.mkdir(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.experimentDirectory))
            else:
                print("Experiment Directory already exists)")
            #check to see if Processes directory exists
            if(os.path.exists(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.processDirectory))!=1):
                os.mkdir(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.processDirectory))
            else:
                print("Process Directory already exists)")
           
            experimentDirectory = os.path.join(self.currentUser.baseDirectory, self.currentUser.name , self.currentUser.experimentDirectory , (self.currentUser.experimentDate + "_" + self.currentUser.experimentName + "_" + str(self.currentUser.experimentTime)))
            print(experimentDirectory)
            if (os.path.exists(experimentDirectory) != 1):
                os.mkdir(experimentDirectory)
                print("Made Experiment Path")
            else:
                print("Experiment path already exists somehow?")
            #maybe put this into User class

            tempCommandLogFilename = os.path.join(experimentDirectory, "commandLog.txt")
            print(tempCommandLogFilename)
            tempCommandLog = open(tempCommandLogFilename, 'w')
            tempSystemLogFilename = os.path.join(experimentDirectory , "systemLog.txt")
            print(tempSystemLogFilename)

            btn_RUN.configure(state=DISABLED)
            btn_STOP.configure(state=NORMAL)
            #for i in range(self.systemState.numMFCs):
            #    self.MFC_GUI_updateButtons[i].configure(state=NORMAL)
            self.MFC_GUI_updateALL.configure(state=NORMAL)


            self.isRunning.set(True)
            self.isFillToPressure.set(value=False)

        def systemStop():
            print("System Stop")
            btn_RUN.configure(state=NORMAL)
            btn_STOP.configure(state=DISABLED )

            for i in range(self.systemState.numMFCs):
                self.systemState.MFCs[i].currentSetPoint = 0
                self.systemState.MFCs[i].currentPercentSetPoint = 0
                #self.MFC_GUI_updateButtons[i].configure(state=DISABLED)
                self.MFC_GUI_updateALL.configure(state=DISABLED)
                self.MFC_GUI_setpointActuals[i].configure(text="STOPPED")
                self.systemState.MFCs[i].setFlowrate(self.systemState.MFCs[i].currentPercentSetPoint, self.arduino,self.currentUser)
            
            #close all solenoids
            for i in range(self.systemState.numSolenoids):
                self.solenoidCheckbuttonStates[i].set(False)
                self.systemState.solenoids[i].actuateSolenoid(0, self.arduino,self.currentUser)

            self.isRunning.set(False)
            self.isFillToPressure.set(value=False)

        # def openLoggingWindow():
        #     pass

        def fillToPressure_push_MFC_setpoint():
            isEntryBox_number = 0
            tempEntryBox_value = 0
            temp_MFC_setpoints = []
            for i in range(self.systemState.numMFCs):
                tempMFC_number = i
                string_MFC_flowRate = self.pressureTab_MFC_GUI_setpointEntries[tempMFC_number].get()
                isEntryBox_number = string_MFC_flowRate.replace(".","").isnumeric()  # checks to see if string is numerical, isnumeric() can't deal with decimal points for whatever reason so need to use .replace("." , "") to remove
                # print(isEntryBox_number)#debug output

                if (isEntryBox_number == 1):
                    tempEntryBox_value = float(string_MFC_flowRate)

                if (isEntryBox_number == 1 and tempEntryBox_value <= 100 and tempEntryBox_value >= 0):
                    temp_MFC_setpoints.append(tempEntryBox_value)

                elif (isEntryBox_number == 0):
                    tkinter.messagebox.showerror("Set MFC Error", "Ensure entry is a number")

                elif (tempEntryBox_value > 100):
                    tkinter.messagebox.showerror("Set MFC Error",
                                                 "MFC Cannot be set higher than 100% - please enter smaller number")

                else:
                    pass

            for i in range(self.systemState.numMFCs):
                self.pressureTab_MFC_GUI_setpointRatios[i].configure(text = str(temp_MFC_setpoints[i]/temp_MFC_setpoints[0]))


        def fillToPressure_runProcess():
            print("System Filling Start")
            self.systemState.processStartTime = time.time()
            #print(self.systemState.processStartTime)
            self.currentUser.name = entry_username.get()
            self.currentUser.baseDirectory=entry_baseDirectory.get()
            self.currentUser.parentDirectory=self.currentUser.baseDirectory
            self.currentUser.experimentName = "testing"
            self.currentUser.experimentDate = date.today().strftime("%Y%m%d")
            self.currentUser.experimentTime = int(time.time())
            userDirectory = os.path.join(self.currentUser.baseDirectory, self.currentUser.name)
            processDirectory = os.path.join(self.currentUser.baseDirectory , self.currentUser.name , "processes")
            #check to see if user directory exists
            if (os.path.exists(userDirectory) != 1):
                os.mkdir(userDirectory)
            else:
                print("User path already exists")
            #check to see if Experiment directory exits
            if(os.path.exists(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.experimentDirectory))!=1):
                os.mkdir(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.experimentDirectory))
            else:
                print("Experiment Directory already exists)")
            #check to see if Processes directory exists
            if(os.path.exists(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.processDirectory))!=1):
                os.mkdir(os.path.join(self.currentUser.baseDirectory , self.currentUser.name , self.currentUser.processDirectory))
            else:
                print("Process Directory already exists)")
           
            experimentDirectory = os.path.join(self.currentUser.baseDirectory, self.currentUser.name , self.currentUser.experimentDirectory , (self.currentUser.experimentDate + "_" + self.currentUser.experimentName + "_" + str(self.currentUser.experimentTime)))
            print(experimentDirectory)
            if (os.path.exists(experimentDirectory) != 1):
                os.mkdir(experimentDirectory)
                print("Made Experiment Path")
            else:
                print("Experiment path already exists somehow?")

            self.isRunning.set(value=True)
            self.isFillToPressure.set(value=True)
        
        def fillToPressure_stopProcess():
            self.isRunning.set(value=False)
            self.isFillToPressure.set(value=False)

            print("System Stop")
            btn_RUN.configure(state=NORMAL)
            btn_STOP.configure(state=DISABLED )

            for i in range(self.systemState.numMFCs):
                self.systemState.MFCs[i].currentSetPoint = 0
                self.systemState.MFCs[i].currentPercentSetPoint = 0
                #self.MFC_GUI_updateButtons[i].configure(state=DISABLED)
                self.MFC_GUI_updateALL.configure(state=DISABLED)
                self.MFC_GUI_setpointActuals[i].configure(text="STOPPED")
                self.systemState.MFCs[i].setFlowrate(self.systemState.MFCs[i].currentPercentSetPoint, self.arduino,self.currentUser)
            
            #close all solenoids
            for i in range(self.systemState.numSolenoids):
                self.solenoidCheckbuttonStates[i].set(False)
                self.systemState.solenoids[i].actuateSolenoid(0, self.arduino,self.currentUser)
            



        lbl_tabLayout_realTimeControl_col0 = Label(self.tab_realTimeControl , text = "MFCs")
        lbl_tabLayout_realTimeControl_col0.grid(column=0 , row=0)
        lbl_tabLayout_realTimeControl_col1 = Label(self.tab_realTimeControl, text="MFC Setpoint Entry (SCCM)")
        lbl_tabLayout_realTimeControl_col1.grid(column=1, row=0)
        lbl_tabLayout_realTimeControl_col2 = Label(self.tab_realTimeControl, text="Current Set Point (SCCM)")
        lbl_tabLayout_realTimeControl_col2.grid(column=2, row=0)
        lbl_tabLayout_realTimeControl_col3 = Label(self.tab_realTimeControl, text="Current Actual (SCCM)")
        lbl_tabLayout_realTimeControl_col3.grid(column=3, row=0)
        lbl_tabLayout_realTimeControl_col4 = Label(self.tab_realTimeControl, text="Gauge Actual(bar)")
        lbl_tabLayout_realTimeControl_col4.grid(column=4, row=0)
        lbl_tabLayout_realTimeControl_col5 = Label(self.tab_realTimeControl, text="Solenoid")
        lbl_tabLayout_realTimeControl_col5.grid(column=5, row=0)
        lbl_tabLayout_realTimeControl_col6 = Label(self.tab_realTimeControl, text="ACTIVE")
        lbl_tabLayout_realTimeControl_col6.grid(column=6, row=0)


        ####MFCs
        self.MFC_GUI_labels = []
        self.MFC_GUI_setpointEntries = []
        #self.MFC_GUI_updateButtons = [] #removed in favour of one button to update all
        self.MFC_GUI_setpointActuals = []
        self.MFC_GUI_liveFlowRates = []

        for i in range(self.systemState.numMFCs):
            #print(i)
            tempMFC_address = i
            self.MFC_GUI_labels.append(Label(self.tab_realTimeControl , text=("MFC_"+str(i) + " Set Point (SCCM)")))
            self.MFC_GUI_labels[i].grid(column=0 , row=(i+1))
            self.MFC_GUI_setpointEntries.append(Entry(self.tab_realTimeControl))
            self.MFC_GUI_setpointEntries[i].insert(0, "0")
            self.MFC_GUI_setpointEntries[i].grid(column=1, row=(i + 1))
            #self.MFC_GUI_updateButtons.append(Button(self.tab_realTimeControl, state=DISABLED, text="Update", command=lambda: update_flowRate_MFC(tempMFC_address)))
            #self.MFC_GUI_updateButtons[i].grid(column=2 , row=(i+1))
            self.MFC_GUI_setpointActuals.append(Label(self.tab_realTimeControl, text="0"))
            self.MFC_GUI_setpointActuals[i].grid(column=2 , row=(i+1))
            self.MFC_GUI_liveFlowRates.append(Label(self.tab_realTimeControl, text="Live Flow Rate"))
            self.MFC_GUI_liveFlowRates[i].grid(column=3 , row=(i+1))


        self.MFC_GUI_updateALL = Button(self.tab_realTimeControl, state=DISABLED, text="Update", command=lambda: update_flowRate_MFC())
        self.MFC_GUI_updateALL.grid(column=1 , row=(self.systemState.numMFCs+1))

        ####GAUGES

        self.realTimeControl_gaugeLabels = []
        for i in range(self.systemState.numGauges):
            self.realTimeControl_gaugeLabels.append(Label(self.tab_realTimeControl , text= ("Gauge_" + str(i) + ":-")))
            self.realTimeControl_gaugeLabels[i].grid(column=4,row=(i+1))

        ####SOLENOIDS
        self.solenoidCheckbuttons = []
        self.solenoidCheckbuttonLabels = []
        #print("DEFINING CHECKBUTTONS")
        for i in range(self.systemState.numSolenoids):
            #print(i)
            self.solenoidCheckbuttons.append(Checkbutton(self.tab_realTimeControl , variable = self.solenoidCheckbuttonStates[i]))
            self.solenoidCheckbuttonLabels.append(Label(self.tab_realTimeControl , text = ("Solenoid_" + str(i))))
            self.solenoidCheckbuttonLabels[i].grid(column=5 , row=(i+1))
            self.solenoidCheckbuttons[i].grid(column=6, row=(i+1))

        btn_run_style = ttk.Style()
        btn_run_style.configure("runButton" , background="green")
        btn_RUN = Button(self.tab_realTimeControl,text="RUN" , state=NORMAL, command = lambda:systemRun())
        btn_RUN.grid(column=5,row=(self.systemState.numSolenoids+1) )
        btn_stop_style = ttk.Style()
        btn_stop_style.configure("stopButton" , background="red")
        btn_STOP = Button(self.tab_realTimeControl,text="STOP", state=DISABLED ,command = lambda:systemStop())
        btn_STOP.grid(column=6,row=(self.systemState.numSolenoids+1))
        # btn_openLogger = Button(self.tab_realTimeControl,text="Open Log", state=DISABLED ,command = lambda:openLoggingWindow())
        # btn_openLogger.grid(column=3,row=5)

        ####Pressurisation Tab
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="MFCs")
        lbl_tabLayout_fillToPressure_col0.grid(column=0, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="MFC Setpoint Entry (SCCM)")
        lbl_tabLayout_fillToPressure_col0.grid(column=1, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="Current Set Point (%)")
        lbl_tabLayout_fillToPressure_col0.grid(column=2, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="Current Actual (V)")
        lbl_tabLayout_fillToPressure_col0.grid(column=3, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="Ratio (ref MFC_0)")
        lbl_tabLayout_fillToPressure_col0.grid(column=4, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="Real-Time Ratio")
        lbl_tabLayout_fillToPressure_col0.grid(column=5, row=0)
        lbl_tabLayout_fillToPressure_col0 = Label(self.tab_fillToPressure, text="Gauge Pressures")
        lbl_tabLayout_fillToPressure_col0.grid(column=6, row=0)

        ####MFCs
        self.pressureTab_MFC_GUI_labels = []
        self.pressureTab_MFC_GUI_setpointEntries = []
        # self.pressureTab_MFC_GUI_updateButtons = [] #removed in favour of one button to update all
        self.pressureTab_MFC_GUI_setpointActuals = []
        self.pressureTab_MFC_GUI_liveFlowRates = []
        self.pressureTab_MFC_GUI_setpointRatios = []
        self.pressureTab_MFC_GUI_realTimeRatios = []



        for i in range(self.systemState.numMFCs):
            # print(i)
            tempMFC_address = i
            self.pressureTab_MFC_GUI_labels.append(Label(self.tab_fillToPressure, text=("MFC_" + str(i) + " Set Point (SCCM)")))
            self.pressureTab_MFC_GUI_labels[i].grid(column=0, row=(i + 1))
            self.pressureTab_MFC_GUI_setpointEntries.append(Entry(self.tab_fillToPressure))
            self.pressureTab_MFC_GUI_setpointEntries[i].insert(0, "0")
            self.pressureTab_MFC_GUI_setpointEntries[i].grid(column=1, row=(i + 1))
            # self.MFC_GUI_updateButtons.append(Button(self.tab_fillToPressure, state=DISABLED, text="Update", command=lambda: update_flowRate_MFC(tempMFC_address)))
            # self.MFC_GUI_updateButtons[i].grid(column=2 , row=(i+1))
            self.pressureTab_MFC_GUI_setpointActuals.append(Label(self.tab_fillToPressure, text="0"))
            self.pressureTab_MFC_GUI_setpointActuals[i].grid(column=2, row=(i + 1))
            self.pressureTab_MFC_GUI_liveFlowRates.append(Label(self.tab_fillToPressure, text="Live Flow Rate"))
            self.pressureTab_MFC_GUI_liveFlowRates[i].grid(column=3, row=(i + 1))
            self.pressureTab_MFC_GUI_setpointRatios.append(Label(self.tab_fillToPressure , text="-"))
            self.pressureTab_MFC_GUI_setpointRatios[i].grid(column=4 , row=(i+1))
            self.pressureTab_MFC_GUI_realTimeRatios.append(Label(self.tab_fillToPressure , text="-"))
            self.pressureTab_MFC_GUI_realTimeRatios[i].grid(column=5 , row=(i+1))

        self.pressureTab_gaugeLabels = []
        for i in range(self.systemState.numGauges):
            self.pressureTab_gaugeLabels.append(Label(self.tab_fillToPressure , text= ("Gauge_" + str(i) + ":-")))
            self.pressureTab_gaugeLabels[i].grid(column=6,row=(i+1))
        for i in range(self.systemState.numGauges):
            self.pressureTab_gaugeLabels.append(Label(self.tab_fillToPressure , text= ("Gauge_" + str(i) + ":-")))
            self.pressureTab_gaugeLabels[i].grid(column=6,row=(i+1))

        self.pressureTab_fillPressureLabel = Label(self.tab_fillToPressure , text = "Fill Pressure (bar)")
        self.pressureTab_fillPressureLabel.grid(column=5 , row =(self.systemState.numGauges + 1))
        self.pressureTab_fillPressure_Entry = Entry(self.tab_fillToPressure)
        self.pressureTab_fillPressure_Entry.grid(column=6 , row = (self.systemState.numGauges + 1))

        self.pressureTab_MFC_GUI_btn_PUSH = Button(self.tab_fillToPressure , text="PUSH MFC SETPOINTS" , command=lambda: fillToPressure_push_MFC_setpoint())
        self.pressureTab_MFC_GUI_btn_PUSH.grid(column=1, row=(self.systemState.numMFCs+1))
        
        self.pressureTab_START_BUTTON = Button(self.tab_fillToPressure , text = "START FILLING" , command=lambda: fillToPressure_runProcess())
        self.pressureTab_START_BUTTON.grid(column=6 , row = (self.systemState.numMFCs+2))
        self.pressureTab_STOP_BUTTON = Button(self.tab_fillToPressure , text = "STOP FILLING" , command=lambda: fillToPressure_stopProcess())
        self.pressureTab_STOP_BUTTON.grid(column=5 , row = (self.systemState.numMFCs+2))

        menuBar = Menu(self)  # define menu bar

        #file_menu = Menu(menuBar)  # add item to menu bar
        #file_menu.add_command(label="New Command")  # add item to drop down menu, then need to generate instance of a cascade

        program_menu = Menu(menuBar)
        program_menu.add_command(label="Information")
        program_menu.add_command(label="Quit")
        #program_menu.add_command(label="Maintenance Login")

        #edit_menu = Menu(menuBar)
        #edit_menu.add_command(label="First label here")

        menuBar.add_cascade(label="SteierLab GUI", menu=program_menu)  # generate a dropdown menu from items defined before
        #menuBar.add_cascade(label="File", menu=file_menu)
        #menuBar.add_cascade(label="Edit", menu=edit_menu)


        #Show tab bar
        self.tabList.pack(expand=1 , fill = 'both')





    def configure_GUI(self):
        pass

    def runProgram(self):
        #self.updateGUI()
        self.mainloop()

    def updateGUI(self, k=1):

        ###Introduce some logic here for RTC and Different operating modes

        if (self.isRunning.get() and self.isFillToPressure.get() == False): #only updates values if arduino tells MFCs what to do
            # MFC_0_debugFlowrate = random.randint(1, 100)
            # MFC_1_debugFlowrate = random.randint(1, 100)
            # MFC_2_debugFlowrate = random.randint(1, 100)
            # MFC_3_debugFlowrate = random.randint(1, 100)
            # MFC0_tempVar = MFC_0_debugFlowrate
            # MFC1_tempVar = MFC_1_debugFlowrate
            # MFC2_tempVar = MFC_2_debugFlowrate
            # MFC3_tempVar = MFC_3_debugFlowrate

            # self.systemState.MFCs[0].getFlowrate(self.arduino , self.currentUser)
            # self.systemState.MFCs[1].getFlowrate(self.arduino , self.currentUser)
            # self.systemState.MFCs[2].getFlowrate(self.arduino , self.currentUser)
            # self.systemState.MFCs[3].getFlowrate(self.arduino , self.currentUser)
            # #print("got MFC values")
            # MFC0_tempVar = self.systemState.MFCs[0].currentFlowRate
            # MFC1_tempVar = self.systemState.MFCs[1].currentFlowRate
            # MFC2_tempVar = self.systemState.MFCs[2].currentFlowRate
            # MFC3_tempVar = self.systemState.MFCs[3].currentFlowRate
            # self.lbl_MFC_0_liveFlowRate.configure(text=str(MFC0_tempVar))
            # #print(MFC0_tempVar)  # debugOutput
            # self.lbl_MFC_1_liveFlowRate.configure(text=str(MFC1_tempVar))
            # #print(MFC1_tempVar)  # debugOutput
            # self.lbl_MFC_2_liveFlowRate.configure(text=str(MFC2_tempVar))
            # #print(MFC2_tempVar)  # debugOutput
            # self.lbl_MFC_3_liveFlowRate.configure(text=str(MFC3_tempVar))
            # #print(MFC3_tempVar)  # debugOutput


            
            self.systemState.check(self.arduino , self.currentUser)
            
            for i in range(self.systemState.numMFCs):
                #self.systemState.MFCs[i].getFlowrate(self.arduino,self.currentUser)
                #print(self.systemState.MFCs[i].currentFlowRate)
                #self.MFC_GUI_liveFlowRates[i].configure(text=str(self.systemState.MFCs[i].currentReadVoltage))
                self.systemState.MFCs[i].currentFlowRate = round((50*self.systemState.MFCs[i].currentReadVoltage/5) , 3)
                #print(self.systemState.MFCs[i].currentFlowRate)
                self.MFC_GUI_liveFlowRates[i].configure(text=str(self.systemState.MFCs[i].currentFlowRate) + " SCCM")



            for i in range(self.systemState.numGauges):
                #self.systemState.gauges[i].getPressure(self.arduino , self.currentUser)
                #print(self.systemState.gauges[i].currentVoltage)
                #self.realTimeControl_gaugeLabels[i].configure(text =("Gauge_" + str(i) + ": " + str(self.systemState.gauges[i].currentVoltage)))
                self.systemState.gauges[i].currentPressure = round((-1 + 16*(self.systemState.gauges[i].currentVoltage/5)) , 3)
                #print(self.systemState.gauges[i].currentPressure)
                self.realTimeControl_gaugeLabels[i].configure(text =("Gauge_" + str(i) + ": " + str(self.systemState.gauges[i].currentPressure) + " Bar"))
                

            #do more here, have some history stuff available
            #update solenoid stuff
            for i in range(self.systemState.numSolenoids):
                tempSolenoidState = self.solenoidCheckbuttonStates[i].get()
                tempCurrentSolenoidState =self.systemState.solenoids[i].currentValue
                #print(tempSolenoidState)
                #print(tempCurrentSolenoidState)
                if tempSolenoidState:
                    if tempCurrentSolenoidState==100:
                        pass
                    elif tempCurrentSolenoidState==0:
                        self.systemState.solenoids[i].actuateSolenoid(100 , self.arduino , self.currentUser)
                        #print("solenoid " + str(i) + " enabled")
                    else:
                        pass

                else:
                    if tempCurrentSolenoidState==100:
                        self.systemState.solenoids[i].actuateSolenoid(0, self.arduino, self.currentUser)
                        #print("solenoid " + str(i) + " disabled")
                    elif tempCurrentSolenoidState==0:
                        pass
                    else:
                        pass

            self.systemState.logToFile(self.currentUser)

        if (self.isRunning.get() and self.isFillToPressure.get()):
            self.systemState.check(self.arduino , self.currentUser)
            
            for i in range(self.systemState.numMFCs):
                #self.systemState.MFCs[i].getFlowrate(self.arduino,self.currentUser)
                #print(self.systemState.MFCs[i].currentFlowRate)
                #self.pressureTab_MFC_GUI_liveFlowRates[i].configure(text=str(self.systemState.MFCs[i].currentReadVoltage))
                self.systemState.MFCs[i].currentFlowRate = round((50*self.systemState.MFCs[i].currentReadVoltage/5) , 3)
                #print(self.systemState.MFCs[i].currentFlowRate)
                self.pressureTab_MFC_GUI_liveFlowRates[i].configure(text=str(self.systemState.MFCs[i].currentFlowRate) + " SCCM")



            for i in range(self.systemState.numGauges):
                #self.systemState.gauges[i].getPressure(self.arduino , self.currentUser)
                #print(self.systemState.gauges[i].currentVoltage)
                #self.pressureTab_gaugeLabels[i].configure(text =("Gauge_" + str(i) + ": " + str(self.systemState.gauges[i].currentVoltage)))
                self.systemState.gauges[i].currentPressure = round((-1 + 16*(self.systemState.gauges[i].currentVoltage/5)) , 3)
                #print(self.systemState.gauges[i].currentPressure)
                self.pressureTab_gaugeLabels[i].configure(text =("Gauge_" + str(i) + ": " + str(self.systemState.gauges[i].currentPressure) + " Bar"))

            #check to see if stop condition met.
            if(self.systemState.gauges[0].currentPressure >= self.fillPressure):
                self.isRunning.set(value=False)
                self.isFillToPressure.set(value=False)
                messagebox.showinfo("Fill To Pressure" , "System Filled to"  + str(self.fillPressure) + "Bar")

                #all the other bits of enabling/diabling buttons etc


        if True:
            self.after(250, self.updateGUI, k)#updates GUI every 250ms
















def main():
    #maybe build in a setup-Window class to provide a config file for default?
    app = MainWindow()
    app.after(1000 , app.updateGUI)
    app.mainloop()







main()