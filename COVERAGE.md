# Coverage and composition friction

Qualified 2026-10-18 against the canonical source revision and exact spec hashes in manifest.json. These observations describe synthetic non-production compositions, not customer demand, production readiness or vendor parity.

| Recipe | Source boundary | Transform / relation pattern | Sink boundary | Observed qualification |
| --- | --- | --- | --- | --- |
| HTTP customer enrichment | HTTP JSON array plus PostgreSQL rows | Named orders/customers inputs; left join; explicit unmatched fallback | Rows serialized as JSON object content in S3-compatible storage | Real local HTTP/PostgreSQL/SeaweedFS execution; two expected rows independently read back |
| Settlement/ledger reconciliation | S3 CSV normalized to rows; PostgreSQL integer ledger | Named inputs; signed integer-cent arithmetic; two left/anti-join branches | Two independent BigQuery append writes | Runtime execution against a local BigQuery protocol mock; five exact records and 1800/1550/250-cent totals independently read back. Google Cloud and public connection-creation flow unexercised |
| Spreadsheet contact overrides | S3 XLSX worksheet/range normalized to rows; PostgreSQL contacts | Named inputs; NULLIF/COALESCE precedence; blank override retains source value | HubSpot keyed contact upsert | Runtime execution with a local CRM protocol mock, unique-property prerequisite and direct provider readback. Real account entitlements/workflows/delivery not exercised |
| Document inventory projection | MongoDB JSON document array | Supported row normalization; nonnegative inventory filter; rows projection | MySQL primary-key insert/update using input relation | Local MongoDB/MySQL execution and exact two-row independent table comparison |
| Opaque file archive | HTTP octet-stream runtime file | No relational transform or re-encoding | S3-compatible format:file write | Local execution and independent 31-byte/SHA256 equality |

All five specs passed local CLI validation and target-aware validation before deployment. Each execution.json retains the run, executed spec hash, observed step events and independent destination comparison; validation.json and the raw-file hash remain separate. Diagnostics do not retain customer values for historical inspection. Existing checkpoint/replay storage is a different capability.

## Friction and limits

| Observation | Resolution / owner / remaining limit |
| --- | --- |
| Public CLI alpha.5 rejects left joins although the current source runtime supports them | Public CLI publication prerequisite under BP-1207. The canonical export allowlist correction is prepared; no claim of alpha.5 compatibility. CI pins the intended refreshed alpha.6 release and cannot pass public installation until it is actually published |
| Canonical CLI export omitted 33 already-tracked shared source/test/enum files | Explicit manifest correction in the canonical Braidplane repository, followed by repeatable export, standalone tests and unchanged generation. A local snapshot is not a public release |
| An offline-valid inline S3 sink failed at runtime because config.key and a saved operation are required | Use the documented saved operation plus explicit S3 sink config. BigQuery and HubSpot also use saved sinks. SQL sink remains supported inline. This collection does not implement missing inline adapter behavior |
| ORDER BY requires unqualified projected field names; integer CAST syntax is SIGNED | Specs use the supported SQL dialect explicitly. The engine is not arbitrary PostgreSQL/GoogleSQL/MySQL execution |
| Reconciliation UNION was rejected | Preserve both unmatched directions with two explicit transforms and two sink writes. No hidden union adapter, new dialect, dropped rows or atomic multi-sink guarantee |
| Target-aware type inference classified arithmetic as number | Explicitly cast cent differences to SIGNED, retaining the integer contract and exact expected calculations |
| HubSpot upsert failed without the declared unique custom property | Provider setup requires external_customer_id as a unique string, plus mapped property access. A policy or pipeline declaration does not create that provider schema or grant |
| Public BigQuery config has no arbitrary provider/token URL override | Local protocol fixture seeded through the existing service boundary; real users configure the actual Google provider/project/table and service account. No public API widening or deployment bypass |
| Applying a partial Git directory can remove omitted materialized pipelines | Use the complete configured recipes directory and the pipeline filter. Keep Git authoring authority visible and preserve unrelated authored specs |
| Declared query contract is not proof every boundary was checked | Deliberate malformed cents failed at the observed transform boundary with transform_contract_mismatch. No sink started. Keep that reason and boundary; do not label it a source check |
| Missing document-api binding | Target validation refused DATA_SOURCE_BINDING_NOT_FOUND before execution. Fix that pipeline/environment binding; do not infer readiness from offline validity |
| Append, overwrites, upserts and multiple sinks have different consequences | Inspect each independent sink and actual destination. New runs can duplicate BigQuery appends or overwrite keyed data. Effect-ledger metadata is not global exactly-once execution, rollback or external processing proof |

No quality/freshness evaluator, retained payload preview, implicit completion trigger, artifact follow-on read, general native JSON transform or provider account automation is added. Unsupported shape/representation/permission cases remain explicit failures rather than examples that quietly change the task.

## Evidence freshness and maintenance

After changing a spec, operation, fixture or provider precondition, rerun the affected validation and controlled execution, compare expected output and independent sink effects, and record the exact new identities. Keep historical receipts as dated records; do not edit their observed outcomes to match a new spec. Ordinary CI checks canonical integrity and calls the pinned CLI offline validator. It neither authenticates provider resources nor replays external writes.
