# InfraGenie

## _Your Magic Wand for Effortless Cloud Infrastructure_

![InfraGenie Logo](https://img.shields.io/badge/InfraGenie-Cloud%20Infrastructure%20Generator-blue)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

InfraGenie is an AI-powered infrastructure code generator that uses LLMs to create production-ready Terraform code for AWS environments. It handles the complexity of configuring best-practice infrastructure as code, allowing you to focus on your application requirements rather than cloud configuration details.

## 🌟 Features

- **AI-Powered Terraform Generation**: Automatically generate production-ready Terraform code from simple requirements
- **Multi-Environment Support**: Creates configurations for dev, stage, and prod environments
- **Modular Architecture**: Generates reusable Terraform modules for different AWS services
- **Best Practices Included**: Follows AWS Well-Architected Framework and Terraform best practices
- **Multiple LLM Support**: Works with Groq, Gemini, OpenAI, Mistral, and Qwen models
- **Code Validation**: Built-in Terraform validation and feedback
- **User-Friendly Interface**: Simple web UI built with Streamlit

## 📋 Prerequisites

- Python 3.12+
- uv (Python package installer)
- Docker (for Redis)
- Terraform CLI
- API keys for any of the supported LLMs:
  - Groq
  - Gemini
  - OpenAI
  - Mistral
  - Qwen

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/infragenie.git
   cd infragenie
   ```

2. Create and activate a virtual environment with uv:
   ```bash
   # Create a virtual environment
   uv venv
   
   # Activate it
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies using uv:
   ```bash
   # Install uv if you don't have it
   pip install uv
   
   # If uv is already installed then, install project dependencies
   uv sync
   ```

4. Start the Redis container:
   ```bash
   docker-compose up -d
   ```

5. Create a `.env` file with your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   QWEN_API_KEY=your_qwen_api_key
   
   # Optional LangFuse tracking (for observability)
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_HOST=your_langfuse_host
   ```

## 🏃‍♂️ Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

3. Follow the workflow in the UI:
   - Enter a project name
   - Define your infrastructure requirements
   - Select AWS services and configuration details
   - Generate and validate Terraform code
   - Download the generated artifacts

## 🔄 Workflow

InfraGenie follows a structured workflow:

1. **Project Initialization**: Set up a new project
2. **Requirements Collection**: Specify your infrastructure needs
3. **Code Generation**: AI generates Terraform code based on requirements
4. **Code Validation**: Terraform code is validated for correctness
5. **Artifact Generation**: Downloadable Terraform files are created

## 🏗️ Architecture

InfraGenie uses a modular architecture with the following components:

- **UI Layer**: Streamlit-based web interface
- **Graph Layer**: LangGraph-powered workflow orchestration
- **LLM Integration**: Multiple LLM support for code generation
- **Code Processing**: Terraform validation and output formatting
- **Caching**: Redis-based state management

## 📁 Project Structure

```
infragenie/
├── src/
│   └── infra_genie/
│       ├── LLMS/                # LLM integrations (Groq, Gemini, OpenAI, etc.)
│       ├── cache/               # Redis cache implementation
│       ├── data/                # Static data files
│       ├── graph/               # LangGraph workflow definitions
│       ├── nodes/               # Workflow nodes implementation
│       ├── notebooks/           # Development notebooks
│       ├── prompts/             # LLM prompt templates
│       ├── state/               # State management
│       ├── ui/                  # Streamlit UI components
│       └── utils/               # Utility functions
├── docker-compose.yaml          # Docker setup for Redis
├── main.py                      # Application entry point
├── pyproject.toml               # Project dependencies
├── .python-version              # Python version specification
├── uv.lock                      # uv lock file for dependency management
└── README.md                    # This file
```

## 🚀 Generated Terraform Structure

InfraGenie generates Terraform code with the following structure:

```
output/src/
├── environments/               # Environment-specific configurations
│   ├── dev/                    # Development environment
│   │   ├── main.tf             # Main configuration referencing modules
│   │   ├── variables.tf        # Input variables
│   │   └── output.tf           # Output values
│   ├── stage/                  # Staging environment
│   └── prod/                   # Production environment
└── modules/                    # Reusable Terraform modules
    ├── vpc/                    # VPC/networking module
    ├── ec2/                    # EC2 compute module
    ├── rds/                    # RDS database module
    └── ...                     # Other service modules
```

## 📄 Example

Here's a sample workflow to generate a VPC with EC2 instances and RDS:

1. Start InfraGenie and enter a project name
2. Specify your requirements:
   - AWS Services: ec2, rds, alb
   - Region: us-west-2
   - VPC CIDR: 10.0.0.0/16
   - Subnet Configuration for public, private, and database subnets
   - Compute Type: ec2
   - Database Type: postgres
   - Multi-AZ: true
   - Requirements: "Create a highly available web application with a PostgreSQL database."

3. Generate and validate code
4. Download the resulting Terraform files

## 🧩 Supported AWS Services

InfraGenie supports a wide range of AWS services, including:

### Compute
- EC2, Lambda, Autoscaling, EKS, ECS, Batch, Lightsail, Outposts

### Storage
- S3, EFS, FSx, Glacier, Backup, Storage Gateway

### Networking
- VPC, Route53, API Gateway, CloudFront, ELB, ALB, NLB, Global Accelerator

### Security
- IAM, KMS, WAFv2, Shield, GuardDuty, Macie, Inspector, Secrets Manager, Certificate Manager

### Monitoring
- CloudWatch, CloudTrail, X-Ray, Config, Health, Trusted Advisor

### Analytics
- Athena, Glue, EMR, Kinesis, QuickSight, Data Pipeline

### Developer Tools
- CodeCommit, CodePipeline, CodeDeploy, CodeBuild, CloudFormation, Systems Manager

### AI Services
- SageMaker, Comprehend, Rekognition, Textract, Translate, Polly, Forecast

### Messaging
- SNS, SQS, EventBridge, SES

### Search
- OpenSearch, CloudSearch

### Other
- Mobile Hub, IoT Core, AppSync, Step Functions, App Mesh

### Databases
- RDS, DynamoDB, Redshift, Neptune, DocumentDB, Keyspaces, MemoryDB

## 🛠️ Development

### Managing Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for dependency management, a fast Python package installer and resolver.

- Add a new dependency:
  ```bash
  uv add <package-name>
  ```

- Update dependencies:
  ```bash
  uv sync
  ```

### Virtual Environment

uv handles virtual environment creation and activation:

```bash
# Create a new virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/MacOS
# or
.venv\Scripts\activate     # On Windows
```

## 📚 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ❤️ Made with Love

Built with passion to automate the process.

If you find this project useful, please consider giving it a star ⭐
