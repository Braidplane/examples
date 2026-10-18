# Working with these examples

Start with README.md, manifest.json and GUIDE.md. Use the recipe's canonical spec, operations, bindings, fixtures and expected outputs. Keep credentials and local connection files outside the repository. Do not invent missing operations, silently substitute an inner join for unmatched-record handling, or infer delivery from a successful run.

Inspect validation.json and execution.json separately. Local protocol mocks do not establish cloud-provider acceptance. After changing a spec, qualify it again and refresh its file hash and exact version/run evidence; never relabel old receipts as current. Use scripts/validate.py for integrity plus the pinned public CLI's offline schema/semantic checks. Provider-dependent execution remains explicit and separate from CI.
