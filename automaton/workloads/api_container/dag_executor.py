# workloads/api_container/dag_executor.py

import networkx as nx
from .resource_creators import (
    create_s3_bucket,
    pullFrom_ecr_repo,
    create_apprunner_role,
    create_apprunner_service,
)
import json


def run(stack):
    context = stack.node.try_get_context

    image_repo = context("image_repo")
    image_tag = context("image_tag")
    service_name = context("service_name")
    resources = context("resources")
    action = context("action")

    if action != "deploy":
        return

    resources = resources if isinstance(resources, list) else json.loads(resources)
    env_vars = {}
    results = {}
    dag = nx.DiGraph()

    for r in resources:
        if r["type"] == "s3":
            dag.add_node(r["name"], type="s3", props=r.get("properties", {}))
            dag.add_edge(r["name"], "apprunner_service")

    dag.add_node("ecr_repo", type="ecr")
    dag.add_node("apprunner_role", type="role")
    dag.add_node("apprunner_service", type="service")

    dag.add_edge("ecr_repo", "apprunner_service")
    dag.add_edge("apprunner_role", "apprunner_service")

    for node in nx.topological_sort(dag):
        ntype = dag.nodes[node]["type"]
        if ntype == "s3":
            create_s3_bucket(stack, node, dag.nodes[node]["props"], env_vars, results)
        elif ntype == "ecr":
            pullFrom_ecr_repo(stack, image_repo, results)
        elif ntype == "role":
            create_apprunner_role(stack, results)
        elif ntype == "service":
            create_apprunner_service(stack, service_name, image_tag, env_vars, results)
