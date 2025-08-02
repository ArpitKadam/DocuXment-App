import os
from dotenv import load_dotenv
load_dotenv()
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser

NVIDIA_LLM_MODEL = "google/gemma-3n-e2b-it"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

def create_rag_chain(vector_store):
    try:
        llm = ChatNVIDIA(model=NVIDIA_LLM_MODEL, api_key=NVIDIA_API_KEY)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert insurance policy assistant. Your goal is to provide clear and concise answers.
            Read the provided context and the user's question.
            **Do not copy the text directly from the context.** Instead, synthesize the key information and provide a summarized answer in natural language.
            Focus only on the information that directly answers the user's question."""),
            ("human", "Context:\n---\n{context}\n---\n\nQuestion: {input}")
        ])

        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt_template,
            output_parser=StrOutputParser()
        )

        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        return retrieval_chain

    except Exception as e:
        print(f"Error creating RAG chain: {e}")
        return None