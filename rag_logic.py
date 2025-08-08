import os
from dotenv import load_dotenv
load_dotenv()
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser

NVIDIA_LLM_MODEL = "meta/llama-4-maverick-17b-128e-instruct"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

def create_rag_chain(retriever):
    try:
        llm = ChatNVIDIA(model=NVIDIA_LLM_MODEL, api_key=NVIDIA_API_KEY)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Q&A assistant for policy documents. Your goal is to provide a direct and concise answer in a single, well-written paragraph.

            Instructions:
            - Read the context and the user's question carefully.
            - Synthesize the information to answer all parts of the question.
            - **Crucially, your entire response must be a single sentence or two sentences.**
            - **Do NOT use bullet points, numbered lists, or markdown formatting (like bolding with **).**
            - Do NOT add conversational filler or introductions like "Here is the information...".
            - **CRUCIAL RULE: If the answer is not explicitly stated in the context, you MUST reply with only this exact phrase: "The information is not available in the provided documents." Do not infer, guess, or provide any information not directly present in the text.**"""),
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