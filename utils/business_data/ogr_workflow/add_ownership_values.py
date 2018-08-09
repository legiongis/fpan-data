from osgeo import ogr
import csv
import argparse
import os

def add_field_if_missing(layer,field_name):
    
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
    if not field_name in field_names:
        # Add a new field
        print "    adding ownership field"
        new_field = ogr.FieldDefn(field_name, ogr.OFTString)
        layer.CreateField(new_field)
    else:
        print "    ownership field already exists"
        
    return layer
    
def get_ownership_dict(csv_path):

    print "creating in memory lookup dictionary of ownership types..."

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

    print "    " +str(ct)+" rows processed"
    print "    " +str(len(ownership))+" unique site ids"
    ct = 0
    for k,v in ownership.iteritems():
        if len(v) > 1:
            ct+=1

    print "    " +str(ct)+" site ids have conflicting ownership values"
    
    print "    done"
    return ownership
    
def add_ownership_attribute(layer,owner_dict={}):
    
    layer.ResetReading()
    ct=0
    for feat in layer:
        ct+=1
        siteid = feat.GetFieldAsString("SITEID")
        try:
            ownership = owner_dict[siteid][0]
        except:
            continue

        feat.SetField("OWNERSHIP",ownership)
        layer.SetFeature(feat)
    print "    "+str(ct)+" features processed"
    return layer
    
def process_shapefile(shapefile_path,ownership_dict):
    
    print "processing "+shapefile_path
    
    # Open a Shapefile make layer
    driver = ogr.GetDriverByName("ESRI Shapefile")
    source = driver.Open(shapefile_path, 1)
    layer = source.GetLayer()

    layer = add_field_if_missing(layer,"OWNERSHIP")

    layer = add_ownership_attribute(layer,owner_dict=od)
    
    # Close the Shapefile
    source.Destroy()
    
    print "    done"
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir",help="input directory containing shapefiles to which ownership values will be added")
    parser.add_argument("ownership_file",help="csv file holding all of the ownership information")
    args = parser.parse_args()
    
    dir = args.input_dir
    od = get_ownership_dict(args.ownership_file)

    for shp in os.listdir(dir):
        if not shp.endswith(".shp"):
            continue
            
        shp_path = os.path.join(dir,shp)
        process_shapefile(shp_path,od)