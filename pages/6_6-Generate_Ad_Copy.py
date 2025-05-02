# Author: Gary A. Stafford, Ranjith Krishnamoorthy
# Modified: 2025-05-01
# AWS Code Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import datetime
import logging
import os
import streamlit as st
from argparse import ArgumentParser
from src.utils import utils, generateAd
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
        st.session_state["model_id"] = "stability.stable-diffusion-xl-v1"

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

    if "top_p" not in st.session_state:
        st.session_state["top_p"] = 0.999

    if "cfg_scale" not in st.session_state:
        st.session_state["cfg_scale"] = 10

    if "steps" not in st.session_state:
        st.session_state["steps"] = 30
    
    if "media_type" not in st.session_state:
        st.session_state["media_type"] = "image/png"

    st.markdown("## Generative AI-powered Image Generation")

    with st.form("ad_analyze_form", border=True, clear_on_submit=False):
        st.markdown(
            "This step uses a python program to process the below image to generate a digital ad copy"
        )
        image_path = os.path.join(f"{assets_dir}/generated_images/", "generated_image_frm_seed.png")
        st.image(image_path)
        img_analysis = utils.pickle_load("creative_brief_analysis.pkl")
        headline = st.text_area(label="Headline:", value=img_analysis["advertisements"][0]["headline"], height=68)
        ad_copy = st.text_area(label="Ad copy text:", value=img_analysis["advertisements"][0]["ad_copy"], height=68)
        cta = st.text_area(label="Call to action:", value=img_analysis["advertisements"][0]["call_to_action"], height=68)
        brand = st.text_area(label="Brand:", value=img_analysis["advertisements"][0]["brand"], height=68)

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.markdown("---")

            with st.spinner(text="Analyzing..."):
                current_time1 = datetime.datetime.now()
                generateAd.generate_ad_image(headline, ad_copy, cta, image_path, brand)
                current_time2 = datetime.datetime.now()

                ad_image_path = os.path.join(f"{assets_dir}/generated_ads/", "generated_ad.png")

                # Display the generated image in Streamlit
                st.image(ad_image_path)

                st.session_state.analysis_time = (
                    current_time2 - current_time1
                ).total_seconds()

                st.markdown(
                    f"Analysis time: {current_time2 - current_time1}",
                    unsafe_allow_html=True,
                )
                # st.session_state.input_tokens = response["usage"]["input_tokens"]
                # st.session_state.output_tokens = response["usage"]["output_tokens"]

    with st.sidebar:
        st.markdown("### Inference Parameters")
        st.session_state["model_id"] = "stability.stable-diffusion-xl-v1"

        st.session_state.model_id = st.selectbox(
            "model_id",
            options=[
                "stability.stable-diffusion-xl-v1",
                "amazon.titan-image-generator-v2:0"
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
            ]
        )

        st.session_state.seed = st.slider(
            "seed", min_value=0, max_value=680, value=45, step=5
        )

        st.session_state.cfg_scale = st.slider(
            "cfg_scale", min_value=0, max_value=30, value=10, step=1
        )

        st.session_state.steps = st.slider(
            "steps", min_value=0, max_value=168, value=30, step=1
        )

        st.markdown("---")

        st.text(
            f"""• model_id: {st.session_state.model_id}
• style_preset: {st.session_state.style_preset}
• seed: {st.session_state.seed}
• cfg_scale: {st.session_state.cfg_scale}
• steps: {st.session_state.steps}
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
