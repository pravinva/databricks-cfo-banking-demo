"""
============================================================================
WS5: Enterprise Lakeview Dashboard - Design System
Bank CFO Command Center - Professional Design Standards
============================================================================
Created: 2026-01-25
Purpose: Bloomberg Terminal-level design system for Databricks Lakeview
Aesthetic: Navy/slate/white professional palette, enterprise banking quality
============================================================================
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ============================================================================
# COLOR PALETTE
# ============================================================================

@dataclass
class ColorPalette:
    """Professional color palette for enterprise banking dashboards"""

    # Primary Colors - Navy Foundation
    navy_dark: str = '#1B3139'         # Main headers, critical text
    navy_medium: str = '#2C4A54'       # Secondary headers, borders
    navy_light: str = '#3D5F6B'        # Tertiary elements

    # Neutral Colors - Slate Sophistication
    slate_dark: str = '#475569'        # Body text, labels
    slate_medium: str = '#64748B'      # Secondary text
    slate_light: str = '#94A3B8'       # Tertiary text, disabled states
    slate_border: str = '#CBD5E1'      # Dividers, borders

    # Background Colors
    white: str = '#FFFFFF'             # Cards, panels
    gray_bg: str = '#F8FAFC'           # Dashboard background
    gray_hover: str = '#F1F5F9'        # Hover states

    # Accent Colors - Strategic Use Only
    cyan: str = '#00A8E1'              # Primary action, data visualization
    cyan_light: str = '#33BCEA'        # Hover states, highlights
    cyan_dark: str = '#0088B8'         # Active states

    lava: str = '#FF3621'              # Alerts, warnings, critical metrics
    lava_light: str = '#FF6B5E'        # Hover states for alerts
    lava_dark: str = '#CC2B1A'         # Active alert states

    # Data Visualization Spectrum
    gold: str = '#F59E0B'              # Warning states, medium priority
    green: str = '#10B981'             # Success, positive trends
    green_light: str = '#34D399'       # Light success states
    green_dark: str = '#059669'        # Dark success states
    red: str = '#EF4444'               # Errors, negative trends
    red_light: str = '#F87171'         # Light error states
    red_dark: str = '#DC2626'          # Dark error states

    # Status Colors
    success: str = '#10B981'           # Compliant, passed, good
    warning: str = '#F59E0B'           # At risk, caution, review
    danger: str = '#EF4444'            # Non-compliant, failed, critical
    info: str = '#00A8E1'              # Informational, neutral

    # Chart-Specific Colors (Professional Gradients)
    chart_blue_scale: List[str] = None
    chart_green_scale: List[str] = None
    chart_red_scale: List[str] = None
    chart_heatmap_scale: List[str] = None

    def __post_init__(self):
        """Initialize gradient scales after instantiation"""
        self.chart_blue_scale = [
            '#E0F2FE',  # Lightest blue
            '#BAE6FD',
            '#7DD3FC',
            '#38BDF8',
            '#0EA5E9',
            '#0284C7',
            '#0369A1',
            '#075985',  # Darkest blue
        ]

        self.chart_green_scale = [
            '#D1FAE5',  # Lightest green
            '#A7F3D0',
            '#6EE7B7',
            '#34D399',
            '#10B981',
            '#059669',
            '#047857',
            '#065F46',  # Darkest green
        ]

        self.chart_red_scale = [
            '#FEE2E2',  # Lightest red
            '#FECACA',
            '#FCA5A5',
            '#F87171',
            '#EF4444',
            '#DC2626',
            '#B91C1C',
            '#991B1B',  # Darkest red
        ]

        self.chart_heatmap_scale = [
            self.green,      # Low risk / high performance
            self.gold,       # Medium
            self.red         # High risk / low performance
        ]

    def get_trend_color(self, trend: str) -> str:
        """
        Get color for trend indicators

        Args:
            trend: 'up', 'down', or 'neutral'

        Returns:
            Hex color code
        """
        trend_map = {
            'up': self.green,
            'down': self.red,
            'neutral': self.slate_medium
        }
        return trend_map.get(trend.lower(), self.slate_medium)

    def get_status_color(self, status: str) -> str:
        """
        Get color for status badges

        Args:
            status: 'success', 'warning', 'danger', 'info'

        Returns:
            Hex color code
        """
        status_map = {
            'success': self.success,
            'warning': self.warning,
            'danger': self.danger,
            'info': self.info,
            'compliant': self.success,
            'non-compliant': self.danger,
            'at-risk': self.warning
        }
        return status_map.get(status.lower(), self.slate_medium)

    def to_dict(self) -> Dict[str, str]:
        """Export color palette as dictionary for JSON/config"""
        return {
            'navy_dark': self.navy_dark,
            'navy_medium': self.navy_medium,
            'navy_light': self.navy_light,
            'slate_dark': self.slate_dark,
            'slate_medium': self.slate_medium,
            'slate_light': self.slate_light,
            'white': self.white,
            'gray_bg': self.gray_bg,
            'cyan': self.cyan,
            'lava': self.lava,
            'gold': self.gold,
            'green': self.green,
            'red': self.red,
            'success': self.success,
            'warning': self.warning,
            'danger': self.danger,
            'info': self.info
        }


# ============================================================================
# TYPOGRAPHY SYSTEM
# ============================================================================

@dataclass
class Typography:
    """Professional typography scale for enterprise dashboards"""

    # Font Families
    font_title: str = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    font_body: str = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    font_mono: str = '"SF Mono", Consolas, Monaco, "Courier New", monospace'

    # Font Sizes (in pixels)
    size_xs: int = 10       # Fine print, captions
    size_sm: int = 12       # Body text, labels
    size_base: int = 14     # Primary body text
    size_lg: int = 16       # Emphasized text
    size_xl: int = 18       # Subheadings
    size_2xl: int = 20      # Section headers
    size_3xl: int = 24      # Page headers
    size_4xl: int = 32      # Dashboard title
    size_5xl: int = 40      # Hero numbers (KPIs)

    # Font Weights
    weight_light: int = 300
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700

    # Line Heights (unitless multipliers)
    line_tight: float = 1.2    # Headings
    line_normal: float = 1.5   # Body text
    line_relaxed: float = 1.75 # Paragraphs

    # Letter Spacing (in em)
    tracking_tight: str = '-0.025em'   # Large headings
    tracking_normal: str = '0em'       # Body text
    tracking_wide: str = '0.05em'      # All caps labels

    def get_heading_style(self, level: int) -> Dict[str, str]:
        """
        Get complete style for heading level (H1-H6)

        Args:
            level: 1-6 (H1 through H6)

        Returns:
            Dict with font-size, font-weight, line-height, letter-spacing
        """
        heading_map = {
            1: {'size': self.size_4xl, 'weight': self.weight_bold, 'line': self.line_tight, 'tracking': self.tracking_tight},
            2: {'size': self.size_3xl, 'weight': self.weight_bold, 'line': self.line_tight, 'tracking': self.tracking_tight},
            3: {'size': self.size_2xl, 'weight': self.weight_semibold, 'line': self.line_tight, 'tracking': self.tracking_normal},
            4: {'size': self.size_xl, 'weight': self.weight_semibold, 'line': self.line_normal, 'tracking': self.tracking_normal},
            5: {'size': self.size_lg, 'weight': self.weight_medium, 'line': self.line_normal, 'tracking': self.tracking_normal},
            6: {'size': self.size_base, 'weight': self.weight_medium, 'line': self.line_normal, 'tracking': self.tracking_normal},
        }

        style = heading_map.get(level, heading_map[3])
        return {
            'font-family': self.font_title,
            'font-size': f"{style['size']}px",
            'font-weight': str(style['weight']),
            'line-height': str(style['line']),
            'letter-spacing': style['tracking']
        }

    def get_kpi_number_style(self) -> Dict[str, str]:
        """Get style for large KPI numbers"""
        return {
            'font-family': self.font_title,
            'font-size': f"{self.size_5xl}px",
            'font-weight': str(self.weight_bold),
            'line-height': str(self.line_tight),
            'letter-spacing': self.tracking_tight
        }

    def get_body_style(self) -> Dict[str, str]:
        """Get style for body text"""
        return {
            'font-family': self.font_body,
            'font-size': f"{self.size_base}px",
            'font-weight': str(self.weight_normal),
            'line-height': str(self.line_normal),
            'letter-spacing': self.tracking_normal
        }

    def get_label_style(self) -> Dict[str, str]:
        """Get style for form labels and small text"""
        return {
            'font-family': self.font_body,
            'font-size': f"{self.size_sm}px",
            'font-weight': str(self.weight_medium),
            'line-height': str(self.line_normal),
            'letter-spacing': self.tracking_wide,
            'text-transform': 'uppercase'
        }

    def get_monospace_style(self) -> Dict[str, str]:
        """Get style for code/data display"""
        return {
            'font-family': self.font_mono,
            'font-size': f"{self.size_sm}px",
            'font-weight': str(self.weight_normal),
            'line-height': str(self.line_relaxed),
            'letter-spacing': self.tracking_normal
        }


# ============================================================================
# SPACING SYSTEM
# ============================================================================

@dataclass
class Spacing:
    """Consistent spacing scale (8px base unit)"""

    # Base unit: 8px
    base: int = 8

    # Scale (multiples of base)
    xs: int = 4      # 0.5 * base
    sm: int = 8      # 1 * base
    md: int = 16     # 2 * base
    lg: int = 24     # 3 * base
    xl: int = 32     # 4 * base
    xxl: int = 48    # 6 * base
    xxxl: int = 64   # 8 * base

    # Specific use cases
    card_padding: int = 24
    section_gap: int = 32
    dashboard_margin: int = 40
    chart_margin: int = 16

    def get_rem(self, size: str) -> str:
        """
        Convert spacing size to rem units (assuming 16px base)

        Args:
            size: 'xs', 'sm', 'md', 'lg', 'xl', 'xxl', 'xxxl'

        Returns:
            String like '1rem'
        """
        size_map = {
            'xs': self.xs,
            'sm': self.sm,
            'md': self.md,
            'lg': self.lg,
            'xl': self.xl,
            'xxl': self.xxl,
            'xxxl': self.xxxl
        }
        px = size_map.get(size, self.md)
        return f"{px / 16}rem"


# ============================================================================
# COMPONENT STYLES
# ============================================================================

@dataclass
class ComponentStyles:
    """Pre-defined styles for common dashboard components"""

    colors: ColorPalette
    typography: Typography
    spacing: Spacing

    def __init__(self):
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()

    def get_card_style(self) -> Dict[str, str]:
        """Professional card/panel style"""
        return {
            'background-color': self.colors.white,
            'border': f"1px solid {self.colors.slate_border}",
            'border-radius': '8px',
            'padding': f"{self.spacing.card_padding}px",
            'box-shadow': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
            'transition': 'box-shadow 0.2s ease'
        }

    def get_kpi_card_style(self) -> Dict[str, str]:
        """KPI card with emphasis"""
        base = self.get_card_style()
        base.update({
            'border-top': f"3px solid {self.colors.cyan}",
            'padding': f"{self.spacing.lg}px"
        })
        return base

    def get_button_primary_style(self) -> Dict[str, str]:
        """Primary action button"""
        return {
            'background-color': self.colors.cyan,
            'color': self.colors.white,
            'border': 'none',
            'border-radius': '6px',
            'padding': f"{self.spacing.sm}px {self.spacing.md}px",
            'font-family': self.typography.font_body,
            'font-size': f"{self.typography.size_base}px",
            'font-weight': str(self.typography.weight_medium),
            'cursor': 'pointer',
            'transition': 'background-color 0.2s ease'
        }

    def get_button_secondary_style(self) -> Dict[str, str]:
        """Secondary action button"""
        return {
            'background-color': self.colors.white,
            'color': self.colors.navy_dark,
            'border': f"1px solid {self.colors.slate_border}",
            'border-radius': '6px',
            'padding': f"{self.spacing.sm}px {self.spacing.md}px",
            'font-family': self.typography.font_body,
            'font-size': f"{self.typography.size_base}px",
            'font-weight': str(self.typography.weight_medium),
            'cursor': 'pointer',
            'transition': 'border-color 0.2s ease, background-color 0.2s ease'
        }

    def get_status_badge_style(self, status: str) -> Dict[str, str]:
        """Status badge (success, warning, danger, info)"""
        color = self.colors.get_status_color(status)

        return {
            'background-color': f"{color}20",  # 20% opacity
            'color': color,
            'border': f"1px solid {color}40",
            'border-radius': '4px',
            'padding': f"{self.spacing.xs}px {self.spacing.sm}px",
            'font-family': self.typography.font_body,
            'font-size': f"{self.typography.size_xs}px",
            'font-weight': str(self.typography.weight_semibold),
            'letter-spacing': self.typography.tracking_wide,
            'text-transform': 'uppercase'
        }

    def get_table_style(self) -> Dict[str, Dict[str, str]]:
        """Professional table styling"""
        return {
            'table': {
                'width': '100%',
                'border-collapse': 'collapse',
                'font-family': self.typography.font_body,
                'font-size': f"{self.typography.size_sm}px"
            },
            'thead': {
                'background-color': self.colors.gray_bg,
                'border-bottom': f"2px solid {self.colors.slate_border}"
            },
            'th': {
                'text-align': 'left',
                'padding': f"{self.spacing.sm}px {self.spacing.md}px",
                'font-weight': str(self.typography.weight_semibold),
                'color': self.colors.slate_dark,
                'text-transform': 'uppercase',
                'letter-spacing': self.typography.tracking_wide,
                'font-size': f"{self.typography.size_xs}px"
            },
            'td': {
                'padding': f"{self.spacing.sm}px {self.spacing.md}px",
                'border-bottom': f"1px solid {self.colors.slate_border}",
                'color': self.colors.navy_dark
            },
            'tr:hover': {
                'background-color': self.colors.gray_hover
            }
        }

    def get_tooltip_style(self) -> Dict[str, str]:
        """Tooltip/popover style"""
        return {
            'background-color': self.colors.navy_dark,
            'color': self.colors.white,
            'border-radius': '6px',
            'padding': f"{self.spacing.sm}px {self.spacing.md}px",
            'font-family': self.typography.font_body,
            'font-size': f"{self.typography.size_xs}px",
            'box-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
            'max-width': '250px',
            'z-index': '1000'
        }


# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

@dataclass
class LayoutGrid:
    """Grid system for dashboard layout"""

    # Grid configuration (12-column system)
    columns: int = 12
    gutter: int = 24  # Gap between columns

    # Breakpoints (responsive design)
    breakpoint_sm: int = 640   # Mobile
    breakpoint_md: int = 768   # Tablet
    breakpoint_lg: int = 1024  # Desktop
    breakpoint_xl: int = 1280  # Large desktop
    breakpoint_xxl: int = 1536 # Extra large

    def get_column_width(self, span: int) -> str:
        """
        Calculate column width percentage

        Args:
            span: Number of columns to span (1-12)

        Returns:
            Width as percentage string
        """
        return f"{(span / self.columns) * 100}%"

    def get_grid_template(self, cols: int = 12) -> str:
        """
        Get CSS grid-template-columns value

        Args:
            cols: Number of columns

        Returns:
            CSS grid template string
        """
        return f"repeat({cols}, minmax(0, 1fr))"


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_css_variables() -> str:
    """Export design system as CSS custom properties"""
    colors = ColorPalette()
    typography = Typography()
    spacing = Spacing()

    css = ":root {\n"

    # Colors
    css += "  /* Colors */\n"
    for name, value in colors.to_dict().items():
        css += f"  --color-{name.replace('_', '-')}: {value};\n"

    css += "\n  /* Typography */\n"
    css += f"  --font-title: {typography.font_title};\n"
    css += f"  --font-body: {typography.font_body};\n"
    css += f"  --font-mono: {typography.font_mono};\n"

    css += "\n  /* Spacing */\n"
    css += f"  --spacing-xs: {spacing.xs}px;\n"
    css += f"  --spacing-sm: {spacing.sm}px;\n"
    css += f"  --spacing-md: {spacing.md}px;\n"
    css += f"  --spacing-lg: {spacing.lg}px;\n"
    css += f"  --spacing-xl: {spacing.xl}px;\n"

    css += "}\n"

    return css


def export_json_config() -> Dict:
    """Export design system as JSON configuration"""
    colors = ColorPalette()
    typography = Typography()
    spacing = Spacing()

    return {
        "colors": colors.to_dict(),
        "typography": {
            "font_title": typography.font_title,
            "font_body": typography.font_body,
            "font_mono": typography.font_mono,
            "sizes": {
                "xs": typography.size_xs,
                "sm": typography.size_sm,
                "base": typography.size_base,
                "lg": typography.size_lg,
                "xl": typography.size_xl,
                "2xl": typography.size_2xl,
                "3xl": typography.size_3xl,
                "4xl": typography.size_4xl,
                "5xl": typography.size_5xl
            }
        },
        "spacing": {
            "xs": spacing.xs,
            "sm": spacing.sm,
            "md": spacing.md,
            "lg": spacing.lg,
            "xl": spacing.xl,
            "xxl": spacing.xxl,
            "xxxl": spacing.xxxl
        }
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=== WS5 Design System ===")
    print("Professional enterprise banking design standards\n")

    # Instantiate design system
    colors = ColorPalette()
    typography = Typography()
    spacing = Spacing()
    components = ComponentStyles()

    print("COLOR PALETTE:")
    print(f"  Primary Navy: {colors.navy_dark}")
    print(f"  Accent Cyan: {colors.cyan}")
    print(f"  Alert Lava: {colors.lava}")
    print(f"  Success Green: {colors.success}")

    print("\nTYPOGRAPHY:")
    print(f"  Title Font: {typography.font_title}")
    print(f"  KPI Size: {typography.size_5xl}px")
    print(f"  Body Size: {typography.size_base}px")

    print("\nSPACING:")
    print(f"  Card Padding: {spacing.card_padding}px")
    print(f"  Section Gap: {spacing.section_gap}px")

    print("\nCOMPONENT STYLES:")
    kpi_card = components.get_kpi_card_style()
    print(f"  KPI Card Border: {kpi_card['border-top']}")

    print("\nCSS VARIABLES (sample):")
    css_vars = export_css_variables()
    print(css_vars[:300] + "...")

    print("\n✅ Design system ready for Lakeview dashboards")
