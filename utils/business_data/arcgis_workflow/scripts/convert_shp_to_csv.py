# from osgeo import ogr
import os
import sys
import argparse
import uuid
import csv
from dateutil.parser import parse
from datetime import datetime
from arcpy import (
    AddMessage,
    ListFields,
)
from arcpy.da import SearchCursor
from arcpy.management import (
    
    MakeFeatureLayer,
)

def parse_date(value):

    if isinstance(value,datetime):
        return value.strftime("%Y-%m-%d")

    # AddMessage(value)
    value = value.replace("00:00:00","")
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
            AddMessage("    couldn't parse this date: "+str(clean)+"wieoonarginaergn")
            return ""
    else:
        AddMessage("    couldn't parse this date: "+str(clean))
        return ""

def sanitize_row(inrow,date_fields=[],concat_fields={},field_lookup={}):

    skip_fields = []
    for k,v in concat_fields.iteritems():
        skip_fields+=v
        
    row =[]
    concat_vals = {k:[] for (k,v) in concat_fields.iteritems()}
    for field_num,val in enumerate(inrow):
        name = field_lookup[field_num]
        if name in date_fields:
            
            if val:
                val = parse_date(val)
            else:
                val = ""
        else:
            try:
                val = val.encode("utf-8").rstrip()
            except AttributeError:
                val = str(val).rstrip()
                AddMessage("error encoding in utf-8, casting to str()")
                AddMessage(val)
        
        if not val or val is None:
            val = ""

        ## this is a dataset specific operation!!!!
        if val == "0" and name == "SURVEYNUM":
            val = ""
        
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

def shp_to_csv(in_file,out_dir='',truncate=0,date_fields=[],concat_fields={},uuid_file=''):
    '''
    converts a shapefile to a csv that is ready for arches upload
    '''
    AddMessage("~"*60)
    AddMessage("converting shapefile to csv: "+in_file)
    # out_file = in_file.replace(".shp",".csv")
    out_file = os.path.join(out_dir,os.path.basename(in_file).replace(".shp",".csv"))
    if truncate:
        out_file = out_file.replace(".csv","_"+str(truncate)+".csv")
    AddMessage("output csv: "+out_file)

    ## make feature layer form input shapefile
    in_ds = "in_ds"
    MakeFeatureLayer(in_file,in_ds)

    ## create new list of field names
    shp_field_names = [f.name for f in ListFields(in_ds) if not f.required]
    shp_field_dict = {}
    for name in shp_field_names:
        shp_field_dict[shp_field_names.index(name)] = name
    fields = ['ResourceID','geom']+shp_field_names
    for target,sources in concat_fields.iteritems():
        fields = [i for i in fields if not i in sources]
    fs = concat_fields.keys()
    fs.sort()
    fields+=fs
    
    ## get uuid dictionary from input csv
    uuid_dict = {}
    if uuid_file:
        with open(uuid_file,"rb") as opencsv:
            reader = csv.reader(opencsv)
            reader.next()
            for row in reader:
                uuid_dict[row[1]] = row[0]
    
    ct = 0
    with open(out_file,"wb") as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(fields)
        cursor_fields = ["SHAPE@WKT"]+shp_field_names
        siteid_i = cursor_fields.index('SITEID')
        if not siteid_i:
            raise Exception("can't find site id field")
        with SearchCursor(in_ds,cursor_fields) as cursor:
            for row in cursor:
                siteid = row[siteid_i]
                try:
                    id = uuid_dict[siteid]
                except KeyError:
                    id = str(uuid.uuid4())
                    AddMessage("need to generate new UUID for "+siteid)
                row = list(row)
                geom = row.pop(0)
                featrow = sanitize_row(row,
                    date_fields=date_fields,
                    concat_fields=concat_fields,
                    field_lookup=shp_field_dict
                )
                outrow = [id]+[geom]+featrow
                writer.writerow(outrow)
            
                ct+=1
                if truncate == ct:
                    break
    
    AddMessage("    created file with {} data rows".format(ct))
