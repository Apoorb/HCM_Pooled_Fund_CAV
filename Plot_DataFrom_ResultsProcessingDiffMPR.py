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
from scipy.stats import t
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

def PlotData(ReadFileInfo1, VolTimeIntDat, Y_Var, Y_Lab, tittleAddOn,fileNm="",Y_StdDev="",CountCol="Count",
             range_y_ = [0,2], PlotMPR = ["0PerMPR","20PerMPR","40PerMPR","60PerMPR","80PerMPR","100PerMPR"]):
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
    if fileNm =="":
        fileNm = tittleAddOn
    Data = ReadData(ExcelFile1 = ReadFileInfo1["ExFi1"],SheetName = ReadFileInfo1["ShNm"],KeepColumns = ReadFileInfo1["KeepColumns"])
    Data1 = Data.reset_index()
    Data1 = Data1[Data1.PltSize.isin([1,5,8])] # Remove Platoon Size 1 and 2
    Data1.loc[Data1.PltSize==1,'Gap'] = 0.6
    Data1 = Data1[Data1.Gap.isin([0.6,1.1])]
    Data1.loc[:,'TimeInt'] = Data1.TimeInt.str.split("-",n=1,expand =True)[0].astype(int)
    Data1 = Data1.merge(VolTimeIntDat, left_on = "TimeInt",right_on ="IntStart", how= "left")
    if("Test100PerMPR" in PlotMPR):
        Data1 = Data1[~((Data1.MPR=="Test100PerMPR") & (Data1.TimeInt==300))]
        Data1.loc[Data1.MPR=="Test100PerMPR","Volume"] = 3000
        Data1 = Data1.groupby(['LaneDesc','Volume',"MPR"])[Y_Var].mean().reset_index()
    Data1 = Data1[Data1.Volume>=1600]
    # Data1 = Data1[Data1.Volume<= 2400]
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
    if Y_StdDev=="":
        fig = px.bar(Data1_EBT, x = "Volume (Veh/hr)", y = Y_Lab,color ="Scenario",facet_row ="PltSize" ,facet_col ="Gap" ,barmode="group", 
                     color_discrete_sequence = colorScale_Axb,template="plotly_white",range_y=range_y_
                     , title = "{}{}".format(tittleAddOn,"<br><i>Gap is not relevant for ACC (Platoon Size 1)</i>"))
    else:
        Data1_EBT.loc[:,"Tstat"] =  Data1_EBT.loc[:,CountCol].apply(lambda x:t.ppf(0.975,x))
        Data1_EBT.loc[:,"Error_Bar"] = Data1_EBT.loc[:,"Tstat"]* Data1_EBT.loc[:,Y_StdDev] / np.sqrt(Data1_EBT.loc[:,CountCol])
        fig = px.bar(Data1_EBT, x = "Volume (Veh/hr)", y = Y_Lab,color ="Scenario",facet_row ="PltSize" ,facet_col ="Gap" ,barmode="group", 
                  color_discrete_sequence = colorScale_Axb,template="plotly_white",range_y=range_y_,
                  title = "{}{}".format(tittleAddOn,"<br><i>Gap is not relevant for ACC (Platoon Size 1)</i>"),error_y="Error_Bar")
        fig.add_annotation(
            x=0.5,
            y=-0.18,
            text="Error Bars Show 95% CI based on t Distribution")
        fig.update_annotations(dict(
                    xref="paper",
                    yref="paper",
                    showarrow=False,
        ))
    fig.update_layout(showlegend=True)
    plot(fig, filename="{}.html".format(fileNm))
    return()
    

# Read the Data and Add Volume Info --- Startup-Loss
#****************************************************************************************************************************************
SheetNm = 'StartUplossDat'
ReadFileInfo = {
    "ExFi1" : x1,
    "ShNm" : SheetNm,
    "KeepColumns":  ["Avg_StartUpLoss","std_StartUpLoss","Count","Avg_Headway1st4Veh","std_Headway1st4Veh","Count_Headway1st4Veh",
                     "Avg_1st4Veh","std_1st4Veh","Count_1st4Veh","MPR","PltSize","Gap"]
    }
PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_StartUpLoss",
         Y_Lab ="Average StartUp<br> Loss Time (sec)",
         tittleAddOn ="Exclusive EBT Start-Up Loss Time",
         range_y_ = [0,2])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_StartUpLoss",
         Y_StdDev = "std_StartUpLoss",
         Y_Lab ="Average StartUp<br> Loss Time (sec)",
         tittleAddOn ="Exclusive EBT Start-Up Loss Time",
         fileNm= "Exclusive EBT Start-Up Loss Time with Error Bars",
         range_y_ = [0,2])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_Headway1st4Veh",
         Y_StdDev = "std_Headway1st4Veh",
         CountCol = "Count_Headway1st4Veh",
         Y_Lab ="Avg_Headway1st4Veh",
         tittleAddOn ="Avg_Headway1st4Veh",
         fileNm= "Headway_Headway1st4Veh",
         range_y_ = [0,10])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_1st4Veh",
         Y_StdDev = "std_1st4Veh",
         CountCol = "Count_1st4Veh",
         Y_Lab ="Avg_1st4Veh",
         tittleAddOn ="Avg_1st4Veh",
         fileNm= "Avg_1st4Veh",
         range_y_ = [0,5])

# Read the Data and Add Volume Info --- End-Loss
#****************************************************************************************************************************************
SheetNm = 'EndLossDat'
ReadFileInfo = {
    "ExFi1" : x1,
    "ShNm" : SheetNm,
    "KeepColumns":  ["Avg_Veh_Y_AR","std_Veh_Y_AR","Count_Veh_Y_AR","Avg_EndLossTime","std_EndLossTime","Count_ELT","MPR","PltSize","Gap"]
    }
PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_Veh_Y_AR",
         CountCol = "Count_Veh_Y_AR",
         Y_Lab ="Average Number<br> of Vehicles in Y+AR",
         tittleAddOn ="Exclusive EBT Vehicles Crossing in Y+AR",
         range_y_ = [0,2])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_EndLossTime",
         CountCol = "Count_ELT",
         Y_Lab ="Average End<br> Loss Time (sec)",
         tittleAddOn ="Exclusive EBT End Loss Time",
         range_y_ = [0,4])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_Veh_Y_AR",
         Y_StdDev = "std_Veh_Y_AR",
         CountCol = "Count_Veh_Y_AR",
         Y_Lab ="Average Number<br> of Vehicles in Y+AR",
         tittleAddOn ="Exclusive EBT Vehicles Crossing in Y+AR",
         fileNm= "Exclusive EBT Vehicles Crossing in Y+AR with Error Bars",
         range_y_ = [0,3])

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_EndLossTime",
         Y_StdDev = "std_EndLossTime",
         CountCol = "Count_ELT",
         Y_Lab ="Average End<br> Loss Time (sec)",
         tittleAddOn ="Exclusive EBT End Loss Time",
         fileNm = "Exclusive EBT End Loss Time with Error Bars",
         range_y_ = [0,4])

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
         Y_Lab ="Average<br> Headway (sec)",
         tittleAddOn ="Exclusive EBT Headway")

PlotData(ReadFileInfo1 = ReadFileInfo,
         VolTimeIntDat= VolTimeIntDat,
         Y_Var="Avg_headway",
         Y_StdDev = "std_headway",
         Y_Lab ="Average<br> Headway (sec)",
         tittleAddOn ="Exclusive EBT Headway with Error Bars")

# Test Data
#****************************************************************************************************************************************




