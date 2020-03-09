# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:18:50 2020
Purpose: Process the results from different scenarios 
@author: abibeka
"""


#0.0 Housekeeping. Clear variable space
from IPython import get_ipython  #run magic commands
ipython = get_ipython()
ipython.magic("reset -f")
ipython = get_ipython()


# Load Libraries
#****************************************************************************************************************************************
import pandas as pd
import os
import sys
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
from CommonFunctions import ProcessSigTime
from CommonFunctions import ProcessDatCol
from CommonFunctions import MergeDatCol_SigDat
import numpy as np
from glob import glob
import subprocess
#os.chdir(r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel')
os.chdir(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModels')
os.getcwd()
MainDir = os.getcwd()


# Get the Run # and the File
#****************************************************************************************************************************
MPR_Suffixes = ["0PerMPR","20PerMPR","40PerMPR","80PerMPR","100PerMPR"]
# MPR_Suffixes = ["0PerMPR","100PerMPR"]
MPR_Level =  "100PerMPR"

# SigDat_clean =SigDat; DataColDat_Sub= DatColDat; StartVeh = 0; EndVeh =14; RunNum = "002"


def GetPerformanceMeasures(MPR_Level):
    SigFiles = glob('ArtBaseNet_{}*.lsa'.format(MPR_Level))
    map1 = lambda x: x.split('_')[-1].split('.')[0]
    SigFileNos = list(map(map1, SigFiles))
    SigFilesDict = dict(zip(SigFileNos, SigFiles))
    DatColFiles = glob('ArtBaseNet_{}*.mer'.format(MPR_Level))
    DatColNos = list(map(map1, DatColFiles))
    DatColFilesDict = dict(zip(DatColNos, DatColFiles))
    file = SigFiles[1]
    file = DatColFiles[1]
    #Debug:
    SigVal = SigFiles[1]
    RunNum = '002'
    #Get the Raw data for getting Start-up loss time, follow-up headway and End loss time
    #****************************************************************************************************************************
    LaneDict = {1:'EBT/R', 2:'EBT', 3:"EBL"}
    ListRes = []
    SigDataDict = {}
    DataColDataDict = {}
    RawDataDict = {}
    RawDataDict2 = {}
    for RunNum,SigVal in SigFilesDict.items():
        print(RunNum,SigVal,DatColFilesDict[RunNum])
        SigDat = ProcessSigTime(SigVal) 
        SigDataDict[RunNum] = SigDat
        DatColDat = ProcessDatCol(DatColFilesDict[RunNum],LaneDict)
        DataColDataDict[RunNum] = DatColDat
        tempDat = MergeDatCol_SigDat(SigDat, DatColDat ,LaneDict, StartVeh = 0, EndVeh =14, RunNum = RunNum)
        ListRes.append(tempDat[0])
        RawDataDict[RunNum] = tempDat[1]
        RawDataDict2[RunNum] = tempDat[2]
        RawDataDict[RunNum].loc[:,"RunNo"] = RunNum
        RawDataDict2[RunNum].loc[:,"RunNo"] = RunNum
    RawDat= pd.concat(RawDataDict.values())
    RawDat2= pd.concat(RawDataDict2.values())
    RawDat2.loc[:,'MPR_Level'] = MPR_Level
    StartUplossDat= StartUpLostTimeFun(RawDat2,MPR_Level)
    FollowUpLossDat, NumDataLoss= FollowUpHeadwayFun(RawDat2,MPR_Level)
    EndLossDat= EndLossTimeFun(RawDat2,MPR_Level,FollowUpLossDat.copy())
    Dat_dataLoss = pd.DataFrame({"MPR_Level":[MPR_Level],"NumRowsRemovedByTQueue":[NumDataLoss]})
    ReturnDatDict ={
        'RawData': RawDat2,
        'StartUplossDat':StartUplossDat,
        'EndLossDat':EndLossDat,
        'FollowUpLossDat':FollowUpLossDat,
        'Dat_dataLoss':Dat_dataLoss
        }
    return(ReturnDatDict)

    
#Start Up  loss time 
#****************************************************************************************************************************
def StartUpLostTimeFun(Data,MPR_Level):
   
    StartUpLossTmDat = Data.groupby(['RunNo','Lane','LaneDesc','CycNum'])[['t_Entry','G_st']].min()
    StartUpLossTmDat.loc[:,'StartUpLossTm'] = StartUpLossTmDat.t_Entry - StartUpLossTmDat.G_st
    StartUpLossTmDat.loc[:,'StartUpLossTm'].describe()
    StartUpLossTmDat = StartUpLossTmDat[StartUpLossTmDat.StartUpLossTm<2.5] #Remove outrageously large values
    cut_bins = list(range(300,12000,900))
    labels = ["{}-{}".format(i,i+900) for i in cut_bins[:-1]]
    StartUpLossTmDat.loc[:,'TimeInt'] = pd.cut(StartUpLossTmDat.t_Entry,bins=cut_bins,labels=labels)
    StartUpLossTmDat= StartUpLossTmDat.groupby(['LaneDesc','TimeInt']).agg({'StartUpLossTm':['mean','std','count']})
    StartUpLossTmDat.loc[:,'MPR_Level'] = MPR_Level
    return(StartUpLossTmDat)
#End Loss Time
#****************************************************************************************************************************
def EndLossTimeFun(Data,MPR_Level,HeadwayDat):
    '''
    Data: Raw Data
    MPR_Level : MPR
    HeadwayDat: Average headway data
    '''
    Mask = ((Data.t_Entry - Data.G_end)>0)
    EndLossTime = Data[Mask]
    EndLossTime = EndLossTime.groupby(['RunNo','Lane','LaneDesc','CycNum']).agg({"t_Entry":["count","first"]})
    EndLossTime.columns = ["NumVehInAmber_AllRed","t_Entry"]
    EndLossTime.loc[:,"NumVehInAmber_AllRed"].describe()
    np.percentile(EndLossTime.loc[:,"NumVehInAmber_AllRed"],95)
    cut_bins = list(range(300,12000,900))
    labels = ["{}-{}".format(i,i+900) for i in cut_bins[:-1]]
    EndLossTime.loc[:,'TimeInt'] = pd.cut(EndLossTime.t_Entry,bins=cut_bins,labels=labels)
    EndLossTime = EndLossTime.groupby(['LaneDesc','TimeInt']).agg({'NumVehInAmber_AllRed':['mean','std','count']})
    EndLossTime.loc[:,'MPR_Level'] = MPR_Level
    #Get the End Loss Time
    HeadwayDat.drop(columns ="MPR_Level",inplace=True)
    HeadwayDat.columns = HeadwayDat.columns.droplevel(0)
    HeadwayDat.rename(columns ={"mean":"AvgHeadway"},inplace=True)
    HeadwayDat.drop(columns = ["std","count"],inplace=True)
    EndLossTime = EndLossTime.merge(HeadwayDat,left_index=True,right_index=True,how="left")
    Y_AR = 5 # seconds
    EndLossTime.rename(columns = {"AvgHeadway":("AvgHeadway","")},inplace=True)
    EndLossTime.columns = pd.MultiIndex.from_tuples(EndLossTime.columns, names = [None,None])
    idx=pd.IndexSlice
    EndLossTime.loc[:,"EndLossTime"] = Y_AR - EndLossTime.AvgHeadway *EndLossTime.loc[:,idx["NumVehInAmber_AllRed","mean"]]
    return(EndLossTime)

#Follow Up Headway
#***************************************************************************************************************************
def FollowUpHeadwayFun(Data,MPR_Level):
    HeadwayDat = Data[Data.VehNum>=5] # This would be 5 becuase we are using headway. Not the difference of t_Entry min and max
    Debug = HeadwayDat[HeadwayDat.tQueue< 30]
    NumDataLossDuetoTQueue30 = Debug.shape[0]
    cut_bins = list(range(300,12000,900))
    labels = ["{}-{}".format(i,i+900) for i in cut_bins[:-1]]
    HeadwayDat.loc[:,'TimeInt'] = pd.cut(HeadwayDat.t_Entry,bins=cut_bins,labels=labels)
    HeadwayDat = HeadwayDat.groupby(['LaneDesc','TimeInt']).agg({'Headway':['mean','std','count']})
    HeadwayDat.loc[:,'MPR_Level'] = MPR_Level
    return(HeadwayDat,NumDataLossDuetoTQueue30)    


# MPR_Suffixes = ["0PerMPR","100PerMPR"]
MPR_Suffixes = ["0PerMPR","20PerMPR","40PerMPR","80PerMPR","100PerMPR"]

ReturnDatDict ={
    'RawData': pd.DataFrame(),
    'StartUplossDat':pd.DataFrame(),
    'EndLossDat':pd.DataFrame(),
    'FollowUpLossDat':pd.DataFrame(),
    'Dat_dataLoss': pd.DataFrame()
    }
    
for MPR in MPR_Suffixes:
    OutFi = ""
    ResDict= GetPerformanceMeasures(MPR)
    for key,value in ResDict.items():
        ReturnDatDict[key] = pd.concat([ReturnDatDict[key],value])




os.chdir("../Results")
os.getcwd()
OutFi = "Results_MPR.xlsx"
OutFi_plot = "Results_MPR_Plotting.xlsx"
writer = pd.ExcelWriter(OutFi)
writer_plot = pd.ExcelWriter(OutFi_plot)
for key,value in ReturnDatDict.items(): 
    value.to_excel(writer_plot,key,index=True)
    if (not ((key=="RawData") | (key=="Dat_dataLoss"))):
        dat =value.copy()
        ColNames = ['_'.join(col) if col[1]!="" else col[0] for col in dat.columns]
        dat.columns =ColNames
        dat = dat.reset_index().set_index(['LaneDesc','TimeInt','MPR_Level']).unstack()
        dat = dat.swaplevel(i=0,j=1,axis=1)
        dat.sort_index(axis=1, inplace=True)
        dat.to_excel(writer,key,index=True)
    else:
        value.to_excel(writer,key,index=True)
writer.save()
writer_plot.save()
subprocess.Popen([OutFi_plot],shell=True)  