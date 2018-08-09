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

def sanitize_row(feature,date_fields=[],concat_fields={}):

    skip_fields = []
    for k,v in concat_fields.iteritems():
        skip_fields+=v

    row =[]
    concat_vals = {k:[] for (k,v) in concat_fields.iteritems()}
    for i in range(feature.GetFieldCount()):
        name = feature.GetFieldDefnRef(i).GetName()
        val = feature.GetFieldAsString(name).rstrip()
        if val == "0":
            val = ""
        if name in date_fields:
            val = parse_date(val,name)
            
        if not name in skip_fields:
            row.append(val)
            continue
            
        for k,v in concat_fields.iteritems():
            if name in v and not val == "":
                concat_vals[k].append(val)
                
    new_concat = concat_fields.keys()
    new_concat.sort()
    for nc in new_concat:
        row.append(";".join(concat_vals[nc]))

    return row

def shp_to_csv(in_file,truncate=0,date_fields=[],concat_fields={}):
    '''
    converts a shapefile to a csv that is ready for arches upload
    '''
    print "~"*60
    print "converting shapefile to csv:", in_file
    out_file = in_file.replace(".shp",".csv")
    if truncate:
        out_file = out_file.replace(".csv","_"+str(truncate)+".csv")
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
    for target,sources in concat_fields.iteritems():
        fields = [i for i in fields if not i in sources]
    fs = concat_fields.keys()
    fs.sort()
    fields+=fs
    
    ct = 0
    with open(out_file,"wb") as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(fields)
        for n,feat in enumerate(in_lyr,1):
            ct+=1
            id = str(uuid.uuid4())
            geom = feat.GetGeometryRef().ExportToWkt()
            featrow = sanitize_row(feat,date_fields,concat_fields=concat_fields)
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
    parser.add_argument("input",help="input directory containing shapefiles, or single shapefile input")
    parser.add_argument("-t","--truncate",type=int,help="make a truncated csv with only this many rows")
    args = parser.parse_args()
    
    date_fields = ["YEARESTAB","D_NRLISTED","YEARBUILT"]
    struct_concat = {
        'STRUCUSE':['STRUCUSE1','STRUCUSE2','STRUCUSE3'],
        'STRUCSYS':['STRUCSYS1','STRUCSYS2','STRUCSYS3'],
        'EXTFABRIC':['EXTFABRIC1','EXTFABRIC2','EXTFABRIC3','EXTFABRIC4']
    }
    cem_concat = {
        'CEMTYPE':['CEMTYPE1','CEMTYPE2'],
        'ETHNICGRP':['ETHNICGRP1','ETHNICGRP2','ETHNICGRP3','ETHNICGRP4']
    }
    site_concat = {
        'SITETYPE':['SITETYPE1','SITETYPE2','SITETYPE3','SITETYPE4','SITETYPE5','SITETYPE6'],
        'CULTURE':['CULTURE1','CULTURE2','CULTURE3','CULTURE4','CULTURE5','CULTURE6','CULTURE7','CULTURE8']
    }
    
    source = args.input
    if os.path.isdir(source):
        files = [os.path.join(source,i) for i in os.listdir(source)]
    else:
        if not os.path.isfile(source):
            print "non-existant file:", source
            exit()
        files = [os.path.abspath(source)]

    for path in files:
        filename = os.path.basename(path)
        if not filename.endswith(".shp"):
            continue
        if filename.startswith("FloridaSites"):
            concat = site_concat
        if filename == "FloridaStructures.shp":
            concat = struct_concat
        if filename =="HistoricalCemeteries.shp":
            concat = cem_concat
        shp_to_csv(path,truncate=args.truncate,date_fields=date_fields,concat_fields=concat)
        