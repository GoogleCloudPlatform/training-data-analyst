# Using Prompt Design to Create Learning Assets


## Overview


In this demo you learn to use prompt design to create learning assets, including a Training Plan to upskill on Generative AI based on a team's skill profile, a Training Assessment Form to capture existing skill levels, a Course Curriculum with Objectives, and the actual script for a specific course.

Use Case: Cymbal Solar is a energy company looking to upskill their team on Generative AI. They are particular interested in several key area: Project Management, Marketing, and Digital Transformation using Generative AI. They are currently a Google Cloud customer.

### Learning objectives

* Create instruction based prompts using Gemini or Vertex AI Studio.
* Create a training skills assessment using Google Forms
* Capture team training skills using Google Sheets
* Visualize team skills using Google Forms/Data Studio
* Advanced: (Create a chatbot for company training)
* Part 2 of the demo looks at using Vertex AI to capture text based sentiments to assess post-training outcomes

Vertex AI is a unified platform for building, deploying, and managing machine learning (ML) applications. Gemnini is Google's AI model. Vertex AI Studio allows you to write prompts without writing code and is available in Vertex AI.

## Task 1. Write Instruction Prompts

In the world of large language models (LLMs), an instruction prompt is a way of telling the AI exactly what you want it to do. Think of it like giving a super-smart assistant clear directions for a task.

#### Prompt
```
Cymbal Solar is our company. We need to upskill our team on Generative AI. How can Generative AI help this solar installation company?

```
Response: Note - Only sample out is shown here.

```
Absolutely! Here's a breakdown of how Generative AI can be a powerful tool for upskilling your team and boosting Cymbal Solar's operations. I'll include some ways to focus your training initiatives:

How Generative AI Can Help Cymbal Solar.

Enhanced Sales and Marketing:

Lead Generation: Generative AI can craft compelling social media posts, email campaigns, and website copy to attract potential customers.

Personalized Proposals: Create tailored proposals highlighting energy savings and ROI calculations specific to a client's needs and location.

Chatbots: Develop AI-powered chatbots to handle initial customer inquiries 24/7, freeing up your team.

Site Analysis: Analyze satellite imagery and data using AI to identify ideal roof layouts and potential shading issues for increased system efficiency.

Document Generation: Generate contracts, permits, and other essential paperwork quickly and accurately.

```

#### Prompt

Next, let's ask the model to create four levels of technical knowledge for Generative AI. This will allow us to create categories we can use later. 

### Prompt
```
Create four levels of technical knowledge for Generative AI.

```

Response: Only sample out is shown here.

```
Level 1: Basic User

Understanding: Knows what Generative AI is and its potential applications.

Skills:
Can use existing Generative AI tools with simple prompts (e.g., image generation, basic text editing).
Understands the importance of clear instructions when interacting with AI.

Level 2: Informed Practitioner

Understanding: Has a deeper grasp of how Generative AI models work and the different types (text, image, code, etc.).

Skills:
Can evaluate the quality and relevance of AI-generated output. Starting to experiment with prompt engineering for better results. Understands basic data concepts and how they impact AI outputs.

```

Now that we have the Generative AI benefits to Cymbal Solar and the levels of Generative AI technical knowledge, let's have the model create a survey to assess existing Generative AI team knowledge.

### Prompt
```
Create a survey for the Cymbal Solar team to self-assess their Generative AI skill level based upon the four levels of technical knowledge for Generative AI. Use a five-point scale. Add a few open-ended questions. 

```

Response: Only sample output shown.

```
Here's a survey tailored to the Cymbal Solar team, using a five-point scale and incorporating some open-ended questions for deeper insights.

Cymbal Solar Generative AI Skills Survey

Purpose: This survey will help us understand the current skills of our team and determine the best areas for upskilling initiatives in Generative AI.

Instructions: Please answer each question honestly to the best of your ability. There are no right or wrong answers!

Section 1: Skill Self-Assessment

Please rate your current proficiency in the following areas using the scale below:

1 - Not at all familiar
2 - Slightly familiar
3 - Somewhat familiar
4 - Moderately familiar
5 - Extremely familiar

Understanding Generative AI:

I can clearly define Generative AI and explain how it works.

I am familiar with different types of Generative AI (image, text, etc.).

I understand the potential benefits of Generative AI for the solar industry.

Using Generative AI Tools:

I can use existing Generative AI tools to complete simple tasks.

I understand the importance of writing effective prompts.


Technical Skills:

I am familiar with the concepts of data and how it influences AI models.

I have some experience modifying or fine-tuning simple Generative AI models.

Section 2: Open-Ended Questions:

In what areas of your work do you see the greatest potential for Generative AI to be helpful?

What are your biggest concerns or questions about implementing Generative AI at Cymbal Solar?

What kind of training or resources would you find most useful to advance your Generative AI skills?

Thank you for your participation! Your feedback is valuable as we design our Generative AI upskilling program.

Let me know if you'd like help analyzing the results or designing the upskilling program based on the survey data!

```

My last sentence of the response is the model asking me if I would like help analyzing the results or designing the upskilling program based on the survey data. I take this sentence and create another instruction prompt. 

### Prompt

```
Yes, I would like help analyzing the results or designing the upskilling program based on the survey data!

```

Response: Only sample output shown.

```
Absolutely! Here's a breakdown of how to tackle the analysis and then leverage that insight for targeted upskilling program design:

Quantitative Analysis:

Averages: Calculate the average score for each question within the skill assessment section. This will highlight overall strengths and weaknesses.

Distributions: Examine how many respondents fall into each proficiency level (1-5) for each question. This reveals the range of skills across the team.

Qualitative Analysis:

Collate Open-Ended Responses: Group the answers to each open-ended question together.

Tiered Approach: Based on  survey results,  design training in different tiers to match the four skill levels:

Tier 1: Foundational (for those scoring mostly 1s and 2s)
Tier 2: Applied Practice (for those scoring mostly 3s)
Tier 3: Technical Development (for a smaller number with scores of 4s)
Tier 4: Exploration/Research (invite those scoring mostly 5s to explore advanced projects or mentor others)

Focus Areas:

Quantitative Data: Use average scores to understand the weakest skill areas across the board that need to be included in all tiers.

Qualitative Data: Open-ended questions reveal what employees think will be beneficial. Address these topics even if the survey doesn't suggest low proficiency. Motivation to learn is key!

Program Structure:

Blended Learning: Combine workshops, online lessons, hands-on projects, and mentorship opportunities.
Cymbal-Specific Examples: Tailor training so employees understand how AI applies directly to their role and company goals.

Iterative Evaluation: Gather feedback throughout the training and assess skill gains with follow-up surveys or competency demonstrations.

Example Scenario:

Survey Says: Average scores are highest for basic use of tools, but low for data concepts. Open-ended answers reveal enthusiasm for sales lead generation with AI.

Program Design:
Tier 1: Explaining AI fundamentals, how data works, prompt writing basics.

Tiers 2-3: AI tool workshops specific to sales with ample practice time. Include basic data literacy for everyone as a core element.

Tier 4 (if applicable): Explore advanced prompt engineering for lead generation or sponsor a small-scale research project.

Let me know if you want to dive into a specific analysis of potential survey data or brainstorm training formats. I'm here to help!

```



## Task 1. Create a Google Form. 

In this demo, the survey was created using Google Forms. The results of Google Forms automatically captures the data in sheets and automatically gives visualizations of survey results.

I'll briefly shown the Form and visualizations.
Then, I'll briefly show the spreadsheet.



```

```

1. Enable the Vertex AI API

Navigate to the [Vertex AI section of your Cloud Console](https://console.cloud.google.com/ai/platform?utm_source=codelabs&utm_medium=et&utm_campaign=CDR_sar_aiml_vertexio_&utm_content=-) and click __Enable All Recommended APIs__.

## Task 2. Create a Workbench Notebook

1. In the Vertex AI section, scroll down to __Notebooks__. Click __Workbench__.

![select_workbench](img/select_workbench.png)

2. At the top of the workspace, make sure __INSTANCES__ is selected.

3. Click __CREATE NEW__.

![create_wbnb](img/create_wbnb.png)

A new instance window appears (as shown below)

4. For this lab, name the instance and select __CREATE__.
If you want more control, you can select __ADVANCED OPTIONS__. Once you name the instance, and select __CREATE__, you assume all default environment settings  .

![wb_new_instance_window](img/wb_new_instance_window.png)

You will notice your new instance spinning up in the __Instance Name__ section.


A green check appears next to the instance when it is ready to be use.

![my-new-instance](img/my-new-instance.png)

5. Click __OPEN JUPYTERLAB__ to open a Jupyter notebook.

![open_jupyterlab](img/open_jupyterlab.png)

6. To launch Python 3 Jupyter Notebook, click the __Python 3__ notebook.

![launch_wb_nb](img/launch_wb_nb.png)

7. Once the notebook is launched, rename it by right-clicking on the __untitled.ipynb__ file in the menu bar and selecting __Rename Notebook__.

![rename_wbnb](img/rename_wbnb.png)
![my-notebook2](img/my-notebook2.png)


## Task 3. Clone a repo within your Vertex AI Notebook instance

The GitHub repo contains both the lab file and solutions files for the course.

1. To clone the training-data-analyst notebook in your JupyterLab instance, copy this code into the first cell in the notebook.

```
!git clone https://github.com/GoogleCloudPlatform/training-data-analyst
```
Output shown.
![git_ouput](img/git_ouput.png)


2. Confirm that you have cloned the repository. Double-click on the __training-data-analyst__ directory and ensure that you can see its contents.

![confirm_training-data-analyst](img/confirm_training-data-analyst.png)

1. In the notebook interface, navigate to __training-data-analyst > courses > machine_learning > deepdive2 > launching_into_ml > solutions__ and open __workbench_explore_bq.ipynb__.

2. Carefully read through the notebook instructions.

![Alt text](img/workbench_explore_bq_nb.png)



## Congratulations!

In this lab you learned how to:

* Create a Workbench Instance Notebook
* Clone a GitHub repository
* Connect to a BigQuery dataset
* Perform statistical analysis on a Pandas Dataframe
* Create Seaborn plots for Exploratory Data Analysis in Python
* Write a SQL query to pick up specific fields from a BigQuery dataset.


![[/fragments/endqwiklab]]


**Manual Last Updated: December 14, 2023**

**Lab Last Tested: December 14, 2023**

![[/fragments/copyright]]
