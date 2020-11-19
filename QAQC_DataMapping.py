# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 10:30:31 2020
#QAQC Spatial Join 
@author: abibeka
"""

# 0.0 Housekeeping. Clear variable space
from IPython import get_ipython  # run magic commands

ipython = get_ipython()
ipython.magic("reset -f")
ipython = get_ipython()


import geopandas as gpd
import pandas as pd
import os
from shapely import wkt
from shapely.geometry import Point, LineString, MultiLineString
import pyepsg

os.chdir(
    r"C:\Users\abibeka\OneDrive - Kittelson & Associates, Inc\Documents\HSIP\DataMapping"
)
x1 = pd.ExcelFile("DataSummary.xlsx")
x1.sheet_names
Dat = x1.parse("2014", index_col=[0, 1, 2, 3, 4, 5, 6, 7, 8])
Dat.reset_index(inplace=True)
Dat.LineSeg

Dat["LineSeg"] = Dat["LineSeg"].apply(wkt.loads)
crs = {"init": "epsg:4326"}
gdf = gpd.GeoDataFrame(Dat, crs=crs, geometry="LineSeg")


SegInfoData = pd.read_csv(
    "RMSSEG_State_Roads.csv",
    usecols=[
        "CTY_CODE",
        "ST_RT_NO",
        "SEG_NO",
        "SEG_LNGTH_FEET",
        "CUR_AADT",
        "X_VALUE_BGN",
        "Y_VALUE_BGN",
        "X_VALUE_END",
        "Y_VALUE_END",
    ],
)
SegInfoData = SegInfoData.rename(
    columns={
        "CTY_CODE": "CountyCode",
        "ST_RT_NO": "SR",
        "SEG_NO": "SegNo",
        "SEG_LNGTH_FEET": "SegLenFt",
        "CUR_AADT": "CurAADT",
    }
)
SegInfoData.columns
SegInfoData.loc[:, "BegGeom"] = SegInfoData[["X_VALUE_BGN", "Y_VALUE_BGN"]].apply(
    lambda x: Point((x[0], x[1])), axis=1
)
SegInfoData.loc[:, "EndGeom"] = SegInfoData[["X_VALUE_END", "Y_VALUE_END"]].apply(
    lambda x: Point((x[0], x[1])), axis=1
)
SegInfoData.loc[:, "LineSeg"] = SegInfoData[["BegGeom", "EndGeom"]].apply(
    lambda x: LineString(x.tolist()), axis=1
)

SegInfoData = gpd.GeoDataFrame(SegInfoData, crs=crs, geometry="BegGeom")
sum(SegInfoData.Y_VALUE_BGN.isna())
SegInfoData = SegInfoData[~SegInfoData.Y_VALUE_BGN.isna()]
SegInfoData.geometry.name
pyepsg.get(SegInfoData.crs["init"].split(":")[1])

Qaqc_dat = gpd.sjoin(SegInfoData, gdf, how="inner")

Qaqc_dat.columns

Qaqc_dat2 = Qaqc_dat[
    [
        "CountyCode_left",
        "CountyCode_right",
        "SR_left",
        "SR_right",
        "BegSeg",
        "SegNo",
        "EndSeg",
        "ProjID",
    ]
]


mask = (Qaqc_dat2.SR_left == Qaqc_dat2.SR_right) & (
    Qaqc_dat2.CountyCode_left == Qaqc_dat2.CountyCode_right
)
Qaqc_dat3 = Qaqc_dat2[mask]

A = set(Qaqc_dat3.ProjID)

B = set(gdf.ProjID)
B - A
