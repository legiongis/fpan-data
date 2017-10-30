import os
import arcpy
import csv
import time
import uuid
import subprocess

def prepairGeometry(wkt,prepair_path):
    '''runs prepair on the input and returns the fixed polygon'''
    cmd = prepair_path+' --wkt "{}"'.format(wkt)
    try:
        prepaired_wkt = subprocess.check_output(cmd,shell=True)
    except:
        prepaired_wkt = None
    return prepaired_wkt
    
def hasHole(geom):
    parts = geom.partCount
    boundaries = geom.boundary().partCount
    if boundaries > parts:
        return True
    else:
        return False

dataset = arcpy.GetParameterAsText(0)
use_fields = arcpy.GetParameter(1)
output = arcpy.GetParameterAsText(2)
use_prepair = arcpy.GetParameter(3)
prepair_dir = arcpy.GetParameterAsText(4)

if use_prepair:
    prepair_exe = os.path.join(prepair_dir,"prepair.exe")

arcpy.AddMessage("Converting {} to CSV".format(os.path.basename(dataset)))
arcpy.AddMessage("Fields Included:")
arcpy.AddMessage(", ".join(use_fields))
arcpy.AddMessage("\nwriting output...")

starttime = time.time()

cursor_fields = ['SHAPE@','SHAPE@WKT']+use_fields
outfields = [u'ResourceID',u'geom']+use_fields

cursor = arcpy.da.SearchCursor(dataset,cursor_fields)

if os.path.exists(output):
    os.remove(output)

ct=0
with open(output,"wb") as csvfile:
    csvout = csv.writer(csvfile)
    csvout.writerow(outfields)
    for row in cursor:
        ct+=1
        
        ## some attempted geometry wrangling in an effort to make it ES-friendly
        shape = row[0]
        wkt = row[1]
        
        if use_prepair:
            if not hasHole(shape):
                wkt = prepairGeometry(wkt,prepair_exe)
        
        clean_row = [str(uuid.uuid4()),wkt]

        for ind,val in enumerate(row):
            ## skip first two items in the row (which are both geometries)
            if ind == 0 or ind == 1:
                continue
            if isinstance(val, (int, long)):
                clean_row.append(str(val))
            else:
                try:
                    clean_row.append(val.encode("utf-8"))
                except:
                    clean_row.append(str(val))
                
        try:
            csvout.writerow(clean_row)
        except:
            arcpy.AddMessage("error writing this row:")
            arcpy.AddMessage(row)
			
arcpy.AddMessage("    done.")
arcpy.AddMessage("\nseconds elapsed: "+str(round(time.time()-starttime,2)))