

def get_natality_query(data_size=10):
    '''
    generates a BigQuery query

    :param data_size: number of records to retrieve
    :return: string - BigQuery query
    '''


    query = """
            SELECT
              weight_pounds,
              is_male,
              mother_age,
              mother_race,
              plurality,
              gestation_weeks,
              mother_married,
              cigarette_use,
              alcohol_use
            FROM
              publicdata.samples.natality
            WHERE year > 2000
            AND weight_pounds > 0
            AND mother_age > 0
            AND plurality > 0
            AND gestation_weeks > 0
            AND month > 0
            LIMIT {}
        """.format(data_size)

    return query

