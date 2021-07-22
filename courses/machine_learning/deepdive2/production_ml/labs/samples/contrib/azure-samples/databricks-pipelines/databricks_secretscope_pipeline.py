"""Create a new secret scope in Databricks."""
import kfp.dsl as dsl
import kfp.compiler as compiler
import databricks

def create_secretscope(
        scope_name,
        string_secret,
        byte_secret,
        ref_secret_name,
        ref_secret_key,
        principal_name):
    return databricks.CreateSecretScopeOp(
        name="createsecretscope",
        scope_name=scope_name,
        initial_manage_principal="users",
        secrets=[
            {
                "key": "string-secret",
                "string_value": string_secret
            },
            {
                "key": "byte-secret",
                "byte_value": byte_secret
            },
            {
                "key": "ref-secret",
                "value_from": {
                    "secret_key_ref": {
                        "name": ref_secret_name,
                        "key": ref_secret_key
                    }
                }
            }
        ],
        acls=[
            {
                "principal": principal_name,
                "permission": "READ"
            }
        ]
    )

def delete_secretscope(scope_name):
    return databricks.DeleteSecretScopeOp(
        name="deletesecretscope",
        scope_name=scope_name
    )

@dsl.pipeline(
    name="DatabricksSecretScope",
    description="A toy pipeline that sets some secrets and acls in an Azure Databricks Secret Scope."
)
def calc_pipeline(
        scope_name="test-secretscope",
        string_secret="helloworld",
        byte_secret="aGVsbG93b3JsZA==",
        ref_secret_name="mysecret",
        ref_secret_key="username",
        principal_name="user@foo.com"
    ):
    create_secretscope_task = create_secretscope(
        scope_name,
        string_secret,
        byte_secret,
        ref_secret_name,
        ref_secret_key,
        principal_name)
    delete_secretscope_task = delete_secretscope(scope_name)
    delete_secretscope_task.after(create_secretscope_task)

if __name__ == "__main__":
    compiler.Compiler()._create_and_write_workflow(
        pipeline_func=calc_pipeline,
        package_path=__file__ + ".tar.gz")
