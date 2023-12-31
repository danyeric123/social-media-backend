import asyncio
import re

import jwt

import utils
from models.users import UserDocument, find_user
from services.secrets import get_secret
from utils.logging import LOG_MANAGER

logger = LOG_MANAGER.getLogger(__name__)


def lambda_handler(event, context):
    """
    Validate the incoming token and produce the principal user identifier
    associated with the token. This can be accomplished in a number of ways:

    1. Call out to the OAuth provider
    2. Decode a JWT token inline
    3. Lookup in a self-managed DB


    You can send a 401 Unauthorized response to the client by failing like so:

      raise Exception('Unauthorized')

    If the token is valid, a policy must be generated which will allow or deny
    access to the client. If access is denied, the client will receive a 403
    Access Denied response. If access is allowed, API Gateway will proceed with
    the backend integration configured on the method that was called.

    This function must generate a policy that is associated with the recognized
    principal user identifier. Depending on your use case, you might store
    policies in a DB, or generate them on the fly.

    Keep in mind, the policy is cached for 5 minutes by default (TTL is
    configurable in the authorizer) and will apply to subsequent calls to any
    method/resource in the RestApi made with the same token.

    The example policy below denies access to all resources in the RestApi.
    """

    logger.info("Authorizer received event: " + str(event),)

    policy = AuthPolicy(event)

    if "authorization-token" not in event["headers"]:
        logger.info("No token was passed")
        policy.denyAllMethods()
        authResponse = policy.build()
        return authResponse

    logger.info("Client token: " + event["headers"]["authorization-token"],)
    logger.info("Method ARN: " + event["routeArn"])

    token = event["headers"]["authorization-token"]
    try:
        payload = jwt.decode(
            token,
            key=get_secret(),
            algorithms=[
                "HS256",
            ],
        )
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        policy.denyAllMethods()
        authResponse = policy.build()
        return authResponse

    async def get_user(username: str) -> UserDocument:
        await utils.setup()
        return await find_user(username)

    found_user = asyncio.run(get_user(payload["username"]))

    if payload["username"] == found_user.username:
        logger.info(
            "User authorized",
            extra={
                "username": payload["username"],
                "found_user": found_user.username,
            },
        )
        policy.allowAllMethods()
    else:
        logger.info(
            "User not authorized",
            extra={
                "username": payload["username"],
                "found_user": found_user.username,
            },
        )
        policy.denyAllMethods()
    # policy.allowMethod(HttpVerb.GET, '/pets/*')

    # Finally, build the policy
    authResponse = policy.build()

    return authResponse


class HttpVerb:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL = "*"


class AuthPolicy(object):
    # The AWS account id the policy will be generated for. This is used to create the method ARNs.
    awsAccountId = ""
    # The principal used for the policy, this should be a unique identifier for the end user.
    principalId = ""
    # The policy version used for the evaluation. This should always be '2012-10-17'
    version = "2012-10-17"
    # The regular expression used to validate resource paths for the policy
    pathRegex = "^[/.a-zA-Z0-9-\*]+$"
    """Internal lists of allowed and denied methods.

    These are lists of objects and each object has 2 properties: A resource
    ARN and a nullable conditions statement. The build method processes these
    lists and generates the approriate statements for the final policy.
    """
    allowMethods = []
    denyMethods = []
    """Replace the placeholder value with a default API Gateway API id to be used in the policy.
    Beware of using '*' since it will not simply mean any API Gateway API id, because stars will greedily expand over '/' or other separators.
    See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more details."""
    restApiId = "<<restApiId>>"
    """Replace the placeholder value with a default region to be used in the policy.
    Beware of using '*' since it will not simply mean any region, because stars will greedily expand over '/' or other separators.
    See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more details."""
    region = "<<region>>"
    """Replace the placeholder value with a default stage to be used in the policy.
    Beware of using '*' since it will not simply mean any stage, because stars will greedily expand over '/' or other separators.
    See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more details."""
    stage = "<<stage>>"

    def __init__(self, event):
        tmp = event["routeArn"].split(":")
        apiGatewayArnTmp = tmp[5].split("/")
        self.restApiId = apiGatewayArnTmp[0]
        self.region = tmp[3]
        self.stage = apiGatewayArnTmp[1]
        self.awsAccountId = tmp[4]
        self.principalId = "user|a1b2c3d4"
        self.allowMethods = []
        self.denyMethods = []

    def _addMethod(self, effect, verb, resource, conditions):
        """Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null."""
        if verb != "*" and not hasattr(HttpVerb, verb):
            raise NameError("Invalid HTTP verb " + verb +
                            ". Allowed verbs in HttpVerb class")
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError("Invalid resource path: " + resource +
                            ". Path should match " + self.pathRegex)

        if resource[:1] == "/":
            resource = resource[1:]

        resourceArn = "arn:aws:execute-api:{}:{}:{}/{}/{}/{}".format(
            self.region, self.awsAccountId, self.restApiId, self.stage, verb,
            resource)

        if effect.lower() == "allow":
            self.allowMethods.append({
                "resourceArn": resourceArn,
                "conditions": conditions
            })
        elif effect.lower() == "deny":
            self.denyMethods.append({
                "resourceArn": resourceArn,
                "conditions": conditions
            })

    def _getEmptyStatement(self, effect):
        """Returns an empty statement object prepopulated with the correct action and the
        desired effect."""
        statement = {
            "Action": "execute-api:Invoke",
            "Effect": effect[:1].upper() + effect[1:].lower(),
            "Resource": [],
        }

        return statement

    def _getStatementForEffect(self, effect, methods):
        """This function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy."""
        statements = []

        if len(methods) > 0:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if curMethod["conditions"] is None or len(
                        curMethod["conditions"]) == 0:
                    statement["Resource"].append(curMethod["resourceArn"])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement["Resource"].append(
                        curMethod["resourceArn"])
                    conditionalStatement["Condition"] = curMethod["conditions"]
                    statements.append(conditionalStatement)

            if statement["Resource"]:
                statements.append(statement)

        return statements

    def allowAllMethods(self):
        """Adds a '*' allow to the policy to authorize access to all methods of an API"""
        self._addMethod("Allow", HttpVerb.ALL, "*", [])

    def denyAllMethods(self):
        """Adds a '*' allow to the policy to deny access to all methods of an API"""
        self._addMethod("Deny", HttpVerb.ALL, "*", [])

    def allowMethod(self, verb, resource):
        """Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy"""
        self._addMethod("Allow", verb, resource, [])

    def denyMethod(self, verb, resource):
        """Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy"""
        self._addMethod("Deny", verb, resource, [])

    def allowMethodWithConditions(self, verb, resource, conditions):
        """Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
        """
        self._addMethod("Allow", verb, resource, conditions)

    def denyMethodWithConditions(self, verb, resource, conditions):
        """Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
        """
        self._addMethod("Deny", verb, resource, conditions)

    def build(self):
        """Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy."""
        if (self.allowMethods is None or
                len(self.allowMethods) == 0) and (self.denyMethods is None or
                                                  len(self.denyMethods) == 0):
            raise NameError("No statements defined for the policy")

        policy = {
            "principalId": self.principalId,
            "policyDocument": {
                "Version": self.version,
                "Statement": []
            },
        }

        policy["policyDocument"]["Statement"].extend(
            self._getStatementForEffect("Allow", self.allowMethods))
        policy["policyDocument"]["Statement"].extend(
            self._getStatementForEffect("Deny", self.denyMethods))

        return policy
