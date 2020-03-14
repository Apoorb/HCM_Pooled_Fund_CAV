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
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')

Vissim = com.Dispatch("Vissim.Vissim-64.1100") # Vissim 9 - 64 bit
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim.11") # Vissim 11 

## ========================================================================
# Load Network
#==========================================================================
# 5 runs 
# Path_to_VissimFile = r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel'
Path_to_VissimFile = r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModels'
os.chdir(Path_to_VissimFile)
os.getcwd()
Filename = Path_to_VissimFile +"\\ArtBaseNet.inpx"
layoutFile=Filename.replace(".inpx",".layx")
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
    
def SaveVissimFile(OuterDir, PltSz, Gap, Mpr):
    Filename = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap)
                            ,"ArtBaseNet_{}_{}_{}.inpx".format(PltSz,Gap,MPR))
    Vissim.SaveNetAs(Filename)
    Vissim.SaveLayout(Filename.replace('inpx','layx'))
    Nm = "ArtBaseNet_{}".format(MPR)
    return()
    
def EditParamFile(OuterDir,Speed,PltSz,Gap):
    ParamFile = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap),"parameters.txt")
    file1 = open(ParamFile,"w") 
    L1 = Speed * 0.44704; L2 = PltSz; L3 = Gap # Speed in m/s
    file1.write("{}\n".format(L1)); file1.write("{}\n".format(L2)); file1.write("{}\n".format(L3))
    file1.close()
    return()
    
def CopyDriverModelDll(OuterDir,Speed,PltSz,Gap):
    DriverModelDll = os.path.join(OuterDir,"DriverModel.dll")
    NewLoc = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap))
    shutil.copy(DriverModelDll, NewLoc)
    return()

def CopyRBCFile(OuterDir,Speed,PltSz,Gap):
    RBCFile = os.path.join(OuterDir,"PreTime_Synchro_V1.rbc")
    NewLoc = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap))
    shutil.copy(RBCFile, NewLoc)
    return()

def RunVissimBatchModel():
    Vissim.Simulation.SetAttValue('NumRuns', 10)
    Vissim.Simulation.SetAttValue('UseMaxSimSpeed', True)
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue('QuickMode', True)
    Vissim.Simulation.RunContinuous()
    return()
    
VI_number   = 1 # VI = Vehicle Input
Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(1)")

Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(2)")


Gaps = [0.6, 1, 1.2]
PlatoonSizes = [1,2,5,10]
MPR_to_VissimVehCompMap ={
 "0PerMPR":1,
 "20PerMPR":2,
 "40PerMPR":4,
 "60PerMPR":6,
 "80PerMPR":8,
 "100PerMPR":10
 }
VehComp = 1

AlreadyRan = []
# EditParamFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=2,Gap=0.6)

for PltSz_l in PlatoonSizes:
    try:
        os.mkdir(os.path.join(Path_to_VissimFile,"{}".format(PltSz_l)))
    except:
        print("Dir creation error")
    for Gap_l in Gaps:
        if (PltSz_l== 1) & (Gap_l in [1,1.2]):
            continue
        elif PltSz_l== 1:
            Gap_l = 1.4
        else: ""
        try:
            os.mkdir(os.path.join(Path_to_VissimFile,"{}".format(PltSz_l),"{}".format(Gap_l)))
        except:
            print("Dir creation error")  
        EditParamFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap=Gap_l)
        CopyDriverModelDll(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap=Gap_l)
        CopyRBCFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=PltSz_l,Gap=Gap_l)
        for MPR in MPR_to_VissimVehCompMap.keys():
            if MPR not in AlreadyRan:
                SetMPRforVISSIM(MPR)
                SaveVissimFile(OuterDir=Path_to_VissimFile, PltSz=PltSz_l, Gap=Gap_l, Mpr=MPR)
                os.chdir(Path_to_VissimFile)
                RunVissimBatchModel()
## ========================================================================
# End Vissim
#==========================================================================
Vissim = None
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    