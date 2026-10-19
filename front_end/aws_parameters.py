
import os
import boto3
from functools import lru_cache

@lru_cache(maxsize=None)
def get_parameter(name):
    arn = os.environ[name]
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=arn, WithDecryption=True)
    return response["Parameter"]["Value"]
