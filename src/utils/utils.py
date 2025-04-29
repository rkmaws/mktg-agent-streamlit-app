import pickle
custom_css = """
        <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap');
                html, body, p, li, a, h1, h2, h3, h4, h5, h6, div, form, input, button, textarea, [class*="css"] {
                    font-family: 'Inter', sans-serif;
                }
                .block-container {
                    padding-top: 32px;
                    padding-bottom: 32px;
                    padding-left: 0;
                    padding-right: 0;
                }
                textarea[class^="st-"] {
                    height: 100px;
                    font-family: 'Inter', sans-serif;
                    background-color: #777777;
                    color: #ffffff;
                }
                section[aria-label="Upload JPG, PNG, GIF, WEBP, PDF, CSV, or TXT files:"] {
                    background-color: #777777;
                }
                textarea[aria-label="Analysis:"] { # llm response
                    height: 800px;
                }
                .element-container img { # uploaded image preview
                    background-color: #ffffff;
                }
                h2 { # main headline
                    color: white;
                }
                MainMenu {
                    visibility: hidden;
                }
                footer {
                    visibility: hidden;
                }
                header {
                    visibility: hidden;
                }
                p, div, h1, h2, h3, h4, h5, h6, button, section, label, input, small[class^="st-"] {
                    color: #ffffff;
                }
                button, section, label, input {
                    background-color: #555555;
                }
                button[class^="st-"] {
                    background-color: #777777;
                    color: #ffffff;
                    border-color: #ffffff;
                }
                hr span {
                    color: #ffffff;
                }
                div[class^="st-"] {
                    color: #ccc8aa;
                }
                div[class^="stSlider"] p {
                    color: #ccc8aa;
                }
                div[class^="stSlider"] label {
                    background-color: #777777;
                }
                div[data-testid="stSidebarUserContent"] {
                    padding-top: 40px;
                }
                div[class="row-widget stSelectbox"] label {
                    background-color: #777777;
                }
                label[data-testid="stWidgetLabel"] p {
                    color: #ccc8aa;
                }
                div[data-baseweb="select"] div {
                    font-size: 14px;
                }
                div[data-baseweb="select"] li {
                    font-size: 12px;
                }
                [data-testid="stForm"] {
                    border-color: #777777;
                }
                [id="generative-ai-powered-multimodal-analysis"] span {
                    color: #e6e6e6;
                    font-size: 34px;
                }
                [data-testid="stForm"] {
                    width: 850px;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                }

                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }

                tr:hover {
                    background-color: #f5f5f5;
                }

                tr:nth-child(even) {
                    background-color: #f2f2f2;
                }

                th {
                    background-color: #4CAF50;
                    color: white;
                }
        </style>
        """
import os
def pickle_dump(obj, file_name):
    print(f"current Dir: {os.getcwd()}")
    full_path = f"{os.getcwd()}/temp/{file_name}"
    with open(full_path, "wb") as f:
        pickle.dump(obj, f)

def pickle_load(file_name):
    print(f"current Dir: {os.getcwd()}")
    full_path = f"{os.getcwd()}/temp/{file_name}"
    with open(full_path, "rb") as f:
        return pickle.load(f)