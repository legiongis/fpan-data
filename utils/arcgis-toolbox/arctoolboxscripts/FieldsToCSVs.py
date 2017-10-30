import arcpy
import csv
import os

inputfile = arcpy.GetParameterAsText(0)
location = arcpy.GetParameterAsText(1)
fields = arcpy.GetParameter(2)

## make output directory for this dataset
dirname = os.path.splitext(os.path.basename(inputfile))[0]+"_lists"
outdir = os.path.join(location,dirname)
if not os.path.isdir(outdir):
    os.makedirs(outdir)

## collect all data to a single dictionary
dict = {}
for f in fields:
    dict[f] = []
    
rows = arcpy.da.SearchCursor(inputfile,fields)
for row in rows:
    for i,name in enumerate(fields):
        if row[i] == "":
            continue
        dict[fields[i]].append(row[i])

## write out all lists to individual CSV files
for k,v in dict.iteritems():
    vals = set(v)
    vals = [i for i in vals]
    vals.sort()
    csvpath = os.path.join(outdir,k+".csv")
    with open(csvpath,"wb") as csvfile:
        outcsv = csv.writer(csvfile)
        for val in vals:
            outcsv.writerow([val])