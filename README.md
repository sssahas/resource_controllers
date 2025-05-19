This `prototype` code demonstrates how to use AWS CDK and Python Flask to stand up a `resource controllers` service as part of a `control plane`. The primary objective of this service is to abstract away AWS resource management complexities to run various workloads such as APIs, WebApps, MLOps, etc., in a standard yet flexible and extensible manner.

# Technical Brief

This service exposes the following API endpoints:

### 1. GET `/workload-templates`

Returns all the templates available for the developer. Use `?long=true` to return all required and optional inputs, output signatures, and auxiliary resources needed alongside the APIs. Auxiliary resources can be sent via the `resources` list.

### 2. POST `/deploy`

Deploys the workload.

**Deploy just the API:**

```json
{
  "template_name": "api_container",
  "image_repo": "core_search",
  "image_tag": "latest",
  "service_name": "core_search"
}
```

**Deploy API along with an auxiliary resource (S3) with default configs:**

```json
{
  "template_name": "api_container",
  "image_repo": "core_search",
  "image_tag": "latest",
  "service_name": "core_search",
  "resources": [
    {
      "type": "s3",
      "name": "core_search"
    }
  ]
}
```

**Tweak S3 configs to suit your needs:**

```json
{
  "template_name": "api_container",
  "image_repo": "core_search",
  "image_tag": "latest",
  "service_name": "core_search_delete",
  "resources": [
    {
      "type": "s3",
      "name": "core_search_delete",
      "properties": {
        "object_lock_enabled": true,
        "versioned": true,
        "removal_policy": "retain",
        "encryption": "kms"
      }
    }
  ]
}
```

### 3. POST `/destroy`

Uninstall/clean up.

**Uninstall the API and resources attached to it:**

```json
{
  "service_name": "core_search"
}
```

---

## Concepts

### Workload Templates

Stored inside the `workload-templates` folder, a set of `.yaml` files defines all the types of workloads that can be managed by this `resource controllers` service.

### Stacks

An orchestrator that stands up or destroys a CDK stack needed for a given type of workload template.

In this example, a standard container workload for APIs will be deployed to the AWS AppRunner service.

### Auxiliary Resources

Provides reusable resources across workload templates. For example, `s3_bucket.py` helps create an S3 bucket for this purpose.

---

# Local Development Setup

## Create Python venv

```sh
python -m venv venv
```

## Activate venv

```sh
source venv/bin/activate
```

## Set up your AWS credentials

```sh
export AWS_ACCESS_KEY_ID={{your_key}}
export AWS_SECRET_ACCESS_KEY={{your_secret}}
export AWS_DEFAULT_REGION={{your_region}}
```

## Install dependencies

```sh
pip install -r requirements.txt --no-cache
```

## Run locally

```sh
make run-local
```

## Build and run Docker container

```sh
make build-docker
make run-docker
```
