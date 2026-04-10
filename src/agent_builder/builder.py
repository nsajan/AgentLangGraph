"""AgentBuilder: compiles an AgentConfig into a runnable LangGraph."""

from __future__ import annotations

import importlib
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent_builder.schemas import AgentConfig, LLMProvider, NodeConfig
from src.agent_builder.state import AgentState
from src.agent_builder.tools import resolve_tool


class AgentBuilder:
    """Build a LangGraph CompiledGraph from a declarative AgentConfig."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._graph = StateGraph(AgentState)
        self._tool_nodes: dict[str, ToolNode] = {}

    # --- public ---

    def build(self):
        """Compile the config into a runnable graph and return it."""
        for node_cfg in self.config.nodes:
            self._add_node(node_cfg)

        for edge_cfg in self.config.edges:
            if edge_cfg.condition:
                condition_fn = self._resolve_condition(edge_cfg.condition)
                self._graph.add_conditional_edges(edge_cfg.source, condition_fn)
            else:
                self._graph.add_edge(edge_cfg.source, edge_cfg.target)

        self._graph.set_entry_point(self.config.entry_point)

        if self.config.finish_point:
            self._graph.add_edge(self.config.finish_point, END)

        return self._graph.compile()

    # --- private ---

    def _add_node(self, node_cfg: NodeConfig):
        if node_cfg.type == "llm":
            self._add_llm_node(node_cfg)
        elif node_cfg.type == "tool":
            self._add_tool_node(node_cfg)
        elif node_cfg.type == "custom":
            self._add_custom_node(node_cfg)
        else:
            raise ValueError(f"Unknown node type: {node_cfg.type}")

    def _add_llm_node(self, node_cfg: NodeConfig):
        llm = self._create_llm(node_cfg)
        tools = [resolve_tool(t) for t in node_cfg.tools]

        if tools:
            llm = llm.bind_tools(tools)
            tool_node_name = f"{node_cfg.name}_tools"
            self._graph.add_node(tool_node_name, ToolNode(tools))
            self._tool_nodes[node_cfg.name] = tool_node_name

        system_prompt = node_cfg.system_prompt

        def make_node_fn(llm_instance, prompt, name, tool_node_name=None):
            def node_fn(state: AgentState):
                messages = state.messages
                if prompt:
                    messages = [SystemMessage(content=prompt)] + list(messages)
                response = llm_instance.invoke(messages)
                return {"messages": [response], "current_node": name}
            return node_fn

        self._graph.add_node(
            node_cfg.name,
            make_node_fn(llm, system_prompt, node_cfg.name),
        )

        # If tools are present, add conditional routing: call tools or end
        if tools:
            tool_node_name = f"{node_cfg.name}_tools"

            def make_should_continue(tn_name):
                def should_continue(state: AgentState):
                    last = state.messages[-1]
                    if hasattr(last, "tool_calls") and last.tool_calls:
                        return tn_name
                    return END
                return should_continue

            self._graph.add_conditional_edges(
                node_cfg.name,
                make_should_continue(tool_node_name),
            )
            # After tool execution, loop back to the LLM
            self._graph.add_edge(tool_node_name, node_cfg.name)

    def _add_tool_node(self, node_cfg: NodeConfig):
        tools = [resolve_tool(t) for t in node_cfg.tools]
        self._graph.add_node(node_cfg.name, ToolNode(tools))

    def _add_custom_node(self, node_cfg: NodeConfig):
        if not node_cfg.custom_function_path:
            raise ValueError(f"Custom node '{node_cfg.name}' requires custom_function_path")
        module_path, func_name = node_cfg.custom_function_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        self._graph.add_node(node_cfg.name, func)

    @staticmethod
    def _create_llm(node_cfg: NodeConfig) -> Any:
        if node_cfg.provider == LLMProvider.OPENAI:
            return ChatOpenAI(model=node_cfg.model, temperature=0)
        elif node_cfg.provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(model=node_cfg.model, temperature=0)
        raise ValueError(f"Unknown provider: {node_cfg.provider}")

    @staticmethod
    def _resolve_condition(condition: str):
        if "." in condition:
            module_path, func_name = condition.rsplit(".", 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        raise ValueError(f"Condition must be a dotted function path, got: {condition}")
