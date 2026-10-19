from odoo import api, models, _


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def _str_to_one2many(self, model, field, records):
        if field.comodel_name == "product.template.attribute.line":
            records = self.tha_merge_attribute_value_rows(records)
        return super()._str_to_one2many(model, field, records)

    @api.model
    def tha_merge_attribute_value_rows(self, records):
        """Fold value-only continuation rows within this product's lines.

        The extractor has already grouped rows by product. Never carry state
        between conversions, so a new product must supply its own attribute.
        Keep line references and additional writable fields as native rows.
        """
        merged = []
        for record in records:
            values = record.get("value_ids")
            previous = merged[-1] if merged else {}
            previous_values = previous.get("value_ids")
            if (
                not record.get("attribute_id")
                and set(record) <= {"attribute_id", "value_ids"}
                and previous.get("attribute_id")
                and values and len(values) == 1
                and previous_values and len(previous_values) == 1
                and len(values[0]) == 1
                and set(values[0]) == set(previous_values[0])
                and next(iter(values[0])) in (None, "id", ".id")
            ):
                key = next(iter(values[0]))
                merged[-1] = dict(previous, value_ids=[{
                    key: ",".join(filter(None, [previous_values[0][key], values[0][key]])),
                }])
            else:
                merged.append(record)
        return merged

    @api.model
    def for_model(self, model, fromtype=str):
        convert = super().for_model(model, fromtype=fromtype)
        if model._name != "product.template.attribute.line" or fromtype is not str:
            return convert

        def convert_attribute_line(record, log):
            try:
                record = self.tha_scope_attribute_values(model, record)
            except ValueError as error:
                log("value_ids", error)
                return {}
            return convert(record, log)

        return convert_attribute_line

    @api.model
    def tha_scope_attribute_values(self, model, record):
        """Resolve sibling fields before Odoo converts them independently.

        Rewrite only name-based values to database references, leaving Odoo's
        own command generation, ID imports and access checks in place.
        """
        attributes = record.get("attribute_id")
        values = record.get("value_ids")
        if not attributes or not values or len(values) != 1:
            return record
        value_record = values[0]
        if set(value_record) != {None} or not value_record[None]:
            return record

        attribute_id, warnings = self._str_to_many2one(
            model, model._fields["attribute_id"], attributes
        )
        if warnings:
            raise ValueError(_(
                "The attribute reference is ambiguous. Use a unique attribute "
                "name, External ID or Database ID."
            ))
        if not attribute_id:
            raise ValueError(_("An attribute is required to match its values."))

        self.env.context.get("import_flush", lambda **kw: None)(
            model="product.attribute.value"
        )
        attribute = self.env["product.attribute"].browse(attribute_id)
        value_ids = []
        for name in value_record[None].split(","):
            name = name.strip()
            matches = self.env["product.attribute.value"].search([
                ("attribute_id", "=", attribute_id), ("name", "=", name),
            ], limit=2)
            if len(matches) != 1:
                raise ValueError(_(
                    "Expected one value '%(value)s' under attribute '%(attribute)s'; "
                    "found %(count)s. Check the value in that attribute.",
                    value=name, attribute=attribute.name, count=len(matches),
                ).replace("%", "%%"))
            value_ids.append(str(matches.id))
        return dict(record, value_ids=[{".id": ",".join(value_ids)}])
