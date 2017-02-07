import os
import sys
import re

def dump_time(local_jobname, section_name, time):
    '''dump_time
    keeps log of cpu run time, current formulation is not robust
    '''
    if (os.path.isfile(local_jobname+"_run_time.txt") is False):    
        f = open(local_jobname+"_run_time.txt", "w")
        f.write("Runs times for " + local_jobname + "\n")
    else:
        f = open(local_jobname+"_run_time.txt", "a")
    if time < 60.0:
        line = section_name + " :  %f seconds\n"%time
    else:
        line = section_name + " :  %f minutes\n"%(time/60.0)
    f.write(line)
    f.close()

def print_run_time(local_jobname):
    '''print_run_time
    Read in run times from file and and print to screen with percentages
    '''
    f=open(local_jobname+"_run_time.txt").readlines()
    unit = f[-1].split()[-1]
    total = float(f[-1].split()[-2])
    if unit is 'minutes':
        total *= 60.0

    print 'Runs times for ', f[0]
    percent = []
    name = []
    for i in range(1,len(f)):
        unit = f[i].split()[-1]
        time = float(f[i].split()[-2])

        if unit is 'minutes':
            time *= 60.0
        percent.append(100.0*(time/total))
        name.append(f[i].split(':')[1])
        print f[i], '\t--> Percent if total %0.2f \n'%percent[i-1]
    print("Primary Function Percentages")

    for i in range(1,len(f) - 1):
        if name[i-1] == ' dfnGen ' or name[i-1] == ' dfnFlow ' or name[i-1] == ' dfnTrans ':
            print(name[i-1]+"\t"+"*"*int(percent[i-1]))
    print("\n")

def get_num_frac():
    try: 
        f = open('params.txt')
        _num_frac = int(f.readline())
        f.close()
    except:
        print '-->ERROR getting number of fractures, no params.txt file'

class input_helper():
    
    def __init__(self, params, minFracSize):
        self.params = params
        self.minFracSize = minFracSize
    ## ====================================================================== ##
    ##                              Helper Functions                          ##
    ## ====================================================================== ##

    ## '{1,2,3}' --> [1,2,3]
    def curlyToList(self, curlyList):
        return re.sub("{|}", "", curlyList).strip().split(",")

    ## [1,2,3] --> '{1,2,3}'   for writing output
    def listToCurly(self, strList):
         curl = re.sub(r'\[','{', strList)
         curl = re.sub(r'\]','}', curl)
         curl = re.sub(r"\'", '', curl)
         return curl 

    def hasCurlys(self, line, key):
        if '{' in line and '}' in line: return True 
        elif '{' in line or '}' in line: 
            self.error("Line defining \"{}\" contains a single curly brace.".format(key))
        return False

    ## Use to get key's value in params. writing always false  
    def valueOf(self, key, writing = False):
        if (not writing) and (len(self.params[key]) > 1):
            self.error("\"{}\" can only correspond to 1 list. {} lists have been defined.".format(key, len(self.params[key])))
        #try:    
        val = self.params[key][0]
        if val == '' or val == []:
            self.error("\"{}\" does not have a value.".format(key))
        return val
        #except IndexError:
        #    self.error("\"{}\" has not been defined.".format(key)) ## Include assumptions (ie no Angleoption -> degrees?)

    def getGroups(self, line, valList, key):
        curlyGroup = re.compile('({.*?})')
        groups = re.findall(curlyGroup, line)
        for group in groups:
            line = line.replace(group, '', 1) ## only delete first occurence
            valList.append(self.curlyToList(group))
            
        if line.strip() != "":
            self.error("Unexpected character found while parsing \"{}\".".format(key))

    def valHelper(self, line, valList, key):
        if self.hasCurlys(line, key):
            self.getGroups(line, valList, key)
        else:
            valList.append(line)
        
    def error(self, errString):
        print("\nERROR --- " + errString)
        print("\n----Program terminated while parsing input----\n")
        sys.exit(1)

    def warning(self, warnString):
        print("WARNING --- " + warnString)
    
    def warning(self, warnString, warningFile=''):
        #global warningFile
        print("WARNING --- " + warnString)
        #warningFile.write("WARNING --- " + warnString + "\n")

    def isNegative(self, num): 
        return True if num < 0 else False

    ## Makes sure at least one polygon family has been defined in nFamRect or nFamEll
    ##      OR that there is a user input file for polygons. 
    def checkFamCount(self):
        userDefExists = (self.valueOf('userEllipsesOnOff') == '1') |\
                   (self.valueOf('userRectanglesOnOff') == '1') |\
                   (self.valueOf('userRecByCoord') == '1') |\
                   (self.valueOf('userEllByCoord') == '1')
        
        ellipseFams = len(self.valueOf('nFamRect'))
        rectFams = len(self.valueOf('nFamEll'))


        if ellipseFams + rectFams <= 0 and not userDefExists:
            self.error("Zero polygon families have been defined. Please create at least one family "\
                  "of ellipses/rectagnles, or provide a user-defined-polygon input file path in "\
                  "\"UserEll_Input_File_Path\", \"UserRect_Input_File_Path\", \"UserEll_Input_File_Path\", or "\
                  "\"RectByCoord_Input_File_Path\" and set the corresponding flag to '1'.")

    ## scales list of probabilities (famProb) that doesn't add up to 1
    ## ie [.2, .2, .4] --> [0.25, 0.25, 0.5]        
    def scale(self, probList, warningFile):
        total = sum(probList)
        scaled = [float("{:.6}".format(x/total)) for x in probList]
        self.warning("'famProb' probabilities did not add to 1 and have been scaled accordingly "\
            "for their current sum, {:.6}. Scaled {} to {}".format(total, probList, scaled), warningFile)
        return [x/total for x in probList]                

    def zeroInStdDevs(self, valList):
        for val in valList:
            if float(val) == 0: return True
        
    def checkMinMax(self, minParam, maxParam, shape):
        for minV, maxV in zip(self.valueOf(minParam), self.valueOf(maxParam)):
            if minV == maxV:
                self.error("\"{}\" and \"{}\" contain equal values for the same {} family. "\
                      "If {} and {} were intended to be the same, use the constant distribution "\
                      "(4) instead.".format(minParam, maxParam, shape, minParam, maxParam))
            if minV > maxV:
                self.error("\"{}\" is greater than \"{}\" in a(n) {} family.".format(minParam, maxParam, shape))
                sys.exit()

    def checkMean(self, minParam, maxParam, meanParam, warningFile=''):
        for minV, meanV in zip(self.valueOf(minParam), self.valueOf(meanParam)):
            if minV > meanV: 
               self.warning("\"{}\" contains a min value greater than its family's mean value in "\
                      "\"{}\". This could drastically increase computation time due to increased "\
                      "rejection rate of the most common fracture sizes.".format(minParam, meanParam), warningFile)
        for maxV, meanV in zip(self.valueOf(maxParam), self.valueOf(meanParam)):
            if maxV < meanV: 
               self.warning("\"{}\" contains a max value less than its family's mean value in "\
                      "\"{}\". This could drastically increase computation time due to increased "\
                      "rejection rate of the most common fracture sizes.".format(maxParam, meanParam), warningFile)

    def checkMinFracSize(self, valList):
        for val in valList:
            if val < self.minFracSize: self.minFracSize = val



    ## ====================================================================== ##
    ##                              Parsing Functions                         ##
    ## ====================================================================== ##
    def extractParameters(self, line, inputIterator):
        if "/*" in line:
            comment = line
            line = line[:line.index("/*")] ## only process text before '/*' comment
            while "*/" not in comment:
                comment = next(inputIterator) ## just moves iterator past comment

        elif "//" in line:
            line = line[:line.index("//")] ## only process text before '//' comment
            
        return line.strip()


    def findVal(self, line, key, inputIterator, unfoundKeys, warningFile):
        valList = []
        line = line[line.index(":") + 1:].strip()
        if line != "" : self.valHelper(line, valList, key)

        line = self.extractParameters(next(inputIterator), inputIterator)
        while ':' not in line:
            line = line.strip()
            if line != "" :
                self.valHelper(line, valList, key)
            try:
                line = self.extractParameters(next(inputIterator), inputIterator)
            except StopIteration:
                break
        
        if valList == [] and key in mandatory:
            self.error("\"{}\" is a mandatory parameter and must be defined.".format(key))
        if key is not None:
            self.params[key] = valList if valList != [] else [""] ## allows nothing to be entered for unused params 
        if line != "": self.processLine(line, unfoundKeys, inputIterator, warningFile)
            
    ## Input: line containing a paramter (key) preceding a ":" 
    ## Returns: key -- if it has not been defined yet and is valid
    ##          None -- if key does not exist
    ##          exits -- if the key has already been defined to prevent duplicate confusion        
    def findKey(self, line, unfoundKeys, warningFile):
        key = line[:line.index(":")].strip()
        if key in unfoundKeys:
            unfoundKeys.remove(key)
            return key
        try:
            self.params[key]
            self.error("\"{}\" has been defined more than once.".format(key))
        except KeyError:
           self.warning("\"" + key + "\" is not one of the valid parameter names.", warningFile)

    def processLine(self, line, unfoundKeys, inputIterator, warningFile):
        if line.strip != "":
            key = self.findKey(line, unfoundKeys, warningFile)
            if key != None: self.findVal(line, key, inputIterator, unfoundKeys, warningFile)   


    ## ====================================================================== ##
    ##                              Verification                              ##
    ## ====================================================================== ##
    ## Note: Always provide EITHER a key (ie "stopCondition") 
    ##         OR inList = True/False (boolean indicating val being checked is inside a list) 

    ## Input: value - value being checked
    ##        key - parameter the value belongs to
    ##        inList - (Optional)
    def verifyFlag(self, value, key = "", inList = False):
        if value is '0' or value is '1':
            return int(value)
        elif inList:
            return None
        else:
            self.error("\"{}\" must be either '0' or '1'".format(key))

    def verifyFloat(self, value, key = "", inList = False, noNeg = False):
        if type(value) is list:
            self.error("\"{}\" contains curly braces {{}} but should not be a list value.".format(key))
        try:
            if noNeg and float(value) < 0:
                self.error("\"{}\" cannot be a negative number.".format(key))
            return float(value)
        except ValueError:
            if inList: return None
            else:
                self.error("\"{}\" contains an unexpected character. Must be a single "\
                      "floating point value (0.5, 1.6, 4.0, etc.)".format(key))
                
                
    def verifyInt(self, value, key = "", inList = False, noNeg = False):
        if type(value) is list:
            self.error("\"{}\" contains curly braces {{}} but should not be a list value.".format(key))
        try:
            if noNeg and int(re.sub(r'\.0*$', '', value)) < 0:
                self.error("\"{}\" cannot be a negative number.".format(key))
            return int(re.sub(r'\.0*$', '', value)) ## regex for removing .0* (ie 4.00 -> 4)
        except ValueError:
            if inList: return None
            else:
                self.error("\"{}\" contains an unexpected character. Must be a single "\
                      "integer value (0,1,2,3,etc.)".format(key))
                
    ## Verifies input list that come in format {0, 1, 2, 3}
    ##
    ## Input:  valList - List of values (flags, floats, or ints) corresponding to a parameter
    ##         key - the name of the parameter whose list is being verified
    ##         verificationFn - (either verifyFlag, verifyFloat or verifyInt) checks each list element 
    ##         desiredLength - how many elements are supposed to be in the list
    ##         noZeros - (Optional) True for lists than cannot contain 0's, False if 0's are ok  
    ##         noNegs - (Optional) True for lists than cannot contain negative numbers, False otherwise
    ## Output: returns negative value of list length to indicate incorrect length and provide meaningful error message
    ##         Prints error and exits if a value of the wrong type is found in the list
    ##         returns None if successful
    ##
    def verifyList(self, valList, key, verificationFn, desiredLength, noZeros=False, noNegs=False):
        if valList == ['']: return 0
        if type(valList) is not list:
            self.error("\"{}\"'s value must be a list encolsed in curly brackets {{}}.".format(key))
        if desiredLength != 0 and int(len(valList)) != int(desiredLength):
            print 'list desired length is ', desiredLength, 'but valList is ', valList, 'with length ', len(valList)
            return -len(valList)
        for i, value in enumerate(valList):
            value = value.strip()
            verifiedVal = verificationFn(value, inList = True)
            if verifiedVal == None:
                listType = re.sub('Integer', 'Int', re.sub(r'verify', '', verificationFn.__name__)) ## 'verifyInt' --> 'Integer'
                self.error("\"{}\" must be a list of {}s {}. Non-{} found in "\
                      "list".format(key, listType, examples[listType], listType))
            if noZeros and verifiedVal == 0:
                self.error("\"{}\" list cannot contain any zeroes.".format(key))
            if noNegs and self.isNegative(float(verifiedVal)):
                self.error("\"{}\" list cannot contain any negative values.".format(key)) 
            valList[i] = verifiedVal 
           

    ## def verifyNumValsIs(length, key):f
           ##  if len(self.params[key]) != length:
            ##     self.error("ERROR: ", "\"" + param + "\"", "should have", length, "value(s) but", len(self.params[key]), "are defined.")
             ##    sys.exit()                
            

            
