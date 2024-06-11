from serial import Serial
import serial.tools.list_ports

def searchForAvailableSerial():
    # Ask the snake to look for available COM ports, return these as an array of objects
    ports = serial.tools.list_ports.comports(include_links=False)
    # create lists for later on, not yet sure exactly which of these will be needed later on, but easy to have and memory is cheap
    portsList = []
    portsDescriptionList = []
    portsMenuList = []
    outputArray = []
    # iterate through and generate lists that will be used later on, print statements for debugging and testing, remove later if necessary
    for port in ports:
        # print(port.device)
        portsList.append(port.device)
        # print(port.description)
        portsDescriptionList.append(port.description)
        portsMenuList.append(port.device + ' - ' + port.description)

    # print(portsList)
    # print(portsDescriptionList)
    # print(portsMenuList)
    # generate 2D output array to get passed to main GUI function
    outputArray.append(portsList)
    outputArray.append(portsDescriptionList)
    outputArray.append(portsMenuList)
    # print(outputArray)
    return (outputArray)