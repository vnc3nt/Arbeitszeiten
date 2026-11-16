from sqlalchemy import text
from models import db, users, profiles


def ensure_profile_image_column():
    db.session.execute(text("ALTER TABLE arbeitszeiten.users ADD COLUMN IF NOT EXISTS profile_image TEXT"))
    db.session.execute(text("ALTER TABLE arbeitszeiten.users ALTER COLUMN profile_image TYPE TEXT"))
    db.session.commit()


def ensure_profiles():
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS arbeitszeiten.profiles (
            id BIGSERIAL PRIMARY KEY,
            userid BIGINT NOT NULL REFERENCES arbeitszeiten.users(id),
            name VARCHAR(30) NOT NULL,
            maxhours NUMERIC(5, 2) NOT NULL DEFAULT 0,
            visible BOOLEAN NOT NULL DEFAULT TRUE,
            CONSTRAINT uq_profiles_user_name UNIQUE (userid, name)
        )
    """))
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.data ADD COLUMN IF NOT EXISTS profileid BIGINT")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.category ADD COLUMN IF NOT EXISTS profileid BIGINT")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS maxhours NUMERIC(5, 2) NOT NULL DEFAULT 0")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS visible BOOLEAN NOT NULL DEFAULT TRUE")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS position INT NOT NULL DEFAULT 0")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles ADD COLUMN IF NOT EXISTS color VARCHAR(7)")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.users ADD COLUMN IF NOT EXISTS language VARCHAR(10) NOT NULL DEFAULT 'de'")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.users ADD COLUMN IF NOT EXISTS theme VARCHAR(10) NOT NULL DEFAULT 'auto'")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.users ADD COLUMN IF NOT EXISTS last_profile_id BIGINT")
    )
    db.session.execute(
        text("ALTER TABLE arbeitszeiten.profiles DROP COLUMN IF EXISTS profile_image")
    )
    db.session.execute(text("ALTER TABLE arbeitszeiten.data DROP CONSTRAINT IF EXISTS data_pkey"))

    # Synchronisiere einmalig die PostgreSQL-Sequenzen mit den höchsten vorhandenen IDs (sicher für SERIAL & IDENTITY)
    db.session.execute(text("""
        DO $$
        DECLARE
            tbl text;
            seq text;
        BEGIN
            FOR tbl IN SELECT unnest(ARRAY['profiles', 'users', 'category'])
            LOOP
                seq := pg_get_serial_sequence('arbeitszeiten.' || tbl, 'id');
                IF seq IS NOT NULL THEN
                    EXECUTE format(
                        'SELECT setval(%L, COALESCE((SELECT MAX(id) FROM arbeitszeiten.%I), 1), (SELECT MAX(id) FROM arbeitszeiten.%I) IS NOT NULL)',
                        seq, tbl, tbl
                    );
                END IF;
            END LOOP;
        END $$;
    """))

    for user in db.session.query(users).all():
        has_profile = db.session.query(profiles).filter_by(userid=user.id).first()
        if has_profile is None:
            # Nur wenn der User noch überhaupt kein Profil hat, ein Initial-Profil anlegen
            default_profile = profiles(
                userid=user.id,
                name="Standardprofil",
                maxhours=0,
                visible=True,
                position=0,
            )
            db.session.add(default_profile)
            db.session.flush()

    # Bulk-Update einmalig außerhalb der User-Schleife für alte Einträge ohne profileid
    db.session.execute(text("""
        UPDATE arbeitszeiten.data d
        SET profileid = sub.id
        FROM (
            SELECT DISTINCT ON (userid) userid, id
            FROM arbeitszeiten.profiles
            ORDER BY userid, position ASC, id ASC
        ) sub
        WHERE d.userid = sub.userid
          AND d.profileid IS NULL
    """))
    db.session.execute(text("""
        UPDATE arbeitszeiten.category c
        SET profileid = sub.id
        FROM (
            SELECT DISTINCT ON (userid) userid, id
            FROM arbeitszeiten.profiles
            ORDER BY userid, position ASC, id ASC
        ) sub
        WHERE c.userid = sub.userid
          AND c.profileid IS NULL
    """))
    db.session.execute(text("""
        ALTER TABLE arbeitszeiten.data
        ADD CONSTRAINT data_pkey PRIMARY KEY (userid, date, profileid)
    """))
    db.session.commit()
