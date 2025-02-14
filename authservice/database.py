import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")

dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

users_table_name = "Users"
users_table = dynamodb.Table(users_table_name)

def create_users_table():
    try:
        existing_tables = [table.name for table in dynamodb.tables.all()]
        if users_table_name not in existing_tables:
            table = dynamodb.create_table(
                TableName=users_table_name,
                KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST"
            )
            print(f"Tablica '{users_table_name}' kreirana. Čekanje na aktivaciju...")
            table.wait_until_exists()
            print(f"Tablica '{users_table_name}' sada je spremna za korištenje.")
        else:
            print(f"Tablica '{users_table_name}' već postoji.")
    except ClientError as e:
        print(f"Greška pri kreiranju tablice: {e}")

if __name__ == "__main__":
    create_users_table()
