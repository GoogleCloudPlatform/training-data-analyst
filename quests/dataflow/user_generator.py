# Generates random users for a website

import argparse
from faker import Faker
import geocoder
from random import choice

parser = argparse.ArgumentParser(__file__, description="Web Server Data Generator")
parser.add_argument("--num_users", "-u", type=int, dest="num_users",
                    help="The number of users to create", default=100)

args = parser.parse_args()
num_users = int(args.num_users)

faker = Faker()
# A list of functions for generating user agent strings for various browsers
ualist = [faker.firefox, faker.chrome, faker.safari, faker.internet_explorer, faker.opera]

sensitive_fields = ['lat', 'lng', 'ip', 'user_agent']

def generate_user():
    """
    Returns a randomly generate dictionary representing a user, where each user is described by
    a user agent string, an ID, a latlng, an IP, an age_bracket, whether they've oped into marketing
    and the
    :return:
    """
    user = {}
    user['lat'] = ""
    user['lng'] = ""
    while user['lat'] == "" or user['lng'] == "":
        user['ip'] = faker.ipv4()
        g = geocoder.ip(user['ip'])
        latlng = list(map(str, g.latlng))
        if len(latlng) == 2:
            user['lat'] = latlng[0]
            user['lng'] = latlng[1]
    user['user_agent'] = choice(ualist)()
    user['age_bracket'] = choice(['18-25', '26-40', '41-55', '55+'])
    user['opted_into_marketing'] = choice([True, False])
    user['id'] = hash(str(user['ip']) + str(user['lat'] + str(user['lng'])))
    return user

def write_csvs(users):
    """
    Writes two .csv files, one for ingestiong by an event generator, the other formatted to be uploaded to BigQuery
    :param users:
    :return:
    """
    with open("users.csv", 'w') as event_out, open("users_bq.txt", 'w') as bq_out:
            cols = list(users[0].keys())
            cols.sort()
            bq_cols = cols.copy()
            [bq_cols.remove(s) for s in sensitive_fields]
            event_out.write(",".join(cols) + '\n')
            for user in users:
                event_vals = [str(user[key]) for key in cols]
                event_out.write(",".join(event_vals) + '\n')
                bq_vals = [str(user[key]) for key in bq_cols]
                bq_out.write(",".join(bq_vals) + '\n')

if __name__ == '__main__':
    users = [generate_user() for i in range(num_users)]
    write_csvs(users)
