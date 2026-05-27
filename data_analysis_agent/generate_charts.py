"""
Generate sample charts for README documentation
This creates actual visualizations from the sales_data.csv
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Setup
DATA_FILE = 'sales_data.csv'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])

# Style
sns.set_style("darkgrid")
plt.rcParams['figure.facecolor'] = '#0f1117'
plt.rcParams['axes.facecolor'] = '#1e2130'
plt.rcParams['text.color'] = '#c9d1d9'

print("📊 Generating sample analysis charts...\n")

# 1. Monthly Revenue Trend
print("1️⃣  Creating monthly revenue trend...")
monthly_revenue = df.groupby(df['date'].dt.to_period('M'))['revenue'].sum()
fig, ax = plt.subplots(figsize=(12, 6))
monthly_revenue.plot(kind='line', ax=ax, color='#4f8ef7', linewidth=2.5, marker='o')
ax.set_title('Monthly Revenue Trend', fontsize=16, fontweight='bold', color='#c9d1d9')
ax.set_xlabel('Month', color='#c9d1d9')
ax.set_ylabel('Revenue ($)', color='#c9d1d9')
ax.tick_params(colors='#c9d1d9')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'monthly_revenue.png'), facecolor='#0f1117', dpi=150)
plt.close()
print(f"   ✅ Saved to {OUTPUT_DIR}/monthly_revenue.png\n")

# 2. Top 5 Products
print("2️⃣  Creating top 5 products chart...")
top_products = df.groupby('product')['revenue'].sum().nlargest(5)
fig, ax = plt.subplots(figsize=(10, 6))
top_products.plot(kind='bar', ax=ax, color='#4fcb71', edgecolor='white', linewidth=1.5)
ax.set_title('Top 5 Products by Revenue', fontsize=16, fontweight='bold', color='#c9d1d9')
ax.set_xlabel('Product', color='#c9d1d9')
ax.set_ylabel('Revenue ($)', color='#c9d1d9')
ax.tick_params(colors='#c9d1d9')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'top_products.png'), facecolor='#0f1117', dpi=150)
plt.close()
print(f"   ✅ Saved to {OUTPUT_DIR}/top_products.png\n")

# 3. Regional Breakdown
print("3️⃣  Creating regional breakdown chart...")
regional_revenue = df.groupby('region')['revenue'].sum()
fig, ax = plt.subplots(figsize=(8, 8))
colors = ['#f77f4f', '#4fcb71', '#4f8ef7', '#af4ff7']
ax.pie(regional_revenue, labels=regional_revenue.index, autopct='%1.1f%%', 
       colors=colors, startangle=90, textprops={'color': '#c9d1d9'})
ax.set_title('Revenue Breakdown by Region', fontsize=16, fontweight='bold', color='#c9d1d9')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'regional_breakdown.png'), facecolor='#0f1117', dpi=150)
plt.close()
print(f"   ✅ Saved to {OUTPUT_DIR}/regional_breakdown.png\n")

# 4. Sales Channel Performance
print("4️⃣  Creating sales channel performance chart...")
channel_revenue = df.groupby('channel')['revenue'].sum()
fig, ax = plt.subplots(figsize=(10, 6))
channel_revenue.plot(kind='bar', ax=ax, color='#f7c948', edgecolor='white', linewidth=1.5)
ax.set_title('Revenue by Sales Channel', fontsize=16, fontweight='bold', color='#c9d1d9')
ax.set_xlabel('Channel', color='#c9d1d9')
ax.set_ylabel('Revenue ($)', color='#c9d1d9')
ax.tick_params(colors='#c9d1d9')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'channel_performance.png'), facecolor='#0f1117', dpi=150)
plt.close()
print(f"   ✅ Saved to {OUTPUT_DIR}/channel_performance.png\n")

# 5. Discount vs Revenue Scatter
print("5️⃣  Creating discount impact analysis...")
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df['discount']*100, df['revenue'], alpha=0.4, s=30, color='#af4ff7', edgecolors='white', linewidth=0.5)
ax.set_title('Impact of Discount on Transaction Revenue', fontsize=16, fontweight='bold', color='#c9d1d9')
ax.set_xlabel('Discount (%)', color='#c9d1d9')
ax.set_ylabel('Revenue per Transaction ($)', color='#c9d1d9')
ax.tick_params(colors='#c9d1d9')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'discount_impact.png'), facecolor='#0f1117', dpi=150)
plt.close()
print(f"   ✅ Saved to {OUTPUT_DIR}/discount_impact.png\n")

# 6. Summary Statistics
print("6️⃣  Generating summary statistics...")
print("\n" + "="*60)
print("              SALES ANALYSIS SUMMARY STATISTICS")
print("="*60)
print(f"\nTotal Revenue:              ${df['revenue'].sum():,.2f}")
print(f"Average Transaction Size:   ${df['revenue'].mean():,.2f}")
print(f"Number of Transactions:     {len(df):,}")
print(f"\nRevenue by Region:")
for region, revenue in df.groupby('region')['revenue'].sum().sort_values(ascending=False).items():
    pct = (revenue / df['revenue'].sum()) * 100
    print(f"  {region:15} ${revenue:>12,.2f}  ({pct:>5.1f}%)")

print(f"\nTop 5 Products:")
for i, (product, revenue) in enumerate(top_products.items(), 1):
    pct = (revenue / df['revenue'].sum()) * 100
    print(f"  {i}. {product:12} ${revenue:>12,.2f}  ({pct:>5.1f}%)")

print(f"\nRevenue by Channel:")
for channel, revenue in df.groupby('channel')['revenue'].sum().sort_values(ascending=False).items():
    pct = (revenue / df['revenue'].sum()) * 100
    print(f"  {channel:15} ${revenue:>12,.2f}  ({pct:>5.1f}%)")

print(f"\nAverage Discount Applied:   {df['discount'].mean()*100:.1f}%")
print(f"Avg Revenue (No Discount):  ${df[df['discount']==0]['revenue'].mean():,.2f}")
print(f"Avg Revenue (With Discount):${df[df['discount']>0]['revenue'].mean():,.2f}")
print("\n" + "="*60)

print("\n✨ All charts generated successfully!")
print(f"📁 Output files saved to: {os.path.abspath(OUTPUT_DIR)}/")
