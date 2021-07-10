uritemplate
===========

Documentation_ -- GitHub_ -- BitBucket_ -- Travis-CI_

Simple python library to deal with `URI Templates`_. The API looks like

.. code-block:: python

    from uritemplate import URITemplate, expand

    # NOTE: URI params must be strings not integers

    gist_uri = 'https://api.github.com/users/sigmavirus24/gists{/gist_id}'
    t = URITemplate(gist_uri)
    print(t.expand(gist_id='123456'))
    # => https://api.github.com/users/sigmavirus24/gists/123456

    # or
    print(expand(gist_uri, gist_id='123456'))

    # also
    t.expand({'gist_id': '123456'})
    print(expand(gist_uri, {'gist_id': '123456'}))

Where it might be useful to have a class

.. code-block:: python

    import requests

    class GitHubUser(object):
        url = URITemplate('https://api.github.com/user{/login}')
        def __init__(self, name):
            self.api_url = url.expand(login=name)
            response = requests.get(self.api_url)
            if response.status_code == 200:
                self.__dict__.update(response.json())

When the module containing this class is loaded, ``GitHubUser.url`` is 
evaluated and so the template is created once. It's often hard to notice in 
Python, but object creation can consume a great deal of time and so can the 
``re`` module which uritemplate relies on. Constructing the object once should 
reduce the amount of time your code takes to run.

Installing
----------

::

    pip install uritemplate.py

License
-------

Modified BSD license_


.. _Documentation: http://uritemplate.rtfd.org/
.. _GitHub: https://github.com/sigmavirus24/uritemplate
.. _BitBucket: https://bitbucket.org/icordasc/uritemplate
.. _Travis-CI: https://travis-ci.org/sigmavirus24/uritemplate
.. _URI Templates: http://tools.ietf.org/html/rfc6570
.. _license: https://github.com/sigmavirus24/uritemplate/blob/master/LICENSE


Changelog - uritemplate
=======================

2.0.0 - 2016-08-29
------------------

- Merge uritemplate.py into uritemplate


Changelog - uritemplate.py
==========================

2.0.0 - 2016-08-20
------------------

- Relicense uritemplate.py as Apache 2 and BSD (See
  https://github.com/sigmavirus24/uritemplate/pull/23)

1.0.1 - 2016-08-18
------------------

- Fix some minor packaging problems.

1.0.0 - 2016-08-17
------------------

- Fix handling of Unicode values on Python 2.6 and 2.7 for urllib.quote.

- Confirm public stable API via version number.

0.3.0 - 2013-10-22
------------------

- Add ``#partial`` to partially expand templates and return new instances of 
  ``URITemplate``.

0.2.0 - 2013-07-26
------------------

- Refactor the library a bit and add more tests.

- Backwards incompatible with 0.1.x if using ``URIVariable`` directly from
  ``uritemplate.template``

0.1.1 - 2013-05-19
------------------

- Add ability to get set of variable names in the current URI

- If there is no value or default given, simply return an empty string

- Fix sdist

0.1.0 - 2013-05-14
------------------

- Initial Release


