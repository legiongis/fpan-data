import csv
import os
import json

error_log_list = r"C:\arches\fpan\logs\FPANArchSite_geometry_load_errors.csv"

error_uuids = {}
with open(error_log_list,'rb') as opencsv:
    reader = csv.reader(opencsv)
    reader.next()
    for row in reader:
        error_uuids[row[0]] = row[1]

filelist = [
    "FloridaSites_Central.csv",
    "FloridaSites_EastCentral.csv",
    "FloridaSites_NorthCentral.csv",
    "FloridaSites_Northwest.csv",
    "FloridaSites_Northeast.csv",
    "FloridaSites_Southeast.csv",
    "FloridaSites_Southwest.csv",
    "FloridaSites_StateParks.csv",
    "FloridaSites_WestCentral.csv",
    "FloridaStructures.csv",
    "HistoricalCemeteries.csv",
]
outrows = []
ddir = r"C:\arches\fpan\data\tools\data"
for f in os.listdir(ddir):
    
    if not f in filelist:
        continue
    path = os.path.join(ddir,f)
    with open(path,"rb") as csvopen:
        reader = csv.reader(csvopen)
        reader.next()
        for row in reader:
            uuid = row[0]
            siteid = row[2]
            
            try:
                error_uuids[uuid]
                loaded = False
            except KeyError:
                loaded = True
                
            outrows.append([uuid,siteid,f,loaded])
            
with open('output.csv', 'wb') as outopen:
    writer = csv.writer(outopen)
    writer.writerow(['ResourceID','SiteID','FileName','Loaded'])
    for row in outrows:
        writer.writerow(row)