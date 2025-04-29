import sagemaker
import boto3
from PIL import Image
import base64
import io
from sagemaker.huggingface import HuggingFaceModel
import logging
import json
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
assets_dir = "../../assets"
original_dir = '../../assets/stock_originals'

class ImageError(Exception):
    "Custom exception for errors returned by Foundation Model"
    def __init__(self, message):
        self.message = message

def deploy_hf_model(boto_session, hub_env, instance_type, role_name):
    # boto_session = boto3.Session(profile_name=profile_name)
    sagemaker_session = sagemaker.Session(boto_session=boto_session)
    transformers_version='4.37.0'
    pytorch_version='2.1.0'
    py_version='py310'

    try:
        role = sagemaker.get_execution_role()
    except ValueError:
        iam = boto_session.client('iam')
        # role = iam.get_role(RoleName='sagemaker_execution_role')['Role']['Arn']
        role = iam.get_role(RoleName=role_name)['Role']['Arn']
        print(role)

    # Hub Model configuration. https://huggingface.co/models
    # hub = {
    #     'HF_MODEL_ID':'Salesforce/blip2-flan-t5-xl',
    #     'HF_TASK':'image-to-text'
    # }
    hub = hub_env

    # create Hugging Face Model Class
    huggingface_model = HuggingFaceModel(
        transformers_version=transformers_version,
        pytorch_version=pytorch_version,
        py_version=py_version,
        env=hub,
        role=role,
        sagemaker_session=sagemaker_session
    )

    # deploy model to SageMaker Inference
    predictor = huggingface_model.deploy(
        initial_instance_count=1, # number of instances
        # instance_type='ml.g5.2xlarge' # ec2 instance type
        instance_type=instance_type # ec2 instance type
    )
    return predictor.endpoint_name

def run_inference(prompt, image_path, profile_name, endpoint_name, image_format = 'JPEG'):
    # setup clients
    # Create a SageMaker runtime client
    boto_session = boto3.Session(profile_name=profile_name)
    runtime = boto_session.client('sagemaker-runtime')
    
    # Open the image
    # image = Image.open(f"{original_dir}/AdobeStock_185274335.jpeg")
    image = Image.open(image_path)
    # rimage = image.resize((400, 300))
    # Convert the image to a base64 string
    buffered = io.BytesIO()
    # rimage.save(buffered, format="JPEG")
    image.save(buffered, format=image_format)
    byte_array = buffered.getvalue()
    img_str = base64.b64encode(byte_array).decode("utf-8")
    prompt = f"""Question: {prompt}? Answer:"""
    # inputs = {"inputs": {"image":img_str, "prompt":prompt}}
    inputs = {"inputs": img_str, "parameters": {"prompt":prompt}}
    # print(json.dumps(inputs, indent=2))
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            # EndpointName="blip-2-test",
            ContentType="application/json",
            # Body=bytearray(json.dumps({"inputs": img_str, "text":prompt}), "utf-8"),
            Body=bytearray(json.dumps(inputs), "utf-8")
        )
            # Decode the response
        result = json.loads(response["Body"].read().decode("utf-8"))
        # Print the generated caption
        return(result[0]["generated_text"])
    except Exception as e:
        raise ImageError(e)

