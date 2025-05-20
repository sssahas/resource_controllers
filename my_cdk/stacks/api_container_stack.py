import json
from aws_cdk import (
    Stack,
    aws_apprunner as apprunner,
    aws_ecr as ecr,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
from auxiliary_resources.s3_bucket import S3BucketStack


class ApiDeployerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_repo = self.node.try_get_context("image_repo")
        image_tag = self.node.try_get_context("image_tag")
        service_name = self.node.try_get_context("service_name")
        action = self.node.try_get_context("action")
        resources_raw = self.node.try_get_context("resources")
        resources = (
            json.loads(resources_raw)
            if isinstance(resources_raw, str)
            else resources_raw
        )

        if action == "deploy":
            if not image_repo or not image_tag or not service_name:
                raise ValueError(
                    "Missing context: image_repo, image_tag, or service_name"
                )
            env_vars = {}

            for resource in resources:
                if resource.get("type") == "s3":
                    name = resource.get("name", None)
                    properties = resource.get("properties", {})
                    if name:
                        bucket_construct = S3BucketStack(
                            self, f"{name}Construct", name, properties
                        )
                        bucket_arn = bucket_construct.bucket_arn
                        env_vars["BUCKET_ARN"] = bucket_arn or ""

            repository = ecr.Repository.from_repository_name(
                self,
                "ECRRepo",
                repository_name=image_repo,
            )

            apprunner_role = iam.Role(
                self,
                "AppRunnerRole",
                assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSAppRunnerServicePolicyForECRAccess"
                    )
                ],
            )
            # set env vars
            env_props = []
            for k, v in env_vars.items():
                env_props.append(
                    apprunner.CfnService.KeyValuePairProperty(name=k, value=v)
                )

            service = apprunner.CfnService(
                self,
                "AppRunnerService",
                service_name=service_name,
                source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                    image_repository=apprunner.CfnService.ImageRepositoryProperty(
                        image_identifier=f"{repository.repository_uri}:{image_tag}",
                        image_repository_type="ECR",
                        image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                            port="8080",
                            runtime_environment_variables=env_props,
                        ),
                    ),
                    authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                        access_role_arn=apprunner_role.role_arn
                    ),
                    auto_deployments_enabled=True,
                ),
            )

            CfnOutput(self, "ServiceUrl", value=service.attr_service_url)
            CfnOutput(self, "ServiceStatus", value=service.attr_status)

        elif action == "destroy":
            if not service_name:
                raise ValueError("Missing context: service_name")
                # No resources created here — just a placeholder for destroy logic if needed
