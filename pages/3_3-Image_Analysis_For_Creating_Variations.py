# Author: Gary A. Stafford, Ranjith Krishnamoorthy
# Modified: 2025-05-01
# AWS Code Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import datetime
import logging
from io import StringIO
import os
import fitz
import streamlit as st
from PIL import Image
from tempfile import NamedTemporaryFile
from argparse import ArgumentParser
from src.utils import bedrockHelper, utils
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
        st.session_state["model_id"] = "anthropic.claude-3-sonnet-20240229-v1:0"

    if "analysis_time" not in st.session_state:
        st.session_state["analysis_time"] = 0

    if "input_tokens" not in st.session_state:
        st.session_state["input_tokens"] = 0

    if "output_tokens" not in st.session_state:
        st.session_state["output_tokens"] = 0

    if "max_tokens" not in st.session_state:
        st.session_state["max_tokens"] = 1000

    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 1.0

    if "top_p" not in st.session_state:
        st.session_state["top_p"] = 0.999

    if "top_k" not in st.session_state:
        st.session_state["top_k"] = 268

    if "media_type" not in st.session_state:
        st.session_state["media_type"] = None

    if "seed" not in st.session_state:
        st.session_state["seed"] = 45
    
    if "cfg_scale" not in st.session_state:
        st.session_state["cfg_scale"] = 10

    if "steps" not in st.session_state:
        st.session_state["steps"] = 30
    
    if "media_type" not in st.session_state:
        st.session_state["media_type"] = "image/png"

    if "num_images" not in st.session_state:
        st.session_state["num_images"] = 3
    
    if "style_preset" not in st.session_state:
        st.session_state["style_preset"] = "photographic"
    
    if "weight" not in st.session_state:
        st.session_state["weight"] = 1

    if "image_strength" not in st.session_state:
        st.session_state["image_strength"] = 1

    st.header("AWS Agentic AI Demo powered by Amazon Bedrock Agents", divider="rainbow")

    with st.form("ad_analyze_form", border=True, clear_on_submit=False):
        st.markdown(
            """Describe the analysis task you wish to perform and optionally upload the content to be analyzed. 
Generative AI analysis powered by Amazon Bedrock and Anthropic Claude 3 family of foundation models."""
        )
        default_prompt = '''You are a Creative Director for a leading advertising agency.
Analyze the attached image and identify the key attributes that can be used for marketing campaign.
Include pet breed and color and their positioning in pet_description
In prompt add the details of imagery that matches the campaign theme
In mask_prompt include the pet description and additional details
The ad copy should be 20 words or less.
campaign theme: christmas holiday
Format the response as a series of JSON objects according to the template below.
{
    "name": "",
    "short_description": "",
    "identified_pets": "",
    "pet_description": "",
    "background_setting": ""
    "suggested_ad_copy": "",
    "call_to_action": ""
    "additional_details": "",
    "prompt: "",
    "mask_prompt": "",
    "negative_prompt": ""
}
Important: if no image is provided, do not produce the analysis.'''
        prompt = st.text_area(label="User Prompt:", value=default_prompt, height=268)

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

        # file_paths = []  # only used for images, else none

        if uploaded_files is not None:
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

            print(f"Prompt: {prompt}")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.markdown("---")
            if uploaded_files and uploaded_files[0].type in [
                "text/csv",
                "text/plain",
            ]:
                st.markdown(
                    f"Sample of file contents:\n\n{stringio.getvalue()[0:680]}..."
                )
            elif uploaded_files and uploaded_files[0].type == "application/pdf":
                st.markdown(f"Sample of file contents:\n\n{text[0:680]}...")
            elif uploaded_files and file_paths:  # image media-type
                for file_path in file_paths:
                    st.image(file_path["file_path"], caption="", width=400)

            with st.spinner(text="Analyzing..."):
                current_time1 = datetime.datetime.now()
                response, error = bedrockHelper.build_request(prompt, file_paths, profile)
                current_time2 = datetime.datetime.now()
                if response:
                    st.text_area(
                        label="Analysis:",
                        value=response["content"][0]["text"],
                        height=800,
                    )
                    img_analysis = response["content"][0]["text"]
                    # if first charecter of response is not { find its first occurance and return 
                    # rest of the string
                    logger.info(img_analysis[0])
                    if img_analysis[0].find("{") > 0:
                        if img_analysis[0] != "{":
                            img_analysis = json.loads(img_analysis[img_analysis.find("{") :])
                        else:
                            img_analysis = json.loads(img_analysis)
                        logger.info("Extraced json")
                    # logger.info(img_analysis)
                    utils.pickle_dump(img_analysis, "img_analysis.pkl")
                    logger.info("Pickled json")
                    st.session_state.analysis_time = (
                        current_time2 - current_time1
                    ).total_seconds()

                    # st.markdown(
                    #     f"Analysis time: {current_time2 - current_time1}",
                    #     unsafe_allow_html=True,
                    # )
                    st.session_state.input_tokens = response["usage"]["input_tokens"]
                    st.session_state.output_tokens = response["usage"]["output_tokens"]
                else:
                    st.error(error)

    with st.sidebar:
        st.markdown("### Inference Parameters")
        st.session_state["model_id"] = "anthropic.claude-3-sonnet-20240229-v1:0"

        st.session_state.model_id = st.selectbox(
            "model_id",
            options=bedrockHelper.get_filtered_models(profile, input_mode='IMAGE', output_mode='TEXT'),
        )

        st.session_state.max_tokens = st.slider(
            "max_tokens", min_value=0, max_value=6800, value=2000, step=10
        )

        st.session_state.temperature = st.slider(
            "temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.01
        )

        st.session_state.top_p = st.slider(
            "top_p", min_value=0.0, max_value=1.0, value=0.999, step=0.001
        )

        st.session_state.top_k = st.slider(
            "top_k", min_value=0, max_value=680, value=268, step=1
        )

        st.markdown("---")

        st.text(
            f"""• model_id: {st.session_state.model_id}
• max_tokens: {st.session_state.max_tokens}
• temperature: {st.session_state.temperature}
• top_p: {st.session_state.top_p}
• top_k: {st.session_state.top_k}
⎯
• uploaded_media_type: {st.session_state.media_type}
⎯
• analysis_time_sec: {st.session_state.analysis_time}
• input_tokens: {st.session_state.input_tokens}
• output_tokens: {st.session_state.output_tokens}
"""
        )

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
