# Local validation - 2026-10-19

- Database: THA17, development Compose project `odoo_17_projects`.
- Module upgraded: `tha_product_attribute_import`, version `17.0.1.0.1`.
- Python AST and literal manifest validation passed for all six Python files.
- No XML files or new models/fields/security records are introduced.
- Native Odoo import backend regression suite: 11 tests, 0 failures, 0 errors.
- Covered: duplicate values in different attributes; multiple attribute lines;
  reversed column order; whitespace around values; a value belonging only to
  another attribute; ambiguous attribute names; explicit database references;
  attribute database reference with name-based values; one value per row with
  blank attribute continuation; mixed comma/vertical rows; attribute switches;
  product boundaries; rejected values in continuation rows; vertical database IDs.
- Tests use transactional fixtures that are rolled back.
- Development stack brought up with `docker compose up -d --wait`, then Odoo
  restarted. Module installation state confirmed with a read-only database query.
- Browser XLSX upload and production deployment were not performed.

The maintenance command printed an existing PostgreSQL `postgres` database
collation warning (database version 2.41, operating system 2.36). Installation
and all module tests completed successfully; no collation changes were made.

The negative product-boundary test intentionally omitted the attribute on a new
product. Odoo rejected it with the native required-attribute constraint (logged
SQL errors during that test); the suite confirmed no inheritance across products.
