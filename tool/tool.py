import arcpy
from arcpy.sa import *

dem_raster = r"data\dem_raster"
turbines = r"data\turbines\windturbines_mva.shp"
mva_zones = r"data\MVA_zones\MVA_Germany.shp"
dfs_safety_distance = 1000

arcpy.CheckOutExtension("Spatial")

# Func to add elevation to turbines based on DEM raster 30m x 30m
def get_turbine_dem():
    temp_points = "in_memory/temp_points"
    arcpy.sa.ExtractValuesToPoints(turbines,dem_raster,temp_points)

    arcpy.AddField_management(turbines, "elev_ft", "DOUBLE")
    
    with arcpy.da.SearchCursor(temp_points, ["RASTERVALU", "FID"]) as src_cursor:
        fid_dict = {int(fid)-1: elev*3.28084 for elev, fid in src_cursor}
    
    with arcpy.da.UpdateCursor(turbines, ["elev_ft", "FID"]) as upd_cursor:
        for row in upd_cursor:
            row[0] = fid_dict.get(row[1], -9999)
            upd_cursor.updateRow(row)
    
    arcpy.Delete_management(temp_points)
    return "Elevation added."

# Func to add the given MVA value by the DFS to the turbines
def get_turbine_mva():
    arcpy.AddField_management(turbines, "mva_restr", "DOUBLE")
    temp_join = r"memory\temp_join"
    arcpy.analysis.SpatialJoin(target_features=turbines,join_features=mva_zones,out_feature_class=temp_join,join_operation="JOIN_ONE_TO_ONE",join_type="KEEP_ALL",match_option="INTERSECT")

    try:
        with arcpy.da.SearchCursor(temp_join, ["FIRST_LOWE", "TARGET_FID"]) as src_cursor:
            fid_dict = {fid: value for value, fid in src_cursor}
        
        with arcpy.da.UpdateCursor(turbines, ["mva_restr", "FID"]) as upd_cursor:
            for row in upd_cursor:
                row[0] = fid_dict.get(row[1], -9999)
                upd_cursor.updateRow(row)   
    finally:
        arcpy.Delete_management(temp_join)
    
    return "MVA values added."

# Func to calculate the maximum height of the turbines restricted by the MVA value
def write_maximum_height():
    arcpy.AddField_management(turbines, "max_meter", "DOUBLE")
    with arcpy.da.UpdateCursor(turbines, ["elev_ft", "mva_restr", "max_meter"]) as hgt_cursor:
        for row in hgt_cursor:
            if row[0] in (-9999, None) or row[1] in (-9999, None):
                row[2] = -9999
            else:
                row[2] = (float(row[1]) - float(row[0]) - dfs_safety_distance)/3.28084
            
            hgt_cursor.updateRow(row)
        
        return "Maximum height added."

# main func
if __name__ == "__main__":
    try:
        print(get_turbine_dem())
        print(get_turbine_mva())
        print(write_maximum_height())
    finally:
        arcpy.CheckInExtension("Spatial")
