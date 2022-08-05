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
const im = require('imagemagick');
const Promise = require("bluebird");
const path = require('path');
const {Storage} = require('@google-cloud/storage');
const storage = new Storage();
const Firestore = require('@google-cloud/firestore');

const app = express();

const maxImages = 4;
const thumbnailBucketName = process.env.THUMBNAIL_BUCKET;

app.get('/', async (req, res) => {
    try {
        console.log('Collage request');

        const thumbnailFiles = [];
        const imageStore = new Firestore().collection('images');
        const snapshot = await imageStore
            .where('thumbnail', '==', true)
            .orderBy('created', 'desc')
            .limit(maxImages).get();

        if (snapshot.empty) {
            console.log('Empty collection, no collage to make');
            res.status(204).send("No collage created.");
        } else {
            snapshot.forEach(doc => {
                thumbnailFiles.push(doc.id);
            });
            console.log(`Image files: ${JSON.stringify(thumbnailFiles)}`);

            const thumbBucket = new Storage().bucket(thumbnailBucketName);

            await Promise.all(thumbnailFiles.map(async fileName => {
                const filePath = path.resolve('/tmp', fileName);
                console.log(`Downloading ${fileName}...`);
                await thumbBucket.file(fileName).download({
                    destination: filePath
                });
            }));
            console.log('Downloaded all thumbnails');

            const collagePath = path.resolve('/tmp', 'collage.png');

            const thumbnailPaths = thumbnailFiles.map(f => path.resolve('/tmp', f));
            const convert = Promise.promisify(imageMagick.convert);
            await convert([
                '(', ...thumbnailPaths.slice(0, 2), '+append', ')',
                '(', ...thumbnailPaths.slice(2), '+append', ')',
                '-size', '400x400', 'xc:none', '-background', 'none',  '-append', '-trim',
                collagePath]);
            console.log("Created local collage picture");

            await thumbBucket.upload(collagePath);
            console.log(`Uploaded collage to bucket ${thumbnailBucketName}`);

            res.status(204).send("Collage created.");
        }
    } catch (err) {
        console.log(`Error: creating the collage: ${err}`);
        console.error(err);
        res.status(500).send(err);
    }
});

const PORT = process.env.PORT || 8080;

app.listen(PORT, () => {
    if (!thumbnailBucketName) throw new Error("THUMBNAIL_BUCKET environment variable not set");
    console.log(`Started create-collage service on port ${PORT}`);
});
