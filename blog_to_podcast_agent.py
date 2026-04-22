import os
from uuid import uuid4
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from elevenlabs import ElevenLabs
import streamlit as st

# Streamlit Setup
st.set_page_config(page_title="Blog to Podcast AI", page_icon="🎙️", layout="centered")

# Custom CSS for Professional, Theme-Suitable UI
custom_css = """
<style>
    /* Main container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header/Title styling */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-bottom: 10px;
        margin-bottom: 0px;
    }
    
    /* Subtitle/Text styling */
    .subtitle {
        color: #a0aec0;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(118, 75, 162, 0.4);
        border: none;
        color: white;
    }
    .stButton>button:disabled {
        background: #4a5568;
        color: #a0aec0;
        transform: none;
        box-shadow: none;
    }

    /* Audio player wrapper */
    .stAudio {
        margin-top: 20px;
        margin-bottom: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Card-like container for URL input */
    .url-container {
        background-color: #1e212b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #2d3748;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Main Header
st.markdown("<h1>🎙️ Blog to Podcast AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Transform any written blog post into an engaging, high-quality audio podcast in seconds.</div>", unsafe_allow_html=True)

# API Keys (Sidebar)
st.sidebar.markdown("### ⚙️ Configuration")
st.sidebar.markdown("Enter your API keys to get started.")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Required for text summarization")
elevenlabs_key = st.sidebar.text_input("ElevenLabs API Key", type="password", help="Required for voice generation")
firecrawl_key = st.sidebar.text_input("Firecrawl API Key", type="password", help="Required for blog scraping")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ How it works")
st.sidebar.info(
    "1. **Scraping**: Firecrawl extracts the content from the blog URL.\n"
    "2. **Summarizing**: OpenAI GPT-4o crafts an engaging podcast script.\n"
    "3. **Audio Gen**: ElevenLabs brings the script to life with natural voices."
)

# Blog URL Input Area
st.markdown("<div class='url-container'>", unsafe_allow_html=True)
url = st.text_input("🔗 Paste Blog URL:", placeholder="https://example.com/blog-post")
st.markdown("</div>", unsafe_allow_html=True)

# Generate Button
st.markdown("<br>", unsafe_allow_html=True)
button_disabled = not all([openai_key, elevenlabs_key, firecrawl_key])

if button_disabled:
    st.warning("⚠️ Please provide all API keys in the sidebar to enable podcast generation.")

if st.button("🎙️ Generate Podcast Episode", disabled=button_disabled):
    if not url.strip():
        st.error("Please enter a valid blog URL.")
    else:
        with st.spinner("🔄 Scraping blog and generating podcast script..."):
            try:
                # Set API keys
                os.environ["OPENAI_API_KEY"] = openai_key
                os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
                
                # Create agent for scraping and summarization
                agent = Agent(
                    name="Blog Summarizer",
                    model=OpenAIChat(id="gpt-4o"),
                    tools=[FirecrawlTools()],
                    instructions=[
                        "Scrape the blog URL and create a concise, engaging summary (max 2000 characters) suitable for a podcast.",
                        "The summary should be conversational, engaging, and capture the main points perfectly for listening."
                    ],
                )
                
                # Get summary
                response: RunOutput = agent.run(f"Scrape and summarize this blog for a podcast: {url}")
                summary = response.content if hasattr(response, 'content') else str(response)
                
                if summary:
                    with st.spinner("🎙️ Generating lifelike audio with ElevenLabs..."):
                        # Initialize ElevenLabs client and generate audio
                        client = ElevenLabs(api_key=elevenlabs_key)
                        
                        # Generate audio using text_to_speech.convert
                        audio_generator = client.text_to_speech.convert(
                            text=summary,
                            voice_id="JBFqnCBsd6RMkjVDRZzb",
                            model_id="eleven_multilingual_v2"
                        )
                        
                        # Collect audio chunks if it's a generator
                        audio_chunks = []
                        for chunk in audio_generator:
                            if chunk:
                                audio_chunks.append(chunk)
                        audio_bytes = b"".join(audio_chunks)
                        
                        # Display audio
                        st.success("✨ Podcast generated successfully! 🎧")
                        st.audio(audio_bytes, format="audio/mp3")
                        
                        # Download button
                        st.download_button(
                            label="💾 Download Podcast (.mp3)",
                            data=audio_bytes,
                            file_name="podcast_episode.mp3",
                            mime="audio/mp3"
                        )
                        
                        # Show summary
                        with st.expander("📄 View Podcast Script (Summary)"):
                            st.write(summary)
                else:
                    st.error("Failed to generate summary from the blog content.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

