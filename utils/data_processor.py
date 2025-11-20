# utils/data_processor.py
import pandas as pd

def clean_orders_df(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = ['order_id', 'order_status', 'order_date', 'sales']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    df['sales'] = pd.to_numeric(df['sales'], errors='coerce')
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df = df.dropna(subset=['sales', 'quantity'])
    df['order_date'] = pd.to_datetime(df['order_date'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['order_date'])
    return df[df['order_status'] == 'Shipped'].copy()

def clean_adspend_df(df: pd.DataFrame) -> pd.DataFrame:
    if 'Day' not in df.columns or 'Amount spent (PKR)' not in df.columns:
        raise ValueError("Ad spend file must have 'Day' and 'Amount spent (PKR)'")
    df = df[['Day', 'Amount spent (PKR)']].copy()
    df.columns = ['date', 'ad_spend']
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['ad_spend'] = pd.to_numeric(df['ad_spend'], errors='coerce')
    df = df.dropna(subset=['date', 'ad_spend'])
    return df

def process_data(orders_df: pd.DataFrame, adspend_df: pd.DataFrame):
    # Clean
    orders = clean_orders_df(orders_df)
    ads = clean_adspend_df(adspend_df)
    
    if orders.empty or ads.empty:
        raise ValueError("No valid shipped orders or ad spend data.")

    # Time features
    orders['order_day'] = orders['order_date'].dt.date
    orders['order_week'] = orders['order_date'].dt.to_period('W').astype(str)
    orders['order_month'] = orders['order_date'].dt.to_period('M').astype(str)
    orders['order_qtr'] = orders['order_date'].dt.to_period('Q').astype(str)

    # Daily revenue
    daily_rev = orders.groupby('order_day')['sales'].sum().reset_index()
    daily_rev.columns = ['date', 'revenue']
    daily_rev['date'] = pd.to_datetime(daily_rev['date'])

    # Full date range
    min_date = min(daily_rev['date'].min(), ads['date'].min())
    max_date = max(daily_rev['date'].max(), ads['date'].max())
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    full_dates = pd.DataFrame({'date': date_range})

    # Merge
    merged = full_dates.merge(daily_rev, on='date', how='left').merge(ads, on='date', how='left')
    merged['revenue'] = merged['revenue'].fillna(0).astype(float)
    merged['ad_spend'] = merged['ad_spend'].fillna(0).astype(float)

    # Core KPIs
    total_revenue = orders['sales'].sum()
    total_orders = orders['order_id'].nunique()
    total_units = orders['quantity'].sum()
    total_ad_spend = ads['ad_spend'].sum()

    # === 1. Core Sales Metrics ===
    aov = total_revenue / total_orders if total_orders > 0 else 0
    avg_units_per_order = total_units / total_orders if total_orders > 0 else 0

    # === 2. Breakdowns ===
    rev_by_category = orders.groupby('category')['sales'].sum().round(2).to_dict()
    rev_by_city = orders.groupby('city')['sales'].sum().round(2).to_dict()
    rev_by_sku = orders.groupby('sku')['sales'].sum().round(2).to_dict()
    rev_by_source = orders.groupby('order_source')['sales'].sum().round(2).to_dict()

    # === 3. Marketing & ROI ===
    roas = total_revenue / total_ad_spend if total_ad_spend > 0 else 0
    cpo = total_ad_spend / total_orders if total_orders > 0 else 0

    # ROAS by source (merge daily data with source)
    orders_daily = orders.groupby(['order_day', 'order_source'])['sales'].sum().reset_index()
    orders_daily['order_day'] = pd.to_datetime(orders_daily['order_day'])
    daily_with_source = full_dates.merge(orders_daily, left_on='date', right_on='order_day', how='left')
    daily_with_source['sales'] = daily_with_source['sales'].fillna(0)
    daily_with_source = daily_with_source.merge(ads, on='date', how='left')
    daily_with_source['ad_spend'] = daily_with_source['ad_spend'].fillna(0)

    roas_by_source = {}
    for source in rev_by_source.keys():
        source_rev = daily_with_source[daily_with_source['order_source'] == source]['sales'].sum()
        # Approximate ad spend attribution: equal split per order source (simplified)
        roas_by_source[source] = round(source_rev / (total_ad_spend + 1e-6), 2)

    # === 4. Time-Series ===
    # Weekly
    merged['week'] = merged['date'].dt.to_period('W').astype(str)
    weekly_rev = merged.groupby('week')['revenue'].sum().round(2).to_dict()
    weekly_spend = merged.groupby('week')['ad_spend'].sum().round(2).to_dict()

    # Monthly
    orders['month'] = orders['order_date'].dt.to_period('M')
    monthly_rev = orders.groupby('month')['sales'].sum()
    apr_rev = monthly_rev.get(pd.Period('2025-04'), 0)
    may_rev = monthly_rev.get(pd.Period('2025-05'), 0)
    mom_growth = ((may_rev - apr_rev) / apr_rev * 100) if apr_rev > 0 else 0

    # Quarterly
    q1_rev = orders[orders['order_qtr'] == '2025Q1']['sales'].sum()
    q2_rev = orders[orders['order_qtr'] == '2025Q2']['sales'].sum()
    q2_vs_q1_growth = ((q2_rev - q1_rev) / q1_rev * 100) if q1_rev > 0 else 0

    # === 5. Advanced Segmentation ===
    def top_bottom_dict(series, top_n=5, bottom_n=5):
        sorted_items = series.sort_values(ascending=False)
        top = [{"name": k, "value": round(v, 2)} for k, v in sorted_items.head(top_n).items()]
        bottom = [{"name": k, "value": round(v, 2)} for k, v in sorted_items.tail(bottom_n).items()]
        return top, bottom

    top_cities, bottom_cities = top_bottom_dict(pd.Series(rev_by_city))
    top_skus, bottom_skus = top_bottom_dict(pd.Series(rev_by_sku))
    top_categories, bottom_categories = top_bottom_dict(pd.Series(rev_by_category))

    # Order status distribution (all statuses)
    order_status_dist = orders_df['order_status'].value_counts().to_dict()

    # === 6. Final KPI Summary (25+ KPIs) ===
    kpi_summary = {
        # Core Sales
        "total_revenue": round(total_revenue, 2),
        "total_orders": int(total_orders),
        "aov": round(aov, 2),
        "total_units_sold": int(total_units),
        "avg_units_per_order": round(avg_units_per_order, 2),
        "revenue_by_category": rev_by_category,
        "revenue_by_city": rev_by_city,
        "revenue_by_sku": rev_by_sku,
        "revenue_by_source": rev_by_source,

        # Marketing & ROI
        "total_ad_spend": round(total_ad_spend, 2),
        "roas": round(roas, 2),
        "cpo": round(cpo, 2),
        "roas_by_source": roas_by_source,

        # Time-Series Trends
        "weekly_revenue": weekly_rev,
        "weekly_ad_spend": weekly_spend,
        "mom_growth_apr_to_may_pct": round(mom_growth, 2),
        "q1_revenue": round(q1_rev, 2),
        "q2_revenue": round(q2_rev, 2),
        "q2_vs_q1_growth_pct": round(q2_vs_q1_growth, 2),

        # Advanced Segmentation
        "top_cities_by_revenue": top_cities,
        "bottom_cities_by_revenue": bottom_cities,
        "top_skus_by_revenue": top_skus,
        "bottom_skus_by_revenue": bottom_skus,
        "top_categories_by_revenue": top_categories,
        "bottom_categories_by_revenue": bottom_categories,

        # Order Health
        "order_status_distribution": order_status_dist,

        # Metadata
        "time_range": f"{min_date.date()} to {max_date.date()}"
    }

    return kpi_summary, orders, merged