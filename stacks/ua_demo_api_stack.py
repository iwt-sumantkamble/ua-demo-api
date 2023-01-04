from aws_cdk import (
    Stack,
    Duration,
    aws_route53 as _r53,
    aws_lambda as _lambda,
    aws_apigateway as _apigw,
    aws_dynamodb as _dynamodb,
    aws_certificatemanager as _cm,
    aws_route53_targets as _r53targets, RemovalPolicy, CfnOutput
)
from constructs import Construct

from stacks import rootDomain, memory_size


class UaDemoApiStack(Stack):

    def build_infrastructure(self):

        # Create Lambda function
        lambda_function = _lambda.Function(
            self, f'{self.recordName}-lambda',
            function_name=self.recordName,
            runtime=_lambda.Runtime.PYTHON_3_9,  # type: ignore
            code=_lambda.Code.from_asset('lambda'),
            handler='lambda_function.lambda_handler',
            timeout=Duration.seconds(30),
            environment={'stage': self.stage},
            memory_size=self.memory_size,
        )

        # Create DynamoDB table
        ua_demo_table = _dynamodb.Table(
            self, f'{self.recordName}-table',
            table_name='ua-demo',
            partition_key=_dynamodb.Attribute(
                name='id', type=_dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )
        lambda_function.add_environment('TABLE_NAME', ua_demo_table.table_name)

        # Grant Lambda permission to access DynamoDB
        ua_demo_table.grant_read_write_data(lambda_function)

        # Create ApiGateway
        default_cors_preflight_options = _apigw.CorsOptions(
            allow_headers=_apigw.Cors.DEFAULT_HEADERS,  # type: ignore
            allow_origins=_apigw.Cors.ALL_ORIGINS,  # type: ignore
            allow_methods=_apigw.Cors.ALL_METHODS,  # type: ignore
            status_code=200
        )
        api = _apigw.LambdaRestApi(
            self, f'{self.recordName}-gw',
            handler=lambda_function,
            description='Demo API',
            endpoint_types=[_apigw.EndpointType.REGIONAL],
            deploy_options=_apigw.StageOptions(
                stage_name=self.stage, variables={'stage': self.stage}),
            default_cors_preflight_options=default_cors_preflight_options,
            proxy=False
        )
        api_gw_proxy = api.root.add_proxy(
            any_method=False,
            default_cors_preflight_options=default_cors_preflight_options,
            default_method_options=_apigw.MethodOptions(api_key_required=False)
        )
        api_gw_proxy.add_method(http_method='ANY', api_key_required=False)

        # Create a new hosted zone
        route53_hosted_zone = _r53.HostedZone.from_lookup(
            self, f'{self.recordName}-hz',
            domain_name=self.rootDomain
        )
        certificate = _cm.Certificate(
            self, f'{self.recordName}-cert',
            domain_name=f'{self.recordName}.{self.rootDomain}',
            validation=_cm.CertificateValidation.from_dns(route53_hosted_zone)
        )
        api_gw_domain_name = api.add_domain_name(
            f'{self.recordName}-domain',
            domain_name=f'{self.recordName}.{self.rootDomain}',
            certificate=certificate
        )
        _r53.ARecord(
            self, f'{self.recordName}-record',
            record_name=self.recordName,
            zone=route53_hosted_zone,
            target=_r53.RecordTarget.from_alias(
                _r53targets.ApiGatewayDomain(api_gw_domain_name))
        )
        CfnOutput(self, 'Endpoint',
                  value=f'https://{api_gw_domain_name.domain_name}')

    def __init__(self, scope: Construct, construct_id: str, stage: str = 'dev', **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stage = stage
        self.recordName = 'ua-demo-api'
        self.rootDomain = rootDomain[stage]
        self.memory_size = memory_size[stage]
        self.build_infrastructure()
