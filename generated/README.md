# Generated Code

This directory contains auto-generated code from API specifications.

## Structure

```
generated/
├── clients/
│   ├── python/       # Python SDK client
│   ├── typescript/   # TypeScript SDK client
│   └── go/           # Go SDK client
├── servers/
│   └── python-fastapi/  # FastAPI server stubs
└── proto/
    ├── go/           # Go protobuf/gRPC code
    └── python/       # Python protobuf/gRPC code
```

## Regeneration

To regenerate all clients:

```bash
make generate-all
```

To regenerate a specific client:

```bash
make generate-python
make generate-typescript
make generate-go
make generate-proto
```

## Important Notes

1. **Do not edit generated code directly** - changes will be overwritten
2. **Customize via templates** - use `templates/` directory for customizations
3. **Preserve specific files** - add to `ignoreFileOverride` in generator config

## Source Specifications

- OpenAPI: `specs/openapi/openapi.yaml`
- AsyncAPI: `specs/asyncapi/events.yaml`
- Protobuf: `specs/protobuf/*.proto`
- JSON Schema: `specs/json-schema/*.schema.json`

## CI/CD Integration

Generated code is created by:
- `generate-clients.yml` workflow on spec changes
- `release-sdks.yml` workflow for publishing
