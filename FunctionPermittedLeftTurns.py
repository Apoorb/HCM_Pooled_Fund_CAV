# -*- coding: utf-8 -*-
"""
Created on Fri May  8 12:57:16 2020

@author: abibeka
"""

import pandas as pd
import numpy as np
import os
import re
import sys
from glob import glob
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
from CommonFunctions import ProcessSigTime
from CommonFunctions import ProcessDatCol
import plotly.express as px
import plotly.graph_objects as go
#Using Plotly with Spyder
#https://community.plot.ly/t/plotly-for-spyder/10527/2
from plotly.offline import plot

def BatchProcessFiles(SearchDirectory,VolumeMap):
    #List Files to Read
    #------------------------------------------------------------------------------------------
    SigFiles = glob(os.path.join(SearchDirectory,'*.lsa'))  # Get List of files 
    map1 = lambda x: x.split('_')[-1].split('.')[0]  
    SigFileNos = list(map(map1, SigFiles)) #Get Run Num
    SigFilesDict = dict(zip(SigFileNos, SigFiles)) #Mapping of file and run number
    fileSig = SigFiles[0] # Debug Code
    DatColFiles = glob(os.path.join(SearchDirectory,'*.mer')) # get list of files 
    DatColNos = list(map(map1, DatColFiles))
    DatColFilesDict = dict(zip(DatColNos, DatColFiles)) #Mapping of file and run number
    LaneDict = {1:'EBT/R', 2:'EBT', 3:"EBL",4:"WBT",5:"WBT"}
    fileDatCol = DatColFiles[0]
    FollowupHeadwayDat = pd.DataFrame()
    SneakerDat = pd.DataFrame()
    CapacityDat = pd.DataFrame()
    FollowUpDatList = []
    SneakerDatList= []
    CapacityList = []
    for RunNum,SigVal in SigFilesDict.items():
        # Read Signal Controller File
        fileSig = SigFilesDict[RunNum]
        SigDat = ProcessSigTime(fileSig, False) # Process .lsa files
        SigDat.loc[:,"Phase2Interval"] = pd.IntervalIndex.from_arrays(SigDat.G_st,SigDat.G_end+10) #Search in Phase 2 green
        #Read Data Collection File
        #------------------------------------------------------------------------------------------
        fileDatCol =    DatColFilesDict[RunNum]
        DatColDat = ProcessDatCol(fileDatCol,LaneDict,13)
        FollowUpDatList.append(GetFollowUpHeadway(DatColDat, SigDat,VolumeMap))
        SneakerDatList.append(GetTotalSneaker(DatColDat, SigDat,VolumeMap))
        CapacityList.append(GetCapacity(DatColDat, SigDat,VolumeMap))
    FollowupHeadwayDat = pd.concat(FollowUpDatList)
    FollowupHeadwayDat = FollowupHeadwayDat.groupby(['TimeIntevals'])['FollowUpHeadway'].mean().reset_index()
    SneakerDat = pd.concat(SneakerDatList)
    SneakerDat = SneakerDat.groupby(['TimeIntevals'])['NumSneakerPerCycle'].mean().reset_index()
    CapacityDat = pd.concat(CapacityList)
    CapacityDat = CapacityDat.groupby(['TimeIntevals'])['Capacity'].mean().reset_index()
    
    FinalDat = FollowupHeadwayDat.merge(SneakerDat,on="TimeIntevals",how="outer")
    FinalDat = FinalDat.merge(CapacityDat,on="TimeIntevals",how="outer")
    FinalDat = VolumeMap.merge(FinalDat,on="TimeIntevals",how="left")
    return(FinalDat)

def GetFollowUpHeadway(DatColDat, SigDat,VolumeMap):
    #Get WBT data to get headway is opposing through
    #------------------------------------------------------------------------------------------
    DatColDatWBT = DatColDat.query("LaneDesc=='WBT'")
    DatColDatWBT.sort_values('t_Entry',inplace=True)
    bins = DatColDatWBT.t_Entry.values #Define Headway bins
    uniqueBins, c = np.unique(bins, return_counts=True)
    DatColDatWBT.loc[:,"HeadwayBins"]= pd.cut(DatColDatWBT.t_Entry, uniqueBins,right=False,include_lowest=True).dropna()
    #Get EBL data
    #------------------------------------------------------------------------------------------
    DatColDatEBL = DatColDat.query("LaneDesc=='EBL'")
    HeadwayBins = pd.IntervalIndex(DatColDatWBT.HeadwayBins[~DatColDatWBT.HeadwayBins.duplicated()]).dropna()
    DatColDatEBL.loc[:,'HeadwayBins'] = pd.cut(DatColDatEBL.t_Entry, HeadwayBins) #Get EBL b/w WBT gaps
    DatColDatEBL.loc[:,"Phase2Interval"] =\
    pd.cut(DatColDatEBL.t_Entry.values,pd.IntervalIndex(SigDat.Phase2Interval)) #Get the phase 2 interval
    Issues = DatColDatEBL[DatColDatEBL.Phase2Interval.isna()] #Debug Code
    Issues.loc[:,"GapLen"] = Issues.HeadwayBins.apply(lambda x: x.length)
    if Issues.shape[0]!=0: assert(Issues.loc[:,"GapLen"].min() >35) #Really big gap---generally after the cycle has ended
    # Remove the rows where the vehicles crossed during cross street green
    DatColDatEBL = DatColDatEBL[~DatColDatEBL.Phase2Interval.isna()]
    #if (DatColDatEBL.HeadwayBins.isna()).any():
        #print("Issue at lines");print("*"*112); print(DatColDatEBL[DatColDatEBL.HeadwayBins.isna()])
    try:
        CheckDat = DatColDatEBL[DatColDatEBL.HeadwayBins.isna()]
        VehArrivalBeforePhaseEnd= CheckDat.Phase2Interval.apply(lambda x:x.right).astype('float')-CheckDat.t_Entry
        #assert((VehArrivalBeforePhaseEnd < 10).all()),"Check the data" 
    finally:
        DatColDatEBL = DatColDatEBL[~DatColDatEBL.HeadwayBins.isna()]
    #Get Follow-up Headway 
    #------------------------------------------------------------------------------------------
    DatColDatEBL.loc[:,'CycleNum'] = DatColDatEBL.groupby('Phase2Interval').ngroup().values
    DatColDatEBL.loc[:,'VehicleNum'] = DatColDatEBL.groupby('HeadwayBins').cumcount().values
    DatColDatEBL.loc[:,'t_EntryNxt'] = DatColDatEBL.groupby('HeadwayBins').t_Entry.shift(1).values
    #Need Follow-up Headway not GAp
    # DatColDatEBL = DatColDatEBL.eval('VehicleGapSub = (3600/5820)*VehLen_ft/V_mph') #Get the time for 0th vehicle crossing
    # DatColDatEBL.loc[:,'VehicleGapSub'] = DatColDatEBL.groupby('HeadwayBins').VehicleGapSub.shift(1).values # shift the above value by 1
    DatColDatEBL_FollowUp = DatColDatEBL.query('VehicleNum!=0') #Follow-up headway doesn't include 1st vehicle
    DatColDatEBL_FollowUp.insert(12,"GapLen",DatColDatEBL_FollowUp.HeadwayBins.apply(lambda x: x.length)) 
    DatColDatEBL_FollowUp = DatColDatEBL_FollowUp.eval("FollowUpHeadway=t_Entry - t_EntryNxt") 
    DatColDatEBL_FollowUp.loc[:,"TimeIntevals"] = pd.cut(DatColDatEBL_FollowUp.t_Entry.values,pd.IntervalIndex(VolumeMap.TimeIntevals.values)) #Get the follow-up gap by interval
    DatColDatEBL_FollowUp1 = DatColDatEBL_FollowUp.groupby(['TimeIntevals'])['FollowUpHeadway'].mean().reset_index()
    DatColDatEBL_FollowUp1 = DatColDatEBL_FollowUp1.merge(VolumeMap, left_on="TimeIntevals",right_on="TimeIntevals",how="outer")
    return(DatColDatEBL_FollowUp1)


def GetTotalSneaker(DatColDat, SigDat,VolumeMap):
    SigDat.loc[:,"Phase2ClearanceInterval"] = pd.IntervalIndex.from_arrays(SigDat.G_end,SigDat.G_end+15) 
    #Get clearance interval for phase 2. Should use +5 but I am using + 20 to get some sneakers in Vissim that are not getting
    #Captured with +5
    SigDatNumCycle= SigDat.copy()
    SigDatNumCycle.loc[:,"PhaseEnd"] = SigDat.G_end+5
    SigDatNumCycle.loc[:,"TimeInt"] = pd.cut(SigDatNumCycle.PhaseEnd.values,pd.IntervalIndex(VolumeMap.TimeIntevals.values)) #Get the follow-up gap by interval
    assert(SigDatNumCycle.groupby('TimeInt').PhaseEnd.count().mean() ==9)
    #Get EBL data
    #------------------------------------------------------------------------------------------
    DatColDatEBL = DatColDat.query("LaneDesc=='EBL'")
    DatColDatEBL.loc[:,"Phase2ClearanceInterval"] =\
    pd.cut(DatColDatEBL.t_Entry.values,pd.IntervalIndex(SigDat.Phase2ClearanceInterval)) #Get the phase 2 clearance interval interval
    # Remove the rows where the vehicles crossed during left green OR the cross street green
    DatColDatEBL = DatColDatEBL[~DatColDatEBL.Phase2ClearanceInterval.isna()]
    DatColDatEBL.loc[:,'CycleNum'] = DatColDatEBL.groupby('Phase2ClearanceInterval').ngroup().values
    DatColDatEBL.loc[:,"TimeIntevals"] = pd.cut(DatColDatEBL.t_Entry.values,pd.IntervalIndex(VolumeMap.TimeIntevals.values)) #Get the follow-up gap by interval
    DatColDatEBL = DatColDatEBL[~DatColDatEBL.TimeIntevals.isna()]
    DatColDatEBL.loc[:,"TempCol"] = DatColDatEBL.TimeIntevals.apply(lambda x: x.left).astype(str)
    DatColDatEBL_Sneaker = DatColDatEBL.groupby(['TempCol','CycleNum'])['LaneDesc']\
        .agg(['count']).rename(columns={'count':"NumSneakers"}).reset_index()
    DatColDatEBL_Sneaker = DatColDatEBL_Sneaker.groupby('TempCol').NumSneakers.sum().reset_index()
    VolumeMap.loc[:,"TempCol"] = VolumeMap.TimeIntevals.apply(lambda x: x.left).astype(str)
    DatColDatEBL_Sneaker = VolumeMap.merge(DatColDatEBL_Sneaker,on="TempCol",how="left")
    DatColDatEBL_Sneaker.drop(columns ="TempCol",inplace=True)
    CycleLen = 100
    AnalysisPeriod =900 #sec 
    DatColDatEBL_Sneaker.loc[:,"NumSneakerPerCycle"]=CycleLen* DatColDatEBL_Sneaker.NumSneakers/ AnalysisPeriod
    return(DatColDatEBL_Sneaker)


def GetCapacity(DatColDat, SigDat,VolumeMap):
    DatColDatEBL = DatColDat.query("LaneDesc=='EBL'")
    DatColDatEBL.loc[:,"TimeIntevals"] = pd.cut(DatColDatEBL.t_Entry.values,pd.IntervalIndex(VolumeMap.TimeIntevals.values)) #Get the follow-up gap by interval
    DatColDatEBL = DatColDatEBL[~DatColDatEBL.TimeIntevals.isna()]
    DatColDatEBL.loc[:,"TempCol"] = DatColDatEBL.TimeIntevals.apply(lambda x: x.left).astype(str)
    DatColDatEBL_Capacity = DatColDatEBL.groupby(['TempCol'])['LaneDesc']\
        .agg(['count']).rename(columns={'count':"Capacity"}).reset_index()
    VolumeMap.loc[:,"TempCol"] = VolumeMap.TimeIntevals.apply(lambda x: x.left).astype(str)
    DatColDatEBL_Capacity = VolumeMap.merge(DatColDatEBL_Capacity,on="TempCol",how="left")
    DatColDatEBL_Capacity.Capacity =  DatColDatEBL_Capacity.Capacity *4 
    DatColDatEBL_Capacity.drop(columns ="TempCol",inplace=True)
    return(DatColDatEBL_Capacity)

def ReadData(ExcelFile1, SheetName, KeepColumns):
    '''
    

    Parameters
    ----------
    ExcelFile1 : pd.ExcelFile for "Results_MPR_Plotting.xlsx"
        DESCRIPTION.
    SheetName : "StartUplossDat", "EndLossDat" or "FollowUpLossDat"
        DESCRIPTION.
    KeepColumns : Columns needed for plotting
        DESCRIPTION.

    Returns
    -------
    Pandas dataframe needed for plotting.

    '''
    Data = ExcelFile1.parse(SheetName,index_col=[0,1],header=[0,1])
    Data.columns = Data.columns.droplevel(0)
    Data.columns = KeepColumns
    return(Data)    

def ReadSatFlowData():
    # Get the Saturation flow rate by Scenario
    ############################################################################################################
    MainDir =r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\Results\Results Protected'
    # Read once --- Takes time to load
    x1 = pd.ExcelFile(os.path.join(MainDir,"Results_MPR_Plotting_Exp.xlsx"))
    ReadFileInfo3 = {
        "ExFi1" : x1,
        "ShNm" : "FollowUpLossDat",
        "KeepColumns":  ["Avg_headway","std_headway","Count","MPR","PltSize","Gap"]    }
    ThroughSatFlowDat = ReadData(ExcelFile1 = ReadFileInfo3["ExFi1"],SheetName = ReadFileInfo3["ShNm"],KeepColumns = ReadFileInfo3["KeepColumns"])
    ThroughSatFlowDat = ThroughSatFlowDat.reset_index()
    VolTimeIntDat = pd.read_csv(os.path.join(MainDir,"VolumeTimeIntervalMap.csv"))
    ThroughSatFlowDat.loc[:,'TimeInt'] = ThroughSatFlowDat.TimeInt.str.split("-",n=1,expand =True)[0].astype(int)
    ThroughSatFlowDat = ThroughSatFlowDat.merge(VolTimeIntDat, left_on = "TimeInt",right_on ="IntStart", how= "left")
    ThroughSatFlowDat = ThroughSatFlowDat[(ThroughSatFlowDat["Volume"]==2600) & (ThroughSatFlowDat["LaneDesc"]=="EBT")]
    ThroughSatFlowDat1 = ThroughSatFlowDat.groupby(['PltSize','Gap','MPR'])["Avg_headway"].mean().reset_index()
    # This sat flow doesn't match the figures- -- Rounding error
    ThroughSatFlowDat1.loc[:,"SatFlowRateOppThru"] = (3600/ThroughSatFlowDat1.Avg_headway).round(2)
    return(ThroughSatFlowDat1)

def ReLab_Gap(x):
    GapLab = {
    "0.6":"Aggressive",
    "Normal": "Normal",
    "1.1": "Conservative",
    "1.2":"Normal"}
    return(GapLab[x])

def ReLab(x):
    MprLab = {
    "0PerMPR":"0",
    "20PerMPR": "20",
    "40PerMPR": "40",
    "60PerMPR": "60",
    "80PerMPR": "80",
    "100PerMPR": "100"}
    return(MprLab[x])

def PlotData(Data1, Y_Var, Y_Lab,tittleAddOn,MainDir,fileNm="",range_y_ = [0,6]):
    Data1 = Data1.reset_index()
    Data1.Volumes = pd.Categorical(Data1.Volumes)
    Data1.loc[:,"MPR"] = Data1.MPR.apply(ReLab)
    Data1.loc[:,"Gap"] = Data1.Gap.apply(ReLab_Gap)
    Data1.rename(columns={Y_Var:Y_Lab, "Volumes": "Volume (Veh/hr)"},inplace=True)
    
    MprCats=["0","20","40","60","80","100"]
    GapCats = ['Aggressive','Normal','Conservative']
    Data1.MPR = pd.Categorical(Data1.MPR, MprCats, ordered =True)
    Data1.PltSize = pd.Categorical(Data1.PltSize,[1,5,8], ordered =True)
    Data1.Gap = pd.Categorical(Data1.Gap, GapCats, ordered =True)
    
    Data1 = Data1.sort_values(["Volume (Veh/hr)","MPR","PltSize","Gap"])
    colorScale_Axb = ['rgb(210,210,210)', 'rgb(180,180,180)','rgb(120,120,120)','rgb(100,100,100)','rgb(60,60,60)','rgb(20,20,20)','rgb(0,0,0)']
        
    Data1.rename(columns={Y_Var:Y_Lab, "MPR": "CAV Market Penetration Rate (%)","PltSize":"Platoon Size"},inplace=True)
    
    fig3 = px.scatter(Data1, x ="Volume (Veh/hr)", y = Y_Lab, color ="CAV Market Penetration Rate (%)",facet_col ="Gap" ,
                     facet_row="Platoon Size" ,symbol="CAV Market Penetration Rate (%)"
         ,template="plotly_white",range_y=range_y_
         , title = "{}".format(tittleAddOn))
    
    fig3.add_annotation(
        x=0.5,
        y=-0.18,
        text="<i>Note: Intra-Platoon Gap is not relevant for ACC mode (Platoon Size 1 and Platoon Leaders). Vehicles have a Desired Gap of 1.5 seconds in ACC mode</i>")
    fig3.update_annotations(dict(
                xref="paper",
                yref="paper",
                showarrow=False,))
    fig3.update_layout(showlegend=True)
    plot(fig3, filename=os.path.join(MainDir,"Plt_{}.html".format(fileNm)),auto_open=False)
    return()
    