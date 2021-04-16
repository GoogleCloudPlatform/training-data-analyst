# Covertype Data Set

This dataset is based on **Covertype Data Set** from UCI Machine Learning Repository

https://archive.ics.uci.edu/ml/datasets/covertype

## Schema

The original dataset has been modified to conform to the following schema:

Column Name | Data Type | Feature Type | Data Domain | Description
------------|-----------|--------------|-------------|------------
Elevation | Integer | Quantitative | meters |  Elevation in meters
Aspect | Integer  | Quantitative | azimuth |  Aspect in degrees azimuth
Slope | Integer | Quantitative | degress | Slop in degress
Horizontal_Distance_To_Hydrology | Integer  | Quantitative | meters | Horizontal distance to nearest surface water features
Vertical_Distance_To_Hydrology | Integer  | Quantitative | meters | Vertical distance to nearest surface water features
Horizontal_Distance_To_Roadways | Integer  | Quantitative | meters | Horizontal distance to nearest roadway
Hillshade_9am | Integer  | Quantitative | 0 to 255 index |  Hillshade index at 9am, summer solstice
Hillshade_Noon | Integer  | Quantitative | 0 to 255 index |  Hillshade index at noon, summer soltice
Hillshade_3pm | Integer  | Quantitative | 0 to 255 index |  Hillshade index at 3pm, summer solstice
Horizontal_Distance_To_Fire_Points | Integer  | Quantitative | meters | Horizontal distance to nearest wildfire ignition points
Wilderness_Area | String | Categorical | Text codes |  Wilderness area designation - refer to the below table for code designations
Soil_Type | Integer | Categorical | Integer codes | Soil Type designation - refer to the below table for code designations
Cover_Type | Integer | Categorical | Integer codes | Forest Cover Type designation - refer to the below table for code designations

### Wilderness Area Code designations

Code | Wilderness Area 
----------------|-----
Rawah | Rawah Wilderness Area 
Neota | Neota Wilderness Area 
Comanche | Comanche Peak Wilderness Area 
Cache | Cache la Poudre Wilderness Area


    
### Soil Type Code designations

 ELU Code | Description
----------|------------
 2702|Cathedral family - Rock outcrop complex, extremely stony.
 2703|Vanet - Ratake families complex, very stony.
 2704|Haploborolis - Rock outcrop complex, rubbly.
 2705|Ratake family - Rock outcrop complex, rubbly.
 2706|Vanet family - Rock outcrop complex complex, rubbly.
 2717|Vanet - Wetmore families - Rock outcrop complex, stony.
 3501|Gothic family.
 3502|Supervisor - Limber families complex.
 4201|Troutville family, very stony.
 4703|Bullwark - Catamount families - Rock outcrop complex, rubbly.
 4704|Bullwark - Catamount families - Rock land complex, rubbly.
 4744|Legault family - Rock land complex, stony.
 4758|Catamount family - Rock land - Bullwark family complex, rubbly.
 5101|Pachic Argiborolis - Aquolis complex.
 5151|unspecified in the USFS Soil and ELU Survey.
 6101|Cryaquolis - Cryoborolis complex.
 6102|Gateview family - Cryaquolis complex.
 6731|Rogert family, very stony.
 7101|Typic Cryaquolis - Borohemists complex.
 7102|Typic Cryaquepts - Typic Cryaquolls complex.
 7103|Typic Cryaquolls - Leighcan family, till substratum complex.
 7201|Leighcan family, till substratum, extremely bouldery.
 7202|Leighcan family, till substratum - Typic Cryaquolls complex.
 7700|Leighcan family, extremely stony.
 7701|Leighcan family, warm, extremely stony.
 7702|Granile - Catamount families complex, very stony.
 7709|Leighcan family, warm - Rock outcrop complex, extremely stony.
 7710|Leighcan family - Rock outcrop complex, extremely stony.
 7745|Como - Legault families complex, extremely stony.
 7746|Como family - Rock land - Legault family complex, extremely stony.
 7755|Leighcan - Catamount families complex, extremely stony.
 7756|Catamount family - Rock outcrop - Leighcan family complex, extremely stony.
 7757|Leighcan - Catamount families - Rock outcrop complex, extremely stony.
 7790|Cryorthents - Rock land complex, extremely stony.
 8703|Cryumbrepts - Rock outcrop - Cryaquepts complex.
 8707|Bross family - Rock land - Cryumbrepts complex, extremely stony.
 8708|Rock outcrop - Cryumbrepts - Cryorthents complex, extremely stony.
 8771|Leighcan - Moran families - Cryaquolls complex, extremely stony.
 8772|Moran family - Cryorthents - Leighcan family complex, extremely stony.
 8776|Moran family - Cryorthents - Rock land complex, extremely stony.

### Forest Cover Code designations (type classes)

Code | Description
-----|------------
0 | Spruce/Fir
1 | Lodgepole Pine
2 | Ponderosa Pine
3 | Cottonwood/Willow
4 | Aspen
5 | Douglas-fir
6 | Krummholz

## Data Splits

In addition to the full data split that contains all records from the original UCI file, the training, evaluation, testing and serving splits have been created.


All data set splits have been uploaded to the `gs://workshop-datasets/covertype` public GCS location.


