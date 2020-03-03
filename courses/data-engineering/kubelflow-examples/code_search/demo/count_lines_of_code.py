"""Count lines of code in different types of file.

This has nothing to do with actually running code search.

The sole purpose of this script is to collect data for the presentation to
illustrate the point that most effort isn't spent on ML.
"""

import argparse
import csv
import logging
import os
import re
import sys
import tempfile

# Mapping from categories to regexes to include
# These are applied to the full path.
MATCH_RES = {
  "dataflow": [re.compile(r".*dataflow.*\.py")],
  "packaging (e.g dockerfile)": [
    re.compile(".*Dockerfile.*"),
    re.compile(r"code_search/src/.*requirements.*\.txt")],
  "cloud config": [re.compile(".*gcp_config.*")],
  "k8s & kubeflow config": [
    re.compile(r".*/cs-demo-1103/ks_app/components/.*"),
    re.compile(r".*/cs-demo-1103/k8s_specs/.*")],
  "model": [
    re.compile(r".*t2t/.*\.py")
  ],
  "serving k8s config": [
    re.compile(r".*/ks-web-app/components/.*"),
  ],
  "batch k8s config": [
    re.compile(r".*/kubeflow/components/.*"),
  ],
  "serving code": [
      re.compile(r".*/code_search/nmslib/.*\.py"),
      re.compile(r".*/ui.*\.js$"),
  ],
}

# Regexes matching files to exclude
NAME_EXCLUDES = [
  re.compile(r".*\.pyc"),
  re.compile(r"__init__\.py"),
]

class Results(object):
  def __init__(self):
    self.files = []
    self.loc = 0

  def add_file(self, full_path):
    self.files.append(full_path)
    with open(full_path) as hf:
      lines = hf.readlines()
      self.loc += len(lines)

  @property
  def num_files(self):
    return len(self.files)

def classify_files(root_dir):
  """Return lists of files in different categories

  Args:
    root_dir: Root directory to begin searching in

  Returns:
    categories: Dictionary mapping a category to list of files.
  """
  categories = {}
  for k in MATCH_RES.iterkeys():
    categories[k] = Results()

  for root, _, files in os.walk(root_dir):
    for name in files:
      full_path = os.path.join(root, name)
      exclude = False
      for m in NAME_EXCLUDES:
        if m.match(name):
          exclude = True
          break
      if exclude:
        continue
      for k, patterns in MATCH_RES.iteritems():
        for p in patterns:
          if p.match(full_path):
            categories[k].add_file(full_path)
            break

  return categories

def main():
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)

  parser = argparse.ArgumentParser(
     description="Create a CSV file containing # of PRs by company.")

  parser.add_argument(
    "--output",
    default="",
    type=str,
    help="The file to write.")

  args = parser.parse_args()

  if not args.output:
    with tempfile.NamedTemporaryFile(prefix="tmpCS_demo_code_stats", dir=None,
                                     suffix=".csv",
                                     delete=True) as hf:
      args.output = hf.name
    logging.info("--output not specified; defaulting to %s", args.output)

  root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
  logging.info("root_dir")

  categories = classify_files(root_dir)

  for k, v in categories.iteritems():
    for path in v.files:
      print(k, path)

  logging.info("Writing output to %s", args.output)
  with open(args.output, "w") as hf:
    writer = csv.writer(hf)
    std_writer = csv.writer(sys.stdout)

    row = ["category", "number of files", "lines of code"]
    writer.writerow(row)
    std_writer.writerow(row)

    for k, v in categories.iteritems():
      row = [k, v.num_files, v.loc]
      writer.writerow(row)
      std_writer.writerow(row)

if __name__ == "__main__":
  main()
