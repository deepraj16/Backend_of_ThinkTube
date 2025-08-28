from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from youtube_tran import get_video_transcript
from vector_store import setup_embeddings_and_vectorstore
from indexing import setup_llm, create_document_chunks
from promt_templtes import create_prompt_template


import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64
if not hasattr(np, 'int_'):
    np.int_ = np.int64 

    
def format_docs(retrieved_docs):
    """Format retrieved documents into context text"""
    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return context_text

def setup_rag_chain(vector_store, prompt, llm):
    """Setup the complete RAG chain"""
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={'k': 4})
    
    parallel_chain = RunnableParallel({
        'context': retriever | RunnableLambda(format_docs),
        'question': RunnablePassthrough()
    })
    
    parser = StrOutputParser()
    main_chain = parallel_chain | prompt | llm | parser
    
    return main_chain

def initialize_rag_system(video_id):
    """Initialize the complete RAG system for a video"""
    try:
        # Setup LLM
        llm = setup_llm()
        
        # Get transcript
        transcript = get_video_transcript(video_id)
        if not transcript:
            return None, "Failed to get transcript. Video may not have captions or captions may be disabled."
        # Create chunks
        chunks = create_document_chunks(transcript)
        # Setup vector store
        vector_store = setup_embeddings_and_vectorstore(chunks)
        # Create prompt
        prompt = create_prompt_template()
        main_chain = setup_rag_chain(vector_store, prompt, llm)
        
        return main_chain, "Success"
    
    except Exception as e:
        return None, f"Error initializing RAG system: {str(e)}"

def query_video(question, main_chain):
    """Query the video using the RAG chain"""
    try:
        response = main_chain.invoke(question)
        return response
    except Exception as e:
        return None

def process_video_query(video_id, question):
    """Process a single query for a video - complete pipeline"""
    main_chain, status = initialize_rag_system(video_id)
    
    if main_chain is None:
        return {"error": status}
    
    response = query_video(question, main_chain)
    if response:
        return {"response": response}
    else:
        return {"error": "Failed to process query"}