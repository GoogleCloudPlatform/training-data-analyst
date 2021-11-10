#!/bin/bash

echo "There is now a better way to access Jupyter ... use Dataproc Hub directly from the web console. You don't need any of the proxying now!   https://cloud.google.com/dataproc/docs/tutorials/dataproc-hub-users "

exit;

rm -rf /tmp/junk
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="socks5://localhost:1080" \
  --host-resolver-rules="MAP * 0.0.0.0 , EXCLUDE localhost" \
  --user-data-dir=/tmp/junk
