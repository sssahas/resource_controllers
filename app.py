from flask import Flask, request, jsonify
import subprocess
import yaml
from pathlib import Path
import re
import json

app = Flask(__name__)

CDK_DIR = "automaton"
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


def parse_destroy_output(stderr: str):
    lines = stderr.splitlines()
    stack_name = None
    resources = []

    resource_line_pattern = re.compile(
        r"(?P<stack>[\w\-]+)\s+\|\s+\d+\s+\|\s+[\d:APM ]+\s+\|\s+(?P<status>[\w_]+)\s+\|\s+(?P<type>[\w:]+)\s+\|\s+(?P<name>.+)"
    )

    for line in lines:
        if "destroying..." in line:
            match = re.match(r"(?P<stack>[\w\-]+): destroying", line)
            if match:
                stack_name = match.group("stack")

        match = resource_line_pattern.match(line)
        if match:
            resources.append(
                {
                    "type": match.group("type"),
                    "name": match.group("name").strip(),
                    "status": match.group("status"),
                }
            )

    return {"status": "destroyed", "stack": stack_name, "resources": resources}


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
    resources = data.get("resources", {})
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
        f"resources={json.dumps(resources)}",
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


@app.route("/destroy", methods=["POST"])
def destroy():
    data = request.json
    service_name = data["service_name"]
    if service_name is None:
        return jsonify({"error": "service_name is required"}), 400
    command = [
        "cdk",
        "destroy",
        "--context",
        f"service_name={service_name}",
        "--context",
        "action=destroy",
        "--force",
    ]

    result = subprocess.run(command, cwd=CDK_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"status": "error", "stderr": result.stderr}), 500

    # return jsonify({"status": "destroyed", "service_name": service_name})
    parsed = parse_destroy_output(result.stderr)
    return jsonify(parsed)


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
