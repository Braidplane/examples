# Enrich API orders with customer segments

HTTP JSON order array + PostgreSQL customer rows → named orders/customers left join → S3 JSON object. Unknown customers remain present with segment unmatched.

Start with the [shared setup/run/cleanup guide](../../GUIDE.md). Commands below run from the repository root. [Spec](http-customer-enrichment.pipeline.json), [bindings](bindings.template.json), [offline/target validation](validation.json), and [execution evidence](execution.json) are separate canonical records.

## Provider setup

Use a synthetic HTTP server reachable by the Braidplane worker. Its `/health` returns success and `/orders` returns [fixtures/orders.json](fixtures/orders.json) with `Content-Type: application/json`. It must not wrap the array in an envelope. The PostgreSQL source needs SELECT on `recipe_customers`. Create that table once in an empty isolated database using the canonical fixture:

```sh
psql 'service=recipe-source' -v ON_ERROR_STOP=1 -f recipes/http-customer-enrichment/fixtures/source.sql
```

The PostgreSQL service profile and password file belong outside this repository. Create an isolated S3 bucket/prefix with write access to `recipes/enriched-orders.json`; the connection prefix is prepended to that key. Use [HTTP](../../connections/http.template.json), [PostgreSQL](../../connections/postgres.template.json), and [S3 destination](../../connections/s3-destination.template.json) templates. Export their created slugs as `RECIPE_HTTP_SOURCE`, `RECIPE_PG_SOURCE`, and `RECIPE_OBJECT_DEST`.

For a self-hosted qualification worker that can reach this machine, serve only the canonical synthetic routes in another terminal:

```sh
export RECIPE_HTTP_BIND='<interface-address-reachable-by-your-worker>'
export RECIPE_HTTP_PORT='<available-port>'
python3 scripts/serve_http_fixtures.py --bind "$RECIPE_HTTP_BIND" --port "$RECIPE_HTTP_PORT"
```

Set the HTTP connection base_url to that server and health_check_path to /health. This is an unauthenticated test-only HTTP fixture, not an Internet deployment. For hosted execution, use your authorized reachable HTTPS fixture host with the same routes, bytes and content types. Stop the local fixture with Ctrl-C after the exercise.

## Operations and logical bindings

Create the exact saved operation on its destination before validation:

```sh
braidplane query create --data-source "$RECIPE_OBJECT_DEST" --name "Enrich API orders with customer segments write" --slug http-customer-enrichment-write --statement-file recipes/http-customer-enrichment/operations/write.statement.json
```

Commit the canonical spec to your configured Git backend and import it as described in GUIDE.md, then bind the exact pipeline refs:

```sh
braidplane data-source-binding bind orders-api --pipeline http-customer-enrichment --data-source "$RECIPE_HTTP_SOURCE"
braidplane data-source-binding bind customer-db --pipeline http-customer-enrichment --data-source "$RECIPE_PG_SOURCE"
braidplane data-source-binding bind enriched-export --pipeline http-customer-enrichment --data-source "$RECIPE_OBJECT_DEST"
```

Use RECIPE_SLUG=http-customer-enrichment for the shared validate/deploy/run/inspect commands. The selected environment is explicit; binding or importing does not execute the pipeline.

## Expected results and independent inspection

The [expected output](expected.json) has two orders. `o-1` is wholesale; `o-2` has segment unmatched. Read the actual object independently using your authenticated AWS CLI profile (and explicit endpoint setting for compatible stores):

```sh
aws s3 cp "s3://$RECIPE_BUCKET/$RECIPE_PREFIX/recipes/enriched-orders.json" /tmp/recipe-enriched-orders.json
python3 - <<'CHECK'
import json
assert json.load(open('/tmp/recipe-enriched-orders.json')) == json.load(open('recipes/http-customer-enrichment/expected.json'))
CHECK
```

`RECIPE_BUCKET` and `RECIPE_PREFIX` must match your destination connection. Compare the exact run version and both source/transform row metadata with [execution.json](execution.json); those records belong to the dated qualification, not your new run.

## Write and replay consequences

The destination overwrites one fixed object key. An explicit new run can replace its previous content; naturally_idempotent does not protect unrelated data at that key. A later source change changes the object. There is no global exactly-once guarantee, retained-value preview or completion trigger.

## Deliberate failure case

[negative/orders.contract-mismatch.json](negative/orders.contract-mismatch.json) replaces one integer cent value with a nonnumeric string. Serve that input deliberately only in your isolated HTTP fixture, then explicitly start a new run of the same selected version. The observed [negative receipt](negative/contract-mismatch.evidence.json) failed at enrich-orders with transform_contract_mismatch before export-orders started. It does not claim a source-boundary evaluation. Restore the valid provider response and validate before a new run; do not loosen the integer-cent contract just to accept malformed data.

## Cleanup

Remove only your `recipes/enriched-orders.json` object with `aws s3 rm "s3://$RECIPE_BUCKET/$RECIPE_PREFIX/recipes/enriched-orders.json"`. In the isolated source database created for this recipe, `DROP TABLE recipe_customers;` removes the fixture. Follow the shared guide to remove the three bindings and the saved operation. Do not delete a shared bucket or connection.
