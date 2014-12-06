import arcpy
from arcpy import env
from arcpy.sa import *
env.workspace = "E:\School\Personal Drive\Fall2014\Python\Project\Data"
## Create new shape file using desired coordinates for dimensions
fc = "AOI.shp"
newfc= "Data/AOI.shp"
arcpy.CreateFeatureclass_management("E:\School\Personal Drive\Fall2014\Python\Project\Data", fc, "Polygon")
cursor = arcpy.da.InsertCursor(fc, ["SHAPE@"])
array = arcpy.Array()
## Predetermined coordinates of AOI [x,y] for each corner (bottom = b top=t left =1 right =r)
            #TL                          BL                         BR                         TR
coordlist =[[2366128.459, 1554637.73], [2366128.459, 1553228.128], [2367413.15, 1553228.128], [2367413.184, 1554637.73]]
for x, y in coordlist:
    point = arcpy.Point(x,y)
    array.append(point)
polygon = arcpy.Polygon(array)
cursor.insertRow([polygon])
del cursor

## Extract by mask Lake.tif by AOI
inRaster = "Lake.tif"
inMaskData = "AOI.shp"

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Execute ExtractByMask
outExtractByMask = ExtractByMask(inRaster, inMaskData)

# Save the output 
outExtractByMask.save("E:\School\Personal Drive\Fall2014\Python\Project\Data\extractmask_Lake.tif")

####IsoCluster tool

inRaster = "extractmask_Lake.tif"
classes = 6
minMembers = 20
sampInterval = 10

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Execute IsoCluster
outUnsupervised = IsoClusterUnsupervisedClassification(inRaster, classes, minMembers, sampInterval)
outUnsupervised.save("E:\School\Personal Drive\Fall2014\Python\Project\Data\UNSUP_ISO_CLUS_Lake.tif")

# Raster to Polygon tool
# Set local variables
inRaster = "UNSUP_ISO_CLUS_Lake.tif"
outPolygons = "E:\School\Personal Drive\Fall2014\Python\Project\Data\Polygons.shp"
field = "VALUE"

# Execute RasterToPolygon
arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "NO_SIMPLIFY", field)

#Extract by attribute tool
# Set local variables
inRaster = "UNSUP_ISO_CLUS_Lake.tif"
inSQLClause = "VALUE = 1"

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Execute ExtractByAttributes
attExtract = ExtractByAttributes(inRaster, inSQLClause) 

# Save the output 
attExtract.save("E:\School\Personal Drive\Fall2014\Python\Project\Data\WaterExtract.tif")

### Raster to Polygon tool for water extract file
### Set local variables
inRaster = "WaterExtract.tif"
outPolygons = "E:\School\Personal Drive\Fall2014\Python\Project\Data\WEXPolygon.shp"
field = "VALUE"
# Execute RasterToPolygon
arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "NO_SIMPLIFY", field)

## Create a new field
# Set local variables
inFeatures = "WEXPolygon.shp"
fieldName1 = "Area"
fieldPrecision = 15
fieldAlias = "refcode"
fieldName2 = "status"
fieldLength = 15
 
# Execute AddField for new field
arcpy.AddField_management(inFeatures, fieldName1, "FLOAT", fieldPrecision, "", "",
                          fieldAlias, "NULLABLE")
# Calculate Geometry of Area field with Calculate Field Tool
arcpy.CalculateField_management("WEXPolygon.shp", "Area", "!SHAPE.area!", "PYTHON_9.3")

#Select by attribute Area > 9 ft^2 due to this being the largest size of the wayward polygons
arcpy.MakeFeatureLayer_management("E:\School\Personal Drive\Fall2014\Python\Project\Data\WEXPolygon.shp", "shade_lyr")
##fieldDelimited = arcpy.ListFields("shade_lyr")
##print([field.name for field in fieldDelimited])
arcpy.SelectLayerByLocation_management ("shade_lyr", "intersect", "E:\School\Personal Drive\Fall2014\Python\Project\Data\WEXPolygon.shp",0,"new_selection")
arcpy.SelectLayerByAttribute_management("shade_lyr", "SUBSET_SELECTION", ' "AREA" > 9.0 ')
arcpy.CopyFeatures_management("shade_lyr", "Shade_water")


##Select By location to select shadow classes (2) in contact with Water classes (1)
#First, make a layer from the feature class
arcpy.MakeFeatureLayer_management("E:\School\Personal Drive\Fall2014\Python\Project\Data\Polygons.shp", "new_shade_lyr")

# Then add a selection to the layer based on location to features in another feature class 
arcpy.SelectLayerByLocation_management ("new_shade_lyr", "intersect", "E:\School\Personal Drive\Fall2014\Python\Project\Data\Shade_water.shp",0,"new_selection")

## Select by attribute from current selection
 ##Within selected features, further select  
arcpy.SelectLayerByAttribute_management("new_shade_lyr", "SUBSET_SELECTION", ' "GRIDCODE" = 1 OR "GRIDCODE" = 2 ')
 
## Write the selected features to a new featureclass
arcpy.CopyFeatures_management("new_shade_lyr", "Shade_water_Final")

####### Create a new field
# Set local variables
inFeatures = "Shade_water_Final.shp"
fieldName1 = "Area"
fieldPrecision = 15
fieldAlias = "refcode"
fieldName2 = "status"
fieldLength = 15

# Execute AddField for new field
arcpy.AddField_management(inFeatures, fieldName1, "FLOAT", fieldPrecision, "", "",
                          fieldAlias, "NULLABLE")
#Calculate Geometry of Area field with Calculate Field Tool
arcpy.CalculateField_management("Shade_water_Final.shp", "Area", "!SHAPE.area!", "PYTHON_9.3")

#Select by attribute Area >1300  ft^2 due to this being the largest size of the wayward polygons
arcpy.MakeFeatureLayer_management("E:\School\Personal Drive\Fall2014\Python\Project\Data\Shade_water_Final.shp", "sw_lyr")
arcpy.SelectLayerByLocation_management ("sw_lyr", "intersect", "E:\School\Personal Drive\Fall2014\Python\Project\Data\Shade_Water_Final.shp",0,"new_selection")
arcpy.SelectLayerByAttribute_management("sw_lyr", "SUBSET_SELECTION", ' "AREA" >= 1300 ')
arcpy.CopyFeatures_management("sw_lyr", "SWFinal")

## Dissolve Tool to Create final Output file
arcpy.Dissolve_management("SWFinal.shp", "E:\School\Personal Drive\Fall2014\Python\Project\Data\SWFinal_Dissolved.shp",
                          ["GRIDCODE"], "", "MULTI_PART", 
                          "DISSOLVE_LINES")
