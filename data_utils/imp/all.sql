--
-- File generated with SQLiteStudio v3.4.4 on �� ��� 23 22:10:25 2024
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: AdditionalData
CREATE TABLE IF NOT EXISTS AdditionalData (id INTEGER PRIMARY KEY NOT NULL, result_name TEXT NOT NULL DEFAULT RESULT, result_text TEXT NOT NULL DEFAULT "", result_type TEXT CHECK (result_type IN ("probability", "confidence")), tree_data BLOB, example_positions TEXT NOT NULL DEFAULT "[]", factor_positions TEXT NOT NULL DEFAULT "[]", result_value_positions TEXT NOT NULL DEFAULT "[]", count TEXT DEFAULT ('{"values": {}, "factors": 0}') NOT NULL);
INSERT INTO AdditionalData (id, result_name, result_text, result_type, tree_data, example_positions, factor_positions, result_value_positions, count) VALUES (1, 'RESULT', '', NULL, NULL, '[]', '[]', '[]', '{"values": {},"factors": 0}');

-- Table: Example
CREATE TABLE IF NOT EXISTS Example (example_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, result_value_id INTEGER REFERENCES ResultValue (result_value_id) ON DELETE CASCADE NOT NULL, weight REAL NOT NULL, active INTEGER NOT NULL DEFAULT (1) CHECK (active = 0 or active = 1));

-- Table: ExampleFactorValue
CREATE TABLE IF NOT EXISTS ExampleFactorValue (example_factor_value_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, example_id INTEGER NOT NULL REFERENCES Example (example_id) ON DELETE CASCADE, value_id INTEGER NOT NULL REFERENCES Value (value_id) ON DELETE CASCADE);

-- Table: Factor
CREATE TABLE IF NOT EXISTS Factor (factor_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL UNIQUE, text TEXT NOT NULL DEFAULT "", active INTEGER DEFAULT (1) NOT NULL CHECK (active = 0 or active = 1), value_positions TEXT DEFAULT "[]" NOT NULL);

-- Table: ResultValue
CREATE TABLE IF NOT EXISTS ResultValue (result_value_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL UNIQUE, text TEXT NOT NULL DEFAULT "");

-- Table: Value
CREATE TABLE IF NOT EXISTS Value (value_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, factor_id INTEGER REFERENCES Factor (factor_id) ON DELETE CASCADE NOT NULL, name TEXT NOT NULL, text TEXT NOT NULL DEFAULT "");

-- Trigger: change_count_on_delete
CREATE TRIGGER IF NOT EXISTS change_count_on_delete AFTER DELETE ON Value FOR EACH ROW BEGIN UPDATE AdditionalData
SET count = json_set(count, '$.values.'|| old.factor_id, json_extract(count, '$.values.'|| old.factor_id) - 1); END;

-- Trigger: change_count_on_insert
CREATE TRIGGER IF NOT EXISTS change_count_on_insert AFTER INSERT ON Value FOR EACH ROW BEGIN UPDATE AdditionalData
SET count = json_set(count, '$.values.'|| new.factor_id, json_extract(count, '$.values.'|| new.factor_id) + 1); END;

-- Trigger: example_position_delete
CREATE TRIGGER IF NOT EXISTS example_position_delete AFTER DELETE ON Example FOR EACH ROW BEGIN UPDATE AdditionalData
SET example_positions = json_remove(example_positions, '$['||
(SELECT json_each.id - 1
FROM json_each((SELECT example_positions FROM AdditionalData))
WHERE json_each.value = old.example_id)
||"]")
WHERE id = 1; END;

-- Trigger: example_position_insert
CREATE TRIGGER IF NOT EXISTS example_position_insert AFTER INSERT ON Example FOR EACH ROW BEGIN UPDATE AdditionalData
SET example_positions = json_insert(example_positions, '$['||json_array_length(example_positions)||"]", new.example_id)
WHERE id = 1;
 END;

-- Trigger: factor_change_count_on_delete
CREATE TRIGGER IF NOT EXISTS factor_change_count_on_delete AFTER DELETE ON Factor BEGIN UPDATE AdditionalData
SET count = json_set(count, '$.factors', json_extract(count, '$.factors') - 1);
UPDATE AdditionalData
SET count = json_remove(count, '$.values.'||old.factor_id); END;

-- Trigger: factor_change_count_on_insert
CREATE TRIGGER IF NOT EXISTS factor_change_count_on_insert AFTER INSERT ON Factor FOR EACH ROW BEGIN UPDATE AdditionalData
SET count = json_set(count, '$.factors', json_extract(count, '$.factors') + 1);
UPDATE AdditionalData
SET count = json_set(count, '$.values.'||new.factor_id, 0); END;

-- Trigger: factor_position_delete
CREATE TRIGGER IF NOT EXISTS factor_position_delete AFTER DELETE ON Factor FOR EACH ROW BEGIN UPDATE AdditionalData
SET factor_positions = json_remove(factor_positions, '$['||
(SELECT json_each.id - 1
FROM json_each((SELECT factor_positions FROM AdditionalData))
WHERE json_each.value = old.factor_id)
||"]")
WHERE id = 1; END;

-- Trigger: factor_position_insert
CREATE TRIGGER IF NOT EXISTS factor_position_insert AFTER INSERT ON Factor FOR EACH ROW BEGIN UPDATE AdditionalData SET factor_positions = json_insert(factor_positions, '$[' || json_array_length(factor_positions) || "]", new.factor_id) WHERE id = 1; END;

-- Trigger: result_value_position_delete
CREATE TRIGGER IF NOT EXISTS result_value_position_delete
         AFTER DELETE
            ON ResultValue
      FOR EACH ROW
BEGIN
    UPDATE AdditionalData
       SET result_value_positions = json_remove(result_value_positions, '$[' || (
                                                                                    SELECT json_each.id - 1
                                                                                      FROM json_each( (
                                                                                                          SELECT result_value_positions
                                                                                                            FROM AdditionalData
                                                                                                      )
                                                                                           )
                                                                                     WHERE json_each.value = old.result_value_id
                                                                                )
||                                              "]")
     WHERE id = 1;
END;

-- Trigger: result_value_position_insert
CREATE TRIGGER IF NOT EXISTS result_value_position_insert
         AFTER INSERT
            ON ResultValue
      FOR EACH ROW
BEGIN
    UPDATE AdditionalData
       SET result_value_positions = json_insert(result_value_positions, '$[' || json_array_length(result_value_positions) || "]", new.result_value_id)
     WHERE id = 1;
END;

-- Trigger: unique_name
CREATE TRIGGER IF NOT EXISTS unique_name BEFORE INSERT ON Value FOR EACH ROW BEGIN SELECT IIF(name = new.name, RAISE(ROLLBACK, "unique name in one factor") , '') FROM Value WHERE factor_id = new.factor_id; END;

-- Trigger: value_position_delete
CREATE TRIGGER IF NOT EXISTS value_position_delete AFTER DELETE ON Value FOR EACH ROW BEGIN UPDATE Factor
SET value_positions = json_remove(value_positions, '$['||
(SELECT json_each.id - 1
FROM json_each((SELECT value_positions FROM Factor WHERE factor_id = old.factor_id))
WHERE json_each.value = old.value_id)
||"]")
WHERE factor_id = old.factor_id;
 END;

-- Trigger: value_position_insert
CREATE TRIGGER IF NOT EXISTS value_position_insert AFTER INSERT ON Value FOR EACH ROW BEGIN UPDATE Factor
SET value_positions = json_insert(value_positions, '$['||json_array_length(value_positions)||"]", new.value_id)
WHERE factor_id = new.factor_id; END;

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
