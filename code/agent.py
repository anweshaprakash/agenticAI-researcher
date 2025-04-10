import streamlit as st
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import ArxivLoader
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.callbacks.base import BaseCallbackHandler


# Streaming callback for Streamlit
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.accum_text = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.accum_text += token
        self.placeholder.markdown(self.accum_text)

llm_stream = ChatOpenAI(
    temperature=0.7,
    model="gpt-4-0125-preview",
    streaming=True
)

llm = ChatOpenAI(
    temperature=0.7,
    model="gpt-4-0125-preview"
)

# Tool functions with trimmed inputs
def fetch_arxiv(query: str) -> str:
    loader = ArxivLoader(query=query, load_max_docs=1)
    docs = loader.load()
    return docs[0].page_content[:6000] if docs else "No paper found."

def summarize_text(text: str) -> str:
    prompt = f"Summarize the following academic paper:\n\n{text[:4000]}\n\nUse an academic tone."
    return llm.invoke(prompt).content

def detailed_explainer(text: str) -> str:
    prompt = f"""
    Provide a deep technical explanation, real-world applications, and references for this paper content:
    
    {text[:3000]}

    Use an academic tone.
    """
    return llm.invoke(prompt).content

search_tool = DuckDuckGoSearchAPIWrapper()

def web_search(query: str) -> str:
    return search_tool.run(query)

def qa_tool(context_and_question: str) -> str:
    prompt = f"Answer based on context and question:\n\n{context_and_question[:4000]}"
    return llm.invoke(prompt).content

# Tool list
tools = [
    Tool(name="ArxivFetcher", func=fetch_arxiv, description="Fetches a research paper from ArXiv based on query."),
    Tool(name="Summarizer", func=summarize_text, description="Summarizes academic text."),
    Tool(name="DetailedExplainer", func=detailed_explainer, description="Gives a technical explanation and applications of academic content."),
    Tool(name="WebSearch", func=web_search, description="Searches DuckDuckGo for additional insights."),
    Tool(name="QnAExtractor", func=qa_tool, description="Answers questions from academic text."),
]

# Streamlit UI
st.set_page_config(page_title="Agentic Streaming AI", page_icon="🧠")
st.markdown("<h1 style='text-align: center;'>🧠 Agentic AI for Research</h1>", unsafe_allow_html=True)

query = st.text_input("Enter your research prompt:")

if st.button("Run Agent") and query:
    with st.spinner("Agent is thinking..."):
        stream_placeholder = st.empty()
        handler = StreamlitCallbackHandler(stream_placeholder)

        agent = initialize_agent(
            tools=tools,
            llm=ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True, callbacks=[handler]),
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )

        try:
            result = agent.run(query)
            st.markdown("### ✅ Final Answer")
            st.markdown(result)
        except Exception as e:
            st.error(f"Agent encountered an error:\n\n{str(e)}")
