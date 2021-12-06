"""Default model training constants and hyperparameters.
These values can be tweaked to affect model training performance.
"""


HIDDEN_UNITS = [64, 32]
LEARNING_RATE = 0.0001
BATCH_SIZE = 512
NUM_EPOCHS = 10
NUM_EVAL_STEPS = 100

# Model training constants.
# Virtual epochs design pattern:
# https://medium.com/google-cloud/ml-design-pattern-3-virtual-epochs-f842296de730
TRAIN_EXAMPLES = 80000
DEV_EXAMPLES = 20000
STOP_POINT = 1.0
TOTAL_TRAIN_EXAMPLES = int(STOP_POINT * TRAIN_EXAMPLES)
TRAIN_BATCH_SIZE = 64
EVAL_BATCH_SIZE = 64
N_CHECKPOINTS = 2


def update_hyperparameters(hyperparameters: dict) -> dict:
    if "hidden_units" not in hyperparameters:
        hyperparameters["hidden_units"] = HIDDEN_UNITS
    else:
        if not isinstance(hyperparams["hidden_units"], list):
            hyperparams["hidden_units"] = [
                int(v) for v in hyperparams["hidden_units"].split(",")
            ]
    if "learning_rate" not in hyperparameters:
        hyperparameters["learning_rate"] = LEARNING_RATE
    if "batch_size" not in hyperparameters:
        hyperparameters["batch_size"] = BATCH_SIZE
    if "num_epochs" not in hyperparameters:
        hyperparameters["num_epochs"] = NUM_EPOCHS

    return hyperparameters
