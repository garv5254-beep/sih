import plotly.express as px
import plotly.graph_objects as go
from utils.theme import get_colors

def get_base_layout():
    """Returns a base layout for Plotly charts to ensure consistent premium design."""
    colors = get_colors()
    return dict(
        plot_bgcolor="#EDE5D0",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif", color="#292622"),
        title=dict(font=dict(color="#292622")),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            title=dict(font=dict(color="#292622")),
            tickfont=dict(color="#292622")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#d8cdb5",
            zeroline=False,
            title=dict(font=dict(color="#292622")),
            tickfont=dict(color="#292622")
        ),
        legend=dict(font=dict(color="#292622")),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color="#292622"), bordercolor="#9B493C"),
        hovermode="x unified"
    )

def create_line_chart(df, x_col, y_col, title, color=None):
    if not color: color = get_colors()['terracotta']
    fig = px.line(df, x=x_col, y=y_col, title=title)
    fig.update_traces(line_color=color, line_width=3)
    fig.update_layout(**get_base_layout())
    return fig

def create_bar_chart(df, x_col, y_col, title, color=None, orientation='v'):
    if not color: color = get_colors()['olive']
    fig = px.bar(df, x=x_col, y=y_col, title=title, orientation=orientation)
    fig.update_traces(marker_color=color, marker_line_width=0, textfont=dict(color="#292622", size=12))
    fig.update_layout(**get_base_layout())
    return fig
    
def create_donut_chart(df, names_col, values_col, title):
    colors_dict = get_colors()
    palette = [colors_dict['terracotta'], colors_dict['olive'], colors_dict['limestone']]
    
    fig = px.pie(df, names=names_col, values=values_col, title=title, hole=0.6, color_discrete_sequence=palette)
    fig.update_layout(
        plot_bgcolor="#EDE5D0",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif", color="#292622"),
        title=dict(font=dict(color="#292622")),
        legend=dict(font=dict(color="#292622")),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color="#292622"), bordercolor="#9B493C")
    )
    return fig
