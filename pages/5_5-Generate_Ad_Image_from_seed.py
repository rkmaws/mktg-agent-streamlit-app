# Author: Gary A. Stafford, Ranjith Krishnamoorthy
# Modified: 2025-05-01
# AWS Code Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import datetime
import logging
from io import StringIO, BytesIO
import os
import fitz
import streamlit as st
from PIL import Image
from tempfile import NamedTemporaryFile
from argparse import ArgumentParser
from src.utils import bedrockHelper, utils
import base64
import json
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
assets_dir = "assets"
original_dir = f'{assets_dir}/stock_originals'
thumbs_dir = f'{assets_dir}/stock_thumbs'


def main(profile):
    """
    Entrypoint for Anthropic Claude multimodal prompt example.
    """

    # st.markdown(
    #     utils.custom_css,
    #     unsafe_allow_html=True,
    # )

    if "model_id" not in st.session_state:
        st.session_state["model_id"] = "stability.sd3-large-v1:0"

    if "analysis_time" not in st.session_state:
        st.session_state["analysis_time"] = 0

    if "input_tokens" not in st.session_state:
        st.session_state["input_tokens"] = 0

    if "output_tokens" not in st.session_state:
        st.session_state["output_tokens"] = 0

    if "style_preset" not in st.session_state:
        st.session_state["style_preset"] = "photographic"

    if "seed" not in st.session_state:
        st.session_state["seed"] = 42

    if "num_images" not in st.session_state:
        st.session_state["num_images"] = 3

    if "cfg_scale" not in st.session_state:
        st.session_state["cfg_scale"] = 10

    if "steps" not in st.session_state:
        st.session_state["steps"] = 30

    if "media_type" not in st.session_state:
        st.session_state["media_type"] = 'image/jpeg'

    if "max_tokens" not in st.session_state:
        st.session_state["max_tokens"] = 1000

    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 1.0

    if "top_p" not in st.session_state:
        st.session_state["top_p"] = 0.999

    if "top_k" not in st.session_state:
        st.session_state["top_k"] = 268

    if "weight" not in st.session_state:
        st.session_state["weight"] = 1

    if "image_strength" not in st.session_state:
        st.session_state["image_strength"] = 1
    
    if "task_type" not in st.session_state:
        st.session_state["task_type"] = "TEXT_IMAGE"

    if "file_paths" not in st.session_state:
        st.session_state["file_paths"] = []

    st.markdown("## Generative AI-powered Image Generation")

    with st.form("ad_analyze_form", border=True, clear_on_submit=False):
        st.markdown(
            "Describe the image you want to generate. Generative AI image generation powered by Amazon Bedrock and Stable Diffusion 1 XL and Amazon Titan G1 V2 foundation models."
        )
        # main prompt
        # img_prompt = json.loads(utils.pickle_load("img_prompt.pkl"))
        img_prompt = json.loads(utils.pickle_load("img_analysis.pkl"))
        prompt = st.text_area(label="Image Prompt:", value=img_prompt["prompt"])
        # Masking prompt
        msk_prompt = img_prompt["mask_prompt"]
        mask_prompt = st.text_area(label="Mask Prompt:", value=msk_prompt)
        # Neg prompt
        neg_prompt = img_prompt["negative_prompt"]
        negative_prompt = st.text_area(label="Negative Prompt:", value=neg_prompt)
        # list the image thumbnails for user to pick as input
        # Display the selected image
        st.markdown(
            "Select Image from the list or upload new image"
        )
        # Set the directory where your images are located
        # Get a list of all image files in the directory
        image_files = [f for f in os.listdir(thumbs_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        # print(image_files[0])
        # Create a grid layout with 3 columns
        cols = st.columns(3)

        # Loop through the image files and display them in the grid
        for i, image_file in enumerate(image_files):
            with cols[i % 3]:
                image_path = os.path.join(thumbs_dir, image_file)
                image = Image.open(image_path)
                st.image(image, caption=image_file, use_container_width=True)
            # Add a new row of columns every 3 images
            if (i + 1) % 3 == 0:
                cols = st.columns(3)
        selected_thumb = st.selectbox("Select Image", image_files)

        if selected_thumb:
            original_file = selected_thumb.replace('thumbnail_','')
            selected_image_path = os.path.join(original_dir, original_file)
            logger.info(selected_image_path)
            selected_image = Image.open(selected_image_path)
            st.image(selected_image, caption='Selected Image', use_container_width=True)
            file_paths= [
                {
                    "file_path": selected_image_path,
                    "file_type": 'image/jpeg',
                }
            ]
        
        uploaded_files = st.file_uploader(
            "Upload JPG, PNG, GIF, WEBP, PDF, CSV, or TXT files:",
            type=["jpg", "png", "webp", "pdf", "gif", "csv", "txt"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            logger.info("Uploaded files")
            logger.info(uploaded_files)
            for uploaded_file in uploaded_files:
                print(
                    uploaded_file.file_id,
                    uploaded_file.name,
                    uploaded_file.type,
                    uploaded_file.size,
                )
                st.session_state.media_type = uploaded_file.type
                if uploaded_file.type in [
                    "text/csv",
                    "text/plain",
                ]:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    prompt = f"{prompt}\n\n{stringio.getvalue()}"
                elif uploaded_file.type == "application/pdf":
                    with NamedTemporaryFile(suffix="pdf") as temp:
                        temp.write(uploaded_file.getvalue())
                        temp.seek(0)
                        doc = fitz.open(temp.name)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        prompt = f"{prompt}\n\n{text}"
                else:  # image media-type
                    image = Image.open(uploaded_file)
                    file_path = f"{assets_dir}/_temp_images/{uploaded_file.name}"
                    image.save(file_path)
                    file_paths.append(
                        {
                            "file_path": file_path,
                            "file_type": uploaded_file.type,
                        }
                    )

            logger.info(f"Prompt: {prompt}")
        
        submitted = st.form_submit_button("Submit")

        if submitted:
            st.markdown("---")
            if uploaded_files and uploaded_files[0].type in ["text/csv","text/plain"]:
                st.markdown(
                    f"Sample of file contents:\n\n{stringio.getvalue()[0:680]}..."
                )
            elif uploaded_files and uploaded_files[0].type == "application/pdf":
                st.markdown(f"Sample of file contents:\n\n{text[0:680]}...")
            elif uploaded_files and file_paths:  # image media-type
                for file_path in file_paths:
                    st.image(file_path["file_path"], caption="", width=400)
            else:
                logger.info("No files uploaded, using selected image")
                for file_path in file_paths:
                    logger.info(file_path["file_path"])
                    image = Image.open(file_path["file_path"])
                #     st.image(image, caption="", width=400)

            with st.spinner(text="Analyzing..."):
                current_time1 = datetime.datetime.now()
                response, error = bedrockHelper.build_request(prompt, file_paths, profile,  mask_prompt, negative_prompt, st.session_state.task_type)
                current_time2 = datetime.datetime.now()
                if response:
                    # Extract the image data
                    if "stability" in st.session_state["model_id"]:
                        image_path = os.path.join(f"{assets_dir}/generated_images/", "generated_image_frm_seed.png")
                        if "sd3" in st.session_state["model_id"]:
                            base64_output_image = response["images"][0]
                            image_data = base64.b64decode(base64_output_image)
                            image = Image.open(BytesIO(image_data))
                            image.save(image_path)
                            finish_reason = response.get("finish_reasons")[0]
                            print(finish_reason)
                            if finish_reason:
                                raise bedrockHelper.ImageError(f"Image generation error. Error code is {finish_reason}")
                        else:
                            base64_image = response.get("artifacts")[0].get("base64")
                            base64_bytes = base64_image.encode('ascii')
                            image_bytes = base64.b64decode(base64_bytes)
                            finish_reason = response.get("artifacts")[0].get("finishReason")
                            # Save the generated image to a local file
                            with open(image_path, "wb") as file:
                                file.write(image_bytes)
                            if finish_reason == 'ERROR' or finish_reason == 'CONTENT_FILTERED':
                                raise bedrockHelper.ImageError(f"Image generation error. Error code is {finish_reason}")

                        # Display the generated image in Streamlit
                        st.image(image_path)

                    else:
                        images = response.get("images")
                        for i, item in enumerate(images):
                            base64_bytes = item.encode('ascii')
                            image_bytes = base64.b64decode(base64_bytes)

                            # Save the generated image to a local file
                            image_path = os.path.join(f"{assets_dir}/generated_images/", f"generated_image_frm_seed{i}.png")
                            with open(image_path, "wb") as file:
                                file.write(image_bytes)

                            # Display the generated image in Streamlit
                            st.image(image_path)

                            finish_reason = response.get("error")
                            if finish_reason is not None:
                                raise bedrockHelper.ImageError(f"Image generation error. Error code is {finish_reason}")
                    
                    st.session_state.analysis_time = (
                        current_time2 - current_time1
                    ).total_seconds()

                    st.markdown(
                        f"Analysis time: {current_time2 - current_time1}",
                        unsafe_allow_html=True,
                    )
                    # st.session_state.input_tokens = response["usage"]["input_tokens"]
                    # st.session_state.output_tokens = response["usage"]["output_tokens"]
                else:
                    st.error(error)

    with st.sidebar:
        st.markdown("### Inference Parameters")
        st.session_state["model_id"] = "stability.sd3-large-v1:0"

        st.session_state.model_id = st.selectbox(
            "model_id",
            options=bedrockHelper.get_filtered_models(profile, input_mode='TEXT', output_mode='IMAGE'),
        )
        st.session_state.task_type = st.selectbox(
            "task_type",
            options=[
                "TEXT_IMAGE",
                "INPAINTING",
                "OUTPAINTING",
                "IMAGE_VARIATION",
                "COLOR_GUIDED_GENERATION",
                "BACKGROUND_REMOVAL",
            ],
        )

        st.session_state.style_preset = st.selectbox(
            "style_preset", 
            options=[
                "3d-model" , 
                "analog-film" , 
                "anime" , 
                "cinematic" , 
                "comic-book" , 
                "digital-art" , 
                "enhance" , 
                "fantasy-art" , 
                "isometric" , 
                "line-art" , 
                "low-poly" , 
                "modeling-compound" , 
                "neon-punk" , 
                "origami" , 
                "photographic" , 
                "pixel-art" , 
                "tile-texture"
            ], index=14
        )

        st.session_state.weight = st.slider(
            "weight", min_value=0.0, max_value=1.0, value=1.0, step=0.1
        )

        st.session_state.image_strength = st.slider(
            "image_strength", min_value=0.0, max_value=1.0, value=0.5, step=0.1
        )

        st.session_state.seed = st.slider(
            "seed", min_value=0, max_value=680, value=0, step=5
        )

        st.session_state.cfg_scale = st.slider(
            "cfg_scale", min_value=0, max_value=30, value=7, step=1
        )

        st.session_state.steps = st.slider(
            "steps", min_value=10, max_value=68, value=30, step=5
        )

        st.session_state.num_images = st.slider(
            "num_images", min_value=1, max_value=4, value=3, step=1
        )

        st.markdown("---")

        st.text(f"""• model_id: {st.session_state.model_id}

• style_preset: {st.session_state.style_preset}
(Optional) A style preset that guides the image model towards 
a particular style.

• weight: {st.session_state.weight}
(Optional) The weight that the model should apply to the prompt. 
A value that is less than zero declares a negative prompt. 
Use a negative prompt to tell the model to avoid certain concepts. 
The default value for weight is one.

• image_strength: {st.session_state.image_strength}
(Optional) Determines how much influence the source image in init_image 
has on the diffusion process. Values close to 1 yield images very similar 
to the source image. Values close to 0 yield images very different than the
 source image.

• seed: {st.session_state.seed}
(Optional) The seed determines the initial noise setting. 
Use the same seed and the same settings as a previous run to allow 
inference to create a similar image. If you don't set this value, 
or the value is 0, it is set as a random number.

• cfg_scale: {st.session_state.cfg_scale}
(Optional) Determines how much the final image portrays the prompt. 
Use a lower number to increase randomness in the generation.

• steps: {st.session_state.steps}
(Optional) Generation step determines how many times the image is sampled.
 More steps can result in a more accurate result.
• num_images: {st.session_state.num_images}
⎯
• uploaded_media_type: {st.session_state.media_type}
⎯
• analysis_time_sec: {st.session_state.analysis_time}
• input_tokens: {st.session_state.input_tokens}
• output_tokens: {st.session_state.output_tokens}
""")

if __name__ == "__main__":
    parser = ArgumentParser(description='This app demonstrates creative brief analysis using bedrock')

    parser.add_argument('--profile', default="default",
                        help="Pass the aws cli profile name for connecting to bedrock service on your aws account")
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # This exception will be raised if --help or invalid command line arguments
        # are used. Currently streamlit prevents the program from exiting normally
        # so we have to do a hard exit.
        os._exit(e.code)
    logger.info(f"profile: {args.profile}")
    main(args.profile)
