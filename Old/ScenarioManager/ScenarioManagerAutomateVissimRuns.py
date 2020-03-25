# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 16:03:21 2020
Purpose: Automate Folder creation for Scenario Manager
@author: abibeka
"""

# COM-Server
import win32com.client as com
import os
import glob
import sys
import shutil
from distutils.dir_util import copy_tree


sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
OuterDir = r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModelScManager'

def EditParamFile(OuterDir,Speed,PltSz,Gap):
    ParamFile = os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l),"parameters.txt")
    file1 = open(ParamFile,"w") 
    L1 = Speed * 0.44704; L2 = PltSz; L3 = Gap # Speed in m/s
    file1.write("{}\n".format(L1)); file1.write("{}\n".format(L2)); file1.write("{}\n".format(L3))
    file1.close()
    return()
    
def CopyDriverModelDll(OuterDir,Speed,PltSz,Gap):
    DriverModelDll = os.path.join(OuterDir,"DriverModel.dll")
    NewLoc = os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l))
    shutil.copy(DriverModelDll, NewLoc)
    return()

def CopyRBCFile(OuterDir,Speed,PltSz,Gap):
    RBCFile = os.path.join(OuterDir,"PreTime_Synchro_V1.rbc")
    NewLoc = os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l))
    shutil.copy(RBCFile, NewLoc)
    return()

def CopyScenarioManagerFolder(OuterDir,PltSz,Gap):
    ScenManagerFolder = os.path.join(OuterDir,"TemplateSeed")
    NewLoc = os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l))
    copy_tree(ScenManagerFolder, NewLoc)
    return()



Gaps = [0.6, 0.7, 1.1]
PlatoonSizes = [1,2,5,8]
MPR_to_VissimVehCompMap ={
 "0PerMPR":1,
 "20PerMPR":2,
 "40PerMPR":4,
 "60PerMPR":6,
 "80PerMPR":8,
 "100PerMPR":10
 }

PltSz_l = PltSz =2
Gap_l= Gap =  0.7
for PltSz_l in PlatoonSizes:
    for Gap_l in Gaps:
        if (PltSz_l== 1) & (Gap_l in [0.7, 1.1]):
            continue
        elif PltSz_l== 1:
            Gap_l = 1.2
        else: ""
        try:
            os.mkdir(os.path.join(OuterDir,"P{}_G{}".format(PltSz_l,Gap_l)))
        except:
            print("Dir creation error")  
        CopyScenarioManagerFolder(OuterDir,PltSz_l,Gap_l)
        EditParamFile(OuterDir=OuterDir,Speed= 40,PltSz=PltSz_l,Gap=Gap_l)

        
        
        