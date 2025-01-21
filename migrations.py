async def m000_create_migrations_table(db):
    """Create the migrations table."""
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS boltt.dbversions (
            db TEXT PRIMARY KEY,
            version INTEGER NOT NULL
        );
        """
    )

async def m001_initial(db):
    """Create initial tables."""
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS boltt.cards (
            id TEXT PRIMARY KEY UNIQUE,
            wallet TEXT NOT NULL,
            card_name TEXT NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            external_id TEXT NOT NULL UNIQUE,
            counter INT NOT NULL DEFAULT 0,
            tx_limit TEXT NOT NULL,
            daily_limit TEXT NOT NULL,
            enable BOOL NOT NULL,
            k0 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            k1 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            k2 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            prev_k0 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            prev_k1 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            prev_k2 TEXT NOT NULL DEFAULT '00000000000000000000000000000000',
            otp TEXT NOT NULL DEFAULT '',
            time TIMESTAMP NOT NULL DEFAULT """
        + db.timestamp_now
        + """
        );
    """
    )

    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS boltt.hits (
            id TEXT PRIMARY KEY UNIQUE,
            card_id TEXT NOT NULL,
            ip TEXT NOT NULL,
            spent BOOL NOT NULL DEFAULT True,
            useragent TEXT,
            old_ctr INT NOT NULL DEFAULT 0,
            new_ctr INT NOT NULL DEFAULT 0,
            amount {db.big_int} NOT NULL,
            time TIMESTAMP NOT NULL DEFAULT """
        + db.timestamp_now
        + """
        );
    """
    )

    await db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS boltt.refunds (
            id TEXT PRIMARY KEY UNIQUE,
            hit_id TEXT NOT NULL,
            refund_amount {db.big_int} NOT NULL,
            time TIMESTAMP NOT NULL DEFAULT """
        + db.timestamp_now
        + """
        );
    """
    )

async def m002_rename_tx_limit(db):
    """Rename tx_limit column to verification_limit."""
    # First create new column
    await db.execute(
        """
        ALTER TABLE boltt.cards ADD COLUMN verification_limit TEXT;
        """
    )
    
    # Copy data from old column to new column
    await db.execute(
        """
        UPDATE boltt.cards SET verification_limit = tx_limit;
        """
    )
    
    # Make new column NOT NULL after data is copied
    await db.execute(
        """
        ALTER TABLE boltt.cards ALTER COLUMN verification_limit SET NOT NULL;
        """
    )
    
    # Drop old column
    await db.execute(
        """
        ALTER TABLE boltt.cards DROP COLUMN tx_limit;
        """
    )