# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

# TODO: Import the spanner module



# END TODO

"""
Get spanner management objects
"""

# TODO: Create a spanner Client



# END TODO


# TODO: Get a reference to the Cloud Spanner quiz-instance



# END TODO

# TODO: Get a reference to the Cloud Spanner quiz-database



# END TODO

"""
Takes an email address and reverses it (to be used as primary key)
"""
def reverse_email(email):
    return '_'.join(list(reversed(email.replace('@','_').
                        replace('.','_').
                        split('_'))))

"""
Persists feedback data into Spanner
- create primary key value
- do a batch insert (even though it's a single record)
"""
def save_feedback(data):
    # TODO: Create a batch object for database operations

    
        # TODO: Create a key for the record
        # from the email, quiz and timestamp

        


        # END TODO

        # TODO: Use the batch to insert a record
        # into the feedback table
        # This needs the columns and values

        






        

        # END TODO

    # END TODO

