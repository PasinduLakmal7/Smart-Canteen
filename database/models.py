"""
Database Table Schema DDL for SQLite.
Defines foods, nutrition, food_prices, employees, user_profiles, and food_preferences tables.
"""

# --- Phase 2 Tables: Food, Nutrition & Billing ---
CREATE_FOODS_TABLE = """
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    serving_type TEXT NOT NULL CHECK(serving_type IN ('piece', 'serving', 'portion')),
    standard_serving_g REAL NOT NULL DEFAULT 100.0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_NUTRITION_TABLE = """
CREATE TABLE IF NOT EXISTS nutrition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    basis_type TEXT NOT NULL DEFAULT 'per_unit' CHECK(basis_type IN ('per_unit', 'per_100g')),
    basis_amount REAL NOT NULL DEFAULT 1.0,
    calories_kcal REAL NOT NULL DEFAULT 0.0,
    protein_g REAL NOT NULL DEFAULT 0.0,
    carbs_g REAL NOT NULL DEFAULT 0.0,
    fat_g REAL NOT NULL DEFAULT 0.0,
    sugar_g REAL NOT NULL DEFAULT 0.0,
    fiber_g REAL NOT NULL DEFAULT 0.0,
    sodium_mg REAL NOT NULL DEFAULT 0.0,
    source_name TEXT DEFAULT 'MRI Sri Lanka / USDA',
    source_reference TEXT DEFAULT 'Standard Sri Lankan Food Composition Tables',
    verified INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);
"""

CREATE_FOOD_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS food_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    serving_type TEXT NOT NULL CHECK(serving_type IN ('piece', 'serving', 'portion')),
    price REAL NOT NULL CHECK(price >= 0.0),
    effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMP NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);
"""

# --- Phase 3 Tables: Employees, User Profiles & Diet Preferences ---
CREATE_EMPLOYEES_TABLE = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER UNIQUE NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 16 AND age <= 100),
    height_cm REAL NOT NULL CHECK(height_cm >= 100.0 AND height_cm <= 250.0),
    weight_kg REAL NOT NULL CHECK(weight_kg >= 30.0 AND weight_kg <= 300.0),
    daily_calorie_target REAL NOT NULL DEFAULT 2000.0 CHECK(daily_calorie_target > 0.0),
    diet_type TEXT NOT NULL DEFAULT 'normal' CHECK(diet_type IN ('normal', 'vegetarian', 'vegan', 'pescatarian', 'halal', 'diabetic')),
    health_goal TEXT NOT NULL DEFAULT 'maintain' CHECK(health_goal IN ('maintain', 'weight_loss', 'weight_gain', 'high_protein', 'low_carb', 'heart_healthy')),
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
"""

CREATE_FOOD_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS food_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    preference_type TEXT NOT NULL CHECK(preference_type IN ('like', 'dislike', 'avoid')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(employee_id, food_name)
);
"""

# --- Phase 4 Tables: Biometric Face Recognition Embeddings ---
CREATE_FACE_EMBEDDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS face_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    embedding TEXT NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'yunet_sface_128d',
    sample_tag TEXT DEFAULT 'frontal',
    quality_score REAL DEFAULT 1.0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
"""

# --- Phase 5 Tables: Meal History & Transactions ---
CREATE_MEAL_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS meal_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_code TEXT UNIQUE NOT NULL,
    employee_id INTEGER NOT NULL,
    total_calories REAL NOT NULL DEFAULT 0.0,
    total_protein REAL NOT NULL DEFAULT 0.0,
    total_carbs REAL NOT NULL DEFAULT 0.0,
    total_fat REAL NOT NULL DEFAULT 0.0,
    total_sugar REAL NOT NULL DEFAULT 0.0,
    total_fiber REAL NOT NULL DEFAULT 0.0,
    total_sodium_mg REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL CHECK(total_amount >= 0.0),
    payment_status TEXT NOT NULL DEFAULT 'completed' CHECK(payment_status IN ('completed', 'pending', 'payroll_deducted', 'refunded')),
    payment_method TEXT NOT NULL DEFAULT 'payroll' CHECK(payment_method IN ('payroll', 'nfc', 'cash', 'qr')),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
"""

CREATE_MEAL_TRANSACTION_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS meal_transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    food_id INTEGER NULL,
    food_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity >= 1),
    serving_size_g REAL NOT NULL DEFAULT 100.0,
    calories REAL NOT NULL DEFAULT 0.0,
    protein REAL NOT NULL DEFAULT 0.0,
    carbs REAL NOT NULL DEFAULT 0.0,
    fat REAL NOT NULL DEFAULT 0.0,
    sugar REAL NOT NULL DEFAULT 0.0,
    fiber REAL NOT NULL DEFAULT 0.0,
    sodium_mg REAL NOT NULL DEFAULT 0.0,
    unit_price REAL NOT NULL CHECK(unit_price >= 0.0),
    subtotal REAL NOT NULL CHECK(subtotal >= 0.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES meal_transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
);
"""

CREATE_INDEXES = [
    # Phase 2 Indexes
    "CREATE INDEX IF NOT EXISTS idx_foods_class_name ON foods(class_name);",
    "CREATE INDEX IF NOT EXISTS idx_foods_active ON foods(active);",
    "CREATE INDEX IF NOT EXISTS idx_nutrition_food_id ON nutrition(food_id);",
    "CREATE INDEX IF NOT EXISTS idx_food_prices_food_id ON food_prices(food_id);",
    "CREATE INDEX IF NOT EXISTS idx_food_prices_active ON food_prices(active);",
    # Phase 3 Indexes
    "CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code);",
    "CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);",
    "CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(active);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_employee_id ON user_profiles(employee_id);",
    "CREATE INDEX IF NOT EXISTS idx_prefs_employee_id ON food_preferences(employee_id);",
    # Phase 4 Indexes
    "CREATE INDEX IF NOT EXISTS idx_face_embeddings_employee_id ON face_embeddings(employee_id);",
    "CREATE INDEX IF NOT EXISTS idx_face_embeddings_active ON face_embeddings(active);",
    # Phase 5 Indexes
    "CREATE INDEX IF NOT EXISTS idx_meal_tx_code ON meal_transactions(transaction_code);",
    "CREATE INDEX IF NOT EXISTS idx_meal_tx_employee_id ON meal_transactions(employee_id);",
    "CREATE INDEX IF NOT EXISTS idx_meal_tx_date ON meal_transactions(transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_meal_tx_items_tx_id ON meal_transaction_items(transaction_id);",
    "CREATE INDEX IF NOT EXISTS idx_meal_tx_items_food_id ON meal_transaction_items(food_id);"
]


