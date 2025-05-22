 terraform_prompt = """
        You're a senior AWS Solutions Architect creating production-grade Terraform code. Generate infrastructure as code based on the following specifications:

        USER REQUIREMENTS:
        {requirements}

        INFRASTRUCTURE SPECIFICATIONS:
        - AWS Services: {services}
        - AWS Region: {region}
        - VPC CIDR: {vpc_cidr}
        - Subnet Configuration: {subnet_configuration}
        - Availability Zones: {availability_zones}
        - Compute Type: {compute_type}
        - Multi-AZ Deployment: {is_multi_az}
        - Serverless Architecture: {is_serverless}
        - Load Balancer Type: {load_balancer_type}
        - Logging Enabled: {enable_logging}
        - Monitoring Enabled: {enable_monitoring}
        - WAF Enabled: {enable_waf}
        - Resource Tags: {tags}
        - Custom Parameters: {custom_parameters}

        TERRAFORM BEST PRACTICES TO IMPLEMENT:
        1. ONLY Use provider as aws for all the environments
        2. Add region {region} for all the environments under the provider
        3. Create a modular design with proper service isolation
        4. Implement proper network segregation (public/private/database subnets)
        5. Follow least privilege IAM policies and proper encryption
        6. Use environment-specific configurations with proper variable typing
        7. Use data sources for dynamic lookups and proper resource repetition
        8. Put all the network related things under a 'netoworking' module e.g. vpc, subnets, security groups etc.

        ENVIRONMENT CONFIGURATIONS:
        - dev: minimal capacity and redundancy
        - stage: medium capacity with good redundancy
        - prod: high capacity with full redundancy and auto-scaling

        I need you to generate Terraform (HCL) code for the following environments and modules.
        For each environment (dev, stage, prod), create three files:
        1. main.tf - with the module configurations
        2. variables.tf - with input variables
        3. output.tf - with output values
        In each environment configurations (dev, stage, prod), in their main.tf file give the module path as ex: (source = "../../modules/lambda")

        For each required module based on the services list ({services}) and {requirements}, create:
        1. main.tf - with the resource definitions
        2. variables.tf - with input variables for the module
        3. output.tf - with output values from the module

        Format your response with clear headers between each file, like this:
        # ENV: dev - main.tf
        <code here>

        # ENV: dev - variables.tf
        <code here>

        # ENV: dev - output.tf
        <code here>

        # MODULE: vpc - main.tf
        <code here>

        And so on for all environments and modules.
        DO NOT provide explanations or additional text - ONLY the Terraform code with headers.
        IMPORTANT: Do not include any markdown code block syntax or fences (such as triple backticks) around the generated code. Only provide raw .tf content with headers.
        """