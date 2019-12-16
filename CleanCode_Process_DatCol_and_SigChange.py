# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 08:59:32 2019
Purpose : Signal timing and data col
@author: abibeka
"""


#0.0 Housekeeping. Clear variable space
from IPython import get_ipython  #run magic commands
ipython = get_ipython()
ipython.magic("reset -f")
ipython = get_ipython()


# Load Libraries
import pandas as pd
import os
import sys
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
from CommonFunctions import ProcessSigTime
from CommonFunctions import ProcessDatCol
from CommonFunctions import MergeDatCol_SigDat

import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from glob import glob
import statsmodels.stats.api as sms
import statsmodels.stats.weightstats
from scipy.stats import sem, t
from scipy import mean

from scipy import stats
#os.chdir(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\VissimBaseModel')
os.chdir(r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel')
os.getcwd()

# Get the Run # and the File
#****************************************************************************************************************************
IsResForBase = False
if IsResForBase:
    SigFiles = glob('VissimBaseModel_Calibration-DefaultParam*.lsa')
else:
    SigFiles = glob('VissimBaseModel_Calibration - V2*.lsa')

map1 = lambda x: x.split('_')[-1].split('.')[0]
SigFileNos = list(map(map1, SigFiles))
SigFilesDict = dict(zip(SigFileNos, SigFiles))

if IsResForBase:
    DatColFiles = glob('VissimBaseModel_Calibration-DefaultParam*.mer')
else:
    DatColFiles = glob('VissimBaseModel_Calibration - V2_*.mer')


DatColNos = list(map(map1, DatColFiles))
DatColFilesDict = dict(zip(DatColNos, DatColFiles))

file = SigFiles[9]

file = DatColFiles[9]
#****************************************************************************************************************************
LaneDict = {1:'EBT/R', 2:'EBT', 3:"EBL"}
ListRes = []
SigDataDict = {}
DataColDataDict = {}
RawDataDict = {}
for RunNum,SigVal in SigFilesDict.items():
    print(RunNum,SigVal,DatColFilesDict[RunNum])
    SigDat = ProcessSigTime(SigVal) 
    SigDataDict[RunNum] = SigDat
    DatColDat = ProcessDatCol(DatColFilesDict[RunNum],LaneDict)
    DataColDataDict[RunNum] = DatColDat
    tempDat = MergeDatCol_SigDat(SigDat, DatColDat ,LaneDict, StartVeh = 5, EndVeh =14, RunNum = RunNum)
    ListRes.append(tempDat[0])
    RawDataDict[RunNum] = tempDat[1]
    
    
#****************************************************************************************************************************
FinDat = pd.concat(ListRes)
FinDat = FinDat.sort_index()
FinDat = FinDat.reset_index().set_index(['LaneDesc','RunNum']).sort_index()
FinDat.columns
FinDatSatFlow = FinDat.groupby(['LaneDesc'])['SatFlow'].describe()

# Get a list of sat flow rates
VISSIM_Val = FinDatSatFlow.loc['EBT','mean']
Target_Val = 1900
SatFlowVals = np.array(FinDat.loc['EBT','SatFlow'].values)

# Statistical Testing
sms.DescrStatsW(SatFlowVals).tconfint_mean()
stats.ttest_1samp(SatFlowVals, 1900 )

# Output data
if IsResForBase:
    OutFi = "Results/Base_HeadwaySatFlowRes.xlsx"
else:
    OutFi = "Results/Calib_HeadwaySatFlowRes.xlsx"


writer=pd.ExcelWriter(OutFi)
FinDat.to_excel(writer, 'HeadwaySatFlowSummary',na_rep='-')
FinDatSatFlow.to_excel(writer, 'SatFlowByRun',na_rep='-')

writer.save() #****************************************************************************************************************************


