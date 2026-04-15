# config/data_quality.py

DATA_QUALITY_PROFILE = {
    "customers": {
        "duplicate_rate": 0.4,
        "missing_email_rate": 0.4,
        "invalid_email_rate": 0.4,
        "missing_city_rate": 0.4
    },

    "orders": {
        "duplicate_rate": 0.4,
        "missing_product_rate": 0.4,
        "invalid_amount_rate": 0.4,
        "negative_amount_rate": 0.4,
        "invalid_status_rate": 0.4
    },

    "products": {
        "duplicate_rate": 0.3,
        "missing_name_rate": 0.42,
        "invalid_price_rate": 0.4,
        "zero_price_rate": 0.4,
        "category_mismatch_rate": 0.4,
        "schema_drift_rate": 0.4
        }
}
