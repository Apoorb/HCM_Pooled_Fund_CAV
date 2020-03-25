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
from multiprocessing import Process
from time import sleep
Vissim = com.Dispatch("Vissim.Vissim-64.1100") # Vissim 9 - 64 bit
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim.11") # Vissim 11 
## ========================================================================
# Set Vehicle/ Input
#==========================================================================

def RunVissimBatchModel(OuterDir, PltSz, Gap, Mpr):
    Filename = os.path.join(OuterDir,"{}".format(PltSz),"{}".format(Gap)
                            ,"ArtBaseNet_{}_{}_{}.inpx".format(PltSz,Gap,MPR))
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

    return()
    

    
if __name__ == '__main__':
    sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
    
    ## ========================================================================
    # Load Network
    #==========================================================================
    # 5 runs 
    # Path_to_VissimFile = r'H:\22\22398 - CAV in HCM Pooled Fund Study\Task4-ScenarioTesting\Base VISSIM Models\Arterial_Model\VissimBaseModel'
    Path_to_VissimFile = r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\ExperimentalDesignArterial\VissimModels'
    Gaps = [1.2]
    MPR_to_VissimVehCompMap ={
     "0PerMPR":1,
     "20PerMPR":2,
     "40PerMPR":4,
     "60PerMPR":6,
     "80PerMPR":8,
     "100PerMPR":10
     }
    VehComp = 1


    AlreadyRan = [[2,0.7]]
    # EditParamFile(OuterDir=Path_to_VissimFile,Speed= 40,PltSz=2,Gap=0.6)
    #         p1 = Process(target =RunVissimBatchModel(OuterDir=Path_to_VissimFile, PltSz=1, Gap=Gap_l, Mpr=MPR))
    for Gap_l in Gaps:
       for MPR in MPR_to_VissimVehCompMap.keys():
             #SetMPRforVISSIM(MPR)
             #SaveVissimFile(OuterDir=Path_to_VissimFile, PltSz=PltSz_l, Gap=Gap_l, Mpr=MPR)
             RunVissimBatchModel(Path_to_VissimFile, 1, Gap_l, MPR)
    ## ========================================================================
    # End Vissim
    #==========================================================================
    Vissim = None
    
    
    
    
    
    
    
    
    
    
    
    
    