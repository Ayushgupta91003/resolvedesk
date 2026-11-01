from app.agent import AgentRecommendation
from conftest import login
from test_support import start

def fake_model(monkeypatch, responder):
    import app.agent as agent
    import langchain.agents
    import langchain_openai
    class FakeAgent:
        def __init__(self, tools):
            self.tools = {tool.name: tool for tool in tools}
        def invoke(self, *args, **kwargs):
            return {"structured_response": responder(self.tools), "messages": []}
    monkeypatch.setattr(agent, "AGENT_MODE", "llm")
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kwargs: object())
    monkeypatch.setattr(langchain.agents, "create_agent", lambda **kwargs: FakeAgent(kwargs["tools"]))

def test_invented_model_citation_escalates(owner, monkeypatch):
    fake_model(monkeypatch, lambda tools: AgentRecommendation(action="reply", reason="Invented evidence", reply="Unsupported answer", source_ids=["invented-source"]))
    run = start(owner, "ticket-2")
    assert run["proposal"]["action"] == "escalate"
    assert run["proposal"]["citations"] == []
    assert "Unsupported answer" not in run["proposal"]["reply"]

def test_model_sources_match_its_actual_tool_results(owner, monkeypatch):
    def respond(tools):
        sources = tools["search_knowledge"].invoke({"search_query": "password reset account"})
        return AgentRecommendation(action="reply", reason="Account policy", reply="Use your store's reset-password link.", source_ids=[sources[0]["id"]])
    fake_model(monkeypatch, respond)
    run = start(owner, "ticket-2")
    assert run["proposal"]["action"] == "reply"
    assert len(run["proposal"]["citations"]) == 1
    assert run["proposal"]["citations"][0]["document_id"] == "doc-account"
    assert any(event["step"].startswith("search:") for event in run["events"])
