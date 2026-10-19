from odoo import api, models, _


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

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
