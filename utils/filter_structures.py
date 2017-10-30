### largely taken from https://geoexamples.blogspot.com.br/2013/04/fast-tip-filtering-features-using-ogr.html
### thanks Roger Veciana i Rovira

from osgeo import ogr
from os.path import exists
from os.path import basename
from os.path import splitext
from os import remove
import os
import sys
import argparse
from datetime import datetime

def make_outfile_path(infile):
    '''makes an output path for the input file, and creates a new
    containing directory if necessary.'''
    
    dirname = "processed_"+datetime.today().strftime("%m%d%y")
    location = os.path.dirname(os.path.dirname(infile))
    
    newdir = os.path.join(location,dirname)
    
    if not exists(newdir):
        os.makedirs(newdir)
        
    outpath = os.path.join(newdir,os.path.basename(infile))
    
    return outpath
    

def extract(in_file, out_file,clip_shp=""):
    '''
    Opens the input file, copies it into the output file, allowing for
    feature-level filtering to take place.
    '''
    print "filtering input shapefile:", in_file
    print "output shapefile:", out_file
    print "   (this may take a few minutes...)"    
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( splitext(basename(in_file))[0] )
    if in_lyr is None:
        print "Error opening layer"
        sys.exit( 1 )

    ##Creating the output file, with its projection
    if exists(out_file):
        remove(out_file)
    driver_name = "ESRI Shapefile"
    drv = ogr.GetDriverByName( driver_name )
    if drv is None:
        print "%s driver not available.\n" % driver_name
        sys.exit( 1 )
    out_ds = drv.CreateDataSource( out_file )
    if out_ds is None:
        print "Creation of output file failed.\n"
        sys.exit( 1 )
    proj = in_lyr.GetSpatialRef()
    
    ##Creating the output layer with its fields
    out_lyr = out_ds.CreateLayer( 
        splitext(basename(out_file))[0], proj, ogr.wkbPoint )
    lyr_def = in_lyr.GetLayerDefn ()
    for i in range(lyr_def.GetFieldCount()):
        out_lyr.CreateField ( lyr_def.GetFieldDefn(i) )

    ## create the comparison layer with parks and districts in it
    # filter_shp = r"shp-ref\struct_filter.shp"
    if clip_shp:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        filter_shp_ds = driver.Open(clip_shp, 0)
        f_lyr = filter_shp_ds.GetLayer()
    
    ##Writing all the features
    in_lyr.ResetReading()
    total = in_lyr.GetFeatureCount()
    twentieth = total/20
    ct = 0
    for feat in in_lyr:

        ## mediocre progress bar
        ct+=1
        if ct % twentieth == 0: 
                print "#",
        if ct == total:
            print " 100%"

        match = False

        ## skip structures that have been destroyed
        if feat.GetFieldAsString(feat.GetFieldIndex('DESTROYED')) == "YES":
            continue

        ## test all of the structure use fields to see if lighthouse
        use_fields = ['STRUCUSE1','STRUCUSE2','STRUCUSE3']
        for usef in use_fields:
            use = feat.GetFieldAsString(feat.GetFieldIndex(usef))
            if use == "Lighthouse":
                match = True

        ## set spatial query on the filter poly shp to see if this feature
        ## intersects it
        geom = feat.GetGeometryRef()
        if clip_shp:
            f_lyr.SetSpatialFilter(geom)
            if f_lyr.GetFeatureCount() > 0:
                match = True

        if match:   
            out_lyr.CreateFeature(feat)

    in_ds = None
    out_ds = None
    filter_shp_ds = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input",help="input shapefile to be filter")
    parser.add_argument("--clip",help="shapefile to be used as a clip feature for a spatial filter")
    args = parser.parse_args()
    outfile = make_outfile_path(args.input)
    extract(args.input,outfile,clip_shp=args.clip)
