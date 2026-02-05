# Story Simulation Specification

Story schema, step definitions, and validation rules.

## Story Schema

```yaml
- code: US-02-01
  title: "Create DPP shell"
  roles: ["manufacturer", "developer"]
  difficulty: "intermediate"
  steps:
    - action: user.input
      params:
        prompt: "Provide DPP creation details"
    - action: aas.create
      params:
        payload:
          id: "urn:uuid:example"
          idShort: "DPP-Create"
```

## Step Actions

- `user.input`: UI prompt step (no backend action).
- `aas.create`: Create AAS shell.
- `aas.update`: Update session state with AAS changes.
- `aas.submodel.add`: Create submodel in BaSyx.
- `aas.submodel.patch`: Patch submodel elements.
- `aasx.upload`: Store AASX payload (base64).
- `compliance.check`: Invoke compliance service.
- `edc.negotiate`: Create EDC negotiation.
- `edc.transfer`: Create EDC transfer.
- `api.call`: External API stub.
