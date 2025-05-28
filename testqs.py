import boto3

client = boto3.client('quicksight')
resp = client.create_account_subscription(
    Edition="STANDARD",
    AccountName="c7n-test",
    AwsAccountId="644160558196",
    NotificationEmail="matthew.heidelbaugh@capitalone.com",
    AuthenticationMethod="IAM_ONLY",
)
print(resp)