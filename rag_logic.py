import os
from dotenv import load_dotenv
load_dotenv()
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
import hashlib
import time

NVIDIA_LLM_MODEL = "qwen/qwen2.5-7b-instruct"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Performance caching system
class QueryCache:
    def __init__(self):
        self.cache = {}
        self.hit_count = 0
        self.total_queries = 0
    
    def get_cache_key(self, query):
        return hashlib.md5(query.strip().lower().encode()).hexdigest()
    
    def get(self, query):
        self.total_queries += 1
        key = self.get_cache_key(query)
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        return None
    
    def set(self, query, response):
        key = self.get_cache_key(query)
        self.cache[key] = response
    
    def get_hit_rate(self):
        return self.hit_count / max(self.total_queries, 1)

# Global cache instance
query_cache = QueryCache()

def create_rag_chain(retriever, temperature=0.5, model_name=None):
    """Create optimized RAG chain with simple, direct responses.
       model_name comes from the Flask UI selection.
    """
    try:
        chosen_model = model_name or NVIDIA_LLM_MODEL
        llm = ChatNVIDIA(
            model=chosen_model,
            api_key=NVIDIA_API_KEY,
            temperature=temperature
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a highly intelligent Q&A assistant designed to analyze any provided document. Your primary goal is to answer questions accurately based *only* on the text supplied in the 'Context' section.

            **Core Instructions:**
            - Analyze the Context: Carefully examine the provided context. If it appears to be a table (e.g., with rows, columns, or comma-separated values), interpret it as structured data.
            - Read the context and the user's question carefully.
            - Synthesize the information to answer all parts of the question.
            - **Be Precise:** Locate the exact information needed to answer the question. For tabular data, this means finding the correct row and column. For text, it means finding the relevant sentence or fact.
            - **Crucially, your entire response must be a single sentence or two sentences.**
            - **Do NOT use bullet points, numbered lists, or markdown formatting (like bolding with **).**
            - Do NOT add conversational filler, thinking process or introductions like "Here is the information...", "<think>\nOkay, let's break down the user's question", "<think>\nOkay, let's tackle the user's question".
            - **CRUCIAL RULE: If the answer is not explicitly stated in the context, you MUST reply with only this exact phrase: "The information is not available in the provided documents." Do not infer, guess, or provide any information not directly present in the text.**),

            RESPONSE EXAMPLES:
            "questions": [
                "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
                "What is the waiting period for pre-existing diseases (PED) to be covered?",
                "Does this policy cover maternity expenses, and what are the conditions?",
                "What is the waiting period for cataract surgery?",
                "Are the medical expenses for an organ donor covered under this policy?",
                "What is the No Claim Discount (NCD) offered in this policy?",
                "Is there a benefit for preventive health check-ups?",
                "How does the policy define a 'Hospital'?",
                "What is the extent of coverage for AYUSH treatments?",
                "Are there any sub-limits on room rent and ICU charges for Plan A?"
            ]
             
            "answers": [
                "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
                "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
                "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months. The benefit is limited to two deliveries or terminations during the policy period.",
                "The policy has a specific waiting period of two (2) years for cataract surgery.",
                "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person and the donation complies with the Transplantation of Human Organs Act, 1994.",
                "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year. The maximum aggregate NCD is capped at 5% of the total base premium.",
                "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break. The amount is subject to the limits specified in the Table of Benefits.",
                "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7, a fully equipped operation theatre, and which maintains daily records of patients.",
                "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit, provided the treatment is taken in an AYUSH Hospital.",
                "Yes, for Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured. These limits do not apply if the treatment is for a listed procedure in a Preferred Provider Network (PPN)."
            ]

            Provide concise, factual answers only:"""),
            ("human", "Context:\n---\n{context}\n---\n\nQuestion: {input}")
        ])

        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt_template,
            output_parser=StrOutputParser()
        )

        base_chain = create_retrieval_chain(retriever, document_chain)

        class CachedRAGChain:
            def __init__(self, chain):
                self.chain = chain
            
            def invoke(self, inputs):
                query = inputs.get("input", "")
                cached_response = query_cache.get(query)
                if cached_response:
                    print(f"🚀 Cache HIT: {query[:60]}...")
                    return {"answer": cached_response, "input": query, "context": []}
                
                start_time = time.time()
                result = self.chain.invoke(inputs)
                end_time = time.time()

                answer = self.clean_answer(result.get("answer", ""))
                query_cache.set(query, answer)
                print(f"⚡ Processed in {end_time - start_time:.2f}s: {query[:60]}...")
                result["answer"] = answer
                return result

            async def ainvoke(self, inputs):
                query = inputs.get("input", "")
                cached_response = query_cache.get(query)
                if cached_response:
                    print(f"🚀 Async Cache HIT: {query[:60]}...")
                    return {"answer": cached_response, "input": query, "context": []}

                start_time = time.time()
                result = await self.chain.ainvoke(inputs)
                end_time = time.time()

                answer = self.clean_answer(result.get("answer", ""))
                query_cache.set(query, answer)
                print(f"⚡ Async processed in {end_time - start_time:.2f}s: {query[:60]}...")
                result["answer"] = answer
                return result

            def clean_answer(self, answer):
                """Remove thinking tags and verbose intros."""
                import re
                if not answer:
                    return answer
                answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
                answer = re.sub(r'\n\s*\n', '\n', answer)
                answer = answer.strip()
                intro_patterns = [
                    r'^(Answer:|Response:|Based on the context:)\s*',
                    r'^\*\*Answer:\*\*\s*',
                    r'^\*\*Response:\*\*\s*'
                ]
                for pattern in intro_patterns:
                    answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
                return answer.strip()

        print(f"✅ RAG chain ready — Cache hit rate: {query_cache.get_hit_rate():.1%}")
        return CachedRAGChain(base_chain)

    except Exception as e:
        print(f"❌ ERROR creating RAG chain: {e}")
        import traceback
        traceback.print_exc()
        return None
