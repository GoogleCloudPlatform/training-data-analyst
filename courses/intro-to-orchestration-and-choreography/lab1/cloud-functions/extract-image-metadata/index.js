// Copyright 2022, Google, Inc.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

exports.extract_image_metadata = (req, res) => {
    console.log(`Image analysis response: ${JSON.stringify(req.body)}`);

    const analysis = req.body.responses[0];
    console.log(`Analysis: ${JSON.stringify(analysis)}`);

    // check for image safety
    const safeSearchAnnotation = analysis.safeSearchAnnotation;

    // if any of the SafeSearch categories are likely or very likely,
    // the image is not considered safe
    const isSafe = ["adult", "medical", "racy", "spoof", "violence"]
            .every(val => !['LIKELY', 'VERY_LIKELY'].includes(safeSearchAnnotation[val]));
    console.log(`SAFE: ${isSafe}`);

    // find the labels found for the picture
	console.log('LABELS:')
    const labels = analysis.labelAnnotations
        .sort((val1, val2) => val2.score - val1.score)
        .map(val => {
			console.log(`${val.description}`);
            return { stringValue: val.description }
        })

    // retrieve any text found in the picture
    const fullText = analysis.fullTextAnnotation.text;
    console.log(`TEXT:`);
    console.log(`${fullText}`);

    res.json({
        safe: isSafe,
        labels: labels,
        text: fullText,
        created: new Date()
    });
};

