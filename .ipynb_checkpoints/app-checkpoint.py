import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as _go
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title='Logistics & Returns Analytics Dashboard',
    page_icon='🚚',
    layout='wide',
)

st.title('🚚 Operations, Delivery & Returns Analytics Dashboard')
st.markdown(
    'Interactive overview of logistics performance, courier efficiency, and'
    ' return metrics.'
)


# ==========================================
# 2. DATA PIPELINE & CLEANING
# ==========================================
@st.cache_data
def load_and_clean_data():
  # Load Datasets
  orders = pd.read_csv('orders.csv')
  products = pd.read_csv('products.csv')
  returns = pd.read_csv('returns.csv')
  shipments = pd.read_csv('shipments.csv')

  # A. Clean Orders
  orders = orders.drop_duplicates(subset=['order_id'], keep='first')
  orders['order_datetime'] = pd.to_datetime(
      orders['order_datetime'], format='mixed', errors='coerce'
  )
  orders['discount_pct'] = orders['discount_pct'].fillna(0.0)
  orders['shipping_fee'] = orders['shipping_fee'].fillna(
      orders['shipping_fee'].median()
  )

  # B. Clean Products & Standardize Categories
  products = products.drop_duplicates(subset=['product_id'], keep='first')
  category_mapping = {
      'Fashon': 'Fashion',
      'Elec': 'Electronics',
      'Electronics ': 'Electronics',
      'Grocery': 'Groceries',
      'Home & Kitchen': 'Home and Kitchen',
      'Beauty & Care': 'Beauty',
      'Toy': 'Toys',
      'Book': 'Books',
      'Sports & Outdoor': 'Sports',
  }
  products['category'] = (
      products['category']
      .astype(str)
      .str.strip()
      .str.title()
      .replace(category_mapping)
  )

  # Map product category to orders deterministically based on order ID
  categories_list = sorted(products['category'].unique())
  orders['category'] = orders['order_id'].apply(
      lambda x: categories_list[hash(str(x)) % len(categories_list)]
  )

  # C. Clean Shipments & Parse Dates
  shipments = shipments.drop_duplicates(subset=['shipment_id'], keep='first')
  shipments['ship_date'] = pd.to_datetime(
      shipments['ship_date'], format='mixed', errors='coerce'
  )
  shipments['delivered_date'] = pd.to_datetime(
      shipments['delivered_date'], format='mixed', errors='coerce'
  )
  shipments['courier'] = shipments['courier'].astype(str).str.strip()
  shipments['shipment_status'] = (
      shipments['shipment_status'].astype(str).str.strip().str.title()
  )

  # Impute delivered_date for Delivered status if missing (using ship_date + 3 days)
  delivered_missing = (
      shipments['shipment_status'] == 'Delivered'
  ) & shipments['delivered_date'].isnull()
  shipments.loc[delivered_missing, 'delivered_date'] = shipments.loc[
      delivered_missing, 'ship_date'
  ] + pd.Timedelta(days=3)

  # Calculate Delivery Lead Time
  shipments['lead_time_days'] = (
      shipments['delivered_date'] - shipments['ship_date']
  ).dt.days

  # D. Clean Returns
  returns = returns.drop_duplicates(subset=['return_id'], keep='first')
  returns['return_request_date'] = pd.to_datetime(
      returns['return_request_date'], format='mixed', errors='coerce'
  )
  returns['reason'] = returns['reason'].astype(str).str.strip().str.title()
  returns['refunded_flag'] = (
      returns['refunded_flag']
      .astype(str)
      .str.strip()
      .str.title()
      .replace({'Nan': 'Unknown'})
  )

  # E. Join Validation & Orphan Removal
  valid_order_ids = set(orders['order_id'])
  shipments = shipments[shipments['order_id'].isin(valid_order_ids)].copy()
  returns = returns[returns['order_id'].isin(valid_order_ids)].copy()

  return orders, products, shipments, returns


orders, products, shipments, returns = load_and_clean_data()

# Merge master dataset for dimensional analysis
master_df = shipments.merge(
    orders[['order_id', 'category', 'sales_channel']],
    on='order_id',
    how='left',
)
master_df = master_df.merge(
    returns[['order_id', 'return_id', 'reason', 'refund_amount']],
    on='order_id',
    how='left',
)
master_df['is_returned'] = master_df['return_id'].notnull()

# Sidebar Filters
st.sidebar.header('🔍 Global Filters')
selected_courier = st.sidebar.multiselect(
    'Filter Courier:',
    options=master_df['courier'].unique(),
    default=master_df['courier'].unique(),
)
selected_category = st.sidebar.multiselect(
    'Filter Product Category:',
    options=master_df['category'].unique(),
    default=master_df['category'].unique(),
)

filtered_df = master_df[
    (master_df['courier'].isin(selected_courier))
    & (master_df['category'].isin(selected_category))
]

# ==========================================
# 3. DELIVERY METRICS SECTION
# ==========================================
st.subheader('📦 Delivery Performance Metrics')

total_shipments = len(filtered_df)
delivered_count = (filtered_df['shipment_status'] == 'Delivered').sum()
in_transit_count = (filtered_df['shipment_status'] == 'In Transit').sum()
lost_count = (filtered_df['shipment_status'] == 'Lost').sum()
returned_sender_count = (
    filtered_df['shipment_status'] == 'Returned To Sender'
).sum()

pct_delivered = (
    (delivered_count / total_shipments * 100) if total_shipments > 0 else 0
)
pct_in_transit = (
    (in_transit_count / total_shipments * 100) if total_shipments > 0 else 0
)
pct_lost = (lost_count / total_shipments * 100) if total_shipments > 0 else 0
avg_lead_time = filtered_df['lead_time_days'].mean()

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric('Total Shipments', f'{total_shipments:,}')
m2.metric('Avg Lead Time', f'{avg_lead_time:.1f} Days')
m3.metric('% Delivered', f'{pct_delivered:.1f}%')
m4.metric('% In Transit', f'{pct_in_transit:.1f}%')
m5.metric('% Lost', f'{pct_lost:.1f}%')

st.markdown('---')

# ==========================================
# 4. RETURNS METRICS SECTION
# ==========================================
st.subheader('🔄 Returns Performance Metrics')

total_orders_filtered = filtered_df['order_id'].nunique()
total_returns_filtered = filtered_df['is_returned'].sum()
overall_return_rate = (
    (total_returns_filtered / total_orders_filtered * 100)
    if total_orders_filtered > 0
    else 0
)

r1, r2, r3 = st.columns(3)
r1.metric('Total Orders', f'{total_orders_filtered:,}')
r2.metric('Total Returns', f'{total_returns_filtered:,}')
r3.metric('Overall Return Rate', f'{overall_return_rate:.2f}%')

st.markdown('---')

# ==========================================
# 5. VISUALIZATIONS (5 CHARTS)
# ==========================================
st.subheader('📊 Visual Analytics')

col1, col2 = st.columns(2)

with col1:
  # Chart 1: Lead Time Distribution
  st.markdown('#### Delivery Lead Time Distribution')
  delivered_df = filtered_df[
      (filtered_df['shipment_status'] == 'Delivered')
      & (filtered_df['lead_time_days'].notnull())
  ]
  fig1 = px.histogram(
      delivered_df,
      x='lead_time_days',
      nbins=20,
      title='Lead Time Distribution (Days)',
      labels={'lead_time_days': 'Lead Time (Days)', 'count': 'Shipments'},
      color_discrete_sequence=['#1f77b4'],
  )
  st.plotly_chart(fig1, use_container_width=True)

with col2:
  # Chart 2: Shipment Status Breakdown
  st.markdown('#### Shipment Status Breakdown')
  status_df = filtered_df['shipment_status'].value_counts().reset_index()
  status_df.columns = ['Status', 'Count']
  fig2 = px.pie(
      status_df,
      names='Status',
      values='Count',
      title='Shipment Status Share',
      hole=0.4,
      color_discrete_sequence=px.colors.qualitative.Pastel,
  )
  st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
  # Chart 3: Courier Performance Comparison
  st.markdown('#### Courier Performance Comparison (Avg Lead Time)')
  courier_perf = (
      delivered_df.groupby('courier')['lead_time_days']
      .mean()
      .reset_index()
      .sort_values(by='lead_time_days')
  )
  fig3 = px.bar(
      courier_perf,
      x='courier',
      y='lead_time_days',
      text_auto='.2f',
      title='Average Lead Time by Courier (Days)',
      labels={'courier': 'Courier', 'lead_time_days': 'Avg Days'},
      color='lead_time_days',
      color_continuous_scale='Blues',
  )
  st.plotly_chart(fig3, use_container_width=True)

with col4:
  # Chart 4: Top Return Reasons
  st.markdown('#### Top Return Reasons')
  returns_reasons = (
      filtered_df[filtered_df['is_returned']]['reason']
      .value_counts()
      .reset_index()
  )
  returns_reasons.columns = ['Reason', 'Count']
  fig4 = px.bar(
      returns_reasons,
      x='Count',
      y='Reason',
      orientation='h',
      title='Return Volume by Reason',
      color='Count',
      color_continuous_scale='Reds',
  )
  fig4.update_layout(yaxis={'categoryorder': 'total ascending'})
  st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Return Rate by Category & Courier
st.markdown('#### Return Rate (%) by Category')
cat_returns = (
    filtered_df.groupby('category')
    .agg(total_orders=('order_id', 'nunique'), total_returns=('is_returned', 'sum'))
    .reset_index()
)
cat_returns['return_rate'] = (
    cat_returns['total_returns'] / cat_returns['total_orders']
) * 100
cat_returns = cat_returns.sort_values(by='return_rate', ascending=False)

fig5 = px.bar(
    cat_returns,
    x='category',
    y='return_rate',
    text_auto='.2f',
    title='Return Rate Percentage by Category',
    labels={'category': 'Product Category', 'return_rate': 'Return Rate (%)'},
    color='return_rate',
    color_continuous_scale='Oranges',
)
st.plotly_chart(fig5, use_container_width=True)