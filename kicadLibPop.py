# -*- coding: utf-8 -*-
"""
KiCAD Library Populator (Python 3.6) V0.0.1

DESCRIPTION:
The purpose of this library is to be able to populate KiCAD libraries with
components using only Digi-Key part numbers

USAGE:
Currently, this only works as a Python script in Python 3.6. To run the script,
add in either one or a group of Digi-Key part numbers to the list "partNum".
Only capacitors, inductors, and resistors are supported at this time.

Created: Wed 20180131-0007
Last updated: Mon 20180205-0134
Author: Alex Naylor

FUTURE ADDITIONS:
-Ability to find DK PN based on MPN
-Ability to add more components to other libraries (i.e. diodes, connectors, 
 etc.)
-Make the script runnable from the CLI

CHANGELOG (V0.0.1):
AN:
-
"""

import bs4
import os
import re
import sys

from kicadLibPopConst import *
from urllib.request import urlopen

fieldsToIgnore = ["Detailed Description",
                  "Moisture Sensitivity Level (MSL)",
                  "Quantity Available",
                  "Packaging"]

capLibFile = "SFUSat-cap.lib"
indLibFile = "SFUSat-ind.lib"
resLibFile = "SFUSat-res.lib"

capDescFile = "SFUSat-cap.dcm"
indDescFile = "SFUSat-ind.dcm"
resDescFile = "SFUSat-res.dcm"

dirName = os.path.dirname(os.path.abspath(__file__))

capLibFilePath = dirName+"\\"+capLibFile
indLibFilePath = dirName+"\\"+indLibFile
resLibFilePath = dirName+"\\"+resLibFile

capDescFilePath = dirName+"\\"+capDescFile
indDescFilePath = dirName+"\\"+indDescFile
resDescFilePath = dirName+"\\"+resDescFile

capLibContents = None
indLibContents = None
resLibContents = None

capDescContents = None
indDescContents = None
resDescContents = None

#To hold all of the parts for the library file
capParts = []
indParts = []
resParts = []

#To hold all of the descriptions for the description file
capDesc = []
indDesc = []
resDesc = []

productList = {} #For processing multiple parts
productAttrDict = {} #Product attributes that are not required for a KiCAD part
fixedAttrDict = {} #Fixed attributes in KiCAD

partDict = {"capParts":[],#list of all of the parts to be written to various libraries
            "indParts":[],
            "resParts":[]} 
libDict = {"capLib":{capLibFile:capLibContents},#list of all of the libraries to be written to
           "indLib":{indLibFile:indLibContents},
           "resLib":{resLibFile:resLibContents}}

dataToWrite = [] #data to write to the library file

#Part numbers to add to the library
partNums = ["490-5523-1-ND",
            "490-1520-1-ND",
            "490-1522-1-ND",
            "399-7752-1-ND",
            "490-5307-1-ND", #duplicate items in BOM
            "399-1063-1-ND",
            "490-1524-1-ND",
            "399-8099-1-ND",
            "490-6518-1-ND",
            "490-5307-1-ND",
            "490-7204-1-ND",
            "490-5936-1-ND",
            "490-3240-1-ND",
            "490-3246-1-ND",
            "490-5888-1-ND",
            "399-6842-1-ND",
            "490-1521-1-ND",
            "P16249CT-ND", #End of caps
            "732-7201-1-ND", #End of inductors
            "WSLP-.01CT-ND",
            "541-3.9ECT-ND",
            "311-100KHRCT-ND",
            "P10.0FCT-ND",
            "541-4.99HHCT-ND",
            "541-1.0ACT-ND",
            "541-20KGCT-ND",
            "541-4057-1-ND",
            "541-10KSACT-ND",
            "541-3952-1-ND",
            "541-383KHCT-ND",
            "311-120KHRCT-ND",
            "311-64.9KHRCT-ND",
            "541-40.2KLCT-ND",
            "541-10.0KLCT-ND",
            "541-280KHCT-ND",
            "541-10.0KHCT-ND",
            "311-220KHRCT-ND",
            "541-300KHCT-ND",
            "311-137KHRCT-ND",
            "541-3951-1-ND",
            "541-10.0KHCT-ND", #duplicate item in BOM
            "541-30.1KHCT-ND",
            "541-3953-1-ND",
            "541-2.0MGCT-ND"] #end of resistors

partNums = list(set(partNums)) #Ensures no duplicates

#constants 
nonNumericChars = r"[^\d.+]"

######
#KiCAD library file options
#see here for more information: https://en.wikibooks.org/wiki/Kicad/file_formats#Description_of_DEF
######
#part value
textOffset = 10
drawPinnumber = "N" #Can be "Y" or "N"
drawPinname = "N" #Can be "Y" or "N"
unitCount = 1 #number of parts in a package; maximum 26
unitsLocked = "F" #can be "L" (units cannot be swapped) or "F" (units can be swapped)
optionFlag = "N" #can be "N" for normal component or "P" for power 

#attribute locations on the symbol
capAttrConfig = {"ref":{"posx":0,
                        "posy":50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"L", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"BNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "val":{"posx":0,
                        "posy":-50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"L", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"TNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "other":{"posx":0,
                        "posy":0,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"I", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"CNN"}} #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)

resAttrConfig = {"ref":{"posx":0,
                        "posy":50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"BNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "val":{"posx":0,
                        "posy":-50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"TNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "other":{"posx":0,
                        "posy":0,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"I", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"CNN"}} #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)

indAttrConfig = {"ref":{"posx":0,
                        "posy":50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"BNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "val":{"posx":0,
                        "posy":-50,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"V", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"TNN"}, #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)
                 "other":{"posx":0,
                        "posy":0,
                        "textSize":50,
                        "textOrient":"H", #"V" for vertical, "H" for horizontal
                        "visible":"I", #"V" for visible, "I" for invisible
                        "hTextJustify":"C", #"L" for left, "R" for right, "C" for center
                        "vTextJustify":"CNN"}} #"T" for top, "B" for bottom, "C" for center (not sure why it's CNN though)

#The physical symbols (too lazy to do it all line by line right now, so I'm just pasting it as a block (i.e. only works for chip components with 2 leads))
capSymbolShape = "DRAW\nP 2 0 1 20 -80 -30 80 -30 N\nP 2 0 1 20 -80 30 80 30 N\nX ~ 1 0 150 110 D 50 50 1 1 P\nX ~ 2 0 -150 110 U 50 50 1 1 P\nENDDRAW"
indSymbolShape = "DRAW\nA -75 0 25 1 -1801 0 1 0 N -50 0 -100 0\nA -25 0 25 1 -1801 0 1 0 N 0 0 -50 0\nA 25 0 25 1 -1801 0 1 0 N 50 0 0 0\nA 75 0 25 1 -1801 0 1 0 N 100 0 50 0\nX 1 1 -150 0 50 R 50 50 1 1 P\nX 2 2 150 0 50 L 50 50 1 1 P\nENDDRAW"
resSymbolShape = "DRAW\nS 100 -40 -100 40 0 1 10 N\nX ~ 1 -150 0 50 R 50 50 1 1 P\nX ~ 2 150 0 50 L 50 50 1 1 P\nENDDRAW"

###############################################################################
### HELPER FUNCTIONS ###
###############################################################################
#Open the part's webpage
def openUrl(partNum):
    dkUrl = "https://www.digikey.ca/products/en?keywords={0}".format(partNum) 
    webpage = urlopen(dkUrl).read().decode("utf-8")
    soup = bs4.BeautifulSoup(webpage,"html5lib")

    return(soup)

#Find the SI unit associated with a value 
def getSiUnit(searchValue):
    for unit, value in siUnitToValDict.items():
        if value == searchValue:
            return(unit)

    print("ERROR: Value does not have a valid SI unit")
    return("")

#generate a part definition to be written to the library file
def makeLibPart(productAttrDict,fixedAttrDict,attrConfig,symbolShape):
    dataToWrite = []
    attributeNum = 4    #F4 is the first optional attribute

    dataToWrite.append("# \n# {0}\n#".format(fixedAttrDict["Value"])) #header
    dataToWrite.append("DEF {0} {1} 0 {2} {3} {4} {5} {6} {7}".format(fixedAttrDict["Value"], #part definition
                                                                      fixedAttrDict["Reference"],
                                                                      textOffset,
                                                                      drawPinnumber,
                                                                      drawPinname,
                                                                      unitCount,
                                                                      unitsLocked,
                                                                      optionFlag))
    
    dataToWrite.append('F0 "{0}" {1} {2} {3} {4} {5} {6} {7}'.format(fixedAttrDict["Reference"],
                                                                     attrConfig['ref']['posx'],
                                                                     attrConfig['ref']['posy'],
                                                                     attrConfig['ref']['textSize'],
                                                                     attrConfig['ref']['textOrient'],
                                                                     attrConfig['ref']['visible'],
                                                                     attrConfig['ref']['hTextJustify'],
                                                                     attrConfig['ref']['vTextJustify']))
    dataToWrite.append('F1 "{0}" {1} {2} {3} {4} {5} {6} {7}'.format(fixedAttrDict["Value"],
                                                                     attrConfig['val']['posx'],
                                                                     attrConfig['val']['posy'],
                                                                     attrConfig['val']['textSize'],
                                                                     attrConfig['val']['textOrient'],
                                                                     attrConfig['val']['visible'],
                                                                     attrConfig['val']['hTextJustify'],
                                                                     attrConfig['val']['vTextJustify']))
    dataToWrite.append('F2 "{0}" {1} {2} {3} {4} {5} {6} {7}'.format(fixedAttrDict["Footprint"],
                                                                     attrConfig['other']['posx'],
                                                                     attrConfig['other']['posy'],
                                                                     attrConfig['other']['textSize'],
                                                                     attrConfig['other']['textOrient'],
                                                                     attrConfig['other']['visible'],
                                                                     attrConfig['other']['hTextJustify'],
                                                                     attrConfig['other']['vTextJustify']))
    dataToWrite.append('F3 "{0}" {1} {2} {3} {4} {5} {6} {7}'.format(fixedAttrDict["Datasheet"],
                                                                     attrConfig['other']['posx'],
                                                                     attrConfig['other']['posy'],
                                                                     attrConfig['other']['textSize'],
                                                                     attrConfig['other']['textOrient'],
                                                                     attrConfig['other']['visible'],
                                                                     attrConfig['other']['hTextJustify'],
                                                                     attrConfig['other']['vTextJustify']))

    for key, value in sorted(productAttrDict.items()):
        #put the description into the description file instead
        if not key == "Description":
            dataToWrite.append('F{0} "{1}" {2} {3} {4} {5} {6} {7} {8} "{9}"'.format(attributeNum,
                                                                                     value,
                                                                                     attrConfig['other']['posx'],
                                                                                     attrConfig['other']['posy'],
                                                                                     attrConfig['other']['textSize'],
                                                                                     attrConfig['other']['textOrient'],
                                                                                     attrConfig['other']['visible'],
                                                                                     attrConfig['other']['hTextJustify'],
                                                                                     attrConfig['other']['vTextJustify'],
                                                                                     key))
        attributeNum += 1

    dataToWrite.append(symbolShape)
    dataToWrite.append("ENDDEF")
    
    return dataToWrite

#Make the description for the description file
def makeDesc(description,name):
    dataToWrite = []
    
    dataToWrite.append('#')
    dataToWrite.append('$CMP {0}'.format(name))
    dataToWrite.append('D {0}'.format(description))
    dataToWrite.append('$ENDCMP')
    
    return(dataToWrite)

#Make a dictionary filled with the fixed attributes
def makeFixedAttrs(productAttrDict):
    if "Capacitor" in productAttrDict["Categories"]:
        
        #Make sure the value is formatted properly
        unit = productAttrDict["Capacitance"][-2]
        
        if unit.isdigit() or unit == " ":
            unit = ""
        
        if unit == "µ": unit = "u"
        
        value = float(re.sub(nonNumericChars, "", productAttrDict["Capacitance"]))
        
        #want to fix any value that can be expressed with a different unit (usually nano)
        if value < 1.0: 
            value *= 1000 #avoid values with decimals; move them to the previous unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e-3) #the new unit
        elif value >= 1000.0:
            value /= 1000 #avoid values larger than 1000; move them to the next unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e3) #the new unit            
        
    
        valueStr = str(value).replace(".",unit)
    
        tolerance = productAttrDict["Tolerance"].replace("±","")
        
        if productAttrDict["Package / Case"] == "Nonstandard":
            package = productAttrDict["Supplier Device Package"]
        else:
            package = productAttrDict["Package / Case"].split(" ")[0]
        
        if not "Temperature Coefficient" in productAttrDict:
            if "Tantalum" in productAttrDict["Categories"]:
                lastParam = "TANT"
            else:
                lastParam = "[FIX_THIS]"
        elif productAttrDict["Temperature Coefficient"] == "C0G, NP0":
            lastParam = "NP0"
        else:
            lastParam = productAttrDict["Temperature Coefficient"]
    
        symbolName = "C_{0}_{1}_{2}_{3}_{4}".format(valueStr,
                                                    tolerance,
                                                    productAttrDict["Voltage - Rated"],
                                                    lastParam,
                                                    package)
        
        footprint = "SFUSat-cap:C_{0}".format(package)

        if not any(footprint.split(":")[1] in file for file in os.listdir(path="SFUSat-cap.pretty")):
            print("No footprint '{0}' found for {1}".format(footprint,symbolName))
            footprint = ""
        
        fixedAttrDict["Reference"] = "C"

    elif "Inductor" in productAttrDict["Categories"]:
        
        #Make sure the value is formatted properly
        unit = productAttrDict["Inductance"][-2]
        
        if unit.isdigit() or unit == " ":
            unit = ""
        
        if unit == "µ": unit = "u"
        
        value = float(re.sub(nonNumericChars, "", productAttrDict["Inductance"]))
        
        #want to fix any value that can be expressed with a different unit (usually nano)
        if value < 1.0: 
            value *= 1000 #avoid values with decimals; move them to the previous unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e-3) #the new unit
        elif value >= 1000.0:
            value /= 1000 #avoid values larger than 1000; move them to the next unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e3) #the new unit            
         
        valueStr = str(value).replace(".",unit)
    
        tolerance = productAttrDict["Tolerance"].replace("±","")

        if productAttrDict["Package / Case"] == "Nonstandard":
            package = productAttrDict["Supplier Device Package"]
        else:
            package = productAttrDict["Package / Case"].split(" ")[0]
    
        symbolName = "L_{0}_{1}_{2}_{3}".format(valueStr,
                                                    tolerance,
                                                    productAttrDict["Current Rating"],
                                                    package)
        
        footprint = "SFUSat-ind:L_{0}".format(package)
        
        if not any(footprint.split(":")[1] in file for file in os.listdir(path="SFUSat-ind.pretty")):
            print("No footprint '{0}' found for {1}".format(footprint,symbolName))
            footprint = ""
        
        fixedAttrDict["Reference"] = "L"

    elif "Resistor" in productAttrDict["Categories"]:
        
        #Make sure the value is formatted properly
        unit = productAttrDict["Resistance"][-5]
        
        if unit.isdigit() or unit == " ":
            unit = "R"
        
        if unit == "µ": unit = "u"
        
        value = float(re.sub(nonNumericChars, "", productAttrDict["Resistance"]))
        
        #want to fix any value that can be expressed with a different unit (usually nano)
        if value < 1.0: 
            value *= 1000 #avoid values with decimals; move them to the previous unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e-3) #the new unit
        elif value >= 1000.0:
            value /= 1000 #avoid values larger than 1000; move them to the next unit
            unitValue = siUnitToValDict[unit] #get the value associated with the unit
            unit = getSiUnit(unitValue*1e3) #the new unit            
        
        valueStr = str(value).replace(".",unit)
    
        if productAttrDict["Tolerance"] == "Jumper":
            tolerance = "0%"
        else:
            tolerance = productAttrDict["Tolerance"].replace("±","")
        power = productAttrDict["Power (Watts)"].split(",")[0]

        if productAttrDict["Package / Case"] == "Nonstandard":
            package = productAttrDict["Supplier Device Package"]
        else:
            package = productAttrDict["Package / Case"].split(" ")[0]
    
        symbolName = "R_{0}_{1}_{2}_{3}".format(valueStr,
                                                tolerance,
                                                power,
                                                package)
        
        footprint = "SFUSat-res:R_{0}".format(package)
        
        
        
        if not any(footprint.split(":")[1] in file for file in os.listdir(path="SFUSat-res.pretty")):
            print("No footprint '{0}' found for {1}".format(footprint,symbolName))
            footprint = ""
        
        fixedAttrDict["Reference"] = "R"

    else:
        print("Sorry, there's only functionality for chip capacitors, resistors, and inductors at this time")
        sys.exit()

    fixedAttrDict["Value"] = symbolName
    fixedAttrDict["Footprint"] = footprint
    fixedAttrDict["Datasheet"] = ""
    
    return(fixedAttrDict)

#Create the product attribute dictionary
def makeProdAttrs(soup,productAttrDict):
    productAttrDict = getProdDetails(soup,productAttrDict) #Populate dictionary with product details
    productAttrDict = getProdAttrs(soup,productAttrDict) #Append dictionary with product attributes 
    
    productAttrDict = removeAttrs(productAttrDict) #Remove unwanted attributes from dictionary
    
    return(productAttrDict)
    
#Grab product details from the component webpage
def getProdDetails(soup,productAttrDict):
    productDetailsTable = soup.find("table", {"id": "product-details"}).find("tbody").find_all("tr")

    for row in productDetailsTable:
        field = row.find_all("th")[0].get_text().rstrip(" \r\n ").lstrip(" \r\n ")
        value = row.find_all("td")[0].get_text().rstrip(" \r\n ").lstrip(" \r\n ")
        
        productAttrDict[field] = value
        
    return(productAttrDict)

#Grab product attributes from the component webpage
def getProdAttrs(soup,productAttrDict):
    appendLastField = False #Used when the "Categories" field spans multiple rows
    productAttrTable = soup.find("table", {"id": "prod-att-table"}).find("tbody").find_all("tr")

    for row in productAttrTable:
        if ("id" in row.attrs):
            if (row.attrs["id"] == "prod-att-title-row"):
                continue
        
        try: field = row.find_all("th")[0].get_text().rstrip(" \r\n ").lstrip(" \r\n ")
        except: appendLastField = True
        
        value = row.find_all("td")[0].get_text().rstrip(" \r\n ").lstrip(" \r\n ")

        #Need to add an escape character to fields with quotation marks (like dimensions)
        if '"' in value:
            value = value.replace('\"','\\\"')
        
        #If a field (typically "Categories" spans more than one row, merge the rows)
        if appendLastField == True:
            productAttrDict[field] += (" - {0}".format(value))
            appendLastField = False
        else:
            productAttrDict[field] = value
        
    return(productAttrDict)

#Remove attributes we don't want
def removeAttrs(productAttrDict):
    for field in fieldsToIgnore:
        if field in productAttrDict:
            del(productAttrDict[field])
            
    return(productAttrDict)

#Read data from the library file
def readFile(filepath):
    libfile = open(filepath, "r")
    contents = libfile.read()
    libfile.close()
    
    return(contents)

#Write data to the library file
def writeFile(filepath,dataToWrite):
    libfile = open(filepath, "w")

    for part in dataToWrite:
        for item in part:
            libfile.write("%s\n" % item)
        
    libfile.close()

#Write data to the second last lines of the library file before the "End Library statement"
def writeToLibFile(filepath,libContents,dataToWrite):    
    dataToWrite = [[libContents.rstrip("#\n#End Library")]]+dataToWrite
    dataToWrite.append(["#\n#End Library"])

    writeFile(filepath,dataToWrite)
    
    return(dataToWrite)

def writeToDescFile(filepath,descContents,dataToWrite):
    dataToWrite = [[descContents.rstrip("#\n#End Doc Library")]]+dataToWrite
    dataToWrite.append(["#\n#End Doc Library"])
                        
    writeFile(filepath,dataToWrite)
    
    return(dataToWrite)    

###############################################################################
### MAIN SCRIPT ###
###############################################################################
for partNum in partNums:    
    soup = openUrl(partNum)
    
    productAttrDict = {}
    fixedAttrDict = {}
    
    productAttrDict = makeProdAttrs(soup,productAttrDict) #Make a dictionary filled with the product attributes
    fixedAttrDict = makeFixedAttrs(productAttrDict) #Make a dictionary filled with the KiCAD fixed attributes

    if "Capacitor" in productAttrDict["Categories"]:
        if capLibContents == None:
            capLibContents = readFile(capLibFilePath) #read the library file so we can see whether or not the part number/name already exists
            capDescContents = readFile(capDescFilePath) #read the description file to populate it later

        if partNum in capLibContents:
            print("Part number ({0}) already exists in capacitor library, checking next part...".format(partNum))
            continue
        
        if fixedAttrDict["Value"] in capLibContents:
            print("Similar part ({0}) already exists in capacitor library, checking next part...".format(fixedAttrDict["Value"]))
            continue

        capParts.append(makeLibPart(productAttrDict,fixedAttrDict,capAttrConfig,capSymbolShape))
        capDesc.append(makeDesc(productAttrDict["Description"],fixedAttrDict["Value"]))

    elif "Inductor" in productAttrDict["Categories"]:
        if indLibContents == None:
            indLibContents = readFile(indLibFilePath) #read the library file so we can see whether or not the part number/name already exists
            indDescContents = readFile(indDescFilePath) #read the description file to populate it later

        if partNum in indLibContents:
            print("Part number ({0}) already exists in inductor library, checking next part...".format(partNum))
            continue
        
        if fixedAttrDict["Value"] in indLibContents:
            print("Similar part ({0}) already exists in inductor library, checking next part...".format(fixedAttrDict["Value"]))
            continue

        indParts.append(makeLibPart(productAttrDict,fixedAttrDict,indAttrConfig,indSymbolShape))
        indDesc.append(makeDesc(productAttrDict["Description"],fixedAttrDict["Value"]))

    elif "Resistor" in productAttrDict["Categories"]:
        if resLibContents == None:
            resLibContents = readFile(resLibFilePath) #read the library file so we can see whether or not the part number/name already exists
            resDescContents = readFile(resDescFilePath) #read the description file to populate it later

        if partNum in resLibContents:
            print("Part number ({0}) already exists in resistor library, checking next part...".format(partNum))
            continue
        
        if fixedAttrDict["Value"] in resLibContents:
            print("Similar part ({0}) already exists in resistor library, checking next part...".format(fixedAttrDict["Value"]))
            continue

        resParts.append(makeLibPart(productAttrDict,fixedAttrDict,resAttrConfig,resSymbolShape))
        resDesc.append(makeDesc(productAttrDict["Description"],fixedAttrDict["Value"]))

    else:
        print("Sorry, currently only chip capacitors, inductors, and resistors are supported.")
        continue

if not capParts == []:
    writeToLibFile(capLibFilePath,capLibContents,capParts)
    writeToDescFile(capDescFilePath,capDescContents,capDesc)
if not indParts == []:
    writeToLibFile(indLibFilePath,indLibContents,indParts)
    writeToDescFile(indDescFilePath,indDescContents,indDesc)
if not resParts == []:
    writeToLibFile(resLibFilePath,resLibContents,resParts)
    writeToDescFile(resDescFilePath,resDescContents,resDesc)

print("Library updating complete.")