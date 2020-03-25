# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 15:04:57 2020
Purpose: Plot data obtained from Results Processing Different MPR
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
import numpy as np
from glob import glob

import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
#Using Plotly with Spyder
#https://community.plot.ly/t/plotly-for-spyder/10527/2
from plotly.offline import plot

os.chdir(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\Results')
os.getcwd()
MainDir = os.getcwd()

# Read once --- Takes time to load
VolTimeIntDat = pd.read_csv("VolumeTimeIntervalMap.csv")
x1 = pd.ExcelFile("Results_MPR_Plotting.xlsx")



def ReLab(x):
    MprLab = {
    "0PerMPR":"Base Case",
    "20PerMPR": "20% MPR",
    "40PerMPR": "40% MPR",
    "60PerMPR": "60% MPR",
    "80PerMPR": "80% MPR",
    "100PerMPR": "100% MPR",
    "Test100PerMPR": "100% MPR with 3000 veh/hr EB"
    }
    return(MprLab[x])



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

def PlotData(ReadFileInfo1, VolTimeIntDat, Y_Var, Y_Lab, tittleAddOn, PlotMPR = ["0PerMPR","20PerMPR","40PerMPR","60PerMPR","80PerMPR","100PerMPR"]):
    '''
    

    Parameters
    ----------
    ReadFileInfo1 : dict
        Dictionary with ExcelFile object, sheet name, and keep columns
    VolTimeIntDat : Pandas dataframe
        Mapping of time interval and volumes .
    Y_Var : str
        Y variable for the plot.
    Y_Lab : str
        Label that needs to be shown for Y variable.
    tittleAddOn : str
        Titile and output file name.
    PlotMPR : list, optional
        MPR levels for plotting. The default is ["0PerMPR","20PerMPR","40PerMPR","60PerMPR","80PerMPR","100PerMPR"].

    Returns
    -------
    None.

    '''
    Data = ReadData(ExcelFile1 = ReadFileInfo1["ExFi1"],SheetName = ReadFileInfo1["ShNm"],KeepColumns = ReadFileInfo1["KeepColumns"])
    Data1 = Data.reset_index()
    Data1 = Data1[Data1.Gap!= 1.2] # Remove Platoon Size 1 for now
    # Data1 = Data1[Data1.PltSize==5] # Remove Platoon Size 1 for now

    Data1.loc[:,'TimeInt'] = Data1.TimeInt.str.split("-",n=1,expand =True)[0].astype(int)
    Data1 = Data1.merge(VolTimeIntDat, left_on = "TimeInt",right_on ="IntStart", how= "left")
    if("Test100PerMPR" in PlotMPR):
        Data1 = Data1[~((Data1.MPR=="Test100PerMPR") & (Data1.TimeInt==300))]
        Data1.loc[Data1.MPR=="Test100PerMPR","Volume"] = 3000
        Data1 = Data1.groupby(['LaneDesc','Volume',"MPR"])[Y_Var].mean().reset_index()
    Data1 = Data1[Data1.Volume>1000]
    if(Y_Var == "Avg_StartUpLoss"):
        Data1 = Data1[Data1.Volume<= 2400]
    Data1.Volume = pd.Categorical(Data1.Volume)
    Data1.loc[:,Y_Var] =Data1.loc[:,Y_Var].round(2)
    Data1 = Data1[Data1.MPR.isin(PlotMPR)]
    # Correct MPR Labels
    Data1.loc[:,"MPR"] = Data1.MPR.apply(ReLab)
    
    Data1.rename(columns={Y_Var:Y_Lab, "Volume": "Volume (Veh/hr)","MPR":"Scenario"},inplace=True)
    Data1_EBT = Data1[Data1.LaneDesc =="EBT"]
    MprCats=["Base Case","20% MPR","40% MPR","60% MPR","80% MPR","100% MPR","100% MPR with 3000 veh/hr EB"]
    Data1_EBT.Scenario = pd.Categorical(Data1_EBT.Scenario, MprCats, ordered =True)
    Data1_EBT = Data1_EBT.sort_values(["Volume (Veh/hr)","Scenario"])
    colorScale_Axb = ['rgb(210,210,210)', 'rgb(180,180,180)','rgb(120,120,120)','rgb(100,100,100)','rgb(60,60,60)','rgb(20,20,20)','rgb(0,0,0)']
    # Plot the figure 
    fig = px.bar(Data1_EBT, x = "Volume (Veh/hr)", y = Y_Lab,color ="Scenario",facet_row ="PltSize" ,facet_col ="Gap" ,barmode="group", 
                 color_discrete_sequence = colorScale_Axb,template="plotly_white", title = "{}".format(tittleAddOn))
    plot(fig, filename="{}.html".format(tittleAddOn))
    return()
    

# Read the Data and Add Volume Info --- Startup-Loss
#****************************************************************************************************************************************
SheetNm = 'StartUplossDat'
ReadFileInfo = {
    "ExFi1" : x1,
    "ShNm" : SheetNm,
    "KeepColumns":  ["Avg_StartUpLoss","std_StartUpLoss","Count","MPR","PltSize","Gap"]
    }
PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_StartUpLoss",
         Y_Lab ="Average StartUp<br>Loss Time (sec)",
         tittleAddOn ="Exclusive EBT Start-Up Loss Time")

# Read the Data and Add Volume Info --- End-Loss
#****************************************************************************************************************************************
SheetNm = 'EndLossDat'
ReadFileInfo = {
    "ExFi1" : x1,
    "ShNm" : SheetNm,
    "KeepColumns":  ["Avg_Veh_Y_AR","std_Veh_Y_AR","Count","MPR","AvgHeadway","End Loss Time","PltSize","Gap"]
    }
PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_Veh_Y_AR",
         Y_Lab ="Average Number<br> of Vehicles in Y+AR",
         tittleAddOn ="Exclusive EBT Vehicles Crossing in Y+AR")

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="End Loss Time",
         Y_Lab ="Average End Loss<br> Time (sec)",
         tittleAddOn ="Exclusive EBT End Loss Time")

# Read the Data and Add Volume Info --- Follow-up-Headway
#****************************************************************************************************************************************
SheetNm = 'FollowUpLossDat'
ReadFileInfo = {
    "ExFi1" : x1,
    "ShNm" : SheetNm,
    "KeepColumns":  ["Avg_headway","std_headway","Count","MPR","PltSize","Gap"]
    }

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_headway",
         Y_Lab ="Average Headway (sec)",
         tittleAddOn ="Exclusive EBT Headway")

# Test Data
#****************************************************************************************************************************************




