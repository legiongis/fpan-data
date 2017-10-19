import os
import uuid
import csv

indir = "examplecsvs"
outdir = os.path.join(indir,"csvswithuuids")


def addUUIDColumn(csv_file,outdir,header_row=False):

    filename = os.path.basename(csv_file)
    outfile = os.path.join(outdir,filename)

    print filename

    outrows = []
    with open(csv_file,'rb') as csvopen:
        reader = csv.reader(csvopen)
        if header_row:
            headers = reader.next()
            if headers[-1] == "UUID":
                print "  UUIDs already present in this file"
                return
            headers.append("UUID")
            outrows.append(headers)
            
        for row in reader:
            try:
                uuid.UUID(row[-1])
                print "  UUIDs already present in this file"
                return
            except:
                pass
            row.append(str(uuid.uuid4()))
            outrows.append(row)
    
    with open(outfile,'wb') as csvout:
        writer = csv.writer(csvout)
        for row in outrows:
            writer.writerow(row)

    print "  done"

if not os.path.isdir(outdir):
    os.makedirs(outdir)

for f in [i for i in os.listdir(indir) if i.endswith(".csv")]:
    addUUIDColumn(os.path.join(indir,f),outdir)


    
