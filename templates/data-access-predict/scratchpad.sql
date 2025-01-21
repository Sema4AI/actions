/*
You can use .sql files to develop your queries amd models. It's an eaasy way to iterate before creating
the actual models amd named queries. This example showcases the two types of models that are supported
by the Sema4.ai Data Access. For each model, you will find the model creation query, describe and DROP
queries, as well as a query to use the model to predict the target.

/*
*****************************************************
LINEAR REGRESSION
*****************************************************
 
This example uses the energy consumption data to predict the energy consumption of a building.
The data is stored in a CSV file and is loaded into a table called energy_consumption.

Dataset source: https://www.kaggle.com/datasets/govindaramsriram/energy-consumption-dataset-linear-regression
*/

SELECT * FROM files.energy_consumption;

-- The model is created using the lightwood engine with the prediction target being energy_consumption.
CREATE MODEL models.energy_consumption_model
FROM files
(SELECT * FROM energy_consumption)
PREDICT energy_consumption
USING engine = 'lightwood';

-- You can check the status of the model and see the model's performance with the following query:
DESCRIBE MODEL models.energy_consumption_model;

-- Here's a query to drop the model if you need to start over.
DROP MODEL IF EXISTS models.energy_consumption_model;

-- To use the model to predict the energy consumption of a building, you can use the following query:
SELECT energy_consumption, JSON_EXTRACT(energy_consumption_explain, '$.confidence') as confidence
FROM models.energy_consumption_model
WHERE building_type = 'Residential' -- Residential, Commercial or Industrial
AND square_footage = 20000
AND number_of_occupants = 1
AND appliances_used = 2
AND average_temperature = 10
AND day_of_week = 'Weekday'; -- Weekday or Weekend


/*
*****************************************************
TIMESERIES - FORECASTING
*****************************************************

This example uses the house price data where data is collected quarterly and
represented by the median price in the period (MA) for houses and units of various sizes.
The data is stored in a CSV file and is loaded into a table called house_sales.

Dataset source: https://www.kaggle.com/datasets/htagholdings/property-sales
*/

SELECT * FROM files.house_sales;

-- The model is created using the stats engine with the prediction target being median price in the period (MA).
CREATE MODEL models.house_sales_model
FROM files
(SELECT * FROM house_sales)
PREDICT MA
ORDER BY saledate
GROUP BY bedrooms, type
-- as the data is quarterly, look back two years to forecast the next one year
WINDOW 8
HORIZON 4
-- use the statsforecast engine for this model
USING engine = 'statsforecast';

DESCRIBE MODEL models.house_sales_model;
DROP MODEL IF EXISTS models.house_sales_model;

-- To use the model to predict the median price in the period (MA) for houses
-- and units of various sizes, you can use the following query:
SELECT m.saledate as date, m.MA as forecast
FROM models.house_sales_model as m
JOIN files.house_sales as t
WHERE t.saledate > LATEST
AND t.type = 'house'
AND t.bedrooms=2
LIMIT 4;