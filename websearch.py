import streamlit as st
import os
from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.firecrawl import FirecrawlTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
from typing import List, Dict
import json

load_dotenv()

st.set_page_config(
    page_title="Web Search Assistant",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Web Search Assistant")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def initialize_agent():
    duckduckgo_tool = DuckDuckGo()
    firecrawl_tool = FirecrawlTools(scrape=True, crawl=False)
    claude_model = Claude(id="claude-3-5-sonnet-20240620")
    return Agent(
        model=claude_model,
        tools=[duckduckgo_tool, firecrawl_tool],
        show_tool_calls=True,
        markdown=True,
        description="A web search agent that can search the internet and provide detailed answers.",
        instructions=[
            "Search the web for relevant information",
            "Provide detailed answers with citations",
            "Use web scraping when needed for deeper analysis"
        ]
    )

def format_response_with_citations(response: str, search_results: List[Dict]) -> str:
    """Format agent response with citations"""
    
    formatted_response = response
    
    # Add citations section
    formatted_response += "\n\n### Sources:\n"
    for i, result in enumerate(search_results, 1):
        title = result.get('title', '')
        href = result.get('href', '')
        formatted_response += f"{i}. [{title}]({href})\n"
    
    return formatted_response

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask me anything...")

if prompt:
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            agent = initialize_agent()
            response = agent.run(prompt)
            
            # Extract search results from agent response
            search_results = []
            for msg in response.messages:
                if msg.role == "user" and isinstance(msg.content, list):
                    for content in msg.content:
                        if isinstance(content, dict) and content.get('type') == 'tool_result':
                            try:
                                results = json.loads(content['content'])
                                search_results.extend(results)
                            except:
                                continue
            
            # Format response with citations
            formatted_response = format_response_with_citations(
                response.content,
                search_results
            )
            
            st.markdown(formatted_response)
            print(response)
    st.session_state.messages.append({"role": "assistant", "content": response.content})

# Sidebar with info
with st.sidebar:
    st.markdown("### About")
    st.markdown("This assistant can:")
    st.markdown("- Search the web using DuckDuckGo")
    st.markdown("- Analyze webpage content")
    st.markdown("- Provide detailed answers with sources")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()