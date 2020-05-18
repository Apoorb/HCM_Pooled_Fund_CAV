# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 13:18:22 2020
Purpose: Automate Simulation runs at different MPR
@author: abibeka
"""


# COM-Server
import win32com.client as com
import os
import glob
import sys
import shutil
import gc
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')

Vissim = com.Dispatch("Vissim.Vissim-64.1100") # Vissim 9 - 64 bit
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim.11") # Vissim 11 

## ========================================================================
# Load Network
#==========================================================================
# 5 runs 
# Path_to_VissimFile = r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel'
Path_to_VissimFile = r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\VissimModel_permissive\Platoon-8_Gap-0.6 - Copy'
os.chdir(Path_to_VissimFile)
os.getcwd()
Filename = Path_to_VissimFile +"\\VissimBaseModelPermissiveLeft.vissimpdb"
layoutFile=Filename.replace(".vissimpdb",".layx")
flag_read_additionally  = False # you can read network(elements) additionally, in this case set "flag_read_additionally" to true
Vissim.LoadNet(Filename, flag_read_additionally)
Vissim.LoadLayout(layoutFile)



## ========================================================================
# Set Vehicle/ Input
#==========================================================================
def SetMPRforVISSIM(MPR="0PerMPR"):
    # Set the MPR by changing the veh composition type for vehicle inputs 
    # Set vehicle input:
    VI_number   = 1 # VI = Vehicle Input. EB direction
    EBLinkNm = Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue('Name')
    assert(EBLinkNm=="EB")
    for i in range(1,14):
        #print(Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp({})".format(i)))
        Vissim.Net.VehicleInputs.ItemByKey(VI_number).SetAttValue("VehComp({})".format(i),MPR_to_VissimVehCompMap[MPR])    
    return()
    
def SaveVissimFile(OuterDir, PltSz, Gap_Label, Mpr):
    Filename = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap_Label)
                            ,"ArtBaseNet_{}_{}_{}.inpx".format(PltSz,Gap_Label,MPR))
    Vissim.Simulation.SetAttValue("SimPeriod",8400)
    Vissim.Simulation.SetAttValue('NumRuns', 10)
    Vissim.Simulation.SetAttValue('UseMaxSimSpeed', True)
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue('QuickMode', True)
    Vissim.SaveNetAs(Filename)
    Vissim.SaveLayout(Filename.replace('inpx','layx'))
    Nm = "ArtBaseNet_{}".format(MPR)
    return()
    
def EditParamFile(OuterDir,Speed,PltSz,Gap,Gap_Label):
    ParamFile = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap_Label),"parameters.txt")
    file1 = open(ParamFile,"w") 
    L1 = Speed * 0.44704; L2 = PltSz; L3 = Gap # Speed in m/s
    file1.write("{}\n".format(L1)); file1.write("{}\n".format(L2)); file1.write("{}\n".format(L3))
    file1.close()
    return()
    
def CopyDriverModelDll(OuterDir,Speed,PltSz,Gap_Label):
    DriverModelDll = os.path.join(OuterDir,"DriverModel.dll")
    NewLoc = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap_Label))
    shutil.copy(DriverModelDll, NewLoc)
    return()

def CopyRBCFile(OuterDir,Speed,PltSz,Gap_Label):
    RBCFile = os.path.join(OuterDir,"PreTime_Synchro_V1.rbc")
    NewLoc = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap_Label))
    shutil.copy(RBCFile, NewLoc)
    return()

def RunVissimBatchModel(OuterDir, PltSz, Gap_Label, Mpr):
    Filename = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap_Label)
                            ,"ArtBaseNet_{}_{}_{}.inpx".format(PltSz,Gap_Label,MPR))
    layoutFile=Filename.replace(".inpx",".layx")
    flag_read_additionally  = False # you can read network(elements) additionally, in this case set "flag_read_additionally" to true
    Vissim.LoadNet(Filename, flag_read_additionally)
    Vissim.LoadLayout(layoutFile)
    Vissim.Simulation.SetAttValue("SimPeriod",8400)
    Vissim.Simulation.SetAttValue('NumRuns', 10)
    Vissim.Simulation.SetAttValue('UseMaxSimSpeed', True)
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue('QuickMode', True)
    Vissim.Simulation.RunContinuous()
    # Vissim.Exit()
    return(Filename)
    
VI_number   = 1 # VI = Vehicle Input
Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(1)")

Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(2)")


# Gaps = [0.1, 0.6, 1.1]
# PlatoonSizes = [1,5,8]
MPR_to_VissimVehCompMap ={
 "0PerMPR":1,
 "20PerMPR":2,
 "40PerMPR":4,
 "60PerMPR":6,
 "80PerMPR":8,
 "100PerMPR":10
 }
VehComp = 1

# AlreadyRan = [[2,0.7]]
# PltSz_l = 2
# Gap_l= 0.7
# MPR = "100PerMPR"

AlreadyRan = []
Gaps = [0.1]
PlatoonSizes = [5,8]

# EditParamFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=2,Gap=0.6)

ScneariosRan = []
for PltSz_l in PlatoonSizes:
    try:
        os.mkdir(os.path.join(Path_to_VissimFile,"{}".format(PltSz_l)))
    except:
        print("Dir creation error")
    for Gap_l in Gaps:
        if (PltSz_l== 1) & (Gap_l in [0.7, 1.1]):
            continue
        elif PltSz_l== 1:
            Gap_l = 1.2
        else: ""
        Gap_Label = Gap_l
        if Gap_l == 0.1 : Gap_Label= "Normal"
        try:
            os.mkdir(os.path.join(Path_to_VissimFile,"{}".format(PltSz_l),"{}".format(Gap_Label)))
        except:
            print("Dir creation error")  
        EditParamFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap=Gap_l,Gap_Label=Gap_Label)
        CopyDriverModelDll(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap_Label=Gap_Label)
        CopyRBCFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap_Label=Gap_Label)
        os.chdir(os.path.join(Path_to_VissimFile,"{}".format(PltSz_l),"{}".format(Gap_Label)))
        for MPR in MPR_to_VissimVehCompMap.keys():
            if [PltSz_l,Gap_l] not in AlreadyRan:
                SetMPRforVISSIM(MPR)
                SaveVissimFile(OuterDir=Path_to_VissimFile, PltSz=PltSz_l, Gap_Label=Gap_Label, Mpr=MPR)
                try:
                    temp = RunVissimBatchModel(OuterDir=Path_to_VissimFile, PltSz=PltSz_l, Gap_Label=Gap_Label, Mpr=MPR)
                    ScneariosRan.append(temp)
                except:
                    print(ScneariosRan)
        os.chdir(Path_to_VissimFile)
        

## ========================================================================
# End Vissim
#==========================================================================
Vissim = None
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    