
from google.cloud import bigquery
import google.cloud.storage as gcs
import tempfile
import os

def create_report(BUCKET, gcsfilename, tmpdir):
    """
    Creates report in gs://BUCKET/ based on contents in gcsfilename (gs://bucket/some/dir/filename)
    """
    # connect to BigQuery
    client = bigquery.Client()
    destination_table = client.get_table('sparktobq.kdd_cup')
    
    # Specify table schema. Autodetect is not a good idea for production code
    job_config = bigquery.LoadJobConfig()
    schema = [
        bigquery.SchemaField("duration", "INT64"),
    ]
    for name in ['protocol_type', 'service', 'flag']:
        schema.append(bigquery.SchemaField(name, "STRING"))
    for name in 'src_bytes,dst_bytes,wrong_fragment,urgent,hot,num_failed_logins'.split(','):
        schema.append(bigquery.SchemaField(name, "INT64"))
    schema.append(bigquery.SchemaField("unused_10", "STRING"))
    schema.append(bigquery.SchemaField("num_compromised", "INT64"))
    schema.append(bigquery.SchemaField("unused_12", "STRING"))
    for name in 'su_attempted,num_root,num_file_creations'.split(','):
        schema.append(bigquery.SchemaField(name, "INT64")) 
    for fieldno in range(16, 41):
        schema.append(bigquery.SchemaField("unused_{}".format(fieldno), "STRING"))
    schema.append(bigquery.SchemaField("label", "STRING"))
    job_config.schema = schema

    # Load CSV data into BigQuery, replacing any rows that were there before
    job_config.create_disposition = bigquery.CreateDisposition.CREATE_IF_NEEDED
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
    job_config.skip_leading_rows = 0
    job_config.source_format = bigquery.SourceFormat.CSV
    load_job = client.load_table_from_uri(gcsfilename, destination_table, job_config=job_config)
    print("Starting LOAD job {} for {}".format(load_job.job_id, gcsfilename))
    load_job.result()  # Waits for table load to complete.
    print("Finished LOAD job {}".format(load_job.job_id))
    
    # connections by protocol
    sql = """
        SELECT COUNT(*) AS count
        FROM sparktobq.kdd_cup
        GROUP BY protocol_type
        ORDER by count ASC    
    """
    connections_by_protocol = client.query(sql).to_dataframe()
    connections_by_protocol.to_csv(os.path.join(tmpdir,"connections_by_protocol.csv"))
    print("Finished analyzing connections")
    
    # attacks plot
    sql = """
                            SELECT 
                             protocol_type, 
                             CASE label
                               WHEN 'normal.' THEN 'no attack'
                               ELSE 'attack'
                             END AS state,
                             COUNT(*) as total_freq,
                             ROUND(AVG(src_bytes), 2) as mean_src_bytes,
                             ROUND(AVG(dst_bytes), 2) as mean_dst_bytes,
                             ROUND(AVG(duration), 2) as mean_duration,
                             SUM(num_failed_logins) as total_failed_logins,
                             SUM(num_compromised) as total_compromised,
                             SUM(num_file_creations) as total_file_creations,
                             SUM(su_attempted) as total_root_attempts,
                             SUM(num_root) as total_root_acceses
                           FROM sparktobq.kdd_cup
                           GROUP BY protocol_type, state
                           ORDER BY 3 DESC
    """
    attack_stats = client.query(sql).to_dataframe()
    ax = attack_stats.plot.bar(x='protocol_type', subplots=True, figsize=(10,25))
    ax[0].get_figure().savefig(os.path.join(tmpdir,'report.png'));
    print("Finished analyzing attacks")
    
    bucket = gcs.Client().get_bucket(BUCKET)
    for blob in bucket.list_blobs(prefix='sparktobq/'):
        blob.delete()
    for fname in ['report.png', 'connections_by_protocol.csv']:
        bucket.blob('sparktobq/{}'.format(fname)).upload_from_filename(os.path.join(tmpdir,fname))
    print("Uploaded report based on {} to {}".format(gcsfilename, BUCKET))


def bigquery_analysis_cf(data, context):
    # check that trigger is for a file of interest
    bucket = data['bucket']
    name = data['name']
    if ('kddcup' in name) and not ('gz' in name):
        filename = 'gs://{}/{}'.format(bucket, data['name'])
        print(bucket, filename)
        with tempfile.TemporaryDirectory() as tmpdir:
            create_report(bucket, filename, tmpdir)
