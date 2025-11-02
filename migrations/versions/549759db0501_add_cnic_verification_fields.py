"""
Migration: Add CNIC and verification fields to User model

This migration adds:
- cnic: National ID number (nullable, unique)
- cnic_verified: Boolean flag for verification status
- verification_notes: Admin notes about verification
- verified_at: Timestamp when verification was completed
- verified_by: Foreign key to admin user who verified
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = 'add_cnic_verification'
down_revision = None  # Replace with your latest migration revision
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('cnic', sa.String(length=15), nullable=True))
    op.add_column('users', sa.Column('cnic_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_notes', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('verified_by_id', sa.Integer(), nullable=True))
    
    # Add unique constraint on cnic
    op.create_unique_constraint('uq_users_cnic', 'users', ['cnic'])
    
    # Add foreign key constraint for verified_by
    op.create_foreign_key(
        'fk_users_verified_by_id_users',
        'users', 'users',
        ['verified_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for faster queries on verification status
    op.create_index('idx_users_cnic_verified', 'users', ['cnic_verified'])


def downgrade():
    # Remove index
    op.drop_index('idx_users_cnic_verified', table_name='users')
    
    # Remove foreign key
    op.drop_constraint('fk_users_verified_by_id_users', 'users', type_='foreignkey')
    
    # Remove unique constraint
    op.drop_constraint('uq_users_cnic', 'users', type_='unique')
    
    # Remove columns
    op.drop_column('users', 'verified_by_id')
    op.drop_column('users', 'verified_at')
    op.drop_column('users', 'verification_notes')
    op.drop_column('users', 'cnic_verified')
    op.drop_column('users', 'cnic')