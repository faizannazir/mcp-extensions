"""Native MCP Python SDK integration for OpenAI server extensions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mcp.server.elicitation import ElicitationResult, ElicitSchemaModelT
from mcp.server.extension import Extension, ToolBinding
from mcp.server.mcpserver.context import Context

from openai_mcp_extensions.form import elicit_form
from openai_mcp_extensions.mentions import OpenAIMentions
from openai_mcp_extensions.settings import OpenAISettings


class OpenAIExtensions(Extension):
    """Compose OpenAI-specific server behavior into an MCP Python server."""

    identifier = "openai/extensions"

    def __init__(self) -> None:
        self.mentions = OpenAIMentions()
        self._settings: OpenAISettings | None = None

    @property
    def settings(self) -> OpenAISettings:
        if self._settings is None:
            raise AttributeError(
                "Settings have not been registered. "
                "Call register_settings() before accessing."
            )
        return self._settings

    def register_settings(self, settings: OpenAISettings) -> OpenAISettings:
        if self._settings is not None:
            raise ValueError("Settings are already registered on this extension.")
        self._settings = settings
        return settings

    def tools(self) -> Sequence[ToolBinding]:
        """Contribute only the OpenAI tools explicitly configured by the server."""

        bindings: list[ToolBinding] = list(self.mentions.tools())
        if self._settings is not None:
            bindings.extend(self._settings.tools())
        return bindings

    async def elicit_input(
        self,
        context: Context[Any, Any],
        *,
        mode: Literal["form"],
        message: str,
        schema: type[ElicitSchemaModelT],
    ) -> ElicitationResult[ElicitSchemaModelT]:
        """Request input and return the validated Pydantic model."""

        if mode != "form":
            raise ValueError("Unsupported OpenAI elicitation mode")
        return await elicit_form(context, message=message, schema=schema)
