import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.coms.config import node_dictionary

import os
# Use an absolute path for the database connection
DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db'))

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas

def get_station_data(station_ip):
    """Extract raw data for a specific station"""
    conn = sqlite3.connect(DATABASE_PATH)
    query = f"SELECT * FROM '{station_ip}' ORDER BY time ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert time column to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Replace column names with more readable names
    df.rename(columns={
        'ns=3;s="xCurConvStatus"': 'conveyor_status',
        'ns=3;s="xBG1"': 'pallet_sensor',
        'ns=3;s="xSF5"': 'emergency_stop'
    }, inplace=True)
    
    return df

def calculate_runtime_between_state_changes(df, status_column='conveyor_status'):
    """Calculate runtime between state changes (1=running, 0=stopped)"""
    if df.empty or status_column not in df.columns:
        return pd.DataFrame(columns=['start_time', 'end_time', 'duration_seconds'])
    
    # Filter for rows where we have values (not NULL)
    status_df = df[['time', status_column]].dropna(subset=[status_column]).copy()
    
    if status_df.empty:
        return pd.DataFrame(columns=['start_time', 'end_time', 'duration_seconds'])
    
    # Find state changes
    status_df['prev_status'] = status_df[status_column].shift(1)
    status_df['state_change'] = (status_df[status_column] != status_df['prev_status'])
    
    # Get start times (when status changes to 1)
    starts = status_df[(status_df['state_change']) & (status_df[status_column] == 1.0)]['time']
    
    # Get end times (when status changes to 0)
    ends = status_df[(status_df['state_change']) & (status_df[status_column] == 0.0)]['time']
    
    # If we start with status=1, add the first timestamp as a start
    if status_df[status_column].iloc[0] == 1.0 and not status_df['state_change'].iloc[0]:
        starts = pd.concat([pd.Series([status_df['time'].iloc[0]]), starts])
    
    # If we end with status=1, add the last timestamp as an end
    if status_df[status_column].iloc[-1] == 1.0:
        ends = pd.concat([ends, pd.Series([status_df['time'].iloc[-1]])])
    
    # Create a DataFrame of start and end times
    if len(starts) == 0 or len(ends) == 0:
        return pd.DataFrame(columns=['start_time', 'end_time', 'duration_seconds'])
    
    periods = min(len(starts), len(ends))
    runtime_df = pd.DataFrame({
        'start_time': starts.iloc[:periods].reset_index(drop=True),
        'end_time': ends.iloc[:periods].reset_index(drop=True)
    })
    
    # Calculate duration in seconds
    runtime_df['duration_seconds'] = (runtime_df['end_time'] - runtime_df['start_time']).dt.total_seconds()
    
    return runtime_df

def count_events(df, column, event_value=1.0):
    """Count events (e.g., alarms, pallet passes) based on transitions to event_value"""
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=['time', 'event_count'])
    
    # Filter for rows where we have values (not NULL)
    events_df = df[['time', column]].dropna(subset=[column]).copy()
    
    if events_df.empty:
        return pd.DataFrame(columns=['time', 'event_count'])
    
    # Find transitions to event_value
    events_df['prev_value'] = events_df[column].shift(1)
    events_df['event'] = (events_df[column] == event_value) & (events_df['prev_value'] != event_value)
    
    # For emergency stops, the event is when value changes to 0
    if column == 'emergency_stop':
        events_df['event'] = (events_df[column] == 0.0) & (events_df['prev_value'] != 0.0)
    
    # Extract events with timestamps
    events_only = events_df[events_df['event']][['time']]
    events_only['event_count'] = 1
    
    return events_only

def get_daily_metrics():
    """Calculate daily metrics for all stations"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all table names (stations)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    stations = [table[0] for table in cursor.fetchall()]
    
    daily_metrics = []
    
    for station in stations:
        station_df = get_station_data(station)
        
        if station_df.empty:
            continue
        
        # Runtime calculations
        runtime_df = calculate_runtime_between_state_changes(station_df)
        
        if not runtime_df.empty:
            # Add date column for grouping
            runtime_df['date'] = runtime_df['start_time'].dt.date
            
            # Calculate daily runtime
            daily_runtime = runtime_df.groupby('date')['duration_seconds'].sum().reset_index()
            daily_runtime['station'] = station
            daily_runtime['metric'] = 'runtime_seconds'
            daily_runtime.rename(columns={'duration_seconds': 'value'}, inplace=True)
            
            daily_metrics.append(daily_runtime)
        
        # Alarm calculations
        alarms_df = count_events(station_df, 'emergency_stop', 0.0)  # 0 means alarm active
        
        if not alarms_df.empty:
            alarms_df['date'] = alarms_df['time'].dt.date
            daily_alarms = alarms_df.groupby('date')['event_count'].sum().reset_index()
            daily_alarms['station'] = station
            daily_alarms['metric'] = 'alarms_count'
            daily_alarms.rename(columns={'event_count': 'value'}, inplace=True)
            
            daily_metrics.append(daily_alarms)
    
    # Combine all metrics
    if daily_metrics:
        daily_df = pd.concat(daily_metrics, ignore_index=True)
        
        # Pivot to get a more usable format
        daily_pivot = daily_df.pivot_table(
            index=['date', 'station'],
            columns='metric',
            values='value',
            fill_value=0
        ).reset_index()
        
        return daily_pivot
    else:
        return pd.DataFrame(columns=['date', 'station', 'runtime_seconds', 'alarms_count'])

def get_station_metrics():
    """Calculate cumulative metrics for each station over time"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all table names (stations)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    stations = [table[0] for table in cursor.fetchall()]
    
    all_station_metrics = []
    
    for station in stations:
        station_df = get_station_data(station)
        
        if station_df.empty:
            continue
            
        # Get runtime periods
        runtime_df = calculate_runtime_between_state_changes(station_df)
        
        # Get alarm events
        alarms_df = count_events(station_df, 'emergency_stop', 0.0)
        
        # Get pallet events
        pallets_df = count_events(station_df, 'pallet_sensor', 1.0)
        
        # Create a date range covering all data
        if not runtime_df.empty or not alarms_df.empty or not pallets_df.empty:
            all_dates = pd.DataFrame()
            
            if not runtime_df.empty:
                all_dates = pd.concat([all_dates, pd.DataFrame({'date': runtime_df['start_time'].dt.date})])
            
            if not alarms_df.empty:
                all_dates = pd.concat([all_dates, pd.DataFrame({'date': alarms_df['time'].dt.date})])
                
            if not pallets_df.empty:
                all_dates = pd.concat([all_dates, pd.DataFrame({'date': pallets_df['time'].dt.date})])
            
            date_range = pd.DataFrame({'date': pd.date_range(start=all_dates['date'].min(), end=all_dates['date'].max(), freq='D')})
            
            # Calculate daily runtime
            daily_runtime = pd.DataFrame({'date': []})
            if not runtime_df.empty:
                runtime_df['date'] = runtime_df['start_time'].dt.date
                daily_runtime = runtime_df.groupby('date')['duration_seconds'].sum().reset_index()
            
            # Calculate daily alarms
            daily_alarms = pd.DataFrame({'date': []})
            if not alarms_df.empty:
                alarms_df['date'] = alarms_df['time'].dt.date
                daily_alarms = alarms_df.groupby('date')['event_count'].sum().reset_index()
                
            # Calculate daily pallets
            daily_pallets = pd.DataFrame({'date': []})
            if not pallets_df.empty:
                pallets_df['date'] = pallets_df['time'].dt.date
                daily_pallets = pallets_df.groupby('date')['event_count'].sum().reset_index()
            
            # Merge with date range and fill NAs with 0
            station_metrics = date_range.copy()
            station_metrics['date'] = station_metrics['date'].dt.date
            
            if not daily_runtime.empty:
                station_metrics = station_metrics.merge(daily_runtime, on='date', how='left')
                station_metrics['duration_seconds'].fillna(0, inplace=True)
            else:
                station_metrics['duration_seconds'] = 0
                
            if not daily_alarms.empty:
                # Rename the column before merging to avoid suffixes
                daily_alarms_renamed = daily_alarms.rename(columns={'event_count': 'alarms_count'})
                station_metrics = station_metrics.merge(daily_alarms_renamed, on='date', how='left')
                station_metrics['alarms_count'] = station_metrics['alarms_count'].fillna(0)
            else:
                station_metrics['alarms_count'] = 0
                
            if not daily_pallets.empty:
                # Rename the column before merging to avoid suffixes
                daily_pallets_renamed = daily_pallets.rename(columns={'event_count': 'pallets_count'})
                station_metrics = station_metrics.merge(daily_pallets_renamed, on='date', how='left')
                station_metrics['pallets_count'] = station_metrics['pallets_count'].fillna(0)
            else:
                station_metrics['pallets_count'] = 0
            
            # Calculate cumulative values
            station_metrics['cum_runtime'] = station_metrics['duration_seconds'].cumsum()
            station_metrics['cum_alarms'] = station_metrics['alarms_count'].cumsum()
            station_metrics['cum_pallets'] = station_metrics['pallets_count'].cumsum()
            station_metrics['station'] = station
            
            all_station_metrics.append(station_metrics)
    
    # Combine all stations
    if all_station_metrics:
        return pd.concat(all_station_metrics, ignore_index=True)
    else:
        return pd.DataFrame(columns=[
            'date', 'station', 'duration_seconds', 'alarms_count', 'pallets_count',
            'cum_runtime', 'cum_alarms', 'cum_pallets'
        ])

def get_overall_metrics():
    """Calculate overall totals across all stations"""
    station_metrics = get_station_metrics()
    
    if station_metrics.empty:
        return pd.DataFrame({
            'total_runtime_seconds': [0],
            'total_alarms': [0],
            'total_pallets': [0]
        })
    
    # Get the latest date for each station to get the current totals
    latest_dates = station_metrics.groupby('station')['date'].max().reset_index()
    
    # Merge to get the latest cumulative values for each station
    latest_metrics = latest_dates.merge(
        station_metrics,
        on=['station', 'date'],
        how='left'
    )
    
    # Sum across all stations
    overall = {
        'total_runtime_seconds': latest_metrics['cum_runtime'].sum(),
        'total_runtime_hours': latest_metrics['cum_runtime'].sum() / 3600,
        'total_alarms': latest_metrics['cum_alarms'].sum(),
        'total_pallets': latest_metrics['cum_pallets'].sum()
    }
    
    return pd.DataFrame([overall])

def get_analytics_dataframes():
    """Return all the analytics DataFrames needed for the streamlit app"""
    return {
        'daily_metrics': get_daily_metrics(),
        'station_metrics': get_station_metrics(),
        'overall_metrics': get_overall_metrics()
    }

if __name__ == "__main__":
    # Example usage for testing
    dfs = get_analytics_dataframes()
    print("Daily Metrics Sample:")
    print(dfs['daily_metrics'])
    print("\nStation Metrics Sample:")
    print(dfs['station_metrics'])
    print("\nOverall Metrics:")
    print(dfs['overall_metrics'])
