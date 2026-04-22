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

# Custom UI Tweaks (Minimal & Native)
st.markdown("""
    <style>
        /* Center the top padding a bit more */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 800px;
        }
        /* Make the audio player look nice */
        .stAudio {
            margin-top: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        /* Hide sidebar divider */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("<h1 style='text-align: center; color: #8B5CF6; font-size: 3.5rem; font-weight: 800; margin-bottom: 0; padding-bottom: 0;'>🎙️ Blog to Podcast AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.25rem; font-weight: 400; margin-top: 0.5rem; margin-bottom: 3rem;'>Transform any written blog post into an engaging, high-quality audio podcast in seconds.</p>", unsafe_allow_html=True)

# API Keys (Sidebar)
with st.sidebar:
    st.header("⚙️ Configuration")
    st.caption("Enter your API keys to unlock all features.")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Required for summarizing text (GPT-4o)")
    elevenlabs_key = st.text_input("ElevenLabs API Key", type="password", help="Required for generating lifelike voices")
    firecrawl_key = st.text_input("Firecrawl API Key", type="password", help="Required for scraping blog content")
    
    st.divider()
    
    st.subheader("ℹ️ How it works")
    st.markdown("""
    <div style='color: #94A3B8; font-size: 0.95rem; line-height: 1.6;'>
    <b>1. Scraping:</b> Extracts clean content from any blog URL using Firecrawl.<br><br>
    <b>2. Summarizing:</b> OpenAI's GPT-4o analyzes and crafts an engaging podcast script.<br><br>
    <b>3. Audio Generation:</b> ElevenLabs converts the script into natural, expressive speech.
    </div>
    """, unsafe_allow_html=True)

# Main Input Section
st.markdown("### 🔗 Enter Blog URL")
url = st.text_input("URL", label_visibility="collapsed", placeholder="e.g. https://example.com/my-awesome-blog-post")

st.write("") # Spacer

# Generate Button Logic
button_disabled = not all([openai_key, elevenlabs_key, firecrawl_key])

if button_disabled:
    st.info("💡 **Almost ready!** Please provide your OpenAI, ElevenLabs, and Firecrawl API keys in the sidebar to continue.", icon="ℹ️")

if st.button("🎙️ Generate Podcast Episode", type="primary", disabled=button_disabled, use_container_width=True):
    if not url.strip():
        st.error("Please enter a valid blog URL to proceed.", icon="🚨")
    else:
        # Progress UI
        status_container = st.empty()
        
        try:
            # Set API keys
            os.environ["OPENAI_API_KEY"] = openai_key
            os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
            
            with status_container.status("🚀 Processing your request...", expanded=True) as status:
                st.write("🔍 Scraping blog content and analyzing text...")
                
                # Create agent for scraping and summarization
                agent = Agent(
                    name="Blog Summarizer",
                    model=OpenAIChat(id="gpt-4o"),
                    tools=[FirecrawlTools()],
                    instructions=[
                        "Scrape the blog URL and create a concise, engaging summary (max 2000 characters) suitable for a podcast.",
                        "The summary should be conversational, engaging, and capture the main points perfectly for listening. Start with a catchy hook."
                    ],
                )
                
                # Get summary
                response: RunOutput = agent.run(f"Scrape and summarize this blog for a podcast: {url}")
                summary = response.content if hasattr(response, 'content') else str(response)
                
                if summary:
                    st.write("🎙️ Generating lifelike audio with ElevenLabs...")
                    
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
                    
                    status.update(label="✨ Podcast generated successfully!", state="complete", expanded=False)
                    
            # Display results outside the status spinner
            st.success("Your episode is ready! 🎧", icon="✅")
            st.audio(audio_bytes, format="audio/mp3")
            
            # Action buttons side-by-side
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 Download Episode (.mp3)",
                    data=audio_bytes,
                    file_name="podcast_episode.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            
            # Show summary
            with st.expander("📄 View Podcast Script"):
                st.write(summary)
                
        except Exception as e:
            status_container.error(f"**An error occurred:** {str(e)}", icon="❌")


