import boto3
from jose import jwk, jwt
from jose.utils import base64url_decode
import requests
import json
import os
import time
from urllib.parse import urlencode
import base64
from streamlit_cognito_auth import CognitoAuthenticator
import logging
logger = logging.getLogger(__name__)
    
class CognitoAuth:
    def __init__(self):
        # Determine if running locally
        self.is_local = os.environ.get('STREAMLIT_ENV') == 'local'
        self._load_config()
        self.jwks = self._get_jwks()
        

    def _load_config(self):
        """Load configuration from AWS Secrets Manager"""
        secret_name = os.environ.get('COGNITO_SECRET_NAME')
        profile_name = os.getenv('AWS_PROFILE', None)
        session = boto3.Session(profile_name=profile_name)
        client = session.client(
            service_name='secretsmanager'
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except Exception as e:
            raise Exception(f"Failed to load Cognito configuration: {str(e)}")

        secret = json.loads(get_secret_value_response['SecretString'])
        
        self.user_pool_id = secret['user_pool_id']
        self.client_id = secret['client_id']
        self.client_secret = secret['client_secret']
        self.domain = secret['domain']
        self.region = secret['region']
        if self.is_local:
            self.app_url = 'http://localhost:8501'
        else:
            self.app_url = secret['app_url']

    def _get_jwks(self):
        jwks_url = f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
        response = requests.get(jwks_url)
        return response.json()

    def get_login_url(self, redirect_uri=None):
        """Generate Cognito login URL"""
        if redirect_uri is None:
            redirect_uri = self.app_url
        
        base_url = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/login"
        params = {
            "client_id": self.client_id,
            "response_type": "code", 
            "scope": "openid email profile",
            "redirect_uri": redirect_uri
        }
        # Create URL with HTML anchor tag to make it clickable
        return f"{base_url}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code, redirect_uri=None):
        """Exchange authorization code for tokens"""
        if redirect_uri is None:
            # Use the app_url from configuration
            redirect_uri = self.app_url

        token_endpoint = f"https://{self.domain}.auth.{self.region}.amazoncognito.com/oauth2/token"
        
        # Create the authorization header
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode('utf-8')
        ).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': redirect_uri
        }
        logger.info(f"Token exchange request to: {token_endpoint}")  # Debug
        logger.info(f"With redirect URI: {redirect_uri}")  # Debug

        response = requests.post(token_endpoint, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Token exchange failed with status {response.status_code}")  # Debug
            logger.error(f"Response: {response.text}")  # Debug
            raise Exception(f"Token exchange failed: {response.text}")
        
    def verify_token(self, token):
        # Get the kid from the headers prior to verification
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        
        # Search for the kid in the downloaded public keys
        key_index = -1
        for i in range(len(self.jwks['keys'])):
            if kid == self.jwks['keys'][i]['kid']:
                key_index = i
                break
        if key_index == -1:
            raise Exception('Public key not found in jwks.json')
        
        # Construct the public key
        public_key = self.jwks['keys'][key_index]
        
        # Get the last two sections of the token,
        # message and signature (encoded in base64)
        message, encoded_signature = str(token).rsplit('.', 1)
        
        # Decode the signature
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        
        # Verify the signature
        try:
            verified = jwk.construct(public_key).verify(
                message.encode('utf8'),
                decoded_signature
            )
        except Exception as e:
            verified = False
            
        if not verified:
            raise Exception('Signature verification failed')

        # Since we passed the verification, we can now safely
        # use the unverified claims
        claims = jwt.get_unverified_claims(token)
        
        # Verify the token expiration
        if time.time() > claims['exp']:
            raise Exception('Token has expired')
            
        # Verify audience (use claims['client_id'] if verifying access token)
        if claims['aud'] != self.client_id:
            raise Exception('Token was not issued for this audience')

        return claims

    def get_authenticator(self):
        """
        returns a CognitoAuthenticator object.
        """

        # Initialise CognitoAuthenticator
        authenticator = CognitoAuthenticator(
            pool_id=self.user_pool_id,
            app_client_id=self.client_id,
            app_client_secret=self.client_secret,
        )

        return authenticator