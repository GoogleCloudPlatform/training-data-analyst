## Simplify the creation of `PersistentVolumeClaim` instances

**`VolumeOp`:** A specified `ResourceOp` for PVC creation.

### Arguments:
The following arguments are an extension to the `ResourceOp` arguments.
If a `k8s_resource` is passed, then none of the following may be provided.

* `resource_name`: The name of the resource which will be created.
  This string will be prepended with the workflow name.
  This may contain `PipelineParam`s.
  (_required_)
* `size`: The requested size for the PVC.
  This may contain `PipelineParam`s.
  (_required_)
* `storage_class`: The storage class to be used.
  This may contain `PipelineParam`s.
  (_optional_)
* `modes`: The `accessModes` of the PVC.
  Check
  [this documentation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes)
  for further information.
  The user may find the following modes built-in:
    * `VOLUME_MODE_RWO`: `["ReadWriteOnce"]`
    * `VOLUME_MODE_RWM`: `["ReadWriteMany"]`
    * `VOLUME_MODE_ROM`: `["ReadOnlyMany"]`

  Defaults to `VOLUME_MODE_RWM`.
* `annotations`: Annotations to be patched in the PVC.
  These may contain `PipelineParam`s.
  (_optional_)
* `data_source`: It is used to create a PVC from a `VolumeSnapshot`.
  Can be either a `V1TypedLocalObjectReference` or a `string`, and may contain `PipelineParam`s.
  (_Alpha feature_, _optional_)

### Outputs
Additionally to the whole specification of the resource and its name (`ResourceOp` defaults), a
`VolumeOp` also outputs the storage size of the bounded PV (as `step.outputs["size"]`).
However, this may be empty if the storage provisioner has a `WaitForFirstConsumer` binding mode.
This value, if not empty, is always &ge; the requested size.

### Useful attributes
1. The `VolumeOp` step has a `.volume` attribute which is a `PipelineVolume` referencing the
   created PVC.
   A `PipelineVolume` is essentially a `V1Volume` supplemented with an `.after()` method extending
   the carried dependencies.
   These dependencies can then be parsed properly by a `ContainerOp`, if used with the `pvolumes`
   attribute, to extend the `ContainerOp`'s dependencies.
2. A `ContainerOp` has a `pvolumes` argument in its constructor.
   This is a dictionary with mount paths as keys and volumes as values and functions similarly to
   `file_outputs` (which can then be used as `op.outputs["key"]` or `op.output`).
   For example:
   ```python
   vop = dsl.VolumeOp(
       name="volume_creation",
       resource_name="mypvc",
       size="1Gi"
   )
   step1 = dsl.ContainerOp(
       name="step1",
       ...
       pvolumes={"/mnt": vop.volume}  # Implies execution after vop
   )
   step2 = dsl.ContainerOp(
       name="step2",
       ...
       pvolumes={"/data": step1.pvolume,  # Implies execution after step1
                 "/mnt": dsl.PipelineVolume(pvc="existing-pvc")}
   )
   step3 = dsl.ContainerOp(
       name="step3",
       ...
       pvolumes={"/common": step2.pvolumes["/mnt"]}  # Implies execution after step2
   )
   ```
