#!/usr/bin/env python3

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def respond():

    payload = request.json
# This will print the payload sent by GitHub
    print(payload)

    return payload

if __name__ == '__main__':
    app.run(port=5000, debug=True)

# from flask import Flask, request, jsonify
# import os
# import hmac
# import hashlib

# app = Flask(__name__)
# # Fetch the GitHub secret from environment variables
# GIT_SECRET = os.environ.get("GIT_SECRET")

# def verify_event(req_headers, body, secret):
#     """
#     Verify the GitHub webhook event by checking its signature.

#     Parameters:
#     - req_headers: The headers from the incoming request.
#     - body: The raw body of the incoming request as bytes.
#     - secret: The secret used to verify the HMAC signature.

#     Returns:
#     - A boolean indicating whether the verification succeeded.
#     """
#     # Extract the signature from the request headers
#     sig_header = req_headers.get('X-Hub-Signature')
#     if not sig_header or len(sig_header) != 45 or not sig_header.startswith('sha1='):
#         return False

#     # Decode the hex signature
#     sig = bytes.fromhex(sig_header[5:])
    
#     # Create a new HMAC object using the secret and the SHA1 algorithm
#     mac = hmac.new(bytes(secret, 'utf-8'), msg=body, digestmod=hashlib.sha1)
    
#     # Compare the HMAC signature with the provided signature
#     return hmac.compare_digest(mac.digest(), sig)

# # Example usage within a Flask route
# @app.route('/', methods=['POST'])
# def webhook():
#     """
#     Webhook endpoint that verifies GitHub webhook signatures.
#     """
#     body = request.data
#     if verify_event(request.headers, body, GIT_SECRET):
#         # Signature verified
#         print("Signature verified.")
#         return jsonify({'message': 'Signature verified.'}), 200
#     else:
#         # Signature verification failed
#         print("Signature verification failed.")
#         return jsonify({'message': 'Signature verification failed.'}), 403

# if __name__ == '__main__':
#     app.run(port=5000, debug=True) 