# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

from c7n.manager import resources
from c7n import query
from c7n.utils import local_session, type_schema
from c7n.tags import Tag, RemoveTag, TagDelayedAction, TagActionFilter, universal_augment
from c7n.actions import BaseAction

class PmtcryptAppJobDescribe(query.DescribeSource):

    def augment(self, resources):
        return universal_augment(self.manager, super().augment(resources))
    
@resources.register('payment-cryptography')
class PmtcryptApp(query.QueryResourceManager):

    class resource_type(query.TypeInfo):
        service = 'payment-cryptography'
        enum_spec = ('list_keys', 'Keys[]', None)
        universal_taggable = object()
        cfn_type = "AWS::PaymentCryptography::Key"
        arn = id = name = "KeyArn"
        permission_prefix = 'payment-cryptography'
        detail_spec = (
            'get_key', 'KeyIdentifier',
            'KeyArn', 'Key')
        
    
    source_mapping = {"describe":PmtcryptAppJobDescribe,}



##################################

@PmtcryptApp.action_registry.register('tag')
class PmtcryptTag(Tag):
    """Action to tag a payment-cryptography"""

    batch_size = 1
    permissions = ('payment-cryptography:TagResource')

    def process(self, resources):
        client = local_session(self.manager.session_factory).client('payment-cryptography')
        for r in resources:
            tags = [{'Key': k, 'Value': v} for k, v in self.data.get('tags',{}).items()]
            self.manager.retry(
                client.tag_resource, ResourceArn=r["KeyArn"], Tags=tags)


@PmtcryptApp.filter_registry.register('marked-for-op')
class PmtcryptMarked(TagActionFilter):
    """Filter to check if """
    schema = type_schema('marked-for-op', rinherit=TagActionFilter.schema)   
    permissions = ('payment-cryptography:TagResource')

    def process(self, resources):
        client = local_session(self.manager.session_factory).client('payment-cryptography')
        tag_key =  self.data.get('tag', '')
        op = self.data.get('op', '{op}')
        marked = []
        for r in resources:
            tags = client.list_tags_for_resource(ResourceArn=r["KeyArn"]).get('Tags', [])
            if tags is None:
                tags = []
            for tag in tags:    
                if tag['Key'] == tag_key and op in tag['Value']:
                    marked.append(r)
                    break
        return marked






@PmtcryptApp.action_registry.register('delete')
class PmtcryptDelete(BaseAction):
    """Action to tag a payment-cryptography resource for derferred action
    :example 

    .. code-block:: yaml

            policies:
                - name: payment-crpytography-delete
                  resource: payment-cryptography
                  filters:
                    - "tag:custodian_cleanup": present
                  actions: 
                    - delete
    """
   
    batch_size = 1
    schema = type_schema('delete')
    permissions = ('payment-cryptography:delete_key',)

    def process(self, resource):
        client = local_session(self.manager.session_factory).client('payment-cryptography')
        for r in resource:
            self.manager.retry(
            client.delete_key, ResourceArn=r["KeyArn"])
                
             