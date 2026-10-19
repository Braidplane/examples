# Braidplane pipeline examples

Five synthetic workflows for authoring, adapting and inspecting Braidplane pipelines. Use the same [manifest](manifest.json) and canonical files whether you are a human or an agent.

| Task | Connectors and composition | Start here |
| --- | --- | --- |
| Enrich API orders, keeping unknown customers | HTTP + PostgreSQL left join → S3 JSON | [Customer enrichment](recipes/http-customer-enrichment/README.md) |
| Reconcile payments/refunds and unmatched ledger entries | S3 CSV + PostgreSQL → two BigQuery append branches | [Settlement reconciliation](recipes/settlement-ledger-reconciliation/README.md) |
| Apply spreadsheet overrides before CRM upsert | S3 XLSX + PostgreSQL precedence join → HubSpot | [Contact overrides](recipes/spreadsheet-contact-overrides/README.md) |
| Project document inventory into relational reporting | MongoDB JSON array → SQL rows → MySQL | [Inventory projection](recipes/document-inventory-projection/README.md) |
| Archive a file without parsing its bytes | HTTP file → S3 file | [File archive](recipes/opaque-file-archive/README.md) |

Read [setup and execution](GUIDE.md), [coverage and friction](COVERAGE.md), and the selected recipe before creating resources. Each recipe includes its full spec, operations where required, logical binding template, fixtures, expected output, and separate validation/execution records.

## Compatibility and evidence

The collection passed offline/ref-aware validation and controlled local runtime execution at the source revision in manifest.json. PostgreSQL, MongoDB, MySQL and S3-compatible storage were local containers; HTTP was a synthetic fixture. BigQuery and HubSpot were local protocol mocks. Their receipts do not establish Google Cloud or HubSpot account acceptance, provider retries, or production readiness.

The published [CLI v0.1.0-alpha.6](https://github.com/Braidplane/cli/releases/tag/v0.1.0-alpha.6) validates all five included specs. Both a fresh Go installation and the verified macOS ARM64 release archive passed; [public CLI validation](public-cli-validation.json) records the exact source and checks. Runtime/target-validation receipts retain their original source revision and provider limits. Public alpha.5 rejects the left joins used here; use the version pinned in cli-version.txt.

With the Go toolchain pinned in .go-version available, install the public CLI and check the collection (its install directory must be on PATH):

```sh
go install "github.com/Braidplane/cli/cmd/braidplane@$(cat cli-version.txt)"
python3 scripts/validate.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

## Ownership and reuse

Braidplane maintains this collection under [Apache-2.0](LICENSE). Report a reproducible problem through [Braidplane contact](https://braidplane.com/contact) with the recipe, manifest revision, CLI/server version and safe diagnostic reason. Exclude tokens, connection files, payloads and raw provider replies. Maintainers update canonical specs and evidence together. Release changes through review; never overwrite a historical receipt to hide an execution gap.
