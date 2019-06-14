# Get a record count of a table in the baseline, flat, and nested table sets and compare the count
# issue a warning when count doesn't match across the 3 sets of tables
# run this script after loading all the tables and before running the benchmark queries
from google.cloud import bigquery

project_id ='project-id-here'
baseline_dataset = 'tpcds_2t_baseline'  
flat_dataset = 'tpcds_2t_flat_part_clust' 
nested_dataset = 'tpcds_2t_nest_part_clust'

client = bigquery.Client()
baseline_dataset_id = client.dataset(baseline_dataset, project=project_id)
flat_dataset_id = client.dataset(flat_dataset, project=project_id)
nested_dataset_id = client.dataset(nested_dataset, project=project_id)

baseline_table_list = client.list_tables(baseline_dataset_id)

def get_row_count(dataset, table):
    query_str = ('select count(*) from `' + project_id + '.' + dataset + '.' + table + '`')   
    query_job = client.query(query_str) 
    rows = query_job.result() 

    for row in rows:
        row_count = row.values()[0]
    
    return row_count

for table_item in baseline_table_list:
    baseline_table_ref = table_item.reference
    table_name = baseline_table_ref.table_id
    print("table_name: " + table_name)
    
    if str(table_name) == "dbgen_version":
        continue
    
    baseline_row_count = get_row_count(baseline_dataset, table_name)
    flat_row_count = get_row_count(flat_dataset, table_name)
            
    if str(table_name) == "date_dim" or str(table_name) == "time_dim" or str(table_name) == "income_band":
        if baseline_row_count == flat_row_count:
            print("INFO: record count matches for " + table_name + " (" + str(baseline_row_count) + ").")
        else:
            print("WARNING: record count doesn\'t match for " + table_name + ". baseline = " + str(baseline_row_count) + ", flat = "
                  + str(flat_row_count) + ".")
    else:
        nested_row_count = get_row_count(nested_dataset, table_name)
    
        if baseline_row_count == flat_row_count and flat_row_count == nested_row_count:
            print("INFO: record count matches for " + table_name + " (" + str(baseline_row_count) + ").")
        else:
            print("WARNING: record count doesn\'t match for " + table_name + ". baseline = " + str(baseline_row_count) + ", flat = "
                  + str(flat_row_count) + ", nested = " + str(nested_row_count) + ".")
        
 