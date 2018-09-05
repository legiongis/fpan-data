import os
import csv
from arcpy import (
    env,
    AddMessage,
    ListFields,
    GetParameterAsText,
)
from arcpy.management import (
    GetCount,
    Delete,
    CopyFeatures,
    SelectLayerByAttribute,
    SelectLayerByLocation,
    MakeFeatureLayer,
    MakeTableView,
    DeleteFeatures,
    AddField,
)
from arcpy.da import (
    SearchCursor,
    UpdateCursor,
)

env.overwriteOutput = True
    
class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "HMS Tools"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [
            ProcessFMSFData,
            AddOwnershipValues,
            AddLocationAttributes,
            RepairGeometry,
            ConvertToCSV,
            SplitErrorsFromCSVs,
        ]


class ProcessFMSFData(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "1. Process FMSF Shapefiles"
        self.description = "performs preprocessing on the shapefiles that come"\
            " straight from FMSF"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="FMSF Shapefile Directory",
            name="data_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"input_fmsf")
        param1 = arcpy.Parameter(
            displayName="Output Directory",
            name="out_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param1.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"processing_shp")
        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        import scripts.fmsf_processing
        scripts.fmsf_processing = reload(scripts.fmsf_processing)
        from scripts.fmsf_processing import (
            filter_structures,
            copy_cemeteries,
            split_archaelogical_sites,
        )
        
        shp_dir = parameters[0].valueAsText
        out_dir = parameters[1].valueAsText
        
        filter_structures(shp_dir,out_dir)
        copy_cemeteries(shp_dir,out_dir)
        split_archaelogical_sites(shp_dir,out_dir)
        
        return
        
class AddOwnershipValues(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2. Add Ownership Values"
        self.description = "adds ownership information to the shapefiles"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Shapefiles Directory",
            name="out_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"processing_shp")
        param1 = arcpy.Parameter(
            displayName="OwnType CSV",
            name="owner_csv",
            datatype="DETextfile",
            parameterType="Required",
            direction="Input"
        )
        
        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        import scripts.ownership_values
        scripts.ownership_values = reload(scripts.ownership_values)
        from scripts.ownership_values import (
            add_ownership_values,
        )
        
        shp_dir = parameters[0].valueAsText
        csv_path = parameters[1].valueAsText
        add_ownership_values(csv_path,shp_dir)
        
        return
        
class AddLocationAttributes(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3. Add Location Attributes"
        self.description = "adds managing area name, managing agency,"\
        "managing agency category, and FPAN region name"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Shapefile Directory",
            name="data_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"processing_shp")
        params = [param0]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        import scripts.add_agency_and_region_info
        scripts.add_agency_and_region_info = reload(scripts.add_agency_and_region_info)
        from scripts.add_agency_and_region_info import (
            add_attributes_to_shp,
        )
        
        shp_dir = parameters[0].valueAsText
        
        for f in os.listdir(shp_dir):
            if not f.endswith(".shp"):
                continue
            add_attributes_to_shp(os.path.join(shp_dir,f))
        
        return
        
class RepairGeometry(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4. Repair Geometry"
        self.description = "checks and repairs geometry on the input shapefiles"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Shapefile Directory",
            name="data_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"processing_shp")
        params = [param0]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import scripts.conversion
        scripts.conversion = reload(scripts.conversion)
        from scripts.conversion import check_geometry
        
        datadir = parameters[0].valueAsText
        
        for f in os.listdir(datadir):
            if not f.endswith(".shp"):
                continue
            shp = os.path.join(datadir,f)
            check_geometry(shp)
            
        return

        
class ConvertToCSV(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "5. Convert To CSV"
        self.description = "converts the input shapefiles into CSVs for upload to Arches"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Shapefile Directory",
            name="data_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"processing_shp")
        param1 = arcpy.Parameter(
            displayName="Output CSV Directory",
            name="output_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param1.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"output_csv")
        param2 = arcpy.Parameter(
            displayName="Input CSV of existing UUIDs/SiteIDs",
            name="uuid_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input"
        )
        param2.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"resources\\uuid_x_siteid.csv")
        param3 = arcpy.Parameter(
            displayName="Truncate",
            name="truncate",
            datatype="Long",
            parameterType="Optional",
            direction="Input"
        )
        params = [param0,param1,param2,param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        import scripts.convert_shp_to_csv
        scripts.convert_shp_to_csv = reload(scripts.convert_shp_to_csv)
        from scripts.convert_shp_to_csv import shp_to_csv

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

        shp_dir = parameters[0].valueAsText
        csv_dir = parameters[1].valueAsText
        uuid_file = parameters[2].valueAsText
        if parameters[3].valueAsText:
            truncate = int(parameters[3].valueAsText)
        else:
            truncate = ""

        for f in os.listdir(shp_dir):

            if not f.endswith(".shp"):
                continue
            if f.startswith("FloridaSites"):
                concat = site_concat
            elif f == "FloridaStructures.shp":
                concat = struct_concat
            elif f =="HistoricalCemeteries.shp":
                concat = cem_concat
            else:
                concat = {}

            path = os.path.join(shp_dir,f)

            shp_to_csv(
                path,
                out_dir=csv_dir,
                truncate=truncate,
                date_fields=date_fields,
                concat_fields=concat,
                uuid_file=uuid_file
            )

        return

class SplitErrorsFromCSVs(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "6. Split Errors From CSVs"
        self.description = "creates a _good and _bad csv for each input"\
            "based on uuids that have been collected ahead of time"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="CSV Directory",
            name="data_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param0.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"output_csv")
        param1 = arcpy.Parameter(
            displayName="Input CSV of errored resources to split off",
            name="uuid_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input"
        )
        # param1.value = os.path.join(os.path.dirname(os.path.realpath(__file__)),"resources\\uuid_x_siteid.csv")
        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        import scripts.split_error_resources
        scripts.split_error_resources = reload(scripts.split_error_resources)
        from scripts.split_error_resources import (
            split_csv,
        )
        
        csv_dir = parameters[0].valueAsText
        error_log_list = parameters[1].valueAsText
        
        for f in os.listdir(csv_dir):
            if not f.endswith(".csv"):
                continue
            if f.endswith("good.csv") or f.endswith("bad.csv"):
                continue
            csvpath = os.path.join(csv_dir,f)
            split_csv(csvpath,error_log_list)
        return