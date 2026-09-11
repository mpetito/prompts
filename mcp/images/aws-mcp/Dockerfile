FROM ghcr.io/astral-sh/uv:python3.12-alpine@sha256:a25d04690bce3e733cee2a2779d97ae60892edb517e85f43578b80ddf625e536

ENV PATH="/root/.local/bin:${PATH}"

RUN uv tool install mcp-proxy-for-aws==1.6.4

ENTRYPOINT ["mcp-proxy-for-aws"]
CMD ["https://aws-mcp.us-east-1.api.aws/mcp"]
