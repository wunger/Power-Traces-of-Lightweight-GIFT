import numpy as np
from tqdm import tqdm
from random import random
from tqdm import tnrange
import time
import pickle

print("Started Program")

#GIFTSbox = ( 0x1, 0xa, 0x4, 0xc, 0x6, 0xf, 0x3, 0x9, 0x2, 0xd, 0xb, 0x7, 0x5, 0x0, 0x8, 0xe) #GIFT
#GIFTSbox = ( 0xc, 0x5, 0x6, 0xb, 0x9, 0x0, 0xa, 0xd, 0x3, 0xe, 0xf, 0x8, 0x4, 0x7, 0x1, 0x2 )#PRESENT
GIFTSbox =  ( 0xe, 0x4, 0xb, 0x2, 0x3, 0x8, 0x0, 0x9,0x1, 0xa, 0x7, 0xf, 0x6, 0xc, 0x5, 0xd )#Piccolo
#GIFTSbox = (0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8,0x9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x0)#S(x) = x+1
#GIFTSbox = (0,0xf,0xe, 0xd,0xc,0xb,0xa,0x9,0x8,0x7,0x6,0x5,0x4,0x3,0x2,0x1)#S(x) = -x mod 16
#GIFTSbox = (0x0,0xe,0x7,0x6,0x4,0x5,0x2,0x1,0x3,0xf,0xa,0xb,0x8,0x9,0xc,0xd) #Random 1.1
#GIFTSbox = (0x5,0x1,0x7,0x6,0x4,0x0,0x2,0xe,0x3,0xf,0xb,0xa,0x8,0x9,0xc,0xd) #Random 1.2

GIFTPbox64 =             ( 0,  17, 34, 51, 48, 1,  18, 35, 32, 49, 2,  19, 16,
                           33, 50, 3,  4,  21, 38, 55, 52, 5,  22, 39, 36, 53,
                           6,  23, 20, 37, 54, 7,  8,  25, 42, 59, 56, 9,  26,
                           43, 40, 57, 10, 27, 24, 41, 58, 11, 12, 29, 46, 63,
                           60, 13, 30, 47, 44, 61, 14, 31, 28, 45, 62, 15 )

#print( GIFTSbox[0])



def BitToByte(input):
    return (int)((input)/8)

def NibbleToByte(input):
    return (int)((input)/2)

def ByteInputSBoxGIFT(input):
    temp = GIFTSbox[(input & 0xf)]
    temp2 = GIFTSbox[((input >> 4) & 0xf)]
    return (temp2 << 4) | temp

def ApplySBox64(input):
    for i in range(8):
        input[i] = ByteInputSBoxGIFT(input[i])
    return input

def ApplyPLayer(input):
    #print ("player function input " , input)
    temp = []
    for i in range(8):
        temp.append(input[i])
        temp[i] = 0 #Used to create an empty byte array of length 8
        #print("byte " , i , " has value " , input[i] )
    for i in range(64):
        tempBit = ((input[BitToByte(i)]) >> ((i%8))) & 0x1
        #print (tempBit)
        pVal = GIFTPbox64[i]
        temp[BitToByte(pVal)] |= (tempBit << (pVal%8))
    return temp

def Invert(input):
    temp = []
    for i in range(8):
        temp.append(input[7-i])
    return temp

def GIFT64PTtoIntermediate1(pt):  #value inbetween 1st pLayer and 1st Add round key
    #temp = Invert(pt)
    temp = []
    for i in range(8):
        temp.append(pt[i])
    temp = ApplySBox64(temp)
    temp = ApplyPLayer(temp)
    return temp

def GIFT64PTtoIntermediate2(pt, RK1):
    temp = GIFT64PTtoIntermediate1(pt)
    for i in range(8):
        temp[i] = temp[i] ^ RK1[i]
    temp = GIFT64PTtoIntermediate1(temp)
    return temp

def GIFT64PTtoIntermediate3(pt, RK1, RK2):
    temp = GIFT64PTtoIntermediate2(pt, RK1)
    for i in range(8):
        temp[i] = temp[i] ^ RK2[i]
    temp = GIFT64PTtoIntermediate1(temp)
    return temp

def GIFT64PTtoIntermediate4(pt, RK1, RK2, RK3):
    temp = GIFT64PTtoIntermediate3(pt, RK1, RK2)
    for i in range(8):
        temp[i] = temp[i] ^ RK3[i]
    temp = GIFT64PTtoIntermediate1(temp)
    return temp

def applyGuess(index, buffer, subKeyGuess):
    #print(NibbleToByte(index))
    temp = (buffer[NibbleToByte(index)] >> ((index % 2)*4)) & 0x0f
    temp = temp ^ subKeyGuess
    temp = GIFTSbox[temp]
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


    
def ExtractV(RK):
    retArr = [0]*2
    for i in range(8):
        bitLow = (RK[i] & 0b1)
        bitHigh = ((RK[i] >> 4) & 0b1)
        concatVal = bitLow | (bitHigh << 1)
        retArr[(int)(i/4)] |= (concatVal << ((i%4)*2))
    return retArr

def ExtractU(RK):
    retArr = [0]*2
    for i in range(8):
        bitLow = ( (RK[i]>> 1) & 0b1)
        bitHigh = ((RK[i] >> 5) & 0b1)
        concatVal = bitLow | (bitHigh << 1)
        retArr[(int)(i/4)] |= (concatVal << ((i%4)*2))
    return retArr

def ReverseKeyScheduler(RK1, RK2, RK3,RK4):
    retArr = [0] * 16
    
    V0 = ExtractV(RK1)
    V1 = ExtractV(RK2)
    V2 = ExtractV(RK3)
    V3 = ExtractV(RK4)
    U0 = ExtractU(RK1)
    U1 = ExtractU(RK2)
    U2 = ExtractU(RK3)
    U3 = ExtractU(RK4)
    
    retArr[0] = V0[0]
    retArr[1] = V0[1]
    retArr[2] = U0[0]
    retArr[3] = U0[1]
    retArr[4] = V1[0]
    retArr[5] = V1[1]
    retArr[6] = U1[0]
    retArr[7] = U1[1]
    retArr[8] = V2[0]
    retArr[9] = V2[1]
    retArr[10] = U2[0]
    retArr[11] = U2[1]
    retArr[12] = V3[0]
    retArr[13] = V3[1]
    retArr[14] = U3[0]
    retArr[15] = U3[1]
    
    return retArr



def Base2CPAAttack(DS1, DS2,DS3,DS4, TIn1, TIn2, TIn3, TIn4, knownkey):
    HW = [bin(n).count("1") for n in range(0, 16)]

    numtraces = np.shape(DS1)[0] #total number of traces
    numpoint = np.shape(DS1)[1] #samples per trace
    numtraces2 = np.shape(DS2)[0] #total number of traces
    numpoint2 = np.shape(DS2)[1] #samples per trace
    numtraces3 = np.shape(DS3)[0] #total number of traces
    numpoint3 = np.shape(DS3)[1] #samples per trace
    numtraces4 = np.shape(DS4)[0] #total number of traces
    numpoint4 = np.shape(DS4)[1] #samples per trace
#numpoint = 22000
#print (numtraces)

    #pt = textin_array
    #knownkey = traces[0].key
    cparefs = [0] * 16
    bestguess = [0]*16

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in range(0, 16):

        # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces)
            for tnum in range(0, numtraces):
                #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
                tempNum = GIFT64PTtoIntermediate1(TIn1[tnum])
                appliedGuess = applyGuess(bnum, tempNum, kguess)
                hyp[tnum] = HW[appliedGuess]

        # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
        #print(meanh)

        # Mean of all points in trace
            meant = np.mean(DS1, axis=0, dtype=np.float64)
        #print("here")
        
        #print(len(meant))

        # For each trace, do the following
            for tnum in range(0, numtraces):
                hdiff = (hyp[tnum] - meanh)
                tdiff = DS1[tnum, :] - meant
                #print("tdiff")
                #print("len tdiff " , len(tdiff))
                #print(tdiff)

                sumnum = sumnum + (hdiff * tdiff)
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff
                #print("len sumnum ", len(sumnum))

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
           # print("Subkey guess " , kguess, " had correlation value " , maxcpa[kguess])

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

    for bnum in range(0, 16):
        maxcpa = [0] * 16
        for kguess in range(0, 16):

            # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces2)
            for tnum in range(0, numtraces2):
                #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
                tempNum = GIFT64PTtoIntermediate2(TIn2[tnum], RK1)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
                hyp[tnum] = HW[appliedGuess]

            # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)

            # Mean of all points in trace
            meant = np.mean(DS2, axis=0, dtype=np.float64)

            # For each trace, do the following
            for tnum in range(0, numtraces):
                hdiff = (hyp[tnum] - meanh)
                tdiff = DS2[tnum, :] - meant


                sumnum = sumnum + (hdiff * tdiff)
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK2 = GuessToRoundKeyFormat(bestguess)
    #print("Prediction for Round Key 2")
    #for b in RK2: print("%02x " % b, end="")
    #print("Best Key Guess: ", end="")
    #for b in bestguess: print("%01x " % b, end="")

    cparefs = [0] * 16
    bestguess = [0]*16

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in range(0, 16):

            # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces3)
            for tnum in range(0, numtraces3):
                #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
                tempNum = GIFT64PTtoIntermediate3(TIn3[tnum], RK1, RK2)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
                hyp[tnum] = HW[appliedGuess]

            # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)

            # Mean of all points in trace
            meant = np.mean(DS3, axis=0, dtype=np.float64)

            # For each trace, do the following
            for tnum in range(0, numtraces3):
                hdiff = (hyp[tnum] - meanh)
                tdiff = DS3[tnum, :] - meant

                sumnum = sumnum + (hdiff * tdiff)
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK3 = GuessToRoundKeyFormat(bestguess)
    #print("Prediction for Round Key 3")
    #for b in RK3: print("%02x " % b, end="")
    #print("Best Key Guess: ", end="")
    #for b in bestguess: print("%01x " % b, end="")

    cparefs = [0] * 16
    bestguess = [0]*16

    for bnum in range(0, 16):
        cpaoutput = [0] * 16
        maxcpa = [0] * 16
        for kguess in range(0, 16):

            # Initialize arrays &amp; variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)

            hyp = np.zeros(numtraces4)
            for tnum in range(0, numtraces4):
                #hyp[tnum] = HW[intermediate(pt[tnum][bnum], kguess)]
                tempNum = GIFT64PTtoIntermediate4(TIn4[tnum], RK1, RK2, RK3)
                appliedGuess = applyGuess(bnum, tempNum, kguess)
                hyp[tnum] = HW[appliedGuess]

            # Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)

            # Mean of all points in trace
            meant = np.mean(DS4, axis=0, dtype=np.float64)

            # For each trace, do the following
            for tnum in range(0, numtraces4):
                hdiff = (hyp[tnum] - meanh)
                tdiff = DS4[tnum, :] - meant

                sumnum = sumnum + (hdiff * tdiff)
                sumden1 = sumden1 + hdiff * hdiff
                sumden2 = sumden2 + tdiff * tdiff

            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))

        bestguess[bnum] = np.argmax(maxcpa)
        cparefs[bnum] = np.argsort(maxcpa)[::-1]

    RK4 = GuessToRoundKeyFormat(bestguess)
    #print("Prediction for Round Key 4")
    #for b in RK4: print("%02x " % b, end="")
    #print("Best Key Guess: ", end="")
    #for b in bestguess: print("%01x " % b, end="")

    guessKey = ReverseKeyScheduler(RK1, RK2, RK3,RK4)
    #print ("\nPredicted Key")
    #for b in guessKey: print("%02x " % b, end="")
        
    return guessKey

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
knownKey = (0x2b, 0x7e, 0x15, 0x16,0x28, 0xae, 0xd2, 0xa6,0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c)

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
            guess = Base2CPAAttack(traces1Out,traces2Out,traces3Out,traces4Out,text1Out,text2Out,text3Out,text4Out, knownKey)
			
        
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
