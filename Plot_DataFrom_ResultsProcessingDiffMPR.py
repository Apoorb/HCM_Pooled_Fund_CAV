# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 15:04:57 2020
Purpose: Plot data obtained from Results Processing Different MPR
@author: abibeka
"""


#0.0 Housekeeping. Clear variable space
# from IPython import get_ipython  #run magic commands
# ipython = get_ipython()
# ipython.magic("reset -f")
# ipython = get_ipython()

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
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
#Using Plotly with Spyder
#https://community.plot.ly/t/plotly-for-spyder/10527/2
from plotly.offline import plot

#os.chdir(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\Results')
#os.getcwd()
MainDir =r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\Results\Results Protected'

# Read once --- Takes time to load
VolTimeIntDat = pd.read_csv(os.path.join(MainDir,"VolumeTimeIntervalMap.csv"))
x1 = pd.ExcelFile(os.path.join(MainDir,"Results_MPR_Plotting_Exp.xlsx"))



def ReLab(x):
    MprLab = {
    "0PerMPR":"0",
    "20PerMPR": "20",
    "40PerMPR": "40",
    "60PerMPR": "60",
    "80PerMPR": "80",
    "100PerMPR": "100"}
    return(MprLab[x])

def ReLab_Gap(x):
    GapLab = {
    0.6:"Aggressive",
    "Normal": "Normal",
    1.1: "Conservative"}
    return(GapLab[x])

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

def PlotData(ReadFileInfo1, VolTimeIntDat, Y_Var, Y_Lab,tittleAddOn,direction="EBT",fileNm="",Y_StdDev="",CountCol="Count",
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
    Y_StdDev: float
        Std deviation for CI
    CountCol: Int
        Count for CI
    direction: str
        Direction = "EBT" or "EBL"
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
    tempDat = Data1.loc[Data1.PltSize==1]
    tempDat.loc[:,'Gap'] = 1.1
    tempDat2 = Data1.loc[Data1.PltSize==1]
    tempDat2.loc[:,'Gap'] = "Normal"
    Data1 = pd.concat([Data1,tempDat,tempDat2])
    
    Data1 = Data1[Data1.Gap.isin(['Normal',0.6,1.1])]
    Data1.loc[:,'TimeInt'] = Data1.TimeInt.str.split("-",n=1,expand =True)[0].astype(int)
    Data1 = Data1.merge(VolTimeIntDat, left_on = "TimeInt",right_on ="IntStart", how= "left")
    Data1 = Data1[Data1.Volume>=1600]
    # Data1 = Data1[Data1.Volume<= 2400]
    Data1.Volume = pd.Categorical(Data1.Volume)
    #Data1.loc[:,Y_Var] =Data1.loc[:,Y_Var].round(2)
    Data1 = Data1[Data1.MPR.isin(PlotMPR)]
    # Correct MPR Labels
    Data1.loc[:,"MPR"] = Data1.MPR.apply(ReLab)
    Data1.loc[:,"Gap"] = Data1.Gap.apply(ReLab_Gap)
    Data1.rename(columns={Y_Var:Y_Lab, "Volume": "Volume (Veh/hr)"},inplace=True)
    
    Data1_PLot = Data1[Data1.LaneDesc == direction]
    MprCats=["0","20","40","60","80","100"]
    GapCats = ['Aggressive','Normal','Conservative']
    Data1_PLot.MPR = pd.Categorical(Data1_PLot.MPR, MprCats, ordered =True)
    Data1_PLot.PltSize = pd.Categorical(Data1_PLot.PltSize,[1,5,8], ordered =True)
    Data1_PLot.Gap = pd.Categorical(Data1_PLot.Gap, GapCats, ordered =True)
    
    Data1_PLot = Data1_PLot.sort_values(["Volume (Veh/hr)","MPR","PltSize","Gap"])
    colorScale_Axb = ['rgb(210,210,210)', 'rgb(180,180,180)','rgb(120,120,120)','rgb(100,100,100)','rgb(60,60,60)','rgb(20,20,20)','rgb(0,0,0)']
    
    
    Data1_PLot.loc[:,"Tstat"] =  Data1_PLot.loc[:,CountCol].apply(lambda x:t.ppf(0.975,x))
    Data1_PLot.loc[:,"Error_Bar"] = Data1_PLot.loc[:,"Tstat"]* Data1_PLot.loc[:,Y_StdDev] / np.sqrt(Data1_PLot.loc[:,CountCol])
    Data1_PLot.rename(columns={Y_Var:Y_Lab, "MPR": "CAV Market Penetration Rate (%)","PltSize":"Platoon Size"},inplace=True)
    Data1_PLot_1 = Data1_PLot[Data1_PLot["Volume (Veh/hr)"]==2600]


    # Plot the figure 
    fig = px.bar(Data1_PLot, x = "Volume (Veh/hr)", y = Y_Lab,color ="CAV Market Penetration Rate (%)",facet_row ="Platoon Size" ,facet_col ="Gap" ,barmode="group", 
                 color_discrete_sequence = colorScale_Axb,template="plotly_white",range_y=range_y_
                 , title = "{}{}".format(tittleAddOn,"<br><i>Gap is not relevant for ACC (Platoon Size 1)</i>"))
    #
    fig.update_layout(showlegend=True)
    plot(fig, filename=os.path.join(MainDir,"Plots/{}.html".format(fileNm)),auto_open=False)
    
    fig2 = px.bar(Data1_PLot, x = "Volume (Veh/hr)", y = Y_Lab,color ="CAV Market Penetration Rate (%)",facet_row ="Platoon Size" ,facet_col ="Gap" ,barmode="group", 
              color_discrete_sequence = colorScale_Axb,template="plotly_white",range_y=range_y_,
              title = "{}{}".format(tittleAddOn,"<br><i>Gap is not relevant for ACC (Platoon Size 1)</i>"),error_y="Error_Bar")
    fig2.add_annotation(
        x=0.5,
        y=-0.18,
        text="Error Bars Show 95% CI based on t Distribution")
    fig2.update_annotations(dict(
                xref="paper",
                yref="paper",
                showarrow=False,
    ))
    fig2.update_layout(showlegend=True)
    plot(fig2, filename=os.path.join(MainDir,"Plots/DebugPlots/{} with Error Bars.html").format(fileNm),auto_open=False)
    if(Y_Var=="Avg_headway"):
        Data1_PLot_1.loc[:,"Saturation Flow Rate (pcu/hr/ln)"] = 3600/Data1_PLot_1.loc[:,Y_Lab]
        Y_Lab = "Saturation Flow Rate (pcu/hr/ln)"
        fileNm= fileNm.replace("Headway","SatFlow")
        tittleAddOn = tittleAddOn.replace("Headway","Saturation Flow Rate")
        range_y_ = [1400,3200]
    Y_Lab2 = Y_Lab
    Y_Lab2 = Y_Lab2.replace("<br>","")
    Data1_PLot_1.rename(columns = {Y_Lab:Y_Lab2,"Gap":"Intra-Platoon Gap"},inplace=True)
    
    fig3 = px.scatter(Data1_PLot_1, x = "CAV Market Penetration Rate (%)", y = Y_Lab2, color ="Platoon Size",facet_col ="Intra-Platoon Gap" ,
                      symbol="Platoon Size", symbol_map={0.6:"circle","Normal":"diamonds",1.1:"x"}
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
    plot(fig3, filename=os.path.join(MainDir,"Plots/Scatter/Plt_{}.html".format(fileNm)),auto_open=False)

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

# PlotData(ReadFileInfo1 = ReadFileInfo,
#          VolTimeIntDat= VolTimeIntDat,
#          Y_Var="Avg_1st4Veh",
#          Y_StdDev = "std_1st4Veh",
#          CountCol = "Count_1st4Veh",
#          Y_Lab ="Avg_1st4Veh",
#          tittleAddOn ="Avg_1st4Veh",
#          fileNm= "Avg_1st4Veh",
#          range_y_ = [0,5])

#****************************************************************************************************************************************
# Read the Data and Add Volume Info ---  Startup-Loss, End-Loss, Follow-up-Headway
#****************************************************************************************************************************************
ReadFileInfo1 = {
    "ExFi1" : x1,
    "ShNm" : "StartUplossDat",
    "KeepColumns":  ["Avg_StartUpLoss","std_StartUpLoss","Count","Avg_Headway1st4Veh","std_Headway1st4Veh","Count_Headway1st4Veh",
                     "Avg_1st4Veh","std_1st4Veh","Count_1st4Veh","MPR","PltSize","Gap"]    }
ReadFileInfo2 = {
    "ExFi1" : x1,
    "ShNm" : "EndLossDat",
    "KeepColumns":  ["Avg_Veh_Y_AR","std_Veh_Y_AR","Count_Veh_Y_AR","Avg_EndLossTime","std_EndLossTime","Count_ELT","MPR","PltSize","Gap"]    }
ReadFileInfo3 = {
    "ExFi1" : x1,
    "ShNm" : "FollowUpLossDat",
    "KeepColumns":  ["Avg_headway","std_headway","Count","MPR","PltSize","Gap"]    }

PLotDict = {}

PLotDict["Avg_StartUpLoss"] = {"ReadFileInfo": ReadFileInfo1, 
                               "Y_StdDev": "std_StartUpLoss", "CountCol":"Count", 
                               "Y_Lab":"Average StartUp<br> Loss Time (sec)", 
                               "tittleAddOn":"Exclusive EBT Start-Up Loss Time",
                               "fileNm":"Exclusive EBT Start-Up Loss Time","range_y_":[0,4]}

PLotDict["Avg_Headway1st4Veh"]= {"ReadFileInfo":ReadFileInfo1,
                               "Y_StdDev": "std_Headway1st4Veh", "CountCol":"Count_Headway1st4Veh", 
                               "Y_Lab":"Sum of<br> first 4 Vehicles's Headway (sec)", 
                               "tittleAddOn":"Exclusive EBT Sum of first 4 Vehicles's Headway",
                               "fileNm":"Exclusive EBT SumHeadway1st4Veh","range_y_":[0,10]}
PLotDict["Avg_Veh_Y_AR"]= {"ReadFileInfo":ReadFileInfo2,
                               "Y_StdDev": "std_Veh_Y_AR", "CountCol":"Count_Veh_Y_AR", 
                               "Y_Lab":"Average Number<br> of Vehicles in Y+AR", 
                               "tittleAddOn":"Exclusive EBT Vehicles Crossing in Y+AR",
                               "fileNm":"Exclusive EBT Vehicles Crossing in Y+AR","range_y_":[0,4]}
PLotDict["Avg_EndLossTime"]= {"ReadFileInfo":ReadFileInfo2,
                              "Y_StdDev": "std_EndLossTime", "CountCol":"Count_ELT", 
                               "Y_Lab":"Average End<br> Loss Time (sec)", 
                               "tittleAddOn":"Exclusive EBT End Loss Time",
                               "fileNm":"Exclusive EBT End Loss Time","range_y_":[0,4]}
PLotDict["Avg_headway"]= {"ReadFileInfo":ReadFileInfo3,
                              "Y_StdDev": "std_headway", "CountCol":"Count", 
                               "Y_Lab":"Average<br> Headway (sec)", 
                               "tittleAddOn":"Exclusive EBT Headway",
                               "fileNm":"Exclusive EBT Headway","range_y_":[0,4]}
PLotDict2 = PLotDict.copy()
# del PLotDict2["Avg_StartUpLoss"];del PLotDict2["Avg_Headway1st4Veh"];del PLotDict2["Avg_StartUpLoss"];del PLotDict2["Avg_StartUpLoss"]

for dir1 in ["EBT","EBL"]:
    for key, value in  PLotDict.items():
        title1 =value["tittleAddOn"]
        FileNm1 =value["fileNm"]
        ReadFileInfo_temp = value["ReadFileInfo"]
        range_Yeeee = value["range_y_"]
        if(dir1=="EBL"):
            title1 = title1.replace("Exclusive EBT","Protected EBL")
            FileNm1 = FileNm1.replace("Exclusive EBT","Protected EBL")
            if(key=="Avg_StartUpLoss"): range_Yeeee = [-4,4]
    
        PlotData(ReadFileInfo1 = ReadFileInfo_temp,
             VolTimeIntDat= VolTimeIntDat,
             Y_Var=key,
             Y_StdDev = value["Y_StdDev"],
             CountCol = value["CountCol"],
             Y_Lab =value["Y_Lab"],
             direction = dir1,
             tittleAddOn =title1,
             fileNm=FileNm1 ,
             range_y_ = range_Yeeee)