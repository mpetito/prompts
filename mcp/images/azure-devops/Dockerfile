FROM node:22.20-alpine@sha256:dbcedd8aeab47fbc0f4dd4bffa55b7c3c729a707875968d467aaaea42d6225af

RUN npm install --global @azure-devops/mcp@2.9.0

ENTRYPOINT ["mcp-server-azuredevops"]
CMD ["envative", "--authentication", "envvar", "-d", "core", "work", "work-items", "search"]
