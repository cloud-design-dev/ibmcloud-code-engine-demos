#!/usr/bin/env python3
"""Module providing functions to verify GitHub webhook signatures."""
import os
import hmac
import hashlib
from flask import Flask, request, jsonify


app = Flask(__name__)
# Fetch the GitHub secret from environment variables
git_secret = os.environ.get("GIT_SECRET")

def verify_event(req_headers, body, secret):
    """
    Verify the GitHub webhook event by checking its signature.

    Parameters:
    - req_headers: The headers from the incoming request.
    - body: The raw body of the incoming request as bytes.
    - secret: The secret used to verify the HMAC signature.

    Returns:
    - A boolean indicating whether the verification succeeded.
    """
    # Extract the signature from the request headers
    sig_header = req_headers.get('X-Hub-Signature')
    if not sig_header or len(sig_header) != 45 or not sig_header.startswith('sha1='):
        return False

    # Decode the hex signature
    sig = bytes.fromhex(sig_header[5:])
    # Create a new HMAC object using the secret and the SHA1 algorithm
    mac = hmac.new(bytes(secret, 'utf-8'), msg=body, digestmod=hashlib.sha1)

    digest = hmac.compare_digest(mac.digest(), sig)
    print(digest)
    # Compare the HMAC signature with the provided signature
    return digest

# Example usage within a Flask route
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint that verifies GitHub webhook signatures.
    """
    try:
        body = request.data
        headers = request.headers
        print(headers)
        verify_event(request.headers, body, git_secret)
        return jsonify({'message': 'Received and verified the event'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(port=5000, debug=True)
