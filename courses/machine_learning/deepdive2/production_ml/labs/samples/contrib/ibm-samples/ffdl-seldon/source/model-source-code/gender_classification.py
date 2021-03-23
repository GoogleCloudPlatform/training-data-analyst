# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import glob
import PIL
from PIL import Image
import numpy as np
import argparse

import torch
import torch.utils.data
from torch.autograd import Variable
import torch.nn as nn
from torchsummary import summary
import time

import pandas as pd

np.random.seed(99)
torch.manual_seed(99)


class ThreeLayerCNN(torch.nn.Module):
    """
    Input: 128x128 face image (eye aligned).
    Output: 1-D tensor with 2 elements. Used for binary classification.
    Parameters:
        Number of conv layers: 3
        Number of fully connected layers: 2
    """
    def __init__(self):
        super(ThreeLayerCNN,self).__init__()
        self.conv1 = torch.nn.Conv2d(3,6,5)
        self.pool = torch.nn.MaxPool2d(2,2)
        self.conv2 = torch.nn.Conv2d(6,16,5)
        self.conv3 = torch.nn.Conv2d(16,16,6)
        self.fc1 = torch.nn.Linear(16*4*4,120)
        self.fc2 = torch.nn.Linear(120,2)


    def forward(self, x):
        x = self.pool(torch.nn.functional.relu(self.conv1(x)))
        x = self.pool(torch.nn.functional.relu(self.conv2(x)))
        x = self.pool(torch.nn.functional.relu(self.conv3(x)))
        x = x.view(-1,16*4*4)
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.fc2(x)
        return x


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, help='Dataset directory path')
    parser.add_argument('--result_path', type=str, help='Result model path')
    parser.add_argument('--label_dir', type=str, help='Label directory path')
    args = parser.parse_args()

    image_dir = args.data_dir
    result_dir = args.result_path
    label_dir = args.label_dir

    """ Load and Process Images """

    races_to_consider = [0,4]
    unprivileged_groups = [{'race': 4.0}]
    privileged_groups = [{'race': 0.0}]
    favorable_label = 0.0
    unfavorable_label = 1.0

    img_size = 64

    protected_race = []
    outcome_gender = []
    feature_image = []
    feature_age = []

    for i, image_path in enumerate(glob.glob(image_dir + "*.jpg")):
        try:
            age, gender, race = image_path.split('/')[-1].split("_")[:3]
            age = int(age)
            gender = int(gender)
            race = int(race)

            if race in races_to_consider:
                protected_race.append(race)
                outcome_gender.append(gender)
                feature_image.append(np.array(Image.open(image_path).resize((img_size, img_size))))
                feature_age.append(age)
        except:
            print("Missing: " + image_path)

    feature_image_mat = np.array(feature_image)
    outcome_gender_mat =  np.array(outcome_gender)
    protected_race_mat =  np.array(protected_race)
    age_mat = np.array(feature_age)

    """ Split the dataset into train and test """

    feature_image_mat_normed = 2.0 *feature_image_mat.astype('float32')/256.0 - 1.0

    N = len(feature_image_mat_normed)
    ids = np.random.permutation(N)
    train_size=int(0.7 * N)
    X_train = feature_image_mat_normed[ids[0:train_size]]
    y_train = outcome_gender_mat[ids[0:train_size]]
    X_test = feature_image_mat_normed[ids[train_size:]]
    y_test = outcome_gender_mat[ids[train_size:]]

    p_train = protected_race_mat[ids[0:train_size]]
    p_test = protected_race_mat[ids[train_size:]]

    age_train = age_mat[ids[0:train_size]]
    age_test = age_mat[ids[train_size:]]

    batch_size = 64

    X_train = X_train.transpose(0,3,1,2)
    X_test = X_test.transpose(0,3,1,2)

    train = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_train.astype('float32'))), Variable(torch.LongTensor(y_train.astype('float32'))))
    train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=True)
    test = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_test.astype('float32'))), Variable(torch.LongTensor(y_test.astype('float32'))))
    test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = ThreeLayerCNN().to(device)
    summary(model, (3,img_size,img_size))


    """ Training the network """

    num_epochs = 5
    learning_rate = 0.001
    print_freq = 100

    # Specify the loss and the optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Start training the model
    num_batches = len(train_loader)
    for epoch in range(num_epochs):
        for idx, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if (idx+1) % print_freq == 0:
                print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' .format(epoch+1, num_epochs, idx+1, num_batches, loss.item()))

    # Run model on test set in eval mode.
    model.eval()
    correct = 0
    y_pred = []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            correct += predicted.eq(labels.data.view_as(predicted)).sum().item()
            y_pred += predicted.tolist()
        print('Test_set accuracy: ' + str(100. * correct / len(test_loader.dataset)) + '%')
    # convert y_pred to np array
    y_pred = np.array(y_pred)

    # Save the entire model to enable automated serving
    torch.save(model.state_dict(), result_dir)
    print("Model saved at " + result_dir)

    # Save labels and protected features for fairness check.
    np.savetxt(label_dir + '/y_train.out', y_train)
    np.savetxt(label_dir + '/p_train.out', p_train)
    np.savetxt(label_dir + '/y_test.out', y_test)
    np.savetxt(label_dir + '/p_test.out', p_test)
    np.savetxt(label_dir + '/y_pred.out', y_pred)
    np.save(label_dir + '/x_test', X_test)

    print("Labels stored at directory " + label_dir)
