import numpy as np
from tqdm import tqdm
from random import random
from tqdm import tnrange
import time
import pickle

print("Started Program")

GIFTSboxBase3 = (3,7, 0x2, 5, 0, 1, 0x2, 4, 0x2,0x2,0x2,0x2, 0xd, 0xc, 0x2, 0xf) #S1
#GIFTSboxBase3 = (0, 5, 0x2, 0xf, 7, 0xc, 0x2, 1, 0x2, 0x2, 0x2, 0x2, 0xd, 3, 0x2, 4) #Noted as S2 on R2
#GIFTSboxBase3 = (0,1, 0x2, 4, 3, 5, 0x2, 0xd, 0x2, 0x2, 0x2, 0x2, 0xf, 0xc, 0x2, 7)#Noted as S3 on R2
#GIFTSboxBase3 = (0, 1, 0x2, 4, 0xc, 7, 0x2, 3, 0x2, 0x2, 0x2, 0x2, 0xd, 5, 0x2, 0xf)#S4 code description
#GIFTSboxBase3 = (0, 1, 0x2, 3, 4, 5, 0x2, 7, 0x2, 0x2, 0x2, 0x2, 0xd, 0xf, 0x2, 0xc) #S5 code description
#GIFTSboxBase3 = (0, 1, 0x2, 4, 3, 5, 0x2, 0xc, 0x2, 0x2, 0x2, 0x2, 0xd, 0xf, 0x2, 7) #S6 Code form

GIFTPbox64Base3 = ( 0, 8,16, 24,1,9,17,25,
                            2,10,18,26,3,11,19,27,
                            4,12,20,28,5,13,21,29,
                            6,14,22,30,7,15,23,31 )

def BitToByte(input):
    return (int)((input)/8)

def TritToByte(input):
    return (int) ((input)/4)

def NibbleToByte(input):
    return (int)((input)/2)


def ByteInputSBoxGIFTBase3(input):
    temp = GIFTSboxBase3[(input & 0xf)]
    temp2 = GIFTSboxBase3[((input >> 4) & 0xf)]
    return (temp2 << 4) | temp



def ApplySBox64Base3(input):
    tempArr = [0] * 8
    for i in range(8):
        tempArr[i] = 0x0
        tempArr[i] = ByteInputSBoxGIFTBase3(input[i])
    return tempArr


def ApplyPLayerBase3(input):
    temp = [0] * 8
    for i in range(32):
        tempTrit = (((input[TritToByte(i)]) >> ((i%4)*2)) & 0b11)
        pVal = GIFTPbox64Base3[i]
        temp[TritToByte(pVal)] |= (tempTrit << ((pVal % 4)*2))
    return temp
                    
def NibbleAddRoundKeyBase3(input1, input2):
    highIn1 = (input1 >> 2) & 0b11
    lowIn1 = input1 & 0b11
    highIn2 = (input2 >> 2) & 0b11
    lowIn2 = input2 & 0b11 
    
    highIn1 = fixFormat(highIn1)
    highIn2 = fixFormat(highIn2)
    lowIn1 = fixFormat(lowIn1)
    lowIn2 = fixFormat(lowIn2)
    
    sumHigh = (highIn1 + highIn2) % 3
    sumLow = (lowIn1 + lowIn2) % 3
    return (( fixFormat2(sumHigh)  << 2) | fixFormat2(sumLow))

def fixFormat(inputTrit):
    if(inputTrit == 3):
        return 2
    return inputTrit

def fixFormat2(inputTrit):
    if(inputTrit == 2):
        return 3
    return inputTrit

def ByteAddRoundKeyBase3(input1, input2):
    highIn1 = (input1 >> 4) & 0xf
    highIn2 = (input2 >> 4) & 0xf
    lowIn1 = input1 & 0xf
    lowIn2 = input2 & 0xf
    outHigh = NibbleAddRoundKeyBase3(highIn1, highIn2)
    outLow = NibbleAddRoundKeyBase3(lowIn1, lowIn2)
    return (outHigh << 4) | outLow
   
                    
def FullAddRoundKeyBase3(input, roundKey):
    returnArr = [0] * 8
    for i in range(8):
        returnArr[i] = ByteAddRoundKeyBase3(input[i], roundKey[i])
    return returnArr
                    

                    
def GIFT64toIntermediate1Base3(pt):
    temp = [0] * 8
    for i in range(8):
        temp[i] = pt[i]
    temp = ApplySBox64Base3(temp)
    temp = ApplyPLayerBase3(temp)
    return temp

def GIFT64toIntermediate2Base3(pt, RK1):
    temp = [0] * 8
    temp = GIFT64toIntermediate1Base3(pt)
    temp = FullAddRoundKeyBase3(temp, RK1)
    temp = ApplySBox64Base3(temp)
    temp = ApplyPLayerBase3(temp)
    return temp

def GIFT64toIntermediate3Base3(pt, RK1, RK2):
    temp = [0] * 8
    temp = GIFT64toIntermediate2Base3(pt, RK1)
    temp = FullAddRoundKeyBase3(temp, RK2)
    temp = ApplySBox64Base3(temp)
    temp = ApplyPLayerBase3(temp)
    return temp

def GIFT64toIntermediate4Base3(pt, RK1, RK2, RK3):
    temp = [0] * 8
    temp = GIFT64toIntermediate3Base3(pt, RK1, RK2)
    temp = FullAddRoundKeyBase3(temp, RK3)
    temp = ApplySBox64Base3(temp)
    temp = ApplyPLayerBase3(temp)
    return temp
    
    

def Sanatize(arr):
    returnArr = [0] * len(arr)
    for i in range(len(arr)):
        tempArr = [0] * 4
        for j in range(4): 
            tempArr[j] = ((arr[i] >> (j*2)) & 0b11)
            if(tempArr[j] == 0b10):
                tempArr[j] = 0
        for j in range(4):
            returnArr[i] |= (tempArr[j] << (2*j))
    return returnArr

def applyGuess(index, buffer, subKeyGuess):
    #print(NibbleToByte(index))
    temp = (buffer[NibbleToByte(index)] >> ((index % 2)*4)) & 0x0f
    temp = NibbleAddRoundKeyBase3(temp, subKeyGuess)
    temp = GIFTSboxBase3[temp]
    #print(temp)
    #temp = buffer[0] & 0xf
    #temp = temp ^ subKeyGuess
    #temp = GIFTSbox[temp]
    return temp

def GuessToRoundKeyFormat(arr):
    retArr = [0]*8
    #print ("length return val " , len(retArr))
    #print ("length arr " , len(arr))
    for i in range(8): 
        #print (i)
        retArr[i] = arr[2*i] | (arr[(2*i+1)] << 4)
    return retArr

def ExtractLow(RK):
    retArr = [0]*2
    for i in range(4):
        tritLow = (RK[i] & 0b11)
        tritHigh = ((RK[i] >> 4) & 0b11)
        concatVal = tritLow | (tritHigh << 2)
        retArr[(int)(i/2)] |= (concatVal << ((i%2)*4))
    return retArr

def ExtractHigh(RK):
    retArr = [0]*2
    for i in range(4,8):
        tritLow = ( (RK[i]) & 0b11)
        tritHigh = ((RK[i] >> 4) & 0b11)
        concatVal = tritLow | (tritHigh << 2)
        retArr[(int)((i-4)/2)] |= (concatVal << ((i%2)*4))
    return retArr

def ReverseKeySchedulerBase3(RK1, RK2, RK3, RK4):
    retArr = [0] * 16
    
    V0 = ExtractLow(RK3)
    V1 = ExtractHigh(RK3)
    V2 = ExtractLow(RK4)
    V3 = ExtractHigh(RK4)
    U0 = ExtractLow(RK1)
    U1 = ExtractHigh(RK1)
    U2 = ExtractLow(RK2)
    U3 = ExtractHigh(RK2)
    
    retArr[0] = U1[0]
    retArr[1] = U1[1]
    retArr[2] = U0[0]
    retArr[3] = U0[1]
    retArr[4] = U3[0]
    retArr[5] = U3[1]
    retArr[6] = U2[0]
    retArr[7] = U2[1]
    retArr[8] = V1[0]
    retArr[9] = V1[1]
    retArr[10] = V0[0]
    retArr[11] = V0[1]
    retArr[12] = V3[0]
    retArr[13] = V3[1]
    retArr[14] = V2[0]
    retArr[15] = V2[1]
    
    return retArr


def Base3CPAAttack(trace_array, trace_array2,trace_array3,trace_array4, textin_array, textin_array2, textin_array3, textin_array4, knownkey):
    
    HW = [bin(n).count("1") for n in range(0, 16)]

    numtraces = np.shape(trace_array)[0] #total number of traces
    numtraces2 = np.shape(trace_array2)[0]
    numtraces3 = np.shape(trace_array3)[0]
    numtraces4 = np.shape(trace_array4)[0]
    numpoint = np.shape(trace_array)[1] #samples per trace
    #numpoint = 50000
    #print("num traces " , numtraces)

    cparefs = [0] * 16
    bestguess = [0]*16
    tritSet = (0x00, 0x01, 0x03)

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in tritSet:

        # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
        
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces)
            for tnum in range(0, numtraces):
            #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
            #print(textin_array[tnum])
            #print("PT: " , textin_array[tnum])
            #invText = Invert(textin_array[tnum])
            #tempNum = GIFT64toIntermediate1Base3(invText)
                tempNum = GIFT64toIntermediate1Base3(textin_array[tnum])
            #print("Intermetary state: ", tempNum)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
            #print(appliedGuess)
                hyp[tnum] = HW[appliedGuess]
            #print(HW[appliedGuess])
            #print(hyp[tnum])

        # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
        #print("meanh " , meanh)
        
        #print(meanh)

        # Mean of all points in trace
            meant = np.mean(trace_array, axis=0, dtype=np.float64)
        #print("here")
        #print(len(meant))

        # For each trace, do the following
            for tnum in range(0, numtraces):
                hdiff = (hyp[tnum] - meanh)
                tdiff = trace_array[tnum, :] - meant
            #print("tdiff")
            #print("len tdiff " , len(tdiff))
            #print(tdiff)

                sumnum = sumnum + (hdiff * tdiff)
            #print(sumnum) All zeros
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff
            #print("len sumnum ", len(sumnum))

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
            #print("Subkey guess " , kguess, " had correlation value " , maxcpa[kguess])

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK1 = GuessToRoundKeyFormat(bestguess)
#rint(RK1)
    #print("Prediction for Round Key 1")
    #for b in RK1: print("%02x " % b, end="")
#print("Best Key Guess: ", end="")
#for b in bestguess: print("%01x " % b, end="")

    cparefs = [0] * 16
    bestguess = [0]*16
    tritSet = (0x00, 0x01, 0x03)

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in tritSet:

        # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces2)
            for tnum in range(0, numtraces2):
            #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
            #print(textin_array[tnum])
            #print("PT: " , textin_array[tnum])
            #invText = Invert(textin_array[tnum])
            #tempNum = GIFT64toIntermediate1Base3(invText)
                tempNum = GIFT64toIntermediate2Base3(textin_array2[tnum], RK1)
            #print("Intermetary state: ", tempNum)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
            #print(appliedGuess)
                hyp[tnum] = HW[appliedGuess]
            #print(HW[appliedGuess])
            #print(hyp[tnum])

        # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
        #print("meanh " , meanh)
        
        #print(meanh)

        # Mean of all points in trace
            meant = np.mean(trace_array2, axis=0, dtype=np.float64)
        #print("here")
        #print(len(meant))

        # For each trace, do the following
            for tnum in range(0, numtraces2):
                hdiff = (hyp[tnum] - meanh)
                tdiff = trace_array2[tnum, :] - meant
            #print("tdiff")
            #print("len tdiff " , len(tdiff))
            #print(tdiff)

                sumnum = sumnum + (hdiff * tdiff)
            #print(sumnum) All zeros
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff
            #print("len sumnum ", len(sumnum))

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
            #print("Subkey guess " , kguess, " had correlation value " , maxcpa[kguess])

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK2 = GuessToRoundKeyFormat(bestguess)
#rint(RK1)
    #print("Prediction for Round Key 2")
    #for b in RK2: print("%02x " % b, end="")
    
    
    cparefs = [0] * 16
    bestguess = [0]*16
    tritSet = (0x00, 0x01, 0x03)

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in tritSet:

        # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces3)
            for tnum in range(0, numtraces3):
            #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
            #print(textin_array[tnum])
            #print("PT: " , textin_array[tnum])
            #invText = Invert(textin_array[tnum])
            #tempNum = GIFT64toIntermediate1Base3(invText)
                tempNum = GIFT64toIntermediate3Base3(textin_array3[tnum], RK1, RK2)
            #print("Intermetary state: ", tempNum)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
            #print(appliedGuess)
                hyp[tnum] = HW[appliedGuess]
            #print(HW[appliedGuess])
            #print(hyp[tnum])

        # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
        #print("meanh " , meanh)
        
        #print(meanh)

        # Mean of all points in trace
            meant = np.mean(trace_array3, axis=0, dtype=np.float64)
        #print("here")
        #print(len(meant))

        # For each trace, do the following
            for tnum in range(0, numtraces3):
                hdiff = (hyp[tnum] - meanh)
                tdiff = trace_array3[tnum, :] - meant
            #print("tdiff")
            #print("len tdiff " , len(tdiff))
            #print(tdiff)

                sumnum = sumnum + (hdiff * tdiff)
            #print(sumnum) All zeros
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff
            #print("len sumnum ", len(sumnum))

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
            #print("Subkey guess " , kguess, " had correlation value " , maxcpa[kguess])

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK3 = GuessToRoundKeyFormat(bestguess)
#rint(RK1)
    #print("Prediction for Round Key 3")
    #for b in RK3: print("%02x " % b, end="")
#print("Best Key Guess: ", end="")
#for b in bestguess: print("%01x " % b, end="")

    cparefs = [0] * 16
    bestguess = [0]*16
    tritSet = (0x00, 0x01, 0x03)

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in tritSet:

        # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces4)
            for tnum in range(0, numtraces4):
            #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
            #print(textin_array[tnum])
            #print("PT: " , textin_array[tnum])
            #invText = Invert(textin_array[tnum])
            #tempNum = GIFT64toIntermediate1Base3(invText)
                tempNum = GIFT64toIntermediate4Base3(textin_array4[tnum], RK1, RK2, RK3)
            #print("Intermetary state: ", tempNum)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
            #print(appliedGuess)
                hyp[tnum] = HW[appliedGuess]
            #print(HW[appliedGuess])
            #print(hyp[tnum])

        # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
        #print("meanh " , meanh)
        
        #print(meanh)

        # Mean of all points in trace
            meant = np.mean(trace_array4, axis=0, dtype=np.float64)
        #print("here")
        #print(len(meant))

        # For each trace, do the following
            for tnum in range(0, numtraces4):
                hdiff = (hyp[tnum] - meanh)
                tdiff = trace_array4[tnum, :] - meant
            #print("tdiff")
            #print("len tdiff " , len(tdiff))
            #print(tdiff)

                sumnum = sumnum + (hdiff * tdiff)
            #print(sumnum) All zeros
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff
            #print("len sumnum ", len(sumnum))

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
            #print("Subkey guess " , kguess, " had correlation value " , maxcpa[kguess])

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK4 = GuessToRoundKeyFormat(bestguess)
#rint(RK1)
    #print("Prediction for Round Key 4")
    #for b in RK4: print("%02x " % b, end="")

    #print ("\nReversing the Key scheduler")
    extractedKey = ReverseKeySchedulerBase3(RK1, RK2, RK3, RK4)
    #print (extractedKey)
    #print ("known key")
    #print (knownkey)
    return extractedKey

pool1Trace = pickle.load( open( "pool1Trace.p", "rb" ) )
pool2Trace = pickle.load( open( "pool2Trace.p", "rb" ) )
pool3Trace = pickle.load( open( "pool3Trace.p", "rb" ) )
pool4Trace = pickle.load( open( "pool4Trace.p", "rb" ) )

pool1Text = pickle.load( open( "pool1Text.p", "rb" ) )
pool2Text = pickle.load( open( "pool2Text.p", "rb" ) )
pool3Text = pickle.load( open( "pool3Text.p", "rb" ) )
pool4Text = pickle.load( open( "pool4Text.p", "rb" ) )

print("pickle files loaded")

poolSize = 2000
NumExperements = 100
traceCapSize = 150
SRArr = sumnum = np.zeros(traceCapSize + 1)
#knownKey = pool1[0].key
knownKey = (3, 124, 21, 20, 0, 12, 208, 4, 3, 247, 21, 0, 1, 207, 79, 60)

for i in range(NumExperements):
    traces1 = []
    traces2 = []
    traces3 = []
    traces4 = []
    text1 = []
    text2 = []
    text3 = []
    text4 = []
	
    streak = 0
    for j in range(traceCapSize):
        randNum = int(random() * poolSize)
        traces1.append(pool1Trace[randNum]) 
        traces2.append(pool2Trace[randNum])
        traces3.append(pool3Trace[randNum])
        traces4.append(pool4Trace[randNum])
        text1.append(pool1Text[randNum])
        text2.append(pool2Text[randNum])
        text3.append(pool3Text[randNum])
        text4.append(pool4Text[randNum])
        
        traces1Out = np.asarray([trace for trace in traces1])
        traces2Out = np.asarray([trace for trace in traces2])
        traces3Out = np.asarray([trace for trace in traces3])
        traces4Out = np.asarray([trace for trace in traces4])
        text1Out = np.asarray([trace for trace in text1])
        text2Out = np.asarray([trace for trace in text2])
        text3Out = np.asarray([trace for trace in text3])
        text4Out = np.asarray([trace for trace in text4])
        
        if(streak >= 5):
            guess = knownKey
            print("streak on experement" , i)
        else:
            guess = Base3CPAAttack(traces1Out,traces2Out,traces3Out,traces4Out,text1Out,text2Out,text3Out,text4Out, knownKey)
			
        
        passed = True
        for k in range(16):
            if(guess[k] != knownKey[k]):
                passed = False
                streak = 0
        if (passed):
            SRArr[j+1] += 1
			
        if(passed):
            streak += 1
			

    print("Experement", i, "completed")
            
print ("Finished\n Printing out results")
for i in range(traceCapSize):
    print ("Trace size of " , (i+1) , "had a mean success rate of " , (SRArr[i+1]/NumExperements))
