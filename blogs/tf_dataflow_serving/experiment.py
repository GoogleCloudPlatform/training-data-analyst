
PARAMS = None


def initialise_hyper_params(args_parser):

    args_parser.add_argument(
        '--project_id',
        help="""
        Google Cloud project id\
        """,
        default='ksalama-gcp-playground',
    )

    args_parser.add_argument(
        '--experiment-type',
        help="""
        Can be either: batch-predict,  batch, stream-m-batches, or stream\
        """,
        default='batch-predict',
    )

    args_parser.add_argument(
        '--runner',
        help="""
        Can be either: DirectRunner or DataflowRunner\
        """,
        default='DirectRunner',
    )

    args_parser.add_argument(
        '--inference-type',
        help="""
        Can be either: local, cmle, or None\
        """,
        default='None',
    )

    ###########################################
    # batch parameters

    args_parser.add_argument(
        '--batch-sample-size',
        help="""
        Sample size to fetch from BigQuery table in batch pipelines\
        """,
        default=100,
        type=int
    )

    args_parser.add_argument(
        '--sink-dir',
        help="""
        GCS location or local directory to save the outputs of the batch pipelines\
        """,
        default='local_dir/outputs',
    )

    ###########################################
    # steaming parameters

    args_parser.add_argument(
        '--pubsub-topic',
        help="""
        Cloud Pub/Sub topic to send the messages to\
        """,
        default='babyweights',
    )

    args_parser.add_argument(
        '--pubsub-subscription',
        help="""
        Cloud Pub/Sub subscription to receive the messages from\
        """,
        default='babyweights-sub',
    )

    args_parser.add_argument(
        '--bq-dataset',
        help="""
        Name of the BigQuery dataset that has the table to receive the ingested messages\
        """,
        default='playground_ds',
    )

    args_parser.add_argument(
        '--bq-table',
        help="""
        Name of the BigQuery table to receive the ingested messages\
        """,
        default='babyweight_estimates',
    )

    args_parser.add_argument(
        '--window-size',
        help="""
        window size in seconds in micro-batches streaming pipeline\
        """,
        default=1,
        type=int
    )

    global PARAMS

    PARAMS = args_parser.parse_args()











