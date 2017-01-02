"""
`appengine_config.py` gets loaded every time a new instance is started.

Use this file to configure app engine modules as defined here:
https://developers.google.com/appengine/docs/python/tools/appengineconfig

From:
http://blog.jonparrott.com/managing-vendored-packages-on-app-engine/
"""


def add_vendor_packages(vendor_folder):
    """
    Adds our vendor packages folder to sys.path so that third-party
    packages can be imported.
    """
    import site
    import os.path
    import sys

    # Use site.addsitedir() because it appropriately reads .pth
    # files for namespaced packages. Unfortunately, there's not an
    # option to choose where addsitedir() puts its paths in sys.path
    # so we have to do a little bit of magic to make it play along.

    # We're going to grab the current sys.path and split it up into
    # the first entry and then the rest. Essentially turning
    #   ['.', '/site-packages/x', 'site-packages/y']
    # into
    #   ['.'] and ['/site-packages/x', 'site-packages/y']
    # The reason for this is we want '.' to remain at the top of the
    # list but we want our vendor files to override everything else.
    sys.path, remainder = sys.path[:1], sys.path[1:]

    # Now we call addsitedir which will append our vendor directories
    # to sys.path (which was truncated by the last step.)
    site.addsitedir(os.path.join(os.path.dirname(__file__), vendor_folder))

    # Finally, we'll add the paths we removed back.
    sys.path.extend(remainder)

# Change 'lib' to whichever directory you use for your vendored packages.
add_vendor_packages('lib')

