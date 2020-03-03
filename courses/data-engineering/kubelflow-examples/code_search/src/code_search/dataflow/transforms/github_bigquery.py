import code_search.dataflow.transforms.bigquery as bq_transform


# Default internal table names
PAIRS_TABLE = 'token_pairs'
FAILED_TOKENIZE_TABLE = 'failed_tokenize'
FUNCTION_EMBEDDINGS_TABLE = 'function_embeddings'


class ReadGithubDataset(bq_transform.BigQueryRead):
  """Read original Github files from BigQuery.

  This utility Transform reads Python files
  from a BigQuery public dump which are smaller
  than 15k lines of code, contain at least one
  function definition and its repository has been
  watched at least twice since 2017.

  NOTE: Make sure to modify the `self.limit` property
  as desired.
  """

  @property
  def limit(self):
    # return 500
    return None

  @property
  def query_string(self):
    query = """
      SELECT
        MAX(CONCAT(f.repo_name, ' ', f.path)) AS repo_path,
        c.content
      FROM
        `bigquery-public-data.github_repos.files` AS f
      JOIN
        `bigquery-public-data.github_repos.contents` AS c
      ON
        f.id = c.id
      JOIN (
          --this part of the query makes sure repo is watched at least twice since 2017
        SELECT
          repo
        FROM (
          SELECT
            repo.name AS repo
          FROM
            `githubarchive.year.2017`
          WHERE
            type="WatchEvent"
          UNION ALL
          SELECT
            repo.name AS repo
          FROM
            `githubarchive.month.2018*`
          WHERE
            type="WatchEvent" )
        GROUP BY
          1
        HAVING
          COUNT(*) >= 2 ) AS r
      ON
        f.repo_name = r.repo
      WHERE
        f.path LIKE '%.py' AND --with python extension
        c.size < 15000 AND --get rid of ridiculously long files
        REGEXP_CONTAINS(c.content, r'def ') --contains function definition
      GROUP BY
        c.content
    """

    if self.limit:
      query += '\nLIMIT {}'.format(self.limit)
    return query


class ReadTransformedGithubDatasetQuery(object):

  def __init__(self, table, limit=None):
    """Query to select the transformed (token pairs) from BigQuery.

    Args:
      table: The table to query.
      limit: Limit if needed.
    """
    self.table = table
    self.limit = limit

  @property
  def query_string(self):
    # https://cloud.google.com/bigquery/docs/reference/standard-sql/enabling-standard-sql
    table = self.table
    # In SQL queries table format uses period not :.
    table = table.replace(":", ".")
    query = """
      SELECT
        nwo, path, function_name, lineno, original_function, function_tokens, docstring_tokens
      FROM
        `{0}`
    """.format(table)

    if self.limit:
      query += '\nLIMIT {}'.format(self.limit)
    return query
