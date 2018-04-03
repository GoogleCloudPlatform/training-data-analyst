import math
import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from google.cloud import bigquery

# A Python-based dataflow pipeline that finds Java packages on github that are: 
# (a) used a lot by other projects (we count the number of times this package appears 
# in imports elsewhere) (b) needs help (count the number of times this package has
# the words FIXME or TODO in its source).
#
# WARNING: don't forget to follow the installation steps in 
#   https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python
#   otherwise you will get an error "Request had invalid authentication credentials"
#   after a few minutes of running

bq_query = "SELECT content FROM [fh-bigquery:github_extracts.contents_java_2016]"


def splitPackageName(packageName):
    '''E.g. given 'com.example.appname.library.widgetname'
           returns ['com', 'com.example', 'com.example.appname']
    '''
    result = []
    end = packageName.find('.')
    while end > 0:
        result.append(packageName[0:end])
        end = packageName.find('.', end+1)
    result.append(packageName)
    return result


def get_lines(element):
    '''Each element has a content field that contains the source code committed: return an iterator over its lines'''
    source_code = element['content']
    if source_code: 
        for line in source_code.split('\n'):
            yield line
            

def getPackages(line, keyword):
    '''E.g. given keyword=import and line="import com.example.appname.library.widgetname;\n"
           returns ['com', 'com.example', 'com.example.appname']
    '''
    start = line.find(keyword) + len(keyword)
    end = line.find(';', start)
    if start < end:
        packageName = line[start:end].strip()
        return splitPackageName(packageName)
    return []


def parsePackageStatement(line):
    '''Return an iterator over the list of packages that identify the package for a file. E.g. 
    given "package A.B.C;", returns ["A", "A.B", "A.B.C"] where for any line that does not
    represent a package declaration, returns [].
    '''
    keyword = "package"
    if line.startswith(keyword):
        # only one package statement per file
        packages = getPackages(line, keyword)
        return packages
        
    return []


def flagHelpNeeded(line):
    '''If the line is a package id line, creates an iterator over the packages as (package_name, 1) values'''
    packages = parsePackageStatement(line)
    for package_name in packages:
        yield (package_name, 1)


def composite_score(popularity, needs_help):
    '''Compose the popularity score (how many times a package is imported) with the needs_help side-input'''
    num_need_help = needs_help.get(popularity[0])
    score = 0 if num_need_help is None else math.log(popularity[1]) * math.log(num_need_help)
    return (popularity[0], score)
    
    
class IsPopular(beam.PTransform):
    '''Count how popular packages are, by counting how many times each one gets imported (as 
    represented by github source repos)
    '''
    
    def __init__(self):
        self.keyword = 'import'
        
    def expand(self, pcollection):
        return (pcollection
                  | 'GetImports' >> beam.FlatMap(lambda line: self.__startsWith(line, self.keyword))
                  | 'PackageUse' >> beam.FlatMap(lambda line: self.__packageUse(line, self.keyword))
                  | 'TotalUse' >> beam.CombinePerKey(sum))

    @staticmethod
    def __startsWith(line, term):
        '''Returns the line only if it starts with 'term'.'''
        if line.startswith(term):
            yield line

    @staticmethod
    def __packageUse(line, keyword):
        '''Return an iterator over package count pairs. E.g. given keyword=import and 
        line="import com.example.appname.library.widgetname;\n", yields ('com', 1), 
        then ('com.example', 1) and finally ('com.example.appname', 1)
        '''
        packages = getPackages(line, keyword)
        for p in packages:
            yield (p, 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Demonstrate side inputs')
    parser.add_argument('--bucket', required=True, help='Specify Cloud Storage bucket for output')
    parser.add_argument('--project', required=True, help='Specify Google Cloud project')
    parser.add_argument('--cloud', action='store_true', help='Run in cloud instead of local')
    opts = parser.parse_args()

    options = PipelineOptions()
    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = opts.project
    google_cloud_options.job_name = 'java-projects-needing-help'
    google_cloud_options.staging_location = 'gs://%s/staging' % opts.bucket
    google_cloud_options.temp_location = 'gs://%s/temp' % opts.bucket
    if opts.cloud: 
        print 'ATTENTION: will run this job in Google Cloud DataFlow instead of locally'
        options.view_as(StandardOptions).runner = 'DataflowRunner'
        options.view_as(SetupOptions).save_main_session = True
    else:
        # if local, only test on first 10 files of DB
        bq_query += " LIMIT 10"
   
    p = beam.Pipeline(options=options)

    input = 'fh-bigquery:github_extracts.contents_py'
    output_prefix = 'gs://%s/java-need-help' % opts.bucket
    
    def print_row(row):
        print row
        return row

    # find most used packages 
    all_lines = (p
      | 'GetContents' >> beam.io.Read(beam.io.BigQuerySource(query=bq_query))
      | 'GetLines' >> beam.FlatMap(get_lines)
    )
      
    needs_help = (all_lines
      | "FlagHelpNeeded" >> beam.FlatMap(flagHelpNeeded)
      | "SumByKey" >> beam.CombinePerKey(sum)
      # without the following transform, an assertion in beam source fails, related to side-input visitation:
      | "view" >> beam.Map(lambda x: x)  
      # | "print" >> beam.Map(print_row)
    )
    
    NUM_SCORES = 10
    
    results = (all_lines
      | 'IsPopular' >> IsPopular()
      | 'ComposositeScore' >> beam.Map(composite_score, beam.pvalue.AsDict(needs_help))
      | 'Top_N' >> beam.transforms.combiners.Top.Of(NUM_SCORES, lambda x1, x2: x1[1] < x2[1])
      | 'write' >> beam.io.WriteToText(output_prefix)
      # | "print2" >> beam.Map(print_row)
    )

    p.run().wait_until_finish()
    print 'Output sent to %s-*' % output_prefix
