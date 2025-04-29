# Author: Gary A. Stafford
# Modified: 2024-04-14
# AWS Code Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import datetime
import logging
import os
import streamlit as st
from PIL import Image
from argparse import ArgumentParser
from src.utils import sagemakerHelper, utils
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
assets_dir = "assets"
original_dir = f'{assets_dir}/stock_originals'
thumbs_dir = f'{assets_dir}/stock_thumbs'


def main(profile):
    """
    Entrypoint for Hugging face model prompt example.
    """

    # st.markdown(
    #     utils.custom_css,
    #     unsafe_allow_html=True,
    # )

    if "model_id" not in st.session_state:
        st.session_state["model_id"] = "Salesforce/blip2-flan-t5-xl"

    if "analysis_time" not in st.session_state:
        st.session_state["analysis_time"] = 0

    if "input_tokens" not in st.session_state:
        st.session_state["input_tokens"] = 0

    if "output_tokens" not in st.session_state:
        st.session_state["output_tokens"] = 0

    if "media_type" not in st.session_state:
        st.session_state["media_type"] = 'JPEG'

    if "max_tokens" not in st.session_state:
        st.session_state["max_tokens"] = 1000
    
    if "endpoint_name" not in st.session_state:
        st.session_state["endpoint_name"] = "blip2-flan-t5-xl-test"
        
    if "selected_image" not in st.session_state:
        st.session_state["selected_image"] = ""

    st.markdown("## Generative AI-powered Image Q&A")

    with st.form("ad_analyze_form", border=True, clear_on_submit=False):
        st.markdown(
            "Select the image and the Question you want to answer about the image. Generative AI image analysis powered by Amazon Sagemaker and Huggingface integration"
        )
        st.markdown(
            "Note: You need to create a Sagemaker IAM role deploy the needed model in Sagemaker before running this"
        )
        endpoint_name = "blip2-flan-t5-xl-test"
        endpoint = st.text_area(label="Sagemaker Endpoint:", value=endpoint_name)
        # img_prompt = utils.pickle_load("img_prompt.pkl")
        img_prompt = "what animals are in this picture"
        prompt = st.text_area(label="User Prompt:", value=img_prompt)
        # list the image thumbnails for user to pick as input
        # Display the selected image
        st.markdown(
            "Select Image from the list or upload (1) new image"
        )
        # Set the directory where your images are located
        # Get a list of all image files in the directory
        image_files = [f for f in os.listdir(thumbs_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        # print(image_files[0])
        # st.session_state.selected_image = ""
        # Create a grid layout with 3 columns
        cols = st.columns(3)

        # Loop through the image files and display them in the grid
        for i, image_file in enumerate(image_files):
            with cols[i % 3]:
                image_path = os.path.join(thumbs_dir, image_file)
                image = Image.open(image_path)
                st.image(image, caption=image_file, use_container_width=True)
                # Create a radio button for each image
                is_selected = st.form_submit_button(f"Select Image {i+1}")

                # Update the selected image in session state
                if is_selected:
                    st.session_state.selected_image = image_file
            # Add a new row of columns every 3 images
            if (i + 1) % 3 == 0:
                cols = st.columns(3)
            # return the path of selected image file

        original_file = st.session_state.selected_image.replace('thumbnail_','')
        st.session_state.selected_image_path = os.path.join(original_dir, original_file)

        logger.info(st.session_state.selected_image_path)

        if st.session_state.selected_image:
            selected_image = Image.open(st.session_state.selected_image_path)
            st.image(selected_image, caption='Selected Image', use_container_width=True)
        
        uploaded_files = st.file_uploader(
            "Upload JPG, PNG file:",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=False,
        )

        file_paths = []  # only used for images, else none
        if uploaded_files:
            logger.info("Uploaded file")
            logger.info(uploaded_files)
            for uploaded_file in uploaded_files:
                print(
                    uploaded_file.file_id,
                    uploaded_file.name,
                    uploaded_file.type,
                    uploaded_file.size,
                )
                st.session_state.media_type = uploaded_file.type.split("/")[1].upper()
                image = Image.open(uploaded_file)
                file_path = f"{assets_dir}/_temp_images/{uploaded_file.name}"
                image.save(file_path)
                file_paths.append(
                    {
                        "file_path": file_path,
                        "file_type": st.session_state.media_type,
                    }
                )
            logger.info(f"Prompt: {prompt}")
        # if image is chosen from list
        else:
            # get the file extension
            st.session_state.media_type = st.session_state.selected_image_path.split(".")[-1].upper()
            logger.info("Selected file")
            file_paths.append(
                {
                    "file_path": st.session_state.selected_image_path,
                    "file_type": st.session_state.media_type,
                }
            )
        
        submitted = st.form_submit_button("Submit")
        logger.info(file_paths)

        if submitted:
            st.markdown("---")
            if uploaded_files and file_paths:  # image media-type
                for file_path in file_paths:
                    st.image(file_path["file_path"], caption="", width=400)
            else:
                logger.info("No files uploaded, using selected image")
                for file_path in file_paths:
                    image = Image.open(file_path["file_path"])
                    st.image(image, caption="", width=400)

            with st.spinner(text="Analyzing..."):

                current_time1 = datetime.datetime.now()
                response = sagemakerHelper.run_inference(prompt, file_path["file_path"], profile, endpoint, file_path["file_type"])
                current_time2 = datetime.datetime.now()

                # Show analysis results
                st.text_area(
                    label="Analysis:",
                    value=response,
                    height=100,
                )
                # pickle results
                utils.pickle_dump(response, "img_tag.pkl")
                logger.info("Pickled response")

                # show latency
                st.session_state.analysis_time = (
                    current_time2 - current_time1
                ).total_seconds()

                st.markdown(
                    f"Analysis time: {st.session_state.analysis_time}",
                    unsafe_allow_html=True,
                )
    
    st.markdown(
        "<small style='color: #888888'> Gary A. Stafford, Ranjith Krishnamoorthy 2024</small>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Inference Parameters")
        st.session_state["model_id"] = "Salesforce/blip2-flan-t5-xl"

        st.session_state.model_id = st.selectbox(
            "model_id",
            options=[
                "Salesforce/blip2-flan-t5-xl",
            ],
        )

        st.markdown("---")

        st.text(
            f"""• model_id: {st.session_state.model_id}
⎯
• endpoint_name: {st.session_state.endpoint_name}
• uploaded_media_type: {st.session_state.media_type}
⎯
• analysis_time_sec: {st.session_state.analysis_time}
• input_tokens: {st.session_state.input_tokens}
• output_tokens: {st.session_state.output_tokens}
"""
        )

if __name__ == "__main__":
    parser = ArgumentParser(description='This app demonstrates image tagging using sagemaker deployed models')

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
