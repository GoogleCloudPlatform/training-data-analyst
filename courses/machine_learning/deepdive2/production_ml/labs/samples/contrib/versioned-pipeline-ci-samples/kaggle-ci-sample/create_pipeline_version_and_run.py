import kfp
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--commit_sha', help='Required. Commit SHA, for version name. Must be unique.', type=str)
parser.add_argument('--pipeline_id', help = 'Required. pipeline id',type=str)
parser.add_argument('--bucket_name', help='Required. gs bucket to store files', type=str)
parser.add_argument('--gcr_address', help='Required. Cloud registry address. For example, gcr.io/my-project', type=str)
parser.add_argument('--host', help='Host address of kfp.Client. Will be get from cluster automatically', type=str, default='')
parser.add_argument('--run_name', help='name of the new run.', type=str, default='')
parser.add_argument('--experiment_id', help = 'experiment id',type=str)
parser.add_argument('--code_source_url', help = 'url of source code', type=str, default='')
args = parser.parse_args()

if args.host:
    client = kfp.Client(host=args.host)
else:
    client = kfp.Client()

#create version
import os
package_url = os.path.join('https://storage.googleapis.com', args.bucket_name.lstrip('gs://'), args.commit_sha, 'pipeline.zip')
version_name = args.commit_sha
version_body = {"name": version_name, \
"code_source_url": args.code_source_url, \
"package_url": {"pipeline_url": package_url}, \
"resource_references": [{"key": {"id": args.pipeline_id, "type":3}, "relationship":1}]}

response = client.pipelines.create_pipeline_version(version_body)
version_id = response.id
# create run
run_name = args.run_name if args.run_name else 'run' + version_id
resource_references = [{"key": {"id": version_id, "type":4}, "relationship":2}]
if args.experiment_id:
    resource_references.append({"key": {"id": args.experiment_id, "type":1}, "relationship": 1})
run_body={"name":run_name,
          "pipeline_spec":{"parameters": [{"name": "bucket_name", "value": args.bucket_name}, 
                                          {"name": "commit_sha", "value": args.commit_sha}]},
          "resource_references": resource_references}
try:
    client.runs.create_run(run_body)
except:
    print('Error Creating Run...')



    
