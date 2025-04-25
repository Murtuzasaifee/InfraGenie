import json
from src.infra_genie.state.infra_genie_state import UserInput

class Utility:
    
    def __init__(self):
        pass
    
    def get_formatted_code_prompt(self, user_input: UserInput) -> str:
        return self.get_terraform_code_prompt().format(
            requirements=user_input.requirements or "None",
            services=", ".join(user_input.services),
            region=user_input.region,
            vpc_cidr=user_input.vpc_cidr,
            subnet_configuration=json.dumps(user_input.subnet_configuration, indent=2).replace("{", "{{").replace("}", "}}"),
            availability_zones=", ".join(user_input.availability_zones),
            compute_type=user_input.compute_type,
            database_type=user_input.database_type or "None",
            is_multi_az="Yes" if user_input.is_multi_az else "No",
            is_serverless="Yes" if user_input.is_serverless else "No",
            load_balancer_type=user_input.load_balancer_type or "None",
            enable_logging="Yes" if user_input.enable_logging else "No",
            enable_monitoring="Yes" if user_input.enable_monitoring else "No",
            enable_waf="Yes" if user_input.enable_waf else "No",
            tags=", ".join([f"{k}={v}" for k, v in user_input.tags.items()]),
            custom_parameters=json.dumps(user_input.custom_parameters, indent=2).replace("{", "{{").replace("}", "}}") if user_input.custom_parameters else "None"
        )

    
    