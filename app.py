from flask import Flask, request, jsonify
import subprocess
import boto3
import yaml
from pathlib import Path
import os
import json

app = Flask(__name__)

CDK_DIR = "my_cdk"
PORT = 8080

def run_cdk_command(command_args):
    try:
        result = subprocess.run(
            command_args,
            cwd=CDK_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "output": e.stderr, "code": e.returncode}



@app.route("/bootstrap", methods=["POST"])
def bootstrap():
    result = run_cdk_command(
        [
            "cdk",
            "bootstrap",
            "aws://899156640268/us-east-1",
            "--output",
            "cd.out.bootstrap",
        ]
    )
    if result["status"] == "success":
        return (
            jsonify({"message": "CDK bootstrap complete", "output": result["output"]}),
            200,
        )
    else:
        return jsonify({"error": "Bootstrap failed", "details": result["output"]}), 500


@app.route("/deploy", methods=["POST"])
def deploy():
    data = request.json
    image_repo = data["image_repo"]
    image_tag = data["image_tag"]
    template_name = data["template_name"]
    service_name = data.get(
        "service_name", f"{image_repo}-{image_tag.replace('.', '-')}"
    )
    resources = data.get("resources",{})
    output_dir = f"cd.out.deploy.{service_name}"

    command = [
        "cdk",
        "--context",
        f"image_repo={image_repo}",
        "--context",
        f"image_tag={image_tag}",
        "--context",
        f"service_name={service_name}",
        "--context",
        f"template_name={template_name}",
        "--context",
        "action=deploy",
        "--context",
        f"resources={resources}",        
        "--output",
        output_dir,
        "deploy",
        "--require-approval",
        "never",
    ]

    result = subprocess.run(command, cwd=CDK_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        return (
            jsonify(
                {
                    "request_status": "error",
                    "service_name": service_name,
                    "service_url": None,
                    "service_status": None,
                    "error": result.stderr,
                    "error_code": result.returncode,
                }
            ),
            500,
        )

    try:
        output_path = os.path.join(CDK_DIR, output_dir, "ApiDeployerStack.outputs.json")
        with open(output_path) as f:
            outputs = json.load(f)

        service_url = outputs["ApiDeployerStack.ServiceUrl"]["value"]
        status = outputs["ApiDeployerStack.ServiceStatus"]["value"]

        return jsonify(
            {
                "request_status": "deployed",
                "service_name": service_name,
                "service_url": service_url,
                "service_status": status,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "request_status": "error",
                    "service_name": service_name,
                    "service_url": None,
                    "service_status": None,
                    "error": str(e),
                    "error_code": None,
                }
            ),
            500,
        )


@app.route("/destroy", methods=["POST"])
def destroy():
    data = request.json
    service_name = data["service_name"]
    command = [
        "cdk",
        "--context",
        f"service_name={service_name}",
        "--context",
        "action=destroy",
        "--output",
        f"cd.out.destroy.{service_name}",
        "destroy",
        "--force",
    ]

    result = subprocess.run(command, cwd=CDK_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"status": "error", "stderr": result.stderr}), 500

    return jsonify({"status": "destroyed", "service_name": service_name})


@app.route("/workload-templates", methods=["GET"])
def list_templates():
    templates = []
    templates_dir = Path("workload-templates")
    long = False
    long = request.args.get("long", "False")
    if long.lower() == "true" or long == True:
        long = True
    
    for yaml_file in templates_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if long == True:
                templates.append(
                    {
                        "template_name": data["template_name"],
                        "description": data.get("description"),
                        "required_inputs": data.get("required_inputs", []),
                        "optional_inputs": data.get("optional_inputs", []),
                        "outputs": data.get("outputs", []),
                        "long_description": data.get("long_description", ""),
                    }
                )
            else:
                templates.append(
                    {
                        "template_name": data["template_name"],
                        "description": data.get("description"),
                    }
                )

    return jsonify(templates)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
