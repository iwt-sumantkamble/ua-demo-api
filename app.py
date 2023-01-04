#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.ua_demo_api_stack import UaDemoApiStack

app = cdk.App()
stage = app.node.try_get_context('stage')
env = cdk.Environment(account=os.getenv('AWS_ACCOUNT'),
                      region=os.getenv('AWS_REGION'))
UaDemoApiStack(app, 'ua-demo-api', env=env, stage=stage)
app.synth()
