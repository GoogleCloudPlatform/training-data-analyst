// Data for various experiments.
// Paths are deliberately hard coded so they get versioned and checked into source control.
{
  "demo-trainer-11-07-dist-sync-gpu": {
    name: "demo-trainer-11-07-dist-sync-gpu",
    outputDir: "gs://code-search-demo/models/20181107-dist-sync-gpu",
    train_steps: 200000,
    eval_steps: 100,
    hparams_set: "transformer_base",
    project: "code-search-demo",    
    modelDir: "gs://code-search-demo/models/20181107-dist-sync-gpu/export/1541712907/", 

    problem: "kf_github_function_docstring",
    model: "kf_similarity_transformer",

    // The table containing the token pairs for (docstring, code)
    bqDataset: "code_search",
    //tokenPairsBQTable: self.project,
    //functionEmbeddingsBQTable: "someothervalue",
    tokenPairsBQTable: self.project + ":" + self.bqDataset + ".token_pairs",
    failedTokenizeBQTable: self.project + ":" + self.bqDataset + ".failed_tokenize",
    jobNameSuffix: "20181201-1530",
    bqSuffix: std.strReplace(self.jobNameSuffix, "-", "_"),
    functionEmbeddingsBQTable: self.project + ":" + self.bqDataset + ".code_embeddings_" + self.bqSuffix,

    // Location where the function embeddings should be written.
    functionEmbeddingsDir: "gs://code-search-demo/20181130/code_embeddings",

    // Location to write the index file for nmslib and the file to be used as the reverse lookup
    // with the index server.
    lookupFile: "gs://code-search-demo/20181104/code-embeddings-index/embedding-to-info.csv",
    indexFile: "gs://code-search-demo/20181104/code-embeddings-index/embeddings.index",
  },
  "pipeline": {
    name: "pipeline",
    problem: "kf_github_function_docstring",
    project: "code-search-demo",
  },
}
