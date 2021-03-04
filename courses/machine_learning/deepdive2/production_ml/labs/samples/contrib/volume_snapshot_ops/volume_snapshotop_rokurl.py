# Copyright 2019 Google LLC
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


"""This sample uses Rok as an example to show case how VolumeOp accepts
annotations as an extra argument, and how we can use arbitrary PipelineParams
to determine their contents.

The specific annotation is Rok-specific, but the use of annotations in such way
is widespread in storage systems integrated with K8s.
"""

import kfp.dsl as dsl


@dsl.pipeline(
    name="VolumeSnapshotOp RokURL",
    description="The fifth example of the design doc."
)
def volume_snapshotop_rokurl(rok_url):
    vop1 = dsl.VolumeOp(
        name="create_volume_1",
        resource_name="vol1",
        size="1Gi",
        annotations={"rok/origin": rok_url},
        modes=dsl.VOLUME_MODE_RWM
    )

    step1 = dsl.ContainerOp(
        name="step1_concat",
        image="library/bash:4.4.23",
        command=["sh", "-c"],
        arguments=["cat /data/file*| gzip -c >/data/full.gz"],
        pvolumes={"/data": vop1.volume}
    )

    step1_snap = dsl.VolumeSnapshotOp(
        name="create_snapshot_1",
        resource_name="snap1",
        volume=step1.pvolume
    )

    vop2 = dsl.VolumeOp(
        name="create_volume_2",
        resource_name="vol2",
        data_source=step1_snap.snapshot,
        size=step1_snap.outputs["size"]
    )

    step2 = dsl.ContainerOp(
        name="step2_gunzip",
        image="library/bash:4.4.23",
        command=["gunzip", "-k", "/data/full.gz"],
        pvolumes={"/data": vop2.volume}
    )

    step2_snap = dsl.VolumeSnapshotOp(
        name="create_snapshot_2",
        resource_name="snap2",
        volume=step2.pvolume
    )

    vop3 = dsl.VolumeOp(
        name="create_volume_3",
        resource_name="vol3",
        data_source=step2_snap.snapshot,
        size=step2_snap.outputs["size"]
    )

    step3 = dsl.ContainerOp(
        name="step3_output",
        image="library/bash:4.4.23",
        command=["cat", "/data/full"],
        pvolumes={"/data": vop3.volume}
    )


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(volume_snapshotop_rokurl, __file__ + ".tar.gz")
