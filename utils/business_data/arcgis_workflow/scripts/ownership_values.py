import os
import csv
from arcpy import (
    AddMessage,
    ListFields,
)
from arcpy.management import (
    MakeFeatureLayer,
    AddField,
    GetCount,
)
from arcpy.da import (
    UpdateCursor,
)

def get_ownership_dict(csv_path):

    AddMessage("collecting ownership data")

    ## define lookup table from ownership csv
    lookup = {
        'CITY':"City",
        'COUN':"County",
        'STAT':"State",
        'FEDE':"Federal",
        'PULO':"Local government",
        'PRIV':"Private-individual",
        'CORP':"Private-corporate-for profit",
        'CONP':"Private-corporate-nonprofit",
        'FORE':"Foreign",
        'NAAM':"Native American",
        'MULT':"Multiple categories of ownership",
        'UNSP':"Unspecified by surveyor",
        'PUUN':"Public-unspecified",
        'PRUN':"Private-unspecified",
        'OTHR':"Other",
        'UNKN':"Unknown"
    }

    ownership = {}
    ct = 0
    with open(csv_path,'rb') as f:
        reader = csv.reader(f)
        reader.next()
        for i in reader:
            siteid = i[0].rstrip()
            code = i[1].upper().rstrip()
            try:
                ownership[siteid].append(lookup[code])
            except:
                ownership[siteid] = [lookup[code]]
            ct+=1

    ct = 0
    for k,v in ownership.iteritems():
        if len(v) > 1:
            ct+=1
    AddMessage(" -- {} total sites with ownership data".format(len(ownership)))
    AddMessage(" -- {} site ids have multiple ownership values".format(ct))
    
    print "    done"
    return ownership

def process_shapefile(shp_path,owner_data):

    fl = "fl"
    MakeFeatureLayer(shp_path,fl)
    if not "OWNERSHIP" in [f.name for f in ListFields(fl)]:
        AddField(fl,"OWNERSHIP","TEXT",field_length=50)
    fl_ct = int(GetCount(fl)[0])
    AddMessage("{} features in {}".format(fl_ct,os.path.basename(shp_path)))
    own_ct = 0
    with UpdateCursor(fl,["SITEID","OWNERSHIP"]) as cursor:
        for row in cursor:
            try:
                ownership = owner_data[row[0]]
            except KeyError:
                continue
            if not ownership:
                continue
            row[1] = ownership[0]
            own_ct+=1
            cursor.updateRow(row)
    AddMessage("   >> {} record updated".format(own_ct))
    
def add_ownership_values(csv_path,shp_dir):

    AddMessage("\n"+"-"*80+"\nADDING OWNERSHIP DATA\n")

    ownership_data = get_ownership_dict(csv_path)

    for f in os.listdir(shp_dir):
        if not f.endswith(".shp"):
            continue
        shp = os.path.join(shp_dir,f)
        process_shapefile(shp,ownership_data)