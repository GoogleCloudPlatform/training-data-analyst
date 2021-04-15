import kfp.dsl as dsl
import kfp.components as components
from kfp.gcp import use_gcp_secret

@dsl.pipeline(
    name = "kaggle pipeline",
    description = "kaggle pipeline that goes from download data, analyse data, train model to submit result"
)
def kaggle_houseprice(
    bucket_name: str,
    commit_sha: str
):

    downloadDataOp = components.load_component_from_file('./download_dataset/component.yaml')
    downloadDataStep = downloadDataOp(bucket_name=bucket_name).apply(use_gcp_secret('user-gcp-sa'))

    visualizeTableOp = components.load_component_from_file('./visualize_table/component.yaml')
    visualizeTableStep = visualizeTableOp(train_file_path='%s' % downloadDataStep.outputs['train_dataset']).apply(use_gcp_secret('user-gcp-sa'))

    visualizeHTMLOp = components.load_component_from_file('./visualize_html/component.yaml')
    visualizeHTMLStep = visualizeHTMLOp(train_file_path='%s' % downloadDataStep.outputs['train_dataset'],
                                        commit_sha=commit_sha,
                                        bucket_name=bucket_name).apply(use_gcp_secret('user-gcp-sa'))

    trainModelOp = components.load_component_from_file('./train_model/component.yaml')
    trainModelStep = trainModelOp(train_file='%s' % downloadDataStep.outputs['train_dataset'],
                                  test_file='%s' % downloadDataStep.outputs['test_dataset'],
                                  bucket_name=bucket_name).apply(use_gcp_secret('user-gcp-sa'))

    submitResultOp = components.load_component_from_file('./submit_result/component.yaml')
    submitResultStep = submitResultOp(result_file='%s' % trainModelStep.outputs['result'],
                                      submit_message='submit').apply(use_gcp_secret('user-gcp-sa'))

if __name__ == '__main__':
    import kfp.compiler as compiler
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--gcr_address', type = str)
    args = parser.parse_args()
    compiler.Compiler().compile(kaggle_houseprice, __file__ + '.zip')