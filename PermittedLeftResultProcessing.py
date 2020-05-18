# -*- coding: utf-8 -*-
"""
Created on Fri May  8 12:55:55 2020
Purpose: Permitted left turn results processing
@author: abibeka
"""

#0.0 Housekeeping. Clear variable space
from IPython import get_ipython  #run magic commands
ipython = get_ipython()
ipython.magic("reset -f")
ipython = get_ipython()



# Load Libraries
#****************************************************************************************************************************************
import sys 
sys.path.append(r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\Github\HCM_Pooled_Fund_CAV')
from FunctionPermittedLeftTurns import *
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore") #Too many Pandas warnings
    
    
VolumeMap = {}

ResDir =r'C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\VissimModel_permissive\Results'
Volumes = np.arange(600,3000,300)
TimeIntevals = pd.IntervalIndex.from_tuples([(900, 1800), (2700, 3600), (4500, 5400),
                                     (6300,7200),(8100,9000),(9900,10800),
                                     (11700,12600),(13500,14400)],closed= "both")
VolumeMap = pd.DataFrame({'Volumes':Volumes,'TimeIntevals':TimeIntevals})

OutsideDir = r"C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HCM-CAV-Pooled-Fund\Experimental Design Arterial\VissimModel_permissive\Done"
ListOfScenarioFolders = glob(os.path.join(OutsideDir,"Platoon-*"))
a = ListOfScenarioFolders[0]
Pattern = re.compile("(.*)Platoon-(1|5|8)_Gap-(Normal|1.2|0.6).*")
PlatoonSize =Pattern.search(a).group(2)
GapSize= Pattern.search(a).group(3)
SearchDepth = os.path.join(a,"Scenarios")
SenarioMap = {"S000001":"0PerMPR","S000002":"20PerMPR","S000003":"40PerMPR",
              "S000004":"60PerMPR","S000005":"80PerMPR","S000006":"100PerMPR"}
FinDat = pd.DataFrame()
TempDfList =[]
for Scenario in ListOfScenarioFolders:
    Pattern = re.compile("(.*)Platoon-(1|5|8)_Gap-(Normal|1.1|1.2|0.6).*")
    PlatoonSize =int(Pattern.search(Scenario).group(2))
    GapSize= Pattern.search(Scenario).group(3) 
    SearchDepth = os.path.join(Scenario,"Scenarios")
    for Sno, mpr in SenarioMap.items():
        SearchDepth2 = os.path.join(SearchDepth, Sno)
        try:
            print(PlatoonSize,"---",GapSize,"---",mpr,"---", SearchDepth2)
            print("---"*40)
            TempDf = BatchProcessFiles(SearchDepth2,VolumeMap)
            TempDf.loc[:,"MPR"] = mpr
            TempDf.loc[:,"Platoon"] = PlatoonSize
            TempDf.loc[:,"Gap"] = GapSize
            TempDfList.append(TempDf)
        except AssertionError as error:
            print("xxx"*20)
            print("Needs Debuging")
            print(PlatoonSize,"---",GapSize,"---",mpr)
            print("xxx"*20)
FinDat = pd.concat(TempDfList)

# Back Calculate Critical Gap
#**************************************************************************************************************************************** 
ThroughSatFlowDat1 = ReadSatFlowData()
ThroughSatFlowDat1.Gap =ThroughSatFlowDat1.Gap.astype(str)
FinDat = FinDat.merge(ThroughSatFlowDat1,left_on=['Platoon','Gap','MPR'],right_on=['PltSize','Gap','MPR'],how='left')

#Global Variables:
P = .57 # Proportion arriving on green
C = 100
Y_AR = 5
G2 = 62 # Phase duration for permitted phase
#Effective Green phase 2
g2 = G2- Y_AR
NumLanesOppThrough = 2
ep = 2 #permitted extension of effective green (s).
l1= 2 # start-up loss time
FinDat.loc[:,"ArrivalRateOpposingThrough"] =FinDat.Volumes/(NumLanesOppThrough*3600)
FinDat = FinDat.eval('''
                     gq = (ArrivalRateOpposingThrough* @C* (1-@P))/ ((SatFlowRateOppThru/3600)-ArrivalRateOpposingThrough*@C*@P/@g2)
                     ''')
FinDat = FinDat.assign(Gq = lambda x: x.gq+l1,
                       Gu = lambda x: g2-x.Gq)
FinDat.loc[FinDat.Gu<=0,"Gu"] = 0
FinDat.loc[FinDat.Gu<=0,"Gu"] = 0
FinDat = FinDat.eval("gu = Gu+@ep")
FinDat.loc[FinDat.Gu<=0,"gu"] = 0
FinDat.loc[:,"Min_gp_gu"] = FinDat.gu.apply(lambda x: min(x,g2))
FinDat.loc[:,"FirstTerm"] = FinDat.Capacity - FinDat.NumSneakerPerCycle*3600/C
FinDat = FinDat.eval("PermittedSatFlow= @C*FirstTerm/Min_gp_gu")
FinDat = FinDat.eval("CriticalHeadway = -(3600/Volumes)*log((PermittedSatFlow * (1-exp(-Volumes*FollowUpHeadway/3600)))/Volumes)")
FinDat1 = FinDat.set_index(['Platoon','Gap','Volumes','MPR'])
FinDat1.sort_index(inplace=True)
# -(3600/900)*np.log((628.713 * (1-np.exp(-900*2.5/3600)))/900)

# Plot
#****************************************************************************************************************************************
PlotData(Data1 =FinDat1, Y_Var= "CriticalHeadway", Y_Lab="Critical Headway (sec)",
         tittleAddOn= "CriticalHeadway",MainDir=ResDir,fileNm="CriticalHeadway",range_y_ = [0,6])

PlotData(Data1 =FinDat1, Y_Var= "FollowUpHeadway", Y_Lab="Follow-Up Headway (sec)",
         tittleAddOn= "FollowUpHeadway",MainDir=ResDir,fileNm="FollowUpHeadway",range_y_ = [0,6])










# Round HCM Calculation 
#****************************************************************************************************************************************
#SaturationFlowRateOppThrough =np.array([1900, 1900,1900,1900,1900,1900,1900,1900]) #Revise this 
P = .57 # Proportion arriving on green
C = 100
Y_AR = 5
NumSneakers =2
G2 = 62 # Phase duration for permitted phase
#Effective Green phase 2
g2 = G2- Y_AR
NumLanesOppThrough = 2
ep = 2 #permitted extension of effective green (s).
l1= 2 # start-up loss time
CriticalHeadway = 4.5
FollowUpHeadway =2.5
OpposingThroughVolumes = VolumeMap.Volumes.values
ArrivalRateOpposingThrough =OpposingThroughVolumes/(NumLanesOppThrough*3600)
gq = (ArrivalRateOpposingThrough* C* (1-P))/ ((SaturationFlowRateOppThrough/3600)-ArrivalRateOpposingThrough*C*P/g2)
#(ArrivalRate*Cycle*(1-PropOnGreen))/((SatFlow/3600)-ArrivalRate*Cycle*PropOnGreen/effGreen)
Gq = gq + l1
Gu = g2-Gq
NegativeValues = Gu <= 0
Gu[NegativeValues] = 0
gu = Gu+ep
gu[NegativeValues] = 0
g2 = np.repeat(g2,len(gu))
SatFlowPermitted = OpposingThroughVolumes* np.exp(-OpposingThroughVolumes*CriticalHeadway/3600)/(1- np.exp(-OpposingThroughVolumes*FollowUpHeadway/3600))

HCMcapacity = (np.minimum(gu,g2)*SatFlowPermitted + 3600*NumSneakers)/C

