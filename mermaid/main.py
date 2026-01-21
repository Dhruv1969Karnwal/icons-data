import json
from mermaid.pipeline import DiagramGenerationPipeline

def main():
    print(f"\n{'#'*80}")
    print(f"#{'ARCHITECTURE DIAGRAM GENERATOR - MODULAR MODE'.center(78)}#")
    print(f"{'#'*80}\n")
    
    pipeline = DiagramGenerationPipeline()
    
    # Example 1: Simple web app
    user_request = """
    Build a large-scale cloud-native SaaS application with:
    - Include many nodes and relationships.
    - Show Frontend, Backend, Databases, Caching, Messaging, AI/ML, Observability, Security, and DevOps layers. 
    - Frontend should include: React, Next.js, CDN, S3.
    - Backend should include: API Gateway, Auth Service, User Service, Billing Service, Notification Service, AI Service.
    - Datastores should include: PostgreSQL (primary + read replicas), Redis, Elasticsearch, Object Storage.
    - Messaging/Eventing: Kafka or RabbitMQ.
    - Infrastructure: AWS (ALB, ECS/EKS, Lambda, CloudWatch).
    - Security: OAuth2, JWT, WAF, Secrets Manager.
    - DevOps: CI/CD pipeline, Docker, Kubernetes.
    """
    
    print(f"📋 Test Case: Web Application Architecture")
    print(f"{'─'*80}\n")
    
    result = pipeline.generate(user_request)
    with open("output_modular.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"📊 FINAL OUTPUT - JSON IR")
    print(f"{'='*80}")
    print(json.dumps(result["json_ir"], indent=2))
    
    print(f"\n{'='*80}")
    print(f"🎨 FINAL OUTPUT - MERMAID DIAGRAM CODE")
    print(f"{'='*80}")
    print(result["mermaid"])
    
    print(f"\n{'='*80}")
    print(f"💡 ARCHITECTURE SUGGESTIONS")
    print(f"{'='*80}")
    if result["suggestions"]:
        for i, suggestion in enumerate(result["suggestions"], 1):
            print(f"{i}. {suggestion}")
    else:
        print("No suggestions provided.")
    
    print(f"\n{'='*80}")
    print(f"📈 PIPELINE STATISTICS")
    print(f"{'='*80}")
    print(f"🔄 Total Iterations: {result['iterations']}")
    print(f"📦 Total Nodes: {len(result['json_ir'].get('nodes', []))}")
    print(f"🔗 Total Edges: {len(result['json_ir'].get('edges', []))}")
    print(f"💬 Total Suggestions: {len(result['suggestions'])}")
    print(f"📏 Mermaid Output Size: {len(result['mermaid'])} characters")
    print(f"\n{'#'*80}")
    print(f"#{'GENERATION COMPLETE'.center(78)}#")
    print(f"{'#'*80}\n")

if __name__ == "__main__":
    main()
