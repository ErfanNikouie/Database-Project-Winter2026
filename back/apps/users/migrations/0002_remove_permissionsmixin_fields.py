from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="groups",
        ),
        migrations.RemoveField(
            model_name="user",
            name="user_permissions",
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE IF EXISTS user_groups_ref RENAME TO user_user_group;",
                    reverse_sql="ALTER TABLE IF EXISTS user_user_group RENAME TO user_groups_ref;",
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="user",
                    name="groups_ref",
                    field=models.ManyToManyField(
                        blank=True,
                        db_table="user_user_group",
                        related_name="users",
                        to="users.usergroup",
                    ),
                ),
                migrations.AlterField(
                    model_name="user",
                    name="is_superuser",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]


