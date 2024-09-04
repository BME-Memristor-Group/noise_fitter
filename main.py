import numpy as np
import pandas as pd
from scipy import interpolate, signal
from matplotlib import pyplot as plt
import math


def scaleLength(l, rl, sc):
	return math.floor((sc/l)*rl)
def load_file(file):
	bi = np.fromfile(file, dtype=np.float32)

	# Get metadata from binary file
	chMode = bi[0]
	coupling = bi[1]
	sampleRate = bi[2] 
	mode = bi[3]
	gain = bi[4]
	rSer= bi[5]
	measMode = bi[19]
	progOff=0
	length = bi[20] * 1000 # length in ms

	if measMode != 3:
		agilentOff=0
		cardOff=0
		biasDiv=0
		agilentTime=0
		rcTime=0
	else:
		agilentOff=bi[6]
		cardOff=bi[7]
		biasDiv=bi[8]
		agilentTime=bi[9]
		rcTime=bi[10]

	# filename from input
	fileName = file.split("/")[-1]

	# Number of segments influencing the data [metadata(22) -> segment(numOfSegments*3) -> data(remaining)]
	numOfSegments = int(bi[21])
	

	# Segment data -> [length, start, end]
	endOfSegmentsIndex = 22 + (numOfSegments * 3)
	segmentArray = bi[22:endOfSegmentsIndex].reshape(numOfSegments,3).T

	# Data is (V)
	rawData = bi[endOfSegmentsIndex:]

	# this snippet is used to generate the arbitrary signal for the fixed length of 65535
	# i know it looks magic, sry for that
	# what it does is first generate a signal for the fixed length of 65535 and then scales back it according to the length of the rawData
	# commented arbSignalFixed can help with understanding
	# this signal is in (V)

	cons = 65535
	rLen = len(rawData)
	#arbSignalFixed = np.zeros(cons) 
	arbSignalFull = np.zeros(rLen)
	arbSegmented = []
	rawSegmented = []
	start = 0
	for i in range(numOfSegments):
		next = i < numOfSegments-1 and int(segmentArray[0][i]) or cons
		#arbSignalFixed[start:next] = np.linspace(segmentArray[1][i], segmentArray[2][i], next-start)
		scaledStart, scaledNext = int(rLen*(start/cons)), int(rLen*(next/cons))
		arbSignalFull[scaledStart:scaledNext] = np.linspace(segmentArray[1][i], segmentArray[2][i], scaledNext-scaledStart)
		arbSegmented.append(arbSignalFull[scaledStart:scaledNext])
		rawSegmented.append(rawData[scaledStart:scaledNext]) 
		start = next
	# this signal needs to be converted to the length of the rawData
	rawData = rawData/gain
	resistance = np.zeros(rLen)
	if mode == 0:
		resistance = (rawData*rSer)/(arbSignalFull-rawData)
	elif mode == 1:
		resistance = arbSignalFull/(rawData-rSer)


	# CalcSegmPoints
	dt = 1e-4
	cutStart = 100 # in ms
	cutEnd = 50 # in ms
	
	for i in range(numOfSegments):
		if len(arbSegmented[i]) < 1000:
			print(f"Segment {i} too short, skipping (less than 1000 points)")
			continue
		segLength = len(arbSegmented[i])/rLen * length
		rSegLen = len(rawSegmented[i])
		print(f"Segment {i} length: {segLength}")
		
		cutStartInPoint = scaleLength(segLength, rSegLen, cutStart)
		cutEndInPoint = scaleLength(segLength, rSegLen, segLength-cutEnd)
		
		cuttedSignal = rawSegmented[i][cutStartInPoint:cutEndInPoint]

		(f, S) = signal.periodogram(cuttedSignal, sampleRate, scaling='density')
		return f, S



#load_file("_old/test0_m500")
#load_file("_old/test1_seg")
f, S = load_file("_old/test2_0")