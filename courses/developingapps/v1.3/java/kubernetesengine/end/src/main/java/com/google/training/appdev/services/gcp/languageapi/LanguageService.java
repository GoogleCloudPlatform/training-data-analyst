/*
 * Copyright 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.training.appdev.services.gcp.languageapi;

import com.google.cloud.language.v1.Document;
import com.google.cloud.language.v1.LanguageServiceClient;
import com.google.cloud.language.v1.Sentiment;

public class LanguageService {

    private static final LanguageService languageService= new LanguageService(){};

    public static LanguageService create(){
        return languageService;
    }

    public float analyseSentiment(String feedback)throws Exception{
        try (LanguageServiceClient language = LanguageServiceClient.create()) {


            Document doc = Document.newBuilder()
                    .setContent(feedback).setType(Document.Type.PLAIN_TEXT).build();

            Sentiment sentiment = language.analyzeSentiment(doc).getDocumentSentiment();

            System.out.printf("Feedback Text: %s%n", feedback);
            System.out.printf("Sentiment: %s, %s%n", sentiment.getScore(), sentiment.getMagnitude());
            return sentiment.getScore();
        }
    }
    private LanguageService(){ }
}
