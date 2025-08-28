from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import re
from youtube_rag import initialize_rag_system, query_video, process_video_query

app = Flask(__name__)
CORS(app)

# numpy compatibility for some environments
if not hasattr(np, 'float_'):
    np.float_ = np.float64
if not hasattr(np, 'int_'):
    np.int_ = np.int64

def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|live\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Single video state - only one video at a time
current_video_id = ""
current_rag_chain = None
is_initialized = False

def clear_current_video():
    """Clear current video state completely"""
    global current_video_id, current_rag_chain, is_initialized
    
    # Clear RAG chain properly if it exists
    if current_rag_chain:
        try:
            # If your RAG system has a cleanup method, call it here
            # current_rag_chain.cleanup()  # Uncomment if available
            del current_rag_chain
        except Exception as e:
            print(f"Error clearing RAG chain: {e}")
    
    current_video_id = ""
    current_rag_chain = None
    is_initialized = False
    
    # Force garbage collection to ensure memory is cleared
    import gc
    gc.collect()

@app.route("/get_youtube_video_info", methods=["POST"])
def get_youtube_video_info():
    global current_video_id
    
    data = request.get_json()
    video_url = data.get("video_id")
    
    if not video_url:
        return jsonify({"error": "video_id is required"}), 400
    
    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube video URL"}), 400
    
    # Always clear existing video state before loading new video
    print(f"Clearing previous video state. Current video: {current_video_id}")
    clear_current_video()
    
    # Set new video
    current_video_id = video_id
    print(f"Loading new video: {current_video_id}")
    
    video_info = {
        "video_id": video_id,
        "title": "YouTube Video",
        "description": "Video loaded successfully. You can now ask questions about this video.",
        "status": "ready_for_questions",
        "initialized": False
    }
    return jsonify(video_info)

@app.route("/initialize_video", methods=["POST"])
def initialize_video():
    global current_video_id, current_rag_chain, is_initialized
    
    if not current_video_id:
        return jsonify({"error": "No video ID found. Please load a video first."}), 400
    
    # Force re-initialization even if already initialized to ensure clean state
    print(f"Initializing video: {current_video_id}")
    
    try:
        # Clear any existing RAG chain first
        if current_rag_chain:
            try:
                del current_rag_chain
            except:
                pass
        
        current_rag_chain = None
        is_initialized = False
        
        # Initialize RAG system for current video
        main_chain, status = initialize_rag_system(current_video_id)
        if main_chain:
            current_rag_chain = main_chain
            is_initialized = True
            print(f"Video {current_video_id} initialized successfully")
            return jsonify({
                "status": "success", 
                "message": "Video initialized successfully. You can now ask questions."
            })
        else:
            return jsonify({"error": status}), 400
    except Exception as e:
        print(f"Error initializing video: {e}")
        return jsonify({"error": f"Failed to initialize video: {str(e)}"}), 400

@app.route("/ask_question", methods=["POST"])
def ask_question():
    global current_video_id, current_rag_chain, is_initialized
    
    data = request.get_json()
    question = data.get("question")
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    if not current_video_id:
        return jsonify({"error": "No video loaded. Please load a video first."}), 400
    
    # Initialize if not already done
    if not is_initialized or not current_rag_chain:
        try:
            print(f"Auto-initializing video: {current_video_id}")
            main_chain, status = initialize_rag_system(current_video_id)
            if not main_chain:
                return jsonify({"error": f"Failed to initialize video: {status}"}), 400
            current_rag_chain = main_chain
            is_initialized = True
        except Exception as e:
            return jsonify({"error": f"Failed to initialize video: {str(e)}"}), 400
    
    try:
        print(f"Processing question for video: {current_video_id}")
        response = query_video(question, current_rag_chain)
        if response:
            return jsonify({
                "question": question,
                "answer": response,
                "video_id": current_video_id
            })
        else:
            return jsonify({"error": "Failed to process your question. Please try again."}), 400
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 400

@app.route("/quick_query", methods=["POST"])
def quick_query():
    """Single endpoint for quick question without separate initialization"""
    global current_video_id
    
    data = request.get_json()
    question = data.get("question")
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    if not current_video_id:
        return jsonify({"error": "No video loaded. Please load a video first."}), 400
    
    try:
        print(f"Processing quick query for video: {current_video_id}")
        result = process_video_query(current_video_id, question)
        if "error" in result:
            return jsonify(result), 400
        else:
            return jsonify({
                "question": question,
                "answer": result["response"],
                "video_id": current_video_id
            })
    except Exception as e:
        print(f"Error processing quick query: {e}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 400

@app.route("/get_current_video", methods=["GET"])
def get_current_video():
    """Get current loaded video information"""
    global current_video_id, is_initialized
    
    if current_video_id:
        return jsonify({
            "video_id": current_video_id,
            "initialized": is_initialized,
            "status": "ready" if is_initialized else "loaded"
        })
    else:
        return jsonify({"error": "No video loaded"}), 404

@app.route("/clear_current_video", methods=["POST"])
def clear_video_endpoint():
    """Clear current video and reset state - for frontend use"""
    print("Clearing current video via API call")
    clear_current_video()
    return jsonify({
        "status": "success",
        "message": "Video cleared successfully"
    })

@app.route("/clear_video", methods=["POST"])
def clear_video():
    """Clear current video and reset state - legacy endpoint"""
    print("Clearing current video via legacy API call")
    clear_current_video()
    return jsonify({
        "status": "success",
        "message": "Video cleared successfully"
    })

@app.route("/status", methods=["GET"])
def get_status():
    """Get current system status"""
    return jsonify({
        "current_video_id": current_video_id if current_video_id else None,
        "is_initialized": is_initialized,
        "has_rag_chain": current_rag_chain is not None,
        "status": "ready" if (current_video_id and is_initialized) else "idle"
    })

def get_id():
    """Helper function for current video ID"""
    return current_video_id

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
