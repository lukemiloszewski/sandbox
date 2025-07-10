from boto3 import session

session = session.Session()
client = session.client(
    's3',
    region_name='lon1',
    endpoint_url='https://lukemiloszewski.lon1.digitaloceanspaces.com',
    aws_access_key_id=ACCESS_ID,
    aws_secret_access_key=SECRET_KEY
)

client.upload_file('hello.html', 'lukemiloszewski', ...)
