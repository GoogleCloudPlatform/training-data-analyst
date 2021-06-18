## Simplify the creation of `VolumeSnapshot` instances
    
**`VolumeSnapshotOp`:** A specified `ResourceOp` for `VolumeSnapshot` creation.

---

**NOTE:** `VolumeSnapshot`s is an Alpha feature.
You should check if your Kubernetes cluster admin has them enabled.

---

### Arguments:
The following arguments are an extension to the `ResourceOp` arguments.
If a `k8s_resource` is passed, then none of the following may be provided.

* `resource_name`: The name of the resource which will be created.
  This string will be prepended with the workflow name.
  This may contain `PipelineParam`s.
  (_required_)
* `pvc`: The name of the PVC to be snapshotted.
  This may contain `PipelineParam`s.
  (_optional_)
* `snapshot_class`: The snapshot storage class to be used.
  This may contain `PipelineParam`s.
  (_optional_)
* `volume`: An instance of a `V1Volume`, or its inherited type (e.g. `PipelineVolume`).
  This may contain `PipelineParam`s.
  (_optional_)
* `annotations`: Annotations to be patched in the `VolumeSnapshot`.
  These may contain `PipelineParam`s.
  (_optional_)

**NOTE:** One of the `pvc` or `volume` needs to be provided.

### Outputs
Additionally to the whole specification of the resource and its name (`ResourceOp` defaults), a
`VolumeSnapshotOp` also outputs the `restoreSize` of the bounded `VolumeSnapshot` (as
`step.outputs["size"]`).
This is the minimum size for a PVC created by that snapshot.

### Useful attribute
The `VolumeSnapshotOp` step has a `.snapshot` attribute which is a `V1TypedLocalObjectReference`.
This can be passed as a `data_source` to create a PVC out of that `VolumeSnapshot`.
The user may otherwise use the `step.outputs["name"]` as `data_source`.
