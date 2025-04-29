import base64
import json
import logging
import boto3
import streamlit as st
from botocore.exceptions import ClientError
from PIL import Image
import io
import math
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
assets_dir = "../../assets"

class ImageError(Exception):
    "Custom exception for errors returned by Foundation Model"
    def __init__(self, message):
        self.message = message

def get_supported_img_size(inp_width, aspect_ratio, model_id):
    stability_ratios = (1,1.28, 1.46,1.75,2.4)
    stability_sizes = (
        (1024, 1024),
        (512, 512),
        (1152, 896),
        (1216, 832),
        (1344, 768),
        (1536, 640)
    )
    titan_aspect_ratios = (1,0.666666666666667,1.5,0.6,1.666666666666667,0.777777777777778,
        1.28571428571429,0.545454545454545,1.83333333333333,0.454545454545455,2.2,1.8,1.8328125)
    titan_sizes = (
        (1024,1024),
        (768,768),
        (512,512),
        (768,1152),
        (384,576),
        (1152,768),
        (576,384),
        (768,1280),
        (384,640),
        (1280,768),
        (640,384),
        (896,1152),
        (448,576),
        (1152,896),
        (576,448),
        (768,1408),
        (384,704),
        (1408,768),
        (704,384),
        (640,1408),
        (320,704),
        (1408,640),
        (704,320),
        (1152,640),
        (1173,640),
    )
    if "amazon.titan" in model_id:
        aspect_ratios = titan_aspect_ratios
        sizes = titan_sizes
    else:
        aspect_ratios = stability_ratios
        sizes = stability_sizes
    # for the given aspect ratio find the closest aspect ratio aspect_ratios
    closest_aspect_ratio = min(aspect_ratios, key=lambda x: abs(x - aspect_ratio))
    closest_width= min(sizes, key=lambda x: abs(x[0] - inp_width))
    closest_height = closest_width[0]/closest_aspect_ratio
    logger.info(f"Closest Aspect Ratio: {closest_aspect_ratio}")
    logger.info(f"Closest Width: {closest_width}")
    # for the closest_aspect_ratio and input_width find the best tuple
    closest_match = min(sizes, key=lambda x: abs(x[0] - closest_width[0]) + abs(x[1] - closest_height))
    # return closest_match[0], closest_match[1]
    logger.info(f"Closest Supported image size WxH: {closest_match[0]} x {closest_match[1]}")
    return closest_match[0],closest_match[1]

def resize_image(image_file, task_type, model_id):
    # Open the image
    image = Image.open(image_file)

    # Get the pixel data
    pixels = image.load()

    # Get the original image size
    width, height = image.size

    # Calculate the new size while maintaining the aspect ratio
    aspect_ratio = width / height
    logger.info(f"Original image size WxH: {width} x {height}")
    logger.info(f"Aspect ratio: {aspect_ratio}")
    # round aspect ratio to to the closest int
    asr_int = round(aspect_ratio)
    logger.info(f"Aspect ratio rounded: {asr_int}")
    if asr_int > 1:
        # Max image size using image variation – 4,096 x 4,096 px
        # Max image size using in/outpainting, background removal, image conditioning, color palette – 1,408 x 1,408 px
        if task_type == "TEXT_IMAGE":
            if 'amazon.titan-image' in model_id:
                new_width = 1408 if width > 1408 else width
            else:
                new_width = 1024 if width > 1024 else width
        elif task_type == "IMAGE_VARIATION":
            new_width = 4096 if width > 4096 else width
        elif task_type in ["INPAINTING","OUTPAINTING","COLOR_GUIDED_GENERATION","BACKGROUND_REMOVAL"]:
            new_width = 1024 if width > 1024 else width
        else:
            new_width = width
        new_width, new_height= get_supported_img_size(width, aspect_ratio, model_id)
        # new_height = int(new_width / asr_int)
    else:
        if task_type == "TEXT_IMAGE":
            if 'amazon.titan-image' in model_id:
                new_height = 1408 if height > 1408 else width
            else:
                new_height = 1024 if height > 1024 else width
        elif task_type == "IMAGE_VARIATION":
            new_height = 4096 if height > 4096 else height
        elif task_type in ["INPAINTING","OUTPAINTING","COLOR_GUIDED_GENERATION","BACKGROUND_REMOVAL"]:
            new_height = 1024 if height > 1024 else height
        else:
            new_height = height
        # new_width = int(new_height / asr_int)
        new_width, new_height = get_supported_img_size(width, aspect_ratio, model_id)

    logger.info(f"New image size WxH: {new_width} x {new_height}")
    # Create a new image with the desired size
    new_image = Image.new("RGB", (new_width, new_height))

    # Iterate over the pixels and copy them to the new image
    for x in range(new_width):
        for y in range(new_height):
            # Get the pixel value from the original image
            pixel_value = pixels[int(x * width / new_width), int(y * height / new_height)]

            # Set the pixel value in the new image
            new_image.putpixel((x, y), pixel_value)

    # Create a BytesIO object
    byte_io = io.BytesIO()

    # Save the image to the BytesIO object
    new_image.save(byte_io, format="JPEG")

    # Get the base64 encoded data
    base64_data = base64.b64encode(byte_io.getvalue())

    # Decode the base64 data to a string
    base64_str = base64_data.decode("utf-8")
    return base64_str, new_width, new_height

def run_multi_modal_prompt(
    bedrock_runtime,
    model_id,
    messages,
    max_tokens = 4096,
    temperature = 0.5,
    top_p = .999,
    top_k = 250,
    seed = 45,
    cfg_scale = 10,
    steps = 30,
    num_images = 3,
    style_preset = "photographic",
    weight = 1.0,
    image_strength = 0.5,
    mask_prompt = "",
    negative_prompt = "",
    task_type = "",
    image_height = 1024,
    image_width = 1024
):
    """
    Invokes a model with a multimodal prompt.
    Args:
        bedrock_runtime: The Amazon Bedrock boto3 client.
        model_id (str): The model ID to use.
        messages (JSON) : The messages to send to the model.
        max_tokens (int) : The maximum  number of tokens to generate.
        temperature (float): The amount of randomness injected into the response.
        top_p (float): Use nucleus sampling.
        top_k (int): Only sample from the top K options for each subsequent token.
    Returns:
        response_body (string): Response from foundation model.
    """
    prompt_data = messages[0]["content"][0]["text"]
    init_image = messages[0]["content"][1]["source"]["data"] if len(messages[0]["content"]) > 1 else None
    
    if 'stability' in model_id:
        if 'sd3' in model_id:
            if task_type == "IMAGE_VARIATION":
                logger.info("Image to Image")
                body = json.dumps(
                {
                    "mode":"image-to-image",
                    "prompt":prompt_data,
                    "negative_prompt":negative_prompt,
                    "seed":seed,
                    "output_format": "jpeg",
                    "image": init_image,
                    "strength": image_strength
                }
            )

            else:
                logger.info("Text to Image")
                body = json.dumps(
                {
                    "aspect_ratio":"1:1",
                    "mode":"text-to-image",
                    "prompt":prompt_data,
                    "negative_prompt":negative_prompt,
                    "seed":seed,
                    "output_format": "jpeg"
                }
            )
        else:
            body = json.dumps(
                {
                    "text_prompts":[{"text":prompt_data, "weight": weight}],
                    "cfg_scale":cfg_scale,
                    "steps":steps,
                    "seed":seed,
                    "style_preset":style_preset,
                    "init_image": init_image,
                    "image_strength": image_strength
                }
            )
    elif "amazon.titan-image" in model_id:
        logger.info("Titan Image generation")
        logger.info("Mask provided") if len(mask_prompt) > 2 else logger.info("Mask not provided")
        logger.info("Negative prompt provided") if len(negative_prompt) > 2 else logger.info("Negative prompt not provided")
        logger.info(f"Image height, Image width:{image_height}, {image_width}")
        image_gen_config =  {
            "numberOfImages": num_images,
            # TODO - make inputs
            "height": image_height,
            "width": image_width,
            "cfgScale": cfg_scale,
            "seed": seed
        }
        # TODO add conditioning
        if task_type == "TEXT_IMAGE":
            logger.info("Text to Image")
            body = json.dumps({
                "taskType": task_type,
                "textToImageParams": {
                    "text": prompt_data,
                    "negativeText": negative_prompt
                },
                "imageGenerationConfig": image_gen_config
            })
        elif task_type == "INPAINTING":
            logger.info("Inpainting")
            
            body = json.dumps({
                "taskType": task_type,
                "inPaintingParams": {
                    "image": init_image,
                    "text": prompt_data,
                    "maskPrompt": mask_prompt,
                    "negativeText": negative_prompt,
                    # TODO generate mask image in UI
                    # "maskImage": init_image
                },
                "imageGenerationConfig": image_gen_config            
            })
        elif task_type == "OUTPAINTING":
            logger.info("Outpainting")
            body = json.dumps({
                "taskType": task_type,
                "outPaintingParams": {
                    "image": init_image,
                    "text": prompt_data,
                    "maskPrompt": mask_prompt,
                    "negativeText": negative_prompt,
                    # TODO generate mask image in UI
                    # "maskImage": init_image,
                    "outPaintingMode": "DEFAULT"
                },
                "imageGenerationConfig": image_gen_config            
            })
        if task_type == "IMAGE_VARIATION":
            logger.info("Image Variation")
            body = json.dumps({
                "taskType": task_type,
                "imageVariationParams": {
                    "text": prompt_data,
                    "negativeText": negative_prompt,
                    # TODO multiple images
                    "images": [init_image],
                    # TODO input
                    "similarityStrength": 0.7
                },
                "imageGenerationConfig": image_gen_config,
            })
        if task_type == "COLOR_GUIDED_GENERATION":
            logger.info("Color Guided Generation")
            body = json.dumps({
                "taskType": task_type,
                "imageVariationParams": {
                    "text": prompt_data,
                    "negativeText": negative_prompt,
                    "referenceImage": init_image,
                    # TODO add color pick
                    "colors": ["#FF0000", "#00FF00", "#0000FF"]
                },
                "imageGenerationConfig": image_gen_config
            })
        if task_type == "BACKGROUND_REMOVAL":
            logger.info("Background Removal")
            body = json.dumps({
                "taskType": task_type,
                "backgroundRemovalParams": {
                    "image": init_image,
                }
            })
    else:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            }
        )
    
    logger.info("Sending request to bedrock")

    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    
    response_body = json.loads(response.get("body").read())
    logger.info("Returning bedock response")
    return response_body

def build_request(prompt, file_paths, profile="default", mask_prompt = "", negative_prompt = "", task_type = "", image_height=1024, image_width=1024):
    """
    Entrypoint for Anthropic Claude multimodal prompt example.
    Args:
        prompt (str): The prompt to use.
        image (str): The image to use.
    Returns:
        response_body (string): Response from foundation model.
    """

    try:
        session = boto3.Session(profile_name=profile)
        bedrock_runtime = session.client(service_name="bedrock-runtime")

        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        }

        if file_paths is not None:  # must be image(s)
            for file_path in file_paths:  # append each to message
                with open(file_path["file_path"], "rb") as image_file:
                    # content_image = base64.b64encode(image_file.read()).decode("utf8")
                    resized_image,image_width,image_height = resize_image(image_file, task_type, st.session_state.model_id)
                    logger.info(f"Image height, Image width:{image_height}, {image_width}")

                    message["content"].append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": file_path["file_type"],
                                "data": resized_image,
                            },
                        }
                    )

            messages = [message]

        response = run_multi_modal_prompt(
            bedrock_runtime,
            st.session_state.model_id,
            messages,
            st.session_state.max_tokens,
            st.session_state.temperature,
            st.session_state.top_p,
            st.session_state.top_k,
            st.session_state.seed,
            st.session_state.cfg_scale,
            st.session_state.steps,
            st.session_state.num_images,
            st.session_state.style_preset,
            st.session_state.weight,
            st.session_state.image_strength,
            mask_prompt=mask_prompt,
            negative_prompt=negative_prompt,
            task_type=task_type,
            image_height=image_height,
            image_width=image_width,
        )

        # logger.info(json.dumps(response, indent=4))

        return response
    except ClientError as err:
        message = err.response.get("Error").get("Message")
        logger.error("A client error occurred: %s", message)
        raise ImageError(message)