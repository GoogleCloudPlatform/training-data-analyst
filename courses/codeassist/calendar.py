# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def number_to_roman(number):
    number = int(number)
    roman = ""

    while number >= 1000:
        roman += "M"
        number -= 1000

    if number >= 500:
        roman += "D"
        number -= 500

    while number >= 100:
        roman += "C"
        number -= 100

    if number >= 50:
        roman += "L"
        number -= 50

    while number >= 10:
        roman += "X"
        number -= 10

    if number >= 5:
        roman += "V"
        number -= 5

    while number >= 1:
        roman += "I"
        number -= 1

    return roman