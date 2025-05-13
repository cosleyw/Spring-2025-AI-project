import os


def compareFiles(plan):

    path = "plans"
    synopsis = "synopsis.txt"
    allInputList = []
    allOutputList = []

    '''getting input data'''
    for filename in os.listdir(path):
        inputData = [filename]
        inFile = open(os.path.join(path,filename),'r')
        inFile.readline()
        inFile.readline()
        try:
            for line in inFile:
                dataDescription,data = line.split(': ')
                inputData.append(data)
        except:
            pass
        if filename == plan:
            masterInputList = inputData
        elif filename == synopsis or filename == "top3.txt":
            pass
        else:
            allInputList.append(inputData)
    #getting output data        
    for filename in os.listdir(path):
        outputData = [filename]
        outputCount = 0
        inFile = open(os.path.join(path,filename),'r')
        for line in range(16):
            inFile.readline()
        for line in inFile:
            try:
                data,courseName = line.split('::')
                outputData.append(data)
                outputCount = outputCount + 1
            except:
                pass
        if filename == plan:
            masterOutputList = outputData
            outputCountFinal = outputCount
        elif filename == synopsis or filename == "top3.txt":
            pass
        else:
            allOutputList.append(outputData)
            
    '''getting output data'''
    with open(os.path.join(path, synopsis),"w") as f:
        f.write("Synopsis-\nYour Input:\n")
        f.write(str(masterInputList))
        f.write("\nYour Output:\n")
        f.write(str(masterOutputList))
    matchList = []
    for dataList in allInputList:
        matchList.append(dataList[0])
        inputMatchCount = 0
        for item in range(len(dataList)):
            if dataList[item] == masterInputList[item]:
                inputMatchCount = inputMatchCount + 1
            else:
                pass
        matchList.append(inputMatchCount)
    for dataList2 in allOutputList:
        outputMatchCount = 0
        for item2 in range(len(dataList2)):
            if dataList2[item2] in masterOutputList:
                outputMatchCount = outputMatchCount + 1
        matchList.append(outputMatchCount)
    jumpCount = int(len(matchList)/3)
    for item in range(jumpCount):
        with open(os.path.join(path, synopsis),"a") as f:
            f.write(f"\n{matchList[0 + (2 * item)]},{matchList[1 + (2 * item)]},input,{matchList[(jumpCount * 2) + item]},output")

    '''creating file with top 3 matches'''
    synopsisOpen = open(os.path.join(path,synopsis),'r')
    for j in range(5):
        synopsisOpen.readline()

    in1 = 0
    inName1 = "none"
    in2 = 0
    inName2 = "none"
    in3 = 0
    inName3 = "none"
    out1 = 0
    outName1 = "none"
    out2 = 0
    outName2 = "none"
    out3 = 0
    outName3 = "none"
    for line in synopsisOpen:
        name,inMatches,intext,outMatches,outtext = line.split(",")
        inMatches = int(inMatches)
        if inMatches >= in3:
            in3 = inMatches
            inName3 = name
            if inMatches >= in2:
                in3 = in2
                inName3 = inName2
                in2 = inMatches
                inName2 = name
                if inMatches >= in3:
                    in2 = in1
                    inName2 = inName1
                    in1 = inMatches
                    inName1 = name
        else:
            pass
        outMatches = int(outMatches)
        if outMatches >= out3:
            out3 = outMatches
            outName3 = name
            if outMatches >= out2:
                out3 = out2
                outName3 = outName2
                out2 = outMatches
                outName2 = name
                if outMatches >= out1:
                    out2 = out1
                    outName2 = outName1
                    out1 = outMatches
                    outName1 = name
        else:
            pass
    
    with open(os.path.join(path, "top3.txt"),"w") as f:
        f.write("input\n")
        f.write(f"{inName1},{in1}\n")
        f.write(f"{inName2},{in2}\n")
        f.write(f"{inName3},{in3}\n")
        f.write("output\n")
        f.write(f"{outName1},{out1}\n")
        f.write(f"{outName2},{out2}\n")
        f.write(f"{outName3},{out3}\n")
