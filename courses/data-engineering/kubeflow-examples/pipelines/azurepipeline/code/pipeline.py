"""Main pipeline file"""
from kubernetes import client as k8s_client
import kfp.dsl as dsl
import kfp.compiler as compiler

@dsl.pipeline(
  name='Tacos vs. Burritos',
  description='Simple TF CNN'
)
def tacosandburritos_train(
    tenant_id,
    service_principal_id,
    service_principal_password,
    subscription_id,
    resource_group,
    workspace
):
  """Pipeline steps"""

  persistent_volume_path = '/mnt/azure'
  data_download = 'https://aiadvocate.blob.core.windows.net/public/tacodata.zip'
  epochs = 5
  batch = 32
  learning_rate = 0.0001
  model_name = 'tacosandburritos'
  profile_name = 'tacoprofile'
  operations = {}
  image_size = 160
  training_folder = 'train'
  training_dataset = 'train.txt'
  model_folder = 'model'

  # preprocess data
  operations['preprocess'] = dsl.ContainerOp(
    name='preprocess',
    image='insert your image here',
    command=['python'],
    arguments=[
      '/scripts/data.py',
      '--base_path', persistent_volume_path,
      '--data', training_folder,
      '--target', training_dataset,
      '--img_size', image_size,
      '--zipfile', data_download
    ]
  )

  # train
  operations['training'] = dsl.ContainerOp(
    name='training',
    image='insert your image here',
    command=['python'],
    arguments=[
      '/scripts/train.py',
      '--base_path', persistent_volume_path,
      '--data', training_folder,
      '--epochs', epochs,
      '--batch', batch,
      '--image_size', image_size,
      '--lr', learning_rate,
      '--outputs', model_folder,
      '--dataset', training_dataset
    ]
  )
  operations['training'].after(operations['preprocess'])

  # register model
  operations['register'] = dsl.ContainerOp(
    name='register',
    image='insert your image here',
    command=['python'],
    arguments=[
      '/scripts/register.py',
      '--base_path', persistent_volume_path,
      '--model', 'latest.h5',
      '--model_name', model_name,
      '--tenant_id', tenant_id,
      '--service_principal_id', service_principal_id,
      '--service_principal_password', service_principal_password,
      '--subscription_id', subscription_id,
      '--resource_group', resource_group,
      '--workspace', workspace
    ]
  )
  operations['register'].after(operations['training'])

  operations['profile'] = dsl.ContainerOp(
    name='profile',
    image='insert your image here',
    command=['sh'],
    arguments=[
      '/scripts/profile.sh',
      '-n', profile_name,
      '-m', model_name,
      '-i', '/scripts/inferenceconfig.json',
      '-d', '{"image":"https://www.exploreveg.org/files/2015/05/sofritas-burrito.jpeg"}',
      '-t', tenant_id,
      '-r', resource_group,
      '-w', workspace,
      '-s', service_principal_id,
      '-p', service_principal_password,
      '-u', subscription_id,
      '-b', persistent_volume_path
    ]
  )
  operations['profile'].after(operations['register'])

  operations['deploy'] = dsl.ContainerOp(
    name='deploy',
    image='insert your image here',
    command=['sh'],
    arguments=[
      '/scripts/deploy.sh',
      '-n', model_name,
      '-m', model_name,
      '-i', '/scripts/inferenceconfig.json',
      '-d', '/scripts/deploymentconfig.json',
      '-t', tenant_id,
      '-r', resource_group,
      '-w', workspace,
      '-s', service_principal_id,
      '-p', service_principal_password,
      '-u', subscription_id,
      '-b', persistent_volume_path
    ]
  )
  operations['deploy'].after(operations['profile'])
  for _, op_1 in operations.items():
    op_1.container.set_image_pull_policy("Always")
    op_1.add_volume(
      k8s_client.V1Volume(
        name='azure',
        persistent_volume_claim=k8s_client.V1PersistentVolumeClaimVolumeSource(
          claim_name='azure-managed-disk')
      )
    ).add_volume_mount(k8s_client.V1VolumeMount(
      mount_path='/mnt/azure', name='azure'))

if __name__ == '__main__':
  compiler.Compiler().compile(tacosandburritos_train, __file__ + '.tar.gz')
