from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("product_id", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )


def downgrade():
    op.drop_table("cart_items")
