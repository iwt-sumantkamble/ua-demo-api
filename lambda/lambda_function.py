import json
import logging
import os
from http import HTTPStatus

import demo_service
from constant import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    print(event)
    try:
        body = {
            'aws_request_id': context.aws_request_id,
            'memory_limit_in_mb': context.memory_limit_in_mb,
            'remaining_time_in_millis': context.get_remaining_time_in_millis(),
            'cookies': event.get('cookies', []),
            'headers': event.get('headers', {}),
            'queryStringParameters': event.get('queryStringParameters', {}),
            'pathParameters': event.get('pathParameters', {}),
            'environ': dict(os.environ),
        }
        method = event.get(HTTP_METHOD, None)
        if GET == method:
            if event.get(PATH_PARAMETERS, None) and event[PATH_PARAMETERS].get(PARAM_ITEM, None):
                body = demo_service.get_by_id(str(event[PATH_PARAMETERS][PARAM_ITEM]))
            else:
                body = demo_service.get_all()
        response = {
            'isBase64Encoded': False,
            'statusCode': HTTPStatus.OK,
            'body': json.dumps(body, indent=2),
            'headers': {
                'content-type': 'application/json',
            },
        }
    except Exception as e:
        response = {
            'isBase64Encoded': False,
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': f'Exception={e}',
            'headers': {
                'content-type': 'text/plain',
            },
        }
    return response
