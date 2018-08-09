import os
import csv
from dateutil.parser import parse
from datetime import datetime
from arcpy import (
    AddMessage,
    ListFields,
)
from arcpy.management import (
    GetCount,
    MakeFeatureLayer,
    MakeTableView,
    CopyFeatures,
    CheckGeometry,
    RepairGeometry,
    Copy,
    AddSpatialIndex,
)
from arcpy.da import (
    SearchCursor,
    UpdateCursor,
)

def shapefile_to_csv(shapefile):
    
    cleaned = prep_shapefile(shapefile)
    
def check_geometry(shapefile):
    
    AddMessage(os.path.basename(shapefile))
    
    initial_ct = int(GetCount(shapefile)[0])
    CheckGeometry(shapefile,r"in_memory\output")
    MakeTableView(r"in_memory\output","tv")
    ct = int(GetCount("tv")[0])
    AddMessage(" -- {} errors".format(ct))

    if ct:
        AddMessage(" -- repairing geometry")
        RepairGeometry(shapefile,"DELETE_NULL")
        
        AddSpatialIndex(shapefile)

        CheckGeometry(shapefile,r"in_memory\output")
        MakeTableView(r"in_memory\output","tv")
        ct = int(GetCount("tv")[0])
        if ct == 0:
            AddMessage("   >> all errors fixed")
        else:
            AddMessage("   >> {} left:".format(ct))
        
        with SearchCursor("tv","*") as cursor:
            for row in cursor:
                AddMessage(row)
                
    final_ct = int(GetCount(shapefile)[0])
    AddMessage("  {} records removed due to bad geometry".format(initial_ct-final_ct))

def clean_date(value):

    if isinstance(value,datetime):
        return value
    # AddMessage(value)
    clean = ''.join(n for n in value if n.isdigit() or n in ['-','/','\\'])
    clean = clean.rstrip("-")
    # AddMessage(clean)
    if clean.rstrip() == "":
        return ""
    if len(clean) == 4:
        return "{}-01-01".format(clean)
    elif len(clean) > 4:
        try:
            d = parse(clean)
            return d.strftime("%Y-%m-%d")
        except:
            AddMessage("    couldn't parse this date: "+str(clean))
            return ""
    else:
        AddMessage("    couldn't parse this date: "+str(clean))
        return ""
    
def prep_shapefile(shapefile,date_fields=[]):

    date_fields = ["YEARESTAB","D_NRLISTED","YEARBUILT"]

    ## create copy of the input shapefile and make a layer from it to use
    in_shp = "in_shp"
    MakeFeatureLayer(shapefile,in_shp)
    out_path = shapefile.replace(".shp","_prep.shp")
    CopyFeatures(in_shp,out_path)
    out_fl = "out_fl"
    MakeFeatureLayer(out_path,out_fl)
    
    ## get a list of field index numbers for the date fields
    date_field_index = {}
    for i,f in enumerate(ListFields(out_fl)):
        if f.name in date_fields:
            date_field_index[i] = f.type
            
            AddMessage(f.type)
    
    datefix_ct = 0
    with UpdateCursor(out_fl,"*") as cursor:
        for row in cursor:
            for index in date_field_index.keys():
                old_date = row[index]
                # AddMessage(old_date)
                if old_date:
                    new_date = clean_date(old_date)
                    if new_date != old_date:
                        datefix_ct+=1
                        AddMessage(old_date)
                        AddMessage(new_date)
                        if date_field_index[index] == "Date":
                            new_date = datetime.strptime(new_date,"%Y-%m-%d")
                        
                        row[index] = new_date
                        cursor.updateRow(row)
    
    AddMessage(" -- {} dates cleaned up".format(datefix_ct))
    
    return out_fl

