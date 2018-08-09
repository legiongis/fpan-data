import csv
import os
import json

def split_csv(csvfile,error_log_list):

    error_uuids = []
    with open(error_log_list,'rU') as opencsv:
        reader = csv.reader(opencsv)
        reader.next()
        for row in reader:
            error_uuids.append(row[0])

    # siteid_qrys = {}
    badrows = []
    goodrows = []
    # siteid_qrys[f] = {}
    with open(csvfile,"rU") as openfile:
        reader = csv.reader(openfile)
        headers = reader.next()
        
        badrows.append(headers)
        goodrows.append(headers)
        
        uuid_field = headers.index("ResourceID")
        siteid_field = headers.index("SITEID")

        for row in reader:
            uuid = row[uuid_field]
            if uuid in error_uuids:
                badrows.append(row)
                # siteid_qrys[f][uuid] = row[siteid_field]
            else:
                goodrows.append(row)

    good_ct = len(goodrows)-1
    print "{} good resources".format(good_ct)
    if goodrows:
        goodfilename = csvfile.replace(".csv","_good.csv")
        with open(goodfilename,"wb") as outfile:
            writer = csv.writer(outfile)
            for row in goodrows:
                writer.writerow(row)
        print "   saved to {}".format(os.path.basename(goodfilename))

    bad_ct = len(badrows)-1
    print "{} bad resources".format(bad_ct)
    if bad_ct:
        badfilename = csvfile.replace(".csv","_bad.csv")
        with open(badfilename,"wb") as outfile:
            writer = csv.writer(outfile)
            for row in badrows:
                writer.writerow(row)
        print "   saved to {}".format(os.path.basename(badfilename))
            
# print json.dumps(siteid_qrys,indent=1)
# for k,v in siteid_qrys.iteritems():
    # if not v:
        # continue
    # print k
    # print "\"SITEID\" IN ('{}')".format("','".join(v.values()))