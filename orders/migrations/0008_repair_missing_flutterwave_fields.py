from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0007_repair_missing_order_fields"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE orders_order
                ADD COLUMN IF NOT EXISTS flutterwave_tx_ref varchar(100);

                ALTER TABLE orders_order
                ADD COLUMN IF NOT EXISTS flutterwave_transaction_id varchar(100);

                CREATE UNIQUE INDEX IF NOT EXISTS
                orders_order_flutterwave_tx_ref_unique
                ON orders_order (flutterwave_tx_ref)
                WHERE flutterwave_tx_ref IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]