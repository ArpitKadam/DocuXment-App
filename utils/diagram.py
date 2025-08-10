from graphviz import Digraph

flow = Digraph('RAG_Data_Flow', format='png')
flow.attr(rankdir='TB', splines='ortho', label='RAG API Flowchart', labelloc='t', fontsize='20')

# Nodes
flow.node('User', 'User', shape='ellipse', style='filled', fillcolor='#A8E6CF')
flow.node('API', 'API Request Received', shape='box', style='filled', fillcolor='#E1BEE7')

# Document Cache Check
flow.node('Doc_Provided', 'Documents Provided?', shape='diamond', style='filled', fillcolor='#81D4FA')
flow.node('Doc_Cache', 'Documents in FAISS Cache?', shape='diamond', style='filled', fillcolor='#FFF59D')

# Document processing
flow.node('Create_FAISS', 'Process Docs & Create FAISS Index', shape='box', style='filled', fillcolor='#A5D6A7')
flow.node('Use_Pinecone', 'Use Pinecone Vector Store', shape='box', style='filled', fillcolor='#FFAB91')

# Query Cache
flow.node('Query_Cache', 'Query Cache', shape='cylinder', style='filled', fillcolor='#FFE0B2')

# Retrieval & Answer
flow.node('Retrieve_Docs', 'Retrieve Relevant Docs', shape='box')
flow.node('Generate_Answer', 'Generate Answer with LLM', shape='box')
flow.node('Return_Answer', 'Return Final Answer', shape='ellipse', style='filled', fillcolor='#FFECB3')

# Flow
flow.edge('User', 'API')
flow.edge('API', 'Doc_Provided')

# Docs Provided? -> Yes/No
flow.edge('Doc_Provided', 'Doc_Cache', label='Yes')
flow.edge('Doc_Provided', 'Use_Pinecone', label='No')

# Doc Cache -> Hit/Miss
flow.edge('Doc_Cache', 'Query_Cache', label='Cache Hit')
flow.edge('Doc_Cache', 'Create_FAISS', label='Cache Miss')

# After FAISS creation
flow.edge('Create_FAISS', 'Query_Cache')

# Pinecone path also goes to Query Cache
flow.edge('Use_Pinecone', 'Query_Cache')

# Query Cache -> Hit/Miss
flow.edge('Query_Cache', 'Generate_Answer', label='Cache Hit')
flow.edge('Query_Cache', 'Retrieve_Docs', label='Cache Miss')

# Retrieval path
flow.edge('Retrieve_Docs', 'Generate_Answer')

# Answer generation
flow.edge('Generate_Answer', 'Return_Answer')

flow.render("rag_flowchart", cleanup=True)
