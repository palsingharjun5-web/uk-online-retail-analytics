import streamlit as st
import plotly.express as px


# ==========================================
# DASHBOARD COLOURS
# ==========================================

GREEN = "#087A50"
DARK_GREEN = "#075C3E"
MINT = "#A8DFC5"

PALETTE = [
    "#087A50",
    "#36A77A",
    "#A8DFC5",
    "#075C3E",
    "#70C7A0",
    "#C8EBDD",
]

TEXT = "#26382F"
MUTED = "#68786E"
GRID = "#E8EEE9"


# ==========================================
# REUSABLE CHART FUNCTION
# ==========================================

def render_chart(
    df,
    chart_type,
    x,
    y=None,
    title="",
    x_label=None,
    y_label=None,
    color=None,
    names=None,
    values=None,
    hole=0.5,
    height=380
):

    if df is None or df.empty:
        st.warning(f"No data available for {title}.")
        return

    # ======================================
    # LINE CHART
    # ======================================

    if chart_type == "line":

        fig = px.line(
            df,
            x=x,
            y=y,
            color=color,
            markers=True,
            color_discrete_sequence=PALETTE
        )

        fig.update_traces(
            line=dict(width=3.5, color=GREEN, shape="spline"),
            marker=dict(size=7, color=GREEN),
            fill="tozeroy",
            fillcolor="rgba(8, 122, 80, 0.10)"
        )

    # ======================================
    # BAR CHART
    # ======================================

    elif chart_type == "bar":

        horizontal = df[x].nunique() >= 7

        if horizontal:

            sorted_df = df.sort_values(y, ascending=True)

            fig = px.bar(
                sorted_df,
                x=y,
                y=x,
                orientation="h",
                color_discrete_sequence=[GREEN]
            )
            fig.update_traces(marker_line_width=0, marker_cornerradius=8)

        else:

            fig = px.bar(
                df,
                x=x,
                y=y,
                color_discrete_sequence=[GREEN]
            )
            fig.update_traces(marker_line_width=0, marker_cornerradius=10)

    # ======================================
    # PIE CHART
    # ======================================

    elif chart_type == "pie":

        fig = px.pie(
            df,
            names=names or x,
            values=values or y,
            color_discrete_sequence=PALETTE
        )

    # ======================================
    # DONUT CHART
    # ======================================

    elif chart_type == "donut":

        fig = px.pie(
            df,
            names=names or x,
            values=values or y,
            hole=hole,
            color_discrete_sequence=PALETTE
        )

    # ======================================
    # SCATTER CHART
    # ======================================

    elif chart_type == "scatter":

        fig = px.scatter(
            df,
            x=x,
            y=y,
            color=color,
            color_discrete_sequence=PALETTE
        )

    # ======================================
    # AREA CHART
    # ======================================

    elif chart_type == "area":

        fig = px.area(
            df,
            x=x,
            y=y,
            color=color,
            color_discrete_sequence=PALETTE
        )

    # ======================================
    # HISTOGRAM
    # ======================================

    elif chart_type == "histogram":

        fig = px.histogram(
            df,
            x=x,
            color=color,
            color_discrete_sequence=PALETTE
        )

    # ======================================
    # BOX PLOT
    # ======================================

    elif chart_type == "box":

        fig = px.box(
            df,
            x=x,
            y=y,
            color=color,
            color_discrete_sequence=PALETTE
        )

    else:

        st.error(f"Unsupported chart type: {chart_type}")
        return

    # ======================================
    # UNIVERSAL CHART STYLING
    # ======================================

    fig.update_layout(

        template="plotly_white",

        height=height,

        font=dict(
            family="Plus Jakarta Sans, Arial, sans-serif",
            size=12,
            color=TEXT
        ),

        title=None if not title else dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(
                size=16,
                color=TEXT,
                family="Plus Jakarta Sans, Arial, sans-serif"
            )
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        margin=dict(
            l=10,
            r=10,
            t=18 if title else 8,
            b=18
        ),

        showlegend=(chart_type in ["pie", "donut"]),

        legend=dict(
            font=dict(
                size=11,
                color=TEXT
            )
        ),

        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=13,
            font_color=TEXT
        )
    )

    # ======================================
    # AXIS STYLING
    # ======================================

    fig.update_xaxes(

        title=dict(
            text=x_label or x,
            font=dict(size=12, color=MUTED)
        ),

        tickfont=dict(
            size=11,
            color=MUTED
        ),

        showgrid=False,

        showline=True,
        linecolor=GRID,

        zeroline=False
    )

    fig.update_yaxes(

        title=dict(
            text=y_label or (y if y else ""),
            font=dict(size=12, color=MUTED)
        ),

        tickfont=dict(
            size=11,
            color=MUTED
        ),

        showgrid=True,
        gridcolor=GRID,

        showline=False,

        zeroline=False
    )

    # ======================================
    # DISPLAY CHART
    # ======================================

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True
        }
    )