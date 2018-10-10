# Copyright 2015 Google Inc. All rights reserved.
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
"""Generic simple functions used for python based templage generation."""

import re
import sys
import traceback
import default

import yaml

RFC1035_RE = re.compile(r'^[a-z][-a-z0-9]{1,61}[a-z0-9]{1}$')


class Error(Exception):
  """Common exception wrapper for template exceptions."""
  pass


def AddDiskResourcesIfNeeded(context):
  """Checks context if disk resources need to be added."""
  if default.DISK_RESOURCES in context.properties:
    return context.properties[default.DISK_RESOURCES]
  else:
    return []


def AutoName(base, resource, *args):
  """Helper method to generate names automatically based on default."""
  auto_name = '%s-%s' % (base, '-'.join(list(args) + [default.AKA[resource]]))
  if not RFC1035_RE.match(auto_name):
    raise Error('"%s" name for type %s does not match RFC1035 regex (%s)' %
                (auto_name, resource, RFC1035_RE.pattern))
  return auto_name


def AutoRef(base, resource, *args):
  """Helper method that builds a reference for an auto-named resource."""
  return Ref(AutoName(base, resource, *args))


def OrderedItems(dict_obj):
  """Convenient method to yield sorted iteritems of a dictionary."""
  keys = list(dict_obj.keys())
  keys.sort()
  for k in keys:
    yield (k, dict_obj[k])


def ShortenZoneName(zone):
  """Given a string that looks like a zone name, creates a shorter version."""
  geo, coord, number, letter = re.findall(r'(\w+)-(\w+)(\d)-(\w)', zone)[0]
  geo = geo.lower() if len(geo) == 2 else default.LOC[geo.lower()]
  coord = default.LOC[coord.lower()]
  number = str(number)
  letter = letter.lower()
  return geo + '-' + coord + number + letter


def ZoneToRegion(zone):
  """Derives the region from a zone name."""
  parts = zone.split('-')
  if len(parts) != 3:
    raise Error('Cannot derive region from zone "%s"' % zone)
  return '-'.join(parts[:2])


def FormatException(message):
  """Adds more information to the exception."""
  message = ('Exception Type: %s\n'
             'Details: %s\n'
             'Message: %s\n') % (sys.exc_info()[0], traceback.format_exc(), message)
  return message


def Ref(name):
  return '$(ref.%s.selfLink)' % name


def RefGroup(name):
  return '$(ref.%s.instanceGroup)' % name


def GlobalComputeLink(project, collection, name):
  return ''.join([default.COMPUTE_URL_BASE, 'projects/', project, '/global/',
                  collection, '/', name])


def LocalComputeLink(project, zone, key, value):
  return ''.join([default.COMPUTE_URL_BASE, 'projects/', project, '/zones/',
                  zone, '/', key, '/', value])


def ReadContext(context, prop_key):
  return (context.env['project'], context.properties.get('zone', None),
          context.properties[prop_key])


def MakeLocalComputeLink(context, key):
  project, zone, value = ReadContext(context, key)
  if IsComputeLink(value):
    return value
  else:
    return LocalComputeLink(project, zone, key + 's', value)


def MakeGlobalComputeLink(context, key):
  project, _, value = ReadContext(context, key)
  if IsComputeLink(value):
    return value
  else:
    return GlobalComputeLink(project, key + 's', value)


def MakeSubnetworkComputeLink(context, key):
  project, zone, value = ReadContext(context, key)
  region = ZoneToRegion(zone)
  return ''.join([default.COMPUTE_URL_BASE, 'projects/', project, '/regions/',
                  region, '/subnetworks/', value])


def MakeFQHN(context, name):
  return '%s.c.%s.internal' % (name, context.env['project'])


# TODO(victorg): Consider moving this method to a different file
def MakeC2DImageLink(name, dev_mode=False):
  if IsGlobalProjectShortcut(name) or name.startswith('http'):
    return name
  else:
    if dev_mode:
      return 'global/images/%s' % name
    else:
      return GlobalComputeLink(default.C2D_IMAGES, 'images', name)


def IsGlobalProjectShortcut(name):
  return name.startswith('projects/') or name.startswith('global/')


def IsComputeLink(name):
  return (name.startswith(default.COMPUTE_URL_BASE) or
          name.startswith(default.REFERENCE_PREFIX))


def GetNamesAndTypes(resources_dict):
  return [(d['name'], d['type']) for d in resources_dict]


def SummarizeResources(res_dict):
  """Summarizes the name of resources per resource type."""
  result = {}
  for res in res_dict:
    result.setdefault(res['type'], []).append(res['name'])
  return result


def ListPropertyValuesOfType(res_dict, prop, res_type):
  """Lists all the values for a property of a certain type."""
  return [r['properties'][prop] for r in res_dict if r['type'] == res_type]


def MakeResource(resource_list, output_list=None):
  """Wrapper for a DM template basic spec."""
  content = {'resources': resource_list}
  if output_list:
    content['outputs'] = output_list
  return yaml.dump(content)


def TakeZoneOut(properties):
  """Given a properties dictionary, removes the zone specific information."""

  def _CleanZoneUrl(value):
    value = value.split('/')[-1] if IsComputeLink(value) else value
    return value

  for name in default.VM_ZONE_PROPERTIES:
    if name in properties:
      properties[name] = _CleanZoneUrl(properties[name])
  if default.ZONE in properties:
    properties.pop(default.ZONE)
  if default.BOOTDISK in properties:
    properties[default.BOOTDISK] = _CleanZoneUrl(properties[default.BOOTDISK])
  if default.DISKS in properties:
    for disk in properties[default.DISKS]:
      # Don't touch references to other disks
      if default.DISK_SOURCE in disk:
        continue
      if default.INITIALIZEP in disk:
        disk_init = disk[default.INITIALIZEP]
      if default.DISKTYPE in disk_init:
        disk_init[default.DISKTYPE] = _CleanZoneUrl(disk_init[default.DISKTYPE])


def GenerateEmbeddableYaml(yaml_string):
  # Because YAML is a space delimited format, we need to be careful about
  # embedding one YAML document in another. This function takes in a string in
  # YAML format and produces an equivalent YAML representation that can be
  # inserted into arbitrary points of another YAML document. It does so by
  # printing the YAML string in a single line format. Consistent ordering of
  # the string is also guaranteed by using yaml.dump.
  yaml_object = yaml.load(yaml_string)
  dumped_yaml = yaml.dump(yaml_object, default_flow_style=True)
  return dumped_yaml


def FormatErrorsDec(func):
  """Decorator to format exceptions if they get raised."""

  def FormatErrorsWrap(context):
    try:
      return func(context)
    except Exception as e:
      raise Error(FormatException(e.message))

  return FormatErrorsWrap
