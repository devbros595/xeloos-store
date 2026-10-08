from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0009_repair_orderitem_schema"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE orders_orderitem
                DROP COLUMN IF EXISTS sim_name;

                ALTER TABLE orders_orderitem
                DROP COLUMN IF EXISTS sim_price;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]