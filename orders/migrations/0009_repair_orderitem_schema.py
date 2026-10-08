from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_repair_missing_flutterwave_fields"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE orders_orderitem
                ADD COLUMN IF NOT EXISTS product_type varchar(20);

                ALTER TABLE orders_orderitem
                ADD COLUMN IF NOT EXISTS product_id integer;

                ALTER TABLE orders_orderitem
                ADD COLUMN IF NOT EXISTS product_name varchar(200);

                ALTER TABLE orders_orderitem
                ADD COLUMN IF NOT EXISTS product_price numeric(10, 2);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]