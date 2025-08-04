import os
from dotenv import load_dotenv
load_dotenv()
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser

NVIDIA_LLM_MODEL = "google/gemma-3n-e4b-it"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

def create_rag_chain(retriever):
    try:
        llm = ChatNVIDIA(model=NVIDIA_LLM_MODEL, api_key=NVIDIA_API_KEY)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert document analysis assistant. Your goal is to provide a single, concise sentence that answers the user's question based on the provided text.
            Read the context and the user's question carefully.
            Synthesize the key information from the context to formulate your answer.
            **Your entire response MUST be a single, complete sentence.** Do not use multiple sentences, bullet points, or line breaks."""),
            ("human", "Context:\n---\n{context}\n---\n\nQuestion: {input}")
        ])

        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt_template,
            output_parser=StrOutputParser()
        )

        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        return retrieval_chain

    except Exception as e:
        print(f"Error creating RAG chain: {e}")
        return None