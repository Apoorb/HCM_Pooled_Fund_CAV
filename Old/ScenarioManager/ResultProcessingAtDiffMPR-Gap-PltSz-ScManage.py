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
os.chdir(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModels\5\0.7')

os.getcwd()
MainDir = os.getcwd()


# Get the Run # and the File
#****************************************************************************************************************************
MPR_Suffixes = ["0PerMPR","20PerMPR","40PerMPR","80PerMPR","100PerMPR"]
# MPR_Suffixes = ["0PerMPR","100PerMPR"]
MPR_Level =  "100PerMPR"
Gap= 0.7
PltSize = 5
# SigDat_clean =SigDat; DataColDat_Sub= DatColDat; StartVeh = 5; EndVeh =14; RunNum = "002"

def GetPerformanceMeasures(MPR_Level, Gap= 0.7, PltSize = 5):
    SigFiles = glob('*.lsa'.format(PltSize, Gap, MPR_Level))
    map1 = lambda x: x.split('_')[-1].split('.')[0]
    SigFileNos = list(map(map1, SigFiles))
    SigFilesDict = dict(zip(SigFileNos, SigFiles))
    DatColFiles = glob('*.mer'.format(PltSize, Gap, MPR_Level))
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
        tempDat = MergeDatCol_SigDat(SigDat, DatColDat ,LaneDict, StartVeh = 4, EndVeh =14, RunNum = RunNum)
        ListRes.append(tempDat[0])
        RawDataDict[RunNum] = tempDat[1]
        RawDataDict2[RunNum] = tempDat[2]
        RawDataDict[RunNum].loc[:,"RunNo"] = RunNum
        RawDataDict2[RunNum].loc[:,"RunNo"] = RunNum
    RawDat= pd.concat(RawDataDict.values())
    RawDat2= pd.concat(RawDataDict2.values())
    RawDat2.loc[:,'MPR_Level'] = MPR_Level
    FollowUpLossDat, NumDataLoss= FollowUpHeadwayFun(RawDat2,MPR_Level)
    StartUplossDat= StartUpLostTimeFun(RawDat2,MPR_Level, FollowUpLossDat.copy())
    
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
# Data = RawDat2
# HeadwayDat = FollowUpLossDat.copy()
#****************************************************************************************************************************
def StartUpLostTimeFun(Data ,MPR_Level,HeadwayDat):
    StartUpLossTmDat = Data.copy()
    StartUpLossTmDat.loc[StartUpLossTmDat.VehNum==1,"Headway"] = StartUpLossTmDat.loc[StartUpLossTmDat.VehNum==1,"t_Entry"]-StartUpLossTmDat.loc[StartUpLossTmDat.VehNum==1,"G_st"]
    StartUpLossTmDat = StartUpLossTmDat[StartUpLossTmDat.VehNum<=4] # Only use the 1st 4 vehicles
    StartUpLossTmDat = StartUpLossTmDat.groupby(['RunNo','Lane','LaneDesc','CycNum']).agg({"Headway":["sum","count"],"t_Entry":"min"})
    StartUpLossTmDat.columns = ["Headway1st4Veh","NumVeh","t_Entry"]
    HeadwayDat = HeadwayDat.reset_index()
    HeadwayDat.columns = [' '.join(col).strip() for col in HeadwayDat.columns.values]
    # HeadwayDat = HeadwayDat[HeadwayDat.TimeInt!="300-1200"]
    HeadwayDat = HeadwayDat.groupby(["LaneDesc","TimeInt"])["Headway mean"].mean().reset_index()
    StartUpLossTmDat.reset_index(inplace=True)
    cut_bins = list(range(300,12000,900))
    labels = ["{}-{}".format(i,i+900) for i in cut_bins[:-1]]
    StartUpLossTmDat.loc[:,'TimeInt'] = pd.cut(StartUpLossTmDat.t_Entry,bins=cut_bins,labels=labels)
    
    StartUpLossTmDat = StartUpLossTmDat.merge(HeadwayDat,on=["LaneDesc",'TimeInt'],how= "left")
    StartUpLossTmDat.loc[:,"StartUpLossTm"] = StartUpLossTmDat.Headway1st4Veh - StartUpLossTmDat["Headway mean"] * StartUpLossTmDat.NumVeh
    
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
    HeadwayDat = Data[(Data.VehNum>=5)] # This would be 5 becuase we are using headway. Not the difference of t_Entry min and max
    Debug = HeadwayDat[HeadwayDat.tQueue< 30]
    NumDataLossDuetoTQueue30 = Debug.shape[0]
    HeadwayDat = HeadwayDat[(HeadwayDat.tQueue>=30)]
    cut_bins = list(range(300,12000,900))
    labels = ["{}-{}".format(i,i+900) for i in cut_bins[:-1]]
    HeadwayDat.loc[:,'TimeInt'] = pd.cut(HeadwayDat.t_Entry,bins=cut_bins,labels=labels)
    HeadwayDat = HeadwayDat.groupby(['LaneDesc','TimeInt']).agg({'Headway':['mean','std','count']})
    HeadwayDat.loc[:,'MPR_Level'] = MPR_Level
    return(HeadwayDat,NumDataLossDuetoTQueue30)    


# MPR_Suffixes = ["0PerMPR","100PerMPR"]
MPR_to_Scenario ={
 "0PerMPR":'S000001',
 "20PerMPR":'S000002',
 "40PerMPR":'S000003',
 "60PerMPR":'S000004',
 "80PerMPR":'S000005',
 "100PerMPR":'S000006'
 }


ReturnDatDict ={
    'RawData': pd.DataFrame(),
    'StartUplossDat':pd.DataFrame(),
    'EndLossDat':pd.DataFrame(),
    'FollowUpLossDat':pd.DataFrame(),
    'Dat_dataLoss': pd.DataFrame()
    }
    
Gaps = [0.6, 0.7, 1.1]
PlatoonSizes = [1,2,5]
PltSz_l = PltSz =1
Gap_l= Gap =  1.2

Gaps = [1.2]
PlatoonSizes = [1]
MPR_Lab, VissimSenFolder = list(MPR_to_Scenario.keys())[0], list(MPR_to_Scenario.values())[0]


OuterDir = r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModelScManager'
for PltSz_l in PlatoonSizes:
    for Gap_l in Gaps:
        if (PltSz_l== 1) & (Gap_l in [0.7,1.1]):
            continue
        elif PltSz_l== 1:
            Gap_l = 1.2
        else: ""
        NewLoc = os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l),"Scenarios")
        os.chdir(NewLoc)
        for MPR_Lab, VissimSenFolder in MPR_to_Scenario.items():
            os.chdir(VissimSenFolder)
            os.getcwd()
            OutFi = ""
            ResDict= GetPerformanceMeasures(MPR_Lab,Gap= Gap_l, PltSize = PltSz_l)
            for key,value in ResDict.items():
                value.loc[:,'PltSize'] = PltSz_l
                value.loc[:,'Gap'] = Gap_l
                ReturnDatDict[key] = pd.concat([ReturnDatDict[key],value])


os.chdir(OuterDir)
try:
      os.mkdir("../Results")
except:
    print("Dir creation error")
os.chdir("../Results")
os.getcwd()
OutFi = "Results_MPR.xlsx"
WantResMPR = False
OutFi_plot = "Results_MPR_Plotting.xlsx"
writer = pd.ExcelWriter(OutFi)
writer_plot = pd.ExcelWriter(OutFi_plot)
for key,value in ReturnDatDict.items(): 
    if key!= "RawData":
        value.to_excel(writer_plot,key,index=True)
    if WantResMPR:
        if (not ((key=="RawData") | (key=="Dat_dataLoss"))):
            dat =value.copy()
            ColNames = ['_'.join(col) if col[1]!="" else col[0] for col in dat.columns]
            dat.columns =ColNames
            dat = dat.reset_index().set_index(['LaneDesc','TimeInt','PltSize','Gap','MPR_Level']).unstack()
            dat = dat.swaplevel(i=0,j=1,axis=1)
            dat.sort_index(axis=1, inplace=True)
            dat.to_excel(writer,key,index=True)
        else:
            value.to_excel(writer,key,index=True)
if WantResMPR: writer.save()
writer_plot.save()
subprocess.Popen([OutFi_plot],shell=True)  