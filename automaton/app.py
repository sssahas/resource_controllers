import sys
import os
import importlib
import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class BootstrapStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)


def load_and_run_dag_executor(stack: Stack, template_name: str):
    try:
        module_path = f"workloads.{template_name}.dag_executor"
        dag_executor = importlib.import_module(module_path)
        dag_executor.run(stack)
    except ModuleNotFoundError:
        raise ValueError(f"Unknown template_name: {template_name}")


def get_stack_name(name: str) -> str:
    return f"{name.replace('_', '-')}-stack"


def main():
    app = cdk.App()
    action = app.node.try_get_context("action")
    template_name = app.node.try_get_context("template_name")
    service_name = app.node.try_get_context("service_name")

    if action == "deploy":
        if not template_name:
            raise ValueError("Missing context: template_name")

        class GenericWorkloadStack(Stack):
            def __init__(self, scope: Construct, construct_id: str, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                load_and_run_dag_executor(self, template_name)

        stack_name = get_stack_name(service_name)
        GenericWorkloadStack(app, stack_name)

    elif action == "destroy":
        stack_name = get_stack_name(service_name)
        Stack(app, stack_name)
        # pass

    elif action is None:
        BootstrapStack(app, "BootstrapStack")

    else:
        raise ValueError(f"Unsupported action: {action}")

    app.synth()


if __name__ == "__main__":
    main()
