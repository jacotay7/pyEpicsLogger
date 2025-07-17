# %% [markdown]
# # EPICS Logger Data Analysis
# 
# This notebook analyzes the EPICS channel monitoring data to understand:
# - Time relationships between EPICS and local timestamps
# - Clock skew patterns and timing characteristics  
# - PV value changes and patterns across multiple channels
# - Overall system performance metrics
# - Channel-specific behavior and statistics

# %%
# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# %%
# Load and examine the data
filename = 'jul_7.csv'  # Change this to your actual file name
try:
    df = pd.read_csv(filename)
    print("Dataset Overview:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst few rows:")
    print(df.head())
except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    print("Please ensure you have a CSV file from the EPICS logger.")
    print("Run the logger with: python3 epicsLogger.py <PV_NAMES> --data-file data.csv")
    # Create sample data for demonstration
    import numpy as np
    from datetime import datetime, timedelta
    
    print("\nCreating sample data for demonstration...")
    sample_size = 1000
    base_time = datetime.now()
    
    df = pd.DataFrame({
        'sequence_number': range(1, sample_size + 1),
        'pv_name': np.random.choice(['TEST:TEMP', 'TEST:PRESSURE', 'TEST:FLOW'], sample_size),
        'pv_value': np.random.normal(100, 10, sample_size),
        'pv_type': 'DBF_DOUBLE',
        'epics_timestamp': [base_time.timestamp() + i for i in range(sample_size)],
        'epics_datetime': [(base_time + timedelta(seconds=i)).isoformat() for i in range(sample_size)],
        'local_datetime': [(base_time + timedelta(seconds=i, milliseconds=np.random.randint(-50, 50))).isoformat() for i in range(sample_size)],
        'clock_skew_seconds': np.random.normal(0, 0.01, sample_size),
        'clock_offset_applied': [0.0] * sample_size,
        'previous_value': [None] + list(np.random.normal(100, 10, sample_size-1)),
        'value_changed': np.random.choice([True, False], sample_size, p=[0.3, 0.7]),
        'connection_status': [True] * sample_size,
        'severity': np.random.choice([0, 1, 2], sample_size, p=[0.8, 0.15, 0.05]),
        'alarm_status': np.random.choice([0, 1, 2], sample_size, p=[0.85, 0.1, 0.05])
    })
    print("Sample data created successfully!")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst few rows:")
    print(df.head())

# %%
# Data types and basic info
print("Data Types:")
print(df.dtypes)
print("\nBasic Statistics:")
print(df.describe())

# %%
# Convert datetime columns to proper datetime objects
df['epics_datetime'] = pd.to_datetime(df['epics_datetime'])
df['local_datetime'] = pd.to_datetime(df['local_datetime'])

# Calculate time differences in milliseconds for better visualization
df['time_diff_ms'] = (df['local_datetime'] - df['epics_datetime']).dt.total_seconds() * 1000

print("Time difference statistics (milliseconds):")
print(df['time_diff_ms'].describe())

plt.figure(figsize=(10, 6))
n, bins, patches = plt.hist(
    df['time_diff_ms'], 
    bins=np.logspace(0, 4, 60), 
    edgecolor='black', 
    alpha=0.85
)
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Time Difference Between Sent and Received [ms]', fontsize=14)
plt.ylabel('Number of Received Heartbeats', fontsize=14)
plt.title('Distribution of Time Differences (Log-Log Scale)', fontsize=16, weight='bold')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()

plt.show()

# %%
# Primary Analysis: EPICS vs Local DateTime Scatter Plot
fig = plt.figure(figsize=(15, 10))

# Create subplot layout
gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[3, 1])
ax_main = fig.add_subplot(gs[0, 0])
ax_hist_x = fig.add_subplot(gs[1, 0], sharex=ax_main)
ax_hist_y = fig.add_subplot(gs[0, 1], sharey=ax_main)

# Main scatter plot
scatter = ax_main.scatter(df['epics_datetime'], df['local_datetime'], 
                         c=df['clock_skew_seconds'], cmap='RdYlBu_r', 
                         alpha=0.6, s=10)
ax_main.set_xlabel('EPICS DateTime')
ax_main.set_ylabel('Local DateTime')
ax_main.set_title('EPICS DateTime vs Local DateTime\n(Color represents clock skew)')
ax_main.grid(True, alpha=0.3)

# Add perfect correlation line
min_time = min(df['epics_datetime'].min(), df['local_datetime'].min())
max_time = max(df['epics_datetime'].max(), df['local_datetime'].max())
ax_main.plot([min_time, max_time], [min_time, max_time], 'r--', alpha=0.5, label='Perfect sync')
ax_main.legend()

# Histograms
ax_hist_x.hist(df['epics_datetime'], bins=50, alpha=0.7, color='skyblue')
ax_hist_x.set_ylabel('Frequency')
ax_hist_x.set_title('EPICS DateTime Distribution')

ax_hist_y.hist(df['local_datetime'], bins=50, alpha=0.7, color='lightcoral', orientation='horizontal')
ax_hist_y.set_xlabel('Frequency')
ax_hist_y.set_title('Local DateTime Distribution')

# Colorbar
plt.colorbar(scatter, ax=ax_main, label='Clock Skew (seconds)')

plt.tight_layout()
plt.show()

# %%
# Clock Skew Analysis
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Clock skew over time
axes[0, 0].plot(df['sequence_number'], df['clock_skew_seconds'], alpha=0.7)
axes[0, 0].set_title('Clock Skew Over Time')
axes[0, 0].set_xlabel('Sequence Number')
axes[0, 0].set_ylabel('Clock Skew (seconds)')
axes[0, 0].grid(True, alpha=0.3)

# Clock skew histogram
axes[0, 1].hist(df['clock_skew_seconds'], bins=50, alpha=0.7, color='orange')
axes[0, 1].set_title('Clock Skew Distribution')
axes[0, 1].set_xlabel('Clock Skew (seconds)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].axvline(df['clock_skew_seconds'].mean(), color='red', linestyle='--', label=f'Mean: {df["clock_skew_seconds"].mean():.4f}s')
axes[0, 1].legend()

# Time difference (local - epics) in milliseconds
axes[1, 0].plot(df['sequence_number'], df['time_diff_ms'], alpha=0.7, color='green')
axes[1, 0].set_title('Time Difference (Local - EPICS) Over Time')
axes[1, 0].set_xlabel('Sequence Number')
axes[1, 0].set_ylabel('Time Difference (ms)')
axes[1, 0].grid(True, alpha=0.3)

# Box plot of clock skew
axes[1, 1].boxplot(df['clock_skew_seconds'])
axes[1, 1].set_title('Clock Skew Box Plot')
axes[1, 1].set_ylabel('Clock Skew (seconds)')

plt.tight_layout()
plt.show()

# %%
# Timing Error and Channel Analysis
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Channel distribution
channel_counts = df['pv_name'].value_counts()
axes[0, 0].pie(channel_counts.values, labels=channel_counts.index, autopct='%1.1f%%')
axes[0, 0].set_title('Distribution of Records by Channel')

# Value changes over time
value_changes = df[df['value_changed'] == True]
if not value_changes.empty:
    axes[0, 1].plot(value_changes['sequence_number'], value_changes['pv_value'], 'o', alpha=0.6)
    axes[0, 1].set_title('Value Changes Over Time')
    axes[0, 1].set_xlabel('Sequence Number')
    axes[0, 1].set_ylabel('PV Value')
    axes[0, 1].grid(True, alpha=0.3)

# Clock skew over time
axes[1, 0].plot(df['sequence_number'], df['clock_skew_seconds'], alpha=0.7, color='purple')
axes[1, 0].set_title('Clock Skew Over Time')
axes[1, 0].set_xlabel('Sequence Number')
axes[1, 0].set_ylabel('Clock Skew (seconds)')
axes[1, 0].grid(True, alpha=0.3)

# Alarm status distribution
if 'severity' in df.columns:
    severity_counts = df['severity'].value_counts().sort_index()
    severity_labels = ['NO_ALARM', 'MINOR', 'MAJOR', 'INVALID']
    axes[1, 1].bar(range(len(severity_counts)), severity_counts.values)
    axes[1, 1].set_title('Alarm Severity Distribution')
    axes[1, 1].set_xlabel('Severity Level')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].set_xticks(range(len(severity_counts)))
    axes[1, 1].set_xticklabels([severity_labels[i] if i < len(severity_labels) else str(i) for i in severity_counts.index])

plt.tight_layout()
plt.show()

# %%
# PV Value Analysis
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# PV value over time
axes[0, 0].plot(df['sequence_number'], df['pv_value'], alpha=0.7)
axes[0, 0].set_title('PV Value Over Time')
axes[0, 0].set_xlabel('Sequence Number')
axes[0, 0].set_ylabel('PV Value')
axes[0, 0].grid(True, alpha=0.3)

# Value changes
value_changes = df['value_changed'].value_counts()
axes[0, 1].pie(value_changes.values, labels=value_changes.index, autopct='%1.1f%%')
axes[0, 1].set_title('Value Change Distribution')

# PV value differences (consecutive)
df['pv_value_diff'] = df['pv_value'].diff()
axes[1, 0].plot(df['sequence_number'][1:], df['pv_value_diff'][1:], alpha=0.7, color='orange')
axes[1, 0].set_title('PV Value Changes (Consecutive Differences)')
axes[1, 0].set_xlabel('Sequence Number')
axes[1, 0].set_ylabel('PV Value Difference')
axes[1, 0].grid(True, alpha=0.3)

# Transition analysis
if 'transition_number' in df.columns:
    transition_data = df[df['transition_number'].notna()]
    if not transition_data.empty:
        axes[1, 1].hist(transition_data['transition_number'], bins=50, alpha=0.7, color='green')
        axes[1, 1].set_title('Transition Number Distribution')
        axes[1, 1].set_xlabel('Transition Number')
        axes[1, 1].set_ylabel('Frequency')

plt.tight_layout()
plt.show()

# %%
# Interactive Plotly Visualization
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('EPICS vs Local DateTime', 'Clock Skew Over Time', 
                   'PV Value Changes by Channel', 'Connection Status Distribution'),
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"type": "xy"}]]
)

# EPICS vs Local DateTime scatter
fig.add_trace(
    go.Scatter(x=df['epics_datetime'], y=df['local_datetime'],
               mode='markers',
               marker=dict(color=df['clock_skew_seconds'], colorscale='RdYlBu_r', size=4),
               name='Data Points',
               text=df['sequence_number'],
               hovertemplate='EPICS: %{x}<br>Local: %{y}<br>Seq: %{text}<extra></extra>'),
    row=1, col=1
)

# Clock skew over time
fig.add_trace(
    go.Scatter(x=df['sequence_number'], y=df['clock_skew_seconds'],
               mode='lines+markers',
               name='Clock Skew',
               line=dict(width=1),
               marker=dict(size=3)),
    row=1, col=2
)

# PV value changes by channel (if we have multiple channels)
if df['pv_name'].nunique() > 1:
    for pv_name in df['pv_name'].unique():
        pv_data = df[df['pv_name'] == pv_name]
        fig.add_trace(
            go.Scatter(x=pv_data['sequence_number'], y=pv_data['pv_value'],
                       mode='lines',
                       name=f'{pv_name}',
                       line=dict(width=1)),
            row=2, col=1
        )
else:
    # Single channel
    fig.add_trace(
        go.Scatter(x=df['sequence_number'], y=df['pv_value'],
                   mode='lines',
                   name='PV Value',
                   line=dict(width=1)),
        row=2, col=1
    )

# Connection status pie chart
if 'connection_status' in df.columns:
    connection_counts = df['connection_status'].value_counts()
    fig.add_trace(
        go.Pie(labels=['Connected' if x else 'Disconnected' for x in connection_counts.index],
               values=connection_counts.values,
               name="Connection Status"),
        row=2, col=2
    )

fig.update_layout(height=800, showlegend=False, title_text="PV Monitor Data Analysis Dashboard")
fig.update_xaxes(title_text="EPICS DateTime", row=1, col=1)
fig.update_yaxes(title_text="Local DateTime", row=1, col=1)
fig.update_xaxes(title_text="Sequence Number", row=1, col=2)
fig.update_yaxes(title_text="Clock Skew (seconds)", row=1, col=2)
fig.update_xaxes(title_text="Sequence Number", row=2, col=1)
fig.update_yaxes(title_text="PV Value", row=2, col=1)
fig.update_xaxes(title_text="Timing Error (seconds)", row=2, col=2)
fig.update_yaxes(title_text="Count", row=2, col=2)

fig.show()

# %%
# Statistical Summary Report
print("="*60)
print("EPICS LOGGER DATA ANALYSIS SUMMARY")
print("="*60)

print(f"\n📊 DATASET OVERVIEW:")
print(f"   • Total records: {len(df):,}")
print(f"   • Time span: {df['epics_datetime'].min()} to {df['epics_datetime'].max()}")
print(f"   • Duration: {(df['epics_datetime'].max() - df['epics_datetime'].min()).total_seconds():.1f} seconds")
print(f"   • Monitored channels: {df['pv_name'].nunique()}")
print(f"   • Channel names: {', '.join(df['pv_name'].unique())}")

print(f"\n⏰ TIMING ANALYSIS:")
print(f"   • Average clock skew: {df['clock_skew_seconds'].mean():.4f} ± {df['clock_skew_seconds'].std():.4f} seconds")
print(f"   • Clock skew range: {df['clock_skew_seconds'].min():.4f} to {df['clock_skew_seconds'].max():.4f} seconds")
print(f"   • Time difference (local-epics): {df['time_diff_ms'].mean():.1f} ± {df['time_diff_ms'].std():.1f} ms")

print(f"\n📈 CHANNEL ANALYSIS:")
for pv_name in df['pv_name'].unique():
    pv_data = df[df['pv_name'] == pv_name]
    pv_changes = pv_data[pv_data['value_changed'] == True]
    print(f"   • {pv_name}:")
    print(f"     - Records: {len(pv_data):,}")
    print(f"     - Value changes: {len(pv_changes):,} ({len(pv_changes)/len(pv_data)*100:.1f}%)")
    print(f"     - Value range: {pv_data['pv_value'].min():.3f} to {pv_data['pv_value'].max():.3f}")
    if len(pv_changes) > 0:
        print(f"     - Average change magnitude: {abs(pv_changes['pv_value'].diff()).mean():.3f}")

print(f"\n� SYSTEM PERFORMANCE:")
print(f"   • Clock offset applied: {df['clock_offset_applied'].abs().mean():.6f} seconds average")
print(f"   • Connection success rate: {df['connection_status'].mean()*100:.1f}%")

if 'severity' in df.columns:
    alarm_rate = (df['severity'] > 0).mean() * 100
    print(f"   • Alarm rate: {alarm_rate:.1f}% of records")
    
    # Alarm severity breakdown
    severity_counts = df['severity'].value_counts().sort_index()
    severity_names = ['NO_ALARM', 'MINOR', 'MAJOR', 'INVALID']
    print(f"   • Alarm severity breakdown:")
    for sev, count in severity_counts.items():
        sev_name = severity_names[sev] if sev < len(severity_names) else f'UNKNOWN_{sev}'
        print(f"     - {sev_name}: {count} ({count/len(df)*100:.1f}%)")

# Correlation analysis
numeric_cols = df.select_dtypes(include=[np.number]).columns
corr_matrix = df[numeric_cols].corr()
print(f"\n🔗 KEY CORRELATIONS:")
# Find strongest correlations (excluding self-correlation)
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i,j]))

# Sort by absolute correlation value
corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
for col1, col2, corr in corr_pairs[:5]:
    print(f"   • {col1} ↔ {col2}: {corr:.3f}")

print("\n" + "="*60)

# %%
# Correlation Heatmap
plt.figure(figsize=(12, 10))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.5}, fmt='.2f')
plt.title('Correlation Matrix of Numeric Variables')
plt.tight_layout()
plt.show()

# %%
# Time Series Analysis - Rolling Statistics
window_size = 100  # Rolling window size

df['clock_skew_rolling_mean'] = df['clock_skew_seconds'].rolling(window=window_size).mean()
df['clock_skew_rolling_std'] = df['clock_skew_seconds'].rolling(window=window_size).std()

fig, axes = plt.subplots(2, 1, figsize=(15, 8))

# Rolling mean and std of clock skew
axes[0].plot(df['sequence_number'], df['clock_skew_seconds'], alpha=0.3, label='Clock Skew')
axes[0].plot(df['sequence_number'], df['clock_skew_rolling_mean'], color='red', linewidth=2, label=f'Rolling Mean (window={window_size})')
axes[0].fill_between(df['sequence_number'], 
                    df['clock_skew_rolling_mean'] - df['clock_skew_rolling_std'],
                    df['clock_skew_rolling_mean'] + df['clock_skew_rolling_std'],
                    alpha=0.2, color='red', label='±1 Rolling Std')
axes[0].set_title('Clock Skew Time Series with Rolling Statistics')
axes[0].set_xlabel('Sequence Number')
axes[0].set_ylabel('Clock Skew (seconds)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Value change frequency over time
value_changes = df[df['value_changed'] == True]
if not value_changes.empty:
    # Calculate change frequency in windows
    window_size_freq = 50
    change_freq = []
    seq_centers = []
    
    for i in range(window_size_freq, len(df), window_size_freq//2):
        window_data = df.iloc[max(0, i-window_size_freq):i]
        changes_in_window = window_data['value_changed'].sum()
        change_freq.append(changes_in_window / len(window_data) * 100)  # Percentage
        seq_centers.append(window_data['sequence_number'].mean())
    
    axes[1].plot(seq_centers, change_freq, alpha=0.7, color='green', linewidth=2)
    axes[1].set_title('Value Change Frequency Over Time')
    axes[1].set_xlabel('Sequence Number')
    axes[1].set_ylabel('Change Frequency (%)')
    axes[1].grid(True, alpha=0.3)
else:
    axes[1].text(0.5, 0.5, 'No value changes detected', ha='center', va='center', 
                transform=axes[1].transAxes, fontsize=14)
    axes[1].set_title('Value Change Frequency Over Time')

plt.tight_layout()
plt.show()

print("\n✅ Analysis Complete! The notebook provides comprehensive insights into your EPICS channel monitoring data.")
