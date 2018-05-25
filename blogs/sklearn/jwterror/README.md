To repeat the bug:
(1) In CloudShell, run ./install.sh
(2) run create_key.sh after setting the project number appropriately
(3) run query.py and pkg_query.py after setting the project id appropriately

Note that it works in CloudShell.

The same code doesn't work from within a container
(try it on ML Engine or Datalab, for example)
