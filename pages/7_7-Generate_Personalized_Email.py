# Author: Gary A. Stafford
# Modified: 2024-04-14
# AWS Code Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import datetime
import logging
import os
import fitz
import streamlit as st
from argparse import ArgumentParser
from src.utils import bedrockHelper, utils
import faker
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
assets_dir = "assets"
import pandas as pd
movie_data = pd.read_csv(assets_dir + '/movie_items.csv', sep=',', dtype={'PROMOTION': "string"})
retail_data = pd.read_csv(assets_dir + '/adidas_items.csv', sep=',', dtype={'PROMOTION': "string"})
travel_data = pd.read_csv(assets_dir + '/travel_items.csv', sep=',', dtype={'PROMOTION': "string"})
# retail_data.head(5)
# item_data.head(5)
# return recommended items


def get_user_profile():
    fake = faker.Faker()
    cat_map = ({'domain': 'movie', 'category': 'Drama'},
        {'domain': 'movie', 'category': 'Action'},
        {'domain': 'movie', 'category': 'Adventure'},
        {'domain': 'movie', 'category': 'Comedy'},
        {'domain': 'movie', 'category': 'Sci-Fi'},
        {'domain': 'retail', 'category': 'Kids/Accessories'},
        {'domain': 'retail', 'category': 'Kids/Clothing'},
        {'domain': 'retail', 'category': 'Kids/Shoes'},
        {'domain': 'retail', 'category': 'Men/Accessories'},
        {'domain': 'retail', 'category': 'Men/Clothing'},
        {'domain': 'retail', 'category': 'Men/Shoes'},
        {'domain': 'retail', 'category': 'Running/Accessories'},
        {'domain': 'retail', 'category': 'Running/Shoes'},
        {'domain': 'retail', 'category': 'Soccer/Accessories'},
        {'domain': 'retail', 'category': 'Soccer/Shoes'},
        {'domain': 'retail', 'category': 'Women/Accessories'},
        {'domain': 'retail', 'category': 'Women/Clothing'},
        {'domain': 'retail', 'category': 'Women/Shoes'},
        {'domain': 'travel', 'category': 'Beijing'},
        {'domain': 'travel', 'category': 'Guangzhou'},
        {'domain': 'travel', 'category': 'Hong Kong'},
        {'domain': 'travel', 'category': 'London'},
        {'domain': 'travel', 'category': 'New York'},
        {'domain': 'travel', 'category': 'Seoul'},
        {'domain': 'travel', 'category': 'Shanghai'},
        {'domain': 'travel', 'category': 'Sydney'},
        {'domain': 'travel', 'category': 'Tokyo'})
    languages = ('American English', 'Common Wealth English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Dutch', 
                 'Russian', 'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi')
    user_profile = {
        "user_id": fake.random_int(min=1, max=999),
        "name": fake.name(),
        # "age": fake.random_int(min=18, max=75),
        "fav_category": fake.random_element(elements=cat_map),
        "language": fake.random_element(elements=languages),
        }
    # load to a pandas data frame
    user_df = pd.json_normalize(user_profile)
    return user_df

def get_top_items(type, category, n=3):
    print(f"Getting top {n} items for {category} in {type}")
    if type == 'movie':
        data = movie_data[movie_data['GENRES'].str.contains(category)].sort_values(by='IMDB_RATING', ascending=False).head(3)
        data = data.rename(columns={'TITLE': 'name'})
        data = data.rename(columns={'PLOT': 'description'})
        return data[['name', 'description']]
    elif type == 'retail':
        data = retail_data[retail_data['breadcrumbs'].str.contains(category)].sort_values(by='average_rating', ascending=False).head(3)
        return data[['name', 'description']]
    elif type == 'travel':
        data = travel_data[travel_data['DST_CITY'].str.contains(category)].sort_values(by='NUMBER_OF_SEARCH_BY_USER', ascending=False).head(3)
        data['description'] = data.apply(lambda row: 'Travel from ' + str(row['SRC_CITY']) + ' on ' + str(row['AIRLINE'] + ' for a ' + str(row['DURATION_DAYS']) + ' days trip in ' + str(row['MONTH']) + ' - $' + str(row['DYNAMIC_PRICE'])), axis=1)
        data = data.rename(columns={'DST_CITY': 'name'})
        return data[['name', 'description']]

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

    st.header("AWS Agentic AI Demo powered by Amazon Bedrock Agents", divider="rainbow")

    with st.form("email_prompt", border=True, clear_on_submit=False):
        st.markdown(
            """Generative AI powered by Amazon Bedrock and Anthropic Claude 3 family of foundation models."""
        )
        # display a random user id and their favorite genre on button click
        user_df = get_user_profile()

        submitted1 = st.form_submit_button("Click to pick a consumer profile")

        if submitted1:
            st.session_state.user_id = user_df['user_id'].values[0]
            st.session_state.item_domain = user_df.get('fav_category.domain').values[0]
            st.session_state.fav_category = user_df.get('fav_category.category').values[0]
            cat_df = user_df[['fav_category.domain', 'fav_category.category']]
            # print(f"--{dom}  -- {cat}--")
            st.session_state.user_df = user_df.to_html(escape=False, index=False)
            st.session_state.cat_df = cat_df.to_html(escape=False, index=False)
            st.write(st.session_state.user_df, unsafe_allow_html=True)
        else:
            st.write("--")
        
        submitted2 = st.form_submit_button("Click to get personalized recommendations")

        if submitted2:
            st.write(st.session_state.user_df, unsafe_allow_html=True)
            top_df = get_top_items(st.session_state.item_domain,st.session_state.fav_category)
            st.session_state.top_df = top_df.to_html(escape=False, index=False)
            st.write(st.session_state.top_df, unsafe_allow_html=True)
        else:
            st.write("--")

        default_prompt = f'''You are a skilled publicist working for a leading consumer brand
Write a high-converting marketing email advertising several items available, given the item and user information below. 
Your email will leverage the power of storytelling and persuasive language.
You want the email to impress the user, so make it appealing to them based on the information contained in the <user> tags,
and take into account the user\'s preferred category in the <category> tags.
The items to recommend and their information is contained in the <item> tag.
All items in the <item> tag must be recommended. Give a summary of the items and why the user should consider them.
Use the language of the user to write the email.
Do not include any information that is not explicitly asked for in the prompt.
Do not include any information not explicitly asked for in the prompt.
Do not include any information that is not relevant to the email.
Put the email between <email> tags.'''

        submitted3 = st.form_submit_button("Click to generate prompt")

        if submitted3:
            new_prompt = default_prompt \
            + f"\n<user>{st.session_state.user_df}</user>"\
            + f"\n<category>{st.session_state.cat_df}</category>"\
            + f"\n<item>\n{st.session_state.top_df}\n</item>"\
            + "\n<email>"\
            + "\n"\
            + "\n</email>"
            prompt = st.text_area(label="User Prompt:", value=new_prompt, height=268)
            st.session_state.prompt = prompt
        else:
            st.write("--")

        file_paths = []  # only used for images, else none


        submitted = st.form_submit_button("Submit")
        if submitted:
            # st.write(st.session_state.user_df, unsafe_allow_html=True)
            # st.write(st.session_state.top_df, unsafe_allow_html=True)
            st.write(st.session_state.prompt, unsafe_allow_html=True)
            st.markdown("---")
            with st.spinner(text="Analyzing..."):
                current_time1 = datetime.datetime.now()
                response = bedrockHelper.build_request(f"{st.session_state.prompt}", file_paths, profile)
                current_time2 = datetime.datetime.now()
                st.text_area(
                    label="Analysis:",
                    value=response["content"][0]["text"],
                    height=800,
                )
                st.session_state.analysis_time = (
                    current_time2 - current_time1
                ).total_seconds()
                st.session_state.input_tokens = response["usage"]["input_tokens"]
                st.session_state.output_tokens = response["usage"]["output_tokens"]
    
    st.markdown(
        "<small style='color: #888888'> Gary A. Stafford, Ranjith Krishnamoorthy 2024</small>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Inference Parameters")
        st.session_state["model_id"] = "anthropic.claude-3-sonnet-20240229-v1:0"

        st.session_state.model_id = st.selectbox(
            "model_id",
            options=[
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "anthropic.claude-3-opus-20240229-v1:0",
            ],
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
