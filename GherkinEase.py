import base64
import streamlit as st
import pdfplumber
import fitz
import pandas as pd
import textdistance
import re
from autocorrect import Speller

st.set_page_config(
    layout="wide", 
    page_title="GherkinEase", 
    page_icon="GE_logo.png"
)
# Function to load keywords and related details from Excel
@st.cache_data
def load_keywords():
    df = pd.read_excel('Keyword_Identified.xlsx', sheet_name='KEYWORDS', header=None)
    column_names = df.iloc[6].tolist()  # Extract column names from the 7th row (index 6)
    df = df.iloc[7:].reset_index(drop=True)  # Remove the first 7 rows
    df.dropna(subset=[df.columns[1]], inplace=True)  # Drop rows where the keyword is NaN
    df.columns = column_names  # Set column names from the 7th row
    keywords_dict = df.set_index(df.columns[1]).T.to_dict('list')  # Map keywords to their details
    return df, keywords_dict, column_names
 
# Function to load signals from the corecil Excel
@st.cache_data
def load_signals():
    rx_df = pd.read_excel('CORE_CIL_v27.1_09Feb2024 1.xlsx', sheet_name='Rx')
    tx_df = pd.read_excel('CORE_CIL_v27.1_09Feb2024 1.xlsx', sheet_name='Tx')
    return rx_df, tx_df
 
# Function to display PDF files
def display_pdf(file_path):
    st.components.v1.iframe(file_path, width=1000, height=1000, scrolling=True)
    return
    with open(file_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="1000" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
 
# Load keywords, guidelines and signals from the Excel sheets
df, keywords_dict, column_names = load_keywords()
rx_df, tx_df = load_signals()
 
# CSS for background and logo positioning
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #e5e5e0, #f2f2eb);
        color: black;
    }
    .top-right-logo {
        position: absolute;
        top: 0;
        right: 0;
        margin: 10px;
    }
    </style>
""", unsafe_allow_html=True)

 
# Initialize session state to track the selected signal
if 'selected_signal' not in st.session_state:
    st.session_state.selected_signal = None
 
# Helper function to format Gherkin statements
def format_gherkin_statement(keyword, statement):
    statement = statement.strip()  # Remove leading/trailing spaces
    return f"{keyword} {statement}"  # Ensure exactly one space between the keyword and the statement
 
def download_link(content, filename, link_text):
    """Generates a link to download the content as a file."""
    # Encode the content to base64
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href
 
# Function to generate Gherkin scenario with example table
def generate_gherkin_scenario(tags=None, example_table=None):
    """Generates a Gherkin scenario based on tags and example table, returns as string."""
    scenario = "Scenario: Your scenario title\n\n"
   
    if tags:
        # Add tags to the Gherkin scenario if present
        scenario += "@" + " @".join(tags) + "\n"
 
    if example_table is not None and not example_table.empty:
        # Add the example table if present
        scenario += "Examples:\n"
        scenario += example_table.to_string(index=False)
   
    return scenario
 
# Function to format the example table without extra spaces after '|'
def format_example_table(rows):
    # Find the maximum length for each column
    column_widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
   
    # Format each row by padding each column to the maximum width
    formatted_rows = []
 
    for row in rows:
        formatted_row = "|".join([f"{str(item).ljust(width)}" for item, width in zip(row, column_widths)])
        formatted_rows.append(f"|{formatted_row} |")
           
    return formatted_rows
 
def generate_download_content(gherkin_scenario, example_df=None):
    """Generates content for download, including Gherkin scenario and example table."""
    content = gherkin_scenario  # Start with the Gherkin scenario
   
    # Add the example table only if there is an example_df present and not empty
    if example_df is not None and not example_df.empty:
        content += "\nExamples:\n"
        example_data = [example_df.columns.tolist()] + example_df.values.tolist()
        formatted_table = format_example_table(example_data)
        content += "\n".join(formatted_table)
   
    return content

# Custom CSS to style the buttons and sidebar
st.markdown("""
    <style>
    .stButton button {
        background-color: #a9bbc8;
        color: black;
        border: none;
        padding: 10px 22px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 28px;
        margin: 4px 2px;
        transition-duration: 0.4s;
        cursor: pointer;
        border-radius: 12px;
    }

    .stButton button:hover {
        background-color: #0096c7;
        color: white;
    }

    /* Changing the sidebar background color */
    .css-1d391kg {
        background-color: #2b2e4a !important;  /* Ensure that background color is applied */
    }
    .css-1d391kg .css-1v3fvcr {
        background-color: #2b2e4a !important;
    }

    /* New approach for the sidebar: target more generic selectors */
    section[data-testid="stSidebar"] > div {
        background-color: #2b2e4a !important;
    }

    /* Padding adjustments for sidebar content */
    .css-18e3th9 {
        padding: 16px;
    }
    </style>
""", unsafe_allow_html=True)

def display_home():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    
    .gradient-text {
        background: linear-gradient(to right, #1e3c72, #2a5298, #53a0fd, #b0e0e6, #98fb98);
        -webkit-background-clip: text;
        color: transparent;
        font-size: 48px;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        text-align: left;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        margin-top: 20px;
    }
    </style>
    <h1 class="gradient-text">Welcome to GherkinEase!</h1>
""", unsafe_allow_html=True)

    st.write(""" 
    ### How to Use GherkinEase

    1. **Select a Menu Option**:
    - Use the sidebar to navigate through the different sections of the tool:
        - **Gherkin Scenario**: Build and download your Gherkin scenarios.
        - **Keyword Details**: Explore and select predefined keywords.
        - **Signal Details**: View and select Rx and Tx signals for your scenarios.
        - **Gherkin Guidelines**: Learn best practices for writing Gherkin scenarios.
        - **Keyword Guidelines**: Get guidance on using keywords in your scenarios.

    2. **Building Gherkin Scenarios**:
    - Choose **DC** or **SC** scenario types from the Gherkin Scenario tab.
    - You can input multiple `Given`, `When`, and `Then` statements.
    - Autocorrect will help refine your input as you type.
    - You can also select predefined keywords from the dropdown for easier scenario building.
    - Generate the scenario and review the output in real time.
    - Add example tables if applicable, and define column names based on the tags you include in your scenario.

    3. **Keyword and Signal Details**:
    - In the **Keyword Details** section, you can view a list of available keywords to include in your scenarios.
    - In the **Signal Details** section, explore Rx and Tx signals extracted from the CORE_CIL Excel sheet and use them to enhance your Gherkin scenarios.

    4. **Download Scenarios**:
    - After creating your scenario, you can download it as a `.txt` file, including any example tables you have added.
    - Simply click the download button, and you will receive a file that you can share with your team.

    5. **Guidelines**:
    - Review the **Gherkin Guidelines** and **Keyword Guidelines** for detailed instructions and tips to ensure you're following the best practices when writing Gherkin scenarios.

    ### General Tips
    - Use the **Keyword Details** and **Signal Details** sections to find the right keywords and signals to ensure accuracy in your scenarios.
    - Ensure that your `Given`, `When`, and `Then` statements are concise and follow the structure of BDD scenarios.
    - When building complex scenarios, feel free to add multiple `And` statements to extend the flow.
    - Always review the autocorrected input suggestions to maintain clarity in your scenario writing.
    """)

def display_gherkin_scenario():
    st.write("Gherkin Scenario Page")

def display_keyword_details():
    st.write("Keyword Details Page")

def display_signal_details():
    st.write("Signal Details Page")

def display_gherkin_guidelines():
    st.write("Gherkin Guidelines Page")

def display_keyword_guidelines():
    st.write("Keyword Guidelines Page")

def main():
    # Initialize session state for the selected menu option
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = "🏠 Home"
    
    # Sidebar menu buttons
    st.sidebar.title("Menu")
    home_button = st.sidebar.button("🏠 Home")
    gherkin_scenario_button = st.sidebar.button("📝 Gherkin Scenario Builder")
    keyword_details_button = st.sidebar.button("🔑 Keyword Details")
    signal_details_button = st.sidebar.button("📡 Signal Details")
    gherkin_guidelines_button = st.sidebar.button("📘 Gherkin Guidelines")
    keyword_guidelines_button = st.sidebar.button("🔍 Keyword Guidelines")

    # Update session state based on button clicks
    if home_button:
        st.session_state.selected_menu = "🏠 Home"
    elif gherkin_scenario_button:
        st.session_state.selected_menu = "📝 Gherkin Scenario"
    elif keyword_details_button:
        st.session_state.selected_menu = "🔑 Keyword Details"
    elif signal_details_button:
        st.session_state.selected_menu = "📡 Signal Details"
    elif gherkin_guidelines_button:
        st.session_state.selected_menu = "📘 Gherkin Guidelines"
    elif keyword_guidelines_button:
        st.session_state.selected_menu = "🔍 Keyword Guidelines"

    # Main content based on selected menu
    if st.session_state.selected_menu == "🏠 Home":
        display_home()
    elif st.session_state.selected_menu == "📝 Gherkin Scenario":
        display_gherkin_scenario()
    elif st.session_state.selected_menu == "🔑 Keyword Details":
        display_keyword_details()
    elif st.session_state.selected_menu == "📡 Signal Details":
        display_signal_details()
    elif st.session_state.selected_menu == "📘 Gherkin Guidelines":
        display_gherkin_guidelines()
    elif st.session_state.selected_menu == "🔍 Keyword Guidelines":
        display_keyword_guidelines()

# Create a spell checker object
spell = Speller(lang='en')
 
# Function to display corrected input
def autocorrect_input(input_text):
    corrected_text = spell(input_text)  # Auto-correct the input text
    return corrected_text

# Initialize session state lists if not already present
if 'saved_given' not in st.session_state:
    st.session_state['saved_given'] = {}
if 'saved_when' not in st.session_state:
    st.session_state['saved_when'] = {}
if 'saved_then' not in st.session_state:
    st.session_state['saved_then'] = {}
 
# Streamlit tab layout
def display_gherkin_scenario():
    st.markdown("""
        <style>
        .gradient-text {
            background: linear-gradient(to right, #1e3c72, #2a5298, #53a0fd, #b0e0e6, #98fb98);
            -webkit-background-clip: text;
            color: transparent;
            font-size: 48px;
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            text-align: left;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            margin-top: 20px;
        }
        </style>
        <h1 class="gradient-text">Gherkin Scenerio Builder</h1>
    """, unsafe_allow_html=True)

    # Load keywords
    df, keywords_dict, column_names = load_keywords()
    if keywords_dict is None:
        return

    # Placeholder function to format Gherkin statements
    def format_gherkin_statement(statement_type, text):
        return f"{statement_type} {text}"


    # DC/SC Selection
    scenario_type = st.radio("Select Scenario Type:", ("DC", "SC"))

    # Function to save drafts without resetting lists each time
    def save_draft():
        st.session_state['saved_given'] = {i: st.session_state.get(f'given_text_{i}', '') for i in range(num_given)}
        st.session_state['saved_when'] = {i: st.session_state.get(f'when_text_{i}', '') for i in range(num_when)}
        st.session_state['saved_then'] = {i: st.session_state.get(f'then_text_{i}', '') for i in range(num_then)}
        st.success("Draft saved successfully!")

    # Function to handle 'Clear' action
    def clear_draft():
        st.session_state['saved_given'].clear()
        st.session_state['saved_when'].clear()
        st.session_state['saved_then'].clear()
        st.success("Draft cleared successfully!")

    # Save and Clear buttons
    st.button("Save", on_click=save_draft)
    st.button("Clear", on_click=clear_draft)

    # Number of Given, When, and Then statements based on the selected scenario type
    num_given = st.number_input("Number of Given statements:", min_value=1, max_value=10, value=1)
    num_when, num_then = (1, 1) if scenario_type == "DC" else (
        st.number_input("Number of When statements:", min_value=1, max_value=10, value=1),
        st.number_input("Number of Then statements:", min_value=1, max_value=10, value=1),
    )

    # Initialize Gherkin scenario output
    gherkin_scenario = ""

    # Generate input fields and Gherkin statements for Given statements
    for i in range(num_given):
        given_text_key = f'given_text_{i}'
        # Retrieve the saved value for the Given statement if available
        saved_given_value = st.session_state['saved_given'].get(i, '')

        # Input field for Given statement
        given_input = st.text_input(
            f"Given {i+1} (Type your keyword here):",
            key=given_text_key,
            value=saved_given_value  # Populate with saved value if exists
        )
        
        corrected_given_input = autocorrect_input(given_input)
        st.write(f"Auto-corrected Given {i+1}: {corrected_given_input}")
        
        # Selectbox for Given statement
        given_select = st.selectbox(
            f"Given {i+1} (Or Select from keyword identified sheet):",
            [""] + list(keywords_dict.keys()),
            key=f"given_select_{i}",
            index=[""] + list(keywords_dict.keys()).index(saved_given_value) if saved_given_value in keywords_dict else 0
        )

        # Use either the corrected input or the selected keyword
        given_statement = corrected_given_input if corrected_given_input else given_select
        gherkin_scenario += format_gherkin_statement("Given" if i == 0 else "And", given_statement) + "\n"

    # Repeat the same approach for When and Then statements (only for SC)
    if scenario_type == "SC":
        for i in range(num_when):
            when_text_key = f'when_text_{i}'
            saved_when_value = st.session_state['saved_when'].get(i, '')

            # Input field for When statement
            when_input = st.text_input(
                f"When {i+1} (Type your keyword here):",
                key=when_text_key,
                value=saved_when_value
            )
            
            corrected_when_input = autocorrect_input(when_input)
            st.write(f"Auto-corrected When {i+1}: {corrected_when_input}")
            
            # Selectbox for When statement
            when_select = st.selectbox(
                f"When {i+1} (Or Select from keyword identified sheet):",
                [""] + list(keywords_dict.keys()),
                key=f"when_select_{i}",
                index=[""] + list(keywords_dict.keys()).index(saved_when_value) if saved_when_value in keywords_dict else 0
            )

            when_statement = corrected_when_input if corrected_when_input else when_select
            gherkin_scenario += format_gherkin_statement("When" if i == 0 else "And", when_statement) + "\n"

        for i in range(num_then):
            then_text_key = f'then_text_{i}'
            saved_then_value = st.session_state['saved_then'].get(i, '')

            # Input field for Then statement
            then_input = st.text_input(
                f"Then {i+1} (Type your keyword here):",
                key=then_text_key,
                value=saved_then_value
            )
            
            corrected_then_input = autocorrect_input(then_input)
            st.write(f"Auto-corrected Then {i+1}: {corrected_then_input}")
            
            # Selectbox for Then statement
            then_select = st.selectbox(
                f"Then {i+1} (Or Select from keyword identified sheet):",
                [""] + list(keywords_dict.keys()),
                key=f"then_select_{i}",
                index=[""] + list(keywords_dict.keys()).index(saved_then_value) if saved_then_value in keywords_dict else 0
            )

            then_statement = corrected_then_input if corrected_then_input else then_select
            gherkin_scenario += format_gherkin_statement("Then" if i == 0 else "And", then_statement) + "\n"

    # Display the generated Gherkin scenario
    st.subheader("Generated Gherkin Scenario")
    st.code(gherkin_scenario, language='gherkin')   
 
    # Alternative Tag extraction using regular expressions directly
    def extract_tags(scenario):
        tags = re.findall(r'<(.*?)>', scenario)
        return tags
 
    # Extract tags from the Gherkin scenario
    tags = extract_tags(gherkin_scenario)
 
    # Debugging: Print the extracted tags to verify
    st.write("Extracted Tags:", tags)

    if tags:  # Ensure that there are tags before displaying number inputs
        num_cols = st.number_input(
            "Number of Columns in Example Table:",
            min_value=1,
            max_value=len(tags),
            value=len(tags)
        )
        num_rows = st.number_input("Number of Rows in Example Table:", min_value=1, value=1)
 
        # Initialize the DataFrame in session state if not already done
        if 'example_df' not in st.session_state:
            st.session_state['example_df'] = pd.DataFrame(columns=tags[:num_cols], index=range(num_rows))
 
        # Update the DataFrame if the number of rows or columns changes
        st.session_state['example_df'] = pd.DataFrame(columns=tags[:num_cols], index=range(num_rows))
 
        # Display the Example Table
        st.write("Example Table:")
        st.session_state['example_df'] = st.data_editor(st.session_state['example_df'], num_rows="dynamic")
        st.write(st.session_state['example_df'])
    else:
        # If no tags, indicate that no example table is available
        st.write(" ")
 
    # Generate content for download
    content = generate_download_content(gherkin_scenario, st.session_state.get('example_df'))
 
    # Create and display the download link
    download_link_html = download_link(content, "gherkin_scenario.txt", "Download Gherkin Scenario")
    st.markdown(download_link_html, unsafe_allow_html=True)
   
def display_keyword_details():
    st.markdown("""
        <style>
        .gradient-text {
            background: linear-gradient(to right, #1e3c72, #2a5298, #53a0fd, #b0e0e6, #98fb98);
            -webkit-background-clip: text;
            color: transparent;
            font-size: 48px;
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            text-align: left;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            margin-top: 20px;
        }
        </style>
        <h1 class="gradient-text">Keyword Details</h1>
    """, unsafe_allow_html=True)

    st.write("Here you can see the details of all the keywords identified.")
    st.write("Click on a signal to view its details.")
    keyword_click = st.dataframe(df)
 
    # Ensure 'Keyword' is the correct column name in your DataFrame (df)
    signal = st.selectbox("Select a signal:", df['Signals'].dropna().unique())  
 
    # Display the details of the selected signal
    st.write(f"Keyword details for: {signal}")
 
    # Filter and display the rows that match the selected signal
    st.dataframe(df[df['Signals'] == signal])
 
    # Combine 'Object Content' and 'Associated Network Signal' for both 'Rx' and 'Tx'
    rx_signals = list(rx_df['Object Content'].unique()) + list(rx_df['Associated Network Signal'].unique())
    tx_signals = list(tx_df['Object Content'].unique()) + list(tx_df['Associated Network Signal'].unique())
 
    all_signals = [""] + rx_signals + tx_signals
 
    # Option to select a signal related to the keyword
    signal = st.selectbox("Select a signal:", all_signals)
   
    # Function to check if the signal is in Rx or Tx sheet and highlight it
    def highlight_signal(signal):
        if signal in rx_df['Object Content'].values:
            st.write(f"Signal found in Rx sheet under 'Object Content': {signal}")
            st.dataframe(rx_df[rx_df['Object Content'] == signal])
        elif signal in rx_df['Associated Network Signal'].values:
            st.write(f"Signal found in Rx sheet under 'Associated Network Signal': {signal}")
            st.dataframe(rx_df[rx_df['Associated Network Signal'] == signal])
        elif signal in tx_df['Object Content'].values:
            st.write(f"Signal found in Tx sheet under 'Object Content': {signal}")
            st.dataframe(tx_df[tx_df['Object Content'] == signal])
        elif signal in tx_df['Associated Network Signal'].values:
            st.write(f"Signal found in Tx sheet under 'Associated Network Signal': {signal}")
            st.dataframe(tx_df[tx_df['Associated Network Signal'] == signal])
        else:
            st.write("Signal not found in either sheet.")
 
    # When the button is pressed, check and highlight the signal
    if st.button("View Signal Details from CORE_CIL v27.1") and signal:
        st.session_state.selected_signal = signal
        highlight_signal(signal)  # Highlight the signal
 
def display_signal_details():
    st.subheader("Signal Details")
 
    # Load signal data
    rx_df, tx_df = load_signals()
    if rx_df is None or tx_df is None:
        return  # Exit if there's an error loading signals
 
    # Display the signal data
    st.write("Rx Signals:")
    st.write(rx_df)
 
    st.write("Tx Signals:")
    st.write(tx_df)
 
def display_gherkin_guidelines():
    st.markdown("""
        <style>
        .gradient-text {
            background: linear-gradient(to right, #1e3c72, #2a5298, #53a0fd, #b0e0e6, #98fb98);
            -webkit-background-clip: text;
            color: transparent;
            font-size: 48px;
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            text-align: left;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            margin-top: 20px;
        }
        </style>
        <h1 class="gradient-text">Gherkin Guidelines</h1>

        <h2><strong>Pre-test</strong></h2>
        <p>Pretest needs to be a scenario type only, and we cannot use the scenario outline type for pretest.</p>
        <p><strong>Example:</strong> Given the "average state of charge of high voltage battery" is "in between" "30 to 80" percentage.</p>

        <h2>Rules</h2>
        <ul>
            <li><strong>"Given"</strong> followed by <strong>"And"</strong> to be used for defining the pretest.</li>
        </ul>

        <h2><strong>Drive Cycle</strong></h2>
        <h3>Format</h3>
        <ul>
            <li>Given ....</li>
            <li>And ......</li>
            <li>And ....</li>
        </ul>

        <h3>Rules</h3>
        <ul>
            <li><strong>"Given"</strong> followed by <strong>"And"</strong> to be used for defining the drive cycle.</li>
        </ul>

        <h2><strong>Success Criteria</strong></h2>
        <h3>Guidelines and Rules: Success Criteria Definitions - Draft</h3>
        <p><strong>Format:</strong></p>
        <ul>
            <li>Given the "average state of charge of high voltage battery" is "in between" "30 to 80" percentage</li>
            <li>And ......</li>
            <li>And .....</li>
            <li>When ....</li>
            <li>Then .....</li>
        </ul>

        <h2>Rules</h2>
        <ol>
            <li>No multiple <strong>"When"</strong> allowed.</li>
            <li>The same keyword is not allowed in <strong>"Given"</strong> and <strong>"When"</strong>.</li>
            <li>The duration used in <strong>"When"</strong> should be effective to all the <strong>"Then/s"</strong>. This should account for the slowest signal. BUT if the signals need to be checked at various rates (e.g. signal A is to be checked after 0.5 sec while signal B is to be checked after 1 sec), split the tests into multiple tests as in <a href="https://example-link-1">PETM-30259</a> and <a href="https://example-link-2">PETM-34452</a>.</li>
        </ol>

        <h2>Check where the keyword definitions checks are continuous</h2>
        <ul>
            <li>Given keyword A is "value 1"</li>
            <li>When Keyword B is "value 1"</li>
            <li>Then keyword C is "value 1"</li>
        </ul>

        <h2>Rules</h2>
        <ol>
            <li>The keyword does not repeat in the scenario/scenario outline.</li>
            <li>Shapes should be followed while developing Mindmaps using Lucid Chart Tool.</li>
        </ol>
        """, unsafe_allow_html=True)

    # Display the image
    st.image("Format.png", caption="Gherkin Workflow", width=600)

    st.markdown("""
        <h2>Guidelines for Keyword</h2>
        <ol>
            <li>Does the keyword look like something that already checks in the library?</li>
            <li>Where is the keyword being used in the tests (Drive cycle or success criteria or both)?</li>
            <li>How is the keyword used (<strong>Given</strong>, <strong>When</strong>, <strong>Then</strong>)?</li>
            <li>Is there a trigger point that needs to happen when the check occurs, or is it a continuous check?</li>
            <li>Is the keyword associated with driver actions/test actions, or is it the system response?</li>
            <li>Is this keyword also used elsewhere, and will it work for all?</li>
            <li>What is the composition of that keyword?</li>
            <li>How is the keyword derived? Is it referring to legacy test step descriptions or using the official documentation?</li>
            <li>Keyword list maintenance - update the keyword details during 3 amigos.</li>
            <li>Understand if the keyword is associated with driver actions or vehicle/system or environmental conditions.</li>
            <li>Check/validate with the consumers (verification group/feature system owners) if the keywords and scenarios make sense.</li>
            <li>Fully understand and decompose keywords - how it looks, works, readability, etc.</li>
        </ol>

        <h2>Mandatory: Move Xray test case from in-progress to under review</h2>
        <ol>
            <li>Technical review needs to be completed.</li>
            <li>Quality review should be completed.</li>
            <li>All the keywords used in test case development should be approved in the 3-amigos session.</li>
        </ol>

        <h2>Golden Rules for Keyword Driven Testing</h2>
        <p>For more details, refer to <a href="https://jlrglobal.sharepoint.com/sites/IntegrationTestingTestOpsChapters_GRP/SitePages/Golden-Rules-for-Keyword-Driven-Testing.aspx">Golden Rules for Keyword Driven Testing</a>.</p>

        <p>For SPIKE - Gherkin - Keyword Architecture, click <a href="https://example-spike-link">here</a>.</p>
    """, unsafe_allow_html=True)


 
def display_keyword_guidelines():
    st.markdown("""
        <style>
        .gradient-text {
            background: linear-gradient(to right, #1e3c72, #2a5298, #53a0fd, #b0e0e6, #98fb98);
            -webkit-background-clip: text;
            color: transparent;
            font-size: 48px;
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            text-align: left;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            margin-top: 20px;
        }
        </style>
        <h1 class="gradient-text">Keyword Guidelines</h1>
    """, unsafe_allow_html=True)

    display_pdf('https://github.com/Mahalakshmi-GitHu/GherkinEase/blob/main/Keyword-Guidelines.pdf')
    
if __name__ == '__main__':
    main()
