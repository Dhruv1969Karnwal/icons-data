from typing import Dict

class D2Renderer:
    """Renders professional diagrams with icons INSIDE the active graph nodes."""
    
    def render(self, json_ir: Dict) -> str:
        nodes = json_ir.get("nodes", [])
        edges = json_ir.get("edges", [])
        
        # 1. Setup Global Canvas
        d2_lines = [
            'direction: right',
            '',
            '# --- LAYERS ---',
            ''
        ]

        # 2. Layer Styling Configuration
        layer_configs = {
            "presentation": {"color": "#3498db", "label": "User Interface"},
            "infrastructure": {"color": "#e67e22", "label": "Cloud Infrastructure"},
            "application": {"color": "#9b59b6", "label": "Microservices"},
            "data": {"color": "#2ecc71", "label": "Data Layer"}
        }

        # 3. Map nodes to layers and store node-to-layer mapping for connections
        layers = {}
        node_to_layer = {}
        for node in nodes:
            layer_name = node.get("layer", "application")
            layers.setdefault(layer_name, []).append(node)
            node_to_layer[node["id"]] = layer_name

        # 4. Render Layers and Nodes
        # Use a secondary mapping to handle the key names used in the IR vs the ones in our config
        # Some IR might use 'presentation', 'infrastructure', 'application', 'data'
        # Others might use 'application' or 'services'
        
        # Ensure we cover all layers present in the nodes, even if not in layer_configs
        all_layer_keys = list(layers.keys())
        
        for layer_key in all_layer_keys:
            config = layer_configs.get(layer_key, {"color": "#9b59b6", "label": layer_key.capitalize()})
            
            d2_lines.append(f'{layer_key}: {config["label"]} {{')
            d2_lines.append(f'  style: {{fill: "{config["color"]}"; opacity: 0.1; stroke-dash: 3}}')
            d2_lines.append('')
            
            for node in layers[layer_key]:
                node_id = node["id"]
                label = node.get("label", node_id)
                icon_url = node.get("icon_url", "")
                
                # Logic: Database layers get cylinder shapes automatically, or use shape_type if provided
                shape = node.get("shape_type")
                if not shape:
                    shape = "cylinder" if layer_key == "data" else "rectangle"

                d2_lines.append(f'  {node_id}: {label} {{')
                if shape and shape != "rectangle":
                    d2_lines.append(f'    shape: {shape}')
                if icon_url:
                    d2_lines.append(f'    icon: "{icon_url}"')
                d2_lines.append(f'  }}')
            d2_lines.append('}')
            d2_lines.append('')

        # 5. Render Connections (Edges)
        d2_lines.append('# --- CONNECTIONS ---')
        d2_lines.append('')
        
        for edge in edges:
            src_id = edge.get("from")
            dst_id = edge.get("to")
            lbl = edge.get("label", "")
            
            src_layer = node_to_layer.get(src_id)
            dst_layer = node_to_layer.get(dst_id)
            
            # Use path notation: layer.node
            src_path = f"{src_layer}.{src_id}" if src_layer else src_id
            dst_path = f"{dst_layer}.{dst_id}" if dst_layer else dst_id
            
            arrow = "->"
            if edge.get("type") == "bidirectional":
                arrow = "<->"
            
            if lbl:
                d2_lines.append(f'{src_path} {arrow} {dst_path}: "{lbl}"')
            else:
                d2_lines.append(f'{src_path} {arrow} {dst_path}')

        return "\n".join(d2_lines)



json_ir = {
    "version": "1.0",
    "diagram_metadata": {
      "type": "architecture",
      "direction": "LR",
      "title": "Cloud-Native SaaS Architecture",
      "auto_layout": True
    },
    "nodes": [
      {
        "id": "react_frontend",
        "label": "React/Next.js App",
        "technology": "react",
        "layer": "presentation",
        "description": "Client-side web application",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "cdn",
        "label": "CDN",
        "technology": "aws-cloudfront",
        "layer": "infrastructure",
        "description": "Content Delivery Network for static assets",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "s3_static",
        "label": "S3 Static Assets",
        "technology": "aws-s3",
        "layer": "infrastructure",
        "description": "Storage for frontend static files",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "waf",
        "label": "Web Application Firewall",
        "technology": "aws-waf",
        "layer": "infrastructure",
        "description": "Security layer for traffic filtering",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "alb",
        "label": "Application Load Balancer",
        "technology": "aws-alb",
        "layer": "infrastructure",
        "description": "Load balancing for incoming traffic",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "api_gateway",
        "label": "API Gateway",
        "technology": "aws-api-gateway",
        "layer": "application",
        "description": "Central entry point for API requests",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "auth_service",
        "label": "Auth Service",
        "technology": "oauth2-jwt",
        "layer": "application",
        "description": "Authentication and authorization service",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "user_service",
        "label": "User Service",
        "technology": "nodejs",
        "layer": "application",
        "description": "Manages user profiles and data",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "billing_service",
        "label": "Billing Service",
        "technology": "python",
        "layer": "application",
        "description": "Handles payments and subscriptions",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud-Development-Kit_light-bg.svg",
        "shape_type": "package"
      },
      {
        "id": "notification_service",
        "label": "Notification Service",
        "technology": "golang",
        "layer": "application",
        "description": "Sends emails and push notifications",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "ai_service",
        "label": "AI Service",
        "technology": "python-tensorflow",
        "layer": "application",
        "description": "Machine learning inference engine",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud-Development-Kit_light-bg.svg",
        "shape_type": "package"
      },
      {
        "id": "lambda_processor",
        "label": "Lambda Processor",
        "technology": "aws-lambda",
        "layer": "application",
        "description": "Serverless data processing function",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "postgres_primary",
        "label": "PostgreSQL Primary",
        "technology": "postgresql",
        "layer": "data",
        "description": "Primary relational database",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "postgres_replica",
        "label": "PostgreSQL Replica",
        "technology": "postgresql",
        "layer": "data",
        "description": "Read replica for scaling queries",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "redis_cache",
        "label": "Redis Cache",
        "technology": "redis",
        "layer": "data",
        "description": "In-memory data store for caching",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "elasticsearch",
        "label": "Elasticsearch",
        "technology": "elasticsearch",
        "layer": "data",
        "description": "Search and analytics engine",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "object_storage",
        "label": "Object Storage",
        "technology": "aws-s3",
        "layer": "data",
        "description": "Blob storage for files and models",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "kafka_cluster",
        "label": "Kafka Cluster",
        "technology": "apache-kafka",
        "layer": "data",
        "description": "Event streaming platform",
        "icon_url": "https://icons.terrastruct.com/gcp%2FProducts%20and%20services%2FData%20Analytics%2FCloud%20Dataproc.svg",
        "shape_type": "rectangle"
      },
      {
        "id": "secrets_manager",
        "label": "Secrets Manager",
        "technology": "aws-secrets-manager",
        "layer": "infrastructure",
        "description": "Secure storage for credentials",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "cloudwatch",
        "label": "CloudWatch",
        "technology": "aws-cloudwatch",
        "layer": "infrastructure",
        "description": "Monitoring and logging",
        "icon_url": "https://icons.terrastruct.com/aws%2F_Group%20Icons%2FAWS-Cloud-alt_light-bg.svg",
        "shape_type": "cloud"
      },
      {
        "id": "eks_cluster",
        "label": "EKS Cluster",
        "technology": "kubernetes",
        "layer": "infrastructure",
        "description": "Container orchestration platform",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      },
      {
        "id": "cicd_pipeline",
        "label": "CI/CD Pipeline",
        "technology": "jenkins",
        "layer": "infrastructure",
        "description": "Automated build and deployment",
        "icon_url": "https://icons.terrastruct.com/aws%2FDeveloper%20Tools%2FAWS-Cloud9.svg",
        "shape_type": "cloud"
      }
    ],
    "edges": [
      {
        "from": "react_frontend",
        "to": "cdn",
        "label": "HTTP/HTTPS",
        "type": "unidirectional"
      },
      {
        "from": "cdn",
        "to": "s3_static",
        "label": "Fetch Assets",
        "type": "unidirectional"
      },
      {
        "from": "react_frontend",
        "to": "api_gateway",
        "label": "API Calls",
        "type": "unidirectional"
      },
      {
        "from": "react_frontend",
        "to": "waf",
        "label": "Traffic",
        "type": "unidirectional"
      },
      {
        "from": "waf",
        "to": "alb",
        "label": "Filtered Traffic",
        "type": "unidirectional"
      },
      {
        "from": "alb",
        "to": "api_gateway",
        "label": "Routing",
        "type": "unidirectional"
      },
      {
        "from": "api_gateway",
        "to": "auth_service",
        "label": "Validate Token",
        "type": "unidirectional"
      },
      {
        "from": "api_gateway",
        "to": "user_service",
        "label": "REST/gRPC",
        "type": "unidirectional"
      },
      {
        "from": "api_gateway",
        "to": "billing_service",
        "label": "REST/gRPC",
        "type": "unidirectional"
      },
      {
        "from": "api_gateway",
        "to": "notification_service",
        "label": "REST/gRPC",
        "type": "unidirectional"
      },
      {
        "from": "api_gateway",
        "to": "ai_service",
        "label": "REST/gRPC",
        "type": "unidirectional"
      },
      {
        "from": "auth_service",
        "to": "secrets_manager",
        "label": "Get Keys",
        "type": "unidirectional"
      },
      {
        "from": "user_service",
        "to": "postgres_primary",
        "label": "Write",
        "type": "unidirectional"
      },
      {
        "from": "user_service",
        "to": "postgres_replica",
        "label": "Read",
        "type": "unidirectional"
      },
      {
        "from": "user_service",
        "to": "redis_cache",
        "label": "Cache/Get",
        "type": "bidirectional"
      },
      {
        "from": "user_service",
        "to": "kafka_cluster",
        "label": "Events",
        "type": "unidirectional"
      },
      {
        "from": "billing_service",
        "to": "postgres_primary",
        "label": "Transactions",
        "type": "unidirectional"
      },
      {
        "from": "notification_service",
        "to": "kafka_cluster",
        "label": "Publish",
        "type": "unidirectional"
      },
      {
        "from": "notification_service",
        "to": "elasticsearch",
        "label": "Logs",
        "type": "unidirectional"
      },
      {
        "from": "ai_service",
        "to": "object_storage",
        "label": "Read/Write Models",
        "type": "bidirectional"
      },
      {
        "from": "ai_service",
        "to": "lambda_processor",
        "label": "Async Trigger",
        "type": "unidirectional"
      },
      {
        "from": "kafka_cluster",
        "to": "notification_service",
        "label": "Subscribe",
        "type": "unidirectional"
      },
      {
        "from": "eks_cluster",
        "to": "user_service",
        "label": "Hosts",
        "type": "unidirectional"
      },
      {
        "from": "eks_cluster",
        "to": "billing_service",
        "label": "Hosts",
        "type": "unidirectional"
      },
      {
        "from": "eks_cluster",
        "to": "notification_service",
        "label": "Hosts",
        "type": "unidirectional"
      },
      {
        "from": "eks_cluster",
        "to": "ai_service",
        "label": "Hosts",
        "type": "unidirectional"
      },
      {
        "from": "cicd_pipeline",
        "to": "eks_cluster",
        "label": "Deploy",
        "type": "unidirectional"
      },
      {
        "from": "auth_service",
        "to": "cloudwatch",
        "label": "Logs",
        "type": "unidirectional"
      },
      {
        "from": "user_service",
        "to": "cloudwatch",
        "label": "Logs",
        "type": "unidirectional"
      }
    ]
  }

# Usage example:
# renderer = D2Renderer()
# d2_code = renderer.render(json_ir)

# print(f"=====CODE IS HERE=====")
# print(d2_code)