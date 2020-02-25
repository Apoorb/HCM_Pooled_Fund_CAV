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
    Filename = os.path.join(Path_to_VissimFile,"ArtBaseNet_{}.inpx".format(MPR))
    Vissim.SaveNetAs(Filename)
    Vissim.SaveLayout(Filename.replace('inpx','layx'))
    Nm = "ArtBaseNet_{}".format(MPR)
    return(Nm)
    
def RunVissimBatchModel():
    Vissim.Simulation.SetAttValue('NumRuns', 10)
    Vissim.Simulation.SetAttValue('UseMaxSimSpeed', True)
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue('QuickMode', True)
    Vissim.Simulation.RunContinuous()
    return()
    
VI_number   = 1 # VI = Vehicle Input
Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(1)")

Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue("VehComp(2)")

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
for MPR in MPR_to_VissimVehCompMap.keys():
    if MPR not in AlreadyRan:
        Nm = SetMPRforVISSIM(MPR)
        RunVissimBatchModel()
## ========================================================================
# End Vissim
#==========================================================================
Vissim = None
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    