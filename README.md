# THA Product Attribute Import (Odoo 17)

Import product attribute values by name within the attribute on the same line.
Install this addon on the database where products are imported. No settings are needed.

Keep the usual Excel/CSV columns and import mappings:

| Name | Product Attributes/Attribute | Product Attributes/Values |
| --- | --- | --- |
| Example Product | Choice | Chicken,Sausage,Cheese |
| | Sausage & Mozzarella | Sausage |

The second row is an optional additional attribute for the same product; leave
the product fields blank. Supply the attribute on every attribute line.

`Sausage` on the first row resolves only under `Choice`, even if another attribute
also contains `Sausage`. Spaces around comma-separated values are ignored.
Values must already exist under the selected attribute. Missing values and
ambiguous attribute names block the import with an error. Use attribute External
IDs or Database IDs when attribute names themselves are duplicated.

Native value External ID/Database ID imports remain supported. Without an
attribute column, native Odoo matching applies. Names containing commas should
be imported using IDs. The addon does not change existing product configuration
or values and adds no fields or access rights. It extends only conversion of
`product.template.attribute.line`, including nested product imports.

## Validation

The regression suite exercises the native `load()` import backend with duplicate
value names, multiple attribute rows, reversed columns, missing scoped values,
database references and ambiguous attributes. Test fixtures are rolled back.

```powershell
docker compose stop gateway_17 odoo_17
docker compose run --rm --no-deps odoo_17 odoo -c /run/odoo/odoo.conf -d THA17 -i tha_product_attribute_import --stop-after-init --no-http --workers=0 --max-cron-threads=0 --test-enable --test-tags /tha_product_attribute_import
docker compose up -d --wait
docker compose restart odoo_17
```
