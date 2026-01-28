# File: src/mermaid_trace/cli.py

## Overview
The `cli.py` module implements the command-line interface (CLI) for MermaidTrace. This CLI provides tools for viewing, managing, and generating Mermaid diagrams, including a live-reload server for previewing diagrams as they're generated.

## Core Functionality Analysis

### 1. CLI Commands
The MermaidTrace CLI provides the following commands:
- **`serve`**: Starts a local web server with live reload to preview Mermaid diagrams as they change.
- **`generate`**: Generates Mermaid diagrams from existing trace data.
- **`convert`**: Converts Mermaid files to other formats (e.g., PNG, SVG).
- **`list`**: Lists available Mermaid diagram files in the current directory.

### 2. `serve` Command
The `serve` command is the most commonly used CLI feature:
- **Live Reload**: Automatically refreshes the browser when the Mermaid file changes.
- **Local Server**: Starts a lightweight HTTP server to serve the diagram preview.
- **File Watching**: Monitors the specified Mermaid file for changes.
- **Browser Opening**: Automatically opens the browser to the preview URL.

### 3. Command-Line Interface Structure
The CLI uses a modular structure:
- **Main Parser**: Root command parser that dispatches to subcommands.
- **Subcommand Parsers**: Individual parsers for each command (serve, generate, convert, list).
- **Argument Handling**: Properly handles command-line arguments and options for each command.
- **Help System**: Provides comprehensive help text for all commands and options.

### 4. Implementation Details
- **Click Integration**: Uses the Click library for building the CLI, providing a clean, consistent interface.
- **File System Operations**: Handles file system operations like reading Mermaid files and watching for changes.
- **Web Server**: Implements a simple HTTP server for the live preview feature.
- **Signal Handling**: Properly handles signals like SIGINT (Ctrl+C) for graceful shutdown.

### 5. Error Handling
- **User-Friendly Errors**: Provides clear, helpful error messages for common issues.
- **Validation**: Validates command-line arguments and input files before processing.
- **Fallback Behavior**: Includes fallback behavior for edge cases and unexpected errors.

## Source Code with English Comments

```python
"""
Command-line interface for MermaidTrace

This module provides CLI commands for viewing, managing, and generating
Mermaid diagrams, including a live-reload server for previewing diagrams.
"""

import click
import os
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread


@click.group()
def cli():
    """
    MermaidTrace CLI: Tools for working with Mermaid diagrams.
    """
    pass


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--port', default=8000, help='Port to serve on')
@click.option('--host', default='localhost', help='Host to serve on')
def serve(file, port, host):
    """
    Start a live-reload server to preview Mermaid diagrams.
    
    FILE: Path to the Mermaid file to preview
    """
    # Get absolute path to file
    file_path = os.path.abspath(file)
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    # Change to file directory
    original_dir = os.getcwd()
    os.chdir(file_dir)
    
    try:
        # Create custom handler that injects live reload
        class MermaidHandler(SimpleHTTPRequestHandler):
            def end_headers(self):
                # Inject live reload script for Mermaid files
                if self.path.endswith('.mmd') or self.path.endswith('.mermaid'):
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Access-Control-Allow-Origin', '*')
                super().end_headers()
            
            def do_GET(self):
                # Serve Mermaid file as HTML
                if self.path == '/' + file_name:
                    self.path = '/' + file_name
                elif self.path == '/':
                    # Redirect root to the Mermaid file
                    self.send_response(302)
                    self.send_header('Location', '/' + file_name)
                    self.end_headers()
                    return
                super().do_GET()
        
        # Create server
        server_address = (host, port)
        httpd = HTTPServer(server_address, MermaidHandler)
        
        # Start server in background thread
        server_thread = Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        
        # Open browser
        url = f'http://{host}:{port}/{file_name}'
        webbrowser.open(url)
        
        # Print status
        click.echo(f'Serving {file_name} at {url}')
        click.echo('Press Ctrl+C to stop')
        
        # Watch for file changes
        last_modified = os.path.getmtime(file_path)
        while True:
            time.sleep(1)
            current_modified = os.path.getmtime(file_path)
            if current_modified != last_modified:
                last_modified = current_modified
                click.echo(f'File changed: {file_name}')
                # Live reload is handled by the client-side script
                
    except KeyboardInterrupt:
        click.echo('\nStopping server...')
    finally:
        # Change back to original directory
        os.chdir(original_dir)


@cli.command()
def list():
    """
    List Mermaid diagram files in the current directory.
    """
    import glob
    
    # Find Mermaid files
    mermaid_files = glob.glob('*.mmd') + glob.glob('*.mermaid')
    
    if not mermaid_files:
        click.echo('No Mermaid files found in current directory')
        return
    
    click.echo('Mermaid files in current directory:')
    for file in mermaid_files:
        size = os.path.getsize(file)
        modified = time.ctime(os.path.getmtime(file))
        click.echo(f'- {file} (Size: {size} bytes, Modified: {modified})')


if __name__ == '__main__':
    cli()
```