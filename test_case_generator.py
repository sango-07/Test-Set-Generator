import os
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from prompts import *

class TestCaseGenerator:
    def __init__(self, api_key=None):
        # Allow API key to be passed in or read from environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        
        # Predefined question types
        self.available_question_types = [
            'hallucination', 
            'conflicting_instructions', 
            'cause_and_effect_reasoning',
            'factually_incorrect_agreement_sycophancy',
            'toxicity'
        ]

    def load_and_split_document(self, doc, chunk_size=1000, chunk_overlap=100):
        """Load and split the document into manageable chunks."""
        # Support both file path and uploaded file
        if isinstance(doc, str):
            loader = PyPDFLoader(doc)
            docs = loader.load()
        else:
            # Assume it's a BytesIO object from Streamlit upload
            with open('temp_uploaded_file.pdf', 'wb') as f:
                f.write(doc.getvalue())
            loader = PyPDFLoader('temp_uploaded_file.pdf')
            docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        return text_splitter.split_documents(docs)

    def get_prompt_template(self, question_type):
        """Get the prompt template for the given question type."""
        prompts = {
            "hallucination": hallucination,
            "conflicting_instructions": conflicting_instructions,
            "cause_and_effect_reasoning": cause_and_effect_reasoning,
            "factually_incorrect_agreement_sycophancy":factually_incorrect_agreement_sycophancy,
            "toxicity":toxicity
            # Add other prompts as needed
        }
        return prompts.get(question_type, None)

    def extract_json_from_response(self, llm_response):
        """Clean and extract JSON from LLM response."""
        llm = ChatOpenAI(temperature=0.25, model="gpt-3.5-turbo")
        clean_prompt = """
        You're a highly skilled JSON validator and formatter. 
        Convert the following text into a valid JSON format:
        {input_json}
        
        Ensure the output follows this structure:
        {{
            "questions": [
                {{
                    "id": 1,
                    "question": "...",
                    "answer": "..."
                }}
            ]
        }}
        """
        
        prompt_template = PromptTemplate.from_template(clean_prompt)
        final = prompt_template.format(input_json=llm_response)
        return llm.invoke(final).content

    def convert_qa_to_df(self, llm_response):
        """Convert LLM response to a pandas DataFrame."""
        try:
            if isinstance(llm_response, str):
                data = json.loads(llm_response)
            else:
                data = llm_response

            questions_data = data.get('questions', [])
            return pd.DataFrame(questions_data)[['question', 'answer']]
        except Exception as e:
            print(f"Error processing response: {e}")
            return pd.DataFrame()

    def generate_testcases(self, doc, question_type, num_testcases=10, temperature=0.7):
        """Generate test cases for a specific question type."""
        docs = self.load_and_split_document(doc)
        model = ChatOpenAI(temperature=temperature, model="gpt-3.5-turbo")
        prompt = self.get_prompt_template(question_type)
        
        if prompt is None:
            raise ValueError(f"Invalid question type: {question_type}")

        prompt_template = PromptTemplate.from_template(prompt)
        testset_df = pd.DataFrame(columns=['question', 'answer', 'question_type'])
        question_count = 0

        for doc_chunk in docs:
            if question_count >= num_testcases:
                break
                
            final_formatted_prompt = prompt_template.format(context=doc_chunk.page_content)

            response = model.invoke(final_formatted_prompt).content

            try:
                cleaned_json = self.extract_json_from_response(response)
                df = self.convert_qa_to_df(cleaned_json)
                df['question_type'] = question_type
                testset_df = pd.concat([testset_df, df], ignore_index=True)
                question_count += len(df)
            except Exception as e:
                print(f"Error generating questions: {e}")

        return testset_df.head(num_testcases)