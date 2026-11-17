import asyncio
import json
import os
from pathlib import Path
from skills import SkillRegistry
from settings_store import read_settings, write_settings
from diagnostics import ollama_models, validate_service_url
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
import streamlit as st
import httpx
from dotenv import load_dotenv

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPToolset


MODEL_REQUEST_ERROR = "The model request failed. Check the model and server settings."


class ChatMessage(BaseModel):
    """Structure for chat messages"""
    role: Literal["user", "assistant"] = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")


def model_history(messages: List[ChatMessage]):
    """Convert visible chat turns without promoting their text to instructions."""
    return [
        ModelRequest(parts=[UserPromptPart(m.content)]) if m.role == "user"
        else ModelResponse(parts=[TextPart(m.content)])
        for m in messages
    ]


DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant powered by Pydantic AI and running on Ollama.
You provide accurate, helpful, and engaging responses to user questions.
Always be polite, informative, and concise in your responses.
If you're uncertain about something, acknowledge the uncertainty.

You have access to external tools through MCP (Model Context Protocol) when available.
When using tools, always explain what you're doing and what the tool returned.

When responding to complex questions, feel free to show your thinking process by using phrases like:
- "Let me think about this..."
- "I need to consider..."
- "First, I should..."
- "Let me analyze..."

This helps users understand your reasoning process."""


class PydanticAIWebApp:
    """Main application class for the Pydantic AI Web UI"""
    
    def __init__(self, system_prompt: Optional[str] = None, model_name: str = 'qwen3:14b', 
                 ollama_url: str = 'http://localhost:11434', mcp_url: Optional[str] = None, 
                 mcp_token: Optional[str] = None):
        # Load environment variables
        load_dotenv()
        
        # Store settings
        self.model_name = model_name
        self.ollama_url = ollama_url
        
        # Initialize Ollama model with OpenAI compatibility
        ollama_base_url = f"{ollama_url}/v1"
        self.ollama_model = OpenAIChatModel(
            model_name=model_name,
            provider=OpenAIProvider(base_url=ollama_base_url, api_key="ollama")
        )
        
        # None uses environment defaults; an explicit empty URL disables MCP.
        self.mcp_url = os.getenv('MCP_SERVER_URL', '') if mcp_url is None else mcp_url
        self.mcp_token = os.getenv('MCP_BEARER_TOKEN', '') if mcp_token is None else mcp_token
        self._configure_mcp()

        # Default system prompt if none provided
        
        self.system_prompt = DEFAULT_SYSTEM_PROMPT if system_prompt is None else system_prompt
        self.skills = SkillRegistry(Path(__file__).parent / ".agents" / "skills")
        self.agent = self._create_agent()

    def _configure_mcp(self):
        self.mcp_server = None
        if not self.mcp_url:
            self.mcp_status = "⚠️ MCP is disabled."
            return
        try:
            url = validate_service_url(self.mcp_url)
            headers = {"Authorization": f"Bearer {self.mcp_token}"} if self.mcp_token else {}
            self.mcp_server = MCPToolset(url, headers=headers, init_timeout=10, read_timeout=30)
            self.mcp_status = "✅ MCP configured; connection has not been tested."
        except Exception:
            self.mcp_status = "❌ Invalid MCP configuration. Check the URL and authentication settings."

    def _create_agent(self):
        def activate_skill(name: str) -> str:
            """Load task instructions by name from the available skill catalog. Does not execute scripts."""
            return self.skills.activate(name)

        return Agent(
            model=self.ollama_model,
            system_prompt=self.system_prompt,
            instructions=self.skills.catalog(),
            tools=[activate_skill],
            toolsets=[self.mcp_server] if self.mcp_server else [],
        )

    def update_system_prompt(self, new_system_prompt: str):
        """Update the system prompt and recreate the agent"""
        self.system_prompt = new_system_prompt
        self.agent = self._create_agent()

    def update_settings(self, model_name: str = None, ollama_url: str = None, 
                       mcp_url: str = None, mcp_token: str = None, system_prompt: str = None):
        """Update any combination of settings and recreate the agent"""
        # Update model settings if provided
        if model_name and model_name != self.model_name:
            self.model_name = model_name
            
        if ollama_url and ollama_url != self.ollama_url:
            self.ollama_url = ollama_url
            
        # Recreate Ollama model if model or URL changed
        if model_name or ollama_url:
            ollama_base_url = f"{self.ollama_url}/v1"
            self.ollama_model = OpenAIChatModel(
                model_name=self.model_name,
                provider=OpenAIProvider(base_url=ollama_base_url, api_key="ollama")
            )
        
        if mcp_url is not None or mcp_token is not None:
            if mcp_url is not None:
                self.mcp_url = mcp_url
            if mcp_token is not None:
                self.mcp_token = mcp_token
            self._configure_mcp()

        # Update system prompt if provided
        if system_prompt is not None:
            self.system_prompt = system_prompt
        
        self.agent = self._create_agent()

    async def get_agent_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """
        Get response from the agent
        
        Args:
            message: User's input message
            conversation_history: Previous conversation messages
            
        Returns:
            Response string
        """
        try:
            # Use MCP server context if available
            if self.mcp_server:
                async with self.agent:
                    result = await self.agent.run(user_prompt=message, message_history=model_history(conversation_history))
                    return str(result.output)
            else:
                # Get response from agent without MCP servers
                result = await self.agent.run(user_prompt=message, message_history=model_history(conversation_history))
                return str(result.output)
                
        except Exception as e:
            return MODEL_REQUEST_ERROR
    
    async def get_streaming_response(self, message: str, conversation_history: List[ChatMessage]):
        """Stream text, separating only explicit leading think tags."""
        from streaming import split_output
        sent_thinking = ""
        sent_response = ""
        full_content = ""
        try:
            async with self.agent:
                async with self.agent.run_stream(user_prompt=message, message_history=model_history(conversation_history)) as result:
                    async for full_content in result.stream_text():
                        thinking, response = split_output(full_content)
                        for kind, content, previous in (
                            ("thinking", thinking, sent_thinking),
                            ("response", response, sent_response),
                        ):
                            if len(content) > len(previous):
                                yield {"type": kind, "content": content[len(previous):], "status": "streaming"}
                        sent_thinking, sent_response = thinking, response
                    thinking, response = split_output(full_content, final=True)
                    for kind, content, previous in (
                        ("thinking", thinking, sent_thinking),
                        ("response", response, sent_response),
                    ):
                        if len(content) > len(previous):
                            yield {"type": kind, "content": content[len(previous):], "status": "streaming"}
            yield {"type": "thinking_complete", "content": "", "status": "complete"}
            yield {"type": "response_complete", "content": "", "status": "complete"}
        except Exception:
            yield {"type": "error", "content": MODEL_REQUEST_ERROR, "status": "error"}


def save_settings_to_file(settings: Dict[str, Any], filename: str = "orion_settings.json"):
    """Save settings to a JSON file"""
    try:
        write_settings(settings, filename)
        return True
    except Exception as e:
        st.error("Failed to save settings. Check local file access and available disk space.")
        return False


def load_settings_from_file(filename: str = "orion_settings.json") -> Dict[str, Any]:
    """Load settings from a JSON file"""
    load_dotenv()
    default_settings = {
        "ollama_model": "qwen3:14b",
        "ollama_url": "http://localhost:11434",
        "mcp_url": os.getenv("MCP_SERVER_URL", ""),
        "mcp_token": os.getenv("MCP_BEARER_TOKEN", ""),
        "system_prompt": DEFAULT_SYSTEM_PROMPT
    }
    
    try:
        return read_settings(filename, default_settings)
    except (OSError, ValueError):
        st.warning("Could not load local settings; using defaults.")
        return default_settings


def get_available_ollama_models(server_url: str = "http://localhost:11434"):
    try:
        return ollama_models(server_url)
    except Exception:
        return []


def check_ollama_connection(server_url: str = "http://localhost:11434", model_name: str = "qwen3:14b"):
    try:
        models = ollama_models(server_url)
        if model_name in models:
            return True, f"✅ Ollama responded and {model_name} is listed."
        return False, "⚠️ Ollama responded, but the selected model is not listed."
    except Exception:
        return False, "❌ Model discovery failed. Check the Ollama URL and service."


def auto_focus_chat_input():
    """Inject JavaScript to auto-focus the chat input"""
    st.markdown("""
    <script>
    // Auto-focus chat input - more aggressive approach
    (function() {
        let focusAttempts = 0;
        const maxAttempts = 100;
        
        function tryFocusInput() {
            if (focusAttempts >= maxAttempts) {
                console.log('Max focus attempts reached');
                return;
            }
            
            // Try multiple selectors
            const selectors = [
                'textarea[data-testid="stChatInputTextArea"]',
                'textarea[placeholder="Type your message here..."]',
                'textarea[aria-label="Type your message here..."]',
                'textarea[placeholder*="message"]',
                'div[data-testid="stChatInput"] textarea'
            ];
            
            for (let selector of selectors) {
                const input = document.querySelector(selector);
                if (input && input.offsetParent !== null) { // Check if element is visible
                    input.focus();
                    input.click(); // Also trigger click in case focus alone doesn't work
                    console.log('Successfully focused with selector:', selector);
                    return true;
                }
            }
            
            focusAttempts++;
            setTimeout(tryFocusInput, 50); // Try again in 50ms
            return false;
        }
        
        // Start trying immediately
        tryFocusInput();
        
        // Try again when DOM changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    setTimeout(tryFocusInput, 10);
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also try when document is ready and loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', tryFocusInput);
        } else {
            tryFocusInput();
        }
        
        window.addEventListener('load', tryFocusInput);
        
        // Try every second for the first 10 seconds as a fallback
        let intervalCount = 0;
        const focusInterval = setInterval(function() {
            tryFocusInput();
            intervalCount++;
            if (intervalCount >= 20) { // Stop after 10 seconds
                clearInterval(focusInterval);
            }
        }, 500);
    })();
    </script>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Load settings from file (this will initialize all settings)
    if "settings_loaded" not in st.session_state:
        saved_settings = load_settings_from_file()
        
        # Initialize all settings from saved file or defaults
        st.session_state.system_prompt = saved_settings["system_prompt"]
        st.session_state.ollama_model = saved_settings["ollama_model"]
        st.session_state.ollama_url = saved_settings["ollama_url"]
        
        # Saved values, including empty strings, override environment defaults.
        st.session_state.mcp_url = saved_settings["mcp_url"]
        st.session_state.mcp_token = saved_settings["mcp_token"]
        
        st.session_state.settings_loaded = True
    
    # Runtime-only settings (not persisted)
    if "available_models" not in st.session_state:
        st.session_state.available_models = []
    if "available_models_url" not in st.session_state:
        st.session_state.available_models_url = None
    
    # App instance
    if "app" not in st.session_state:
        st.session_state.app = PydanticAIWebApp(
            system_prompt=st.session_state.system_prompt,
            model_name=st.session_state.ollama_model,
            ollama_url=st.session_state.ollama_url,
            mcp_url=st.session_state.mcp_url,
            mcp_token=st.session_state.mcp_token
        )
    
    # Connection tracking
    if "connection_checked" not in st.session_state:
        st.session_state.connection_checked = False
    if "connection_status" not in st.session_state:
        st.session_state.connection_status = None


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="🌟 Orion - AI Chat Assistant",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Spotify-inspired dark theme compatible CSS
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    
    /* Fixed header styling */
    .st-emotion-cache-8fdueu h3 {
        font-size: 1.75rem;
        padding: 0.75rem 0px 1rem;
        position: fixed;
        top: 12px;
        z-index: 1000000000000000000;
        font-weight: 300;
    }
    
    /* Thinking UI Styles - Spotify green theme */
    .thinking-status {
        background: linear-gradient(90deg, #1DB954 0%, #1ED760 100%);
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 14px;
        margin-bottom: 10px;
        display: inline-block;
    }
    
    .thinking-expander {
        border: 1px solid #282828;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .thinking-content {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #1DB954;
    }
    
    /* Response content styling */
    .response-content {
        margin-top: 10px;
        line-height: 1.6;
    }
    
    /* Spinner Animation with Spotify green */
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #282828;
        border-top: 2px solid #1DB954;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Alternative dot spinner */
    .dot-spinner {
        display: inline-block;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    .dot-spinner:after {
        content: '⠋';
        animation: dots 1.2s linear infinite;
        font-family: monospace;
        font-size: 16px;
        color: #1DB954;
    }
    
    @keyframes dots {
        0% { content: '⠋'; }
        12.5% { content: '⠙'; }
        25% { content: '⠹'; }
        37.5% { content: '⠸'; }
        50% { content: '⠼'; }
        62.5% { content: '⠴'; }
        75% { content: '⠦'; }
        87.5% { content: '⠧'; }
        100% { content: '⠇'; }
    }
    </style>
    

    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("### Orion")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 System Information")
        
        # Connection status
        if not st.session_state.connection_checked:
            with st.spinner("Checking Ollama connection..."):
                is_connected, status_message = check_ollama_connection(
                    server_url=st.session_state.ollama_url,
                    model_name=st.session_state.ollama_model
                )
                st.session_state.connection_status = (is_connected, status_message)
                st.session_state.connection_checked = True
        
        is_connected, status_message = st.session_state.connection_status
        
        if is_connected:
            st.success(status_message)
        else:
            st.error(status_message)
            st.markdown(f"""
            **Setup Steps:**
            1. Install Ollama: [ollama.com](https://ollama.com)
            2. Start server: `ollama serve`
            3. Pull model: `ollama pull {st.session_state.ollama_model}`
            4. Check server URL: {st.session_state.ollama_url}
            """)
        
        st.divider()
        
        # Ollama Configuration
        st.subheader("🤖 Ollama Configuration")
        
        # Ollama URL
        ollama_url_input = st.text_input(
            "Ollama Server URL:",
            value=st.session_state.ollama_url,
            help="URL of your Ollama server",
            key="ollama_url_input"
        )
        
        # Refresh models button and model selection
        col1, col2 = st.columns([2, 1])
        with col2:
            refresh_models = st.button("🔄 Refresh", use_container_width=True, key="refresh_models_btn")
        
        # Get available models
        refresh_requested = st.session_state.pop("refresh_model_list", False) or refresh_models
        models_source_changed = st.session_state.available_models_url != ollama_url_input
        if refresh_requested or models_source_changed:
            with st.spinner("Loading available models..."):
                st.session_state.available_models = get_available_ollama_models(ollama_url_input)
                st.session_state.available_models_url = ollama_url_input
            # A keyed selection from another server must not override its new options.
            if models_source_changed:
                st.session_state.pop("ollama_model_input", None)
                st.session_state.pop("ollama_model_input_fallback", None)
        
        with col1:
            if st.session_state.available_models:
                # Find current model in list or use first available
                current_model_index = 0
                if st.session_state.ollama_model in st.session_state.available_models:
                    current_model_index = st.session_state.available_models.index(st.session_state.ollama_model)
                
                ollama_model_input = st.selectbox(
                    "Model:",
                    options=st.session_state.available_models,
                    index=current_model_index,
                    help="Select an available Ollama model",
                    key="ollama_model_input"
                )
            else:
                ollama_model_input = st.text_input(
                    "Model:",
                    value=st.session_state.ollama_model,
                    help="Model name (couldn't load available models)",
                    key="ollama_model_input_fallback"
                )
        
        st.divider()
        
        # MCP Configuration
        st.subheader("🔗 MCP Configuration")
        
        mcp_url_input = st.text_input(
            "MCP Server URL:",
            value=st.session_state.mcp_url,
            help="URL of your MCP server (optional)",
            key="mcp_url_input"
        )
        
        mcp_token_input = st.text_input(
            "MCP Bearer Token:",
            value=st.session_state.mcp_token,
            type="password",
            help="Bearer token for MCP authentication (optional)",
            key="mcp_token_input"
        )
        
        # Apply Settings Button
        settings_changed = (
            ollama_url_input != st.session_state.ollama_url or
            (st.session_state.available_models and ollama_model_input != st.session_state.ollama_model) or
            (not st.session_state.available_models and ollama_model_input != st.session_state.ollama_model) or
            mcp_url_input != st.session_state.mcp_url or
            mcp_token_input != st.session_state.mcp_token
        )
        
        if st.button("🚀 Apply Settings", use_container_width=True, type="primary", disabled=not settings_changed, key="apply_settings_btn"):
            # Persist the draft before changing the active session.
            settings_to_save = {
                "ollama_model": ollama_model_input,
                "ollama_url": ollama_url_input,
                "mcp_url": mcp_url_input,
                "mcp_token": mcp_token_input,
                "system_prompt": st.session_state.system_prompt
            }
            if not save_settings_to_file(settings_to_save):
                st.stop()
            st.session_state.ollama_url = ollama_url_input
            st.session_state.ollama_model = ollama_model_input
            st.session_state.mcp_url = mcp_url_input
            st.session_state.mcp_token = mcp_token_input

            # Update the app instance
            st.session_state.app.update_settings(
                model_name=st.session_state.ollama_model,
                ollama_url=st.session_state.ollama_url,
                mcp_url=st.session_state.mcp_url,
                mcp_token=st.session_state.mcp_token
            )
            
            # Force connection recheck
            st.session_state.connection_checked = False
            
            st.success("✅ Settings updated and saved successfully!")
            st.rerun()
        
        st.divider()
        
        # System Prompt Configuration
        st.subheader("🎯 System Prompt")
        
        # Show current active system prompt
        with st.expander("📋 Current Active System Prompt", expanded=False):
            st.code(st.session_state.system_prompt, language="text")
        
        # Text area for editing
        system_prompt_draft = st.text_area(
            "Edit system prompt:",
            value=st.session_state.system_prompt,
            height=150,
            help="This defines how the AI assistant will behave and respond to users.",
            key="system_prompt_input"
        )
        
        # Button to apply changes
        col1, col2 = st.columns([2, 1])
        with col1:
            apply_clicked = st.button("🚀 Apply System Prompt", use_container_width=True, type="primary")
            clear_history = st.checkbox("Clear chat history", value=True, help="Recommended when changing system prompt", key="clear_history_checkbox")
            
            if apply_clicked:
                if system_prompt_draft != st.session_state.system_prompt:
                    # Save settings to file for persistence
                    settings_to_save = {
                        "ollama_model": st.session_state.ollama_model,
                        "ollama_url": st.session_state.ollama_url,
                        "mcp_url": st.session_state.mcp_url,
                        "mcp_token": st.session_state.mcp_token,
                        "system_prompt": system_prompt_draft
                    }
                    if not save_settings_to_file(settings_to_save):
                        st.stop()
                    st.session_state.system_prompt = system_prompt_draft
                    
                    # Use the update method to ensure proper agent recreation
                    st.session_state.app.update_system_prompt(system_prompt_draft)
                    st.success("✅ System prompt updated and saved!")
                    # Clear messages to start fresh with new prompt
                    if clear_history:
                        st.session_state.messages = []
                        st.info("💬 Chat history cleared.")
                    st.rerun()
                else:
                    st.info("System prompt unchanged.")
        
        with col2:
            # Reset to default button
            default_prompt = DEFAULT_SYSTEM_PROMPT
            
            if st.button("🔄 Reset", use_container_width=True):
                # Save settings to file for persistence
                settings_to_save = {
                    "ollama_model": st.session_state.ollama_model,
                    "ollama_url": st.session_state.ollama_url,
                    "mcp_url": st.session_state.mcp_url,
                    "mcp_token": st.session_state.mcp_token,
                    "system_prompt": default_prompt
                }
                if not save_settings_to_file(settings_to_save):
                    st.stop()
                st.session_state.system_prompt = default_prompt
                
                st.session_state.app.update_system_prompt(default_prompt)
                st.session_state.messages = []  # Clear history when resetting
                st.rerun()
        
        st.divider()
        
        # MCP Server Status
        st.subheader("🔗 MCP Integration")
        if hasattr(st.session_state.app, 'mcp_status'):
            if "✅" in st.session_state.app.mcp_status:
                st.success(st.session_state.app.mcp_status)
            elif "❌" in st.session_state.app.mcp_status:
                st.error(st.session_state.app.mcp_status)
            else:
                st.warning(st.session_state.app.mcp_status)
        
        st.divider()
        
        # Model info
        settings_file_exists = os.path.exists("orion_settings.json")
        settings_info = ""
        if settings_file_exists:
            try:
                import time
                mtime = os.path.getmtime("orion_settings.json")
                settings_info = f"\n- **Settings**: Saved {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}"
            except:
                settings_info = "\n- **Settings**: File exists"
        else:
            settings_info = "\n- **Settings**: Using defaults (not saved yet)"
            
        st.markdown(f"""
        **Current Configuration:**
        - **Model**: {st.session_state.ollama_model} via Ollama
        - **Framework**: Pydantic AI
        - **Ollama URL**: {st.session_state.ollama_url}/v1
        - **MCP Server**: {'Configured (not tested)' if st.session_state.app.mcp_server else 'Not configured'}
        - **System Prompt**: {len(st.session_state.system_prompt)} characters{settings_info}
        """)
        
        st.divider()
        
        # Controls
        st.header("🎛️ Controls")
        
        if st.button("🔄 Check Connection", use_container_width=True):
            st.session_state.connection_checked = False
            # Also refresh available models when checking connection
            st.session_state.refresh_model_list = True
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Statistics
        if st.session_state.messages:
            st.divider()
            st.header("📊 Statistics")
            total_messages = len(st.session_state.messages)
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            
            st.metric("Total Messages", total_messages)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("User", user_messages)
            with col2:
                st.metric("Assistant", assistant_messages)
    
    # Main chat interface
    if not is_connected:
        st.warning("⚠️ Cannot connect to Ollama. Please check the sidebar for setup instructions.")
        st.stop()
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and "thinking" in message:
                    # Show thinking UI for assistant messages
                    thinking_content = message.get("thinking", "")
                    
                    # Thinking section
                    thinking_container = st.container()
                    with thinking_container:
                        thinking_expander = st.expander("💭 View thinking process", expanded=False)
                        if thinking_content:
                            thinking_expander.markdown(thinking_content)
                        else:
                            thinking_expander.markdown("*No explicit thinking process captured*")
                    
                    # Response section
                    st.markdown(message["content"])
                else:
                    # Regular message display
                    st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Get assistant response with thinking model UI
        with chat_container:
            with st.chat_message("assistant"):
                # Convert session messages to ChatMessage objects
                conversation_history = [
                    ChatMessage(role=msg["role"], content=msg["content"])
                    for msg in st.session_state.messages[:-1]  # Exclude current message
                ]
                
                # Stream response from agent with thinking UI
                try:
                    # Create containers for thinking and response
                    thinking_container = st.container()
                    response_container = st.container()
                    
                    thinking_content = ""
                    response_content = ""
                    thinking_active = True
                    
                    # Spinner characters for animated effect
                    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    spinner_index = 0
                    
                    # Create containers for thinking and response
                    with thinking_container:
                        thinking_expander_container = st.empty()
                    
                    with response_container:
                        response_placeholder = st.empty()
                    
                    # Initialize thinking expander immediately
                    current_expander_title = f"{spinner_chars[0]} Thinking..."
                    with thinking_expander_container.container():
                        thinking_expander = st.expander(current_expander_title, expanded=True)
                        thinking_placeholder = thinking_expander.empty()
                        thinking_placeholder.markdown("*Processing your request...*")
                    
                    update_frequency = 0  # Update title every few chunks to reduce flicker
                    
                    # Get streaming response with thinking separation
                    async def stream_response():
                        nonlocal thinking_content, response_content, thinking_active, thinking_expander_container, spinner_index, current_expander_title, thinking_placeholder, update_frequency
                        
                        async for chunk_data in st.session_state.app.get_streaming_response(prompt, conversation_history):
                            chunk_type = chunk_data.get('type', 'response')
                            chunk_content = chunk_data.get('content', '')
                            chunk_status = chunk_data.get('status', 'streaming')
                            
                            if chunk_type == 'thinking':
                                thinking_content += chunk_content
                                # Update spinner animation in expander title, but not too frequently
                                update_frequency += 1
                                
                                if update_frequency % 5 == 0:  # Update title every 5th chunk to reduce flicker
                                    spinner_index = (spinner_index + 1) % len(spinner_chars)
                                    current_spinner = spinner_chars[spinner_index]
                                    current_expander_title = f"{current_spinner} Thinking..."
                                    
                                    # Update expander with new title and content
                                    with thinking_expander_container.container():
                                        thinking_expander = st.expander(current_expander_title, expanded=True)
                                        thinking_placeholder = thinking_expander.empty()
                                        thinking_placeholder.markdown(thinking_content + "▌")
                                elif thinking_placeholder:
                                    # Just update content without changing title
                                    thinking_placeholder.markdown(thinking_content + "▌")
                                
                            elif chunk_type == 'thinking_complete':
                                thinking_active = False
                                current_expander_title = "💭 View thinking process"
                                
                                # Update to completion title and collapse automatically
                                with thinking_expander_container.container():
                                    thinking_expander = st.expander(current_expander_title, expanded=False)
                                    thinking_placeholder = thinking_expander.empty()
                                    if thinking_content.strip():
                                        thinking_placeholder.markdown(thinking_content)
                                    else:
                                        thinking_placeholder.markdown("*The AI processed your request directly without explicit thinking steps*")
                                
                            elif chunk_type == 'response':
                                # Ensure thinking is properly closed before starting response
                                if thinking_active:
                                    thinking_active = False
                                    current_expander_title = "💭 View thinking process"
                                    
                                    with thinking_expander_container.container():
                                        thinking_expander = st.expander(current_expander_title, expanded=False)
                                        thinking_placeholder = thinking_expander.empty()
                                        if thinking_content.strip():
                                            thinking_placeholder.markdown(thinking_content)
                                        else:
                                            thinking_placeholder.markdown("*Processing complete*")
                                
                                response_content += chunk_content
                                response_placeholder.markdown(response_content + "▌")
                                
                            elif chunk_type == 'response_complete':
                                # Remove the cursor from final response
                                if response_content:
                                    response_placeholder.markdown(response_content)
                                else:
                                    response_placeholder.markdown("*No response generated*")
                                
                            elif chunk_type == 'error':
                                response_placeholder.error(MODEL_REQUEST_ERROR)
                                return None
                        
                        # Final check - if thinking is still active, close it
                        if thinking_active:
                            with thinking_expander_container.container():
                                thinking_expander = st.expander("💭 View thinking process", expanded=False)
                                thinking_placeholder = thinking_expander.empty()
                                if thinking_content.strip():
                                    thinking_placeholder.markdown(thinking_content)
                                else:
                                    thinking_placeholder.markdown("*The AI processed your request directly without explicit thinking steps*")
                        
                        return response_content
                    
                    # Run the streaming function
                    final_response = asyncio.run(stream_response())
                    
                    # Store both thinking and response in message history
                    if final_response and final_response.strip():
                        message_data = {
                            "role": "assistant", 
                            "content": final_response,
                            "thinking": thinking_content if thinking_content.strip() else None
                        }
                        st.session_state.messages.append(message_data)
                        
                except Exception:
                    # Transport exceptions can include credentials or response bodies.
                    # A failed run is not an assistant turn for subsequent requests.
                    st.error(MODEL_REQUEST_ERROR)

    # Auto-focus the chat input after all UI elements are rendered
    auto_focus_chat_input()


if __name__ == "__main__":
    main()
