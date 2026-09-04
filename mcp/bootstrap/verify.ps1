$ErrorActionPreference = "Stop"

docker mcp feature list
docker mcp profile show core-dev --format yaml
docker mcp profile show envative --format yaml
docker mcp gateway run --profile core-dev --dry-run
docker mcp gateway run --profile envative --dry-run
claude mcp list
codex mcp list
