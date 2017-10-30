from osgeo import ogr
import os
import sys
import argparse
import uuid
import csv
from dateutil.parser import parse
from datetime import datetime

def parse_date(value,field_name):

    clean = ''.join(n for n in value if n.isdigit() or n in ['-','/','\\'])
    clean = clean.rstrip("-")
    if clean.rstrip() == "":
        return ""
    if len(clean) == 4:
        return "{}-01-01".format(clean)
    elif len(clean) > 4:
        try:
            d = parse(clean)
            return d.strftime("%Y-%m-%d")
        except:
            print "    couldn't parse this date:", clean, "("+field_name+")"
            return ""
    else:
        print "    couldn't parse this date:", clean, "("+field_name+")"
        return ""

def sanitize_row(feature,date_fields=[]):
    
    row =[]
    for i in range(feature.GetFieldCount()):
        name = feature.GetFieldDefnRef(i).GetName()
        val = feature.GetFieldAsString(name).rstrip()
        if val == "0":
            val = ""
        if name in date_fields:
            val = parse_date(val,name)
        row.append(val)
        
        
    return row

def shp_to_csv(in_file,truncate=0,date_fields=[]):
    '''
    converts a shapefile to a csv that is ready for arches upload
    '''
    print "~"*60
    print "converting shapefile to csv:", in_file
    out_file = in_file.replace(".shp",".csv")
    print "output csv:", out_file

    ## open shapefile for reading
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( os.path.splitext(os.path.basename(in_file))[0] )
    if in_lyr is None:
        print "Error opening layer"
        sys.exit( 1 )

    lyr_def = in_lyr.GetLayerDefn ()
    field_names = [lyr_def.GetFieldDefn(i).GetName() for i in range(lyr_def.GetFieldCount())]
    
    fields = ['ResourceID','geom']+field_names
    
    ct = 0
    with open(out_file,"wb") as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(fields)
        for n,feat in enumerate(in_lyr,1):
            ct+=1
            id = str(uuid.uuid4())
            geom = feat.GetGeometryRef().ExportToWkt()
            featrow = sanitize_row(feat,date_fields)
            row = [id]+[geom]+featrow
            writer.writerow(row)
            
            if truncate == n:
                break
    
    if truncate:
        print "    created test file with {} rows".format(ct)
    else:
        print "    created file with {} rows".format(ct)

    in_ds.Destroy()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir",help="input directory containing shapefiles to which ownership values will be added")
    parser.add_argument("-t","--truncate",type=int,help="make a truncated csv with only this many rows")
    args = parser.parse_args()
    
    date_fields = ["YEARESTAB","D_NRLISTED"]
    
    dir = args.input_dir
    for shp in os.listdir(dir):
        if not shp.endswith(".shp"):
            continue
        shapefile = os.path.join(dir,shp)
        shp_to_csv(shapefile,truncate=args.truncate,date_fields=date_fields)
