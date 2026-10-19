from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAttributeImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.choice, cls.other = cls.env["product.attribute"].create([
            {"name": "THA Import Choice", "create_variant": "no_variant"},
            {"name": "THA Import Sausage & Mozzarella", "create_variant": "no_variant"},
        ])
        cls.choice_values = cls.env["product.attribute.value"].create([
            {"name": name, "attribute_id": cls.choice.id}
            for name in ["Chicken", "Sausage", "Cheese"]
        ])
        cls.other_value = cls.env["product.attribute.value"].create({
            "name": "Sausage", "attribute_id": cls.other.id,
        })
        cls.products = cls.env["product.template"].with_context(import_file=True)
        cls.columns = ["name", "attribute_line_ids/attribute_id", "attribute_line_ids/value_ids"]

    def test_duplicate_name_scoped_to_attribute(self):
        result = self.products.load(self.columns, [[
            "THA Import Test", self.choice.name, "Chicken,Sausage,Cheese",
        ]])
        self.assertFalse(result["messages"], result)
        product = self.products.browse(result["ids"])
        self.assertEqual(product.attribute_line_ids.value_ids, self.choice_values)

    def test_multiple_lines_and_reversed_column_order(self):
        columns = [self.columns[0], self.columns[2], self.columns[1]]
        result = self.products.load(columns, [
            ["THA Import Two Lines", "Sausage, Cheese", self.choice.name],
            ["", "Sausage", self.other.name],
        ])
        self.assertFalse(result["messages"], result)
        lines = self.products.browse(result["ids"]).attribute_line_ids
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines.filtered(lambda line: line.attribute_id == self.other).value_ids, self.other_value)

    def test_value_only_in_other_attribute_is_rejected(self):
        result = self.products.load(self.columns, [[
            "THA Import Invalid", self.other.name, "Chicken",
        ]])
        self.assertFalse(result["ids"], result)
        self.assertTrue(any("Chicken" in message["message"] and self.other.name in message["message"]
                            for message in result["messages"]), result)
        self.assertFalse(self.products.search([("name", "=", "THA Import Invalid")]))

    def test_database_ids_remain_supported(self):
        columns = ["name", "attribute_line_ids/attribute_id/.id", "attribute_line_ids/value_ids/.id"]
        result = self.products.load(columns, [[
            "THA Import IDs", str(self.other.id), str(self.other_value.id),
        ]])
        self.assertFalse(result["messages"], result)
        self.assertEqual(self.products.browse(result["ids"]).attribute_line_ids.value_ids, self.other_value)

    def test_ambiguous_attribute_is_rejected(self):
        self.env["product.attribute"].create({"name": self.choice.name})
        result = self.products.load(self.columns, [[
            "THA Import Ambiguous", self.choice.name, "Sausage",
        ]])
        self.assertFalse(result["ids"], result)
        self.assertTrue(any("ambiguous" in message["message"] for message in result["messages"]), result)

    def test_attribute_database_id_with_value_names(self):
        columns = ["name", "attribute_line_ids/attribute_id/.id", self.columns[2]]
        result = self.products.load(columns, [[
            "THA Import Attribute ID", str(self.other.id), "Sausage",
        ]])
        self.assertFalse(result["messages"], result)
        self.assertEqual(self.products.browse(result["ids"]).attribute_line_ids.value_ids, self.other_value)

    def test_one_value_per_row(self):
        result = self.products.load(self.columns, [
            ["THA Import Vertical", self.choice.name, "Chicken"],
            ["", "", "Sausage"],
            ["", "", "Cheese"],
        ])
        self.assertFalse(result["messages"], result)
        lines = self.products.browse(result["ids"]).attribute_line_ids
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.attribute_id, self.choice)
        self.assertEqual(lines.value_ids, self.choice_values)

    def test_continuation_switches_attribute_and_product(self):
        columns = [self.columns[0], self.columns[2], self.columns[1]]
        result = self.products.load(columns, [
            ["THA Import Vertical First", "Chicken", self.choice.name],
            ["", "Sausage, Cheese", ""],
            ["", "Sausage", self.other.name],
            ["THA Import Vertical Second", "Sausage", self.other.name],
            ["", "Sausage", ""],
        ])
        self.assertFalse(result["messages"], result)
        first, second = self.products.browse(result["ids"])
        self.assertEqual(len(first.attribute_line_ids), 2)
        self.assertEqual(first.attribute_line_ids.filtered(
            lambda line: line.attribute_id == self.choice
        ).value_ids, self.choice_values)
        self.assertEqual(second.attribute_line_ids.attribute_id, self.other)
        self.assertEqual(second.attribute_line_ids.value_ids, self.other_value)

    def test_continuation_does_not_cross_product_boundary(self):
        result = self.products.load(self.columns, [
            ["THA Import Boundary First", self.choice.name, "Chicken"],
            ["THA Import Boundary Second", "", "Cheese"],
        ])
        self.assertFalse(result["ids"], result)
        self.assertTrue(any(message["type"] == "error" for message in result["messages"]), result)

    def test_invalid_continuation_value_is_rejected(self):
        result = self.products.load(self.columns, [
            ["THA Import Vertical Invalid", self.other.name, "Sausage"],
            ["", "", "Chicken"],
        ])
        self.assertFalse(result["ids"], result)
        self.assertTrue(any("Chicken" in message["message"] and self.other.name in message["message"]
                            for message in result["messages"]), result)

    def test_continuation_database_ids(self):
        columns = ["name", "attribute_line_ids/attribute_id/.id", "attribute_line_ids/value_ids/.id"]
        result = self.products.load(columns, [
            ["THA Import Vertical IDs", str(self.choice.id), str(self.choice_values[0].id)],
            ["", "", str(self.choice_values[1].id)],
            ["", "", str(self.choice_values[2].id)],
        ])
        self.assertFalse(result["messages"], result)
        lines = self.products.browse(result["ids"]).attribute_line_ids
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.value_ids, self.choice_values)
