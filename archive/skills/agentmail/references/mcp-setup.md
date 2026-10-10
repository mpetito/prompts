# AgentMail MCP Connection

Read this only when AgentMail tools are missing, erroring, or targeting the wrong
organization. For normal mail operations, stay in [SKILL.md](../SKILL.md).

## Hosted Server

Prefer the hosted Streamable HTTP endpoint — no local Node.js process, faster release
cadence than the packaged local server:

```text
https://mcp.agentmail.to/mcp
```

## Configuration

VS Code (`.vscode/mcp.json`), Cursor (`.cursor/mcp.json`), Windsurf, and Claude Desktop all
take the same `type: http` entry.

**OAuth (preferred where supported)** — bare URL, no credentials. Do not insert an empty
API key; it breaks the OAuth handshake.

```json
{
  "mcpServers": {
    "agentmail": {
      "type": "http",
      "url": "https://mcp.agentmail.to/mcp"
    }
  }
}
```

**API key (clients without remote MCP OAuth)** — send it as a header, never a query
string, so the key stays out of logs and shell history.

```json
{
  "mcpServers": {
    "agentmail": {
      "type": "http",
      "url": "https://mcp.agentmail.to/mcp",
      "headers": {
        "x-api-key": "${env:AGENTMAIL_API_KEY}"
      }
    }
  }
}
```

`Authorization: Bearer am_...` works as an alternative header form. The `?apiKey=` query
parameter is supported but discouraged.

Claude Code can install it directly:

```bash
claude mcp add --transport http agentmail https://mcp.agentmail.to/mcp
```

Generate keys and manage organizations at <https://console.agentmail.to>.

### stdio-only clients

Use the published `agentmail-mcp` npm or PyPI package. Both are thin stdio bridges to the
same hosted runtime — they discover tools dynamically and carry no independent tool logic.

## Verify

1. Restart the client or open a new session after changing the config.
2. Complete the browser sign-in if using OAuth.
3. Call `list_inboxes` as a read-only smoke test.
4. Call `auth_me` to confirm which organization, pod, and inboxes the credential reaches.

## Troubleshooting

| Symptom                                         | Cause and fix                                                                                                                                                      |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `404`                                           | The URL is missing the `/mcp` path segment.                                                                                                                        |
| `401` "Unauthorized" on an OAuth session        | Sign-in incomplete or session expired. Remove any `apiKey` query param and let the browser flow run.                                                               |
| `401` "Invalid API key"                         | Key is wrong, revoked, or lacks permissions — or `AGENTMAIL_API_KEY` was not visible to the client process. Use the full value including the `am_` prefix.         |
| `403` on a specific inbox or pod                | The key is scoped narrower than the request. Check `auth_me`; use a key with the needed scope.                                                                     |
| Tools appear but operate on the wrong org       | Multi-org OAuth session. Use `list_organizations` then `select_organization` (persists across sessions). Or disconnect and reconnect to re-run the consent screen. |
| Connector shows connected, agent says no access | The client cached an old tool list. Restart the client.                                                                                                            |

Never paste an API key into a chat message, a committed config file, or a URL. Reference it
through an environment variable.
