import os
import json
import argparse

import onepanel.core.api
from onepanel.core.api.models.metric import Metric
from onepanel.core.api.rest import ApiException
from onepanel.core.api.models import Parameter

def main(args):
    # Load Task A metrics
    with open(args.from_file) as f:
        metrics = json.load(f)

    with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as f:
        token = f.read()

    # Configure API authorization
    configuration = onepanel.core.api.Configuration(
        host = os.getenv('ONEPANEL_API_URL'),
        api_key = {
            'authorization': token
        }
    )
    configuration.api_key_prefix['authorization'] = 'Bearer'

    # Call SDK method to save metrics
    with onepanel.core.api.ApiClient(configuration) as api_client:
        api_instance = onepanel.core.api.WorkflowServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')
        uid = os.getenv('ONEPANEL_RESOURCE_UID')
        body = onepanel.core.api.AddWorkflowExecutionsMetricsRequest()
        body.metrics = metrics
        try:
            api_response = api_instance.add_workflow_execution_metrics(namespace, uid, body)
            print('Metrics added.')
        except ApiException as e:
            print('Exception when calling WorkflowServiceApi->add_workflow_execution_metrics: %s\n' % e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--from_file', help='JSON file containing metrics.', required=True)

    main(parser.parse_args())