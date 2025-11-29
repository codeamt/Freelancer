# Google OAuth Setup Guide

To enable Google OAuth authentication in your application, follow these steps:

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (if not already enabled)

## 2. Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" for User Type (or "Internal" if using G Suite)
3. Fill in the required application information:
   - App name
   - User support email
   - Developer contact information
4. Add the following scopes:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
5. Add your email to test users (required for apps in testing mode)

## 3. Create OAuth Client Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Set the following URLs:
   - **Authorized JavaScript origins**: `http://localhost:8000`
   - **Authorized redirect URIs**: `http://localhost:8000/auth/google/callback`
5. Click "Create" and note down your Client ID and Client Secret

## 4. Configure Environment Variables

Create a `.env` file in the root of your project with the following content:

```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

Replace `your_google_client_id_here` and `your_google_client_secret_here` with the values from step 3.

## 5. Install Required Dependencies

Make sure you have the required OAuth dependencies installed:

```
pip install fasthtml[oauth]
```

## 6. Test the Integration

1. Start your application
2. Navigate to the login page
3. Click the "Sign in with Google" button
4. You should be redirected to Google's OAuth consent screen
5. After authentication, you should be redirected back to your application

## Troubleshooting

- If you get an "invalid redirect URI" error, make sure the redirect URI in your Google Cloud Console exactly matches the one in your application
- If OAuth is not working, check that both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables are set correctly
- For production deployment, update the redirect URIs to match your production domain
