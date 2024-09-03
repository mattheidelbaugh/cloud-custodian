# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from c7n.filters import ValueFilter
from c7n.manager import resources
from c7n.query import QueryResourceManager, TypeInfo
from c7n.tags import universal_augment
from c7n.utils import local_session, type_schema


@resources.register('storage-gateway')
class StorageGateway(QueryResourceManager):

    class resource_type(TypeInfo):
        service = 'storagegateway'
        enum_spec = ('list_gateways', 'Gateways', None)
        arn = id = 'GatewayARN'
        arn_type = 'gateway'
        name = 'GatewayName'
        universal_taggable = object()
        permissions_augment = ("storagegateway:ListTagsForResource",)

    augment = universal_augment


@StorageGateway.filter_registry.register('info')
class GatewayInfoFilter(ValueFilter):
    """Filter Storage Gateways by additional info

    :example:

    .. code-block:: yaml

            policies:
              - name: gw-info
                resource: storagegateway
                filters:
                  - type: info
                    key: GatewayTimezone
                    op: eq
                    value: GMT-8:00

    """

    permissions = ('ssm:DescribeGatewayInformation',)
    schema = type_schema('info', rinherit=ValueFilter.schema)
    permissions = ('storagegateway:DescribeGatewayInformation',)
    policy_annotation = 'c7n:MatchedInfo'
    content_annotation = "c7n:Info"

    def process(self, resources, event=None):
        client = local_session(self.manager.session_factory).client('storagegateway')
        results = []
        for r in resources:
            if self.content_annotation not in r:
                info = self.manager.retry(client.describe_gateway_information,
                                          GatewayARN=r['GatewayARN'])
                info.pop('ResponseMetadata', None)
                r[self.content_annotation] = info
            if self.match(info):
                r[self.policy_annotation] = self.data.get('value')
                results.append(r)
        return results
