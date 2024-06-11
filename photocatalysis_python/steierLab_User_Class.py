class User:
    def __init__(self):
        self.parentDirectory = ""  # Will be hard coded into the software Temporarily in my python folder for ALD software
        self.name = "Default"
        self.baseDirectory = ""
        self.processDirectory = "processes"
        self.experimentDirectory = "experiments"
        self.logDirectory = "logs"
        self.existingProcessName = "" #gets assigned when user selects a process from drop down menu in GUI
        self.newProcessName = ""
        self.isNewProcess = 0
        self.processList = []
        self.experimentName = "Default"
        self.experimentDate = "" #gets assigned to ISO date when run starts. Helps to date stamp and find logs later on.
        self.experimentTime = 0 #gets assigned to Epoch Time when run starts. Helps to differentiate experiments in case they are the same name.
