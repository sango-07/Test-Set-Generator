import streamlit as st
import pandas as pd
import os

# Import the TestCaseGenerator
from test_case_generator import TestCaseGenerator

def main():
    st.set_page_config(
        page_title="Question Generation App", 
        page_icon="📝", 
        layout="wide"
    )

    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-title {
        font-size: 3em;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #3498DB;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2980B9;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

    # Title
    st.markdown("<h1 class='main-title'>📝 AI Question Generator</h1>", unsafe_allow_html=True)

    # Sidebar for inputs
    st.sidebar.header("Configuration")
    
    # File uploader
    uploaded_file = st.sidebar.file_uploader(
        "Upload PDF Document", 
        type=['pdf'], 
        help="Please upload a PDF file to generate questions from"
    )

    # Question type selection
    generator = TestCaseGenerator()
    question_types = st.sidebar.multiselect(
        "Select Question Types", 
        generator.available_question_types,
        default=['hallucination', 'toxicity']
    )

    # Number of questions
    num_questions = st.sidebar.slider(
        "Number of Questions per Type", 
        min_value=1, 
        max_value=20, 
        value=5
    )

    # Generate button
    generate_button = st.sidebar.button("Generate Questions", use_container_width=True)

    # Main content area
    main_content = st.container()

    # Generation logic
    if generate_button and uploaded_file and question_types:
        with st.spinner('Generating questions...'):
            # Create results DataFrame
            final_df = pd.DataFrame()

            # Generate questions for each selected type
            for q_type in question_types:
                try:
                    type_df = generator.generate_testcases(
                        uploaded_file, 
                        question_type=q_type, 
                        num_testcases=num_questions
                    )
                    type_df['question_type'] = q_type
                    final_df = pd.concat([final_df, type_df], ignore_index=True)
                except Exception as e:
                    st.error(f"Error generating {q_type} questions: {e}")

            # Display results
            if not final_df.empty:
                st.success(f"Generated {len(final_df)} questions!")
                
                # Display questions in an interactive table
                st.dataframe(
                    final_df[['question_type', 'question', 'answer']], 
                    use_container_width=True
                )

                # Download button for Excel
                csv = final_df.to_csv(index=False)
                st.download_button(
                    label="Download Questions as CSV", 
                    data=csv, 
                    file_name="generated_questions.csv", 
                    mime="text/csv"
                )
            else:
                st.warning("No questions could be generated. Please check your inputs.")

    elif not uploaded_file:
        st.info("Please upload a PDF document to start generating questions.")

if __name__ == "__main__":
    main()