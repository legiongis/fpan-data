import os
import csv
from arcpy import (
    env,
    AddMessage,
    ListFields,
)
from arcpy.management import (
    GetCount,
    Delete,
    CopyFeatures,
    SelectLayerByAttribute,
    SelectLayerByLocation,
    MakeFeatureLayer,
    MakeTableView,
    DeleteFeatures,
    AddField,
)
from arcpy.da import (
    SearchCursor,
)

def filter_structures(shp_dir,out_dir):

    AddMessage("\n"+"-"*80+"\nPROCESSING STRUCTURES\n")
    
    shp_path = os.path.join(shp_dir,"FloridaStructures.shp")

    ## make structures layer
    struct_lyr = "struct_lyr"
    MakeFeatureLayer(shp_path,struct_lyr)
    AddMessage("{} input structures".format(GetCount(struct_lyr)[0]))
    AddMessage("filters:")
    
    ## select all that are lighthouses based on structure use fields
    lh_clause = "\"STRUCUSE1\" = 'Lighthouse' OR "\
                "\"STRUCUSE2\" = 'Lighthouse' OR "\
                "\"STRUCUSE3\" = 'Lighthouse'"
    SelectLayerByAttribute(struct_lyr, "NEW_SELECTION", lh_clause)
    lh_ct = int(GetCount(struct_lyr)[0])
    AddMessage(" -- {} are lighthouses".format(lh_ct))
    
    ## make layer of state park boundaries
    sp_lyr = "sp_lyr"
    MakeFeatureLayer(r"resources\AllPublicLandsFL.shp",sp_lyr)
    sp_clause = "\"MANAGING_A\" = 'FL Dept. of Environmental "\
        "Protection, Div. of Recreation and Parks'"
    SelectLayerByAttribute(sp_lyr, "NEW_SELECTION", sp_clause)

    ## select all structures on state parks, append to existing selection
    SelectLayerByLocation(struct_lyr,select_features=sp_lyr,selection_type="ADD_TO_SELECTION")
    sp_ct = int(GetCount(struct_lyr)[0]) - int(lh_ct)
    AddMessage(" -- {} structures in state parks".format(sp_ct))
    
    ## make layer of National Register district boundaries (use a predetermined set)
    nr_lyr = "nr_lyr"
    MakeFeatureLayer(r"resources\NR-Districts.shp",nr_lyr)

    ## select all structures in NR districts, append to output
    SelectLayerByLocation(struct_lyr,select_features=nr_lyr,selection_type="ADD_TO_SELECTION")
    nr_ct = int(GetCount(struct_lyr)[0]) - (lh_ct + sp_ct)
    AddMessage(" -- {} structures in the {} specified national register districts".format(nr_ct,GetCount(nr_lyr)[0]))
    
    ## remove from selection any structures that have been destroyed
    dest_clause = "\"DESTROYED\" = 'YES'"
    SelectLayerByAttribute(struct_lyr, "REMOVE_FROM_SELECTION", dest_clause)
    final_ct = int(GetCount(struct_lyr)[0])
    dest_ct = sum([lh_ct,sp_ct,nr_ct]) - final_ct
    AddMessage(" -- {} structures removed that were destroyed".format(dest_ct))

    ## copy final selection to output shapefile
    out_shp = os.path.join(out_dir,os.path.basename(shp_path))
    # out_shp = r"data\FloridaStructures.shp"
    CopyFeatures(struct_lyr,out_shp)
    AddMessage("{} output structures".format(GetCount(struct_lyr)[0]))
    AddMessage(r"   >> copied to {}".format(out_shp))
    
    return
    
def copy_cemeteries(shp_dir,out_dir):
    
    AddMessage("\n"+"-"*80+"\nPROCESSING CEMETERIES\n")
    
    shp_path = os.path.join(shp_dir,"HistoricalCemeteries.shp")
    
    ## make cemetery layer and copy the whole thing to the output location
    cem_lyr = "cem_lyr"
    MakeFeatureLayer(shp_path,cem_lyr)
    AddMessage("{} input cemeteries".format(GetCount(cem_lyr)[0]))
    AddMessage("no operations performed")
    # out_shp = r"data\HistoricalCemeteries.shp"
    out_shp = os.path.join(out_dir,os.path.basename(shp_path))
    CopyFeatures(cem_lyr,out_shp)
    AddMessage("{} output cemeteries".format(GetCount(cem_lyr)[0]))
    AddMessage(r"   >> copied to {}".format(out_shp))
    
    return
    
def split_archaelogical_sites(shp_dir,out_dir):
    
    AddMessage("\n"+"-"*80+"\nPROCESSING ARCHAEOLOGICAL SITES\n")
    
    shp_path = os.path.join(shp_dir,"FloridaSites.shp")
    arch_temp_path = os.path.join(out_dir,os.path.basename(shp_path))

    ## make layer from original data and copy to temp shapefile
    arch_orig_lyr = "arch_orig_lyr"
    MakeFeatureLayer(shp_path,arch_orig_lyr)
    # arch_temp_path = r"data\FloridaSites.shp"
    CopyFeatures(arch_orig_lyr,arch_temp_path)
    
    ## make new layer from the copied shapefile, use this from now on
    arch_lyr = "arch_lyr"
    MakeFeatureLayer(arch_temp_path,arch_lyr)
    AddMessage("{} input sites".format(GetCount(arch_lyr)[0]))
    AddMessage("sorting operations:")
    
    ## make layer of state park boundaries
    sp_lyr = "sp_lyr"
    MakeFeatureLayer(r"resources\AllPublicLandsFL.shp",sp_lyr)
    sp_clause = "\"MANAGING_A\" = 'FL Dept. of Environmental "\
        "Protection, Div. of Recreation and Parks'"
    SelectLayerByAttribute(sp_lyr, "NEW_SELECTION", sp_clause)

    ## select all sites in state parks, copy to new shapefile
    SelectLayerByLocation(arch_lyr,select_features=sp_lyr)
    sp_ct = int(GetCount(arch_lyr)[0])
    AddMessage(" {} sites in state parks".format(sp_ct))
    sp_out = arch_temp_path.replace(".shp","_StateParks.shp")
    CopyFeatures(arch_lyr,sp_out)
    AddMessage(r"   >> copied to {}".format(sp_out))
    
    ## delete that sites that were in state parks so they can't be reselected
    DeleteFeatures(arch_lyr)
    
    ## make layer of FPAN regions
    fpan_lyr = "fpan_lyr"
    MakeFeatureLayer(r"resources\FPAN-regions-expanded.shp",fpan_lyr)
    
    ## iterate region layer, select, copy, and delete sites in each region
    total = sp_ct
    sql=(None, 'ORDER BY region_cod ASC')
    with SearchCursor(fpan_lyr,["FID","name","region_cod"],sql_clause=sql) as cursor:
        for row in cursor:
            fid_clause = "\"FID\" = {}".format(row[0])
            SelectLayerByAttribute(fpan_lyr, "NEW_SELECTION", fid_clause)
            SelectLayerByLocation(arch_lyr,select_features=fpan_lyr)
            select_ct = int(GetCount(arch_lyr)[0])
            
            AddMessage(" {} sites in {} Region".format(select_ct,row[1]))
            
            out = arch_temp_path.replace(".shp","_{}.shp".format(row[1].replace(" ","")))
            CopyFeatures(arch_lyr,out)
            total+=select_ct
            AddMessage(r"   >> copied to {}".format(out))
            
            ## delete that sites that were in state parks so they can't be reselected
            DeleteFeatures(arch_lyr)
            
    Delete(arch_temp_path)
    AddMessage("{} output sites\n".format(total))
