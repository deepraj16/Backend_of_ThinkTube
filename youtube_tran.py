import requests

import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64
if not hasattr(np, 'int_'):
    np.int_ = np.int64 

    
def get_video_transcript(video_id):
    """Get transcript from YouTube video using RapidAPI"""
    if not video_id:
        raise ValueError("Video ID is not provided.")
   
    api_key = "aa1b4a6932mshbeb683ba4c15e85p1340a8jsn22a230a7d684"

    url = "https://youtube-transcript3.p.rapidapi.com/api/transcript"
    querystring = {"videoId": video_id}
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-transcript3.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                # If response is a list of transcript segments
                transcript = " ".join(item.get('text', '') for item in data if 'text' in item)
                return transcript
            elif isinstance(data, dict):
                # If response is a dictionary, check for common transcript fields
                if 'transcript' in data:
                    if isinstance(data['transcript'], list):
                        transcript = " ".join(item.get('text', '') for item in data['transcript'] if 'text' in item)
                        return transcript
                    else:
                        return str(data['transcript'])
                elif 'text' in data:
                    return data['text']
                elif 'data' in data and isinstance(data['data'], list):
                    transcript = " ".join(item.get('text', '') for item in data['data'] if 'text' in item)
                    return transcript
                else:
                    # Return the whole response if we can't parse it
                    return str(data)
            
            # If we can't parse the response, return it as string
            return str(data)
        
        else:
            # Return None for any error status codes to match original behavior
            return None
            
    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None
    

# video_id = "ZXiruGOCn9s"
# data=get_video_transcript(video_id)
# print(data)    