"""
Jinja2-based Dashboard Generator for Consolidated Robocorp Task Logs

This is an improved version using Jinja2 templating for better security and features.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import base64
from jinja2 import Environment, FileSystemLoader, select_autoescape
from robocorp import log

from .log_consolidator import LogConsolidator


class Jinja2DashboardGenerator:
    """Generates the consolidated dashboard HTML file with Jinja2 templating."""
    
    def __init__(self, output_dir: Path, dashboard_dir: Path):
        self.output_dir = Path(output_dir)
        self.dashboard_dir = Path(dashboard_dir)
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.dashboard_dir / "templates"),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['tojson'] = self._safe_json_filter
        self.env.filters['format_timestamp'] = self._format_timestamp
        self.env.filters['format_filesize'] = self._format_filesize
        
    def _safe_json_filter(self, value):
        """Safely encode values to JSON for JavaScript embedding."""
        try:
            # Custom serializer to handle Python-specific types
            def json_serializer(obj):
                if obj is None:
                    return None  # This will become 'null' in JSON
                elif hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                else:
                    return str(obj)
            
            # Use very strict JSON encoding to prevent JavaScript syntax errors
            json_str = json.dumps(
                value, 
                ensure_ascii=True,
                default=json_serializer,
                separators=(',', ':'),  # Compact encoding
                sort_keys=True
            )
            
            # Additional escaping for JavaScript safety
            json_str = json_str.replace('</script>', '<\\/script>')
            json_str = json_str.replace('<script', '<\\script')
            json_str = json_str.replace('\u2028', '\\u2028')  # Line separator
            json_str = json_str.replace('\u2029', '\\u2029')  # Paragraph separator
            
            return json_str
        except Exception as e:
            log.warn(f"Error encoding value to JSON: {e}")
            return '{"error": "Failed to encode data"}'

    def generate_dashboard(self, output_filename: str = "consolidated_dashboard.html") -> Path:
        """Generate the complete consolidated dashboard."""
        log.info("Starting Jinja2 dashboard generation process")
        
        # Step 1: Consolidate logs
        consolidator = LogConsolidator(self.output_dir)
        consolidated_result = consolidator.consolidate_all_logs()
        
        # Step 2: Generate dashboard HTML
        dashboard_path = self.output_dir / output_filename
        self._generate_html_dashboard(consolidated_result, dashboard_path, consolidator)
        
        log.info(f"Dashboard generated successfully at {dashboard_path}")
        return dashboard_path
    
    def _generate_html_dashboard(self, consolidated_result: Dict[str, Any], output_path: Path, consolidator):
        """Generate the HTML dashboard with embedded data using Jinja2."""
        # Prepare template variables
        template_vars = self._prepare_template_variables(consolidated_result, consolidator)
        
        # Render template
        template = self.env.get_template('consolidated_dashboard_jinja2.html')
        dashboard_html = template.render(**template_vars)
        
        # Write final HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        log.info(f"Dashboard HTML generated: {output_path}")
    
    def _prepare_template_variables(self, consolidated_result: Dict[str, Any], consolidator) -> Dict[str, Any]:
        """Prepare variables for template replacement."""
        data = consolidated_result.get('data', {})
        summary = consolidated_result.get('summary', {})
        log_files = consolidated_result.get('log_files', {})
        
        # Calculate summary statistics
        total_tasks = len(set(
            execution['task_name'] 
            for execution in data.get('task_executions', [])
        ))
        
        total_log_entries = len(data.get('task_logs', []))
        total_work_items = len(data.get('work_items', []))
        total_screenshots = len(data.get('screenshots', []))
        
        # Calculate success rate
        work_items = data.get('work_items', [])
        if work_items:
            success_count = sum(1 for item in work_items if item.get('status') == 'PASS')
            success_rate = round((success_count / len(work_items)) * 100, 1)
        else:
            success_rate = 0
        
        # Calculate execution duration
        execution_timespan = summary.get('execution_timespan', {})
        execution_duration = "N/A"
        if execution_timespan.get('start') and execution_timespan.get('end'):
            try:
                start_dt = datetime.fromisoformat(execution_timespan['start'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(execution_timespan['end'].replace('Z', '+00:00'))
                duration = end_dt - start_dt
                execution_duration = f"{duration.total_seconds():.1f}s"
            except Exception:
                pass
        
        # Generate trends (simplified)
        log_trend = self._calculate_trend(summary.get('log_level_counts', {}))
        success_trend = f"+{success_rate}%" if success_rate > 0 else "No data"
        screenshot_trend = f"+{total_screenshots}" if total_screenshots > 0 else "No screenshots"
        
        # Get HTML contents if available
        html_contents = getattr(consolidator, 'html_contents', [])
        
        # Process HTML content with Base64 encoding for safe embedding
        preserved_html_contents = []
        for content_item in html_contents:
            if isinstance(content_item, dict) and 'html_content' in content_item:
                preserved_item = content_item.copy()
                html_content = preserved_item['html_content']
                
                # Only compress extremely large content (> 5MB) to prevent memory issues
                if len(html_content) > 5000000:  # 5MB limit
                    log.info(f"Large HTML content detected ({len(html_content)} bytes), implementing compression")
                    html_content = html_content[:5000000] + "\n\n<!-- Content truncated due to size -->"
                
                # Encode to Base64 for safe JavaScript embedding
                encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
                preserved_item['html_content'] = encoded_content
                
                preserved_html_contents.append(preserved_item)
            else:
                preserved_html_contents.append(content_item)
        
        # Load HTML log contents for the dashboard
        producer_log_content = self._load_log_content('producer-to-consumer/producer-logs.html')
        
        # Handle consumer logs - check for individual shard files first
        consumer_log_content = None
        consumer_shard_logs = []
        consumer_shard_log_paths = log_files.get('consumer_shard_log_paths', [])
        
        if consumer_shard_log_paths:
            # Load individual shard log files
            for shard_log_path in consumer_shard_log_paths:
                shard_content = self._load_log_content(shard_log_path)
                if shard_content:
                    # Extract shard ID from path
                    shard_match = re.search(r'consumer-shard-(\d+)-logs\.html', shard_log_path)
                    shard_id = shard_match.group(1) if shard_match else "unknown"
                    consumer_shard_logs.append({
                        'shard_id': shard_id,
                        'path': shard_log_path,
                        'content': shard_content
                    })
        else:
            # Fallback to consolidated consumer log
            consumer_log_content = self._load_log_content('consumer-to-reporter/consumer-logs.html')
        
        # Load reporter logs - check for preserved reporter logs first
        reporter_log_content = self._load_log_content('reporter-logs.html')
        if not reporter_log_content:
            # Fallback to generic log.html (might be dashboard's own log)
            reporter_log_content = self._load_log_content('log.html')
        
        return {
            'generated_date': datetime.now(),
            'execution_duration': execution_duration,
            'total_tasks': total_tasks,
            'total_log_entries': total_log_entries,
            'total_work_items': total_work_items,
            'total_screenshots': total_screenshots,
            'success_rate': success_rate,
            'log_trend': log_trend,
            'success_trend': success_trend,
            'screenshot_trend': screenshot_trend,
            'consolidated_data': consolidated_result,  # No need to serialize - Jinja2 handles it
            'html_contents': preserved_html_contents,   # No need to serialize - Jinja2 handles it
            'producer_log_path': log_files.get('producer_log_path', 'about:blank'),
            'consumer_log_path': log_files.get('consumer_log_path', 'about:blank'),
            'reporter_log_path': log_files.get('reporter_log_path', 'about:blank'),
            'producer_log_content': producer_log_content,
            'consumer_log_content': consumer_log_content,
            'reporter_log_content': reporter_log_content,
            'consumer_shard_logs': consumer_shard_logs
        }
    
    def _load_log_content(self, relative_path: str) -> str:
        """Load HTML log content from file with safe JSON encoding."""
        log_path = self.output_dir / relative_path
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Limit content size to prevent browser issues (max 1MB)
                max_size = 1024 * 1024  # 1MB
                if len(content) > max_size:
                    log.warn(f"Log content too large ({len(content)} bytes), truncating to {max_size} bytes")
                    content = content[:max_size] + "\n\n<!-- Content truncated due to size -->"
                
                # Use the safe JSON filter for proper encoding
                return self._safe_json_filter(content)
                
            except Exception as e:
                log.warn(f"Failed to load log content from {log_path}: {e}")
                return self._safe_json_filter(f"<!-- Error loading log content: {e} -->")
        else:
            log.warn(f"Log file not found: {log_path}")
            return self._safe_json_filter(f"<!-- Log file not found: {relative_path} -->")

    def _calculate_trend(self, log_level_counts: Dict[str, int]) -> str:
        """Calculate a simple trend indicator for log levels."""
        total_logs = sum(log_level_counts.values())
        if total_logs == 0:
            return "No logs"
        
        error_count = log_level_counts.get('ERROR', 0)
        warning_count = log_level_counts.get('WARNING', 0)
        
        if error_count > 0:
            return f"{error_count} errors"
        elif warning_count > 0:
            return f"{warning_count} warnings"
        else:
            return "All clear"
    
    @staticmethod
    def _format_timestamp(timestamp):
        """Format timestamp for display."""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return timestamp
        return timestamp.strftime('%B %d, %Y at %I:%M %p')
    
    @staticmethod
    def _format_filesize(bytes_size):
        """Format file size for display."""
        if not bytes_size:
            return 'N/A'
        sizes = ['B', 'KB', 'MB', 'GB']
        i = min(len(sizes) - 1, int(bytes_size.bit_length() / 10))
        return f"{bytes_size / (1024 ** i):.1f} {sizes[i]}"

    def generate_data_exports(self) -> Dict[str, Any]:
        """Generate data export files (JSON, CSV) alongside the dashboard."""
        consolidator = LogConsolidator(self.output_dir)
        
        # Export to JSON
        json_path = self.output_dir / "consolidated_data.json"
        consolidator.export_to_json(json_path)
        
        # Export to CSV
        csv_dir = self.output_dir / "csv_exports"
        csv_dir.mkdir(exist_ok=True)
        csv_files = consolidator.export_to_csv(csv_dir)
        
        return {
            'json': json_path,
            'csv_files': csv_files
        }


def main():
    """Main function for standalone execution."""
    import sys
    
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        output_dir = Path("output")
    
    dashboard_dir = Path(__file__).parent
    
    generator = Jinja2DashboardGenerator(output_dir, dashboard_dir)
    dashboard_path = generator.generate_dashboard()
    
    print(f"Dashboard generated: {dashboard_path}")


if __name__ == "__main__":
    main()
