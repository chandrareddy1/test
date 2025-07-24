# Analysis and Proposed Solution for Default VPC Deletion in AWS Accounts

## Objective
You want to understand the value of replacing the default VPC deletion logic in your custom Python automation framework with an AWS-native solution, given that the deletion process is already automated. Additionally, you asked whether Service Control Policies (SCPs) could prevent default VPC creation in future accounts, and you’re seeking a solution that integrates with your existing framework for provisioning new AWS accounts.

## Analysis

### Current Approach
- **Custom Python Framework**: Your framework automates AWS account provisioning and includes logic to delete default VPCs across all regions, likely using Boto3 to identify and delete VPCs and their dependencies (e.g., subnets, internet gateways).
- **Status**: The deletion logic is working within your framework, and you’re not replacing the entire framework, only considering extracting the VPC deletion piece.
- **Question**: Why move default VPC deletion to an AWS-native solution if it’s already automated?

### Benefits of Moving to an AWS-Native Solution
Switching the default VPC deletion logic to an AWS-native approach (e.g., AWS CloudFormation with a Lambda-backed custom resource) offers several advantages over maintaining it in your custom Python framework:

1. **Reduced Maintenance Overhead**:
   - **Custom Framework**: Requires you to maintain Python scripts, handle Boto3 updates, and manage error cases (e.g., dependency violations) manually.
   - **AWS-Native (CloudFormation/Lambda)**: Leverages AWS-managed services, reducing code maintenance. CloudFormation templates are declarative, and Lambda handles runtime updates, minimizing your team’s effort.

2. **Infrastructure-as-Code (IaC)**:
   - **Custom Framework**: Likely relies on imperative scripts, which are harder to version, audit, or reproduce consistently.
   - **AWS-Native**: CloudFormation provides a standardized, version-controlled IaC approach, improving traceability and repeatability. This aligns with AWS best practices for infrastructure management.

3. **Scalability with AWS Organizations**:
   - **Custom Framework**: Scaling to multiple accounts requires custom logic for cross-account access and orchestration, often involving complex IAM role assumptions.
   - **AWS-Native**: AWS StackSets seamlessly deploy the deletion logic to all accounts in an Organizational Unit (OU), with built-in cross-account IAM roles, simplifying multi-account management.

4. **Error Handling and Reliability**:
   - **Custom Framework**: You must implement error handling (e.g., retry logic, dependency checks) in Python, which can be error-prone.
   - **AWS-Native**: Lambda provides built-in retry mechanisms and logging via CloudWatch. CloudFormation ensures consistent deployment and rollback if errors occur.

5. **Integration with AWS Ecosystem**:
   - **Custom Framework**: Integration with AWS services (e.g., EventBridge for triggering) requires additional scripting.
   - **AWS-Native**: Easily integrates with AWS EventBridge, SNS, or Step Functions to trigger deletion during account creation, leveraging AWS’s event-driven architecture.

6. **Security and Compliance**:
   - **Custom Framework**: Relies on your scripts to manage IAM credentials securely, which can introduce risks if not handled properly.
   - **AWS-Native**: Uses IAM roles with least-privilege permissions, managed by CloudFormation, and integrates with SCPs to enforce compliance (e.g., restricting default VPC usage).

### Trade-Offs of Moving to AWS-Native
- **Initial Setup Effort**: Creating a CloudFormation template and Lambda function requires upfront work, though this is minimal with the provided artifacts.
- **Learning Curve**: Your team may need familiarity with CloudFormation and Lambda if not already in use, but these are standard AWS tools.
- **Dependency on AWS Services**: Ties you to AWS-managed services, though this aligns with your goal of using AWS-native tools.

### Why Keep the Custom Framework?
- **Already Functional**: If your Python scripts are stable and handle edge cases (e.g., dependencies, errors), there’s no immediate need to change.
- **Flexibility**: Custom scripts offer full control over logic, which may be preferred if your use case has unique requirements.
- **Minimal Disruption**: Keeping the logic avoids modifying your existing workflow, which is critical since you’re not replacing the entire framework.

### Can SCPs Prevent Default VPC Creation?
You asked if SCPs, if already in place, would prevent default VPC creation in future accounts. The answer is no:
- **AWS-Managed Process**: AWS creates default VPCs in all supported regions during account provisioning, outside the scope of IAM actions that SCPs control.
- **SCP Limitations**: SCPs restrict user/role actions (e.g., `ec2:CreateVpc`, `ec2:RunInstances`) but cannot block AWS’s internal VPC creation process.
- **SCP Role**: SCPs can restrict *usage* of default VPCs post-creation (e.g., deny launching resources in them), complementing deletion logic.

### Evaluation of AWS-Native Alternatives
Since you’re satisfied with automation but want an AWS-native solution for default VPC deletion, the following options were considered:

1. **AWS CloudFormation with Lambda-backed Custom Resource** (Recommended):
   - **Pros**: Infrastructure-as-code, scalable with StackSets, robust error handling, integrates with your framework via API/SNS/EventBridge.
   - **Cons**: Requires initial setup and minor integration changes.
   - **Why Best**: Aligns with AWS best practices, reduces maintenance, and leverages your existing SCPs for compliance.

2. **AWS CLI Scripts**:
   - **Pros**: Simple to implement.
   - **Cons**: Not IaC, manual maintenance, less scalable for multiple accounts.

3. **AWS Systems Manager (SSM) Automation**:
   - **Pros**: Can execute deletion workflows.
   - **Cons**: Less flexible than Lambda for region iteration and dependency handling.

4. **AWS Control Tower**:
   - **Pros**: Deletes its own VPC in the landing zone region.
   - **Cons**: Doesn’t cover all regions or scale to all accounts.

5. **AWS SDK (Boto3)**:
   - **Pros**: Similar to your current approach.
   - **Cons**: Not IaC, requires manual integration.

### Key Requirements
- **Automation**: Delete default VPCs in all regions for new accounts.
- **Integration**: Seamlessly trigger from your existing Python/PowerShell framework.
- **AWS-Native**: Use managed AWS services for deletion logic.
- **Scalability**: Support multiple accounts, ideally via AWS Organizations.
- **Security**: Use IAM roles for secure access.
- **Compliance**: Leverage existing SCPs to restrict default VPC usage.
- **Minimal Disruption**: Replace only the deletion logic, preserving the rest of your framework.

## Proposed Solution
The best AWS-native solution is to use **AWS CloudFormation with a Lambda-backed custom resource** to handle default VPC deletion, triggered by your existing Python/PowerShell framework. This replaces your current Boto3-based deletion logic while maintaining integration with your workflow. An SCP complements this by restricting default VPC usage, leveraging your existing SCPs.

### Solution Components
1. **Lambda Function**:
   - Python-based, using Boto3.
   - Iterates through all regions, identifies default VPCs (`isDefault=true`), deletes dependencies (subnets, internet gateways), and deletes the VPC.
   - Optionally tags VPCs for SCP compatibility.

2. **CloudFormation Template**:
   - Deploys the Lambda function and an IAM role with permissions for `ec2:Describe*`, `ec2:Delete*`, and `ec2:CreateTags`.
   - Includes a custom resource to trigger deletion during stack creation.

3. **Integration with Existing Framework**:
   - Trigger the CloudFormation stack creation from your Python/PowerShell scripts using an AWS SDK call (e.g., `boto3.client('cloudformation').create_stack()`), SNS message, or EventBridge rule.
   - Example: Call stack creation after account provisioning completes.

4. **AWS StackSets (Optional)**:
   - For multi-account environments, deploy the stack via StackSets to all accounts in an OU, with automatic deployment for new accounts.

5. **SCP Enforcement**:
   - Use an SCP to deny resource creation in default VPCs (tagged or identified).
   - Leverage your existing SCPs for additional compliance.

### Implementation Steps
1. **Create Lambda Function and CloudFormation Template**:
   - Deploy a CloudFormation stack to handle VPC deletion.
   - Artifacts are provided below.

2. **Integrate with Existing Framework**:
   - Modify your Python/PowerShell scripts to trigger the CloudFormation stack after account provisioning.
   - Example: Use Boto3 to call `create_stack` or publish to an SNS topic.

3. **Deploy with StackSets (Optional)**:
   - If using AWS Organizations, create a StackSet to deploy the stack to all accounts in the OU, with auto-deployment for new accounts.

4. **Enhance with SCP**:
   - Apply an SCP to deny resource creation in default VPCs.
   - Tag VPCs in the Lambda function if needed for SCP compatibility.

5. **Test and Monitor**:
   - Test in a single account to ensure deletion works.
   - Monitor Lambda logs in CloudWatch.
   - Verify SCP enforcement by testing resource creation in a default VPC.

### Artifacts

#### Lambda Function Code
This Python Lambda function deletes default VPCs across all regions.

```python
import boto3
import cfnresponse

def delete_default_vpc(region):
    ec2 = boto3.client('ec2', region_name=region)
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    if not vpcs['Vpcs']:
        return f"No default VPC in {region}"
    
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    # Tag VPC for SCP compatibility (optional)
    ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'isDefault', 'Value': 'true'}])
    # Delete internet gateways
    igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
    for igw in igws.get('InternetGateways', []):
        igw_id = igw['InternetGatewayId']
        ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw_id)
    # Delete subnets
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    for subnet in subnets.get('Subnets', []):
        ec2.delete_subnet(SubnetId=subnet['SubnetId'])
    # Delete VPC
    ec2.delete_vpc(VpcId=vpc_id)
    return f"Deleted default VPC {vpc_id} in {region}"

def lambda_handler(event, context):
    try:
        request_type = event['RequestType']
        if request_type in ['Create', 'Update']:
            regions = boto3.client('ec2').describe_regions()['Regions']
            for region in regions:
                delete_default_vpc(region['RegionName'])
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
```

#### CloudFormation Template
This template deploys the Lambda function and IAM role.

```yaml
Resources:
  DeleteVPCFunction:
    Type: AWS::Lambda::Function
    Properties:
      Handler: index.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        ZipFile: |
          import boto3
          import cfnresponse
          
          def delete_default_vpc(region):
              ec2 = boto3.client('ec2', region_name=region)
              vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
              if not vpcs['Vpcs']:
                  return f"No default VPC in {region}"
              
              vpc_id = vpcs['Vpcs'][0]['VpcId']
              ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'isDefault', 'Value': 'true'}])
              igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
              for igw in igws.get('InternetGateways', []):
                  igw_id = igw['InternetGatewayId']
                  ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
                  ec2.delete_internet_gateway(InternetGatewayId=igw_id)
              subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
              for subnet in subnets.get('Subnets', []):
                  ec2.delete_subnet(SubnetId=subnet['SubnetId'])
              ec2.delete_vpc(VpcId=vpc_id)
              return f"Deleted default VPC {vpc_id} in {region}"
          
          def lambda_handler(event, context):
              try:
                  request_type = event['RequestType']
                  if request_type in ['Create', 'Update']:
                      regions = boto3.client('ec2').describe_regions()['Regions']
                      for region in regions:
                          delete_default_vpc(region['RegionName'])
                      cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
                  else:
                      cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
              except Exception as e:
                  cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
      Runtime: python3.9
      Timeout: 300
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: VPCDeletePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ec2:DescribeRegions
                  - ec2:DescribeVpcs
                  - ec2:DescribeInternetGateways
                  - ec2:DescribeSubnets
                  - ec2:DetachInternetGateway
                  - ec2:DeleteInternetGateway
                  - ec2:DeleteSubnet
                  - ec2:DeleteVpc
                  - ec2:CreateTags
                Resource: '*'
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: '*'
  CustomResource:
    Type: AWS::CloudFormation::CustomResource
    Properties:
      ServiceToken: !GetAtt DeleteVPCFunction.Arn
```

#### SCP to Restrict Default VPC Usage
This SCP denies resource creation in default VPCs, assuming they are tagged.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "rds:CreateDBInstance",
        "elasticloadbalancing:CreateLoadBalancer"
      ],
      "Resource": "arn:aws:ec2:*:*:vpc/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/isDefault": "true"
        }
      }
    }
  ]
}
```

#### Integration Example with Existing Framework
This Python snippet triggers the CloudFormation stack from your framework.

```python
import boto3

def trigger_vpc_deletion(account_id, region='us-east-1'):
    cf_client = boto3.client('cloudformation', region_name=region)
    stack_name = f"DeleteDefaultVPC-{account_id}"
    try:
        cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=open('delete_default_vpc.yaml').read(),  # Path to CloudFormation template
            Capabilities=['CAPABILITY_IAM']
        )
        cf_client.get_waiter('stack_create_complete').wait(StackName=stack_name)
        print(f"Default VPC deletion stack deployed for account {account_id}")
    except cf_client.exceptions.AlreadyExistsException:
        print(f"Stack {stack_name} already exists")
    except Exception as e:
        print(f"Error deploying stack: {e}")

# Call after account provisioning in your framework
trigger_vpc_deletion(new_account_id)
```

### Benefits of Moving to AWS-Native
- **Lower Maintenance**: Reduces upkeep of custom deletion scripts.
- **IaC Alignment**: Uses CloudFormation for consistency and auditability.
- **Scalability**: StackSets simplify multi-account deployments.
- **Reliability**: Lambda’s error handling and CloudWatch logging improve robustness.
- **Compliance**: Integrates with existing SCPs to restrict default VPC usage.
- **Minimal Disruption**: Replaces only the deletion logic, triggered by your framework.

### Considerations
- **Permissions**: Ensure the Lambda role and your framework’s credentials have permissions for `ec2:Describe*`, `ec2:Delete*`, `ec2:CreateTags`, and `cloudformation:CreateStack`.
- **Dependencies**: The Lambda function handles standard dependencies (subnets, internet gateways) but may fail if other resources (e.g., EC2 instances) exist. Add checks if needed.
- **Region Coverage**: Dynamically fetches all regions using `describe-regions`.
- **Restoring VPCs**: Deleted default VPCs require AWS Support to restore; confirm this aligns with your needs.
- **SCP Tagging**: If your SCPs rely on tags, the Lambda function tags VPCs; otherwise, remove the tagging logic to simplify.

## Conclusion
While your current Python framework automates default VPC deletion effectively, moving this logic to **AWS CloudFormation with a Lambda-backed custom resource** reduces maintenance, aligns with AWS best practices, and enhances scalability and reliability. SCPs cannot prevent default VPC creation but can restrict usage post-deletion, complementing the solution. The provided artifacts integrate seamlessly with your existing framework, requiring only a trigger (e.g., Boto3 `create_stack` call). This approach minimizes disruption while leveraging AWS-native tools for a more robust, future-proof solution.