#!/usr/bin/env python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import kfp
from kfp import dsl
from kubernetes.client.models import V1PodDNSConfig, V1PodDNSConfigOption


def echo_op():
    return dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['sh', '-c'],
        arguments=['echo "hello world"']
    )


@dsl.pipeline(
    name='dnsConfig setting',
    description='Passes dnsConfig setting to workflow.'
)
def dns_config_pipeline():
    echo_task = echo_op()


if __name__ == '__main__':
    pipeline_conf = kfp.dsl.PipelineConf()
    pipeline_conf.set_dns_config(dns_config=V1PodDNSConfig(
        nameservers=["1.2.3.4"],
        options=[V1PodDNSConfigOption(name="ndots", value="2")]
    ))

    kfp.compiler.Compiler().compile(
        dns_config_pipeline,
        __file__ + '.yaml',
        pipeline_conf=pipeline_conf
    )
