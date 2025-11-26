# Using Prompt Design to create an Upskilling Strategy, Plan, and Learning Assets


## Overview


In this demo you learn to use prompt design to create learning assets, including a Training Plan to upskill on Generative AI based on a team's skill profile, a Training Assessment Form to capture existing skill levels, a Course Curriculum with Objectives, and the actual script for a specific course.

Use Case: Cymbal Solar is a energy company looking to upskill their team on Generative AI. They are particular interested in several key area: Project Management, Marketing, and Digital Transformation using Generative AI. They are currently a Google Cloud customer.

### Learning objectives

* Create instruction based prompts using Gemini or Vertex AI Studio.
* Create a training skills assessment using Google Forms
* Capture team training skills using Google Sheets
* Visualize team skills using Google Forms/Data Studio
* Write prompts to create learning assets.
* Write prompts to create pre/post training assessments.
* Write prompts to create the learning assests
* Write a prompt to export a learning asset into BigQuery.*
* Write a prompt to create a chatbot based on a learning role.


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
Focus: Consuming AI-generated output and exploring various applications.

Level 2: Informed Practitioner

Understanding: Has a deeper grasp of how Generative AI models work and the different types (text, image, code, etc.).

Skills:
Can evaluate the quality and relevance of AI-generated output.
Starting to experiment with prompt engineering for better results.
Understands basic data concepts and how they impact AI outputs.

Focus: Using Generative AI in day-to-day tasks, understanding potential biases, and responsible use.

Level 3:  Proficient Developer

Understanding: Possesses a solid technical foundation of Generative AI algorithms and architectures.

Skills:
Can fine-tune pre-existing models on company-specific data.
Implements basic safety and bias mitigation strategies.
Designs prompts effectively and understands their impact on outputs.
Integrates Generative AI into workflows and tools.

Focus: Adapting existing AI solutions for specific industry challenges and deploying them effectively.

Level 4: AI Researcher/Engineer

Understanding: Deep knowledge of theoretical concepts behind Generative AI, including cutting-edge research.

Skills:
Develops new Generative AI models or significantly modifies existing ones.
Researches methods of improving performance, fairness, and transparency.
Creates training datasets and evaluation protocols.
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

I'll briefly show the Form and visualizations.

[Google Spreedsheet](https://docs.google.com/spreadsheets/d/1IBxQVkZ35jpKa_QPXSlQ4HcP7S_zC-5TzNtGYPMUzeU/edit?resourcekey=0-1MfK39T_6_u2o8LIKu7yFw#gid=1052472429)


Then, I'll briefly show the Skills pProfile spreadsheet.
I'll then copy all the data in the spreadsheet into the model and create a prompt:

### Prompt
```
Here is my team's Generative AI skills profile. Create a training plan for upskilling on Generative AI.
Timestamp	First Name	Last Name	Role	1. Please indicate how long you have worked at Cymbal Solar.	I use Generative AI to brainstorm new ideas.	I can integrate Generative AI outputs into my creative projects.	 I feel comfortable experimenting with different Generative AI tools.	I can leverage generative AI models for specific tasks and can customize them to a limited degree.	I have the knowledge to modify and train generative AI models, typically within existing frameworks.	I can effectively craft prompts to get the desired results from Generative AI tools.	I understand the basic principles of how Generative AI models work.	I use pre-trained generative AI tools through web interfaces or applications (e.g., DALL-E 2, Gemini, ChatGPT, Jasper)	2. What are some methods you use for learning today? Please check the ones that apply.	2. How quickly do you want to learn these skills?						
3/18/2024 18:28:45	Tiko	Greene	Project Manager	1-2 years	1	1	1	1	1	1	1	1	Discussing problems I face with colleagues, Reflecting / maintaining a diary of some things I can try, Trainings I attend within the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 3 months						
3/18/2024 18:44:07	Cora	Whitley	Quality Assurance  Inspector	1-2 years	1	1	3	1	1	4	4	4	Trainings I attend outside the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 6 months						
3/18/2024 18:49:42	Matt	King	Marketing Specialist	10+ years	2	2	2	1	1	4	3	4	Trainings I attend outside the company, Sessions organized by my team members, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 3 months						
3/20/2024 16:24:34	test	test	Project Manager	3-4 years	3	2	2	3	2	4	1	2	Trainings I attend outside the company	Within an year						
3/20/2024 16:53:01	Chioma	Williams	Project Manager	3-4 years	4	4	4	3	2	5	4	5	Discussing problems I face with colleagues, Trainings I attend outside the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	As early as possible						
3/18/2024 18:28:45	Mary	Curley	Project Manager	1-2 years	1	1	1	1	1	1	1	1	Discussing problems I face with colleagues, Reflecting / maintaining a diary of some things I can try, Trainings I attend within the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 3 months						
3/18/2024 18:44:07	Tawanda	Larry	Quality Assurance  Inspector	1-2 years	1	1	3	1	1	4	4	4	Trainings I attend outside the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 6 months						
3/18/2024 18:49:42	Fred	Kang	Marketing Specialist	10+ years	2	3	2	1	1	4	3	4	Trainings I attend outside the company, Sessions organized by my team members, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	Within 3 months						
3/20/2024 16:24:34	Yuki	Walker	Project Manager	3-4 years	4	2	2	3	2	4	1	2	Trainings I attend outside the company	Within an year						
3/20/2024 16:53:01	Mo	Benhardt	Project Manager	3-4 years	4	3	4	3	2	5	4	5	Discussing problems I face with colleagues, Trainings I attend outside the company, On-Demand Learning Platforms (Coursera, Pluralsight, Google Skills, etc.)	As early as possible						
																				
```

Response

```
Here's a training plan designed to upskill your team in Generative AI, based on your team's skills profile. I've included key elements, but you'll need to fill in specific content and resources.

Training Plan Outline

1. Foundational Phase (For Everyone)

Objectives:

Demystify Generative AI (what it is, how it works, different types)
Explore applications for solar (company-specific examples are vital)
Basic prompt writing skills

Format - Interactive workshops led by in-house experts (if available) or external instructors. Supplement with short readings/videos. Hands-on activity: As a team, brainstorm potential use cases across different departments.

2. Targeted Upskilling: Tiered Approach

Based on the survey, create three skill tiers:

Tier 1: Basic Users (Most team members seem to fall here)
Objectives: Use existing Generative AI tools confidently, Evaluate AI-generated outputs
Refine prompts for better results

Format:
Tool-specific workshops (image generators, text tools, etc.)
Department-focused sessions (marketing gets different examples than QA)

Tier 2: Informed Practitioners
Objectives: Basic understanding of data for AI. Exploration of customizing pre-trained models

Format: Mix of workshops and online courses covering data literacy and AI ethics
Short projects to experiment with fine-tuning tools

Tier 3: Exploration & Development (Likely 1-2 people)
Objectives: Encourage innovation, not rigid skills prescription
Format: Mentorship/collaboration with more experienced AI colleagues (if possible)
Small-scale internal research project with clear goals

Motivation Matters: The survey reveals your team is enthusiastic! Leverage this energy with hands-on training sessions and examples tailored to their interests.
Pace & Agility: Divide the training into manageable chunks that correspond with the team's desired learning speed. This plan isn't set in stone – adjust as you go.
Evaluation: Include short quizzes, project demos, or repeat the survey later to gauge progress and tailor the plan further.
																				
```

To get a more target training plan, I will type the following prompts individually until I arrive at table of skilling by actual role.

### Prompt(s)
```
Create the training plan by Role.
```

```
Create the training by First name.

```

Here is the link to the table.
https://gemini.google.com/corp/app/acbfda32607128e8



Part 2 of the Demo is live.

The next steps are to have the model -using prompt design - create the curriculum for one of the role/levels and actually design the course - e.g. it will put a response showing the slide, proposed image, and speaker notes.

After team training, the model can create a post-assessment survey. The model can analyze the results. 

As a final team-building exercise, have the team work together to create a simple sentiment analysis project that will capture customer sentiments using Generative AI.

### Prompt																				
```
Create the Generative AI curriculum for Cora, the QA Inspector.																			
```																				
Response: MY Link to prompt.

```	
Absolutely! Here's a draft Generative AI curriculum for Cora, the QA Inspector, incorporating her background and preferences.

Cora's Learning Profile

Current Skill Tier: Tier 1 (Basic User)
Desired Timeline: Within 6 months
Learning Preferences: External trainings, on-demand learning platforms


Curriculum Structure

Phase 1: Foundational & Applied (Months 1-3)

Foundational Knowledge: Participate in the company-wide intro workshops on Generative AI.

AI for Image Analysis: Enroll in a course like "Introduction to Computer Vision" or "AI for Defect Detection" (search Coursera, etc.). Practice with open-source image analysis tools using datasets relevant to solar panels, if possible.

Text Generation for Reports:Short course on "Natural Language Processing for Report Writing" or similar. Experiment with report generation tools, emphasizing the importance of human review initially.

Data Literacy Basics: Short online module on "Understanding Data for AI." Focus on image data and how it impacts tool performance.

Phase 2:  Consolidation & Exploration (Months 4-6)

Practice and Feedback:Integrate learned tools into Cora's workflow with manager support.Set regular check-ins to troubleshoot, evaluate output quality, and refine prompt writing.

Understanding Bias: Focused course or workshop on "Bias in AI", particularly as it applies to visual data.

Exploring Customization:
If Cymbal Solar has its own image datasets, investigate basic model fine-tuning with guided support (this might be an area for mentorship or external consultation).

Curriculum Considerations

Pacing: Adjust based on Cora's progress and how quickly these skills can be meaningfully integrated into her work.
Company Resources: Can existing image datasets be used for practice? Are there tech-savvy colleagues who can mentor her?
Evaluation: Include small projects or task simulations to gauge Cora's understanding beyond just course completion.

Let's Fine-Tune This!

Specific Courses: Would you like me to suggest course titles or providers that align with Cora's focus areas?
Project Ideas: Can we brainstorm a small-scale project she could work on in Phase 2 to apply her knowledge?
Mentorship: Does Cymbal Solar have anyone with moderate AI experience who could guide Cora, especially as she gets into customization?

Let me know how I can help tailor this curriculum further!

```	

### Prompt

```	
Develop a training plan for Generative AI upskilling for the following employees in the solar installation company: Tiko Greene =Project Manager, Technical Knowledge for Generative AI=1; Cora Whitley = Quality Insurance Inspector, Technical Knowledge for Generative AI=2; Matt King = Marketing Specialist, Technical 
```	

Response:

```	
Here's a tailored training plan for upskilling Tiko, Cora, and Matt in Generative AI, taking into account their existing technical knowledge and their roles within the solar installation company:

Overall Plan Considerations

Varied Skill Levels: Account for the differences in initial Generative AI familiarity. Start with foundational modules and then diverge for role-specific training.

Focus on Application: Emphasize how Generative AI can directly enhance their existing work processes and problem-solving in the solar installation industry.
```	
The model then presents a table, as shown here.
https://gemini.google.com/corp/app/aa1a7acccc4d110e


```	
Create the Generative AI curriculum for Cora, the QA Inspector.
```	

```	
Yes. Suggest a course title and using that title, create the course objectives, slides, image for slides, and speaker notes.
```	

```	
Expand the speaker notes to include more narrative.
```	

```	
Write more sentences of speaker notes for each slide. It is important that this is done.

```

```
Can you put this content into a table?
```

Table shown here in my profile
https://gemini.google.com/corp/app/acbfda32607128e8


We can then use the slides to begin to create a data repository for a slide content, that we'll be able to query by slide image, slide text, and slide speaker notes. There are many uses here - reduced maintenance when you'll need to update a specific reference and reduced development time for leveraging assets.

We'll write a prompt ask the model to help us begin to automate some things.

### Prompt

```
Write code to export this table into a .csv format, upload it to Google Cloud storage, and then import it into BigQuery. This will allow us to create a repository of our training content. 

```

Response:

```
Absolutely! Here's the code breakdown, including explanations for each step. Please note that you'll need to fill in placeholders for project IDs, bucket names, etc.

1. Python Libraries

You'll need the following libraries. If you don't have them, install them using pip install:

import pandas as pd
from google.cloud import storage
from google.cloud import bigquery

2. Create the Table as a DataFrame

# Create a list of dictionaries, each representing a slide
data = [
    {"Slide #": 1, "Slide Image": "Photo of a solar panel...", "Slide Text": "AI-Powered Image Analysis...", "Expanded Speaker Notes": "Intro, background, why important... "},
    # ... Add the remaining slide data as dictionary entries ...
]

# Create a Pandas DataFrame
df = pd.DataFrame(data)

3. Export to CSV

# Replace 'your_file.csv' with your desired filename
df.to_csv("your_file.csv", index=False) 

4. Google Cloud Storage (GCS) Upload

# Authentication (replace placeholders)
client = storage.Client(project="your_project_id") 
bucket = client.get_bucket("your_gcs_bucket_name")

# Upload the CSV
blob = bucket.blob("training_content.csv")  # Adjust the destination filename if needed
blob.upload_from_filename("your_file.csv") 

5. Import to BigQuery

# BigQuery client and references (replace placeholders)
bq_client = bigquery.Client(project="your_project_id")
dataset_id = "your_dataset_id" 
table_id = "training_content"  # Name of the new table in BigQuery

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, autodetect=True
)

# URI of the file in GCS
uri = "gs://your_gcs_bucket_name/training_content.csv" 

# Load the CSV into BigQuery
load_job = bq_client.load_table_from_uri(
    uri, dataset_id + "." + table_id, job_config=job_config
) 
load_job.result()  # Wait for the job to complete

# Success message
print("Loaded {} rows into {}:{}.".format(load_job.output_rows, dataset_id, table_id))

```

Note - You can use the same process to import the Skills Profile created by the model earlier into BigQuery. I'd recommend adding an employeed ID field for future use cases.

Now, back to Cora. It would be great to build a Chatbot based on her course. Let's ask the model.

### Prompt

```
Show me the code to create a chatbot to train Cora on the course you suggested. Use DialogFlow.
```

Response link here:
https://gemini.google.com/corp/app/acbfda32607128e8

------------------------------------------------------------

TRAINING IS COMPLETED. TIME FOR POST-ASSESSMENT

```
Assume all team members have now had training on Generative AI as you have recommended.  Create a survey that captures open-ended questions. Put it into a table format. 
```

Response: 
Post Training Generative AI Feedback https://gemini.google.com/corp/app/aa1a7acccc4d110e

Have the team work together to create a simple chatbot and a simple app to capture Sentiment Analysis. Here is an example using customer feedback. 