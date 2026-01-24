"""
============================================================================
WS5: Enterprise Lakeview Dashboard - Plotly Chart Configurations
Bank CFO Command Center - Professional Visualization Specs
============================================================================
Created: 2026-01-25
Purpose: Bloomberg Terminal-level chart configurations for Databricks Lakeview
Aesthetic: Navy/slate/white professional palette, data-dense but elegant
============================================================================
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================================
# DESIGN SYSTEM CONSTANTS
# ============================================================================

COLORS = {
    # Primary palette
    'navy_dark': '#1B3139',
    'navy_medium': '#2C4A54',
    'navy_light': '#3D5F6B',
    'slate_dark': '#475569',
    'slate_medium': '#64748B',
    'slate_light': '#94A3B8',
    'white': '#FFFFFF',
    'gray_bg': '#F8FAFC',

    # Accent colors
    'cyan': '#00A8E1',
    'cyan_light': '#33BCEA',
    'lava': '#FF3621',
    'lava_light': '#FF6B5E',
    'gold': '#F59E0B',
    'green': '#10B981',
    'green_light': '#34D399',
    'red': '#EF4444',
    'red_light': '#F87171',

    # Status colors
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#00A8E1',
}

FONTS = {
    'title': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'body': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'mono': 'SF Mono, Consolas, Monaco, monospace',
}

CHART_LAYOUT_BASE = {
    'font': {'family': FONTS['body'], 'size': 12, 'color': COLORS['navy_dark']},
    'paper_bgcolor': COLORS['white'],
    'plot_bgcolor': COLORS['gray_bg'],
    'margin': {'l': 60, 'r': 40, 't': 80, 'b': 60},
    'showlegend': True,
    'legend': {
        'orientation': 'h',
        'yanchor': 'bottom',
        'y': -0.2,
        'xanchor': 'center',
        'x': 0.5,
        'font': {'size': 11}
    },
    'xaxis': {
        'gridcolor': COLORS['slate_light'] + '33',
        'showgrid': True,
        'zeroline': False
    },
    'yaxis': {
        'gridcolor': COLORS['slate_light'] + '33',
        'showgrid': True,
        'zeroline': False
    }
}


# ============================================================================
# CHART 1: KPI SCORECARD WITH SPARKLINES
# ============================================================================

def create_kpi_scorecard(df_kpis, df_sparklines):
    """
    Professional KPI cards with embedded sparkline trends

    Args:
        df_kpis: DataFrame with columns [metric_name, current_value_billions, composition, pct_change_30d]
        df_sparklines: DataFrame with columns [metric_name, metric_date, value]

    Returns:
        plotly.graph_objects.Figure
    """
    # Create subplot grid for sparklines
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=df_kpis['metric_name'].tolist(),
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, (metric_name, row, col) in enumerate(zip(df_kpis['metric_name'], [p[0] for p in positions], [p[1] for p in positions])):
        # Filter sparkline data for this metric
        sparkline_data = df_sparklines[df_sparklines['metric_name'] == metric_name]

        # Add sparkline trace
        fig.add_trace(
            go.Scatter(
                x=sparkline_data['metric_date'],
                y=sparkline_data['value'],
                mode='lines',
                line=dict(color=COLORS['cyan'], width=2),
                fill='tozeroy',
                fillcolor=COLORS['cyan'] + '33',
                name=metric_name,
                showlegend=False
            ),
            row=row, col=col
        )

        # Add current value annotation
        current_val = df_kpis[df_kpis['metric_name'] == metric_name]['current_value_billions'].values[0]
        pct_change = df_kpis[df_kpis['metric_name'] == metric_name]['pct_change_30d'].values[0]

        annotation_text = f"<b>${current_val:.1f}B</b><br><span style='color:{COLORS['green'] if pct_change > 0 else COLORS['red']}'>{pct_change:+.1f}%</span>"

        fig.add_annotation(
            xref=f"x{idx+1 if idx > 0 else ''} domain",
            yref=f"y{idx+1 if idx > 0 else ''} domain",
            x=0.95, y=0.95,
            text=annotation_text,
            showarrow=False,
            font=dict(size=16, family=FONTS['body']),
            align='right',
            xanchor='right',
            yanchor='top'
        )

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Executive KPI Scorecard</b><br><sub>30-day performance trends</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=600,
        showlegend=False
    )

    # Remove x-axis labels for cleaner sparklines
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showticklabels=True, showgrid=True)

    return fig


# ============================================================================
# CHART 2: LIQUIDITY WATERFALL
# ============================================================================

def create_liquidity_waterfall(df_components):
    """
    Professional waterfall chart showing LCR component breakdown

    Args:
        df_components: DataFrame with columns [component, flow_type, signed_value_billions, sort_order]

    Returns:
        plotly.graph_objects.Figure
    """
    # Prepare data
    components = df_components.sort_values('sort_order')['component'].tolist()
    values = df_components.sort_values('sort_order')['signed_value_billions'].tolist()
    flow_types = df_components.sort_values('sort_order')['flow_type'].tolist()

    # Color coding
    colors = [COLORS['green'] if ft == 'source' else COLORS['red'] for ft in flow_types]

    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="LCR Components",
        orientation="v",
        measure=["relative"] * len(components),
        x=components,
        textposition="outside",
        text=[f"${v:+.1f}B" for v in values],
        y=values,
        connector={"line": {"color": COLORS['slate_medium'], "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": COLORS['green'], "line": {"color": COLORS['navy_dark'], "width": 1}}},
        decreasing={"marker": {"color": COLORS['red'], "line": {"color": COLORS['navy_dark'], "width": 1}}},
        totals={"marker": {"color": COLORS['cyan'], "line": {"color": COLORS['navy_dark'], "width": 2}}}
    ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Liquidity Coverage Ratio (LCR) Waterfall</b><br><sub>HQLA sources vs 30-day cash outflows</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=500,
        xaxis={'title': '', 'tickangle': -45},
        yaxis={'title': 'Amount ($ Billions)', 'tickformat': ',.1f'},
        showlegend=False
    )

    # Add regulatory threshold line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=COLORS['slate_medium'],
        annotation_text="Basel III Minimum (100%)",
        annotation_position="right"
    )

    return fig


# ============================================================================
# CHART 3: YIELD CURVE SURFACE (3D)
# ============================================================================

def create_yield_curve_surface(df_yield_history):
    """
    3D surface plot of yield curve evolution over time

    Args:
        df_yield_history: DataFrame with columns [observation_date, tenor_years, yield_pct, days_from_start]

    Returns:
        plotly.graph_objects.Figure
    """
    # Pivot data for surface plot
    import pandas as pd
    pivot_data = df_yield_history.pivot(index='observation_date', columns='tenor_years', values='yield_pct')

    # Create 3D surface
    fig = go.Figure(data=[go.Surface(
        z=pivot_data.values,
        x=pivot_data.columns,  # Tenor
        y=pivot_data.index,     # Date
        colorscale=[
            [0, COLORS['green']],
            [0.5, COLORS['gold']],
            [1, COLORS['red']]
        ],
        colorbar=dict(
            title="Yield (%)",
            titleside="right",
            tickmode="linear",
            tick0=0,
            dtick=0.5
        ),
        contours={
            "z": {"show": True, "usecolormap": True, "highlightcolor": COLORS['white'], "project": {"z": True}}
        }
    )])

    # Update layout for 3D
    fig.update_layout(
        title={
            'text': '<b>Treasury Yield Curve Surface</b><br><sub>90-day historical term structure evolution</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        scene=dict(
            xaxis=dict(title='Maturity (Years)', gridcolor=COLORS['slate_light'], showbackground=True, backgroundcolor=COLORS['gray_bg']),
            yaxis=dict(title='Date', gridcolor=COLORS['slate_light'], showbackground=True, backgroundcolor=COLORS['gray_bg']),
            zaxis=dict(title='Yield (%)', gridcolor=COLORS['slate_light'], showbackground=True, backgroundcolor=COLORS['gray_bg']),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
        ),
        height=600,
        paper_bgcolor=COLORS['white'],
        font={'family': FONTS['body'], 'size': 12, 'color': COLORS['navy_dark']}
    )

    return fig


def create_yield_curve_2d(df_latest_curve):
    """
    2D line chart of current yield curve (companion to 3D surface)

    Args:
        df_latest_curve: DataFrame with columns [tenor_years, yield_pct, observation_date]

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Add yield curve line
    fig.add_trace(go.Scatter(
        x=df_latest_curve['tenor_years'],
        y=df_latest_curve['yield_pct'],
        mode='lines+markers',
        line=dict(color=COLORS['cyan'], width=3),
        marker=dict(size=8, color=COLORS['navy_dark'], line=dict(color=COLORS['white'], width=2)),
        name='Current Curve'
    ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': f"<b>Current Treasury Yield Curve</b><br><sub>As of {df_latest_curve['observation_date'].iloc[0]}</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=400,
        xaxis={'title': 'Maturity (Years)', 'tickvals': [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]},
        yaxis={'title': 'Yield (%)', 'tickformat': '.2f'},
        showlegend=False
    )

    return fig


# ============================================================================
# CHART 4: PORTFOLIO RISK-RETURN HEATMAP
# ============================================================================

def create_risk_return_heatmap(df_portfolio):
    """
    Treemap showing portfolio allocation by security type with risk metrics

    Args:
        df_portfolio: DataFrame with columns [security_type, market_value_billions, avg_yield_pct, avg_duration_years, credit_rating]

    Returns:
        plotly.graph_objects.Figure
    """
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=df_portfolio['security_type'],
        parents=['Portfolio'] * len(df_portfolio),
        values=df_portfolio['market_value_billions'],
        text=df_portfolio.apply(lambda x: f"{x['security_type']}<br>${x['market_value_billions']:.1f}B<br>Yield: {x['avg_yield_pct']:.2f}%<br>Duration: {x['avg_duration_years']:.1f}Y<br>{x['credit_rating']}", axis=1),
        textposition='middle center',
        marker=dict(
            colorscale=[
                [0, COLORS['red']],
                [0.5, COLORS['gold']],
                [1, COLORS['green']]
            ],
            cmid=3.0,
            colorbar=dict(title="Yield (%)", thickness=15),
            line=dict(color=COLORS['white'], width=2)
        ),
        marker_colors=df_portfolio['avg_yield_pct'],
        hovertemplate='<b>%{label}</b><br>Value: $%{value:.1f}B<br>%{text}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title={
            'text': '<b>Portfolio Risk-Return Matrix</b><br><sub>Asset allocation by security type</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=500,
        paper_bgcolor=COLORS['white'],
        font={'family': FONTS['body'], 'size': 12, 'color': COLORS['navy_dark']}
    )

    return fig


def create_duration_yield_scatter(df_portfolio):
    """
    Scatter plot: Duration vs Yield with bubble size = market value

    Args:
        df_portfolio: DataFrame with columns [security_type, market_value_billions, avg_yield_pct, avg_duration_years]

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Add scatter trace
    fig.add_trace(go.Scatter(
        x=df_portfolio['avg_duration_years'],
        y=df_portfolio['avg_yield_pct'],
        mode='markers+text',
        marker=dict(
            size=df_portfolio['market_value_billions'] * 20,  # Scale bubble size
            color=df_portfolio['avg_yield_pct'],
            colorscale=[
                [0, COLORS['red']],
                [0.5, COLORS['gold']],
                [1, COLORS['green']]
            ],
            showscale=True,
            colorbar=dict(title="Yield (%)"),
            line=dict(color=COLORS['navy_dark'], width=2)
        ),
        text=df_portfolio['security_type'],
        textposition='top center',
        textfont=dict(size=10, color=COLORS['navy_dark'], family=FONTS['body']),
        hovertemplate='<b>%{text}</b><br>Duration: %{x:.1f} years<br>Yield: %{y:.2f}%<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Duration vs Yield Analysis</b><br><sub>Bubble size = market value</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=500,
        xaxis={'title': 'Effective Duration (Years)', 'range': [0, max(df_portfolio['avg_duration_years']) * 1.1]},
        yaxis={'title': 'Yield to Maturity (%)', 'range': [0, max(df_portfolio['avg_yield_pct']) * 1.1]},
        showlegend=False
    )

    return fig


# ============================================================================
# CHART 5: DEPOSIT BETA SENSITIVITY MATRIX
# ============================================================================

def create_deposit_beta_heatmap(df_rate_shocks):
    """
    Heatmap showing deposit runoff across product types and rate scenarios

    Args:
        df_rate_shocks: DataFrame with columns [product_type, runoff_25bps, runoff_50bps, runoff_100bps, runoff_minus_25bps]

    Returns:
        plotly.graph_objects.Figure
    """
    # Prepare matrix data
    scenarios = ['-25 bps', '+25 bps', '+50 bps', '+100 bps']
    products = df_rate_shocks['product_type'].tolist()

    z_data = [
        df_rate_shocks['runoff_minus_25bps'].tolist(),
        df_rate_shocks['runoff_25bps'].tolist(),
        df_rate_shocks['runoff_50bps'].tolist(),
        df_rate_shocks['runoff_100bps'].tolist()
    ]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=products,
        y=scenarios,
        colorscale=[
            [0, COLORS['green']],
            [0.5, COLORS['gold']],
            [1, COLORS['red']]
        ],
        text=[[f"${val:.1f}B" for val in row] for row in z_data],
        texttemplate='%{text}',
        textfont={"size": 12, "color": COLORS['white']},
        colorbar=dict(title="Runoff ($B)", thickness=15),
        hovertemplate='Product: %{x}<br>Scenario: %{y}<br>Runoff: %{z:.2f}B<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Deposit Beta Sensitivity Matrix</b><br><sub>Rate shock impact on deposit balances</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=400,
        xaxis={'title': 'Product Type', 'side': 'bottom'},
        yaxis={'title': 'Rate Scenario'},
        plot_bgcolor=COLORS['white']
    )

    return fig


# ============================================================================
# CHART 6: REAL-TIME ACTIVITY STREAM
# ============================================================================

def create_activity_timeline(df_activities):
    """
    Timeline visualization of recent banking activities

    Args:
        df_activities: DataFrame with columns [activity_type, entity_name, activity_date, amount_millions, activity_description]

    Returns:
        plotly.graph_objects.Figure
    """
    # Color map for activity types
    color_map = {
        'Loan Origination': COLORS['cyan'],
        'Deposit Account Opened': COLORS['green'],
        'Securities Purchase': COLORS['navy_medium'],
        'Securities Sale': COLORS['slate_medium'],
        'Churn Prediction': COLORS['lava']
    }

    # Create scatter plot
    fig = go.Figure()

    for activity_type in df_activities['activity_type'].unique():
        df_subset = df_activities[df_activities['activity_type'] == activity_type]

        fig.add_trace(go.Scatter(
            x=df_subset['activity_date'],
            y=df_subset['amount_millions'],
            mode='markers',
            name=activity_type,
            marker=dict(
                size=12,
                color=color_map.get(activity_type, COLORS['slate_medium']),
                line=dict(color=COLORS['white'], width=1)
            ),
            text=df_subset['entity_name'],
            hovertemplate='<b>%{text}</b><br>%{fullData.name}<br>Date: %{x}<br>Amount: $%{y:.1f}M<extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Real-Time Activity Stream</b><br><sub>Last 7 days of banking operations</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=500,
        xaxis={'title': 'Date', 'type': 'date'},
        yaxis={'title': 'Transaction Amount ($M)', 'type': 'log'},
        showlegend=True
    )

    return fig


# ============================================================================
# CHART 7: CAPITAL ADEQUACY BULLET CHARTS
# ============================================================================

def create_capital_bullet_chart(df_capital_ratios):
    """
    Bullet charts showing capital ratios against regulatory thresholds

    Args:
        df_capital_ratios: DataFrame with columns [capital_type, actual_ratio_pct, regulatory_minimum_pct, well_capitalized_pct, target_pct]

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    for idx, row in df_capital_ratios.iterrows():
        # Background ranges (regulatory zones)
        fig.add_trace(go.Bar(
            y=[row['capital_type']],
            x=[row['target_pct']],
            orientation='h',
            marker=dict(color=COLORS['gray_bg']),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Well-capitalized zone
        fig.add_trace(go.Bar(
            y=[row['capital_type']],
            x=[row['well_capitalized_pct']],
            orientation='h',
            marker=dict(color=COLORS['green'] + '33'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Minimum zone
        fig.add_trace(go.Bar(
            y=[row['capital_type']],
            x=[row['regulatory_minimum_pct']],
            orientation='h',
            marker=dict(color=COLORS['gold'] + '33'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Actual value (bullet)
        fig.add_trace(go.Bar(
            y=[row['capital_type']],
            x=[row['actual_ratio_pct']],
            orientation='h',
            marker=dict(
                color=COLORS['cyan'] if row['actual_ratio_pct'] >= row['well_capitalized_pct'] else COLORS['gold'],
                line=dict(color=COLORS['navy_dark'], width=2)
            ),
            name=row['capital_type'],
            text=f"{row['actual_ratio_pct']:.1f}%",
            textposition='outside',
            hovertemplate=f"<b>{row['capital_type']}</b><br>Actual: {row['actual_ratio_pct']:.1f}%<br>Target: {row['target_pct']:.1f}%<extra></extra>"
        ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Capital Adequacy Ratios</b><br><sub>Basel III regulatory compliance</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=400,
        xaxis={'title': 'Capital Ratio (%)', 'range': [0, df_capital_ratios['target_pct'].max() * 1.1]},
        yaxis={'title': ''},
        showlegend=False,
        barmode='overlay'
    )

    return fig


# ============================================================================
# CHART 8: NET INTEREST MARGIN (NIM) WATERFALL
# ============================================================================

def create_nim_waterfall(df_nim_components):
    """
    Waterfall chart showing NIM component breakdown

    Args:
        df_nim_components: DataFrame with columns [component, signed_amount_millions, sort_order]

    Returns:
        plotly.graph_objects.Figure
    """
    # Prepare data
    components = df_nim_components.sort_values('sort_order')['component'].tolist()
    values = df_nim_components.sort_values('sort_order')['signed_amount_millions'].tolist()

    # Add "Net Interest Income" as total at the end
    components.append("Net Interest Income")

    # Create waterfall
    fig = go.Figure(go.Waterfall(
        name="NIM Components",
        orientation="v",
        measure=["relative"] * len(df_nim_components) + ["total"],
        x=components,
        textposition="outside",
        text=[f"${v:+.0f}M" for v in values] + [""],
        y=values + [0],  # 0 for total (auto-calculated)
        connector={"line": {"color": COLORS['slate_medium'], "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": COLORS['green'], "line": {"color": COLORS['navy_dark'], "width": 1}}},
        decreasing={"marker": {"color": COLORS['red'], "line": {"color": COLORS['navy_dark'], "width": 1}}},
        totals={"marker": {"color": COLORS['cyan'], "line": {"color": COLORS['navy_dark'], "width": 2}}}
    ))

    # Update layout
    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title={
            'text': '<b>Net Interest Margin (NIM) Attribution</b><br><sub>Monthly income and expense breakdown</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': FONTS['title'], 'color': COLORS['navy_dark']}
        },
        height=500,
        xaxis={'title': '', 'tickangle': -45},
        yaxis={'title': 'Amount ($M)', 'tickformat': ',.0f'},
        showlegend=False
    )

    return fig


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def apply_professional_theme(fig):
    """
    Apply consistent professional styling to any Plotly figure

    Args:
        fig: plotly.graph_objects.Figure

    Returns:
        Modified figure with professional theme applied
    """
    fig.update_layout(**CHART_LAYOUT_BASE)
    return fig


def export_chart_config(chart_name, fig):
    """
    Export chart configuration as JSON for Lakeview dashboard

    Args:
        chart_name: str - Name of the chart
        fig: plotly.graph_objects.Figure

    Returns:
        dict - Chart configuration
    """
    return {
        "chart_name": chart_name,
        "config": fig.to_dict(),
        "layout": fig.layout.to_plotly_json()
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=== WS5 Plotly Chart Configurations ===")
    print("Professional visualization specs for Databricks Lakeview")
    print("\nAvailable chart functions:")
    print("  1. create_kpi_scorecard(df_kpis, df_sparklines)")
    print("  2. create_liquidity_waterfall(df_components)")
    print("  3. create_yield_curve_surface(df_yield_history)")
    print("  4. create_yield_curve_2d(df_latest_curve)")
    print("  5. create_risk_return_heatmap(df_portfolio)")
    print("  6. create_duration_yield_scatter(df_portfolio)")
    print("  7. create_deposit_beta_heatmap(df_rate_shocks)")
    print("  8. create_activity_timeline(df_activities)")
    print("  9. create_capital_bullet_chart(df_capital_ratios)")
    print(" 10. create_nim_waterfall(df_nim_components)")
    print("\nColor Palette:")
    for name, color in COLORS.items():
        print(f"  {name}: {color}")
