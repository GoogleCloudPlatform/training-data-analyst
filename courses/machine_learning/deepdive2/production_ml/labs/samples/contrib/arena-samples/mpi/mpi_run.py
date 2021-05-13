import kfp
import arena
import kfp.dsl as dsl
import argparse

FLAGS = None

@dsl.pipeline(
  name='pipeline to run mpi job',
  description='shows how to run mpi job.'
)
def mpirun_pipeline(image="uber/horovod:0.13.11-tf1.10.0-torch0.4.0-py3.5",
						   batch_size="64",
						   optimizer='momentum',
               sync_source='https://github.com/tensorflow/benchmarks.git',
               git_sync_branch='cnn_tf_v1.9_compatible',
               data='user-susan:/training',
               gpus=1,
               workers=1,
               cpu_limit='2',
               metric='images/sec',
               memory_limit='10Gi'):
  """A pipeline for end to end machine learning workflow."""

  env = ['NCCL_DEBUG=INFO','GIT_SYNC_BRANCH={0}'.format(git_sync_branch)]

  train=arena.mpi_job_op(
  	name="all-reduce",
  	image=image,
  	env=env,
    data=[data],
    workers=workers,
    sync_source=sync_source,
    gpus=gpus,
    cpu_limit=cpu_limit,
    memory_limit=memory_limit,
    metrics=[metric],
  	command="""
  	mpirun python code/benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --model resnet101 \
  	--batch_size {0}  --variable_update horovod --optimizer {1}\
  	--summary_verbosity=3 --save_summaries_steps=10
  	""".format(batch_size, optimizer)
  )

  
if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(mpirun_pipeline, __file__ + '.tar.gz')
