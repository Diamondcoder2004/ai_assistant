# Cloud and Kubernetes icon shapes

Use **`shape=mxgraph.<library>.<icon>;`** plus `whiteSpace=wrap;html=1;` as needed. Exact icon ids match the embedded draw.io stencils; if a name fails to render, open the file in [diagrams.net](https://app.diagrams.net) and pick the shape from the library to copy its style.

## Pattern

```xml
<mxCell id="lambda-1" value="Orders API"
        style="shape=mxgraph.aws4.lambda_function;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#232F3E;"
        vertex="1" parent="1">
  <mxGeometry x="200" y="120" width="80" height="80" as="geometry"/>
</mxCell>
```

## AWS (`shape=mxgraph.aws4.*`)

Prefix: **`shape=mxgraph.aws4.`** — example suffixes:

| Concept | Example style suffix |
|---------|----------------------|
| EC2 | `ec2` |
| S3 | `s3` |
| Lambda | `lambda_function` |
| RDS | `rds` |
| VPC | `virtual_private_cloud` |
| ELB / ALB | `application_load_balancer` (or ELB stencil name in editor) |
| CloudFront | `cloudfront` |
| Route 53 | `route_53` |
| IAM | `iam` |
| SQS / SNS | `sqs`, `sns` |
| DynamoDB | `dynamodb` |
| ECS / EKS | `ecs`, `eks` |

## Azure (`shape=mxgraph.azure.*`)

Prefix: **`shape=mxgraph.azure.`** — examples:

| Concept | Example style suffix |
|---------|----------------------|
| VM | `virtual_machine` |
| Blob storage | `storage` or blob icon from stencil |
| Functions | `function_apps` |
| SQL DB | `sql_database` |
| VNet | `virtual_networks` |
| Load Balancer | `azure_load_balancer` |
| App Service | `app_service` |
| AKS | `kubernetes_services` |

## GCP (`shape=mxgraph.gcp2.*`)

Prefix: **`shape=mxgraph.gcp2.`** — examples:

| Concept | Example style suffix |
|---------|----------------------|
| Compute Engine | `compute_engine` |
| Cloud Storage | `cloud_storage` |
| Cloud Functions | `cloud_functions` |
| Cloud SQL | `cloud_sql` |
| VPC | `virtual_private_cloud` |
| Load balancing | `network_load_balancing` / LB icon from library |
| GKE | `google_kubernetes_engine` |
| Pub/Sub | `cloud_pubsub` |

## Kubernetes (`shape=mxgraph.kubernetes.*`)

Prefix: **`shape=mxgraph.kubernetes.`** — examples: **`pod`**, **`service`**, **`deployment`**, **`ingress`**, **`config_map`**, **`secret`**, **`namespace`**, **`node`**. Verify underscore form in the stencil if a name does not render.

## Generic network (Cisco / basic)

When cloud icons are unnecessary, use neutral topology shapes (see `SKILL.md`):

- **Router** — `shape=mxgraph.cisco.routers.router;`
- **Switch** — `shape=mxgraph.cisco.switches.workgroup_switch;`
- **Firewall** — `shape=mxgraph.cisco.firewalls.firewall;`
- **Server** — `shape=mxgraph.cisco.servers.standard_server;`
- **Database** — cylinder or `mxgraph.azure.sql_database` / RDS icon as appropriate.

Prefer **one icon family per diagram** (all AWS4, or all neutral) unless mixing is intentional for legend clarity.
