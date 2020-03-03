# Dataset

## Dataset description

This example project is using the popular CoNLL 2002 dataset. The csv consists of multiple rows each containing a word with the corresponding tag. Multiple rows are building a single sentence. 

The dataset itself contains different tags
* geo = Geographical Entity 
* org = Organization 
* per = Person 
* gpe = Geopolitical Entity 
* tim = Time indicator 
* art = Artifact 
* eve = Event 
* nat = Natural Phenomenon

Each tag is defined in an IOB format, IOB (short for inside, outside, beginning) is a common tagging format for tagging tokens.

> B - indicates the beginning of a token

> I - indicates the inside of a token

> O - indicates that the token is outside of any entity not annotated

### Example

```bash
"London on Monday evening"
"London(B-geo) on(O) Monday(B-tim) evening(I-tim)"
```

## Data Preparation
You can download the dataset from the [Kaggle dataset](https://www.kaggle.com/abhinavwalia95/entity-annotated-corpus). In order to make it convenient we have uploaded the dataset on GCS.

```
gs://kubeflow-examples-data/named_entity_recognition_dataset/ner.csv
```

> The training pipeline will use this data, there are no further data preperation steps required.

*Next*: [Custom prediction routine](step-4-custom-prediction-routine.md)

*Previous*: [Build the pipeline components](step-2-build-components.md)