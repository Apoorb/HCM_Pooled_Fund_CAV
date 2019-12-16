# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 10:55:45 2019

@author: abibeka
"""

# COM-Server
import win32com.client as com
import os
import glob
import sys
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
from CommonFunctions import ProcessSigTime
from CommonFunctions import ProcessDatCol
from CommonFunctions import MergeDatCol_SigDat 
from CommonFunctions import MultiVISSIM_RunResProcess

Vissim = com.Dispatch("Vissim.Vissim-64.1100") # Vissim 9 - 64 bit
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim.11") # Vissim 11 

## ========================================================================
# Load Network
#==========================================================================
# 5 runs 
Path_to_VissimFile = r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel'
os.getcwd()
Filename = Path_to_VissimFile +"\\VissimBaseModel_Calibration - V2.inpx"
layoutFile=Filename.replace(".inpx",".layx")
flag_read_additionally  = False # you can read network(elements) additionally, in this case set "flag_read_additionally" to true
Vissim.LoadNet(Filename, flag_read_additionally)
Vissim.LoadLayout(layoutFile)


## ========================================================================
# Set Vehicle/ Input
#==========================================================================
def SetStudyApproachVol(new_volume=2000):
    # Calibration/ Sensitivity 
    # Set vehicle input:
    VI_number   = 1 # VI = Vehicle Input
    EBLinkNm = Vissim.Net.VehicleInputs.ItemByKey(VI_number).AttValue('Name')
    assert(EBLinkNm=="EB")
    Vissim.Net.VehicleInputs.ItemByKey(VI_number).SetAttValue('Volume(1)', new_volume)
    
    Filename = os.path.join(Path_to_VissimFile,"ExtraRuns", 'VissimBaseModel_Calibration_VolIs {} - V2.inpx'.format(new_volume))
    Vissim.SaveNetAs(Filename)
    Filename = os.path.join(Path_to_VissimFile, "ExtraRuns",'VissimBaseModel_Calibration_VolIs {} - V2.layx'.format(new_volume))
    Vissim.SaveLayout(Filename)
    Nm = 'VissimBaseModel_Calibration_VolIs {} - V2'.format(new_volume)
    return(Nm)
    

## ========================================================================
# Set Driving Behavior
#==========================================================================
# Calibration/ Sensitivity 
DriverBehavNum = 1
EBLinkNm = Vissim.Net.VehicleInputs.ItemByKey(DriverBehavNum).AttValue('Name')
Vissim.Net.DrivingBehaviors.ItemByKey(DriverBehavNum).AttValue('Name')
Vissim.Net.DrivingBehaviors.ItemByKey(DriverBehavNum).AttValue('W74ax')
Vissim.Net.DrivingBehaviors.ItemByKey(DriverBehavNum).AttValue('W74bxAdd')
Vissim.Net.DrivingBehaviors.ItemByKey(DriverBehavNum).AttValue('W74bxMult')

## ========================================================================
# Simulation
#==========================================================================
# 10 runs 
NewVolumes = [1800,1900,2000,2200]
NewVol = 2000
FileNm = "VissimBaseModel_Calibration_VolIs 2001 - V2"
FileDir = r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel\ExtraRuns'
for NewVol in NewVolumes:
    FileNm = SetStudyApproachVol(NewVol)
    Vissim.Simulation.SetAttValue('NumRuns', 10)
    Vissim.Simulation.SetAttValue('UseMaxSimSpeed', True)
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue('QuickMode', True)
    Vissim.Simulation.RunContinuous()
    MultiVISSIM_RunResProcess(CommonFileNmWithoutINPX =FileNm , NewVol =NewVol , FileDir1 =FileDir )
## ========================================================================
# End Vissim
#==========================================================================
Vissim = None