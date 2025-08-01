import os
from dotenv import load_dotenv
load_dotenv()
from langchain_nvidia import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

# Pydantic model for structured output
class InsuranceAnalysis(BaseModel):
    """Structured data model for the insurance claim analysis."""
    Decision: str = Field(description="The final decision: 'Approved', 'Rejected', or 'Needs More Info'")
    Amount: str = Field(description="The claimable amount as a string (e.g., '50000', 'Up to 2% of Sum Insured', or 'N/A')")
    Justification: str = Field(description="A detailed justification for the decision, citing specific policy clauses or sections from the context provided.")
    Confidence_Score: float = Field(description="A score from 0.0 to 1.0 indicating the model's confidence in its decision.")
    Missing_Info: list[str] = Field(default=[], description="A list of specific questions or information needed if the decision is 'Needs More Info'.")

# LLM and Embedding configuration
OLLAMA_LLM_MODEL = "gemma3n:e2b"
EMBEDDING_MODEL_NAME = "mxbai-embed-large:latest"
GROQ_LLM_MODEL = "gemma-7b-it"
NVIDIA_LLM_MODEL = "google/gemma-3n-e2b-it"

# Centralized RAG chain creation logic
def create_rag_chain(vector_store):
    """Creates and returns the complete RAG retrieval chain."""
    try:
        # 1. Initialize models
        llm = ChatNVIDIA(model=NVIDIA_LLM_MODEL, api_key=os.getenv("NVIDIA_API_KEY"), temperature=0.2)
        
        # 2. Define Pydantic parser
        pydantic_parser = PydanticOutputParser(pydantic_object=InsuranceAnalysis)

        # 3. Create the prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class insurance policy analysis expert. Your task is to act as a claims adjudicator.
            Based on the provided policy document excerpts (context) and the user's query, you must make a decision.
            First, reason step-by-step about the user query and the context. Then, provide your final answer in the requested JSON format.
            Your entire response must be a JSON object that strictly follows the provided format. Do not add any text outside of the JSON structure.
            {format_instructions}
            """),
            ("human", "Policy Documents Context:\n---\n{context}\n---\n\nUser Query: {input}")
        ]).partial(format_instructions=pydantic_parser.get_format_instructions())

        # 4. Create the document chain
        document_chain = create_stuff_documents_chain(llm, prompt_template, output_parser=pydantic_parser)
        
        # 5. Create the retriever from the provided vector store
        retriever = vector_store.as_retriever(search_kwargs={"k": 7})

        # 6. Create and return the final retrieval chain
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        return retrieval_chain

    except Exception as e:
        print(f"Error creating RAG chain: {e}")
        return None