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


import kfp.dsl as dsl


@dsl.pipeline(
    name="VolumeOp Sequential",
    description="The third example of the design doc."
)
def volumeop_sequential():
    vop = dsl.VolumeOp(
        name="mypvc",
        resource_name="newpvc",
        size="10Gi",
        modes=dsl.VOLUME_MODE_RWM
    )

    step1 = dsl.ContainerOp(
        name="step1",
        image="library/bash:4.4.23",
        command=["sh", "-c"],
        arguments=["echo 1|tee /data/file1"],
        pvolumes={"/data": vop.volume}
    )

    step2 = dsl.ContainerOp(
        name="step2",
        image="library/bash:4.4.23",
        command=["sh", "-c"],
        arguments=["cp /data/file1 /data/file2"],
        pvolumes={"/data": step1.pvolume}
    )

    step3 = dsl.ContainerOp(
        name="step3",
        image="library/bash:4.4.23",
        command=["cat", "/mnt/file1", "/mnt/file2"],
        pvolumes={"/mnt": step2.pvolume}
    )


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(volumeop_sequential, __file__ + ".tar.gz")
