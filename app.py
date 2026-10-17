import streamlit as st
import json
from modules.model_setup import (
    MODEL_NAME,
    ollama_is_running,
    model_is_installed,
    pull_model_with_progress_bar,
)
from modules.listing_generator import generate_listing

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Listing Writer — Local AI",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ALLOWED_TYPES = ["jpg", "jpeg", "png"]

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "startup_done" not in st.session_state:
    st.session_state.startup_done = False
if "last_result" not in st.session_state:
    st.session_state.last_result = ""
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "speaking" not in st.session_state:
    st.session_state.speaking = False

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 2rem;
            max-width: 780px;
        }

        .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.55rem 1.2rem;
        }

        /* Status boxes */
        .status-box {
            padding: 1rem 1.2rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }
        .status-ok    { background: #e8f5e9; border-left: 4px solid #2e7d32; color: #1b5e20; }
        .status-warn  { background: #fff8e1; border-left: 4px solid #f9a825; color: #7f6000; }
        .status-error { background: #ffebee; border-left: 4px solid #c62828; color: #8e0000; }

        /* Markdown output styling */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            margin-top: 1.2rem;
            margin-bottom: 0.4rem;
            font-weight: 600;
        }
        .stMarkdown p {
            margin-bottom: 0.9rem;
            line-height: 1.65;
        }
        .stMarkdown ul, .stMarkdown ol {
            margin-bottom: 0.9rem;
            padding-left: 1.4rem;
        }
        .stMarkdown li {
            margin-bottom: 0.3rem;
            line-height: 1.55;
        }
        .stMarkdown strong {
            font-weight: 600;
        }
        .stMarkdown code {
            background: rgba(127,127,127,0.15);
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            font-size: 0.88em;
        }
        .stMarkdown hr {
            margin: 1.5rem 0;
            border: none;
            border-top: 1px solid rgba(127,127,127,0.25);
        }

        /* Animated dots for the custom status box */
        .dots span {
            animation: blink 1.4s infinite both;
        }
        .dots span:nth-child(2) { animation-delay: 0.2s; }
        .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink {
            0%, 80%, 100% { opacity: 0.2; }
            40% { opacity: 1; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def validate_upload(uploaded_file) -> bool:
    if uploaded_file is None:
        return False
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ALLOWED_TYPES:
        st.error(
            f"Unsupported file type: **.{ext}**. "
            f"Please upload one of: {', '.join(ALLOWED_TYPES)}."
        )
        return False
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Image is too large (max 10 MB). Please compress it and try again.")
        return False
    return True


# ---------------------------------------------------------------------------
# One-time startup check
# ---------------------------------------------------------------------------
if not st.session_state.startup_done:
    st.title("🛍️ Listing Writer")
    st.caption("Generate Etsy/eBay listings locally — your photos never leave your laptop.")

    if not ollama_is_running():
        st.markdown(
            '<div class="status-box status-error">'
            '<b>Ollama is not running.</b><br>'
            'Start the Ollama background service, then reload this page.<br><br>'
            '<b>How to start it:</b><br>'
            '• <b>Windows / macOS:</b> open the Ollama app from your Start menu or Applications.<br>'
            '• <b>Linux:</b> run <code>sudo systemctl start ollama</code> in a terminal.<br><br>'
            'Once it is running, refresh this page.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    if model_is_installed(MODEL_NAME):
        st.markdown(
            f'<div class="status-box status-ok">'
            f'✅ <b>{MODEL_NAME}</b> is installed and Ollama is running. Ready to go.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.session_state.startup_done = True
        st.rerun()

    st.markdown(
        f'<div class="status-box status-warn">'
        f'⚠️ <b>{MODEL_NAME}</b> is not installed yet. '
        f'It is a one-time download (~3.3 GB) and everything runs offline afterwards.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Create a single placeholder for the skip message
    skip_msg_placeholder = st.empty()

    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("⬇️ Download model now", type="primary"):
            # Force the skip message to disappear immediately
            skip_msg_placeholder.empty()
            st.session_state.show_skip = False
            
            if pull_model_with_progress_bar(MODEL_NAME):
                st.session_state.startup_done = True
                st.rerun()
                
    with col2:
        if st.button("Skip for now"):
            st.session_state.show_skip = True

    # Only render the skip message if the flag is True
    if st.session_state.get("show_skip", False):
        skip_msg_placeholder.info(
            "You can install the model later by running "
            f"`ollama pull {MODEL_NAME}` in a terminal."
        )

    st.stop()

# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
st.title("🛍️ Listing Writer")
st.caption("Generate Etsy/eBay listings locally — your photos never leave your laptop.")

with st.sidebar:
    st.markdown(f"**Model:** `{MODEL_NAME}`")
    st.markdown("**Status:** ✅ Ready")
    st.markdown("---")
    st.markdown("This app runs entirely on your machine. Turn off WiFi and it still works.")
    if st.button("🔄 Start over (clear result)"):
        st.session_state.last_result = ""
        st.session_state.speaking = False
        st.session_state.uploader_key += 1
        st.rerun()

# ----- Input form -----------------------------------------------------------
st.subheader("1. Upload a product photo")

uploaded = st.file_uploader(
    "Choose an image",
    type=ALLOWED_TYPES,
    accept_multiple_files=False,
    help="Accepted formats: JPG, JPEG, PNG (max 10 MB).",
    key=f"uploader_{st.session_state.uploader_key}",
)

if uploaded is not None and validate_upload(uploaded):
    st.image(uploaded, caption=uploaded.name, width="stretch")

st.subheader("2. Describe your voice")

style_presets = [
    "Casual & warm, uses emojis, friendly",
    "Professional and concise, no emojis",
    "Vintage reseller tone, emphasizes condition",
    "Luxury / premium, elegant wording",
    "Playful, fun, uses light humor",
    "Custom (type your own below)",
]

style_choice = st.selectbox("Pick a style", style_presets, index=0)

custom_style = ""
if style_choice == "Custom (type your own below)":
    custom_style = st.text_area(
        "Your custom voice",
        placeholder="e.g. Minimalist, calm, zero exclamation marks, speaks to design-conscious buyers.",
        max_chars=300,
    )

style_prompt = custom_style.strip() if style_choice.startswith("Custom") else style_choice


# ---------------------------------------------------------------------------
# 3. Generate — uses st.form so double-clicks coalesce into one submit
# ---------------------------------------------------------------------------
st.subheader("3. Generate")

with st.form("generate_form", clear_on_submit=False):
    submitted = st.form_submit_button("✨ Generate listing", type="primary")

if submitted:
    # Guards
    if not ollama_is_running():
        st.error("Ollama stopped responding. Please restart the Ollama service and try again.")
        st.stop()

    if uploaded is None or not validate_upload(uploaded):
        st.stop()

    if not style_prompt:
        st.error("Please provide a style prompt (pick a preset or type a custom one).")
        st.stop()

    # Reset previous result so the render block below doesn't show stale output
    st.session_state.last_result = ""
    st.session_state.speaking = False

    # Status + streaming placeholders
    status_ph = st.empty()
    output_ph = st.empty()
    full_output = ""

    status_ph.markdown(
        '<div class="status-box status-warn">'
        ' ⏳ Reading the photo and writing your listing'
        '<span class="dots"><span>.</span><span>.</span><span>.</span></span>'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        image_bytes = uploaded.read()

        for chunk in generate_listing(image_bytes, style_prompt):
            full_output += chunk
            output_ph.markdown(full_output)

        if not full_output:
            status_ph.markdown(
                '<div class="status-box status-error">'
                '⚠️ Model returned an empty response. Try another photo or style.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            status_ph.markdown(
                '<div class="status-box status-ok">✅ Listing ready</div>',
                unsafe_allow_html=True,
            )
            st.session_state.last_result = full_output.strip()

    except Exception as e:
        status_ph.markdown(
            f'<div class="status-box status-error">❌ Generation failed: {e}</div>',
            unsafe_allow_html=True,
        )

    st.rerun()


# ---------------------------------------------------------------------------
# 4. Render result from session_state (survives any button click)
# ---------------------------------------------------------------------------
if st.session_state.last_result:
    st.subheader("4. Your listing")

    st.markdown(st.session_state.last_result)
    st.markdown("-----")

    # --- Buttons row ---
    col_a, col_c = st.columns(2)

    with col_a:
        st.download_button(
            "⬇️ Download .txt",
            data=st.session_state.last_result,
            file_name="listing.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_c:
        if st.button("🆕 New listing", use_container_width=True):
            st.session_state.last_result = ""
            st.session_state.speaking = False
            st.session_state.uploader_key += 1
            st.rerun()

    # --- Read aloud: rendered inside an iframe so speechSynthesis works ---
    safe = json.dumps(st.session_state.last_result)
    st.components.v1.html(
        f"""
        <div style="font-family: sans-serif;">
          <button id="speak-btn" style="
            background:#ff4b4b;color:white;border:none;border-radius:10px;
            padding:8px 16px;font-weight:600;cursor:pointer;font-size:14px;">
            🔊 Read aloud
          </button>
          <button id="stop-btn" style="
            background:#444;color:white;border:none;border-radius:10px;
            padding:8px 16px;font-weight:600;cursor:pointer;font-size:14px;
            margin-left:8px;">
            ⏹ Stop
          </button>
        </div>
        <script>
          const text = {safe};
          document.getElementById('speak-btn').onclick = () => {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 1.0;
            window.speechSynthesis.speak(u);
          }};
          document.getElementById('stop-btn').onclick = () => {{
            window.speechSynthesis.cancel();
          }};
        </script>
        """,
        height=60,
    )

    st.caption("Tip: click **New listing** to upload another photo without restarting the app.")