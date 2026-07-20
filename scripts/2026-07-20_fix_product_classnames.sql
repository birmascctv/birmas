-- One-off data fix applied 2026-07-20.
-- Root cause: `product.class_name` had a stale "01ot_" prefix that never
-- matched the deployed model's actual class names ("ot_..."), so every
-- Orang Tua event resolved to product_brand/product_name = "Unknown".
-- Also 4 of the model's 16 classes had no row at all.
--
-- This script is a record of what was run directly against the `birmas`
-- database. It is idempotent-ish (DELETE + INSERT) but do not re-run
-- blindly if class_name values have since changed.

BEGIN;

DELETE FROM product WHERE class_name LIKE '01ot_%';

INSERT INTO product (class_id, class_name, product_brand, product_name) VALUES
  (0,  'ot_amerB',      'Orang Tua', 'Anggur Merah 620ml'),
  (1,  'ot_amergoldB',  'Orang Tua', 'Anggur Merah Gold 620ml'),
  (2,  'ot_amergoldS',  'Orang Tua', 'Anggur Merah Gold 275ml'),
  (3,  'ot_amerS',      'Orang Tua', 'Anggur Merah 275ml'),
  (4,  'ot_aoB',        'Orang Tua', 'Arak Obat 620ml'),
  (5,  'ot_apibcB',     'Orang Tua', 'API Anggur Blackcurrant 620ml (unconfirmed name — please verify)'),
  (6,  'ot_apihjB',     'Orang Tua', 'API Anggur Hijau 620ml'),
  (7,  'ot_apiptB',     'Orang Tua', 'API Anggur Putih 620ml'),
  (8,  'ot_aputB',      'Orang Tua', 'Anggur Putih 620ml'),
  (9,  'ot_atlaslB',    'Orang Tua', 'Atlas Lychee 620ml'),
  (10, 'ot_atlaspB',    'Orang Tua', 'Atlas (unconfirmed flavor) 620ml — please verify'),
  (11, 'ot_atlasrpB',   'Orang Tua', 'Atlas Rose Pink 620ml'),
  (12, 'ot_bcintB',     'Orang Tua', 'Intisari Blackcurrant 620ml'),
  (13, 'ot_gintB',      'Orang Tua', 'Unconfirmed product (gintB) — please verify'),
  (14, 'ot_hijauintB',  'Orang Tua', 'Intisari Anggur Hijau 620ml'),
  (15, 'ot_singarajaB', 'Orang Tua', 'Singaraja 620ml');

-- class_name is the actual lookup key used by backend/routes/events.py;
-- enforce uniqueness there (class_id is reused across different brand
-- datasets, so it can't be a global primary key).
ALTER TABLE product ADD CONSTRAINT product_class_name_uniq UNIQUE (class_name);

-- Backfill historical events that were already stamped with the wrong
-- Unknown brand/name at insert time (events.product_brand/product_name
-- are copied in at POST time, not joined live at read time).
UPDATE events e
SET product_brand = p.product_brand,
    product_name  = p.product_name
FROM product p
WHERE p.class_name = e.label
  AND (e.product_brand = 'Unknown' OR e.product_brand IS NULL
    OR e.product_name  = 'Unknown' OR e.product_name  IS NULL);

COMMIT;
