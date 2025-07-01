import json

def handler(request, response):
    """Simple test handler for Vercel serverless function."""
    
    # Set CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Content-Type'] = 'application/json'
    
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response.status = 200
        return ''
    
    # Return test response for any method
    response.status = 200
    return json.dumps({
        'message': 'Hello from Vercel Python serverless function!',
        'method': request.method,
        'path': request.path,
        'query': dict(request.query)
    }) 