```text
 ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

##  Advanced AI Chat Assistant

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Pydantic AI](https://img.shields.io/badge/Pydantic%20AI-Latest-green.svg)](https://ai.pydantic.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-orange.svg)](https://ollama.com)

A powerful, modern chat interface powered by **Pydantic AI** and **Ollama**, featuring advanced thinking visualization, MCP tool integration, and persistent settings. Experience AI conversations like never before! 🚀

---

## ✨ Key Features

### 🤖 **Intelligent Chat Experience**
- **Local AI Power**: Runs entirely on your machine with Ollama
- **Dynamic Model Selection**: Choose from any available Ollama model
- **Thinking Visualization**: See the AI's reasoning process in real-time
- **Streaming Responses**: Real-time response generation with live thinking updates

### 🔗 **Tool Integration**
- **MCP Protocol Support**: Connect to external tools and services
- **15+ Built-in Tools**: Web scraping, research, file operations, and more
- **Transparent Tool Usage**: See exactly what tools the AI is using and why

### ⚙️ **Advanced Configuration**
- **Persistent Settings**: Your preferences survive browser refreshes
- **Dynamic Model Management**: Auto-detect and switch between Ollama models
- **Flexible Server Configuration**: Custom Ollama and MCP server settings
- **System Prompt Customization**: Fine-tune AI behavior to your needs

### 🎨 **Modern Interface**
- **Beautiful UI**: Clean, responsive design with dark theme
- **Real-time Status**: Monitor connections and model availability
- **Collapsible Thinking**: Expandable sections for AI reasoning
- **Chat History**: Persistent conversation memory

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** - Required for MCP support
2. **Ollama** - Local LLM runtime
   ```bash
   # Install from https://ollama.com
   curl -fsSL https://ollama.com/install.sh | sh
   ```

### Installation

1. **Clone & Setup**
   ```bash
   git clone https://github.com/your-username/orion.git
   cd orion
   pip install -r requirements.txt
   ```

2. **Install & Start Ollama**
   ```bash
   # Start Ollama server
   ollama serve
   
   # Pull a model (in another terminal)
   ollama pull qwen3:14b
   # or try: llama3.2, mistral, codellama, etc.
   ```

3. **Launch Orion**
   ```bash
   streamlit run app.py
   ```

4. **Open in Browser**
   Navigate to `http://localhost:8501` and start chatting! 🎉

---

## 🛠️ Configuration

### Easy UI Configuration
All settings can be configured directly in the app's sidebar - no file editing required!

- **🤖 Ollama Settings**: Server URL, model selection
- **🔗 MCP Integration**: Server URL, authentication tokens  
- **🎯 System Prompts**: Customize AI behavior
- **💾 Auto-Save**: Settings persist across sessions

### Environment Variables (Optional)
Create a `.env` file for default MCP settings:

```env
# MCP Server Configuration (optional - can be set in UI)
MCP_SERVER_URL=https://your-mcp-server.com/sse
MCP_BEARER_TOKEN=your_bearer_token
```

---

## 🧠 How It Works

### Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Streamlit UI  │◄──►│ Pydantic AI  │◄──►│ Ollama Server   │
│                 │    │              │    │                 │
│ • Chat Interface│    │ • Agent Logic│    │ • Local LLMs    │
│ • Settings UI   │    │ • Tool Calls │    │ • Model Mgmt    │
│ • Status Monitor│    │ • Streaming  │    │ • GPU Accel     │
└─────────────────┘    └──────┬───────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   MCP Server     │
                    │                  │
                    │ • External Tools │
                    │ • APIs & Services│
                    │ • Data Sources   │
                    └──────────────────┘
```

### Thinking Process Visualization

Orion provides unique insight into AI reasoning:

1. **🧠 Real-time Thinking**: See thoughts as they form
2. **📝 Structured Reasoning**: Clear separation of thinking vs. response
3. **🔍 Transparent Process**: Understand how decisions are made
4. **⚡ Instant Feedback**: Thinking indicator appears immediately

---

## 🎯 Available MCP Tools

When connected to an MCP server, Orion provides access to powerful tools:

| Tool | Description | Usage |
|------|-------------|-------|
| **🌐 scraperAgent** | Web content extraction | `/scrape https://example.com` |
| **🗄️ vaultAgent** | Secure data management | `/vault store data` |
| **📝 blogAgent** | Blog post generation | `/blog "AI trends 2024"` |
| **🎬 comfyAgent** | Media generation | `/comfy generate image` |
| **🔍 researchAgent** | Internet research | `/research "quantum computing"` |
| **📊 githubAgent** | GitHub operations | `/github trending repos` |
| **💾 Save_Memory** | Information storage | Automatic context saving |
| **📧 Get_Emails** | Email management | Message retrieval |
| **📁 Projects** | Project tracking | Notion integration |
| **🔒 Hacker_News** | Tech news access | Latest tech updates |
| **🗣️ Reddit** | Reddit integration | Community insights |
| **📅 Calendar** | Schedule management | Google Calendar sync |
| **🧮 calculator** | Math operations | Complex calculations |
| **🤔 thinking_tool** | Reasoning aid | Internal logic tracking |

---

## 💡 Usage Examples

### Basic Chat
```
You: "What are the latest trends in AI?"
AI: [Thinking] I should research recent developments...
AI: Based on recent research, here are the key AI trends...
```

### Using Tools
```
You: "Scrape the latest news from TechCrunch"
AI: [Thinking] I'll use the scraper tool to get current articles...
AI: *Uses scraperAgent*
AI: Here are the latest TechCrunch headlines...
```

### Custom System Prompts
```
System: You are a Python expert who always shows code examples.
You: "How do I handle exceptions?"
AI: [Thinking] I should provide practical Python examples...
AI: Here's how to handle exceptions in Python:
```

---

## 🔧 Advanced Features

### Persistent Settings
- **Auto-save**: All configurations saved automatically
- **Session Recovery**: Settings persist across browser refreshes  
- **Environment Override**: UI settings take precedence over .env files
- **Backup Safe**: Settings stored locally, not in version control

### Dynamic Model Management
- **Auto-detection**: Scans Ollama for available models
- **Hot-swapping**: Change models without restarting
- **Model Info**: Real-time model and server status
- **Fallback Handling**: Graceful degradation when models unavailable

### Thinking Process Engine
- **Tag Parsing**: Understands `<think>` tags for structured reasoning
- **Natural Language**: Detects thinking phrases automatically
- **Stream Processing**: Real-time thinking updates
- **Collapsible Views**: Clean interface with expandable details

---

## 🐛 Troubleshooting

### Common Issues

**🔴 Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**🔴 No Models Available**
```bash
# List available models
ollama list

# Pull a model
ollama pull qwen3:14b
```

**🔴 MCP Tools Not Working**
- Verify MCP server URL and token in sidebar
- Check MCP server is running and accessible
- Test connection with curl/browser

**🔴 Thinking Process Not Showing**
- Model should use `<think>` tags or natural thinking phrases
- Check if streaming is working properly
- Try different models for comparison

### Performance Tips

- **🚀 GPU Acceleration**: Ensure Ollama is using GPU if available
- **💾 Memory Management**: Monitor RAM usage with large models
- **🌐 Network**: Use local MCP servers for faster tool responses
- **🔄 Model Selection**: Smaller models = faster responses

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/orion.git
cd orion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
streamlit run app.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Pydantic AI](https://ai.pydantic.dev)** - Powerful agent framework
- **[Ollama](https://ollama.com)** - Local LLM runtime
- **[Streamlit](https://streamlit.io)** - Beautiful web apps for ML
- **[MCP Protocol](https://modelcontextprotocol.io)** - Tool integration standard

---

## 🌟 Star History

If you find Orion useful, please consider giving it a star! ⭐

---

<div align="center">
  <p><strong>Built with ❤️ for the AI community</strong></p>
  <p>
    <a href="https://github.com/your-username/orion/issues">Report Bug</a> •
    <a href="https://github.com/your-username/orion/issues">Request Feature</a> •
    <a href="https://github.com/your-username/orion/discussions">Discussions</a>
  </p>
</div> 