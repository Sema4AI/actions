/*
*****************************************************
CLASSIFICATION - DIY WITH OUR TUTORIAL!
*****************************************************

This example uses the customer classification data to predict the customer segment.
The data is stored in a CSV file and is loaded into a table called customer_classification.

NOTE! For this model the template DOES NOT have predefined entries in data_sources.py and @predict
methods in data_actions.py. Follow the tutorial to create them yourself:
https://sema4.ai/docs/solutions/data-access/models

Dataset source: https://www.kaggle.com/datasets/kaushiksuresh147/customer-segmentation
*/

SELECT * FROM files.customer_classification;

-- The model is created using the lightwood engine with the prediction target being Segmentation.
CREATE MODEL models.customer_classification_model
FROM files
(SELECT * FROM customer_classification)
PREDICT Segmentation
USING engine = 'lightwood';

DESCRIBE MODEL models.customer_classification_model;
DROP MODEL IF EXISTS models.customer_classification_model;

-- To use the model to predict the Segmentation of a customer, you can use the following query:
SELECT Segmentation, JSON_EXTRACT(Segmentation_explain, '$.confidence') as confidence
FROM models.customer_classification_model
WHERE Gender = 'Male'
AND Ever_Married = 'Yes'
AND Age = 40
AND Graduated = 'Yes';

