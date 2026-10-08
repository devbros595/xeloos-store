from django.db import migrations


def remove_legacy_fields(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("""
            ALTER TABLE orders_orderitem
            DROP COLUMN IF EXISTS sim_name;

            ALTER TABLE orders_orderitem
            DROP COLUMN IF EXISTS sim_price;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0009_repair_orderitem_schema"),
    ]

    operations = [
        migrations.RunPython(
            remove_legacy_fields,
            reverse_code=migrations.RunPython.noop,
        ),
    ]