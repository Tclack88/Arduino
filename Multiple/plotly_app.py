"""
Plotly Dash Web Interface for ESP32 Data Visualization
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go

# =============================================================================
# CONFIGURATION
# =============================================================================
MAX_DATA_POINTS = 100

# Color mapping for ESP IDs
COLORS = {
    1: '#F74B31',  # Red
    2: '#FAFC4C',  # Yellow
    3: '#27F549'   # Green
}

# =============================================================================
# SHARED DATA STORAGE (will be initialized from main.py)
# =============================================================================
data_buffer = None  # Will be set to manager.list()
system_state = None  # Will be set to manager.dict()

# =============================================================================
# DASH APP SETUP
# =============================================================================
app = dash.Dash(__name__)
app.title = "ESP32 Swarm Monitor"

# =============================================================================
# LAYOUT
# =============================================================================
app.layout = html.Div([
    html.H1("ESP32 Swarm Real-Time Monitor", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': '20px'}),
    
    # Status display
    html.Div(id='status-display', 
            style={'textAlign': 'center', 'margin': '20px', 'fontSize': '24px', 'fontWeight': 'bold'}),
    
    # Main graph
    dcc.Graph(id='live-graph', style={'height': '500px'}),
    
    # Bar chart
    dcc.Graph(id='bar-chart', style={'height': '300px'}),
    
    # Stats display
    html.Div(id='stats-display',
            style={'textAlign': 'center', 'margin': '20px', 'fontSize': '16px'}),
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=500,  # Update every 500ms
        n_intervals=0
    )
], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto'})

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('status-display', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_status(n):
    """Update status display"""
    if system_state is None:
        return html.Span("Initializing...", style={'color': 'gray'})
    
    status = system_state.get('status', 'Ready')
    color = 'green' if system_state.get('running', False) else 'red'
    return html.Span(status, style={'color': color})

@app.callback(
    Output('live-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_main_graph(n):
    """Update the main time-series graph with color-changing continuous line"""
    
    if data_buffer is None:
        return {'data': [], 'layout': {'title': 'Initializing...'}}
    
    data = list(data_buffer)
    
    if not data:
        return {
            'data': [],
            'layout': {
                'title': 'Voltage vs Time (Waiting for data...)',
                'xaxis': {'title': 'Time (s)'},
                'yaxis': {'title': 'Voltage (V)', 'range': [0, 3.5]},
                'hovermode': 'closest',
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white'
            }
        }
    
    # Create segments where master ESP changes
    traces = []
    
    if len(data) == 1:
        # Single point
        d = data[0]
        traces.append(go.Scatter(
            x=[d['timestamp']],
            y=[d['value']],
            mode='markers',
            name=f'ESP {d["id"]}',
            marker={
                'color': COLORS[d['id']],
                'size': 8,
                'line': {'color': 'white', 'width': 1}
            },
            showlegend=False,
            hovertemplate=f'<b>ESP {d["id"]}</b><br>Time: %{{x:.2f}}s<br>Voltage: %{{y:.3f}}V<extra></extra>'
        ))
    else:
        # Create segments for continuous ESP master periods
        segment_start = 0
        
        for i in range(1, len(data)):
            # Check if master changed
            if data[i]['id'] != data[i-1]['id']:
                # Create segment from segment_start to i
                segment_data = data[segment_start:i+1]  # Include connection point
                times = [d['timestamp'] for d in segment_data]
                values = [d['value'] for d in segment_data]
                esp_id = data[segment_start]['id']
                
                traces.append(go.Scatter(
                    x=times,
                    y=values,
                    mode='lines+markers',
                    name=f'ESP {esp_id}',
                    line={'color': COLORS[esp_id], 'width': 3},
                    marker={
                        'color': COLORS[esp_id],
                        'size': 6,
                        'line': {'color': 'white', 'width': 1}
                    },
                    showlegend=False,
                    hovertemplate=f'<b>ESP {esp_id}</b><br>Time: %{{x:.2f}}s<br>Voltage: %{{y:.3f}}V<extra></extra>'
                ))
                
                segment_start = i
        
        # Add final segment
        segment_data = data[segment_start:]
        times = [d['timestamp'] for d in segment_data]
        values = [d['value'] for d in segment_data]
        esp_id = data[segment_start]['id']
        
        traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines+markers',
            name=f'ESP {esp_id}',
            line={'color': COLORS[esp_id], 'width': 3},
            marker={
                'color': COLORS[esp_id],
                'size': 6,
                'line': {'color': 'white', 'width': 1}
            },
            showlegend=False,
            hovertemplate=f'<b>ESP {esp_id}</b><br>Time: %{{x:.2f}}s<br>Voltage: %{{y:.3f}}V<extra></extra>'
        ))
    
    # Create custom legend showing which ESP is which color
    legend_traces = []
    for esp_id in [1, 2, 3]:
        legend_traces.append(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            name=f'ESP {esp_id}',
            marker={'color': COLORS[esp_id], 'size': 10},
            showlegend=True
        ))
    
    all_traces = traces + legend_traces
    
    # Get current master info
    current_master = data[-1]['id'] if data else None
    current_voltage = data[-1]['value'] if data else 0
    
    figure = {
        'data': all_traces,
        'layout': {
            'title': f'Live Master Voltage (Current: ESP {current_master} @ {current_voltage:.3f}V)',
            'xaxis': {'title': 'Time (s)', 'gridcolor': '#e0e0e0'},
            'yaxis': {'title': 'Voltage (V)', 'range': [0, 3.5], 'gridcolor': '#e0e0e0'},
            'hovermode': 'closest',
            'showlegend': True,
            'legend': {
                'x': 0.01, 
                'y': 0.99, 
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': '#ccc',
                'borderwidth': 1
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        }
    }
    
    return figure

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_bar_chart(n):
    """Update bar chart showing counts per ESP"""
    
    if data_buffer is None:
        return {'data': [], 'layout': {'title': 'Initializing...'}}
    
    data = list(data_buffer)
    
    # Count by ESP ID
    counts = {1: 0, 2: 0, 3: 0}
    for d in data:
        if d['id'] in counts:
            counts[d['id']] += 1
    
    figure = {
        'data': [
            go.Bar(
                x=['ESP 1 (Red)', 'ESP 2 (Yellow)', 'ESP 3 (Green)'],
                y=[counts[1], counts[2], counts[3]],
                marker={
                    'color': [COLORS[1], COLORS[2], COLORS[3]],
                    'line': {'color': 'white', 'width': 2}
                },
                text=[counts[1], counts[2], counts[3]],
                textposition='auto',
                textfont={'size': 14, 'color': 'black'},
                hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
            )
        ],
        'layout': {
            'title': 'Data Points per ESP',
            'xaxis': {'title': 'ESP ID'},
            'yaxis': {'title': 'Count'},
            'showlegend': False,
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        }
    }
    
    return figure


@app.callback(
    Output('stats-display', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_stats(n):
    """Display statistics"""
    if data_buffer is None:
        return "Initializing..."
    
    data = list(data_buffer)
    
    if not data:
        return "No data received yet. Press button to start ESP32s."
    
    # Calculate stats
    counts = {1: 0, 2: 0, 3: 0}
    for d in data:
        if d['id'] in counts:
            counts[d['id']] += 1
    
    total_time = data[-1]['timestamp'] if data else 0
    
    return html.Div([
        html.Span(f"Total Points: {len(data)} | ", style={'marginRight': '15px'}),
        html.Span(f"Duration: {total_time:.1f}s | ", style={'marginRight': '15px'}),
        html.Span(f"ESP1: {counts[1]} | ESP2: {counts[2]} | ESP3: {counts[3]}")
    ])


def run_server(host='0.0.0.0', port=8050, debug=False):
    """Helper function to run the Dash server"""
    app.run(debug=debug, host=host, port=port, use_reloader=False)
