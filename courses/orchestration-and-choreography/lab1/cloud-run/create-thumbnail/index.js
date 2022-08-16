// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
const express = require('express');
const bodyParser = require('body-parser');
const im = require('imagemagick');
const Promise = require("bluebird");
const path = require('path');
const {Storage} = require('@google-cloud/storage');
const storage = new Storage();
const Firestore = require('@google-cloud/firestore');

const app = express();
app.use(bodyParser.json());

// directories created in Dockerfile
const sourceDir = '/tmp/source';
const destinationDir = '/tmp/destination';

// retrieve destination bucket name from environment variable
const generatedImagesBucketName = process.env.GENERATED_IMAGES_BUCKET;

const thumbnailDimension = 400;
const firestoreCollectionName = 'images';

// POST /
// {
//   gcsImageUri = "gs://{sourceBucketName}/{fileName}"
// }
app.post('/', async (req, res) => {
    try {
        console.log(`Request body: ${JSON.stringify(req.body)}`);

        // location of source image
        const gcsImageUri = req.body.gcsImageUri;

        // gs://BUCKET/FILENAME - extract bucket and filename
        const [sourceBucketName, fileName] = gcsImageUri.substr(5).split('/');
        console.log(`sourceBucket: ${sourceBucketName}`);
        console.log(`fileName: '${fileName}`);

        // references to source and destination buckets
        const sourceBucket = storage.bucket(sourceBucketName);
        const destinationBucket = storage.bucket(generatedImagesBucketName);

        // locations on disk for files
        const originalFile = path.resolve(sourceDir, fileName);
        const thumbFile = path.resolve(destinationDir, fileName);

        // download the source file
        await sourceBucket.file(fileName).download({
            destination: originalFile
        });
        console.log(`image downloaded: ${originalFile}`);

        // create the thumbnail
        const resizeCrop = Promise.promisify(im.crop);
        await resizeCrop({
                srcPath: originalFile,
                dstPath: thumbFile,
                width: thumbnailDimension,
                height: thumbnailDimension
        });
        console.log(`thumbnail created: ${thumbFile}`);

        // upload thumbnail to bucket
        await destinationBucket.upload(thumbFile);
        console.log(`uploaded thumbnail to bucket ${generatedImagesBucketName}`);

        // modify existing entry in Firestore, noting that thumbnail exists now
        const imageStore = new Firestore().collection(firestoreCollectionName);
        const doc = imageStore.doc(fileName);
        await doc.set({
            thumbnail: true
        }, {merge: true});
        console.log(`updated Firestore doc for ${fileName}`);

        res.status(204).send(`${fileName} processed`);
    } catch (err) {
        console.log(`Error creating the thumbnail: ${err}`);
        console.error(err);
        res.status(500).send(err);
    }
});

const PORT = process.env.PORT || 8080;

app.listen(PORT, () => {
    if (!generatedImagesBucketName) throw new Error("GENERATED_IMAGES_BUCKET environment variable not set");
    console.log(`Started create-thumbnail service on port ${PORT}`);
});