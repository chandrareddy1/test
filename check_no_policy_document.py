from checkov.cloudformation.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.common.util.type_forcers import force_list
import json

class ResourcesWithoutPolicyDocument(BaseResourceCheck):
    def __init__(self):
        name = "Ensure all resources have a Policy Document"
        id = "CUSTOM_CFN_NO_POLICY_DOCUMENT"
        supported_resources = ['*']  # Applies to all resource types
        categories = [CheckCategories.IAM]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        resource_name = conf.get('__startline__')  # Get resource logical ID
        properties = conf.get('Properties', {})

        # Check if PolicyDocument exists in the resource properties
        has_policy_document = self._check_policy_document(properties)

        if not has_policy_document:
            # If no PolicyDocument is found, return FAILED and print resource name
            print(f"Resource without Policy Document: {resource_name}")
            return CheckResult.FAILED
        return CheckResult.PASSED

    def _check_policy_document(self, properties):
        # Check for PolicyDocument directly in properties
        if 'PolicyDocument' in properties:
            return True
        
        # Check for policies in other common property names
        for key, value in properties.items():
            if isinstance(value, dict):
                if 'PolicyDocument' in value:
                    return True
                # Recursively check nested dictionaries
                if self._check_policy_document(value):
                    return True
            elif isinstance(value, list):
                # Check each item in lists
                for item in force_list(value):
                    if isinstance(item, dict) and self._check_policy_document(item):
                        return True
        return False