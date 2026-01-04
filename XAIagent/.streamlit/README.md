# Streamlit Configuration

## Local Development

**1. Copy template:**
```bash
cp secrets.toml.template secrets.toml
```

**2. Add your OpenAI API key to `secrets.toml`:**
```toml
OPENAI_API_KEY = "sk-proj-YOUR-KEY-HERE"
OPENAI_MODEL = "gpt-4o-mini"
```

⚠️ **Never commit `secrets.toml`** - it's already in `.gitignore`

## Streamlit Cloud Deployment

**Add secrets via dashboard:**
1. Go to https://share.streamlit.io
2. Open your app → Settings → Secrets
3. Add:
```toml
OPENAI_API_KEY = "sk-proj-YOUR-KEY-HERE"
OPENAI_MODEL = "gpt-4o-mini"
```

## Configuration Files

- `config.toml` - UI theme settings
- `secrets.toml.template` - Template for API keys
- `secrets.toml` - Your actual keys (gitignored)
# Create secrets file
cp .streamlit/secrets.toml.template .streamlit/secrets.toml

# Edit with real keys
nano .streamlit/secrets.toml

# Run app
streamlit run app_v1.py
```

## Verification

Once deployed, test the LLM validation:
1. Fill out the loan application
2. Enter invalid data (e.g., "gg" for age)
3. You should see a warm, friendly LLM-generated message like:
   - "Oh no, it looks like that input didn't quite fit! 😊"
   - "I see that might have been a little mix-up!"

If you see hardcoded messages instead, check:
- Secrets are correctly added in Streamlit Cloud dashboard
- `HICXAI_GENAI = "on"` is set
- `OPENAI_API_KEY` is valid and has billing enabled
