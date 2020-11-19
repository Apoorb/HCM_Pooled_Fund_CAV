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
import re

sys.path.append(
    r"C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV"
)

Vissim = com.Dispatch("Vissim.Vissim-64.1100")  # Vissim 9 - 64 bit
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim.11")  # Vissim 11


def RunVissimScenarios(Vissim):
    # Activate QuickMode:
    Vissim.Graphics.CurrentNetworkWindow.SetAttValue("QuickMode", 1)
    Vissim.SuspendUpdateGUI()  # stop updating of the complete Vissim workspace (network editor, list, chart and signal time table windows)
    # Alternatively, load a layout (*.layx) where dynamic elements (vehicles and pedestrians) are not visible:
    # Vissim.LoadLayout(os.path.join(Path_of_COM_Basic_Commands_network, 'COM Basic Commands - Hide vehicles.layx')) # loading a layout where vehicles are not displayed
    Sim_break_at = 0  # simulation second [s] => 0 means no break!
    Vissim.Simulation.SetAttValue("SimBreakAt", Sim_break_at)
    # Set maximum speed:
    StartSeed = 42
    Vissim.Simulation.SetAttValue("UseMaxSimSpeed", True)
    Vissim.Simulation.RunContinuous()
    gc.collect()


OutsideDir = r"C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\VissimModel_permissive"
ListOfScenarioFolders = glob.glob(os.path.join(OutsideDir, "Platoon-*"))
SenarioMap = {
    "S000001": "0PerMPR",
    "S000002": "MPR 20PerMPR",
    "S000003": "40PerMPR",
    "S000004": "60PerMPR",
    "S000005": "80PerMPR",
    "S000006": "MPR 100PerMPR",
}

for Scenario in ListOfScenarioFolders:
    Pattern = re.compile(
        "(.*)Platoon-(1|5|8)_Gap-(Normal|1.1||1.2|0.6)(?:(\s*-\s*))?(Copy)?.*"
    )
    PlatoonSize = Pattern.search(Scenario).group(2)
    GapSize = Pattern.search(Scenario).group(3)
    Copy = Pattern.search(Scenario).group(4)
    if Copy == "Copy":
        continue
    # Load File
    Filename = Scenario + "\\VissimBaseModelPermissiveLeft.vissimpdb"
    layoutFile = Filename.replace(".vissimpdb", ".layx")
    flag_read_additionally = False  # you can read network(elements) additionally, in this case set "flag_read_additionally" to true
    Vissim.LoadNet(Filename, flag_read_additionally)
    Vissim.LoadLayout(layoutFile)
    SearchDepth = os.path.join(Scenario, "Scenarios")
    for i in [5, 6]:
        Vissim.ScenarioManagement.LoadScenario(i)
        RunVissimScenarios(Vissim)


## ========================================================================
# End Vissim
# ==========================================================================
Vissim = None
