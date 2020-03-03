local params = std.extVar('__ksonnet/params');
local globals = import 'globals.libsonnet';
local envParams = params + {
  components+: {
    "search-index-server"+: {
      dataDir: 'gs://code-search-demo/models/20181107-dist-sync-gpu',
      indexFile: 'gs://code-search-demo/20181104/code-embeddings-index/embeddings.index',
      lookupFile: 'gs://code-search-demo/20181104/code-embeddings-index/embedding-to-info.csv',
    },
    "query-embed-server"+: {
      modelBasePath: 'gs://code-search-demo/models/20181107-dist-sync-gpu/export/',
    },
  },
};

{
  components: {
    [x]: envParams.components[x] + globals
    for x in std.objectFields(envParams.components)
  },
}