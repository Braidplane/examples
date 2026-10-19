# Set up, run and inspect a recipe

Commands use Bash. Use isolated non-production resources and synthetic data. This guide changes Git authoring, Braidplane configuration and destination systems only when you run the explicit commands. It creates no schedules, hidden triggers or payload retention.

## Prerequisites

Use a compatible Braidplane deployment and the published public CLI pinned in cli-version.txt; alpha.5 cannot validate these left joins. Install Python 3 for integrity checks and jq for the commands below. Provider setup requires the selected recipe's native tools: psql, AWS CLI, Google Cloud BigQuery tooling, mongosh, MySQL client, or authorized HubSpot property administration as applicable. These tools do not run in ordinary CI.

Create a personal access token through your deployment's normal Account/Security flow, then authenticate using the supported CLI login. Select the API URL, organization, project and enabled environment explicitly. The API URL is deployment-specific: a local split app can use an `/api` prefix; use your deployment's documented API base. Keep tokens in the supported secure credential store, never in a committed connection file.

```sh
export BRAIDPLANE_SERVER_URL='<your-api-base-url>'
export BRAIDPLANE_ORG='<your-organization>'
export BRAIDPLANE_PROJECT='<your-dedicated-project>'
export BRAIDPLANE_ENVIRONMENT='<your-enabled-test-environment>'
read -r -s -p 'Personal access token: ' BRAIDPLANE_PAT
printf '\n'
export BRAIDPLANE_PAT
braidplane login
unset BRAIDPLANE_PAT
braidplane organization get
```

Your principal needs access to the selected organization/project, source/destination and saved-operation configuration, bindings, environment-aware validation, deployment, execution and run reads. Provider permissions are independent. Sources need read access; destinations need only their stated table/object/contact writes. Public reads never grant execute, reveal, or destination access. Protected environments require the exact `--confirm-environment` acknowledgement on the applicable mutation; it does not grant permission.

## Git authoring and target setup

Copy the complete collection into a writable Git repository/branch you control, keeping its relative paths. Commit your adapted specs and operations. Do not edit this public repository directly to store personal endpoints or credentials. A project Git backend is required: `pipeline apply` imports committed Git files, not an arbitrary local path.

If you need a new project/target, choose unused slugs and create them explicitly:

```sh
braidplane project create --name 'Recipe qualification' --slug "$BRAIDPLANE_PROJECT"
braidplane environment create --name 'Recipe test' --slug "$BRAIDPLANE_ENVIRONMENT"
braidplane environment project enable "$BRAIDPLANE_ENVIRONMENT"
```

If those resources already exist, inspect them and use the correct scope instead of recreating them. A catalog environment and project enablement are separate. Enabling a target does not bind connections or deploy a version.

Copy `connections/git.template.json` outside the checkout, replace all placeholders, and create its writable Git connection. The token file path is resolved relative to the connection JSON unless absolute; keep both outside Git. Attach an existing initialized branch containing the complete `recipes/` tree:

```sh
braidplane data-source create --file /absolute/path/outside-repo/git.connection.json
export RECIPE_GIT_SOURCE='<your-created-git-source-slug>'
export RECIPE_BRANCH='<your-committed-writable-branch>'
braidplane project pipeline-backend set "$BRAIDPLANE_PROJECT"   --mode adopt_existing --data-source "$RECIPE_GIT_SOURCE"   --tracked-branch "$RECIPE_BRANCH" --pipeline-dir recipes
```

Adopting existing files preserves Git as authoring authority. Importing a directory is authoritative for that scope; a narrower directory can remove materialized pipelines omitted from it. Keep the full configured directory and use the explicit pipeline filter when qualifying one recipe.

## Connections, saved operations and bindings

Use the selected recipe's provider setup and the matching `connections/*.template.json`. Copy templates outside the repository, replace placeholders, and use secret-file fields for credentials. Templates contain no endpoint, org, grant or credential from the qualification environment. For S3-compatible services, add their explicit endpoint and path-style setting. A self-hosted private-network target needs deployment approval plus its connection's supported private-host option; hosted workers cannot reach your laptop's localhost.

```sh
braidplane data-source test --file /absolute/path/outside-repo/source.connection.json
braidplane data-source create --file /absolute/path/outside-repo/source.connection.json
braidplane data-source test --file /absolute/path/outside-repo/destination.connection.json
braidplane data-source create --file /absolute/path/outside-repo/destination.connection.json
```

Create every saved operation listed in the selected recipe before validation. S3, BigQuery and HubSpot sink operations are saved resources in the qualified runtime. SQL sinks shown inline need no invented saved-query resource. Saved operations are connection-owned, so create each on the concrete connection that its logical ref will bind to.

Choose one slug and its canonical spec:

```sh
export RECIPE_SLUG='http-customer-enrichment' # choose a manifest entry
export RECIPE_SPEC="$(jq -r --arg s "$RECIPE_SLUG" '.recipes[] | select(.slug == $s) | .spec' manifest.json)"
braidplane pipeline validate --file "$RECIPE_SPEC" --local
braidplane pipeline apply --dir recipes --pipeline "$RECIPE_SLUG"
```

This materializes the committed remote version. The local file must match that commit; do not use a local-only edit as if deployed. Bind every ref using the recipe's exact commands and `bindings.template.json`. Bindings belong to this pipeline/environment, not to every pipeline with the same ref name. Then validate the selected target:

```sh
braidplane pipeline validate --file "$RECIPE_SPEC"
braidplane pipeline get "$RECIPE_SLUG" > /tmp/recipe-pipeline.json
export RECIPE_SPEC_HASH="$(jq -r '.current_version_spec_hash' /tmp/recipe-pipeline.json)"
braidplane pipeline version get "$RECIPE_SLUG" "$RECIPE_SPEC_HASH"
```

Offline validity is separate from target readiness. Fix missing/denied/invalid bindings in their owning scope; do not silently choose another environment. If the local spec changed after Git import, commit/push/apply it and repeat validation before deployment.

## Deploy, run and inspect

```sh
braidplane pipeline deploy "$RECIPE_SLUG" --spec-hash "$RECIPE_SPEC_HASH"
export RECIPE_RUN_SLUG='<a-new-unused-run-slug>'
braidplane pipeline run start "$RECIPE_SLUG" --run-slug "$RECIPE_RUN_SLUG"
braidplane pipeline run watch "$RECIPE_RUN_SLUG" --timeout-seconds 120
braidplane pipeline run get "$RECIPE_RUN_SLUG" > /tmp/recipe-run.json
```

Check that the run's `metadata.pipeline_version_spec_hash` equals the selected immutable version. Inspect its own timeline/step output metadata and each sink outcome. Do not substitute Current or a later attempt after a failure. Source snapshots, authored contracts, static Proof, sink acknowledgements and independent provider readback are distinct facts. A green run alone is insufficient: perform the recipe's destination comparison and check every expected row/byte/digest.

Retain sanitized evidence separately from credentials. `validation.json` and `execution.json` are dated qualification records for the included specs; they are not records of your new run. If adapting a recipe, create new evidence using your exact version/run identity. Raw values and provider replies must not enter ordinary diagnostics, issue reports or secret-bearing exports.

## Cleanup and replay consequences

Wait for runs to finish, then remove only the resources you created. These recipes create no triggers. To stop a recipe's configuration without deleting its history, remove its explicit bindings using the per-recipe list:

```sh
braidplane data-source-binding delete '<logical-ref>' --pipeline "$RECIPE_SLUG"
```

Delete a saved operation only after its consumers are removed and your deployment permits it:

```sh
braidplane query delete '<recipe-operation-slug>' --data-source '<your-destination-slug>'
```

For a project created solely for the exercise, `braidplane project delete "$BRAIDPLANE_PROJECT"` removes its project state after the platform's checks. Do not use `--cleanup-remote` on a shared Git repository: it deliberately changes remote authored files. An alternative is to remove the selected spec through a reviewed Git commit and re-import the complete configured directory. Deleting Braidplane configuration does not undo provider writes. The per-recipe provider cleanup commands are separate and must target only your isolated tables, object keys or test contacts.

A new run is not a retry, retained-input replay, rollback or proof of exactly-once delivery. File/object overwrites can be deterministic but can replace existing data. BigQuery append can duplicate records on a new run; the two reconciliation sinks are not atomic. MySQL/CRM upserts depend on stable keys and provider constraints. After a partial/unknown write, inspect the actual destination before deciding whether a new run is safe.
