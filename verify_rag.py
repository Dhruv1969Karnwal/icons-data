import requests
import json

URL = "http://localhost:8001/api/rag"

# 1. Test Data - S3 and CloudHSM
test_icons = [
  {
    "id": "4754874a-0667-41b9-b64e-7a1f2b8f9c87",
    "slug": "essentials-add",
    "iconify_id": "material-symbols:add",
    "provider": "Essential Icons",
    "url": "https://icons.terrastruct.com/essentials%2F073-add.svg",
    "semantic_profile": "This icon represents a generic action to add a new component in architecture diagrams. It is used in diagramming tools to indicate the ability to insert new elements. Common in design and modeling phases for creating and modifying system blueprints.",
    "display_name": "Add",
    "aliases": "[\"add\",\"add button\",\"add component\",\"add icon\",\"add element\"]",
    "description": "Add from ESSENTIALS. Generic placeholder for adding a new architectural component in diagramming tools",
    "technical_intent": "Generic placeholder for adding a new architectural component in diagramming tools",
    "shape_type": "image",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#6366F1",
    "popularity": 0.5,
    "tags": "[\"add\",\"placeholder\",\"diagramming\",\"generic\",\"ui\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "97be0e71-1f49-49f5-8dd6-501b38c3def6",
    "slug": "dev-amazonwebservices",
    "iconify_id": "devicon:amazonwebservices",
    "provider": "Development Tools",
    "url": "https://icons.terrastruct.com/dev%2Famazonwebservices.svg",
    "semantic_profile": "Amazon Web Services (AWS) is a comprehensive cloud platform offering infrastructure, platform, and software services. It provides scalable compute, storage, databases, and networking. Used for building and deploying applications in the cloud.",
    "display_name": "Amazonwebservices",
    "aliases": "[\"AWS\",\"Amazon Web Services\",\"Amazon Cloud\",\"Amazon Cloud Services\",\"Amazon Web Services (AWS)\"]",
    "description": "Amazonwebservices from DEV. Amazon Web Services cloud platform for hosting and managing cloud infrastructure",
    "technical_intent": "Amazon Web Services cloud platform for hosting and managing cloud infrastructure",
    "shape_type": "cloud",
    "default_width": 64,
    "is_container": True,
    "icon_position": "top-left",
    "color_theme": "#FF9900",
    "popularity": 0.5,
    "tags": "[\"cloud\",\"aws\",\"iaas\",\"paaS\",\"saas\",\"cloud-computing\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "af297ed6-3e22-4eb9-b445-fcf8fb3e5442",
    "slug": "infra-access-denied",
    "iconify_id": "logos:infra-access-denied",
    "provider": "Infrastructure",
    "url": "https://icons.terrastruct.com/infra%2F001-access-denied.svg",
    "semantic_profile": "Access control mechanism that evaluates permissions and denies unauthorized requests. Enforces least privilege and prevents data breaches. Common in IAM systems and network security policies.",
    "display_name": "Access Denied",
    "aliases": "[\"403\",\"forbidden\",\"unauthorized\",\"denied\",\"access control\",\"security policy\"]",
    "description": "Access Denied from INFRA. Security control that enforces access restrictions and returns denied responses",
    "technical_intent": "Security control that enforces access restrictions and returns denied responses",
    "shape_type": "hexagon",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#6366F1",
    "popularity": 0.5,
    "tags": "[\"security\",\"access control\",\"iam\",\"authorization\",\"forbidden\",\"403\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "d1be4dfc-4255-4bc0-a5da-4d6b1add46e9",
    "slug": "tech-antenna",
    "iconify_id": "mdi:antenna",
    "provider": "Technology",
    "url": "https://icons.terrastruct.com/tech%2Fantenna.svg",
    "semantic_profile": "Antenna is a custom technology asset designed for receiving and processing signals. It serves as an entry point for data streams and is used in scenarios requiring real-time signal handling.",
    "display_name": "Antenna",
    "aliases": "[\"antenna\",\"signal receiver\",\"custom asset\"]",
    "description": "Antenna from TECH. Custom technology asset acting as an antenna for signal reception and processing",
    "technical_intent": "Custom technology asset acting as an antenna for signal reception and processing",
    "shape_type": "image",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#6366F1",
    "popularity": 0.5,
    "tags": "[\"custom\",\"signal\",\"reception\",\"processing\",\"general\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "39a40f40-5895-4e8f-9ac7-b743d899b6bd",
    "slug": "social-behance",
    "iconify_id": "mingcute:behance-fill",
    "provider": "Social Media",
    "url": "https://icons.terrastruct.com/social%2F054-behance.svg",
    "semantic_profile": "Behance is a social media platform for creative professionals. It allows users to showcase portfolios, connect with others, and discover creative work. Used by designers, artists, and agencies for networking and job opportunities.",
    "display_name": "Behance",
    "aliases": "[\"Behance\",\"Adobe Behance\",\"behance.net\",\"creative social network\"]",
    "description": "Behance from SOCIAL. Social platform for creative professionals to showcase and discover work",
    "technical_intent": "Social platform for creative professionals to showcase and discover work",
    "shape_type": "image",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#6366F1",
    "popularity": 0.5,
    "tags": "[\"social\",\"creative\",\"portfolio\",\"networking\",\"adobe\",\"saas\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "93ba3ca6-39f7-4ad7-b368-a07021b3e95e",
    "slug": "emotions-angel",
    "iconify_id": "mingcute:angel-fill",
    "provider": "Emojis",
    "url": "https://icons.terrastruct.com/emotions%2F003-angel.svg",
    "semantic_profile": "Angel is an API service that analyzes text, audio, or video for emotional content and sentiment. It provides real-time emotion detection and sentiment scoring for applications in customer service, social media, and market research.",
    "display_name": "Angel",
    "aliases": "[\"Angel\",\"emotion analysis\",\"sentiment analysis\",\"affect detection\",\"emotional intelligence\"]",
    "description": "Angel from EMOTIONS. API for emotion analysis and sentiment detection in user-generated content",
    "technical_intent": "API for emotion analysis and sentiment detection in user-generated content",
    "shape_type": "hexagon",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#6366F1",
    "popularity": 0.5,
    "tags": "[\"api\",\"emotional\",\"sentiment\",\"analysis\",\"cognitive\",\"ai\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "ad7ba893-cdf5-4af9-be59-21331a7884be",
    "slug": "aws-ad-connector-light",
    "iconify_id": "logos:aws-ad-connector-light",
    "provider": "Amazon Web Services",
    "url": "https://icons.terrastruct.com/aws%2FSecurity%2C%20Identity%2C%20&%20Compliance%2FAD-Connector_light-bg.svg",
    "semantic_profile": "AWS AD Connector Light connects on-premises Active Directory to AWS, enabling directory services for AWS resources. It supports single sign-on and group-based access control. Used for integrating existing on-prem AD with AWS for authentication and authorization.",
    "display_name": "Ad Connector Light",
    "aliases": "[\"AD Connector\",\"Active Directory Connector\",\"AD Connect\",\"AD Connector for AWS\"]",
    "description": "Ad Connector Light from AWS. Enables on-premises Active Directory integration for AWS resource authentication",
    "technical_intent": "Enables on-premises Active Directory integration for AWS resource authentication",
    "shape_type": "hexagon",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#FF9900",
    "popularity": 0.5,
    "tags": "[\"security\",\"directory\",\"identity\",\"authentication\",\"aws\",\"ad\",\"on-premises\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "6fc894e1-1d7e-4505-a6fd-84762b864a08",
    "slug": "gcp-ai-hub",
    "iconify_id": "logos:gcp-ai-hub",
    "provider": "Google Cloud Platform",
    "url": "https://icons.terrastruct.com/gcp%2FProducts%20and%20services%2FAI%20and%20Machine%20Learning%2FAI%20Hub.svg",
    "semantic_profile": "Google Cloud AI Hub is a service for managing and sharing machine learning assets (models, datasets, notebooks) across teams. It enables collaboration, version control, and discovery of AI resources. Used for ML project management and asset sharing in GCP.",
    "display_name": "Ai Hub",
    "aliases": "[\"AI Hub\",\"GCP AI Hub\",\"Google AI Hub\",\"ML Hub\",\"AI Asset Hub\"]",
    "description": "Ai Hub from GCP. Centralized hub for managing and sharing machine learning assets and workflows",
    "technical_intent": "Centralized hub for managing and sharing machine learning assets and workflows",
    "shape_type": "hexagon",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#4285F4",
    "popularity": 0.5,
    "tags": "[\"gcp\",\"ai\",\"ml\",\"asset management\",\"collaboration\",\"api\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  },
  {
    "id": "f233f5b0-3849-46f9-8c0e-c06506d73224",
    "slug": "azure-api-connections",
    "iconify_id": "logos:azure-api-connections",
    "provider": "Microsoft Azure",
    "url": "https://icons.terrastruct.com/azure%2FWeb%20Service%20Color%2FAPI%20Connections.svg",
    "semantic_profile": "Azure API Connections provide secure, managed connections to external services and APIs. They handle authentication and connection management for Logic Apps, enabling integration with third-party services in serverless workflows.",
    "display_name": "Api Connections",
    "aliases": "[\"API Connection\",\"Connection\",\"Azure API Connection\",\"Logic Apps Connection\",\"API Connector\"]",
    "description": "Api Connections from AZURE. Managed connection to external APIs for serverless workflow automation in Azure Logic Apps",
    "technical_intent": "Managed connection to external APIs for serverless workflow automation in Azure Logic Apps",
    "shape_type": "hexagon",
    "default_width": 64,
    "is_container": False,
    "icon_position": "center",
    "color_theme": "#0078D4",
    "popularity": 0.5,
    "tags": "[\"api\",\"integration\",\"logic-apps\",\"serverless\",\"azure\",\"connection\"]",
    "last_scraped": "2026-01-19T11:32:56Z"
  }
]


def verify():
    print("🚀 Starting Verification...")
    
    # Upload
    print("\n📤 Uploading icons...")
    resp = requests.post(f"{URL}/upload", json={"icons": test_icons})
    print(f"Status: {resp.status_code}, Response: {resp.json()}")
    
    # Search for CloudHSM
    print("\n🔍 Searching for 'connector light'...")
    resp = requests.get(f"{URL}/search", params={"q": "connector light", "top_k": 1})
    data = resp.json()
    if data["results"]:
        hit = data["results"][0]
        print(f"✅ Found: {hit['display_name']} (Score: {hit['score']}, Search Type: {hit['search_type']})")
        print(f"📄 Ingestion Doc: {hit.get('search_document')}")
        # Verify format
        expected_start = "connector light by Amazon Web Services. Category"
        if hit.get('search_document', '').startswith("connector light by"):
            print("✅ Ingestion string format is CORRECT")
        else:
            print(f"❌ Ingestion string format is INCORRECT: {hit.get('search_document')}")
    else:
        print("❌ 'connector light' not found!")

    # Search for S3
    print("\n🔍 Searching for 'social media'...")
    resp = requests.get(f"{URL}/search", params={"q": "social media", "top_k": 1})
    data = resp.json()
    if data["results"]:
        hit = data["results"][0]
        print(f"✅ Found: {hit['display_name']} (Score: {hit['score']}, Search Type: {hit['search_type']})")
    else:
        print("❌ 'social media' not found!")

if __name__ == "__main__":
    verify()
