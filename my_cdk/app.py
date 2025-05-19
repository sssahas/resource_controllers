import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import jsii
import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct
from my_cdk.stacks.api_container_stack import ApiDeployerStack

class BootstrapStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)


def get_stack(template: str):
    if template == "api_container":
        return ApiDeployerStack
    raise ValueError("Unknown template: " + template)


app = cdk.App()
action = app.node.try_get_context("action")

if action == "deploy":
    template_name = app.node.try_get_context("template_name")
    if not template_name:
        raise ValueError("Missing context: template_name")
    stack_class = get_stack(template_name)
    stack_class(app, "ApiDeployerStack")

elif action == "destroy":
    stack_class = ApiDeployerStack
    stack_class(app, "ApiDeployerStack")

elif action is None:
    BootstrapStack(app, "BootstrapStack")

else:
    raise ValueError(f"Unsupported action: {action}")

app.synth()
