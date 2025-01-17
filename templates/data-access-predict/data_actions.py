"""
This file contains the @predict actions that are part of the action package, amd will be
available for the agents to use. Each predict showcases a different model and the required
parameters for the model.

TIP! Try running predics in the SDK before publishing them to the agent!
"""

from typing import Optional
from sema4ai.actions import Response
from sema4ai.data import predict
from data_sources import HouseSalesModelDataSource, CustomerClassificationModelDataSource, EnergyConsumptionModelDataSource

@predict
def predict_energy_consumption(
    datasource: EnergyConsumptionModelDataSource,
    building_type: Optional[str] = None,
    square_footage: Optional[int] = None,
    number_of_occupants: Optional[int] = None,
    appliances_used: Optional[int] = None,
    average_temperature: Optional[int] = None,
    day_of_week: Optional[str] = None
) -> Response[str]:
    """
    Use linear regression to predict the energy consumption of a property based on given parameters. All parameters are optional - the prediction will be made based on provided values.

    Args:
        building_type: Type of the building, must be one of these: "Residential", "Industrial" or "Commercial"
        square_footage: Size of the property in square feet, numeric value like 15000
        number_of_occupants: Number of occupants in the property, a numeric value like 2
        appliances_used: Number of appliances in use in the property, a numeric value like 5
        average_temperature: Average temperature during the period in Celsius, like 15
        day_of_week: Defines if prediction is for weekday or weekend, possible values: "Weekday" or "Weekend"

    Returns:
        The result of the query execution.
    """
    # First we define the base query that will be used to predict the energy consumption.
    base_query = """
    SELECT 
        energy_consumption, 
        json_extract(energy_consumption_explain, '$.confidence') AS confidence 
    FROM 
        `models`.energy_consumption_model
    """

    conditions = []
    params = {}

    # Then we add the conditions to the query if the parameters are not None.
    if building_type is not None:
        conditions.append("building_type = $building_type")
        params['building_type'] = building_type
    
    if square_footage is not None:
        conditions.append("square_footage = $square_footage")
        params['square_footage'] = square_footage
    
    if number_of_occupants is not None:
        conditions.append("number_of_occupants = $number_of_occupants")
        params['number_of_occupants'] = number_of_occupants
    
    if appliances_used is not None:
        conditions.append("appliances_used = $appliances_used")
        params['appliances_used'] = appliances_used
    
    if average_temperature is not None:
        conditions.append("average_temperature = $average_temperature")
        params['average_temperature'] = average_temperature
    
    if day_of_week is not None:
        conditions.append("day_of_week = $day_of_week")
        params['day_of_week'] = day_of_week

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    # Finally we execute the query and return the result.
    result = datasource.query(base_query, params)
    return Response(result=result.to_markdown())

@predict
def predict_customer_segment(
    datasource: CustomerClassificationModelDataSource,
    gender: str,
    ever_married: str,
    age: int,
    graduated: str
) -> Response[str]:
    """
    Predicts the customer segment with given parameters. Segments are denoted by letter A to D.

    Args:
        gender: Gender of the customer, one of "Male" or "Female
        ever_married: If the customer has ever been married, one of "Yes" or "No"
        age: Age of the customer at the time of segmentation, numeric value
        graduated: If the customer has graduated, one of "Yes" or "No"

    Returns:
        The result of the query execution.
    """
    query = """
    SELECT 
        Segmentation, 
        json_extract(Segmentation_explain, '$.confidence') AS confidence 
    FROM 
        `models`.customer_classification_model 
    WHERE 
        Gender = $gender 
        AND Ever_Married = $ever_married 
        AND Age = $age 
        AND Graduated = $graduated
    """

    params = {'gender': gender,'ever_married': ever_married,'age': age,'graduated': graduated}

    result = datasource.query(query, params)
    return Response(result=result.to_markdown())

@predict
def predict_house_price(
    datasource: HouseSalesModelDataSource,
    type: str,
    beds: int
) -> Response[str]:
    """
    Predicts the house price based on median values of properties per quarter.

    Args:
        type: Type of the property, one of "house" or "unit".
        beds: How many bedrooms the property has. Numeric value between 1-5.

    Returns:
        The result of the query execution.
    """
    query = """
    SELECT 
        m.saledate AS `date`, 
        m.MA AS forecast 
    FROM 
        `models`.house_sales_model AS m 
    JOIN 
        files.house_sales AS t 
    WHERE 
        t.saledate > LATEST 
        AND t.type = $type 
        AND t.bedrooms = $beds 
    LIMIT 
        4
    """

    params = {'type': type,'beds': beds}

    result = datasource.query(query, params)
    return Response(result=result.to_markdown())
