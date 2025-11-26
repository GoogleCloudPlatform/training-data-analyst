# Exploratory Data Analysis using Bigquery and Colab Enterprise


## Overview






In this lab you learn the process of analyzing a dataset stored in BigQuery using Colab Enterprise to perform queries and present the data using various statistical plotting techniques. The analysis will help you discover patterns in the data.

### Learning objectives

* Create a Colab Enterprise Notebook
* Connect to BigQuery datasets
* Perform statistical analyis on a Pandas Dataframe
* Create Seaborn plots for Exploratory Data Analysis in Python
* Write a SQL query to pick up specific fields from a BigQuery dataset
* Use version history to see code changes
* Share a Colab Enterprise notebook





Vertex AI is a unified platform for building, deploying, and managing machine learning (ML) applications.

Vertex AI Colab Enterprise is a powerful collaborative interactive tool created to explore, analyze, transform and visualize data and build machine learning models on Google Cloud. It offers the security and compliance features needed for enterprise organizations and integrates with other Google Cloud services like Vertex AI and BigQuery for an enhanced data science and machine learning workflow.

BigQuery is a powerful, fully managed, serverless data warehouse that allows you to analyze and manage large datasets with ease. BigQuery uses a familiar standard SQL dialect, making it easy for analysts and data scientists to use without needing to learn a new language.

Vertex AI offers two Notebook Solutions, Workbench and Colab Enterprise. 

![Colab](img/colab1.png)

### Colab Enterprise

The Colab Enterprise worksspace consists of five major sections (as shown in the image below), (1) Notebook storage; (2) Notebook actions; (3) Runtimes and Runtimes templates, (4) Notebook editor and (4) Notebook code cells. Notebook storage is the location of the notebooks, notebook actions are actions that can be performed on a notebook, runtimes let you "run" the notebook, notebook editor is for making edits to the notebook, and code cells let's you enter code.  


![Colab Runtime](img/colab2.png)


## Set up your lab environments

### Lab setup

![[/fragments/start-qwiklab]]



## Task 1. Set up your environment

1. Enable the Vertex AI API

Navigate to the [Vertex AI section of your Cloud Console](https://console.cloud.google.com/ai/platform?utm_source=codelabs&utm_medium=et&utm_campaign=CDR_sar_aiml_vertexio_&utm_content=-) and click __Enable Vertex AI API__.

## Task 2. Create a Colab Enterprise Notebook

1. In the Vertex AI section, scroll down to Notebooks. Click __Colab Enterprise__.

![select_colab](img/select_colab.png)

A "Welcome to Colab Enterprise" page then appears. Click the __Create Notebook__ at the bottom of the page.

![screate_nb](img/create_nb.png)

2.  A new notebook appears with prepopulated cells. This is the "Getting Started" notebook. 

![get_started](img/get_started.png)


In order to execute the cells you need to create a runtime. Recall that runtimes are instances derived from runtime templates that allow users to run Colab notebooks. To create a runtime, you need to first create a runtime template.


3. Click __RUNTIME TEMPLATES__. On the Runtime Templates page, click __NEW TEMPLATE__.

![Colab Runtime](img/runtime2.png)


#### Runtime Basics

There are three steps. Step 2 and Step 3 are optional. 

Step 1: Provide runtime basic information. 

![Colab Runtime](img/create_runtime1.png)


#### Compute Configure

Step 2: Configure Compute (Optional)

![Colab Runtime](img/create_runtime2.png)


#### Networking and Security

Step 3: Networking and Security (Optional)

![Colab Runtime](img/create_runtime3.png)

## Task 3. Run Code in a Colab Enterprise Notebook

In this example, the code cell below “Getting Started” uses numpy to generate some random data and uses matplotlib to visualize it. 

1. Click the __Run__ icon to run the cell.

![run_icon](img/run_icon.png)

As you execute the cell, a massage pops up indicating that the runtime is active and initiating a connection - as shown in the image below. 

![Colab Runtime](img/runtime_active.png)

2. Now check the cell you executed, there should be a green check mark next to, this indicates that the cell executed properly.

![Colab Output](img/output.png)

3. Now, make a change to the code - for example, change the title of the plot from "Sample Visualization" to "Colab Enterprise". Then, execute the cell.

![Colab Output2](img/output2.png)

## Task 4. Show revision history.

One of the most important features of software development is the ability to track version history. 

1. Go to the Notebook Storage section. Right click on the notebook you created and Select __Actions__

![actions](img/actions.png)

2. Select __Revision History__ (as shown in bubble #1 in the image below).

When revision history is selected, you see the changes side by side with a date stamp and color-coding to see the “old” in red and the “new” in green (as shown in bubble #2). 
There are three options to view revision history: the raw source, the inline differences, or the source output (as shown in bubble #3).

![revision_history](img/revision_history.png)

## Task 5. Add code to cells. 

To add code or text to a Notebook, simply click on either code or text in the menu bar above the Notebook Editor. 

![add_code](img/add_code.png)

Now, you will add several blocks of code to the notebook. After you copy a block of code, run the code to see the output. Note - Some cells will have not output (such as when you import the libraries). When you are done, share the notebook.

1. Add a code cell.
2. Copy the code below into the new cell.
3. Click the __Run__ icon to run the cell.
4. View the output.

#### Import libraries
```import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from google.cloud import bigquery
bq = bigquery.Client()
```
No output shown.

Insert the following code as cells to import the necessary modules and initialize a BigQuery client. The BigQuery client will be used to send and receive messages from the BigQuery API.

#### Import BigQuery Client

```from google.cloud.bigquery import Client, QueryJobConfig
client = Client()

query = """SELECT * FROM `bigquery-public-data.catalonian_mobile_coverage_eu.mobile_data_2015_2017` LIMIT 1000"""
job = client.query(query)
df = job.to_dataframe()
```
No output shown.

#### Download a BigQuery Table into a Pandas Dataframe

In Google, %%bigquery is a magic command used within Jupyter notebooks and other interactive environments to interact with BigQuery. Therefore, %%bigquery essentially tells your environment to wwitch to BigQuery mode: It prepares the environment to accept and execute BigQuery queries. BigQuery will execute the query, retrieve the data, and present it to you within the notebook environment, often as a pandas DataFrame (e.g. the "df" as shown in the code) 

```
%%bigquery df
SELECT *
FROM `bigquery-public-data.catalonian_mobile_coverage_eu.mobile_data_2015_2017`
```
Output shown:
![abq_df_output](img/bq_df_output.png)

#### Show the first five rows of the Pandas Dataframe

```
df.head()
```

Output shown:
![adf.headoutput](img/df.headoutput.png)

#### Get information on the Pandas Dataframe

```
df.info()
```
Output shown:
![adf.infooutput](img/df.infooutput.png)

#### Get statistics on the Pandas Dataframe

```
df.describe()
```
Output shown:
![df.describeoutput](img/df.describeoutput.png)


#### Plot a correlation using Seaborn.
```
plt.figure(figsize=(10,5))
sns.heatmap(df.corr(),annot=True,vmin=0,vmax=1,cmap='viridis')
```

Output shown:
![df.corroutput](img/df.corroutput.png)


#### Write a SQL query to pick up specific fields from a BigQuery dataset

```
%%bigquery df2
SELECT signal, status
FROM `bigquery-public-data.catalonian_mobile_coverage_eu.mobile_data_2015_2017`
```
Output shown:
![abq_df_output](img/bq_df_output.png)

#### Get the first five rows of the new fields.

```
df2.info()
```
Output shown:
![asql_output](img/sql_output.png)

## Task 6. Share the Notebook

Next, share your notebook. 
1. When you select “Share” by right-clicking on the notebook, a share permissions window appears, which allows you to  edit or delete permissions, or select "Add Principal" to grant new access.

![share](img/share.png)

2. When you grant principals access to a resource, you also add roles to specify what actions the principals can take. Optionally, you can add conditions to grant access to principals only when a specific criteria is met. 

Principals are users, groups, domains, or service accounts Roles are composed of sets of permissions and determine what the principal can do with this resource.

## Congratulations!

In this lab you learned how to:
* Create a Colab Enterprise Notebook
* Connect to BigQuery datasets
* Perform statistical analyis on a Pandas Dataframe
* Create Seaborn plots for Exploratory Data Analysis in Python
* Write a SQL query to pick up specific fields from a BigQuery dataset
* Use version history to see code changes
* Share a Colab Enterprise notebook


![[/fragments/endqwiklab]]


##### Manual Last Updated: December, 2023

##### Lab Last Tested: December, 2023

![[/fragments/copyright]]

