# Version Conversion Reference

This document provides technical details about converting between OpenAPI 3.0.x and 3.1.x formats.

## Overview

The OAS Slicer supports bidirectional conversion between OpenAPI versions:

- **3.0.x → 3.1.x**: Upgrade to take advantage of new features
- **3.1.x → 3.0.x**: Downgrade for compatibility with older tools

## Transformation Rules

### 3.0 to 3.1 Conversions

#### Nullable Properties

In OpenAPI 3.0, nullable fields use a separate `nullable` keyword:

```yaml
# OpenAPI 3.0
type: string
nullable: true
```

In OpenAPI 3.1, this becomes a type array:

```yaml
# OpenAPI 3.1
type:
  - string
  - "null"
```

#### Version Number

The `openapi` field is updated:

```yaml
# From
openapi: "3.0.3"

# To
openapi: "3.1.0"
```

#### Discriminator Updates

OpenAPI 3.1 supports enhanced discriminator syntax:

```yaml
# OpenAPI 3.0
discriminator:
  propertyName: petType

# OpenAPI 3.1 (enhanced mapping supported)
discriminator:
  propertyName: petType
  mapping:
    dog: '#/components/schemas/Dog'
    cat: '#/components/schemas/Cat'
```

#### Example/Examples

OpenAPI 3.1 aligns more closely with JSON Schema:

```yaml
# OpenAPI 3.0
example: "sample value"

# OpenAPI 3.1 (both supported)
examples:
  - "sample value"
```

### 3.1 to 3.0 Conversions

#### Type Arrays to Nullable

Type arrays with `null` are converted back to the `nullable` keyword:

```yaml
# OpenAPI 3.1
type:
  - string
  - "null"

# OpenAPI 3.0
type: string
nullable: true
```

#### Webhook Removal

Webhooks are not supported in OpenAPI 3.0:

```yaml
# OpenAPI 3.1
webhooks:
  newPet:
    post:
      summary: New pet notification
      ...

# OpenAPI 3.0 - webhooks section removed with warning
```

#### JSON Schema Keywords

Some JSON Schema keywords added in 3.1 are removed or simplified for 3.0 compatibility:

- `$vocabulary` - Removed
- `$dynamicRef` / `$dynamicAnchor` - Simplified or removed
- `if` / `then` / `else` - Cannot be converted (fails in strict mode)

## Conversion Modes

### Permissive Mode (Default)

In permissive mode, the converter:

1. Makes best-effort conversions
2. Removes unsupported constructs with warnings
3. Continues processing despite issues

```bash
slice-oas api.yaml --batch --convert-version 3.0 --output ./output/
```

### Strict Mode

In strict mode, the converter:

1. Fails on any unconvertible structure
2. Reports detailed error messages
3. Does not produce partial output

```bash
slice-oas api.yaml --batch --convert-version 3.0 --strict --output ./output/
```

## Unconvertible Constructs

### 3.1 → 3.0 Limitations

These OpenAPI 3.1 features cannot be converted to 3.0:

| Feature | Issue | Recommendation |
|---------|-------|----------------|
| Webhooks | Not supported in 3.0 | Remove manually or accept warning |
| JSON Schema conditionals (`if`/`then`/`else`) | No 3.0 equivalent | Restructure schema |
| `$dynamicRef` | No 3.0 equivalent | Use standard `$ref` |
| PathItem `$ref` to external files | Limited support | Inline references |

### 3.0 → 3.1 Considerations

Most 3.0 constructs convert cleanly to 3.1. However:

| Feature | Consideration |
|---------|---------------|
| `nullable: true` | Converted to type array |
| `example` | May be converted to `examples` array |
| Security schemes | Unchanged |

## Determinism

Conversions are deterministic:

- Running the same conversion multiple times produces identical output
- Transformation rules are applied in a consistent order
- Hash verification can confirm identical results

```bash
# Verify determinism
slice-oas api.yaml --path /users --method GET --convert-version 3.1 --output out1.yaml
slice-oas api.yaml --path /users --method GET --convert-version 3.1 --output out2.yaml

# Files should be identical
diff out1.yaml out2.yaml
```

## Round-Trip Behavior

Some conversions are not perfectly reversible:

```
3.0 → 3.1 → 3.0: May differ due to normalization
3.1 → 3.0 → 3.1: Information loss if webhooks or advanced features were removed
```

## Post-Conversion Validation

All converted documents are validated against the target OpenAPI schema:

1. Structural validation (required fields, proper nesting)
2. Reference resolution (all `$ref` targets exist)
3. Schema validation (types, formats, constraints)

Failed validation prevents output:

```
Conversion failed: Output document does not conform to OpenAPI 3.0 schema.
Please review the conversion warnings and try again.
```

## Performance

Conversion adds minimal overhead:

- Single endpoint: < 100ms additional
- 100 endpoints: < 5 seconds additional
- Conversion is parallelized with extraction

## Troubleshooting

### "Unconvertible construct" Error

This appears in strict mode when a 3.1 feature cannot be converted:

```
The endpoint uses features that cannot be converted to OpenAPI 3.0.
Specifically: JSON Schema conditional (if/then/else) detected.

Options:
1. Use permissive mode (warnings instead of errors)
2. Modify the source specification
3. Keep the 3.1 format
```

### "Webhook removed" Warning

In permissive mode when converting 3.1 to 3.0:

```
Note: Webhook definitions were removed during conversion.
These are not supported in OpenAPI 3.0.
```

### Validation Failures After Conversion

If the converted document fails validation:

1. Check for unsupported constructs that may have been partially converted
2. Verify all referenced components exist
3. Try strict mode to identify specific issues
