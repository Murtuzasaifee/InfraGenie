from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformOutput, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
from src.infra_genie.utils.Utility import Utility
    

class CodeGeneratorNode:
    
    def __init__(self, llm):
        self.llm = llm
        self.utility = Utility()
       
    
    def generate_terraform_code(self, state: InfraGenieState):
        
        """
        Generate Terraform code with structured output.
        
        """

        if not state.user_input:
            raise ValueError("User input is required to generate Terraform code")
        
        try:
            print("Trying structured code approach...")
                    
            prompt_template = self.get_terraform_code_prompt(state)
            logger.debug(f"Prompt Template: {prompt_template}")
            
            structured_prompt = PromptTemplate.from_template(prompt_template)
            
            logger.debug(f"Structured Prompt: {structured_prompt.to_json()}")

            input_dict = state.user_input.model_dump()
            logger.debug(f"User Input: {input_dict}")

            structured_llm = self.llm.with_structured_output(TerraformOutput)
            structured_chain = structured_prompt | structured_llm
    
            result = structured_chain.invoke(input_dict)
            
            logger.debug(f"Result: {result}")
            
            # Transfer the structured result to the state
            for env in result.environments:
                state.environments.environments.append(TerraformComponent(
                    name=env.name,
                    main_tf=env.main_tf,
                    output_tf=env.output_tf,
                    variables_tf=env.variables_tf
                ))
            
            for module in result.modules:
                state.modules.modules.append(TerraformComponent(
                    name=module.name,
                    main_tf=module.main_tf,
                    output_tf=module.output_tf,
                    variables_tf=module.variables_tf
                ))
            
            print(f"Successfully generated {len(state.environments.environments)} environments and {len(state.modules.modules)} modules using structured output")
            state.code_generated = True
            state.next_node = const.CODE_VALIDATION
            
        except Exception as primary_error:
            print(f"Structured output approach failed: {primary_error}")
            state.code_generated = False
            state.next_node = const.FALLBACK_GENERATION
        
        return state
    
    
    
    def get_terraform_code_prompt(self, state: InfraGenieState) -> str:
        terraform_prompt = """
        **Objective:** Generate a production-grade Terraform configuration (in HCL, not JSON) for an AWS infrastructure spanning development, staging, and production environments.

        **Inputs:**
        - **Requirements:** {{requirements}}
        - **Services:** {{services}}
        - **VPC CIDR:** {{vpc_cidr}}
        - **Subnet Configuration:** {{subnet_configuration}}
        - **Availability Zones:** {{availability_zones}}
        - **Compute Type:** {{compute_type}}
        - **Multi-AZ (`is_multi_az`):** {{is_multi_az}}
        - **Serverless (`is_serverless`):** {{is_serverless}}
        - **Load Balancer Type:** {{load_balancer_type}}
        - **Enable Logging:** {{enable_logging}}
        - **Enable Monitoring:** {{enable_monitoring}}
        - **Enable WAF:** {{enable_waf}}
        - **Tags:** {{tags}}
        - **Database Type:** {{database_type}}
        - **Custom Parameters:** {{custom_parameters}}
        - **AWS Region:** {{region}}

        **Requirements for the Terraform Configuration:**

        1. **Environment Structure:** Create separate configurations for three environments – dev, stage, and prod. Each environment should be defined in its own Terraform configuration (e.g., under an `environments/` directory). These environment files will instantiate infrastructure using reusable modules (defined below).
        2. **Modular Design:** Set up a `modules/` directory containing Terraform modules for each major component:
        - Networking module (VPC, subnets, routing, etc.)
        - Modules for each AWS service listed in **Services** (and any additional components inferred from the requirements). For example, if EC2 is a service, have an EC2 (or compute) module; if RDS or DynamoDB is needed (per **Database Type**), have a database module; if serverless compute (Lambda) is used, a Lambda module; etc. Include a module for the load balancer if one is required.
        3. **Module Integration:** In each environment’s Terraform config, use `module` blocks to call these modules. Use relative paths (e.g., `source = "../../modules/<module_name>"`) to reference module code. Provide environment-specific inputs via variables (for instance, to pass different parameters like instance count, instance size, or any naming prefixes for each environment).
        4. **Networking Setup:** Implement a VPC using the provided CIDR (`{{vpc_cidr}}`). Create subnets as specified by **Subnet Configuration** (e.g., a set of public, private, and database subnets in each AZ as required). Attach an Internet Gateway for public subnets and NAT Gateways for outbound internet access from private subnets. Ensure routing tables direct internet traffic appropriately (public subnets route to IGW, private subnets route through NAT). If `is_multi_az` is true, create subnets in multiple availability zones (from the list provided) and deploy redundant resources across those AZs. If `is_multi_az` is false, a single-AZ deployment is acceptable (though still create the subnet structure in one AZ).
        5. **Security and IAM:** Apply the principle of least privilege throughout:
        - Create IAM roles for compute resources (EC2 instances, ECS tasks, Lambda functions, etc.) with only the necessary permissions (for example, permission to access specific S3 buckets, DynamoDB tables, or other AWS services as needed by the application).
        - If the architecture includes an ECS cluster or EKS, set up any required IAM roles (e.g., ECS task role and execution role; EKS node instance profile).
        - If a load balancer is used, use security groups to allow inbound HTTP/HTTPS (as needed) and restrict access as appropriate. For other components, restrict security group rules to only required ports and sources (e.g., allow DB access only from application subnets or instances).
        - Enable encryption at rest: ensure EBS volumes, RDS databases, etc., have encryption enabled (using AWS-managed or customer-managed keys as appropriate). For S3 buckets, enable default SSE encryption. For DynamoDB, enable encryption (this is on by default in AWS).
        - Enable encryption in transit: enforce HTTPS for any web endpoints (use an SSL certificate on ALB if `load_balancer_type` is ALB), and require TLS connections for databases.
        - If `enable_waf` is true, provision an AWS WAFv2 Web ACL with a reasonable set of rules (could start with AWS Managed Rules) and associate it with the ALB or CloudFront/web distribution if one is inferred by the architecture.
        6. **Compute Resources & Load Balancing:** Configure compute resources based on **Compute Type**:
        - **EC2:** If compute_type is EC2 (and not serverless), use an Auto Scaling Group to manage EC2 instances across the appropriate subnets. Use a Launch Template (or Launch Configuration) specifying the AMI (you can use a generic Amazon Linux 2 AMI via data source), instance type, and user data if needed. Attach the instances to the specified **{{load_balancer_type}}** (e.g., register them in an ALB target group). Ensure health checks are in place. If multi-AZ, span the ASG across subnets in multiple AZs. Include scaling policies (target tracking or step scaling) for the ASG.
        - **ECS/Fargate:** If using ECS (especially with `is_serverless` false for EC2 launch type or true for Fargate), create an ECS cluster (for EC2 launch type, also create an ASG of container instances; for Fargate, no ASG needed). Define an ECS task definition and service for the application. Attach the service to an ALB (if ALB is used) with an appropriate listener and target group. Set up auto-scaling for the ECS service (e.g., using Application Auto Scaling based on CPU utilization).
        - **EKS:** If compute_type is EKS, provision an EKS cluster (which might involve creating node groups or Fargate profiles). This is complex; at minimum, create the cluster and an autoscaling node group across subnets, and perhaps note that application deployment on EKS is outside Terraform’s direct scope (if the user just wants infrastructure).
        - **Lambda (Serverless):** If `is_serverless` is true and compute_type indicates a serverless approach (Lambda), deploy AWS Lambda functions for the application logic. If the application is web-facing, set up an API Gateway (HTTP API or REST API) or an Application Load Balancer to trigger the Lambda. Configure appropriate IAM roles for the Lambda (e.g., to allow access to other services like DynamoDB or S3 as needed). If using API Gateway, define the API Gateway resources (this could also be done via Terraform).
        - **Load Balancer:** Implement the specified **load_balancer_type** if the architecture requires an entry point for web traffic. For ALB, set up listeners (port 80/443 as appropriate) and target groups for the application instances/tasks/Lambda. For NLB, set up listeners (e.g., TCP 80/443 or other ports as needed) and targets. Ensure the load balancer is placed in public subnets and has appropriate security group rules (for ALB) or is attached to the correct subnets (for NLB which uses subnet associations).
        7. **Database and Persistence:** Based on **Database Type**:
        - For a relational database (e.g., RDS MySQL/PostgreSQL or Aurora), create a DB subnet group using the database subnets. Launch an RDS instance (or Aurora cluster) with multi-AZ enabled if `is_multi_az` is true. Use the engine and instance class appropriate for the DB type. Set up master username/password (store these in Secrets Manager as mentioned below). Make the DB only accessible within the VPC (no public access). Output the DB endpoint for use by the application.
        - For DynamoDB or other NoSQL serverless databases, create the table with the required key schema and throughput settings. Ensure that the application has the table name (via environment variable) and IAM permissions to access it.
        - If other storage is needed (e.g., S3 buckets for static content or backups), create those with versioning and encryption enabled.
        8. **Logging and Monitoring:** 
        - If `enable_logging` is true, set up AWS CloudWatch Logs and other logging as appropriate. Create CloudWatch Log Groups for each relevant service (e.g., application logs from EC2 or Lambda, execution logs, etc.). Enable access logging on the ALB (targeting an S3 bucket or CloudWatch Logs). Enable VPC Flow Logs to CloudWatch or S3 for network monitoring.
        - If `enable_monitoring` is true, create CloudWatch Alarms for critical metrics (CPU, memory, ALB response times or error rates, Lambda errors/throttles, etc.). If appropriate, set up SNS topics to receive alarm notifications (though actual SNS subscription detail might be out of scope). You can also include a CloudWatch Dashboard summarizing key metrics for each environment. Optionally, include AWS CloudTrail (for auditing) or AWS Config rules to monitor compliance, if it fits the requirements.
        9. **Secrets Management:** Use AWS Secrets Manager or SSM Parameter Store for sensitive data. For example, if the database requires a password, store that password in Secrets Manager (Terraform can create a random password and put it in a Secret). Reference this secret in the Terraform code (for example, pass the Secrets Manager ARN to the application module, or set an environment variable for Lambda from this secret). Ensure that the IAM policies allow the application (EC2 IAM role, ECS task role, or Lambda role) to read the secret. Do **not** expose sensitive values in plaintext in the Terraform output.
        10. **Terraform Practices (data sources, count/for_each):** Use **Terraform data sources** to retrieve dynamic values (e.g., use `data "aws_region"` or `data "aws_caller_identity"` if needed, `data "aws_ami"` for latest AMIs, etc.). Use **count** or **for_each** for resources that can be parameterized: for instance, use a count to create multiple subnets/NAT Gateways for each AZ, or for_each on a list of AZs for resource creation, or looping through tags map to attach tags, etc., to avoid repetitive code.
        11. **Outputs:** For each module (and possibly each environment), define outputs that might be useful (e.g., VPC ID, subnet IDs, ALB DNS name, DB endpoint, etc.), and ensure environment configurations capture these if needed for cross-module references (you might use outputs from the networking module as inputs to other modules like providing subnet IDs to the compute module).
        12. **Organize & Document:** Structure the Terraform code in a clear, logical manner. Each module may have its own `main.tf` (and optionally `variables.tf` and `outputs.tf`). Each environment directory will have a `main.tf` that calls modules (and possibly a `providers.tf` and `variables.tf` for any environment-specific provider config or input variables). In the **output response**, clearly delineate sections by file path or module name for readability. **Include comments** in the HCL code to explain any tricky parts or to note where the user must insert their specific values (for example, `<YOUR_CERT_ARN_HERE>` for an ACM certificate, or a note to replace placeholder values for things like AMI IDs if a specific one is needed). Ensure no commentary outside of code/comments — the response should essentially be a set of Terraform configuration files that the user can use.

        **Output Instructions:** Provide the complete Terraform configuration as described. Format your output as follows:

        1. Start each file with a line: "### FILE: path/to/filename.tf"
        2. Then include the complete file content
        3. End each file with a line: "### END FILE"
        4. Do not use any markdown code fences, indentation, or other formatting that could interfere with parsing
        5. Include comments within the code for any necessary explanations
        6. Do not include any additional text or explanations outside of the code files

        Example:
        ### FILE: modules/networking/main.tf
        resource "aws_vpc" "main" {
        cidr_block = var.vpc_cidr
        tags = var.tags
        }
        # Rest of VPC resources...
        ### END FILE

        ### FILE: modules/networking/variables.tf
        variable "vpc_cidr" {
        description = "CIDR block for the VPC"
        type        = string
        }
        # More variables...
        ### END FILE

        Now, **generate the Terraform code** according to these specifications.
        """


        
        # Check if code_validation_error exists and insert it into the prompt if it does
        code_feedback = getattr(state, 'code_validation_error', None)
        if code_feedback:
            # Insert the feedback after the objective line but before the inputs section
            objective_line = "**Objective:** Generate a production-grade Terraform configuration (in HCL, not JSON) for an AWS infrastructure spanning development, staging, and production environments."
            feedback_section = f"\n**Incorporate the following code review feedback::** {code_feedback}\n"
            
            # Replace the objective line with objective + feedback
            terraform_prompt = terraform_prompt.replace(
                objective_line, 
                objective_line + feedback_section
            )
        
        return terraform_prompt
    
    def is_code_generated(self, state: InfraGenieState):
        """Decide whether to use the fallback method based on the code generation status."""
        return state.code_generated
    
    def fix_code(self, state: InfraGenieState):
        pass