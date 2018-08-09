### largely taken from https://geoexamples.blogspot.com.br/2013/04/fast-tip-filtering-features-using-ogr.html
### thanks Roger Veciana i Rovira!!

from osgeo import ogr
from os.path import exists
from os.path import basename
from os.path import splitext
from os import remove
import os
import sys
import argparse
from datetime import datetime

def create_output_layer(in_file,out_file=""):

    ## open the input file
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( splitext(basename(in_file))[0] )
    if in_lyr is None:
        print "Error opening layer"
        sys.exit( 1 )
    
    ##Creating the output file (empty), with its projection
    if out_file:
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
            
    return out_lyr

def make_outdir_path():
    '''makes an output directory for the processing'''
    
    dirname = "fmsf-migration\\processed_"+datetime.today().strftime("%m%d%y_%H%M")
    
    if not exists(dirname):
        os.makedirs(dirname)

    return dirname

def make_outfile_path(outdir,infile):
    '''makes an output path for the input file inside of the provided dir'''

    outpath = os.path.join(outdir,os.path.basename(infile))
    
    return outpath

def filter_structures(in_file, output_directory="",state_parks_layer=""):
    '''
    Opens the input file, copies it into the output file, allowing for
    feature-level filtering to take place.
    '''
    
    out_file = make_outfile_path(output_directory,in_file)
    
    print "~~~ FILTERING STRUCTURES ~~~"
    print "input:", in_file
    print "output:", out_file
    print "---"
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( splitext(basename(in_file))[0] )
    if in_lyr is None:
        print "Error opening layer"
        sys.exit( 1 )
        
    print in_lyr.GetFeatureCount()

    ##Creating the output file (empty), with its projection
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

    ## SPATIAL FILTERING PREPARATION
    
    ## national register district shapefile filter
    driver = ogr.GetDriverByName("ESRI Shapefile")
    nr_shp_ds = driver.Open("resources\\NR-Districts.shp", 0)
    nr_lyr = nr_shp_ds.GetLayer()
    
    ##iterate all features and filter
    in_lyr.ResetReading()
    total = in_lyr.GetFeatureCount()
    twentieth = total/20
    ct = 0
    out_ct = 0
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
                match = "Lighthouse"

        ## set spatial query on the filter poly shp to see if this feature
        ## intersects it
        geom = feat.GetGeometryRef()

        nr_lyr.SetSpatialFilter(geom)
        if nr_lyr.GetFeatureCount() > 0:
            match = "NR-Districts"
            
        state_parks_layer.SetSpatialFilter(geom)
        if state_parks_layer.GetFeatureCount() > 0:
            match = "State Park"

        if match:
            out_ct+=1
            out_lyr.CreateFeature(feat)

    print out_ct
    
    in_ds = None
    out_ds = None
    filter_shp_ds = None
    
def filter_sites(in_file, output_directory="",area_layers={}):

    out_file = make_outfile_path(output_directory,in_file)
    
    print "~~~ FILTERING ARCHAEOLOGICAL SITES ~~~"
    print "input:", in_file
    print "---"
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( splitext(basename(in_file))[0] )
    if in_lyr is None:
        print "Error opening layer"
        sys.exit( 1 )
        
    print in_lyr.GetFeatureCount()
    
    ##Creating the output file (empty), with its projection
    sp_output = create_output_layer(in_file,out_file=out_file.replace(".shp","_sp.shp"))
    sf_output = create_output_layer(in_file,out_file=out_file.replace(".shp","_sf.shp"))
    fwcc_output = create_output_layer(in_file,out_file=out_file.replace(".shp","_fwcc.shp"))
    aq_output = create_output_layer(in_file,out_file=out_file.replace(".shp","_aq.shp"))
    other_output = create_output_layer(in_file,out_file=out_file)
    
    sp_geoms = ogr.Geometry(ogr.wkbMultiPolygon)
    
    for feat in area_layers['sp']:
        try:
            sp_geoms.AddGeometry(feat.GetGeometryRef())
        except Exception as e:
            print e
    in_lyr.SetSpatialFilter(sp_geoms)
    print in_lyr.GetFeatureCount(), "in state parks"
    # in_lyr.SetSpatialFilter(area_layers['sf'])
    # print in_lyr.GetFeatureCount(), "in state forests"
    # in_lyr.SetSpatialFilter(area_layers['fwcc'])
    # print in_lyr.GetFeatureCount(), "in fwcc units"
    # in_lyr.SetSpatialFilter(area_layers['aq'])
    # print in_lyr.GetFeatureCount(), "in aquatic preserves"
    # print in_lyr.GetFeatureCount(), "outside of the above categories"
    
    return
    ##iterate all features and filter
    in_lyr.ResetReading()
    total = in_lyr.GetFeatureCount()
    twentieth = total/20
    ct = 0
    out_ct = 0
    for feat in in_lyr:

    ## mediocre progress bar
        ct+=1
        print ct
        if ct % twentieth == 0: 
                print "#",
        if ct == total:
            print " 100%"

        geom = feat.GetGeometryRef()

        sp_lyr = area_layers['sp']
        sp_lyr.SetSpatialFilter(sp_geoms)
        if sp_lyr.GetFeatureCount() > 0:
            sp_output.CreateFeature(feat)
            continue
            
        sf_lyr = area_layers['sf']
        sf_lyr.SetSpatialFilter(geom)
        if sf_lyr.GetFeatureCount() > 0:
            sf_output.CreateFeature(feat)
            continue
            
        fwcc_lyr = area_layers['fwcc']
        fwcc_lyr.SetSpatialFilter(geom)
        if fwcc_lyr.GetFeatureCount() > 0:
            fwcc_output.CreateFeature(feat)
            continue
            
        aq_lyr = area_layers['aq']
        aq_lyr.SetSpatialFilter(geom)
        if aq_lyr.GetFeatureCount() > 0:
            aq_output.CreateFeature(feat)
            continue
            
        other_lyr = area_layers['other']
        other_lyr.SetSpatialFilter(geom)
        if other_lyr.GetFeatureCount() > 0:
            other_output.CreateFeature(feat)
            continue

    return

def filter_cemeteries(in_file, output_directory=""):
    print in_file
    in_ds = ogr.Open( in_file )
    if in_ds is None:
        print "Open failed.\n"
        sys.exit( 1 )
    in_lyr = in_ds.GetLayerByName( splitext(basename(in_file))[0] )
    print in_lyr.GetFeatureCount()
    return
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input",help="input directory with shapefiles")
    args = parser.parse_args()
    
    indir = args.input
    struct_file = os.path.join(indir,"FloridaStructures.shp")
    sites_file_name = os.path.join(indir,"FloridaSites.shp")
    cem_file_name = os.path.join(indir,"HistoricalCemeteries.shp")
    
    outdir = make_outdir_path()
    
    
    print "preparing public lands shapefiles"
    
    shpdir = os.path.join(outdir,"shp")
    if not exists(shpdir):
        os.makedirs(shpdir)
    
    public_lands = ogr.Open("resources\\AllPublicLandsFL.shp")
    pl_lyr = public_lands.GetLayer()

    outdriver=ogr.GetDriverByName('MEMORY')
    
    pl_lyr.SetAttributeFilter("\"MANAGING_A\" = 'FL Dept. of Environmental Protection, Div. of Recreation and Parks'")
    spds = outdriver.CreateDataSource('memData')
    sp_tmp = outdriver.Open('memData',1)
    sp_lyr = spds.CopyLayer(pl_lyr,'sp',['OVERWRITE=YES'])
    print sp_lyr.GetFeatureCount(), "state parks"

    pl_lyr.SetAttributeFilter("\"MANAGING_A\" = 'FL Dept. of Agriculture and Consumer Services, Florida Forest Service'")
    sfds = outdriver.CreateDataSource('memData')
    sf_tmp = outdriver.Open('memData',1)
    sf_lyr = sfds.CopyLayer(pl_lyr,'sf',['OVERWRITE=YES'])
    print sf_lyr.GetFeatureCount(), "state forests"
    
    pl_lyr.SetAttributeFilter("\"MANAGING_A\" = 'FL Fish and Wildlife Conservation Commission'")
    fwccds = outdriver.CreateDataSource('memData')
    fwcc_tmp = outdriver.Open('memData',1)
    fwcc_lyr = fwccds.CopyLayer(pl_lyr,'fwcc',['OVERWRITE=YES'])
    print fwcc_lyr.GetFeatureCount(), "fish and wildlife commission units"
    
    pl_lyr.SetAttributeFilter("\"MANAGING_A\" = 'FL Dept. of Environmental Protection, Florida Coastal Office'")
    aqds = outdriver.CreateDataSource('memData')
    aq_tmp = outdriver.Open('memData',1)
    aq_lyr = aqds.CopyLayer(pl_lyr,'aq',['OVERWRITE=YES'])
    print aq_lyr.GetFeatureCount(), "aquatic preserves"
    
    pl_lyr.SetAttributeFilter("\"MANAGING_A\" != 'FL Dept. of Environmental Protection, Div. of Recreation and Parks' AND \"MANAGING_A\" != 'FL Dept. of Agriculture and Consumer Services, Florida Forest Service' AND \"MANAGING_A\" != 'FL Fish and Wildlife Conservation Commission' AND \"MANAGING_A\" != 'FL Dept. of Environmental Protection, Florida Coastal Office'")
    otherds = outdriver.CreateDataSource('memData')
    other_tmp = outdriver.Open('memData',1)
    other_lyr = otherds.CopyLayer(pl_lyr,'other',['OVERWRITE=YES'])
    print other_lyr.GetFeatureCount(), "other public land areas"
    
    del pl_lyr
    
    area_layers = {
        'sp':sp_lyr,
        'sf':sf_lyr,
        'fwcc':fwcc_lyr,
        'aq':aq_lyr,
    }
    
    filter_structures(struct_file,output_directory=outdir,state_parks_layer=sp_lyr)
    # filter_sites(sites_file_name,output_directory=outdir,area_layers=area_layers)
    filter_cemeteries(cem_file_name,output_directory=outdir)
