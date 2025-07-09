import arcpy
from arcpy.sa import *

def get_objectid_field(fc):
    for field in arcpy.ListFields(fc):
        if field.type == "OID":
            return field.name
    raise Exception("Kein ObjectID-Feld gefunden!")

# --- Parameter und Datenquellen ---
dem_raster = r"data\dem_raster"
turbines = r"data\turbines\windturbines_mva.shp"
mva_zones = r"data\MVA_zones\MVA_Deutschland_8kmBuffer.shp"
dfs_safety_distance = 1000
output_file = r"data"
aprx = arcpy.mp.ArcGISProject("CURRENT")
map_obj = aprx.listMaps()[0]

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

def get_turbine_dem():
    temp_points = "in_memory/temp_points"
    arcpy.sa.ExtractValuesToPoints(turbines, dem_raster, temp_points)

    oid_field_temp = get_objectid_field(temp_points)
    oid_field_turb = get_objectid_field(turbines)

    field_names = [f.name for f in arcpy.ListFields(turbines)]
    if "elev_ft" not in field_names:
        arcpy.AddField_management(turbines, "elev_ft", "DOUBLE")

    fid_dict = {}
    with arcpy.da.SearchCursor(temp_points, ["RASTERVALU", oid_field_temp]) as src_cursor:
        for elev, fid in src_cursor:
            fid_dict[fid] = elev * 3.28084

    with arcpy.da.UpdateCursor(turbines, ["elev_ft", oid_field_turb]) as upd_cursor:
        for row in upd_cursor:
            row[0] = fid_dict.get(row[1], -9999)
            upd_cursor.updateRow(row)

    arcpy.management.CopyFeatures(temp_points, output_file)
    map_obj.addDataFromPath(output_file)
    arcpy.Delete_management(temp_points)
    return "Elevation added."

def get_turbine_mva():
    field_names = [f.name for f in arcpy.ListFields(turbines)]
    if "mva_restr" not in field_names:
        arcpy.AddField_management(turbines, "mva_restr", "DOUBLE")
    
    temp_join = r"memory\temp_join"
    arcpy.analysis.SpatialJoin(
        target_features=turbines,
        join_features=mva_zones,
        out_feature_class=temp_join,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT"
    )

    try:
        oid_field_turb = get_objectid_field(turbines)
        join_fields = [f.name for f in arcpy.ListFields(temp_join)]
        lowerlimit_field = next((f for f in join_fields if f.upper().startswith("LOWERLIMIT")), None)
        if not lowerlimit_field:
            raise Exception("Feld 'LOWERLIMIT' nicht im Spatial Join gefunden!")

        fid_dict = {}
        with arcpy.da.SearchCursor(temp_join, [lowerlimit_field, "TARGET_FID"]) as src_cursor:
            for value, fid in src_cursor:
                fid_dict[fid] = value

        with arcpy.da.UpdateCursor(turbines, ["mva_restr", oid_field_turb]) as upd_cursor:
            for row in upd_cursor:
                row[0] = fid_dict.get(row[1], -9999)
                upd_cursor.updateRow(row)
    finally:
        arcpy.Delete_management(temp_join)
    return "MVA values added."

def write_maximum_height():
    field_names = [f.name for f in arcpy.ListFields(turbines)]
    if "max_meter" not in field_names:
        arcpy.AddField_management(turbines, "max_meter", "DOUBLE")
    oid_field_turb = get_objectid_field(turbines)
    with arcpy.da.UpdateCursor(turbines, ["elev_ft", "mva_restr", "max_meter"]) as hgt_cursor:
        for row in hgt_cursor:
            if row[0] in (-9999, None) or row[1] in (-9999, None):
                row[2] = -9999
            else:
                row[2] = (float(row[1]) - float(row[0]) - dfs_safety_distance) / 3.28084
            hgt_cursor.updateRow(row)
    return "Maximum height added."

if __name__ == "__main__":
    try:
        get_turbine_dem()
        get_turbine_mva()
        write_maximum_height()
    finally:
        arcpy.CheckInExtension("Spatial")
