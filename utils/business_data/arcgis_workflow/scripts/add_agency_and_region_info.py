import arcpy
import os

arcpy.env.overwrite = True

def add_attributes_to_shp(shapefile):

    arcpy.AddMessage(shapefile)

    filename = os.path.basename(shapefile)
    publand = r"resources\AllPublicLandsFL.shp"
    lyr = r"in_memory\joinresult"

    filenameXregion = {
        "FloridaSites_Central.shp" : "Central",
        "FloridaSites_EastCentral.shp" : "East Central",
        "FloridaSites_NorthCentral.shp" : "North Central",
        "FloridaSites_Northeast.shp" : "Northeast",
        "FloridaSites_Northwest.shp" : "Northwest",
        "FloridaSites_Southeast.shp" : "Southeast",
        "FloridaSites_Southwest.shp" : "Southwest",
        "FloridaSites_WestCentral.shp" : "West Central",
    }

    keep_fields = [f.name for f in arcpy.ListFields(shapefile)]
    keep_fields += ['MANAGING_A','MANAME']

    print("creating spatial join")
    arcpy.analysis.SpatialJoin(shapefile,publand,lyr)
    drop_fields = [f.name for f in arcpy.ListFields(lyr) if not f.name in keep_fields]
    print(len(arcpy.ListFields(lyr)))
    arcpy.management.DeleteField(lyr,drop_fields)
    print(len(arcpy.ListFields(lyr)))
    print("adding category field")
    arcpy.management.AddField(lyr,"MA_CAT","TEXT",field_length=50)
    print("updating managing agency and category fields")
    lookup = {
        'FL Dept. of Environmental Protection, Div. of Recreation and Parks':'State Park',
        'FL Dept. of Agriculture and Consumer Services, Florida Forest Service':'State Forest',
        'FL Fish and Wildlife Conservation Commission':'Fish and Wildlife Conservation Commission',
        'FL Dept. of Environmental Protection, Florida Coastal Office':'Aquatic Preserve'
    }

    with arcpy.da.UpdateCursor(lyr,["MANAGING_A","MA_CAT"]) as cursor:
        for row in cursor:
            if not row[0] in lookup:
                row[0] = ""
            else:
                row[1] = lookup[row[0]]
            cursor.updateRow(row)

    regions = r"\resources\FPAN-regions-expanded.shp"
    r_lyr = "r_lyr"

    arcpy.management.MakeFeatureLayer(regions,r_lyr)
    arcpy.management.MakeFeatureLayer(lyr,"lyr")

    arcpy.management.AddField(lyr,"FPAN_REG","TEXT",field_length=50)

    if filename in filenameXregion:
        print("adding region name by filename")
        arcpy.management.CalculateField(lyr,"FPAN_REG",'"'+filenameXregion[filename]+'"')
    else:
        print("adding region name by select by location")
        with arcpy.da.SearchCursor(r_lyr,["name"]) as cursor:
            
            for row in cursor:
                name = row[0]

                expr = "\"name\" = '{}'".format(name)
                arcpy.management.SelectLayerByAttribute(r_lyr,"NEW_SELECTION",expr)
                
                arcpy.management.SelectLayerByLocation("lyr","INTERSECT",r_lyr)
                arcpy.management.CalculateField("lyr","FPAN_REG",'"'+name+'"')

    out = os.path.abspath(shapefile)
    if arcpy.Exists(out):
        arcpy.management.Delete(out)
    arcpy.conversion.FeatureClassToFeatureClass(lyr,os.path.dirname(out),os.path.basename(out))