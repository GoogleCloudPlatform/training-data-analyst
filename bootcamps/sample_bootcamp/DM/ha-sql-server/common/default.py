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
"""Convinence module to hold default constants for C2D components.

There should not be any logic in this module. Its purpose is to simplify
analysis of commonly used GCP and properties names and identify the names
that were custom created for these modules.
"""
# Generic constants
C2D_IMAGES = 'click-to-deploy-images'

# URL constants
COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'

# Deploymen Manager constructs
REFERENCE_PREFIX = '$(ref.'

# Commonly used in properties namespace
AUTO_DELETE = 'autoDelete'
BOOTDISK = 'bootDiskType'
BOOTDISKSIZE = 'bootDiskSizeGb'
C_IMAGE = 'containerImage'
DC_MANIFEST = 'dcManifest'
DEPLOYMENT = 'DEPLOYMENT'  # used in the deployment coordinator
DISK_NAME = 'diskName'
DISK_RESOURCES = 'addedDiskResources'
DISK_SOURCE = 'source'
ENDPOINT_NAME = 'serviceRegistryEndpointName'
FIXED_GCLOUD = 'fixedGcloud'
GENERATED_PROP = 'generatedProperties'
INITIALIZEP = 'initializeParams'
INSTANCE_NAME = 'instanceName'
LOCAL_SSD = 'localSSDs'
MAX_NUM = 'maxNumReplicas'
NETWORKS = 'networks'
NO_SCOPE = 'noScope'
PROVIDE_BOOT = 'provideBoot'
REPLICAS = 'replicas'
SIZE = 'size'
VM_COPIES = 'numberOfVMReplicas'
ZONES = 'zones'

# Common properties values (only official GCP values allowed here)
EXTERNAL = 'External NAT'
ONE_NAT = 'ONE_TO_ONE_NAT'

# Common 1st level properties (only official GCP names allowed here)
CAN_IP_FWD = 'canIpForward'
CONTAINER = 'container'
DCKRENV = 'dockerEnv'
DCKRIMAGE = 'dockerImage'
DEFAULT_SERVICE = 'defaultService'
DEVICE_NAME = 'deviceName'
DISKS = 'disks'
DISK_SIZE = 'diskSizeGb'
DISKTYPE = 'diskType'
HEALTH_PATH = 'healthPath'
HOST_RULES = 'hostRules'
IP_PROTO = 'IPProtocol'
MACHINETYPE = 'machineType'
METADATA = 'metadata'
NAME = 'name'
NETWORK = 'network'
SUBNETWORK = 'subnetwork'
PATH_MATCHERS = 'pathMatchers'
PORT = 'port'
PROJECT = 'project'
SERVICE = 'service'
SERVICE_ACCOUNTS = 'serviceAccounts'
SRCIMAGE = 'sourceImage'
SRC_RANGES = 'sourceRanges'
TAGS = 'tags'
TYPE = 'type'
VM_TEMPLATE = 'instanceTemplate'
ZONE = 'zone'

# Zone specfic VM properties
VM_ZONE_PROPERTIES = [DISKTYPE, MACHINETYPE, BOOTDISK]

# Resource type defaults names
ADDRESS = 'compute.v1.address'
AUTOSCALER = 'compute.v1.autoscaler'
BACKEND_SERVICE = 'compute.v1.backendService'
DISK = 'compute.v1.disk'
ENDPOINT = 'serviceregistry.v1alpha.endpoint'
FIREWALL = 'compute.v1.firewall'
GF_RULE = 'compute.v1.globalForwardingRule'
HEALTHCHECK = 'compute.v1.httpHealthCheck'
IGM = 'compute.v1.instanceGroupManager'
INSTANCE = 'compute.v1.instance'
PROXY = 'compute.v1.targetHttpProxy'
TEMPLATE = 'compute.v1.instanceTemplate'
URL_MAP = 'compute.v1.urlMap'

# Also Known As constants
AKA = {
    AUTOSCALER: 'as',
    BACKEND_SERVICE: 'bes',
    DISK: 'disk',
    FIREWALL: 'fwall',
    GF_RULE: 'ip',
    HEALTHCHECK: 'hc',
    INSTANCE: 'vm',
    PROXY: 'tproxy',
    IGM: 'igm',
    URL_MAP: 'umap',
}

LOC = {
    'europe': 'eu',
    'asia': 'as',
    'central': 'c',
    'east': 'e',
    'west': 'w',
    'north': 'n',
    'south': 's',
}
