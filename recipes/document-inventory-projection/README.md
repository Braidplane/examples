# Project document inventory into MySQL reporting

MongoDB document array → supported row normalization → SQL projection/filter → MySQL keyed report. Negative stock is excluded; zero stock remains. No native JSON-path transform is implied.

Start with the [shared setup/run/cleanup guide](../../GUIDE.md). Commands below run from the repository root. [Spec](document-inventory-projection.pipeline.json), [bindings](bindings.template.json), [offline/target validation](validation.json), and [execution evidence](execution.json) are separate canonical records.

## Provider setup

Use an isolated MongoDB database and MySQL schema. The MongoDB source account needs find/read on recipe_inventory; the reporting writer needs SELECT/INSERT/UPDATE only on recipe_inventory_report. Provisioning requires separate table/collection administration.

Use [MongoDB](../../connections/mongodb.template.json) and [MySQL](../../connections/mysql.template.json) connection templates, exporting their slugs as `RECIPE_MONGODB_SOURCE` and `RECIPE_MYSQL_DEST`. Configure MongoDB Database Tools credentials in a protected file outside the checkout, and the MySQL client login-path outside Git:

```sh
mongoimport --config "$RECIPE_MONGO_TOOLS_CONFIG" --db "$RECIPE_MONGO_DATABASE" --collection recipe_inventory --jsonArray --file recipes/document-inventory-projection/fixtures/inventory.json
mysql --login-path=recipe-destination "$RECIPE_MYSQL_DATABASE" < recipes/document-inventory-projection/mysql-target.sql
```

The [mongoimport config file](https://www.mongodb.com/docs/database-tools/mongoimport/#std-option-mongoimport.--config) keeps provider passwords/URIs out of process arguments. It and the Braidplane connection credentials are separate clients that must select the same isolated target. The fixture marker is recipe=bp-1207; use a fresh collection or inspect existing marked records before import. The target's sku primary key is required for upsert behavior.

## Operations and logical bindings

The source and MySQL sink operations are fully inline in the spec; no saved operation is required.

Commit the canonical spec to your configured Git backend and import it as described in GUIDE.md, then bind the exact pipeline refs:

```sh
braidplane data-source-binding bind inventory-documents --pipeline document-inventory-projection --data-source "$RECIPE_MONGODB_SOURCE"
braidplane data-source-binding bind inventory-reporting --pipeline document-inventory-projection --data-source "$RECIPE_MYSQL_DEST"
```

Use RECIPE_SLUG=document-inventory-projection for the shared validate/deploy/run/inspect commands. The selected environment is explicit; binding or importing does not execute the pipeline.

## Expected results and independent inspection

Read the table independently with the MySQL client and compare both typed records in [expected.json](expected.json). SQL uses the runtime input relation, not a query against a hidden shared table:

```sh
mysql --login-path=recipe-destination --batch --skip-column-names "$RECIPE_MYSQL_DATABASE" -e "SELECT JSON_OBJECT('sku',sku,'quantity',quantity) FROM recipe_inventory_report ORDER BY sku" > /tmp/recipe-inventory.jsonl
python3 - <<'CHECK'
import json
rows=[json.loads(line) for line in open('/tmp/recipe-inventory.jsonl') if line.strip()]
assert rows == json.load(open('recipes/document-inventory-projection/expected.json'))
CHECK
```

[execution.json](execution.json) records the local MongoDB/MySQL run, exact immutable spec version, source/transform/sink events and destination comparison. Nested/missing/mixed-type documents outside the declared fixture shape are not silently flattened.

## Write and replay consequences

The inline MySQL operation inserts or updates by sku. It can overwrite quantity for the same primary key; there is no deletion of other rows or cross-system transaction. deduplicated_by_ledger is not a general exactly-once database claim. Inspect existing report rows before a new run after partial/unknown effects. No incremental watermark or CDC is configured.

## Cleanup

In the isolated provider targets created for the recipe, drop recipe_inventory_report and remove only MongoDB documents with recipe=bp-1207. Do not drop a shared database or unrelated collections. Retire the two bindings using the shared guide. This recipe has no saved sink operation to delete; its complete SQL is inline in the spec.
