"""
Chart rendering with Matplotlib
"""

import logging
import io
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime

from adapters.base_adapter import QueryResult


class ChartRenderer:
    """Chart renderer using Matplotlib"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style
        plt.style.use('default')
        
        # Chart type mappings
        self.chart_types = {
            'bar': self._render_bar_chart,
            'line': self._render_line_chart,
            'pie': self._render_pie_chart,
            'scatter': self._render_scatter_chart,
            'histogram': self._render_histogram,
            'table': self._render_table
        }
    
    def infer_chart_type(self, result: QueryResult) -> str:
        """Infer the best chart type based on data"""
        if not result.rows or not result.columns:
            return 'table'
        
        num_columns = len(result.columns)
        num_rows = len(result.rows)
        
        if num_columns == 1:
            return 'histogram'
        elif num_columns == 2:
            # Check if first column contains dates/timestamps
            if self._has_temporal_data(result, 0):
                return 'line'
            # Check if first column is categorical and second is numeric
            elif self._is_categorical(result, 0) and self._is_numeric(result, 1):
                if num_rows <= 10:  # Small number of categories
                    return 'pie'
                else:
                    return 'bar'
            else:
                return 'scatter'
        else:
            # Multiple columns - default to table
            return 'table'
    
    def render_chart(self, result: QueryResult, chart_type: Optional[str] = None, 
                    title: str = "", **kwargs) -> bytes:
        """Render chart and return as PNG bytes"""
        
        if chart_type is None:
            chart_type = self.infer_chart_type(result)
        
        if chart_type not in self.chart_types:
            chart_type = 'table'
        
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
            
            # Render specific chart type
            self.chart_types[chart_type](ax, result, title, **kwargs)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=kwargs.get('dpi', 300), 
                       bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            
            # Close figure to free memory
            plt.close(fig)
            
            self.logger.info(f"Chart rendered successfully: {chart_type}")
            return buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error rendering chart: {e}")
            # Return empty chart on error
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f"Chart rendering error:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='red')
            ax.set_title("Chart Error")
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)
            
            return buffer.getvalue()
    
    def _render_bar_chart(self, ax, result: QueryResult, title: str, **kwargs):
        """Render bar chart"""
        if len(result.columns) < 2:
            raise ValueError("Bar chart requires at least 2 columns")
        
        df = self._result_to_dataframe(result)
        
        x_col = result.columns[0]
        y_col = result.columns[1]
        
        bars = ax.bar(df[x_col], df[y_col], 
                     color=kwargs.get('color', 'steelblue'),
                     alpha=kwargs.get('alpha', 0.8))
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title or f"{y_col} by {x_col}")
        
        # Rotate x-axis labels if they're long
        if any(len(str(x)) > 10 for x in df[x_col]):
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
    
    def _render_line_chart(self, ax, result: QueryResult, title: str, **kwargs):
        """Render line chart"""
        if len(result.columns) < 2:
            raise ValueError("Line chart requires at least 2 columns")
        
        df = self._result_to_dataframe(result)
        
        x_col = result.columns[0]
        y_col = result.columns[1]
        
        # Handle datetime x-axis
        if self._has_temporal_data(result, 0):
            x_data = pd.to_datetime(df[x_col])
            ax.plot(x_data, df[y_col], 
                   color=kwargs.get('color', 'steelblue'),
                   linewidth=kwargs.get('linewidth', 2),
                   marker=kwargs.get('marker', 'o'),
                   markersize=kwargs.get('markersize', 4))
            
            # Format x-axis for dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df) // 10)))
            plt.setp(ax.get_xticklabels(), rotation=45)
        else:
            ax.plot(df[x_col], df[y_col],
                   color=kwargs.get('color', 'steelblue'),
                   linewidth=kwargs.get('linewidth', 2),
                   marker=kwargs.get('marker', 'o'),
                   markersize=kwargs.get('markersize', 4))
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title or f"{y_col} over {x_col}")
        ax.grid(True, alpha=0.3)
    
    def _render_pie_chart(self, ax, result: QueryResult, title: str, **kwargs):
        """Render pie chart"""
        if len(result.columns) < 2:
            raise ValueError("Pie chart requires at least 2 columns")
        
        df = self._result_to_dataframe(result)
        
        labels_col = result.columns[0]
        values_col = result.columns[1]
        
        # Filter out zero/negative values
        df_filtered = df[df[values_col] > 0]
        
        if df_filtered.empty:
            ax.text(0.5, 0.5, "No positive values to display", 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # Limit to top categories to avoid crowding
        if len(df_filtered) > 10:
            df_filtered = df_filtered.nlargest(10, values_col)
        
        wedges, texts, autotexts = ax.pie(
            df_filtered[values_col], 
            labels=df_filtered[labels_col],
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.Set3(np.linspace(0, 1, len(df_filtered)))
        )
        
        ax.set_title(title or f"Distribution of {values_col}")
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    def _render_scatter_chart(self, ax, result: QueryResult, title: str, **kwargs):
        """Render scatter plot"""
        if len(result.columns) < 2:
            raise ValueError("Scatter plot requires at least 2 columns")
        
        df = self._result_to_dataframe(result)
        
        x_col = result.columns[0]
        y_col = result.columns[1]
        
        # Color by third column if available
        if len(result.columns) > 2 and self._is_categorical(result, 2):
            color_col = result.columns[2]
            scatter = ax.scatter(df[x_col], df[y_col], c=df[color_col].astype('category').cat.codes,
                               alpha=kwargs.get('alpha', 0.7),
                               s=kwargs.get('s', 50),
                               cmap=kwargs.get('cmap', 'viridis'))
            
            # Add color bar
            plt.colorbar(scatter, ax=ax, label=color_col)
        else:
            ax.scatter(df[x_col], df[y_col],
                      color=kwargs.get('color', 'steelblue'),
                      alpha=kwargs.get('alpha', 0.7),
                      s=kwargs.get('s', 50))
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title or f"{y_col} vs {x_col}")
        ax.grid(True, alpha=0.3)
    
    def _render_histogram(self, ax, result: QueryResult, title: str, **kwargs):
        """Render histogram"""
        if len(result.columns) < 1:
            raise ValueError("Histogram requires at least 1 column")
        
        df = self._result_to_dataframe(result)
        
        col = result.columns[0]
        
        # Only plot numeric data
        if self._is_numeric(result, 0):
            data = df[col].dropna()
            
            bins = kwargs.get('bins', min(30, len(data) // 5, 50))
            
            ax.hist(data, bins=bins,
                   color=kwargs.get('color', 'steelblue'),
                   alpha=kwargs.get('alpha', 0.7),
                   edgecolor='black', linewidth=0.5)
            
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            ax.set_title(title or f"Distribution of {col}")
            ax.grid(True, alpha=0.3)
        else:
            # For categorical data, show value counts
            value_counts = df[col].value_counts()
            ax.bar(range(len(value_counts)), value_counts.values,
                  color=kwargs.get('color', 'steelblue'),
                  alpha=kwargs.get('alpha', 0.7))
            
            ax.set_xticks(range(len(value_counts)))
            ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
            ax.set_xlabel(col)
            ax.set_ylabel('Count')
            ax.set_title(title or f"Count of {col}")
    
    def _render_table(self, ax, result: QueryResult, title: str, **kwargs):
        """Render data as table"""
        ax.axis('tight')
        ax.axis('off')
        
        if not result.rows:
            ax.text(0.5, 0.5, "No data to display", 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # Limit rows for display
        max_rows = kwargs.get('max_rows', 20)
        display_data = result.rows[:max_rows]
        
        # Create table
        table = ax.table(cellText=display_data,
                        colLabels=result.columns,
                        cellLoc='center',
                        loc='center')
        
        # Style table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Color header
        for i in range(len(result.columns)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        ax.set_title(title or f"Data Table ({len(display_data)} of {len(result.rows)} rows)")
        
        if len(result.rows) > max_rows:
            ax.text(0.5, 0.02, f"Showing first {max_rows} of {len(result.rows)} rows",
                   ha='center', va='bottom', transform=ax.transAxes,
                   fontsize=8, style='italic')
    
    def _result_to_dataframe(self, result: QueryResult) -> pd.DataFrame:
        """Convert QueryResult to pandas DataFrame"""
        return pd.DataFrame(result.rows, columns=result.columns)
    
    def _is_numeric(self, result: QueryResult, column_index: int) -> bool:
        """Check if column contains numeric data"""
        if not result.rows or column_index >= len(result.columns):
            return False
        
        sample_values = [row[column_index] for row in result.rows[:10] if row[column_index] is not None]
        
        if not sample_values:
            return False
        
        return all(isinstance(val, (int, float)) or 
                  (isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit())
                  for val in sample_values)
    
    def _is_categorical(self, result: QueryResult, column_index: int) -> bool:
        """Check if column contains categorical data"""
        if not result.rows or column_index >= len(result.columns):
            return False
        
        # Count unique values
        unique_values = set()
        for row in result.rows:
            if row[column_index] is not None:
                unique_values.add(row[column_index])
        
        # Consider categorical if less than 20 unique values or less than 50% of total rows
        return len(unique_values) < 20 or len(unique_values) < len(result.rows) * 0.5
    
    def _has_temporal_data(self, result: QueryResult, column_index: int) -> bool:
        """Check if column contains temporal data"""
        if not result.rows or column_index >= len(result.columns):
            return False
        
        sample_values = [row[column_index] for row in result.rows[:5] if row[column_index] is not None]
        
        if not sample_values:
            return False
        
        # Check if values can be parsed as dates
        for val in sample_values:
            try:
                if isinstance(val, str):
                    pd.to_datetime(val)
                elif isinstance(val, datetime):
                    return True
            except:
                return False
        
        return True
    
    def save_chart(self, result: QueryResult, filepath: str, chart_type: Optional[str] = None,
                  title: str = "", **kwargs) -> bool:
        """Save chart to file"""
        try:
            chart_data = self.render_chart(result, chart_type, title, **kwargs)
            
            with open(filepath, 'wb') as f:
                f.write(chart_data)
            
            self.logger.info(f"Chart saved to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving chart: {e}")
            return False
