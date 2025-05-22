from aws_cdk import aws_apprunner as apprunner, aws_ecr as ecr, aws_iam as iam
from auxiliary_resources.s3_bucket import S3BucketStack
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def create_s3_bucket(stack, name, props, env_vars, results):
    logger.info(f"Creating S3 bucket: {name} with properties: {props}")
    bucket = S3BucketStack(stack, f"{name}Construct", name, props)
    logger.info(f"S3 bucket {name} created with ARN: {bucket.bucket_arn}")
    env_vars["BUCKET_ARN"] = bucket.bucket_arn or ""
    results[name] = bucket


def pullFrom_ecr_repo(stack, image_repo, results):
    repo = ecr.Repository.from_repository_name(
        stack, "ECRRepo", repository_name=image_repo
    )
    results["ecr_repo"] = repo


def create_apprunner_role(stack, results):
    logger.info(f"Creating App Runner Role")
    role = iam.Role(
        stack,
        "AppRunnerRole",
        assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSAppRunnerServicePolicyForECRAccess"
            )
        ],
    )
    results["apprunner_role"] = role


def create_apprunner_service(stack, service_name, image_tag, env_vars, results):
    logger.info(f"Creating App Runner service: {service_name}")
    repo = results["ecr_repo"]
    role = results["apprunner_role"]

    env_list = [
        apprunner.CfnService.KeyValuePairProperty(name=k, value=v)
        for k, v in env_vars.items()
    ]
    logger.info(f"App Runner service {service_name} creation submitted.")
    apprunner.CfnService(
        stack,
        "AppRunnerService",
        service_name=service_name,
        source_configuration=apprunner.CfnService.SourceConfigurationProperty(
            image_repository=apprunner.CfnService.ImageRepositoryProperty(
                image_identifier=f"{repo.repository_uri}:{image_tag}",
                image_repository_type="ECR",
                image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                    port="8080",
                    runtime_environment_variables=env_list,
                ),
            ),
            authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                access_role_arn=role.role_arn
            ),
            auto_deployments_enabled=True,
        ),
    )
