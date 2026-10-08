from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_order_user"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE orders_order
                ADD COLUMN IF NOT EXISTS delivery_method varchar(50) NOT NULL DEFAULT '';

                ALTER TABLE orders_order
                ADD COLUMN IF NOT EXISTS delivery_fee numeric(10, 2) NOT NULL DEFAULT 0;

                ALTER TABLE orders_order
                ADD COLUMN IF NOT EXISTS payment_method varchar(20) NOT NULL DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]