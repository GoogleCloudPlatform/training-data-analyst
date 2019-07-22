import json
from datetime import datetime
import argparse
import apache_beam as beam
from apache_beam.io import WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.internal.clients import bigquery
import logging
from apache_beam.io import ReadFromText
import random

play_by_play_schema = {
    'season': 'integer'
    , 'game_id': 'string'
    , 'is_home': 'integer'
    , 'event_id': 'integer'
    , 'is_neutral': 'string'
    , 'home_pts': 'integer'
    , 'away_pts': 'integer'
    , 'player_id': 'integer'
    , 'player_full_name': 'string'
    , 'game_date': 'date'
    , 'elapsed_time_sec': 'integer'
    , 'game_clock': 'string'
    , 'period': 'integer'
    , 'team_code': 'integer'
    , 'event_type': 'string'    
    , 'shot_made': 'boolean'    
    , 'shot_type': 'string'    
    , 'points_scored': 'integer'    
    , 'three_point_shot': 'boolean'    
    , 'rebound_type': 'string'    
    , 'timeout_duration': 'string'    
    , 'foul_type': 'string'    
    , 'substitution_type': 'string'    
}

class Format(beam.DoFn):
    def process(self, element):
        import logging
        import json
        from datetime import datetime
        try:
            j = json.loads(element)
        except:
            j = None
            logging.info('THERE_WAS_AN_ISSUE_WITH_THE_FOLLOWING: ' + str(element))
        if j and j != []:
            score_1_team = None
            score_2_team = None
            home_code = j[0]['game_id'].split('-')[0]
            i = 1
            for p in j:
                if p['actionType'] in ['2pt', '3pt', 'freethrow', 'rebound', 'block', 'assist', 'steal', 'turnover', 'foul', 'substitution', 'timeout']:
                    logging.info(p)
                    try:
                        team_code = int(p['teamExternalId'][2:])
                    except:
                        team_code = None
                    
                    if p['actionType'] in ['2pt', '3pt', 'freethrow'] and not score_1_team and not score_2_team:
                        if p['score1'] > p['score2'] and team_code == home_code:
                            score_1_team = 'home'
                            score_2_team = 'away'
                        elif p['score1'] > p['score2'] and team_code != home_code:
                            score_1_team = 'away'
                            score_2_team = 'home'
                        elif p['score2'] > p['score1'] and team_code == home_code:
                            score_1_team = 'away'
                            score_2_team = 'home'
                        elif p['score2'] > p['score1'] and team_code != home_code:
                            score_1_team = 'home'
                            score_2_team = 'away'

                    game_id_split = p['game_id'].split('-')
                    month = str(game_id_split[3]) if len(str(game_id_split[3])) > 1 else '0' + str(game_id_split[3])       
                    day = str(game_id_split[4]) if len(str(game_id_split[4])) > 1 else '0' + str(game_id_split[4])       

                    game_id = str(game_id_split[0]) + '-' + str(game_id_split[1]) + '-' + str(game_id_split[2]) + '-' + month + '-' + day

                    game_date = str(game_id_split[2]) + '-' + month + '-' + day
                    player_id = p['personExternalId'] if 'personExternalId' in p.keys() else None
                    home_pts = 0
                    away_pts = 0
                    shot_type = None
                    three_point_shot = False
                    points_scored = 0
                    rebound_type = None
                    substitution_type = None
                    foul_type = None
                    timeout_duration = None
                    shot_made = False

                    if 'firstName' in p.keys() and 'familyName' in p.keys():
                        player_full_name = p['firstName'].upper() + ',' + p['familyName'].upper()
                    elif 'firstName' in p.keys():
                        player_full_name = p['firstName'].upper()
                    elif 'familyName' in p.keys():
                        player_full_name = p['familyName'].upper()
                    else:
                        player_full_name = None

                    gc_split = p['clock'].split(':')
                    mins = int(gc_split[0])
                    sec = int(gc_split[1])

                    if p['periodType'] == 'REGULAR':
                        period = int(p['period'])
                    elif p['periodType'] == 'OVERTIME':
                        period = 2 + int(p['period'])

                    if period < 3:
                        min_passed = 19 - mins
                    else:
                        min_passed = 4 - mins    
                    sec_passed = 60 - sec

                    if period == 1:
                        elapsed_time_sec = (60 * min_passed) + sec_passed 
                    elif period == 2:
                        elapsed_time_sec = 1200 + (60 * min_passed) + sec_passed
                    elif period == 3:
                        elapsed_time_sec = 2400 + (60 * min_passed) + sec_passed
                    elif period > 3:
                        elapsed_time_sec = 2400 + (300 * (period - 3)) + (60 * min_passed) + sec_passed
                    
                    if p['actionType'] in ['2pt', '3pt', 'freethrow']:
                        if p['success'] == 1:
                            action_type = 'GOOD'
                            shot_made = True
                        elif p['success'] == 0:
                            action_type = 'MISS'
                            shot_made = False
                        if p['actionType'] == '3pt':
                            shot_type = '3PTR'
                            three_point_shot = True
                            if p['success'] == 1:
                                points_scored = 3
                            else:
                                points_scored = 0
                        elif p['actionType'] == 'freethrow':
                            shot_type = 'FT'
                            three_point_shot = False
                            if p['success'] == 1:
                                points_scored = 1
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] in ['layup', 'drivinglayup']:
                            three_point_shot = False
                            shot_type = 'LAYUP'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] in ['dunk']:
                            three_point_shot = False
                            shot_type = 'DUNK'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] in ['tipin']:
                            three_point_shot = False
                            shot_type = 'TIPIN'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] in ['jumpshot', 'floatingjumpshot', 'stepbackjumpshot', 'pullupjumpshot', 'turnaroundjumpshot', 'fadeaway']:
                            three_point_shot = False
                            shot_type = 'JUMPER'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] == 'hookshot':
                            three_point_shot = False
                            shot_type = 'HOOK'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        elif p['actionType'] == '2pt' and p['subType'] == 'alleyoop':
                            three_point_shot = False
                            shot_type = 'ALLEYOOP'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                        else:
                            three_point_shot = False
                            shot_type = 'OTHER'
                            if p['success'] == 1:
                                points_scored = 2
                            else:
                                points_scored = 0
                    else:
                        points_scored = 0
                        shot_made = False
                        three_point_shot = False
                        shot_type = None

                    if p['actionType'] == 'rebound' and p['subType'] not in ['offensivedeadball', 'defensivedeadball']:
                        action_type = 'REBOUND'
                        if p['subType'] == 'offensive':
                            rebound_type = 'OFF'
                        if p['subType'] == 'defensive':
                            rebound_type = 'DEF'
                    elif p['actionType'] == 'rebound' and p['subType'] in ['offensivedeadball', 'defensivedeadball']:
                        action_type = 'deadball'
                        rebound_type = 'DEADB'
                    else:
                        rebound_type = None

                    if p['actionType'] == 'block':
                        action_type = 'BLOCK'
                    elif p['actionType'] == 'assist':
                        action_type = 'ASSIST'
                    elif p['actionType'] == 'steal':
                        action_type = 'STEAL'
                    elif p['actionType'] == 'turnover':
                        action_type = 'TURNOVER'
                    
                    if p['actionType'] == 'foul':
                        action_type = 'FOUL'
                        if p['subType'] in ['technical', 'benchTechnical', 'coachTechnical', 'adminTechnical']:
                            foul_type = 'TECH'
                        else:
                            foul_type = None
                    else:
                        foul_type = None
                    
                    if p['actionType'] == 'substitution':
                        action_type = 'SUB'
                        if p['subType'] == 'in':
                            substitution_type = 'ON'
                        elif p['subType'] == 'out':
                            substitution_type = 'OFF'
                    else:
                        substitution_type = None

                    if p['actionType'] == 'timeout' and p['subType'] in ['media', 'commercial']:
                        action_type = 'TV_TIMEOUT'
                        timeout_duration = None
                    elif p['actionType'] == 'timeout':
                        if p['subType'] == 'full':
                            action_type = 'TIMEOUT'
                            timeout_duration = 'FULL'
                        elif p['subType'] == 'short':
                            action_type = 'TIMEOUT'
                            timeout_duration = '30SEC'
                        else:
                            action_type = 'TIMEOUT'
                            timeout_duration = None
                    else:
                        timeout_duration = None

                    if points_scored > 0:
                        if score_1_team == 'home':
                            home_pts = p['score1']
                            away_pts = p['score2']
                        else:
                            away_pts = p['score1']
                            home_pts = p['score2']

                    this_play = {
                        'season': p['season']
                        , 'event_id': i
                        , 'game_id': game_id
                        , 'is_home': 1 if team_code == home_code else 0
                        , 'is_neutral': p['neutral_site']
                        , 'home_pts': home_pts
                        , 'away_pts': away_pts
                        , 'player_id': player_id
                        , 'player_full_name': player_full_name
                        , 'game_date': game_date
                        , 'elapsed_time_sec': elapsed_time_sec
                        , 'game_clock': p['clock'][:5]
                        , 'period': period
                        , 'team_code': team_code
                        , 'event_type': action_type
                        , 'shot_made': shot_made
                        , 'shot_type': shot_type
                        , 'points_scored': points_scored
                        , 'three_point_shot': three_point_shot
                        , 'rebound_type': rebound_type
                        , 'timeout_duration': timeout_duration
                        , 'foul_type': foul_type
                        , 'substitution_type': substitution_type
                    }
                    yield this_play
                    i += 1
                else:
                    logging.info(p['actionType'] + ' is not in NCAA data')

class Check(beam.DoFn):
    def process(self, element):
        print 'new item'
        print element

def run(argv=None):
    import random
    import datetime

    currentDT = datetime.datetime.now()

    # Your GCP Project ID and GCS locations
    # are passed through as part of your Dataflow job command

    # BigQuery output info
    dataset = 'lab_dev'
    table = 'play_by_play'

    # Dataflow job name (don't edit)
    job_name = 'play-by-play-{}'.format(currentDT.strftime("%Y-%m-%d-%H-%M-%S"))
    filepath = 'gs://cloud-training-demos/ncaa/next-bootcamp/2018-19/play_by_play/*'
    
    pipeline_args = [
        # change these
      '--runner=DataflowRunner',
      '--project={}'.format(argv['project_id']),
      '--dataset={}'.format(dataset),
      '--table={}'.format(table),
      '--staging_location={}'.format(argv['staging']),
      '--temp_location={}'.format(argv['temp_location']),
      '--num_workers=5',
      '--max_num_workers=20',
      '--region={}'.format(argv['region']),
      '--job_name={}'.format(job_name)
    ]
    

    pipeline_options = PipelineOptions(pipeline_args)
  
    with beam.Pipeline(options=pipeline_options) as p:
        files = p | ReadFromText(filepath)

        keyed = files | 'Key' >> beam.Map(lambda x: (random.randint(1, 101), x))
        grouped = keyed | 'GBK' >> beam.GroupByKey()
        flattended = grouped | 'Expand' >> beam.FlatMap(lambda x: x[1])

        to_insert = flattended | 'Format' >> beam.ParDo(Format())
        
        # to_insert | beam.ParDo(Check())

        table_schema = bigquery.TableSchema()
        for col, col_type in play_by_play_schema.iteritems(): 
            this_schema = bigquery.TableFieldSchema()
            this_schema.name = col
            this_schema.type = col_type
            this_schema.mode = 'nullable'
            table_schema.fields.append(this_schema)

        to_insert | WriteToBigQuery(
                table='{_project_}:{_dataset_}.{_table_}'.format(_dataset_ = dataset, _project_ = argv['project_id'], _table_ = table),
                schema=table_schema,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project_id',
        help='Project ID where the job is to run',
        required=True
    )
    parser.add_argument(
        '--temp_location',
        help='Bucket to store output temporarily',
        required=True
    )
    parser.add_argument(
        '--staging',
        help='Folder on GCS to store ',
        required=True
    )
    parser.add_argument(
        '--region',
        help='Region where to run the job',
        required=True
    )
    
    args, _ = parser.parse_known_args()
    hparams = args.__dict__
    run(hparams)