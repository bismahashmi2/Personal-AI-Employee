"""
LinkedIn OAuth 2.0 Callback Server
Handles the OAuth callback and stores the access token.
Run this script to authenticate with LinkedIn.
"""
import os
import json
import secrets
import webbrowser
import logging
import threading
from pyngrok import ngrok
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, render_template_string
import requests
from requests_oauthlib import OAuth2Session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script lives
SCRIPT_DIR = Path(__file__).parent.resolve()

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# LinkedIn OAuth2 configuration
CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', "http://localhost:8000/callback")

# OAuth2 scopes needed
# IMPORTANT: For personal posting only (Silver Tier):
# - w_member_social: Post as member (available with Share on LinkedIn product)
# - openid: OpenID Connect authentication
# - profile: Access to profile information
SCOPE = [
    'openid',                   # OpenID Connect
    'profile',                  # Profile access
    'w_member_social',          # Post as member
]

# Store the auth code (in-memory, single user)
auth_code = None
token_saved = threading.Event()

# HTML template for the callback page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn OAuth - Authorization Status</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #0077B5 0%, #00a0dc 100%);
            color: white;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        .checkmark {
            font-size: 48px;
            margin-bottom: 20px;
        }
        h1 { margin: 0 0 10px 0; }
        p { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="checkmark">✅</div>
        <h1>Authorization Successful!</h1>
        <p>You can now close this window and return to the application.</p>
    </div>
</body>
</html>
"""

@app.route('/callback')
def callback():
    """Handle OAuth callback from LinkedIn."""
    global auth_code

    error = request.args.get('error')
    if error:
        return f"""
        <h1>Authorization Failed</h1>
        <p>Error: {error}</p>
        <p>Description: {request.args.get('error_description', 'No description provided')}</p>
        """, 400

    auth_code = request.args.get('code')
    state = request.args.get('state')

    if not auth_code:
        return "<h1>Error: No authorization code received</h1>", 400

    print(f"\n✅ Received authorization code: {auth_code[:20]}...")
    print("💾 Exchanging code for access token...")

    # Exchange code for token
    try:
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

        # Calculate expiration
        expires_in = token_data.get('expires_in', 5184000)  # Default: 2 months
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Create token structure
        full_token = {
            'access_token': token_data['access_token'],
            'expires_in': expires_in,
            'expires_at': expires_at.isoformat(),
            'refresh_token': token_data.get('refresh_token'),
            'scope': token_data.get('scope', ' '.join(SCOPE)),
            'created_at': datetime.now().isoformat(),
        }

        # Save token to file (use linkedin_token.json to avoid conflict with Gmail)
        token_path = SCRIPT_DIR / 'linkedin_token.json'
        try:
            token_path.write_text(json.dumps(full_token, indent=2))
            logger.info(f"Successfully wrote token to: {token_path}")
        except Exception as write_error:
            logger.error(f"Failed to write token file: {write_error}")
            raise

        print(f"✅ Access token saved to {token_path}")
        print(f"   Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n🎉 LinkedIn OAuth setup complete! You can now use the LinkedIn API.")

        # Signal that token has been saved
        token_saved.set()

    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        return f"<h1>Error</h1><p>Failed to exchange code: {e}</p>", 500

    return render_template_string(HTML_TEMPLATE)


def get_auth_url():
    """Generate the LinkedIn authorization URL."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in environment variables")

    authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = oauth.authorization_url(
        authorization_base_url,
        prompt='consent'  # Force consent screen for first-time auth
    )
    return authorization_url, state


def main():
    """Main entry point for OAuth setup."""
    print("=" * 60)
    print("🔗 LinkedIn OAuth 2.0 Setup")
    print("=" * 60)

    # Check credentials
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: Missing credentials!")
        print("   Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in your .env file")
        print("\n   Copy from LinkedIn Developer Portal:")
        print("   Settings tab → Authentication keys")
        return

    # Check for existing token
    token_path = SCRIPT_DIR / 'linkedin_token.json'
    if token_path.exists():
        response = input("\n⚠️  linkedin_token.json already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return

    # Generate auth URL
    print("\n1. Generating authorization URL...")
    auth_url, state = get_auth_url()
    print(f"   URL: {auth_url}\n")

    # Start Flask server
    print("2. Starting local server on http://localhost:8000/callback")
    print("   (Press Ctrl+C to cancel)\n")

    def run_flask():
        app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(2)

    # Open browser
    print("3. Opening browser for authorization...")
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"   Could not open browser automatically: {e}")
        # WSL-specific guidance
        print("\n   On WSL, you can also:")
        print("   - Copy and paste this URL into your Windows browser:")
        print(f"   {auth_url}")
        print("   - Or run: explorer.exe \"{auth_url}\"")
        print()

    print("4. Waiting for authorization... (check your browser)")
    print("=" * 60)

    # Keep main thread alive until token is received
    try:
        while not token_saved.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n❌ OAuth setup cancelled by user.")
        return

    print("\n✅ OAuth flow complete! linkedin_token.json has been created.")
    print("   You can now close the Flask server (Ctrl+C).")


if __name__ == '__main__':
    main()
