# config/data_quality.py

DATA_QUALITY_PROFILE = {
    "customers": {
        "duplicate_rate": 0.03,
        "missing_email_rate": 0.05,
        "invalid_email_rate": 0.02,
        "missing_city_rate": 0.03
    },

    "orders": {
        "duplicate_rate": 0.02,
        "missing_product_rate": 0.03,
        "invalid_amount_rate": 0.02,
        "negative_amount_rate": 0.01,
        "invalid_status_rate": 0.01
    },

    "products": {
        "duplicate_rate": 0.02,
        "missing_name_rate": 0.01,
        "invalid_price_rate": 0.02,
        "zero_price_rate": 0.01,
        "category_mismatch_rate": 0.02,
        "schema_drift_rate": 0.05
        }
}
