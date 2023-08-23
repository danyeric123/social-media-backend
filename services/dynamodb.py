import logging

import botocore

logger = logging.getLogger(__name__)


class Users:
    """Encapsulates an Amazon DynamoDB table of user data."""
    def __init__(self, table):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.table = table

    def get_user(self, username: str):
        """
        Gets user data from the table for a specific user.

        :param user: user.
        """
        try:
            response = self.table.get_item(Key={'username': username})
        except botocore.exceptions.ClientError as err:
            logger.error(
                "Couldn't get user %s from table %s. Here's why: %s: %s",
                username, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Item']

