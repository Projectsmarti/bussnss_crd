from PIL import Image
import os, pandas as pd, google.generativeai as gem, csv, ast, streamlit as st
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ["GOOGLE_API_KEY"] = 'AIzaSyC4g4c-Dri_4CiRkSk0vN8w81r7OUj0iQs'
gem.configure(api_key=os.environ["GOOGLE_API_KEY"])
# Configuration
IMAGE_FOLDER = "uploaded_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Initialize Google Generative AI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")

# Streamlit UI
st.markdown(f"<h2 style='color:blue; text-align: center;'>{'Business Card Extractor'}</h2>",unsafe_allow_html = True)
st.markdown("""<style>.stButton > button {display: block;margin: 0 auto;}</style>""", unsafe_allow_html=True)

# Check if the CSV file exists
csv_filename = "business_cards.csv"
csv_exists = os.path.exists(csv_filename)

# Initialize session state for storing JSON data
if 'json_data' not in st.session_state:
    st.session_state.json_data = {}

try:
    # 1. Option to upload images
    uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])
    if uploaded_files:
        try:
            for uploaded_file in uploaded_files:
                with open(os.path.join(IMAGE_FOLDER, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success("Image(s) uploaded successfully!", icon="✅")

            # Display uploaded images in a grid
            image_paths = [os.path.join(IMAGE_FOLDER, uploaded_file.name) for uploaded_file in uploaded_files]
            if image_paths:
                num_cols = 5  # Number of columns for grid layout
                cols = st.columns(num_cols)
                for i, image_path in enumerate(image_paths):
                    with cols[i % num_cols]:
                        image = Image.open(image_path)
                        st.image(image, caption=os.path.basename(image_path))
        except Exception as e:
            st.error("Failed to upload images.")
            st.exception(e)
except Exception as e:
    st.error("An error occurred during the upload process.")
    st.exception(e)

try:
    # 2. Option to choose images from an existing folder
    existing_images = [f for f in os.listdir(IMAGE_FOLDER) if os.path.isfile(os.path.join(IMAGE_FOLDER, f))]

    if not existing_images:
        st.caption("The folder is empty")

    selected_images = st.multiselect("Select Images from Existing Folder", existing_images)

    # Display selected images in a grid
    if selected_images:
        try:
            image_paths = [os.path.join(IMAGE_FOLDER, image_file) for image_file in selected_images]
            if image_paths:
                num_cols = 5  # Number of columns for grid layout
                cols = st.columns(num_cols)
                for i, image_path in enumerate(image_paths):
                    with cols[i % num_cols]:
                        image = Image.open(image_path)
                        st.image(image, caption=os.path.basename(image_path))
        except Exception as e:
            st.error("Failed to display selected images.")
            st.exception(e)
except Exception as e:
    st.error("An error occurred while selecting images from the folder.")
    st.exception(e)

try:
    # Create columns for placing checkboxes
    col1, col2 = st.columns([1, 4])

    # Place the first checkbox (CSV) in the first column
    with col1:
        display_csv = st.checkbox("View CSV", value=csv_exists, help="Check to display CSV data")
    # Place the second checkbox (JSON) in the second column
    with col2:
        display_json = st.checkbox("View JSON", key="display_json", help="Check to display JSON data extracted")

    # Apply custom CSS to move the checkboxes downwards
    st.markdown(
        """
        <style>
        .stCheckbox {
            display: flex;
            justify-content: flex-end;
            margin-top: 20px; /* Adjust the margin-top value as needed */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.error("An error occurred while setting up the checkboxes.")
    st.exception(e)

try:
    # 3. Option to clean the existing images in the folder/clean selected images from the existing folder
    if st.button("Clean All Images"):
        if not existing_images:
            st.error("The folder is empty")
        else:
            try:
                for f in existing_images:
                    os.remove(os.path.join(IMAGE_FOLDER, f))
                st.info("All images cleaned", icon="❗")
            except Exception as e:
                st.error("Failed to clean all images.")
                st.exception(e)

    if st.button("Clean Selected Images"):
        if not selected_images:
            st.error("No images selected for cleaning")
        else:
            try:
                for f in selected_images:
                    os.remove(os.path.join(IMAGE_FOLDER, f))
                st.info("Selected images cleaned!", icon="❗")
            except Exception as e:
                st.error("Failed to clean selected images.")
                st.exception(e)
except Exception as e:
    st.error("An error occurred while cleaning images.")
    st.exception(e)

try:
    # Process selected images
    if st.button("Process Selected Images"):
        if not selected_images:
            st.error("Select image(s) to proceed")
        else:
            columns = ["Person name", "Company name", "Email", "Contact number"]
            all_rows = []
            st.session_state.json_data = {}  # Reset session state for new processing

            try:
                for image_file in selected_images:
                    image_path = os.path.join(IMAGE_FOLDER, image_file)
                    image = Image.open(image_path)
                    vision = gem.GenerativeModel('gemini-1.5-flash-latest')
                    res = vision.generate_content(["""You are only a business card image recognizer,you will tell clean 'YES' if it is it else clean 'NO' """,image])
                    if res.text=='NO':
                        st.info(f"{os.path.basename(image_path)} is not a business card", icon = '❗')
                        continue                
                        
                    message = HumanMessage(
                        # content=[
                        #     {
                        #         "type": "text",
                        #         "text": """Carefully analyze the business card(s) and get the output in pure json format

                        #         [{"Person name": "full name of the person if exists",
                        #             "Company name": "get the full company name if exists",
                        #             "Email": "get the complete mail if exists",
                        #             "Contact number": "get every contact numbers if exists"}]
                        #             your response shall not contain ' ```json ' and ' ``` ' """,
                        #     },
                        #     {"type": "image_url", "image_url": image_path}
                        # ]

                        content=[
                        {
                            "type": "text",
                            "text": """Carefully analyze the business card(s) and get the output in pure json format

                            [{"Person name": "full name of the person if exists",
                                "Company name": "get the full company name if exists",
                                "Email": "get the complete mail if exists",
                                "Contact number": "get every contact number if exists"}]
                                
                            if a card has multiple person name then the output be like:
                            
                            [{"Person name": "full name of the person if exists",
                                "Person name 2": "full name of the person if exists",
                                "Company name": "get the full company name if exists",
                                "Email": "get the complete mail if exists",
                                "Contact number": "get every contact number if exists"}]
                                your response shall not contain ' ```json ' and ' ``` ' """,
                        },
                        {"type": "image_url", "image_url": image_path}
                    ]
                    )

                    try:
                        response = llm.invoke([message])
                        response = response.content.replace('null', 'None')#.replace('null', 'None')
                        extracted_data = ast.literal_eval(response)

                        columns = ["Person name", "Company name", "Email", "Contact number"]

                        rows = []
                        # for item in extracted_data:
                        #     row = {col: item.get(col, "") for col in columns}
                        #     rows.append(row)
                        # all_rows.extend(rows)

                        columns = ["Person name", "Person name 2", "Company name", "Email", "Contact number"]
                        for item in extracted_data:
                            person_name = item.get("Person name", "")
                            person_name_2 = item.get("Person name 2", "")
                            row = {
                                "Person name": f"{person_name}, {person_name_2}",
                                "Company name": item.get("Company name", ""),
                                "Email": item.get("Email", ""),
                                "Contact number": item.get("Contact number", ""),
                            }
                            rows.append(row)
                        all_rows.extend(rows)

                        # Store the extracted JSON data in session state
                        st.session_state.json_data[image_file] = extracted_data
                    except Exception as e:
                        st.error(f"Failed to process image: {image_file}")
                        st.exception(e)

                try:
                    df = pd.DataFrame(all_rows, columns=columns)

                    # Load existing CSV if it exists and append new data
                    if csv_exists:
                        existing_df = pd.read_csv(csv_filename)
                        df = pd.concat([existing_df, df], ignore_index=True)

                    # Save the DataFrame back to the CSV file
                    df.to_csv(csv_filename, index=False)
                    st.info(f"CSV file '{csv_filename}' updated", icon="✅")
                except Exception as e:
                    st.error("Failed to update CSV file.")
                    st.exception(e)
            except Exception as e:
                st.error("An error occurred while processing the selected images.")
                st.exception(e)
except Exception as e:
    st.error("An error occurred during the image processing step.")
    st.exception(e)

try:
    # Display the JSON data if the checkbox is checked
    if display_json:
        for image_file, extracted_data in st.session_state.json_data.items():
            with st.expander(f"Show JSON - {image_file}"):
                st.json(extracted_data)
except Exception as e:
    st.error("An error occurred while displaying JSON data.")
    st.exception(e)

try:
    # Display the DataFrame if the checkbox is checked
    if display_csv and csv_exists:
        df = pd.read_csv(csv_filename)
        st.markdown('##### Verify Data 📝')
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor_displayed")

        # Save the edited DataFrame back to the CSV file
        edited_df.to_csv(csv_filename, index=False)
        st.markdown('##### Final Data')
        st.write(edited_df)
except Exception as e:
    st.error("An error occurred while displaying the CSV data.")
    st.exception(e)

st.stop()
