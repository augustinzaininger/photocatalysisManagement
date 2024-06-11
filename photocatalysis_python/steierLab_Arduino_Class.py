import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter import Menu
from tkinter import messagebox
import serial
from serial import Serial
import serial.tools.list_ports
import re

from datetime import date
import time
import os
import shutil
import csv

class ArduinoObject:
    def __init__(self , inputSerialPort , inputBaudrate):
        self.actionBrackets = ['<', '>']
        self.queryBrackets = ['?', '?']
        self.panicBrackets = ['!', '!']
        self.startBrackets = [self.actionBrackets[0], self.queryBrackets[0], self.panicBrackets[0]]
        self.endBrackets = [self.actionBrackets[1], self.queryBrackets[1], self.panicBrackets[1]]
        self.isInitialised = 0
        self.port = inputSerialPort
        self.baudrate = inputBaudrate
        self.number = ''    #might want to add multiple arduinos at some point. have plenty of available memory to have this variable.
        self.comms = serial.Serial()
        self.comms.port = self.port
        self.comms.baudrate = self.baudrate
        self.comms.xonxoff = 1
        #self.comms.stopbits = 2 #Arduino Serial.print() defaults to 2 stop bits. Unclear why this wasnt necessary earlier

        #self.comms.open()



    def initialise(self):
        #initialises Serial connection with Arduino - call this function at login - include some error handling in case the arduino does not connect properly. If multiple arduinos in system then search for serial connections, ping each one with a query in succession until right one is found.
        #need to figure out initialisation protocol. Maybe just send it a hello and the arduino responds
        #Need a time-out clause to throw an error for when arduion shits the bed

        #check to see if port is open
        print(self.comms.isOpen())
        if(self.comms.isOpen() == False):
            self.comms.open()
            print("opened comms port, waiting 1s for arduino to reboot")
            time.sleep(1)

        print(self.comms.port)

        testSendString = '?tst_01_001?'
        initialisedConfirmString = '?tst_1_001?\r\n'
        numTries = 0

        while (self.isInitialised == 0 and numTries <=10):
            print("Probing Arduino")
            #print(testSendString)
            self.send(testSendString)
            #build in better timeout handling - throw error is nothing received in a certain amount of time
            tempResponse = self.receiveAll()
            #print(tempResponse)
            #print(tempResponse)
            #print(repr(tempResponse))
            #print(len(initialisedConfirmString))
            #print(len(tempResponse))
            if (tempResponse == initialisedConfirmString):
                self.isInitialised = 1
                print("Arduino Initialised! Congratulations")
                messagebox.showinfo("Initialisation", "Arduino initialised.")
            else:
                self.isInitialised = 0
                print("not initialised yet :( sad.gif ")

            time.sleep(0.1)
            numTries +=1

        if(self.isInitialised == 0):
            messagebox.showinfo("Initialisation", "Arduino initialisation failed. Try a different Serial Port")


        # wait for confirmation that arduino fully initialised

        # Add more error handling in here once I flesh out the initialisation process on the arduino.

    def waitFor(self):
        response = ""
        self.send("Can I please start?")
        time.sleep(1)
        response = self.receiveAll()
        print(response)
        time.sleep(1)
        response = self.receiveAll()

        # while (response.find("<START>") == -1):  # looks for initialisation finishing part. Might have to skip some of the SD shenanigans in the arduino script
        #     while (self.comms.inWaiting() == 0):
        #          pass  # loops without doing anything while nothing in serial buffer
        #     response += self.receiveAll()

        print("Response:" + str(response) + "\n")

    def send(self , tempCommandString):
        #print("sending " + tempCommandString)
        self.comms.write(tempCommandString.encode())
        #print(self.comms.port)
        #print(self.comms.baudrate)
        # print(self.comms.bytesize)
        # print(self.comms.parity)
        # print(self.comms.stopbits)
        # print(self.comms.xonxoff)
        # print(self.comms.rtscts)
        # print(self.comms.timeout)
        # print(tempCommandString.encode())

    def promptSend(self):
        tempCommand = input("Enter Command , syntax <XXX_YYY_ZZZ>, brackets <> , ?? , !!\n")
        self.comms.write(tempCommand.encode())


    def receiveAll(self):
        # function for reading in data from Serial port. Eventually will add on to this some extra functionality that will look for start and end markers
        # for initial testing will just read everything from serial connection - arduino will parse command and then respond by printing EVERYTHING to the serial connection. (also to file)
        receivedMessage = ""
        tempBrackets = ["", ""]
        temp = "="
        tempStarted = 0
        tempFinished = 0
        byteCount = -1  # tutorial has this, not entirely sure what it does. Might be needed for something later on. Needs to be -1 so that the array length matches later?
        while (self.comms.inWaiting() == 0):
            #print("Nothing received yet")
            pass

        while (self.comms.inWaiting() > 0):
            # temp = self.comms.read()
            # print(temp)
            # temp = temp.decode()
            temp = self.comms.read().decode()
            receivedMessage = receivedMessage + temp
            byteCount += 1
            if (byteCount == 0):
                time.sleep(0.002)  # delay after first character to make sure that everything hits serial buffer, can ultimately increase this to 1ms if I want, but not probably not necessary as
            #less will be hitting serial buffer in actual script. Only here for testing. If delay is 300µs then things dont work.
        #print(receivedMessage)
        return receivedMessage

    def receive(self):
        # function for reading in data from Serial port. Eventually will add on to this some extra functionality that will look for start and end markers
        # for initial testing will just read everything from serial connection - arduino will parse command and then respond by printing EVERYTHING to the serial connection. (also to file)
        receivedMessage = ""
        tempBrackets = ["", ""]
        temp = "="
        tempStarted = 0
        tempFinished = 0
        byteCount = -1  # tutorial has this, not entirely sure what it does. Might be needed for something later on. Needs to be -1 so that the array length matches later?
        #print("entered receive function")
        while (tempFinished == 0):
            while (self.comms.inWaiting() == 0):
                pass
            while (self.comms.inWaiting() > 0 and tempFinished == 0):
                #print("Something has arrived")
                temp = self.comms.read().decode()
                if (temp in self.startBrackets and tempStarted == 0):  # recognises first character of response. Rest of loop will continue until the end character is read.
                    tempStarted = 1
                    tempBrackets[0] = temp
                    receivedMessage = receivedMessage + temp
                    #print(receivedMessage)
                elif (tempStarted == 1):  # else if required here. Will skip this statement if condition to above if() statement is true.
                    receivedMessage = receivedMessage + temp
                    if (temp in self.endBrackets):
                        tempFinished = 1
                        tempBrackets[1] = temp
                byteCount += 1
                # debugging - check whats actually being read in. Will print tempFinished = 1 a couple of times due to termination of string.
                # print(tempFinished)
                # print(temp)
                # if(byteCount == 0):
                # time.sleep(0.002)#delay after first character to make sure that everything hits serial buffer, can ultimately increase this to 1ms if I want, but not probably not necessary as
                # less will be hitting serial buffer in actual script. Only here for testing. If delay is 300µs then things dont work.
            #print(receivedMessage)
        return receivedMessage
