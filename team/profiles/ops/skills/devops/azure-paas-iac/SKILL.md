---
name: azure-paas-iac
description: "Use when writing or reviewing Azure Bicep/ARM, pipelines or containers."
version: 0.1.0
metadata:
  hermes:
    tags: [azure, bicep, arm, app-service, container-apps, github-actions, iac]
---

# Azure PaaS infrastructure-as-code

Conventions and the validation procedure for this user's infrastructure work. **The repo's existing IaC layout, naming and AGENTS.md win over this file.** Existing examples: `bh-app-thread-portal/deploy/` (main.bicep + modules/, `parameters.<env>.json`, `test-bicep.sh`, GitHub Actions `deploy-infrastructure.yml`) and `ballistic/infra/bicep/`.

## Layout & naming (as the repos already do it)
- `main.bicep` orchestrates; one module per resource type under `modules/`. Extend a module before creating a new one.
- `environment` param (`dev`/`prod`, `@allowed`), `location = resourceGroup().location`, a `tags` var applied to every resource.
- Names derived from a base name + environment in one `var` block (e.g. `'${baseName}-kv-${environment}'`). Keep new names in that block. Respect each resource type's naming rules (length, allowed characters, global uniqueness for storage/Key Vault).
- Per-environment differences in a config map keyed by environment, or in parameter files. Not duplicated templates.

## Security defaults (reviewer checks these)
- No secrets in templates, parameter files, outputs or pipeline logs. Sensitive params are `@secure()`; values come from Key Vault (`getSecret()` or Key Vault references in app settings).
- **Never output secrets or connection strings** (the linter rule `outputs-should-not-contain-secrets`). Output resource names, ids, endpoints and principal ids instead.
- Managed identity (system-assigned unless shared) + RBAC role assignments, scoped to the specific resource with the narrowest built-in role. Prefer identity over keys/connection strings (Storage, Cosmos, Service Bus, Azure OpenAI).
- `httpsOnly: true`, `minTlsVersion: '1.2'`, FTPS disabled on App Service; public network access off where the app doesn't need it, and flag it when it does.
- Diagnostics to the existing Log Analytics / App Insights.

## Azure PaaS notes
- **App Service / Web Apps:** settings in `siteConfig.appSettings` (Key Vault references for secrets), health check path, `alwaysOn` on non-Free SKUs. The app setting names are a contract with the engineer's code.
- **Container Apps:** environment + app; ingress external/internal deliberately; secrets via Key Vault-referenced secrets with managed identity; ACR pull via identity (AcrPull role), not admin credentials; scale rules explicit.
- **Functions:** storage via identity-based connection where supported; Flex Consumption or Premium per card.
- Pin API versions to recent stable ones (no `-preview` unless required). Let `bicep lint` flag stale ones.

## Validation procedure (ops runs it; reviewer re-runs it)
```bash
az bicep build --file <main.bicep> --stdout >/dev/null    # compiles
az bicep lint  --file <main.bicep>                         # zero NEW warnings vs main
# what-if needs a target: only when the card or repo names a dev RG + subscription
az deployment group what-if --subscription <sub> --resource-group <rg> \
  --template-file <main.bicep> --parameters @<parameters.dev.json> --result-format ResourceIdOnly
```
- Compare lint warnings with `main` (`git stash` or a throwaway checkout) and report new vs pre-existing.
- Read the what-if: every **Delete** or replace must be intended and explained in the handoff.
- Run any repo script (e.g. `deploy/test-bicep.sh`) after reading it. If it deploys, don't run it; the deny rules block it anyway.
- Pipelines: validate YAML; every `secrets.*`/`vars.*` referenced must be listed in the handoff for the human to create.
- Containers: `docker build` locally; non-root user, pinned base image tag.

## Never (tool-blocked for ops and reviewer)
`az ... create|update|delete|set|deploy|start|stop|...`, `azd`, `az rest`, `kubectl apply|delete|...`, `helm install|upgrade`, `gh workflow run`, `gh secret`, `git push`. Deployment is a manual step: list the exact command in the handoff's `manual_steps`.

## Kubernetes (rarely used here)
Plain manifests or Helm as the repo already does; `kubectl apply --dry-run=client` and `helm template`/`helm lint` for validation only. Resource requests/limits, probes, non-root securityContext.
