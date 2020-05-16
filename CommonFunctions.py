# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 09:07:51 2019

@author: abibeka
Add all the functions here. Cleaner this way
"""

import pandas as pd
import numpy as np
from glob import glob
import os 
def RenamePhase(x):
    '''
    Rename a phase
    '''
    y= "Null"
    if(x=="green"):
        y="Red"  #if current phase is green then the previous phase was red
    elif (x=="amber"):
        y="green"
    elif (x=="red"):
        y = 'amber'
    else : ""
    return(y)



def ProcessSigTime(file, Phase5Check=True):
    '''
    Process signal data to get green start and end
    '''
    SigDat = pd.read_csv(file, delimiter =';',header=None,skiprows= 19)
    SigDat.drop(columns=[1,2,6,7,8],inplace=True)  # Drop junk columns
    SigDat.columns = ['SimSec','PhaseNum','NewState','DurOldState']
    #Keep only Phase 2 and 5.   
    #Keep Only New state of 'green' and 'amber' : green start and green end
    SigDat.loc[:,'OldState'] = SigDat.NewState.apply(lambda x: RenamePhase(x.strip()))
    SigDat.loc[:,'NewState'] = SigDat.NewState.str.strip()  # Create a column with new states
    SigDat = SigDat[SigDat.PhaseNum.isin([2,5])]
    SigDat = SigDat[SigDat.NewState.isin(['green','amber'])] # Drop the rows with Red as the new state. don't need
    # SigDat_Nw.head()
    #Add new labels of green start and green end
    SigDat  = SigDat[['SimSec','PhaseNum','NewState']]
    SigDat.loc[:,'GrStat'] = SigDat.NewState.apply(lambda x: 'G_st' if x=="green" else "G_end")
    SigDat.sort_values('SimSec',inplace=True)
    SigDat.reset_index(drop=True,inplace=True)
    Phase5Check = None
    if Phase5Check:
        NumPhases = 4
    else:
        NumPhases =2 
    np.ceil((SigDat.index.values+1) /NumPhases) #Cycle numbers if 1st row is kept. 
    #Denominator is 4 because we have 2 phases and 2 rows per phase (green start and End)
    np.ceil((SigDat.index.values) /NumPhases) #Cycle numbers if 1st row is deleted
    # Create Green Start, End Pairs : Call them CycNum
    if(SigDat.GrStat.values[0] == 'G_st'):
        SigDat.loc[:,'CycNum'] = np.ceil((SigDat.index.values+1) /NumPhases)
    else:
        SigDat.drop(index = 0,inplace =True) # We dropped index 0 but didn't reset index, so, index starts from 1
        SigDat.loc[:,'CycNum'] = np.ceil((SigDat.index.values) /NumPhases)
    SigDat.sort_values('SimSec',inplace=True)
    
    # Get start and end of phase 1 and 5 within each cycle
    SigDat_clean = pd.pivot_table(SigDat,values = 'SimSec',index=['CycNum','PhaseNum'],columns='GrStat').reset_index()
    CycleLenPh2 = SigDat_clean[SigDat_clean.PhaseNum==2][['G_st','G_end']].diff().mean(axis=0)
    CycleLenPh5 = SigDat_clean[SigDat_clean.PhaseNum==5][['G_st','G_end']].diff().mean(axis=0)
    CycleLenPh2 = CycleLenPh2.apply(np.ceil); CycleLenPh5 = CycleLenPh5.apply(np.ceil)
    assert((CycleLenPh2[0]==100) & (CycleLenPh2[1] ==100))
    if Phase5Check:
        assert((CycleLenPh5[0]==100) & (CycleLenPh5[1] ==100))
    SigDat_clean.sort_values(['G_st'],inplace=True)
    # SigDat_clean.head()
    # SigDat_clean.tail()
    return(SigDat_clean)
    
    

def ProcessDatCol(file ,LaneDict, skiprows1 = 11):
    '''
    Process data collection points
    '''
    DataColDat = pd.read_csv(file, delimiter =';',skiprows= skiprows1)
    DataColDat = DataColDat.iloc[:,0:-1]
    DataColDat.columns = ['Lane','t_Entry','t_Exit','VehNo','VehType','Del','V_mph','Acc_ftsec2','Del2','Del3','tQueue','VehLen_ft']
    DataColDat = DataColDat[['Lane','t_Entry','t_Exit','VehNo','VehType','V_mph','Acc_ftsec2','tQueue','VehLen_ft']]
    DataColDat_Sub = DataColDat[DataColDat.t_Entry!=-1]
    DataColDat_Sub = DataColDat_Sub[['Lane','t_Entry','tQueue','VehLen_ft','V_mph','Acc_ftsec2']]
    DataColDat_Sub.sort_values('t_Entry',inplace=True) 
    DataColDat_Sub.loc[:,'LaneDesc'] = DataColDat_Sub.Lane.apply(lambda x: LaneDict[x])
    return(DataColDat_Sub)
    
def MergeDatCol_SigDat(SigDat_clean, DataColDat_Sub ,LaneDict, StartVeh = 4, EndVeh =14, RunNum=99):
    '''
    Merge Signal and Data col 
    '''
    #Use pandas.merge_asof for merging t_Entry in data collection results to the nearest phase start time.
    #Similar to infimum ~ Greatest lower bound
    #https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.merge_asof.html
    #A “backward” search selects the last row in the right DataFrame whose ‘on’ key is less than or equal to the left’s key.
    CombData_Ln_Dict = {}
    for Ln in (LaneDict.keys()):
        CombData_Ln_Dict[Ln] = pd.merge_asof(DataColDat_Sub[DataColDat_Sub.Lane==Ln],SigDat_clean, left_on='t_Entry', right_on= 'G_st',direction = 'backward')
        #***********************Reactivate Later**********************************#
        #assert(max(CombData_Ln_Dict[Ln].t_Entry -CombData_Ln_Dict[Ln].G_st) < 50) #Make sure you don't merge vehs to a diff cycle
        
        # Check the vehicles that eneter the intersection during Amber Indication 
        CombData_Ln_Dict[Ln].loc[:,'VehinAmber'] = CombData_Ln_Dict[Ln].t_Entry > CombData_Ln_Dict[Ln].G_end
    CombData = pd.concat(CombData_Ln_Dict.values())
    # #Debug:
    # Ln =1
    # CombData_Ln_Dict[Ln].loc[:,"Debug"] = CombData_Ln_Dict[Ln].t_Entry -CombData_Ln_Dict[Ln].G_st
    # CombData = pd.concat(CombData_Ln_Dict.values())
    # Get the vehicle numbers
    CombData.sort_values(['CycNum','Lane'],inplace=True)
    # Get length of each group and then use arange 
    CombData.loc[:,'VehNum'] = np.hstack(CombData.groupby(['CycNum','Lane'])['t_Entry'].apply(lambda x: np.arange(1,len(x)+1)).values)
    CombData = CombData[['CycNum','Lane','LaneDesc','tQueue','t_Entry','G_st','G_end','VehNum','PhaseNum']]
    ###################         Define conditions for Sat Flow         ###########################################
    mask_SatFlow = (CombData.VehNum >= StartVeh) & (CombData.VehNum <= EndVeh) #Start vehicle is 4th (timeStamp for 4th vehicle is used for 5th vehicle)
    #mask_Headway = (CombData.VehNum >= StartVeh+1) & (CombData.VehNum <= EndVeh) # Start vehicle is 5th as we are directly getting the headway

    ## 
    CombData_SatFlow = CombData[mask_SatFlow]
    CombData_Headway = CombData.copy()
    CombData_Headway.loc[:,'Headway'] = CombData_Headway.groupby(['CycNum','Lane'])['t_Entry'].diff()
    # mask2 = CombData_Headway.Headway<=5
    # CombData_Headway = CombData_Headway[mask2]
    CombData_SatFlow = CombData_SatFlow.groupby(['CycNum','LaneDesc']).agg({'t_Entry':['min','max'],'VehNum':['min','max']})
    CombData_SatFlow.columns = ['_'.join(col).strip() for col in CombData_SatFlow.columns.values]
    CombData_SatFlow.loc[:,'AvgHeadway'] = (CombData_SatFlow.t_Entry_max - CombData_SatFlow.t_Entry_min)/(CombData_SatFlow.VehNum_max - CombData_SatFlow.VehNum_min)
    CombData_SatFlow.reset_index(drop = False, inplace =True)
    CombDataSum = CombData_SatFlow.groupby(['LaneDesc'])['AvgHeadway'].describe()
    CombDataSum.loc[:,'SatFlow'] = np.floor(3600/ CombDataSum['mean'])
    CombDataSum.loc[:,'RunNum'] = RunNum
    return(CombDataSum, CombData_SatFlow,CombData_Headway)
    

def MultiVISSIM_RunResProcess(CommonFileNmWithoutINPX, NewVol, FileDir1):
    os.chdir(FileDir1)
    # Get the Run # and the File
    #****************************************************************************************************************************
    SigFiles = glob(CommonFileNmWithoutINPX+ '*.lsa')
    map1 = lambda x: x.split('_')[-1].split('.')[0]
    SigFileNos = list(map(map1, SigFiles))
    SigFilesDict = dict(zip(SigFileNos, SigFiles))
    DatColFiles = glob(CommonFileNmWithoutINPX+ '*.mer')
    DatColNos = list(map(map1, DatColFiles))
    DatColFilesDict = dict(zip(DatColNos, DatColFiles))
    #****************************************************************************************************************************
    LaneDict = {1:'EBT/R', 2:'EBT', 3:"EBL"}
    ListRes = []
    SigDataDict = {}
    DataColDataDict = {}
    RawDataDict = {}
    RunNum = '001'
    SigVal = 'VissimBaseModel_Calibration_VolIs 2001 - V2_001.lsa'
    
    for RunNum,SigVal in SigFilesDict.items():
        print(RunNum,SigVal,DatColFilesDict[RunNum])
        SigDat = ProcessSigTime(SigVal) 
        SigDataDict[RunNum] = SigDat
        DatColDat = ProcessDatCol(DatColFilesDict[RunNum],LaneDict)
        DataColDataDict[RunNum] = DatColDat
        tempDat = MergeDatCol_SigDat(SigDat, DatColDat ,LaneDict, StartVeh = 4, EndVeh =14, RunNum = RunNum)
        ListRes.append(tempDat[0])
        RawDataDict[RunNum] = tempDat[1]
    #****************************************************************************************************************************
    FinDat = pd.concat(ListRes)
    FinDat = FinDat.sort_index()
    FinDat = FinDat.reset_index().set_index(['LaneDesc','RunNum']).sort_index()
    FinDat.loc[:,"StudyApproachVol"] = NewVol
    FinDatSatFlow = FinDat.groupby(['LaneDesc'])['SatFlow'].describe()
    FinDatSatFlow.loc[:,"StudyApproachVol"] = NewVol

    OutFi = "Results/VolumeIs{}_HeadwaySatFlowRes.xlsx".format(NewVol)
    writer=pd.ExcelWriter(OutFi)
    FinDat.to_excel(writer, 'HeadwaySatFlowSummary',na_rep='-')
    FinDatSatFlow.to_excel(writer, 'SatFlowByRun',na_rep='-')
    writer.save() 
        
    
    
