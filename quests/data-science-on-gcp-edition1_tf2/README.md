# data-science-on-gcp

Source code accompanying book:

<table>
<tr>
  <td>
  <img src="https://images-na.ssl-images-amazon.com/images/I/51dgw%2BCYSOL._SX379_BO1,204,203,200_.jpg" height="100"/>
  </td>
  <td>
  Data Science on the Google Cloud Platform, 2nd Edition <br/>
  Valliappa Lakshmanan <br/>
  O'Reilly, Jan 2022
  </td>
  <td>
  Branch <a href="https://github.com/GoogleCloudPlatform/data-science-on-gcp/">edition2</a> [being built]
  </td>
</tr>
<tr>
  <td>
  <img src="https://images-na.ssl-images-amazon.com/images/I/51dgw%2BCYSOL._SX379_BO1,204,203,200_.jpg" height="100"/>
  </td>
  <td>
  Data Science on the Google Cloud Platform <br/>
  Valliappa Lakshmanan <br/>
  O'Reilly, Jan 2017
  </td>
  <td>
  Branch <a href="https://github.com/GoogleCloudPlatform/training-data-analyst/tree/master/quests/data-science-on-gcp-edition1_tf2">edition1_tf2</a> (also: )
  </td>
</table>

### Try out the code on Google Cloud Platform
<a href="https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/data-science-on-gcp&page=editor&open_in_editor=README.md"> <img alt="Open in Cloud Shell" src ="http://gstatic.com/cloudssh/images/open-btn.png"></a>

The code on Qwiklabs (see below) is **continually tested**, and this repo is kept up-to-date.
The code should work as-is for you, however, there are three very common problems that readers report:
* <i>Ch 2: Download data fails.</i> The Bureau of Transportation website to download the airline dataset periodically goes down or changes availability due to government furloughs and the like.
Please use the instructions in 02_ingest/README.md to copy the data from my bucket. The rest of the chapters work off the data in the
bucket, and will be fine.
* <i>Ch 3: Permission errors.</i> These typically occur because we expect that you will copy the airline data to your bucket. You don't have write access to gs://cloud-training-demos-ml/. The instructions will tell you to change the bucket name to one that you own. Please do that.
* <i>Ch 4, 10: Dataflow doesn't do anything.</i>. The real-time simulation requires that you simultaneously run simulate.py and the Dataflow pipeline. If the Dataflow pipeline is not progressing, make sure that the simulate program is still running.

If the code doesn't work for you, I recommend that you try the corresponding Qwiklab lab to see if there is some step that you missed.
If you still have problems, please leave feedback in Qwiklabs, or file an issue in this repo.

### Try out the code on Qwiklabs

- [Data Science on the Google Cloud Platform Quest](https://google.qwiklabs.com/quests/43)
- [Data Science on Google Cloud Platform: Machine Learning Quest](https://google.qwiklabs.com/quests/50)



### Purchase book
[Read on-line or download PDF of book](http://shop.oreilly.com/product/0636920057628.do)

[Buy on Amazon.com](https://www.amazon.com/Data-Science-Google-Cloud-Platform/dp/1491974567)

### Updates to book
I updated the book in Nov 2019 with TensorFlow 2.0, Cloud Functions, and BigQuery ML.
