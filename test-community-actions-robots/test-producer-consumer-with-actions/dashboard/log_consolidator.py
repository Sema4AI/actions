"""
DuckDB WASM Log Consolidation System for Robocorp Task Logs

This module consolidates logs from Producer, Consumer, and Reporter tasks
into a DuckDB database for the consolidated dashboard.
"""

import os
import re
import json
import sqlite3
import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import html
from bs4 import BeautifulSoup
import pandas as pd
from robocorp import log

class LogConsolidator:
    """Consolidates Robocorp task logs into DuckDB for dashboard consumption."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.consolidated_data = {
            'task_logs': [],
            'task_executions': [],
            'work_items': [],
            'screenshots': [],
            'performance_metrics': []
        }
        
    def _get_log_file_paths(self) -> Dict[str, str]:
        """Get the paths to the original Robocorp HTML log files for embedding."""
        log_files = {}
        
        # Producer logs
        producer_log_path = self.output_dir / "producer-to-consumer" / "producer-logs.html"
        if producer_log_path.exists():
            log_files['producer_log_path'] = str(producer_log_path.relative_to(self.output_dir))
        else:
            log_files['producer_log_path'] = None
        
        # Consumer logs - check for individual shard files first
        consumer_dir = self.output_dir / "consumer-to-reporter"
        shard_log_files = list(consumer_dir.glob("consumer-shard-*-logs.html"))
        
        if shard_log_files:
            # Multiple consumer shard log files
            log_files['consumer_shard_log_paths'] = [
                str(shard_log.relative_to(self.output_dir)) 
                for shard_log in sorted(shard_log_files)
            ]
            log_files['consumer_log_path'] = None  # No consolidated file
        else:
            # Fallback to consolidated consumer log file
            consumer_log_path = self.output_dir / "consumer-to-reporter" / "consumer-logs.html"
            if consumer_log_path.exists():
                log_files['consumer_log_path'] = str(consumer_log_path.relative_to(self.output_dir))
                log_files['consumer_shard_log_paths'] = []
            else:
                log_files['consumer_log_path'] = None
                log_files['consumer_shard_log_paths'] = []
        
        # Reporter logs - check for the preserved reporter logs first
        reporter_log_path = self.output_dir / "reporter-logs.html"
        if reporter_log_path.exists():
            log_files['reporter_log_path'] = str(reporter_log_path.relative_to(self.output_dir))
        else:
            # Fallback to the generic log.html (might be dashboard's own log)
            fallback_reporter_log_path = self.output_dir / "log.html"
            if fallback_reporter_log_path.exists():
                log_files['reporter_log_path'] = str(fallback_reporter_log_path.relative_to(self.output_dir))
            else:
                log_files['reporter_log_path'] = None
        
        log.info(f"Found log files: {log_files}")
        return log_files
        
    def consolidate_all_logs(self) -> Dict[str, Any]:
        """Consolidate all task logs into structured data."""
        log.info("Starting log consolidation process")
        
        # Get log file paths for embedding
        log_files = self._get_log_file_paths()
        
        # Process each task type for work items and screenshots only
        self._process_producer_logs()
        self._process_consumer_logs()
        self._process_reporter_logs()
        
        # Collect screenshot metadata
        self._collect_screenshot_metadata()
        
        # Note: Consumer shard HTML logs are already processed in _process_consumer_logs()
        # so we don't need to call _process_consumer_shard_html_logs() separately
        
        # If no data found, create sample data to show dashboard functionality
        if (len(self.consolidated_data['task_logs']) == 0 and 
            len(self.consolidated_data['work_items']) == 0 and
            len(self.consolidated_data['task_executions']) == 0):
            log.info("No log data found, creating sample data for dashboard demonstration")
            self._create_sample_data()
        
        # Generate summary statistics
        summary = self._generate_summary_statistics()
        
        log.info(f"Log consolidation completed. Total logs: {len(self.consolidated_data['task_logs'])}")
        return {
            'data': self.consolidated_data,
            'summary': summary,
            'log_files': log_files
        }
    
    def _process_producer_logs(self):
        """Process Producer task logs."""
        log.info("Processing Producer task logs")
        
        # Process producer HTML log file
        producer_log_path = self.output_dir / "producer-to-consumer" / "producer-logs.html"
        if producer_log_path.exists():
            self._parse_robocorp_log_html(producer_log_path, "Producer")
        
        # Process producer execution summary
        self._process_task_execution_summary("Producer")
    
    def _process_consumer_logs(self):
        """Process Consumer task logs."""
        log.info("Processing Consumer task logs")
        
        # First try to find individual consumer shard log files
        consumer_dir = self.output_dir / "consumer-to-reporter"
        shard_log_files = list(consumer_dir.glob("consumer-shard-*-logs.html"))
        
        if shard_log_files:
            log.info(f"Found {len(shard_log_files)} consumer shard log files")
            for shard_log_path in sorted(shard_log_files):
                # Extract shard ID from filename
                shard_match = re.search(r'consumer-shard-(\d+)-logs\.html', shard_log_path.name)
                shard_id = shard_match.group(1) if shard_match else "unknown"
                task_name = f"Consumer-Shard-{shard_id}"
                
                log.info(f"Processing {task_name} log file: {shard_log_path}")
                self._parse_robocorp_log_html(shard_log_path, task_name)
                
                # Process corresponding shard work items
                self._process_task_execution_summary(task_name)
        else:
            # Fallback to consolidated consumer log file (old behavior)
            consumer_log_path = self.output_dir / "consumer-to-reporter" / "consumer-logs.html"
            if consumer_log_path.exists():
                log.info("Processing consolidated consumer log file")
                self._parse_robocorp_log_html(consumer_log_path, "Consumer")
            else:
                log.info("No consumer log files found (neither individual shards nor consolidated)")
            
            # Process consumer execution summary
            self._process_task_execution_summary("Consumer")
    
    def _process_reporter_logs(self):
        """Process Reporter task logs."""
        log.info("Processing Reporter task logs")
        
        # Process reporter HTML log file - check for preserved reporter logs first
        reporter_log_path = self.output_dir / "reporter-logs.html"
        if reporter_log_path.exists():
            log.info("Processing reporter-logs.html")
            self._parse_robocorp_log_html(reporter_log_path, "Reporter")
        else:
            # Fallback to the generic log.html (might be dashboard's own log)
            fallback_reporter_log_path = self.output_dir / "log.html"
            if fallback_reporter_log_path.exists():
                log.info("Processing fallback reporter log: log.html")
                self._parse_robocorp_log_html(fallback_reporter_log_path, "Reporter")
            else:
                log.info("No reporter log files found")
        
        # Process reporter execution summary
        self._process_task_execution_summary("Reporter")
    
    def _parse_robocorp_log_html(self, log_path: Path, task_name: str):
        """Parse Robocorp HTML log file and extract log entries."""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Get file modification time to ensure consistent timestamps
            stat = log_path.stat()
            timestamp_iso = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Parse HTML to extract log entries
            soup = BeautifulSoup(html_content, 'html.parser')
            log_entries = self._extract_log_entries_from_html(soup)
            
            # Add extracted log entries to consolidated data
            for entry in log_entries:
                self.consolidated_data['task_logs'].append({
                    'task_name': task_name,
                    'timestamp': entry.get('timestamp', timestamp_iso),
                    'log_level': entry.get('level', 'INFO'),
                    'message': entry.get('message', ''),
                    'file_path': entry.get('file_path'),
                    'line_number': entry.get('line_number'),
                    'execution_time_ms': entry.get('execution_time_ms'),
                    'thread_id': entry.get('thread_id'),
                    'work_item_id': entry.get('work_item_id'),
                    'screenshot_refs': entry.get('screenshot_refs', []),
                    'html_content_path': None,
                    'html_content_size': None,
                    'has_html_content': False
                })
            
            # Also store a reference to the HTML log file for embedding in dashboard
            self.consolidated_data['task_logs'].append({
                'task_name': task_name,
                'timestamp': timestamp_iso,
                'log_level': 'HTML_LOG',
                'message': 'Interactive HTML log content',
                'file_path': str(log_path),
                'line_number': None,
                'execution_time_ms': None,
                'thread_id': None,
                'work_item_id': None,
                'screenshot_refs': [],
                'html_content_path': str(log_path.relative_to(self.output_dir)) if log_path.is_relative_to(self.output_dir) else str(log_path),
                'html_content_size': len(html_content),
                'has_html_content': True  # Flag to indicate HTML content exists
            })
            
            # Store HTML content separately for DuckDB insertion with matching timestamp
            if not hasattr(self, 'html_contents'):
                self.html_contents = []
            
            self.html_contents.append({
                'task_name': task_name,
                'timestamp': timestamp_iso,  # Use same timestamp as task_logs entry
                'html_content': html_content,
                'content_size': len(html_content)
            })
            
            log.info(f"Parsed {len(log_entries)} log entries from {task_name} HTML log file ({len(html_content)} characters)")
            
        except Exception as e:
            log.critical(f"Error reading {task_name} log file {log_path}: {e}")
    
    def _extract_log_entries_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract log entries from BeautifulSoup HTML object."""
        entries = []
        
        # Look for log entries in various HTML structures
        # This is a simplified parser - adjust based on actual Robocorp log HTML structure
        
        # Check for log table rows
        log_rows = soup.find_all('tr', class_=re.compile(r'log-|level-'))
        for row in log_rows:
            entry = self._parse_log_row(row)
            if entry:
                entries.append(entry)
        
        # Check for log div elements
        log_divs = soup.find_all('div', class_=re.compile(r'log-|message-'))
        for div in log_divs:
            entry = self._parse_log_div(div)
            if entry:
                entries.append(entry)
        
        # Fallback: parse pre-formatted text
        if not entries:
            pre_tags = soup.find_all('pre')
            for pre in pre_tags:
                text_entries = self._parse_log_text(pre.get_text())
                entries.extend(text_entries)
        
        return entries
    
    def _parse_log_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse a log table row."""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
            
            timestamp_text = cells[0].get_text(strip=True)
            level_text = cells[1].get_text(strip=True)
            message_text = cells[2].get_text(strip=True)
            
            return {
                'timestamp': self._parse_timestamp(timestamp_text),
                'level': level_text.upper(),
                'message': message_text,
                'file_path': self._extract_file_path(message_text),
                'line_number': self._extract_line_number(message_text),
                'work_item_id': self._extract_work_item_id(message_text),
                'screenshot_refs': self._extract_screenshot_refs(message_text)
            }
        except Exception:
            return None
    
    def _parse_log_div(self, div) -> Optional[Dict[str, Any]]:
        """Parse a log div element."""
        try:
            timestamp_elem = div.find(class_=re.compile(r'timestamp|time'))
            level_elem = div.find(class_=re.compile(r'level|severity'))
            message_elem = div.find(class_=re.compile(r'message|content'))
            
            timestamp_text = timestamp_elem.get_text(strip=True) if timestamp_elem else ""
            level_text = level_elem.get_text(strip=True) if level_elem else "INFO"
            message_text = message_elem.get_text(strip=True) if message_elem else div.get_text(strip=True)
            
            return {
                'timestamp': self._parse_timestamp(timestamp_text),
                'level': level_text.upper(),
                'message': message_text,
                'file_path': self._extract_file_path(message_text),
                'line_number': self._extract_line_number(message_text),
                'work_item_id': self._extract_work_item_id(message_text),
                'screenshot_refs': self._extract_screenshot_refs(message_text)
            }
        except Exception:
            return None
    
    def _parse_log_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse plain text log entries."""
        entries = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for timestamp patterns
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
            level_match = re.search(r'\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b', line)
            
            if timestamp_match:
                timestamp = self._parse_timestamp(timestamp_match.group(1))
                level = level_match.group(1) if level_match else "INFO"
                
                entries.append({
                    'timestamp': timestamp,
                    'level': level,
                    'message': line,
                    'file_path': self._extract_file_path(line),
                    'line_number': self._extract_line_number(line),
                    'work_item_id': self._extract_work_item_id(line),
                    'screenshot_refs': self._extract_screenshot_refs(line)
                })
        
        return entries
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Parse timestamp string into ISO format."""
        if not timestamp_str:
            return None
        
        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return None
    
    def _extract_file_path(self, message: str) -> Optional[str]:
        """Extract file path from log message."""
        # Look for file path patterns
        file_patterns = [
            r'(?:File|file)\s*["\']?([^"\']+\.py)["\']?',
            r'(?:in|at)\s+([^:]+\.py):?\d*',
            r'([^/\s]+\.py)',
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_line_number(self, message: str) -> Optional[int]:
        """Extract line number from log message."""
        line_match = re.search(r'line\s+(\d+)|:(\d+)', message)
        if line_match:
            return int(line_match.group(1) or line_match.group(2))
        return None
    
    def _extract_work_item_id(self, message: str) -> Optional[str]:
        """Extract work item ID from log message."""
        # Look for work item ID patterns
        patterns = [
            r'work[-_]item[-_]id[:\s]*([^\s,]+)',
            r'work[-_]item[:\s]*([^\s,]+)',
            r'item[-_]id[:\s]*([^\s,]+)',
            r'callid[:\s]*([^\s,]+)',
            r'call[-_]id[:\s]*([^\s,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_screenshot_refs(self, message: str) -> List[str]:
        """Extract screenshot references from log message."""
        screenshot_refs = []
        
        # Look for screenshot file references
        patterns = [
            r'screenshot[:\s]*([^\s,]+\.png)',
            r'saved to[:\s]*([^\s,]+\.png)',
            r'image[:\s]*([^\s,]+\.png)',
            r'([^\s,]+\.png)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            screenshot_refs.extend(matches)
        
        return screenshot_refs
    
    def _process_task_execution_summary(self, task_name: str):
        """Process task execution summary information."""
        # Look for work items JSON files to extract execution summary
        work_items_paths = []
        
        # For Producer and Reporter tasks, use standard paths
        if task_name == "Producer":
            work_items_paths = [
                self.output_dir / "producer-to-consumer" / "work-items.json"
            ]
        elif task_name == "Reporter":
            # For Reporter task, don't process individual work items since they're already processed by consumer shards
            # Just create a summary task execution entry
            consolidated_path = self.output_dir / "consumer-to-reporter" / "work-items.json"
            if consolidated_path.exists():
                try:
                    with open(consolidated_path, 'r') as f:
                        work_items = json.load(f)
                    
                    # Count summary statistics from all work items (for task execution summary only)
                    total_items = 0
                    processed_items = 0
                    failed_items = 0
                    
                    for item in work_items if isinstance(work_items, list) else []:
                        if isinstance(item, dict):
                            payload = item.get('payload', item)
                            
                            # Skip detailed form entries and reporter type items
                            if payload.get('TYPE') == 'Reporter':
                                continue
                            if payload.get('form_data') and payload.get('rationale_dict'):
                                continue
                            
                            total_items += 1
                            status = payload.get('status', 'PENDING')
                            if status == 'PASS':
                                processed_items += 1
                            elif status == 'FAIL':
                                failed_items += 1
                    
                    # Add only task execution summary (no individual work items)
                    self.consolidated_data['task_executions'].append({
                        'task_name': task_name,
                        'start_time': datetime.now().isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'duration_ms': 0,
                        'status': 'SUCCESS' if failed_items == 0 else 'PARTIAL_FAILURE',
                        'total_work_items': total_items,
                        'processed_items': processed_items,
                        'failed_items': failed_items,
                        'error_summary': f"{failed_items} items failed" if failed_items > 0 else "",
                        'log_file_path': str(consolidated_path),
                        'output_artifacts': []
                    })
                    
                    log.info(f"Reporter task execution summary: {total_items} total, {processed_items} passed, {failed_items} failed")
                    return  # Don't process individual work items for Reporter
                    
                except Exception as e:
                    log.critical(f"Error processing reporter summary: {e}")
                    return
            
            # If no consolidated file, skip work item processing for Reporter
            return
        elif task_name.startswith("Consumer-Shard-"):
            # For specific consumer shard, look for its specific work items file
            shard_id = task_name.replace("Consumer-Shard-", "")
            consumer_dir = self.output_dir / "consumer-to-reporter"
            shard_file = consumer_dir / f"work-items-{shard_id}.json"
            
            if shard_file.exists():
                work_items_paths = [shard_file]
                log.info(f"Processing individual shard file for {task_name}: {shard_file}")
            else:
                # Fall back to processing from consolidated file, but distribute items across shards
                consolidated_file = consumer_dir / "work-items.json"
                if consolidated_file.exists():
                    work_items_paths = [consolidated_file]
                    log.info(f"Processing consolidated file for {task_name}: {consolidated_file}")
                else:
                    log.warn(f"Neither shard file nor consolidated file found for {task_name}")
                    return
        elif task_name == "Consumer":
            # For generic consumer (fallback), use consolidated work items
            work_items_paths = [
                self.output_dir / "consumer-to-reporter" / "work-items.json"
            ]
        
        for path in work_items_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        work_items = json.load(f)
                    
                    # Calculate execution summary
                    total_items = len(work_items) if isinstance(work_items, list) else 0
                    processed_items = 0
                    failed_items = 0
                    
                    # Determine if we're processing from consolidated file vs individual shard file
                    is_consolidated_file = path.name == "work-items.json"
                    current_shard_id = None
                    if task_name.startswith("Consumer-Shard-"):
                        current_shard_id = int(task_name.replace("Consumer-Shard-", ""))
                    
                    item_count = 0  # Track items processed for this shard
                    for item in work_items if isinstance(work_items, list) else []:
                        if isinstance(item, dict):
                            # Extract payload data if present
                            payload = item.get('payload', item)
                            
                            # Skip reporter type items
                            if payload.get('TYPE') == 'Reporter':
                                continue
                            
                            # Skip detailed form entries (these have extensive form_data and rationale_dict)
                            # We only want the summary entries which show the actual final processing status
                            if payload.get('form_data') and payload.get('rationale_dict'):
                                log.debug(f"Skipping detailed form entry for call_id {payload.get('callid', 'unknown')}")
                                continue
                            
                            # If processing consolidated file, distribute items across shards
                            if is_consolidated_file and current_shard_id is not None:
                                # Get total number of available shards by checking log files
                                consumer_dir = self.output_dir / "consumer-to-reporter"
                                shard_log_files = list(consumer_dir.glob("consumer-shard-*-logs.html"))
                                total_shards = len(shard_log_files)
                                
                                if total_shards > 1:
                                    # Use simple modulo distribution based on item index
                                    call_id = payload.get('callid') or payload.get('contact_id', '')
                                    if call_id:
                                        # Use hash of call_id to distribute consistently
                                        item_hash = hash(call_id)
                                        assigned_shard = abs(item_hash) % total_shards
                                        if assigned_shard != current_shard_id:
                                            continue  # Skip items not assigned to this shard
                            
                            status = payload.get('status', 'PENDING')
                            # Normalize status to PASS/FAIL format
                            if status in ['PASS', 'success']:
                                processed_items += 1
                                status = 'PASS'  # Normalize for counting
                            elif status in ['FAIL', 'error', 'failed']:
                                failed_items += 1
                                status = 'FAIL'  # Normalize for counting
                            
                            # Extract identifiers from the actual data structure
                            # For GitHub repo fetching, use repo name as the main identifier
                            repo_name = payload.get('name', '')
                            repo_url = payload.get('url', '')
                            
                            # Use repo name as call_id and work_item_id since that's the unique identifier
                            call_id = repo_name or repo_url or f"item-{item_count}"
                            work_item_id = call_id
                            
                            # Convert status to expected format (PASS/FAIL instead of success/error)
                            if status == 'success':
                                status = 'PASS'
                            elif status in ['error', 'failed']:
                                status = 'FAIL'
                            else:
                                status = status.upper()
                            
                            # Add to work_items data
                            self.consolidated_data['work_items'].append({
                                'task_name': task_name,
                                'work_item_id': work_item_id,
                                'call_id': call_id,
                                'status': status,
                                'original_file': repo_url,
                                'error_message': payload.get('error', ''),
                                'retry_attempted': payload.get('retry_attempted', False),
                                'processing_time_ms': payload.get('processing_time_ms'),
                                'screenshot_paths': payload.get('screenshot_links', []),
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            item_count += 1
                    
                    # Add task execution summary
                    self.consolidated_data['task_executions'].append({
                        'task_name': task_name,
                        'start_time': datetime.now().isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'duration_ms': 0,  # Will be calculated if available
                        'status': 'SUCCESS' if failed_items == 0 else 'PARTIAL_FAILURE',
                        'total_work_items': total_items,
                        'processed_items': processed_items,
                        'failed_items': failed_items,
                        'error_summary': f"{failed_items} items failed" if failed_items > 0 else "",
                        'log_file_path': str(path),
                        'output_artifacts': []
                    })
                    
                    log.info(f"Processed {total_items} work items for {task_name}")
                    break
                    
                except Exception as e:
                    log.critical(f"Error processing work items for {task_name}: {e}")
    
    def _collect_screenshot_metadata(self):
        """Collect screenshot metadata from output directories."""
        screenshot_dir = self.output_dir / "screenshots"
        if not screenshot_dir.exists():
            return
        
        # Look for all common image formats
        for pattern in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"]:
            for screenshot_path in screenshot_dir.rglob(pattern):
                try:
                    stat = screenshot_path.stat()
                    
                    # Extract work item ID from path structure
                    work_item_id = screenshot_path.parent.name if screenshot_path.parent.name != "screenshots" else ""
                    
                    # Read and encode the image as base64
                    base64_data = None
                    mime_type = None
                    try:
                        with open(screenshot_path, 'rb') as img_file:
                            image_data = img_file.read()
                            base64_data = base64.b64encode(image_data).decode('utf-8')
                            mime_type = mimetypes.guess_type(screenshot_path)[0] or 'image/png'
                    except Exception as e:
                        log.info(f"Could not encode screenshot {screenshot_path} as base64: {e}")
                    
                    self.consolidated_data['screenshots'].append({
                        'task_name': 'Consumer',  # Screenshots are only from Consumer tasks
                        'work_item_id': work_item_id,
                        'file_path': str(screenshot_path.relative_to(self.output_dir)),
                        'file_name': screenshot_path.name,
                        'file_size': stat.st_size,
                        'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'description': f"Screenshot for work item {work_item_id}",
                        'base64_data': base64_data,
                        'mime_type': mime_type
                    })
                    
                except Exception as e:
                    log.critical(f"Error processing screenshot {screenshot_path}: {e}")
    
    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics for the dashboard."""
        summary = {
            'total_tasks': len(set(item['task_name'] for item in self.consolidated_data['task_executions'])),
            'total_log_entries': len(self.consolidated_data['task_logs']),
            'total_work_items': len(self.consolidated_data['work_items']),
            'total_screenshots': len(self.consolidated_data['screenshots']),
            'log_level_counts': {},
            'task_status_counts': {},
            'work_item_status_counts': {},
            'execution_timespan': {}
        }
        
        # Log level distribution
        for log_entry in self.consolidated_data['task_logs']:
            level = log_entry['log_level']
            summary['log_level_counts'][level] = summary['log_level_counts'].get(level, 0) + 1
        
        # Task status distribution
        for execution in self.consolidated_data['task_executions']:
            status = execution['status']
            summary['task_status_counts'][status] = summary['task_status_counts'].get(status, 0) + 1
        
        # Work item status distribution
        for work_item in self.consolidated_data['work_items']:
            status = work_item['status']
            summary['work_item_status_counts'][status] = summary['work_item_status_counts'].get(status, 0) + 1
        
        # Execution timespan
        timestamps = [entry['timestamp'] for entry in self.consolidated_data['task_logs'] if entry['timestamp']]
        if timestamps:
            summary['execution_timespan'] = {
                'start': min(timestamps),
                'end': max(timestamps),
                'duration_minutes': 0  # Calculate based on start/end
            }
        
        return summary
    
    def export_to_json(self, output_path: Path) -> Path:
        """Export consolidated data to JSON for dashboard consumption."""
        consolidated_result = self.consolidate_all_logs()
        
        with open(output_path, 'w') as f:
            json.dump(consolidated_result, f, indent=2, default=str)
        
        log.info(f"Consolidated data exported to {output_path}")
        return output_path
    
    def export_to_csv(self, output_dir: Path) -> Dict[str, Path]:
        """Export consolidated data to CSV files."""
        csv_files = {}
        
        for table_name, data in self.consolidated_data.items():
            if data:
                df = pd.DataFrame(data)
                csv_path = output_dir / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)
                csv_files[table_name] = csv_path
                log.info(f"Exported {len(data)} {table_name} records to {csv_path}")
        
        return csv_files
    
    def _create_sample_data(self):
        """Create sample data for dashboard demonstration when no actual logs exist."""
        from datetime import datetime, timedelta
        
        # Create sample task executions
        base_time = datetime.now() - timedelta(hours=1)
        
        self.consolidated_data['task_executions'] = [
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'start_time': base_time.isoformat(),
                'end_time': (base_time + timedelta(minutes=2)).isoformat(),
                'duration_ms': 120000,
                'status': 'SUCCESS',
                'total_work_items': 1,
                'processed_items': 1,
                'failed_items': 0,
                'error_summary': '',
                'log_file_path': str(self.output_dir / 'log.html'),
                'output_artifacts': ['consolidated_dashboard.html']
            }
        ]
        
        # Create sample task logs
        self.consolidated_data['task_logs'] = [
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'timestamp': base_time.isoformat(),
                'log_level': 'INFO',
                'message': 'Starting dashboard generation process',
                'file_path': 'dashboard_generator.py',
                'line_number': 30,
                'execution_time_ms': 0,
                'thread_id': 'main',
                'work_item_id': None,
                'screenshot_refs': []
            },
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'timestamp': (base_time + timedelta(seconds=30)).isoformat(),
                'log_level': 'INFO',
                'message': 'Log consolidation process started',
                'file_path': 'log_consolidator.py',
                'line_number': 35,
                'execution_time_ms': 30000,
                'thread_id': 'main',
                'work_item_id': None,
                'screenshot_refs': []
            },
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'timestamp': (base_time + timedelta(seconds=60)).isoformat(),
                'log_level': 'INFO',
                'message': 'No log data found, creating sample data for dashboard demonstration',
                'file_path': 'log_consolidator.py',
                'line_number': 49,
                'execution_time_ms': 60000,
                'thread_id': 'main',
                'work_item_id': None,
                'screenshot_refs': []
            },
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'timestamp': (base_time + timedelta(seconds=90)).isoformat(),
                'log_level': 'INFO',
                'message': 'Dashboard HTML generated successfully',
                'file_path': 'dashboard_generator.py',
                'line_number': 59,
                'execution_time_ms': 90000,
                'thread_id': 'main',
                'work_item_id': None,
                'screenshot_refs': []
            },
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'timestamp': (base_time + timedelta(minutes=2)).isoformat(),
                'log_level': 'INFO',
                'message': 'Dashboard generation completed successfully',
                'file_path': 'dashboard_generator.py',
                'line_number': 186,
                'execution_time_ms': 120000,
                'thread_id': 'main',
                'work_item_id': None,
                'screenshot_refs': []
            }
        ]
        
        # Create sample work items
        self.consolidated_data['work_items'] = [
            {
                'task_name': 'GenerateConsolidatedDashboard',
                'work_item_id': 'dashboard-001',
                'call_id': 'dashboard-generation',
                'status': 'PASS',
                'original_file': 'consolidated_dashboard.html',
                'error_message': '',
                'retry_attempted': False,
                'processing_time_ms': 120000,
                'screenshot_paths': [],
                'timestamp': (base_time + timedelta(minutes=2)).isoformat()
            }
        ]
        
        log.info("Sample data created for dashboard demonstration")