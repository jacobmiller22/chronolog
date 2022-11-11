from flask import Flask, request

# This will be run on a separate thread
STATE_CODE = (None, None)
app = Flask(__name__)
app.use_reloader = False

_semaphore = None

def create_auth_server(state_code, semaphore) -> Flask:
    global _semaphore
    _semaphore = semaphore
    
    global STATE_CODE
    STATE_CODE = state_code
    
    global app
    return app

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/google/oauth2/callback", methods=["GET"])
def google_oauth2_callback():
    global STATE_CODE
    args = request.args
    if args.get("state") == STATE_CODE[0]:
        STATE_CODE = (STATE_CODE[0], args.get("code"))
        global _semaphore
        _semaphore.release()
        return "Success! You can close this window now."
    return "Oops! Something went wrong. Please try again."
        
