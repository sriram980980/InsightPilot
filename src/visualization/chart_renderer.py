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
    
    def render_chart_with_recommendation(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Render chart using LLM recommendation"""
        chart_type = recommendation.get("chart_type", "bar") if recommendation else "bar"
        
        try:
            if chart_type == "bar":
                return self._render_bar_chart_enhanced(fig, result, recommendation)
            elif chart_type == "line":
                return self._render_line_chart_enhanced(fig, result, recommendation)
            elif chart_type == "pie":
                return self._render_pie_chart_enhanced(fig, result, recommendation)
            elif chart_type == "scatter":
                return self._render_scatter_chart_enhanced(fig, result, recommendation)
            elif chart_type == "histogram":
                return self._render_histogram_enhanced(fig, result, recommendation)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Chart rendering error: {e}")
            return False
    
    def _render_bar_chart_enhanced(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Enhanced bar chart with LLM recommendation support"""
        try:
            ax = fig.add_subplot(111)
            
            # Determine x and y columns
            if recommendation:
                x_col = recommendation.get('x_column', result.columns[0])
                y_col = recommendation.get('y_column', result.columns[1] if len(result.columns) > 1 else result.columns[0])
                title = recommendation.get('title', 'Bar Chart')
            else:
                x_col = result.columns[0]
                y_col = result.columns[1] if len(result.columns) > 1 else result.columns[0]
                title = 'Bar Chart'
            
            # Get column indices
            x_idx = result.columns.index(x_col) if x_col in result.columns else 0
            y_idx = result.columns.index(y_col) if y_col in result.columns else (1 if len(result.columns) > 1 else 0)
            
            # Extract data
            x_data = [row[x_idx] for row in result.rows]
            y_data = [float(row[y_idx]) if row[y_idx] is not None else 0 for row in result.rows]
            
            # Limit to top 20 items for readability
            if len(x_data) > 20:
                # Sort by y_data and take top 20
                combined = list(zip(x_data, y_data))
                combined.sort(key=lambda x: x[1], reverse=True)
                x_data, y_data = zip(*combined[:20])
            
            # Create bar chart
            bars = ax.bar(range(len(x_data)), y_data, color='steelblue', alpha=0.8)
            
            # Customize
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(title)
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels([str(x)[:15] + '...' if len(str(x)) > 15 else str(x) for x in x_data], rotation=45, ha='right')
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}' if height != int(height) else f'{int(height)}',
                       ha='center', va='bottom', fontsize=8)
            
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            return True
            
        except Exception as e:
            self.logger.error(f"Bar chart error: {e}")
            return False
    
    def _render_line_chart_enhanced(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Enhanced line chart with LLM recommendation support"""
        try:
            ax = fig.add_subplot(111)
            
            # Determine columns
            if recommendation:
                x_col = recommendation.get('x_column', result.columns[0])
                y_col = recommendation.get('y_column', result.columns[1] if len(result.columns) > 1 else result.columns[0])
                title = recommendation.get('title', 'Line Chart')
            else:
                x_col = result.columns[0]
                y_col = result.columns[1] if len(result.columns) > 1 else result.columns[0]
                title = 'Line Chart'
            
            # Get column indices
            x_idx = result.columns.index(x_col) if x_col in result.columns else 0
            y_idx = result.columns.index(y_col) if y_col in result.columns else (1 if len(result.columns) > 1 else 0)
            
            # Extract data
            x_data = [row[x_idx] for row in result.rows]
            y_data = [float(row[y_idx]) if row[y_idx] is not None else 0 for row in result.rows]
            
            # Try to parse dates if x_data looks like dates
            x_parsed = self._try_parse_dates(x_data)
            
            # Create line chart
            ax.plot(x_parsed if x_parsed else range(len(x_data)), y_data, 
                   marker='o', linewidth=2, markersize=4, color='steelblue')
            
            # Customize
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(title)
            
            if not x_parsed:
                ax.set_xticks(range(0, len(x_data), max(1, len(x_data)//10)))
                ax.set_xticklabels([str(x_data[i])[:10] for i in range(0, len(x_data), max(1, len(x_data)//10))], rotation=45)
            else:
                ax.tick_params(axis='x', rotation=45)
            
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            return True
            
        except Exception as e:
            self.logger.error(f"Line chart error: {e}")
            return False
    
    def _render_pie_chart_enhanced(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Enhanced pie chart with LLM recommendation support"""
        try:
            ax = fig.add_subplot(111)
            
            # Determine columns
            if recommendation:
                label_col = recommendation.get('x_column', result.columns[0])
                value_col = recommendation.get('y_column', result.columns[1] if len(result.columns) > 1 else result.columns[0])
                title = recommendation.get('title', 'Pie Chart')
            else:
                label_col = result.columns[0]
                value_col = result.columns[1] if len(result.columns) > 1 else result.columns[0]
                title = 'Pie Chart'
            
            # Get column indices
            label_idx = result.columns.index(label_col) if label_col in result.columns else 0
            value_idx = result.columns.index(value_col) if value_col in result.columns else (1 if len(result.columns) > 1 else 0)
            
            # Extract data
            labels = [str(row[label_idx]) for row in result.rows]
            values = [float(row[value_idx]) if row[value_idx] is not None else 0 for row in result.rows]
            
            # Limit to top 8 slices for readability
            if len(labels) > 8:
                combined = list(zip(labels, values))
                combined.sort(key=lambda x: x[1], reverse=True)
                top_items = combined[:7]
                others_value = sum(item[1] for item in combined[7:])
                
                labels = [item[0] for item in top_items] + ['Others']
                values = [item[1] for item in top_items] + [others_value]
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                            startangle=90, colors=plt.cm.Set3.colors)
            
            # Customize
            ax.set_title(title)
            
            # Adjust text size
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_color('white')
                autotext.set_weight('bold')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pie chart error: {e}")
            return False
    
    def _render_scatter_chart_enhanced(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Enhanced scatter chart with LLM recommendation support"""
        try:
            ax = fig.add_subplot(111)
            
            if len(result.columns) < 2:
                ax.text(0.5, 0.5, 'Scatter plot requires at least 2 numeric columns', 
                       ha='center', va='center', transform=ax.transAxes)
                return False
            
            # Determine columns
            if recommendation:
                x_col = recommendation.get('x_column', result.columns[0])
                y_col = recommendation.get('y_column', result.columns[1])
                title = recommendation.get('title', 'Scatter Plot')
            else:
                x_col = result.columns[0]
                y_col = result.columns[1]
                title = 'Scatter Plot'
            
            # Get column indices
            x_idx = result.columns.index(x_col) if x_col in result.columns else 0
            y_idx = result.columns.index(y_col) if y_col in result.columns else 1
            
            # Extract numeric data
            x_data = []
            y_data = []
            for row in result.rows:
                try:
                    x_val = float(row[x_idx]) if row[x_idx] is not None else None
                    y_val = float(row[y_idx]) if row[y_idx] is not None else None
                    if x_val is not None and y_val is not None:
                        x_data.append(x_val)
                        y_data.append(y_val)
                except (ValueError, TypeError):
                    continue
            
            if not x_data:
                ax.text(0.5, 0.5, 'No valid numeric data for scatter plot', 
                       ha='center', va='center', transform=ax.transAxes)
                return False
            
            # Create scatter plot
            ax.scatter(x_data, y_data, alpha=0.6, s=50, color='steelblue')
            
            # Customize
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Scatter chart error: {e}")
            return False
    
    def _render_histogram_enhanced(self, fig, result: QueryResult, recommendation: Dict[str, Any] = None) -> bool:
        """Enhanced histogram with LLM recommendation support"""
        try:
            ax = fig.add_subplot(111)
            
            # Determine column
            if recommendation:
                data_col = recommendation.get('x_column', result.columns[0])
                title = recommendation.get('title', 'Histogram')
            else:
                # Find first numeric column
                data_col = result.columns[0]
                for col in result.columns:
                    col_idx = result.columns.index(col)
                    if self._is_numeric(result, col_idx):
                        data_col = col
                        break
                title = f'Histogram of {data_col}'
            
            # Get column index
            data_idx = result.columns.index(data_col) if data_col in result.columns else 0
            
            # Extract numeric data
            data_values = []
            for row in result.rows:
                try:
                    val = float(row[data_idx]) if row[data_idx] is not None else None
                    if val is not None:
                        data_values.append(val)
                except (ValueError, TypeError):
                    continue
            
            if not data_values:
                ax.text(0.5, 0.5, 'No valid numeric data for histogram', 
                       ha='center', va='center', transform=ax.transAxes)
                return False
            
            # Create histogram
            n_bins = min(20, max(5, len(set(data_values))))
            ax.hist(data_values, bins=n_bins, alpha=0.7, color='steelblue', edgecolor='black')
            
            # Customize
            ax.set_xlabel(data_col)
            ax.set_ylabel('Frequency')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Histogram error: {e}")
            return False
    
    def _try_parse_dates(self, data_list):
        """Try to parse data as dates"""
        try:
            parsed_dates = []
            for item in data_list:
                if isinstance(item, str):
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            parsed_dates.append(datetime.strptime(item, fmt))
                            break
                        except ValueError:
                            continue
                    else:
                        return None  # Couldn't parse this item
                else:
                    return None  # Not a string
            return parsed_dates
        except Exception:
            return None
