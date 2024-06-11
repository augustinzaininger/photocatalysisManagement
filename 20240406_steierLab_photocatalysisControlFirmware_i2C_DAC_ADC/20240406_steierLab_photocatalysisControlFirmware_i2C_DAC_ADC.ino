#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP4728.h>

//define global variables
static int ledPin = 13;
static char actionBrackets[2] = {'<' , '>'};
static char queryBrackets[2] = {'?' , '?'};
static char panicBrackets[2] = {'!' , '!'};

static int i2C_address_MCP4728 = 0x60;
static int i2C_address_ADS1115 = 0x48;

Adafruit_MCP4728 MCP4728_DAC; //initialise instance of MCP4728
Adafruit_ADS1115 ADS1115_ADC; //initialise instance of ADS1115


char outputFilename[30];
String outputFilenameString;

const static int numSolenoids = 12;
const static int numGauges = 4;
const static int numMFCs = 4;
const static int numTempControllers = 4;
const static int numPrecursors = 4;

//initialise some variables that will be needed later
char tempVariable = 'd';
int tempCount = 0;



//hardcoded pin positions - refer to base board layout
const static int solenoidLocations[numSolenoids] = {23 , 27 , 31 , 35 , 39 , 43 , 42 , 38 , 34 , 30 , 26 , 22};
const static int solenoidStatusLocations[numSolenoids] = {25 , 29 , 33 , 37 , 41 , 45 , 44 , 40 , 36 , 32 , 28 , 24};

const static int gaugeSignalLocations[numGauges] = {A11 , A10 , A9 , A8};
const static int gaugeEnableLocations[numGauges] = {17 , 16 , 15 , 14};

const static int MFC_signalLocations[numMFCs] = {A3 , A2 , A1 , A0};
const static int MFC_setPointLocations[numMFCs] = {3 , 4 , 5 , 6 };



//define necessary data storage types:
  //struct for each device type

typedef struct solenoid {
  int outputPin;
  int currentSetValue;

  int statusPin;
  int currentStatusValue;
};

typedef struct gauge {
   int outputPin;
  int gaugeEnable;
  double currentValue;
  double currentVoltage;
  double currentPressure;
  String manufacturer;
  String modelNumber;
  double inputResponseGradient = 0;
  double inputResponseTurnOnVoltage = 0;
  double inputResponseBaseValue = 0;
  double inputResponseMaxValue = 0;
  //pressure = baseValue+gradient*(currVoltage - turnOnVoltage);
};

typedef struct MFC {
  int inputPin;
  int outputPin;
  float currentReadVoltage;
  float currentReadValue;
  float currentFlowRate;
  float currentSetPoint;
  float currentSetPointFlowrate;
  String manufacturer;
  String modelNumber;
  float inputResponseGradient;
  float inputResponseTurnOnVoltage;
  float inputResponseBaseValue;
  float inputResponseMaxValue;
  //pressure = baseValue+gradient*(currVoltage - turnOnVoltage);
  float outputResponseGradient;
  float outputResponseTurnOnVoltage;
  float outputResponseBaseValue;
  float outputResponseMaxValue;
  //maybe use another variable here that is used in a switch statement in get/setMFC
};

typedef struct precursor {
  int upperSolenoid;
  int lowerSolenoid;
  int precursorNumber;
  int currentState;
  String precursorLabel;
};


  //struct for commands
typedef struct cmd {
  const static int commandLength = 20;
  char fromPython[commandLength + 1] = {'\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0' , '\0'};
  char brackets[2] = {'\0' , '\0'};
  String commandString = fromPython;
  int started = 0;
  int finished = 0;
  int type = 0;
  char subsystem[6] = {'\0' , '\0' , '\0' , '\0' , '\0' , '\0'};
  int location = 0;
  int number = 0;
  int value = 0;
  int isValid = 0;
  long timeIn = 0;
  long timeOut = 0;
  float returnValue;
  String returnString;
  //Need any other components in the struct?
};


//Generate arrays for gauges/solenoids/MFCs
solenoid solenoids[numSolenoids];
precursor precursors[numPrecursors];
gauge gauges[numGauges];
MFC MFCs[numMFCs];


//define global functions

//read command: loops awaiting input via Serial, as soon as input hits buffer reads command and then 
cmd readCommand() {
  cmd nullCommand;
  cmd tempCommand;
  tempCommand.started = 0;
  char tempRead = '\0';
  int tempPosition = 0;
  int startBracketFound = 0;
  int endBracketFound = 0;
  tempCommand.isValid = 0;
  //need to add parts that read from serial buffer until a start character is read, then reads until end character is read.
  //if command improperly formatted then the command is invalid. if command.invalid==0 then action is skipped and reply is
  //command is invalid.
  //Serial.println("Enter Command");
  //wait until command is here
  while (Serial.available() < 1) {
    //do nothing but wait
  }
  //read in one single character, check if its a start bracket, then delay 1ms to allow any more stuff to his serial buffer.
  if (Serial.available() > 0) {
    tempRead = Serial.read();
    delay(1);
    if (tempRead == '<' || tempRead == '?' || tempRead == '!') {
      startBracketFound = 1;
      tempCommand.brackets[0] = tempRead;//for later, check start and end brackets, might just be easier to stick them in their own array
      tempCommand.fromPython[0] = tempRead;
      tempCommand.started = 1;
      tempCommand.timeIn = micros();
      tempPosition = 1;
      //parse commandType
    }
  }
  //if previous char was a bracket, this gets skipped. if not, then script continues to search for start character
  while (Serial.available() > 0 && startBracketFound < 1) {
    tempRead = Serial.read();
    //program continues to read from serial buffer until it finds a start bracket (could be any of the types)
    //maybe think of a better way to this, if tempRead in char* startBracket[];
    if (tempRead == '<' || tempRead == '?' || tempRead == '!') {
      startBracketFound = 1;
      Serial.println("start bracket found");
      tempCommand.brackets[0] = tempRead;//for later, check start and end brackets, might just be easier to stick them in their own array
      tempCommand.fromPython[0] = tempRead;
      tempCommand.started = 1;
      tempPosition = 1;
      //parse commandType
    }
  }
  //need a timeout clause in this loop in case command is not long enough and no end bracket is found. Figure this out later
  while (Serial.available() > 0 && endBracketFound == 0 && tempPosition <= tempCommand.commandLength) {
    //read in rest of command until find an end bracket or run out of space in cmd buffer
    //limit max length of command, in case its too long then tempCommand.isValid = 0; escape from process.
    tempRead = Serial.read();
    tempCommand.fromPython[tempPosition] = tempRead;
    if (tempRead == '>' || tempRead == '?' || tempRead == '!') {
      endBracketFound = 1;
      //Serial.println("End bracket found");
      tempCommand.brackets[1] = tempRead; //escape this loop when end bracket has been read.
      //Serial.println(tempCommand.brackets);
    }
    tempPosition++;
  }
  //at this point should now have whole command in char array.

  //some logic here regarding bracketing and parsing command type, depending on type will then parse the rest of the info
//  if (tempCommand.brackets[0] == '<' && tempCommand.brackets[1] == '>') {
//    tempCommand.isValid = 1;
//    tempCommand.type = 1;//action
//    sscanf(tempCommand.fromPython, "<%03c_%02d_%03d>" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
//  }
//  else if (tempCommand.brackets[0] == '?' && tempCommand.brackets[1] == '?') {
//    tempCommand.isValid = 1;
//    tempCommand.type = 2;//query
//    sscanf(tempCommand.fromPython, "?%03c_%02d_%03d?" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
//  }
//  else if (tempCommand.brackets[0] == '!' && tempCommand.brackets[1] == '!') {
//    tempCommand.isValid = 1;
//    tempCommand.type = 3;//panic
//    sscanf(tempCommand.fromPython, "!%03c_%02d_%03d!" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
//  }
//above code works, trying something new to allow more flexibility in sending commands, so far only can send a subsystem of 3 char long with numbers of any length
//look into strtok() for parsing command.subsystem of arbitrary length (provided within the limits of command.commandLength = 20)
//http://www.cplusplus.com/reference/cstring/strtok/
//should be able to split the input into 3 parts, parse into subsystem, then location, then value. Should be able to do all parts with arbitrary length which will help with error handling.
  if (tempCommand.brackets[0] == '<' && tempCommand.brackets[1] == '>') {
    tempCommand.isValid = 1;
    tempCommand.type = 1;//action
    sscanf(tempCommand.fromPython, "<%03c_%d_%d>" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
  }
  else if (tempCommand.brackets[0] == '?' && tempCommand.brackets[1] == '?') {
    tempCommand.isValid = 1;
    tempCommand.type = 2;//query
    sscanf(tempCommand.fromPython, "?%03c_%d_%d?" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
  }
  else if (tempCommand.brackets[0] == '!' && tempCommand.brackets[1] == '?') {
    tempCommand.isValid = 1;
    tempCommand.type = 3;//panic
    sscanf(tempCommand.fromPython, "!%03c_%d_%d!" , tempCommand.subsystem , &tempCommand.location , &tempCommand.value);
  }

  //Serial.println(tempCommand.fromPython);
  //Serial.println(tempCommand.brackets);
  //Serial.println(tempCommand.type);
  //Serial.println(tempCommand.isValid);
  //parse information from command into the various types.
  //decodes string/array of char that is read in into different parts of command. These then get passed to different functions
  tempCommand.commandString = tempCommand.fromPython;


  //Dunno if I need anything else here
  //Serial.println(F("Read-in Finished"));//for debugging, need to make sure that I get past this stage


  while (Serial.available() > 0) {
    Serial.read();
  }

  //Serial.flush();// flush anything else from the serial buffer? Should be able to not have to do this.

  if (tempCommand.isValid) {
    return tempCommand;
  }
  else {
    return nullCommand;
  }

}

//deal with command: does what the command tells it to do
void dealWithCommand(cmd inputCommand) {
  //switch statement on type of command.
  //within switch statement if statements based on command.subsystem using strcmp (string compare)
  //directs command wherever it needs to go
  switch (inputCommand.type) {
    case 1:
      if (strcmp(inputCommand.subsystem , "sol") == 0) {
        actuateSolenoid(inputCommand.location , inputCommand.value);
        inputCommand.returnValue = inputCommand.value;
      }
      else if (strcmp(inputCommand.subsystem , "gaj") == 0) {
        if(inputCommand.value == 0){
          digitalWrite(gauges[inputCommand.location].gaugeEnable , LOW);
          inputCommand.returnValue = 0;
        }
      else if(inputCommand.value == 100){
          digitalWrite(gauges[inputCommand.location].gaugeEnable , HIGH);
        }
      }
      else if (strcmp(inputCommand.subsystem , "mfc") == 0) {
        set_MFC_flowrate_MCP4728(inputCommand.location , inputCommand.value);
        inputCommand.returnValue = MFCs[inputCommand.location].currentSetPointFlowrate;
      }
      else {
        Serial.println(F("Still nothing recognised"));
      }
      break;
    case 2:
      if (strcmp(inputCommand.subsystem , "sol") == 0) {
        delay(1);
      }
      else if (strcmp(inputCommand.subsystem , "gaj") == 0) {
        inputCommand.returnString = "press"; //will be used later in respondCommand and gets parsed by python
        inputCommand.returnValue = get_gaugePressure(inputCommand.location);
        gauges[inputCommand.location].currentPressure = inputCommand.returnValue;
      }
      else if (strcmp(inputCommand.subsystem , "mfc") == 0) {
        inputCommand.returnString = "flow";
        inputCommand.returnValue = get_MFC_flowrate_ADS1115(inputCommand.location);
      }
      else if (strcmp(inputCommand.subsystem , "tst") == 0) {
        //test query as part of initialisation
        inputCommand.returnString = "tst";
        inputCommand.returnValue = 100;
      }
      else {
        Serial.println(F("Still nothing recognised"));
      }
      break;
    case 3:
      //command type is a panic command
      //writes zero/LOW to *all* analog and digital outputs.
      panic();
      break;
    default:
      Serial.println(F("Code is still broken"));
  }
  //once everything is done, then respond to python script with some response confirming that command has been received and carried out successfully
}

//respond command: Sends response string to Snek - confirming that command has arrived and that has been parsed properly
void respondCommand(cmd inputCommand) {
  int debugging = 0;
  // if debugging, spits out way more info to serial port to check everything is being parsed correctly. Otherwise just build response and send it to Python
  //some logic to determine what the response should be. Maybe just repeat the whole command string for now.
  //outputFile.open();
  if (debugging == 1) {
    //  outputFile.println(inputCommand.fromPython);
    //  outputFile.close();
    inputCommand.timeOut = micros();
    //Serial.print(F("inputCommand.fromPython: \t"));
    Serial.println(inputCommand.fromPython);
    //Serial.print(F("inputCommand.subsystem \t"));
    Serial.println(inputCommand.subsystem);
    //Serial.print(F("inputCommand.location: \t"));
    Serial.println(inputCommand.location);
    //Serial.print(F("inputCommand.value: \t"));
    Serial.println(inputCommand.value);
    //Serial.print(F("inputCommand.type: \t"));
    Serial.println(inputCommand.type);
    long tempDuration = inputCommand.timeOut - inputCommand.timeIn;
    Serial.print(F("Command process Duration on Arduino "));
    Serial.print(tempDuration);
    Serial.println(F(" microseconds"));
  }
  //if not debugging, do the proper thing and send back something to Python script
  else {
    //create ouput string echoing input command format
    // <?! subsystem _ location _ value >?!
    //really only need to do the value part - if its a setting command, just return the input string
    //if its a query command, create new array, only the output number needs to be changed at array indices
    //also need clause here if command.isValid == 0 
    if (inputCommand.type == 1) {
      Serial.print("<");
      Serial.print(inputCommand.subsystem);
      Serial.print("_");
      Serial.print(inputCommand.location);
      Serial.print("_");
      //some logic here to tell the function what number to send to python, add if statements to differentiate between the different subsystems
      Serial.print(inputCommand.value);
      Serial.println(">");

    }
    else if ( inputCommand.type == 2) {
      Serial.print("?");
      Serial.print(inputCommand.subsystem);
      Serial.print("_");
      Serial.print(inputCommand.location);
      Serial.print("_");
      if (strcmp(inputCommand.subsystem , "sol") == 0) {
        Serial.print(solenoids[inputCommand.location].currentSetValue);
      }
      else if (strcmp(inputCommand.subsystem , "gaj") == 0) {
        Serial.print(gauges[inputCommand.location].currentVoltage , 4);
      }
      else if (strcmp(inputCommand.subsystem , "mfc") == 0) {
        Serial.print(MFCs[inputCommand.location].currentReadVoltage , 4);
      }
      else if (strcmp(inputCommand.subsystem , "tst") == 0) {
        Serial.print("001");
      }
      Serial.println("?");
    }
    else if ( inputCommand.type == 3) {
      delay(1);
    }
    else if (inputCommand.type == 3) {
      Serial.println(inputCommand.fromPython);
    }
    //logCommandToSD(inputCommand , tempOutputFilename);
  }
  inputCommand.timeOut = micros();
  //Serial.print("total elapsed time \t");
  //Serial.println(inputCommand.timeOut - inputCommand.timeIn);
    

}


//initialise Serial connection: Handshake process with Snek, python code has timeout clause. Process must be initialised before rest of program can proceed.

//configure system: populates arrays for solenoids, gauges, MFCs
void configureSystem() {
  //define solenoids and their locations and set their current values to LOW i.e. closed
  //const static int solenoidLocations[numSolenoids] = {23 , 25 , 27 , 29 , 31 , 33 , 35 , 37 , 39 , 41 , 43 , 45 , 47 , 49 , 51 , 53};
  //const static int solenoidStatusLocations[numSolenoids] = {22 , 24 , 26 , 28 , 30 , 32 , 34 , 36 , 38 , 40 , 42 , 44 , 46 , 48 , 50 , 52};
  for (int i = 0 ; i < numSolenoids ; i++) {
    solenoids[i].outputPin = solenoidLocations[i];
    solenoids[i].currentSetValue = LOW;
    pinMode(solenoids[i].outputPin , OUTPUT);
    digitalWrite(solenoids[i].outputPin , solenoids[i].currentSetValue);
  }

  //define gauges and their locations
  //const static int gaugeSignalLocations[numGauges] = {A11 , A10 , A9 , A8};
  //const static int gaugeEnableLocations[numGauges] = {17 , 16 , 15 , 14};
  for (int i = 0 ; i < numGauges ; i++) {
    gauges[i].outputPin = gaugeSignalLocations[i];
    gauges[i].gaugeEnable = gaugeEnableLocations[i];
    pinMode(gauges[i].outputPin , INPUT);
    pinMode(gauges[i].gaugeEnable , OUTPUT);

  }

  //set response curves for different gauges.
  for (int i = 0 ; i < numGauges ; i++) {
    if (gauges[i].manufacturer == "Edwards" && gauges[i].modelNumber == "") {
      gauges[i].inputResponseGradient = 0;
      gauges[i].inputResponseTurnOnVoltage = 0;
      gauges[i].inputResponseMaxValue = 0;
      gauges[i].inputResponseBaseValue = 0;
      //comment here with link to datasheet for gauge
    }
    else {
      gauges[i].inputResponseGradient = 0;
      gauges[i].inputResponseTurnOnVoltage = 0;
      gauges[i].inputResponseMaxValue = 0;
      gauges[i].inputResponseBaseValue = 0;
    }
  }

  //define MFCs and their locations
  //const static int MFC_signalLocations[numMFCs] = {A7 , A6 , A5 , A4 , A3 , A2 , A1 , A0};
  //const static int MFC_setPointLocations[numMFCs] = {2 , 3 , 4 , 5 , 4 , 7 , 8 , 9};
  //int mfcOutputLocations[numMFCs] = {A7 , A6 , A5 , A4};;
  //int mfcInputLocations[numMFCs] = { , 3 , 4 , 5};;
  for (int i = 0 ; i < numMFCs ; i++) {
    MFCs[i].inputPin = MFC_setPointLocations[i];
    MFCs[i].outputPin = MFC_signalLocations[i];
    pinMode(MFCs[i].inputPin , OUTPUT);//analog output sends voltage to input pin of MFC
    pinMode(MFCs[i].outputPin , INPUT);//analog input receives voltage from output pin of MFC
  }


  for (int i = 0 ; i < numMFCs ; i++) {
    if (MFCs[i].manufacturer == 'Alicat' && MFCs[i].modelNumber == "") {
      //set inputResponse parameters
      MFCs[i].inputResponseGradient = 0;
      MFCs[i].inputResponseTurnOnVoltage = 0;
      MFCs[i].inputResponseBaseValue = 0;
      MFCs[i].inputResponseMaxValue = 0;
      //set outputResponse parameters
      MFCs[i].outputResponseGradient = 0;
      MFCs[i].outputResponseTurnOnVoltage = 0;
      MFCs[i].outputResponseBaseValue = 0;
      MFCs[i].outputResponseMaxValue = 0;
    }
    else {
      //set inputResponse parameters
      MFCs[i].inputResponseGradient = 0;
      MFCs[i].inputResponseTurnOnVoltage = 0;
      MFCs[i].inputResponseBaseValue = 0;
      MFCs[i].inputResponseMaxValue = 0;
      //set outputResponse parameters
      MFCs[i].outputResponseGradient = 0;
      MFCs[i].outputResponseTurnOnVoltage = 0;
      MFCs[i].outputResponseBaseValue = 0;
      MFCs[i].outputResponseMaxValue = 0;
    }
  }

  //anything else needs to go in here?
  for (int i = 0 ; i < numPrecursors ; i++) {
    precursors[i].upperSolenoid = i;
    precursors[i].lowerSolenoid = 2 * i + 1;
    precursors[i].precursorNumber = i + 1;
  }
}

//actuate solenoid
void actuateSolenoid(int location , int solenoidValue) {
  if (location < numSolenoids) {
    if (solenoidValue == 0) {
      digitalWrite(solenoids[location].outputPin , LOW);
      //Serial.println("Solenoid OFF");
    }
    else if (solenoidValue == 100) {
      digitalWrite(solenoids[location].outputPin , HIGH);
      //Serial.println("Solenoid ON");
    }
    else {
      delay(1);
    }
    solenoids[location].currentSetValue = solenoidValue;
  }
}

//read gauge pressure
float get_gaugePressure(int gaugeNumber) {
  if (gaugeNumber < numGauges) {
    gauges[gaugeNumber].currentValue = analogRead(gauges[gaugeNumber].outputPin);
    //Serial.print("analog read\t");
    //Serial.println(gauges[gaugeNumber].currentValue);
    //analogRead() returns value between 0 and 1023 describing voltage between 0 and 5V
    gauges[gaugeNumber].currentVoltage = gauges[gaugeNumber].currentValue * (5.0 / 1023);
    gauges[gaugeNumber].currentPressure = gauges[gaugeNumber].inputResponseBaseValue + gauges[gaugeNumber].inputResponseGradient * (gauges[gaugeNumber].currentVoltage - gauges[gaugeNumber].inputResponseTurnOnVoltage);

    //Serial.print("Gauge Pressure\t");
    //Serial.println(gauges[gaugeNumber].currentPressure);
    return gauges[gaugeNumber].currentVoltage;
  }

}

float get_gaugePressure_ADS1115(int gaugeNumber){
  if(gaugeNumber < numGauges){
    int16_t tempVar = 0;
    gauges[gaugeNumber].currentValue = ADS1115_ADC.readADC_SingleEnded(gaugeNumber);//Read ADC pin
    //Serial.print("ADC READING: ");
    //Serial.println(gauges[gaugeNumber].currentValue , 4);
    gauges[gaugeNumber].currentVoltage = ADS1115_ADC.computeVolts(gauges[gaugeNumber].currentValue);//Convert reading into volts, ADS1115 library takes care of this
    //Serial.print("ADC Voltage: ");
    //Serial.println(gauges[gaugeNumber].currentVoltage , 4);

    return gauges[gaugeNumber].currentVoltage;
  }
}




//initialise gauge
void enableGauge(int gaugeNumber) {
  delay(0.1);
}

//set MFC flow rate
void set_MFC_flowrate(int mfcNumber , float percentFlowRate) {
  if (mfcNumber < numMFCs) {
    MFCs[mfcNumber].currentSetPoint = percentFlowRate / 100;
    //Serial.println(MFCs[mfcNumber].currentSetPoint);
    MFCs[mfcNumber].currentSetPointFlowrate = percentFlowRate * MFCs[mfcNumber].outputResponseMaxValue;
    float currVoltage = (((MFCs[mfcNumber].currentSetPointFlowrate - MFCs[mfcNumber].outputResponseBaseValue) / MFCs[mfcNumber].outputResponseGradient) + MFCs[mfcNumber].outputResponseTurnOnVoltage);
    int writeToArduino = int((MFCs[mfcNumber].currentSetPoint) * 255);
    analogWrite(MFCs[mfcNumber].inputPin , writeToArduino);
    //Serial.print("Analog Voltage\t");
    //Serial.println(writeToArduino);
  }
}

void set_MFC_flowrate_MCP4728(int mfcNumber , float percentFlowRate) {
  if (mfcNumber < numMFCs) {
    MFCs[mfcNumber].currentSetPoint = percentFlowRate / 100;
    //Serial.println(MFCs[mfcNumber].currentSetPoint);
    MFCs[mfcNumber].currentSetPointFlowrate = percentFlowRate * MFCs[mfcNumber].outputResponseMaxValue;

    float currVoltage = (((MFCs[mfcNumber].currentSetPointFlowrate - MFCs[mfcNumber].outputResponseBaseValue) / MFCs[mfcNumber].outputResponseGradient) + MFCs[mfcNumber].outputResponseTurnOnVoltage);
    
    int writeToDAC = MFCs[mfcNumber].currentSetPoint * 4096 - 1;
    switch (mfcNumber){
      case 0:
        MCP4728_DAC.setChannelValue(MCP4728_CHANNEL_A, writeToDAC);
      case 1:
        MCP4728_DAC.setChannelValue(MCP4728_CHANNEL_B, writeToDAC);
      case 2:
        MCP4728_DAC.setChannelValue(MCP4728_CHANNEL_C, writeToDAC);
      case 3:
        MCP4728_DAC.setChannelValue(MCP4728_CHANNEL_D, writeToDAC);
      default:
        delay(10);
    }


    
    //Serial.println(writeToDAC);
    //Serial.print("Analog Voltage\t");
    //Serial.println();
  }
}

//get MFC flow rate
float get_MFC_flowrate(int mfcNumber) {
  if (mfcNumber < numMFCs) {
    MFCs[mfcNumber].currentReadValue = analogRead(MFCs[mfcNumber].outputPin);
    MFCs[mfcNumber].currentReadVoltage = MFCs[mfcNumber].currentReadValue * (5.0 / 1024);
    //Serial.print("Analog Voltage\t");
    //Serial.println(MFCs[mfcNumber].currentReadVoltage);
    MFCs[mfcNumber].currentFlowRate = MFCs[mfcNumber].inputResponseBaseValue + MFCs[mfcNumber].inputResponseGradient * (MFCs[mfcNumber].currentReadVoltage - MFCs[mfcNumber].inputResponseTurnOnVoltage);
    //Serial.print("Current Flow Rate");
    //Serial.println(MFCs[mfcNumber].currentFlowRate);
    //return MFCs[mfcNumber].currentFlowRate;
    return MFCs[mfcNumber].currentReadVoltage;
  }
}

float get_MFC_flowrate_ADS1115(int mfcNumber){
  if(mfcNumber < numMFCs){
    MFCs[mfcNumber].currentReadValue = ADS1115_ADC.readADC_SingleEnded(mfcNumber);//Read ADC pin
    //int16_t tempReading = ADS1115_ADC.readADC_SingleEnded(mfcNumber);//Read ADC pin
    //Serial.print("ADC READING: ");
    //Serial.println(tempReading, 4);
    MFCs[mfcNumber].currentReadVoltage = ADS1115_ADC.computeVolts(MFCs[mfcNumber].currentReadValue); //Convert reading into volts, ADS1115 library takes care of this
    //Serial.print("ADC Voltage: ");
    //Serial.println(MFCs[mfcNumber].currentReadVoltage , 4);
    MFCs[mfcNumber].currentFlowRate = MFCs[mfcNumber].inputResponseBaseValue + MFCs[mfcNumber].inputResponseGradient * (MFCs[mfcNumber].currentReadVoltage - MFCs[mfcNumber].inputResponseTurnOnVoltage);
    
    return MFCs[mfcNumber].currentReadVoltage;
  }
}

//emergency stop
void panic() {
  //write 0 to all analog outputs
  //write LOW to all digital outputs
  for (int i = 0 ; i < numSolenoids ; i++) {
    digitalWrite(solenoids[i].outputPin , LOW);
    solenoids[i].currentSetValue = 0;
  }
  for (int i = 0 ; i < numMFCs ; i++) {
    analogWrite(MFCs[i].inputPin , 0);
    MFCs[i].currentSetPoint = 0;
    MFCs[i].currentSetPointFlowrate = 0;
  }
}



//configure system, open Serial comms with Snek, perform handshake procedure. Python code has timeout clause, makes sure arduino is properly set up before rest of program is allowed.
void setup() {
// put your setup code here, to run once:
  configureSystem();
  




  //open serial communications with wait clause - need to wait for comms to be open before proceeding to next step.
  Serial.begin(2000000);
  //some sort of wait clause here that doesnt proceed until the serial connection is made.

  while (Serial.available() == 0) {
    //do nothing but wait for first handshake from python interface, needs to see input from Python or Serial Monitor first before proceeding
  }


  if (Serial.available() > 0) {
    tempVariable = Serial.read();
    //Serial.println("message Received");
    delay(10); //delay for rest of message to hit buffer
    tempCount++;
  }
  while (Serial.available() > 0 && tempCount >= 1 && tempCount < 30) {
    tempVariable = Serial.read();
    //Serial.println(tempCount);
    tempCount++;
  }
  //flush serial buffer now
  while (Serial.available() > 0) {
    Serial.read();
    //Serial.println("Flushing Buffer");
  }

  Serial.println("<START>");
  Serial.println("first handshake done");

  //initialise ADS1115 ADC
  int ADS1115_isInitialised = 0;
  if(ADS1115_ADC.begin(i2C_address_ADS1115)){
    ADS1115_isInitialised = 1;
    //send confirm message to python
    Serial.println("ADS1115 Initialised");
  }
  else if (!ADS1115_ADC.begin(i2C_address_ADS1115)){
    Serial.println("ADS1115 Initialisation Failed");
    ADS1115_isInitialised = 0;
    //send error message to python
  }

  //initialise MCP4728 DAC
  int MCP4728_isInitialised = 0;
  if(MCP4728_DAC.begin(i2C_address_MCP4728)){
    MCP4728_isInitialised = 1;
    //send confirm message to python
    Serial.println("MCP4728 Initialised");
  }
  else if (!MCP4728_DAC.begin(i2C_address_MCP4728)){
    Serial.println("MCP4728 Initialisation Failed");
    MCP4728_isInitialised = 0;
    //send error message to python
  }

  //await second handshake where snake lad wants to know how what system is involved, and what processes are allowed
  
  while (Serial.available() == 0) {
    //do nothing but wait for second handshake from python interface, needs to see input from Python or Serial Monitor first before proceeding
  }
  tempCount = 0;
  if (Serial.available() > 0) {
    tempVariable = Serial.read();
    delay(10); //delay for rest of message to hit buffer
    tempCount++;
  }
    while (Serial.available() > 0 && tempCount >= 1 && tempCount < 30) {
     tempVariable = Serial.read();
    tempCount++;
  }
  
    //flush serial buffer now
  while (Serial.available() > 0) {
    Serial.read();
  }
  
  String secondHandshakeString = "<PCC_00_00>"; 
  Serial.println(secondHandshakeString);
  //second handshake done, move to main loop to actually use the thing.
}

//main program
void loop(){
cmd command;
  //initialise local variable Command
  command = readCommand();

  dealWithCommand(command);

  respondCommand(command);
  
}
