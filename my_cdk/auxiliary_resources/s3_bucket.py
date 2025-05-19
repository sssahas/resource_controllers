from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    RemovalPolicy
)
from constructs import Construct
import uuid

class S3BucketStack(Construct):
    def __init__(self, scope: Construct, id: str, name: str, properties: dict = None) -> None:
        super().__init__(scope, id)
        props = properties or {}
        
        allowed_properties = ["versioned", "removal_policy", "object_lock_enabled", "auto_delete_objects", "encryption", "public_read_access"]
        for key in props:
            if key not in allowed_properties:
                raise ValueError(f"Unsupported S3 property: {key}")
        
        # name must exist and uuid 6 digits added for uniqueness
        if name is None:
            raise ValueError(f"Bucket name is required")
        name = f"{name}-{str(uuid.uuid4())[:6]}"
        
        encryption_map = {
            "s3-managed": s3.BucketEncryption.S3_MANAGED,
            "kms": s3.BucketEncryption.KMS_MANAGED,
        }
        removal_policy_map = {
            "retain": RemovalPolicy.RETAIN,
            "destroy": RemovalPolicy.DESTROY
        }
        
        # Create an S3 bucket
        self.bucket = s3.Bucket(
            self,
            name,
            versioned=props.get("versioned",False),
            removal_policy=removal_policy_map.get(props.get("removal_policy","destroy")),
            object_lock_enabled = props.get("object_lock_enabled",False),
            auto_delete_objects=props.get("auto_delete_objects", False),
            encryption = encryption_map.get(props.get("encryption","s3-managed")),
            public_read_access = props.get("public_read_access", False)
        )
        
    @property
    def bucket_name(self):
        return self.bucket.bucket_name

    @property
    def bucket_arn(self):
        return self.bucket.bucket_arn
    
    @property
    def bucket_urn(self):
        return f"s3://{self.bucket.bucket_name}"