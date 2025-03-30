"""
GUI implementation for IPC Debugger using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import queue
import datetime
import math
import random

from .pipe_debug import PipeDebugger
from .queue_debug import QueueDebugger 
from .shared_mem_debug import SharedMemoryDebugger
from .deadlock_detector import DeadlockDetector

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        
        # Base colors
        self.colors = {
            # Main color palette
            "primary": "#1976d2",       # Primary blue
            "primary_dark": "#004ba0",  # Darker shade
            "primary_light": "#63a4ff", # Lighter shade
            "secondary": "#424242",     # Dark gray
            "accent": "#ff4081",        # Pink accent
            "success": "#4caf50",       # Green
            "warning": "#ff9800",       # Orange
            "error": "#f44336",         # Red
            "background": "#f5f5f5",    # Light gray background
            "surface": "#ffffff",       # White surface
            "text": "#212121",          # Near black text
            "text_secondary": "#757575",# Secondary text
            
            # Component-specific colors
            "pipe": "#1e88e5",          # Blue
            "queue": "#43a047",         # Green
            "shared_memory": "#8e24aa", # Purple
            "deadlock": "#e53935",      # Red
        }
        
        # Fonts
        self.fonts = {
            "heading": ("Segoe UI", 16, "bold"),
            "subheading": ("Segoe UI", 12, "bold"),
            "body": ("Segoe UI", 10),
            "small": ("Segoe UI", 9),
            "monospace": ("Consolas", 10)
        }
        
        # Spacing constants
        self.spacing = {
            "xs": 2,
            "small": 5,
            "medium": 10,
            "large": 15,
            "xl": 20
        }
        
        # Configure theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the theme to all ttk widgets"""
        # Reset to a known theme first to avoid platform-specific issues
        self.style.theme_use('default')
        
        # Configure ttk style
        self.style.configure("TFrame", background=self.colors["background"])
        self.style.configure("TLabelframe", background=self.colors["background"])
        self.style.configure("TLabelframe.Label", foreground=self.colors["primary"], 
                            font=self.fonts["subheading"])
        
        # Configure Notebook (tabs)
        self.style.configure("TNotebook", background=self.colors["background"])
        # Explicitly set contrasting colors for tabs
        self.style.configure("TNotebook.Tab", 
                            background="#e1e1e1",         # Light gray for unselected
                            foreground="#000000",         # Black text for unselected
                            padding=(10, 5))
        
        # Explicit mapping for selected tabs with high contrast
        self.style.map("TNotebook.Tab", 
                     background=[("selected", "#1976d2")],  # Blue background when selected
                     foreground=[("selected", "#ffffff")])  # White text when selected
        
        # Buttons - use hard-coded colors for maximum visibility
        self.style.configure("TButton", 
                           background="#1976d2",      # Blue background
                           foreground="#ffffff",      # White text - high contrast
                           font=self.fonts["body"],
                           padding=(8, 4))
        self.style.map("TButton",
                     background=[("active", "#0d47a1"), ("disabled", "#9e9e9e")],  # Darker blue when active, gray when disabled
                     foreground=[("active", "#ffffff"), ("disabled", "#ffffff")])  # White text in all states
        
        # Create button style - green with white text
        self.style.configure("Create.TButton",
                           background="#4caf50",      # Green background
                           foreground="#ffffff")      # White text
        self.style.map("Create.TButton",
                     background=[("active", "#388e3c"), ("disabled", "#9e9e9e")],  # Darker green when active
                     foreground=[("active", "#ffffff"), ("disabled", "#ffffff")])  # White text in all states
        
        # Delete button style - red with white text
        self.style.configure("Delete.TButton",
                           background="#f44336",      # Red background
                           foreground="#ffffff")      # White text
        self.style.map("Delete.TButton",
                     background=[("active", "#d32f2f"), ("disabled", "#9e9e9e")],  # Darker red when active
                     foreground=[("active", "#ffffff"), ("disabled", "#ffffff")])  # White text in all states
        
        # Simulate button style - orange with black text for contrast
        self.style.configure("Simulate.TButton",
                           background="#ff9800",      # Orange background
                           foreground="#000000")      # Black text for contrast with orange
        self.style.map("Simulate.TButton",
                     background=[("active", "#f57c00"), ("disabled", "#9e9e9e")],  # Darker orange when active
                     foreground=[("active", "#000000"), ("disabled", "#ffffff")])
        
        # Warning button style - yellow with black text
        self.style.configure("Warning.TButton",
                           background="#fdd835",      # Yellow background
                           foreground="#000000")      # Black text for contrast with yellow
        self.style.map("Warning.TButton",
                     background=[("active", "#fbc02d"), ("disabled", "#9e9e9e")],  # Darker yellow when active
                     foreground=[("active", "#000000"), ("disabled", "#ffffff")])
        
        # Info button style - light blue with black text
        self.style.configure("Info.TButton",
                           background="#03a9f4",      # Light blue background
                           foreground="#000000")      # Black text for contrast
        self.style.map("Info.TButton",
                     background=[("active", "#0288d1"), ("disabled", "#9e9e9e")],  # Darker blue when active
                     foreground=[("active", "#000000"), ("disabled", "#ffffff")])
        
        # Labels
        self.style.configure("TLabel", 
                           background=self.colors["background"],
                           foreground=self.colors["text"],
                           font=self.fonts["body"])
        
        # Title label style
        self.style.configure("Title.TLabel",
                           font=self.fonts["heading"],
                           foreground=self.colors["primary"])
        
        # Subheading label style
        self.style.configure("Subheading.TLabel",
                           font=self.fonts["subheading"],
                           foreground=self.colors["primary"])
        
        # Metrics label style
        self.style.configure("Metric.TLabel",
                           font=self.fonts["body"],
                           foreground=self.colors["text_secondary"])
        
        # Value label style
        self.style.configure("Value.TLabel",
                           font=("Segoe UI", 10, "bold"),
                           foreground=self.colors["primary"])
        
        # Warning label style
        self.style.configure("Warning.TLabel",
                           foreground=self.colors["warning"],
                           font=("Segoe UI", 10, "bold"))
        
        # Error label style
        self.style.configure("Error.TLabel",
                           foreground=self.colors["error"],
                           font=("Segoe UI", 10, "bold"))
        
        # Success label style
        self.style.configure("Success.TLabel",
                           foreground=self.colors["success"],
                           font=("Segoe UI", 10, "bold"))
        
        # Entry
        self.style.configure("TEntry", font=self.fonts["body"])
        
        # Combobox
        self.style.configure("TCombobox", font=self.fonts["body"])
            
        # Separator
        self.style.configure("TSeparator", background=self.colors["primary_light"])
        
        # Checkbutton
        self.style.configure("TCheckbutton", 
                           background=self.colors["background"],
                           foreground=self.colors["text"],
                           font=self.fonts["body"])
                           
        # Statusbar
        self.style.configure("Statusbar.TLabel", 
                           background=self.colors["primary_dark"],
                           foreground="white",
                           font=self.fonts["small"],
                           padding=4)
    
    def configure_text_widget(self, text_widget):
        """Apply styling to a Text or ScrolledText widget"""
        text_widget.config(
            font=self.fonts["monospace"],
            background=self.colors["surface"],
            foreground=self.colors["text"],
            padx=8,
            pady=8,
            borderwidth=1,
            relief="solid",
            selectbackground=self.colors["primary_light"],
            selectforeground=self.colors["text"],
            insertbackground=self.colors["primary"]  # Cursor color
        )
    
    def configure_canvas(self, canvas):
        """Apply styling to a Canvas widget"""
        canvas.config(
            background="#f8f9fa",  # Light gray background
            borderwidth=1,
            relief="solid",
            highlightthickness=0
        )

class IPCDebuggerGUI:
    def __init__(self, root):
        """Initialize the IPCDebuggerGUI"""
        self.root = root
        self.root.title("IPC Debugger")
        
        # Set initial window size
        self.root.geometry("1024x768")
        
        # Create theme manager
        self.theme_manager = ThemeManager(root)
        
        # Initialize variables
        self.pipe_debugger = PipeDebugger()
        self.queue_debugger = QueueDebugger()
        self.shared_mem_debugger = SharedMemoryDebugger()
        self.deadlock_detector = DeadlockDetector()
        
        # Simulation state
        self.simulation_active = False
        self.simulation_tasks = []
        
        # Deadlock simulation state
        self.deadlock_simulation_active = False
        self.deadlock_sim_button = None
        
        # Event log
        self.log_entries = []
        self.log_paused = False
        self.log_filter = None
        self.log_text = None
        self._log_scroll_position = 1.0
        
        # Set maximum log entries to prevent memory issues
        self.max_log_entries = 1000
        
        # UI update throttling
        self.last_ui_update = 0
        self.ui_update_interval = 0.2  # seconds
        
        # Highlighted elements for visualization
        self.highlighted_elements = []
        
        # Process filtering
        self.filtered_processes = None
        
        # Auto-analyze deadlocks
        self.auto_analyze_active = False
        
        # Deadlock visualization variables
        self.deadlock_canvas_scale = 1.0
        self.deadlock_canvas_offset_x = 0
        self.deadlock_canvas_offset_y = 0
        self.deadlock_canvas_drag_start = None
        self.selected_node = None
        
        # Canvas update flag
        self.canvas_needs_update = True
        
        # Setup UI
        self._setup_ui()
        
        # Setup closing handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Create the main UI elements"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        overview_tab = ttk.Frame(notebook)
        pipes_tab = ttk.Frame(notebook)
        queues_tab = ttk.Frame(notebook)
        shared_mem_tab = ttk.Frame(notebook)
        deadlock_tab = ttk.Frame(notebook)
        
        # Setup each tab
        self._setup_overview_tab(notebook)
        self._setup_pipes_tab(pipes_tab)
        self._setup_queues_tab(queues_tab)
        self._setup_shared_mem_tab(shared_mem_tab)
        self._setup_deadlock_tab(deadlock_tab)
        
        # Add tabs to notebook
        notebook.add(pipes_tab, text="Pipes")
        notebook.add(queues_tab, text="Message Queues")
        notebook.add(shared_mem_tab, text="Shared Memory")
        notebook.add(deadlock_tab, text="Deadlock Detection")
        
        # Add tab change event handler to provide warnings when switching tabs
        def on_tab_change(event):
            selected_tab = notebook.select()
            tab_text = notebook.tab(selected_tab, "text")
            
            # When switching to Deadlock Detection tab, check if there are existing processes/resources
            if tab_text == "Deadlock Detection":
                process_count = len(self.deadlock_detector.processes)
                resource_count = len(self.deadlock_detector.resources)
                
                # If there are existing processes/resources from an overview simulation, show a warning
                if process_count > 0 or resource_count > 0:
                    if process_count > 0 and resource_count > 0:
                        message = f"There are {process_count} processes and {resource_count} resources "
                        message += "that were created by previous simulations. "
                        message += "You may want to clear them before starting a new simulation."
                        self._update_status(message)
                    
                    # Update UI to make sure state is accurate
                    self._update_deadlock_ui()
        
        # Bind the tab change event
        notebook.bind("<<NotebookTabChanged>>", on_tab_change)
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", style="Statusbar.TLabel", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_overview_tab(self, notebook):
        """Set up the overview tab"""
        overview_tab = ttk.Frame(notebook)
        notebook.add(overview_tab, text="Overview")
        
        # Create top control area with simulation controls
        control_frame = ttk.Frame(overview_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Simulation speed on the left
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT, padx=2)
        self.sim_speed_var = tk.IntVar(value=1)
        speed_scale = ttk.Scale(speed_frame, from_=1, to=10, 
                               orient=tk.HORIZONTAL, length=100,
                               variable=self.sim_speed_var)
        speed_scale.pack(side=tk.LEFT, padx=2)
        
        # Create a label to display the current speed
        self.speed_label = ttk.Label(speed_frame, text="Normal")
        self.speed_label.pack(side=tk.LEFT, padx=2)
        
        # Update the speed label when the slider changes
        def update_speed_label(*args):
            speed = self.sim_speed_var.get()
            if speed <= 2:
                self.speed_label.config(text="Slow")
            elif speed <= 5:
                self.speed_label.config(text="Normal")
            elif speed <= 8:
                self.speed_label.config(text="Fast")
            else:
                self.speed_label.config(text="Turbo")
                
        # Use the correct trace syntax for tkinter variables
        self.sim_speed_var.trace_add("write", update_speed_label)
        
        # Simulation controls on the right
        sim_control_frame = ttk.Frame(control_frame)
        sim_control_frame.pack(side=tk.RIGHT, padx=5)
        
        # Duration selection
        ttk.Label(sim_control_frame, text="Duration:").pack(side=tk.LEFT, padx=2)
        self.sim_duration = tk.StringVar(value="Continuous")
        duration_combo = ttk.Combobox(sim_control_frame, 
                                    textvariable=self.sim_duration,
                                    values=["Continuous", "15s", "30s", "60s"],
                                    width=10, state="readonly")
        duration_combo.pack(side=tk.LEFT, padx=2)
        duration_combo.current(0)
        
        # Simulation control button
        self.sim_button = ttk.Button(sim_control_frame, 
                                  text="Run Demo Simulation", 
                                  command=self._toggle_simulation)
        self.sim_button.pack(side=tk.LEFT, padx=5)
        
        # Create summary frames
        summary_frame = ttk.Frame(overview_tab)
        summary_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Create IPC type summary frames
        pipe_frame = ttk.LabelFrame(summary_frame, text="Pipes")
        pipe_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.pipe_count = ttk.Label(pipe_frame, text="Active: 0", style="Value.TLabel")
        self.pipe_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        queue_frame = ttk.LabelFrame(summary_frame, text="Message Queues")
        queue_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.queue_count = ttk.Label(queue_frame, text="Active: 0", style="Value.TLabel")
        self.queue_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.queue_messages = ttk.Label(queue_frame, text="Messages: 0", style="Value.TLabel")
        self.queue_messages.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        shm_frame = ttk.LabelFrame(summary_frame, text="Shared Memory")
        shm_frame.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self.shm_count = ttk.Label(shm_frame, text="Active: 0", style="Value.TLabel")
        self.shm_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.shm_access = ttk.Label(shm_frame, text="Accesses: 0", style="Value.TLabel")
        self.shm_access.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        deadlock_frame = ttk.LabelFrame(summary_frame, text="Deadlock Detection")
        deadlock_frame.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.process_count = ttk.Label(deadlock_frame, text="Processes: 0", style="Value.TLabel")
        self.process_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.resource_count = ttk.Label(deadlock_frame, text="Resources: 0", style="Value.TLabel")
        self.resource_count.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.deadlock_count = ttk.Label(deadlock_frame, text="Deadlocks: 0", style="Value.TLabel")
        self.deadlock_count.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        
        # Configure grid columns to be evenly sized
        for i in range(4):
            summary_frame.columnconfigure(i, weight=1)
        
        # Create visualization frame
        viz_frame = ttk.LabelFrame(overview_tab, text="System Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.overview_canvas = tk.Canvas(viz_frame, bg="white")
        self.overview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.theme_manager.configure_canvas(self.overview_canvas)
        
        # Create metrics frame
        metrics_frame = ttk.LabelFrame(overview_tab, text="System Metrics")
        metrics_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Setup metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Label(metrics_grid, text="CPU Usage:", style="Metric.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cpu_usage = ttk.Label(metrics_grid, text="0%", style="Value.TLabel")
        self.cpu_usage.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="Memory Usage:", style="Metric.TLabel").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.memory_usage = ttk.Label(metrics_grid, text="0 MB", style="Value.TLabel")
        self.memory_usage.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="IPC Throughput:", style="Metric.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.ipc_throughput = ttk.Label(metrics_grid, text="0 ops/sec", style="Value.TLabel")
        self.ipc_throughput.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="Active Processes:", style="Metric.TLabel").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.active_process_count = ttk.Label(metrics_grid, text="0", style="Value.TLabel")
        self.active_process_count.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        # Event log frame
        log_frame = ttk.LabelFrame(overview_tab, text="Event Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log controls frame
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Log pause/play control
        self.log_pause_button = ttk.Button(log_control_frame, text="Pause Log", 
                                        command=self._toggle_log_pause)
        self.log_pause_button.pack(side=tk.LEFT, padx=5)
        
        # Clear log button
        ttk.Button(log_control_frame, text="Clear Log", 
                  command=self._clear_log).pack(side=tk.LEFT, padx=5)
        
        # Export log button
        ttk.Button(log_control_frame, text="Export Log", 
                  command=self._export_log).pack(side=tk.LEFT, padx=5)
        
        # Log filter frame
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.log_filter_var = tk.StringVar()
        log_filter_entry = ttk.Entry(filter_frame, textvariable=self.log_filter_var, width=30)
        log_filter_entry.pack(side=tk.LEFT, padx=5)
        
        apply_filter_btn = ttk.Button(filter_frame, text="Apply Filter", command=self._apply_log_filter)
        apply_filter_btn.pack(side=tk.LEFT, padx=5)
        
        clear_filter_btn = ttk.Button(filter_frame, text="Clear Filter", command=self._clear_log_filter)
        clear_filter_btn.pack(side=tk.LEFT, padx=5)
        
        # Log type checkboxes
        log_type_frame = ttk.Frame(filter_frame)
        log_type_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(log_type_frame, text="Show:").pack(side=tk.LEFT, padx=2)
        
        self.show_pipe_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Pipes", variable=self.show_pipe_logs, 
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_queue_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Queues", variable=self.show_queue_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_shm_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Shared Memory", variable=self.show_shm_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_deadlock_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Deadlocks", variable=self.show_deadlock_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        # Log text area with scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_text_frame, height=10, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Track scroll position changes
        self._log_scroll_position = 1.0  # Default to end
        def on_log_scroll(*args):
            self._log_scroll_position = self.log_text.yview()[0]
        self.log_text.bind("<MouseWheel>", on_log_scroll)  # Windows/macOS
        self.log_text.bind("<Button-4>", on_log_scroll)    # Linux scroll up
        self.log_text.bind("<Button-5>", on_log_scroll)    # Linux scroll down
        
        # Add tracking for scrollbar drag and release
        def on_scrollbar_drag(*args):
            self._log_scroll_position = self.log_text.yview()[0]
        
        # Create scrollbar with drag tracking
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_scrollbar.bind("<B1-Motion>", on_scrollbar_drag)
        log_scrollbar.bind("<ButtonRelease-1>", on_scrollbar_drag)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Apply styling to log text
        self.theme_manager.configure_text_widget(self.log_text)
        
        # Initialize log filter
        self.log_filter = None
    
    def _setup_pipes_tab(self, tab):
        """Set up the pipes tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Pipe IPC Debugger", style="Title.TLabel").pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Pipe ID:").pack(side=tk.LEFT, padx=5)
        self.pipe_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.pipe_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Pipe", style="Create.TButton", command=self._create_pipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Pipe", style="Delete.TButton", command=self._delete_pipe).pack(side=tk.LEFT, padx=5)
        
        # Pipe operations frame
        ops_frame = ttk.LabelFrame(frame, text="Pipe Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Pipe ID:").pack(side=tk.LEFT, padx=5)
        self.op_pipe_id_var = tk.StringVar()
        self.pipe_dropdown = ttk.Combobox(op_controls, textvariable=self.op_pipe_id_var, state="readonly")
        self.pipe_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Writer PID:").pack(side=tk.LEFT, padx=5)
        self.pipe_writer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.pipe_writer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Reader PID:").pack(side=tk.LEFT, padx=5)
        self.pipe_reader_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.pipe_reader_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Set PIDs", command=self._set_pipe_pids).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Transfer", style="Simulate.TButton", command=self._simulate_pipe_transfer).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Bottleneck", style="Simulate.TButton", command=self._simulate_pipe_bottleneck).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Pipe Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.pipe_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.pipe_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.theme_manager.configure_text_widget(self.pipe_status_text)
        self.pipe_status_text.config(state=tk.DISABLED)
        
    def _setup_queues_tab(self, tab):
        """Set up the message queues tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Message Queue Debugger", style="Title.TLabel").pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Queue ID:").pack(side=tk.LEFT, padx=5)
        self.queue_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.queue_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Capacity:").pack(side=tk.LEFT, padx=5)
        self.queue_capacity_var = tk.StringVar(value="10")
        ttk.Entry(control_frame, textvariable=self.queue_capacity_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Queue", style="Create.TButton", command=self._create_queue).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Queue", style="Delete.TButton", command=self._delete_queue).pack(side=tk.LEFT, padx=5)
        
        # Queue operations frame
        ops_frame = ttk.LabelFrame(frame, text="Queue Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Queue ID:").pack(side=tk.LEFT, padx=5)
        self.op_queue_id_var = tk.StringVar()
        self.queue_dropdown = ttk.Combobox(op_controls, textvariable=self.op_queue_id_var, state="readonly")
        self.queue_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Producer PID:").pack(side=tk.LEFT, padx=5)
        self.queue_producer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.queue_producer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Consumer PID:").pack(side=tk.LEFT, padx=5)
        self.queue_consumer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.queue_consumer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Set PIDs", command=self._set_queue_pids).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Enqueue", command=self._enqueue_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Dequeue", command=self._dequeue_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Slow Consumer", command=self._simulate_slow_consumer).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Queue Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.queue_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.queue_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.theme_manager.configure_text_widget(self.queue_status_text)
        self.queue_status_text.config(state=tk.DISABLED)
        
    def _setup_shared_mem_tab(self, tab):
        """Set up the shared memory tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Shared Memory Debugger", style="Title.TLabel").pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Memory ID:").pack(side=tk.LEFT, padx=5)
        self.memory_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.memory_id_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Size (bytes):").pack(side=tk.LEFT, padx=5)
        self.memory_size_var = tk.StringVar(value="1024")
        ttk.Entry(control_frame, textvariable=self.memory_size_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Memory Segment", style="Create.TButton", 
                  command=self._create_shared_memory).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Delete Memory Segment", style="Delete.TButton",
                  command=self._delete_shared_memory).pack(side=tk.LEFT, padx=5)
        
        # Memory operations frame
        ops_frame = ttk.LabelFrame(frame, text="Memory Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Memory ID:").pack(side=tk.LEFT, padx=5)
        self.op_memory_id_var = tk.StringVar()
        self.memory_dropdown = ttk.Combobox(op_controls, textvariable=self.op_memory_id_var, state="readonly")
        self.memory_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Process ID:").pack(side=tk.LEFT, padx=5)
        self.memory_process_id_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.memory_process_id_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Offset:").pack(side=tk.LEFT, padx=5)
        self.memory_offset_var = tk.StringVar(value="0")
        ttk.Entry(op_controls, textvariable=self.memory_offset_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Size:").pack(side=tk.LEFT, padx=5)
        self.memory_op_size_var = tk.StringVar(value="128")
        ttk.Entry(op_controls, textvariable=self.memory_op_size_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Read", command=self._read_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Write", command=self._write_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Lock", style="Simulate.TButton", command=self._lock_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Unlock", style="Simulate.TButton", command=self._unlock_shared_memory).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Shared Memory Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.shm_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.shm_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.theme_manager.configure_text_widget(self.shm_status_text)
        self.shm_status_text.config(state=tk.DISABLED)
    
    def _setup_deadlock_tab(self, tab):
        """Set up the deadlock detection tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left control panel
        control_frame = ttk.LabelFrame(frame, text="Deadlock Controls")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Process controls
        ttk.Label(control_frame, text="Process Management:", style="Subheading.TLabel").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        process_frame = ttk.Frame(control_frame)
        process_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(process_frame, text="Process ID:").pack(side=tk.LEFT)
        self.process_id_var = tk.StringVar(value="process_1")
        ttk.Entry(process_frame, textvariable=self.process_id_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(control_frame, text="Register Process", style="Create.TButton", command=self._register_process).pack(pady=5, padx=10, fill=tk.X)
        
        # Process selection and unregistration
        process_select_frame = ttk.Frame(control_frame)
        process_select_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(process_select_frame, text="Select Process:").pack(side=tk.LEFT)
        self.selected_process_var = tk.StringVar(value="")
        self.process_dropdown = ttk.Combobox(process_select_frame, textvariable=self.selected_process_var, state="readonly")
        self.process_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(control_frame, text="Unregister Process", style="Delete.TButton", command=self._unregister_process).pack(pady=5, padx=10, fill=tk.X)
        
        # Process filter
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(filter_frame, text="Filter by ID:").pack(side=tk.LEFT)
        self.process_filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.process_filter_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Add tooltip/help text for the filter
        filter_help = ttk.Label(control_frame, text="(Helps visualize large systems by showing only processes with IDs containing the filter text)", 
                               style="Metric.TLabel", wraplength=200, justify=tk.LEFT)
        filter_help.pack(pady=0, padx=10, fill=tk.X)
        
        filter_buttons_frame = ttk.Frame(control_frame)
        filter_buttons_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(filter_buttons_frame, text="Apply Filter", command=self._apply_process_filter).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(filter_buttons_frame, text="Clear Filter", command=self._clear_process_filter).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Resource controls
        ttk.Label(control_frame, text="Resource Management:", style="Subheading.TLabel").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        resource_frame = ttk.Frame(control_frame)
        resource_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(resource_frame, text="Resource ID:").pack(side=tk.LEFT)
        self.resource_id_var = tk.StringVar(value="resource_1")
        ttk.Entry(resource_frame, textvariable=self.resource_id_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Add instances field for multi-instance resources
        instances_frame = ttk.Frame(control_frame)
        instances_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(instances_frame, text="Instances:").pack(side=tk.LEFT)
        self.resource_instances_var = tk.StringVar(value="1")
        ttk.Entry(instances_frame, textvariable=self.resource_instances_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(instances_frame, text="(Number of units available)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Register Resource", style="Create.TButton", command=self._register_resource).pack(pady=5, padx=10, fill=tk.X)
        
        # Request/release controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        
        ttk.Label(control_frame, text="Request/Release:", style="Subheading.TLabel").pack(pady=(10, 0), padx=10, anchor=tk.W)
        ttk.Label(control_frame, text="Process:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        # Use the existing dropdown's variable but create a new combobox for this section
        self.request_process_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_process_var, state="readonly")
        self.request_process_dropdown.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(control_frame, text="Resource:").pack(pady=(5, 0), padx=10, anchor=tk.W)
        self.selected_resource_var = tk.StringVar(value="")
        self.resource_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_resource_var, state="readonly")
        self.resource_dropdown.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(control_frame, text="Request Resource", command=self._request_resource).pack(pady=5, padx=10, fill=tk.X)
        ttk.Button(control_frame, text="Release Resource", command=self._release_resource).pack(pady=5, padx=10, fill=tk.X)
        
        # Analysis controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        ttk.Label(control_frame, text="Analysis:", style="Subheading.TLabel").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        analysis_frame = ttk.Frame(control_frame)
        analysis_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(analysis_frame, text="Analyze", command=self._analyze_deadlocks).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.auto_analyze_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(analysis_frame, text="Auto", variable=self.auto_analyze_var, 
                       command=self._toggle_auto_analysis).pack(side=tk.LEFT, padx=(5, 0))
        
        # Simulation controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        ttk.Label(control_frame, text="Simulation:", style="Subheading.TLabel").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        # Add help text for simulation vs manual registration
        sim_help = ttk.Label(control_frame, text="(Quick simulation clears existing processes/resources and creates a new deadlock scenario)", 
                            style="Metric.TLabel", wraplength=200, justify=tk.LEFT)
        sim_help.pack(pady=0, padx=10, fill=tk.X)
        
        sim_frame = ttk.Frame(control_frame)
        sim_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(sim_frame, text="Processes:").pack(side=tk.LEFT)
        self.sim_processes_var = tk.StringVar(value="3")
        ttk.Entry(sim_frame, textvariable=self.sim_processes_var, width=3).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sim_frame, text="Resources:").pack(side=tk.LEFT)
        self.sim_resources_var = tk.StringVar(value="3")
        ttk.Entry(sim_frame, textvariable=self.sim_resources_var, width=3).pack(side=tk.LEFT, padx=5)
        
        # Store a reference to the simulation button
        self.deadlock_sim_button = ttk.Button(
            control_frame, 
            text="Simulate Deadlock", 
            style="Simulate.TButton", 
            command=self._simulate_deadlock
        )
        self.deadlock_sim_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Add a Clear All button to reset the system
        ttk.Button(control_frame, text="Clear All Processes & Resources", style="Delete.TButton", command=self._clear_deadlock_data).pack(pady=5, padx=10, fill=tk.X)
        
        # Deadlock visualization area
        vis_frame = ttk.LabelFrame(frame, text="Deadlock Visualization")
        vis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for deadlock visualization (wait-for graph)
        canvas_frame = ttk.Frame(vis_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.deadlock_canvas = tk.Canvas(canvas_frame, bg="white")
        self.deadlock_canvas.pack(fill=tk.BOTH, expand=True)
        self.theme_manager.configure_canvas(self.deadlock_canvas)
        
        # Add scrollbars for large graphs
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.deadlock_canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.deadlock_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.deadlock_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        self.deadlock_canvas.configure(scrollregion=(0, 0, 1000, 1000))
        
        # Add zoom controls
        zoom_frame = ttk.Frame(vis_frame)
        zoom_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(zoom_frame, text="Zoom In", command=self._zoom_in_deadlock).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self._zoom_out_deadlock).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self._reset_deadlock_view).pack(side=tk.LEFT, padx=2)
        
        # Setup canvas interactions
        self.deadlock_canvas.bind("<ButtonPress-1>", self._deadlock_canvas_click)
        self.deadlock_canvas.bind("<B1-Motion>", self._deadlock_canvas_drag)
        self.deadlock_canvas.bind("<MouseWheel>", self._deadlock_canvas_zoom)  # Windows/macOS
        self.deadlock_canvas.bind("<Button-4>", self._deadlock_canvas_zoom)    # Linux scroll up
        self.deadlock_canvas.bind("<Button-5>", self._deadlock_canvas_zoom)    # Linux scroll down
        
        # Initialize canvas state
        self.deadlock_canvas_drag_start = None
        self.deadlock_canvas_clicked_item = None
        
        # Deadlock status display
        status_frame = ttk.LabelFrame(vis_frame, text="Deadlock Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label for quick overview
        self.deadlock_status = ttk.Label(status_frame, text="No deadlocks detected")
        self.deadlock_status.pack(fill=tk.X, padx=5, pady=5)
        
        # Detailed status text
        self.deadlock_status_text = scrolledtext.ScrolledText(status_frame, height=5)
        self.deadlock_status_text.pack(fill=tk.BOTH, expand=True)
        self.theme_manager.configure_text_widget(self.deadlock_status_text)
        self.deadlock_status_text.config(state=tk.DISABLED)
        
        # Suggestions area
        suggestion_frame = ttk.LabelFrame(vis_frame, text="Analysis & Suggestions")
        suggestion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.deadlock_suggestion_text = scrolledtext.ScrolledText(suggestion_frame, height=3)
        self.deadlock_suggestion_text.pack(fill=tk.BOTH, expand=True)
        self.theme_manager.configure_text_widget(self.deadlock_suggestion_text)
        self.deadlock_suggestion_text.config(state=tk.DISABLED)
        
        # Initialize process filter
        self.filtered_processes = None
        self.auto_analyze_active = False
    
    # ------ Action Callbacks ------
    
    # Pipe actions
    def _create_pipe(self):
        """Create a new pipe"""
        pipe_id = self.pipe_id_var.get()
        if pipe_id:
            self.pipe_debugger.register_pipe(pipe_id)
            self._update_pipe_ui()
            self.status_bar.config(text=f"Pipe {pipe_id} created")
    
    def _delete_pipe(self):
        """Delete a pipe"""
        pipe_id = self.op_pipe_id_var.get()
        if pipe_id:
            self.pipe_debugger.unregister_pipe(pipe_id)
            self._update_pipe_ui()
            self.status_bar.config(text=f"Pipe {pipe_id} deleted")
    
    def _set_pipe_pids(self):
        """Set writer and reader PIDs for a pipe"""
        pipe_id = self.op_pipe_id_var.get()
        writer_pid = self.pipe_writer_pid_var.get()
        reader_pid = self.pipe_reader_pid_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            
            if writer_pid:
                pipe_status["writer_pid"] = writer_pid
            
            if reader_pid:
                pipe_status["reader_pid"] = reader_pid
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self._update_pipe_ui()
            self.status_bar.config(text=f"PIDs updated for pipe {pipe_id}")
    
    def _simulate_pipe_transfer(self):
        """Simulate data transfer through pipe"""
        pipe_id = self.op_pipe_id_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            pipe_status["status"] = "transferring"
            pipe_status["progress"] = 0
            pipe_status["bytes_transferred"] = random.randint(1000, 10000)
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self.pipe_debugger.add_log_entry(pipe_id, "Started data transfer")
            
            # Simulate progress updates
            def update_progress(p_id, progress):
                if progress <= 100:
                    p_status = self.pipe_debugger.get_pipe_status().get(p_id, {}).copy()
                    if p_status and p_status.get("status") == "transferring":
                        p_status["progress"] = progress
                        self.pipe_debugger.update_pipe_status(p_id, p_status)
                        self._update_pipe_ui()
                        
                        # Schedule next update
                        if progress < 100:
                            self.root.after(300, update_progress, p_id, progress + 10)
                        else:
                            p_status["status"] = "idle"
                            self.pipe_debugger.update_pipe_status(p_id, p_status)
                            self.pipe_debugger.add_log_entry(p_id, "Transfer completed")
            
            # Start progress updates
            self.root.after(300, update_progress, pipe_id, 10)
            self.status_bar.config(text=f"Transfer started on pipe {pipe_id}")
    
    def _simulate_pipe_bottleneck(self):
        """Simulate a bottleneck in the pipe"""
        pipe_id = self.op_pipe_id_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            pipe_status["status"] = "bottleneck"
            pipe_status["progress"] = 50  # Stuck at 50%
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self.pipe_debugger.add_log_entry(pipe_id, "Bottleneck detected")
            self._update_pipe_ui()
            self.status_bar.config(text=f"Bottleneck simulated on pipe {pipe_id}")
    
    # Queue actions
    def _create_queue(self):
        """Create a new message queue"""
        queue_id = self.queue_id_var.get()
        capacity = int(self.queue_capacity_var.get() or "10")
        
        if queue_id:
            self.queue_debugger.register_queue(queue_id, capacity)
            self._update_queue_ui()
            self.status_bar.config(text=f"Queue {queue_id} created with capacity {capacity}")
    
    def _delete_queue(self):
        """Delete a message queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            self.queue_debugger.unregister_queue(queue_id)
            self._update_queue_ui()
            self.status_bar.config(text=f"Queue {queue_id} deleted")
    
    def _set_queue_pids(self):
        """Set producer and consumer PIDs for a queue"""
        queue_id = self.op_queue_id_var.get()
        producer_pid = self.queue_producer_pid_var.get()
        consumer_pid = self.queue_consumer_pid_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if producer_pid:
                queue_status["producer_pid"] = producer_pid
            
            if consumer_pid:
                queue_status["consumer_pid"] = consumer_pid
            
            self.queue_debugger.update_queue_status(queue_id, queue_status)
            self._update_queue_ui()
            self.status_bar.config(text=f"PIDs updated for queue {queue_id}")
    
    def _enqueue_message(self):
        """Enqueue a message to the selected queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status and queue_status.get("message_count", 0) < queue_status.get("capacity", 10):
                queue_status["message_count"] = queue_status.get("message_count", 0) + 1
                queue_status["status"] = "active"
                
                self.queue_debugger.update_queue_status(queue_id, queue_status)
                self.queue_debugger.add_log_entry(queue_id, "Message enqueued")
                self._update_queue_ui()
                self.status_bar.config(text=f"Message enqueued to queue {queue_id}")
            else:
                self.status_bar.config(text=f"Queue {queue_id} is full")
    
    def _dequeue_message(self):
        """Dequeue a message from the selected queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status and queue_status.get("message_count", 0) > 0:
                queue_status["message_count"] = queue_status.get("message_count", 0) - 1
                
                if queue_status["message_count"] == 0:
                    queue_status["status"] = "idle"
                
                self.queue_debugger.update_queue_status(queue_id, queue_status)
                self.queue_debugger.add_log_entry(queue_id, "Message dequeued")
                self._update_queue_ui()
                self.status_bar.config(text=f"Message dequeued from queue {queue_id}")
            else:
                self.status_bar.config(text=f"Queue {queue_id} is empty")
    
    def _simulate_slow_consumer(self):
        """Simulate a slow consumer scenario with queue filling up"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status:
                capacity = queue_status.get("capacity", 10)
                
                # Fill up the queue gradually
                def fill_queue(q_id, count):
                    q_status = self.queue_debugger.get_queue_status().get(q_id, {}).copy()
                    
                    if q_status and count < capacity:
                        q_status["message_count"] = count + 1
                        q_status["status"] = "active"
                        
                        if q_status["message_count"] >= capacity:
                            q_status["status"] = "full"
                            self.queue_debugger.add_log_entry(q_id, "Queue is full - slow consumer detected")
                        
                        self.queue_debugger.update_queue_status(q_id, q_status)
                        self._update_queue_ui()
                        
                        # Schedule next fill
                        self.root.after(500, fill_queue, q_id, count + 1)
                
                # Start filling
                current_count = queue_status.get("message_count", 0)
                self.root.after(500, fill_queue, queue_id, current_count)
                self.status_bar.config(text=f"Simulating slow consumer on queue {queue_id}")
    
    # Shared memory actions
    def _create_shared_memory(self):
        """Create a new shared memory segment"""
        memory_id = self.memory_id_var.get()
        size = int(self.memory_size_var.get() or "1024")
        
        if memory_id:
            self.shared_mem_debugger.register_memory_segment(memory_id, size)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} created with size {size} bytes")
    
    def _delete_shared_memory(self):
        """Delete a shared memory segment"""
        memory_id = self.memory_id_var.get()
        
        if memory_id:
            self.shared_mem_debugger.unregister_memory_segment(memory_id)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} deleted")
            
    def _read_shared_memory(self):
        """Simulate reading from shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Update memory status
                memory_status["status"] = "active"
                memory_status["access_count"] = memory_status.get("access_count", 0) + 1
                
                # Add to recent readers
                recent_readers = memory_status.get("recent_readers", [])
                if process_id not in recent_readers:
                    recent_readers.append(process_id)
                memory_status["recent_readers"] = recent_readers
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Read by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Read from shared memory {memory_id}")
    
    def _write_shared_memory(self):
        """Simulate writing to shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Update memory status
                memory_status["status"] = "active"
                memory_status["access_count"] = memory_status.get("access_count", 0) + 1
                memory_status["last_writer"] = process_id
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Written by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Wrote to shared memory {memory_id}")
    
    def _lock_shared_memory(self):
        """Simulate locking a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Add locked region
                locked_regions = memory_status.get("locked_regions", [])
                new_region = {"offset": offset, "size": size, "owner": process_id}
                locked_regions.append(new_region)
                memory_status["locked_regions"] = locked_regions
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Region locked by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Locked region in shared memory {memory_id}")
    
    def _unlock_shared_memory(self):
        """Simulate unlocking a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Remove matching locked region
                locked_regions = memory_status.get("locked_regions", [])
                memory_status["locked_regions"] = [
                    r for r in locked_regions 
                    if not (r.get("offset") == offset and r.get("size") == size)
                ]
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Region unlocked by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Unlocked region in shared memory {memory_id}")
    
    # Deadlock actions
    def _register_process(self):
        """Register a new process"""
        # Get next available process ID
        process_id = f"P{len(self.deadlock_detector.processes) + 1}"
        
        # Register with deadlock detector
        self.deadlock_detector.register_process(process_id)
        
        # Update the UI
        self._refresh_ui()
        self._log_event(f"Registered process {process_id}")
    
    def _unregister_process(self):
        """Unregister a process from deadlock tracking"""
        process_id = self.selected_process_var.get()
        if process_id:
            # Unregister the process
            result = self.deadlock_detector.unregister_process(process_id)
            if result:
                self.status_bar.config(text=f"Process {process_id} unregistered")
                # Clear the selection
                self.selected_process_var.set("")
                # Update UI immediately
                self._update_deadlock_ui()
            else:
                self.status_bar.config(text=f"Failed to unregister process {process_id}")
        else:
            self.status_bar.config(text="No process selected")
    
    def _register_resource(self):
        """Register a resource for deadlock detection"""
        # Get next available resource ID number
        next_id = len(self.deadlock_detector.resources) + 1
        resource_id = f"R{next_id}"
        
        try:
            # Get instances value (default to 1 if invalid)
            instances = 1
            instances_str = self.resource_instances_var.get()
            if instances_str and instances_str.isdigit():
                instances = max(1, int(instances_str))  # Ensure at least 1 instance
            
            # Register with instances
            self.deadlock_detector.register_resource(resource_id, instances=instances)
            
            # Log using the stable resource ID
            self._log_event(f"Registered resource {resource_id}")
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Resource {resource_id} registered with {instances} instances")
        except ValueError as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Input Error", f"Invalid number of instances: {self.resource_instances_var.get()}")
    
    def _unregister_resource(self):
        """Unregister a resource from deadlock detection"""
        resource_id = self.resource_id_var.get()
        if resource_id:
            self.deadlock_detector.unregister_resource(resource_id)
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Resource {resource_id} unregistered")
    
    def _set_resource_owner(self):
        """Set a process as the owner of a resource"""
        process_id = self.owner_process_var.get()
        resource_id = self.owned_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.set_resource_owner(resource_id, process_id)
            
            # Get canonical IDs for logging
            canonical_process = self._get_canonical_process_id(process_id)
            canonical_resource = self._get_canonical_resource_id(resource_id)
            
            self._log_event(f"Process {canonical_process} acquired resource {canonical_resource}")
            
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} set as owner of resource {resource_id}")
    
    def _set_process_waiting(self):
        """Set a process as waiting for a resource"""
        process_id = self.waiting_process_var.get()
        resource_id = self.waited_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.add_waiting_process(resource_id, process_id)
            
            # Get canonical IDs for logging
            canonical_process = self._get_canonical_process_id(process_id)
            canonical_resource = self._get_canonical_resource_id(resource_id)
            
            self._log_event(f"Process {canonical_process} waiting for resource {canonical_resource}")
            
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} set as waiting for resource {resource_id}")
    
    def _clear_process_waiting(self):
        """Clear a process from waiting for a resource"""
        process_id = self.waiting_process_var.get()
        resource_id = self.waited_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.remove_waiting_process(resource_id, process_id)
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Process {process_id} no longer waiting for resource {resource_id}"
            )
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} cleared from waiting for resource {resource_id}")
    
    def _detect_deadlocks(self):
        """Run deadlock detection algorithm"""
        deadlocks = self.deadlock_detector.detect_deadlocks()
        if deadlocks:
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Detected {len(deadlocks)} deadlock cycle(s)"
            )
            self.status_bar.config(text=f"Detected {len(deadlocks)} deadlock cycle(s)")
        else:
            self.status_bar.config(text="No deadlocks detected")
            
        self._update_deadlock_ui()
    
    def _clear_deadlock_data(self):
        """Clear all deadlock detection data"""
        self.deadlock_detector.clear_all()
        self.deadlock_detector.add_log_entry("deadlock_detector", "All data cleared")
        
        # Reset deadlock simulation state
        if self.deadlock_simulation_active:
            self.deadlock_simulation_active = False
            if self.deadlock_sim_button:
                self.deadlock_sim_button.configure(text="Simulate Deadlock")
                
        self._update_deadlock_ui()
        self.status_bar.config(text="Deadlock detection data cleared")
    
    def _toggle_auto_analyze(self):
        """Toggle automatic deadlock analysis"""
        self.auto_analyze_active = self.auto_analyze_var.get()
        action = "enabled" if self.auto_analyze_active else "disabled"
        self.status_bar.config(text=f"Auto-analysis {action}")
    
    def _update_deadlock_ui(self):
        """Update the deadlock detection UI elements"""
        # Check if UI elements have been initialized
        if not all([self.deadlock_status, self.deadlock_status_text, self.deadlock_canvas, 
                  self.process_dropdown, self.resource_dropdown]):
            # UI not yet fully initialized, skip update
            return
            
        # Get current resources and processes
        resources = self.deadlock_detector.get_resource_status()
        processes = self.deadlock_detector.get_process_status()
        
        # Apply process filtering if active
        if self.filtered_processes is not None:
            # Filter processes based on filter criteria
            filtered_processes = {p_id: p_info for p_id, p_info in processes.items() 
                                if p_id in self.filtered_processes}
            processes = filtered_processes
        
        # Update dropdowns
        process_list = list(processes.keys())
        self.process_dropdown['values'] = process_list
        self.request_process_dropdown['values'] = process_list
        self.resource_dropdown['values'] = list(resources.keys())
        
        # Check for deadlocks
        deadlocks = self.deadlock_detector.detect_deadlocks()
        
        # Run auto-analysis if enabled
        if self.auto_analyze_active and deadlocks:
            self._analyze_deadlocks()
        
        if deadlocks:
            self.deadlock_status.config(text=f"Deadlock detected: {len(deadlocks)} cycle(s)", style="Error.TLabel")
        else:
            self.deadlock_status.config(text="No deadlocks detected", style="Success.TLabel")
        
        # Update status text
        self.deadlock_status_text.config(state=tk.NORMAL)
        self.deadlock_status_text.delete(1.0, tk.END)
        
        status_text = "RESOURCES:\n"
        for r_id, r_info in resources.items():
            status_text += f"{r_id}: {r_info['state']} "
            status_text += f"(Total: {r_info.get('total_instances', 1)}, "
            status_text += f"Available: {r_info.get('available_instances', 0)}, "
            
            allocations = r_info.get('allocations', {})
            if allocations:
                alloc_str = ", ".join([f"{p}:{amt}" for p, amt in allocations.items()])
                status_text += f"Allocated: {{{alloc_str}}}, "
            
            waiters_count = len(r_info.get('waiters', []))
            status_text += f"Waiters: {waiters_count})\n"
        
        status_text += "\nPROCESSES:\n"
        for p_id, p_info in processes.items():
            # Format the owned resources with allocation counts
            owns_formatted = []
            for r_id in p_info['owns']:
                if r_id in resources and p_id in resources[r_id].get('allocations', {}):
                    allocation = resources[r_id]['allocations'][p_id]
                    owns_formatted.append(f"{r_id}:{allocation}")
                else:
                    owns_formatted.append(r_id)
            
            status_text += f"{p_id}: Owns {{{', '.join(owns_formatted) if owns_formatted else 'None'}}}, "
            
            # Show waiting information with requested amount
            waiting_for = p_info['waiting_for']
            if waiting_for and waiting_for in resources and p_id in resources[waiting_for].get('waiting_for', {}):
                requested = resources[waiting_for]['waiting_for'][p_id]
                status_text += f"Waiting for: {waiting_for} ({requested} units)\n"
            else:
                status_text += f"Waiting for: {waiting_for or 'None'}\n"
        
        if deadlocks:
            status_text += "\nDEADLOCKS DETECTED:\n"
            for cycle in deadlocks:
                status_text += f"Deadlock cycle: {' -> '.join(cycle)}\n"
        
        self.deadlock_status_text.insert(tk.END, status_text)
        self.deadlock_status_text.config(state=tk.DISABLED)
        
        # Only update the visualization if needed
        if self.canvas_needs_update:
            self._update_deadlock_visualization(resources, processes, deadlocks)
        else:
            # Reset the flag for next update
            self.canvas_needs_update = True
            
    def _update_deadlock_visualization(self, resources, processes, deadlocks):
        """Update the visualization for deadlock detection"""
        self.deadlock_canvas.delete("all")
        
        width = self.deadlock_canvas.winfo_width()
        height = self.deadlock_canvas.winfo_height()
        
        # Adjust the scrolling region based on graph size
        graph_width = max(1000, width * 2)
        graph_height = max(1000, height * 2)
        self.deadlock_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))
        
        # Avoid drawing if canvas size is not yet determined
        if width < 10 or height < 10:
            return
        
        # Calculate positions for resources and processes
        process_nodes = {}
        resource_nodes = {}
        self.process_node_ids = {}  # Store canvas IDs for processes
        self.resource_node_ids = {}  # Store canvas IDs for resources
        
        process_count = len(processes)
        resource_count = len(resources)
        
        if process_count == 0 or resource_count == 0:
            # Nothing to draw
            return
        
        # Create layout for larger graphs
        if process_count > 10 or resource_count > 10:
            # Use a circle layout for larger graphs
            center_x = graph_width / 2
            center_y = graph_height / 2
            process_radius = min(graph_width, graph_height) * 0.3
            resource_radius = min(graph_width, graph_height) * 0.6
            
            # Position processes in inner circle
            for i, p_id in enumerate(processes):
                angle = 2 * 3.14159 * i / process_count
                x = center_x + process_radius * math.cos(angle)
                y = center_y + process_radius * math.sin(angle)
                process_nodes[p_id] = (x, y)
            
            # Position resources in outer circle
            for i, r_id in enumerate(resources):
                angle = 2 * 3.14159 * i / resource_count
                x = center_x + resource_radius * math.cos(angle)
                y = center_y + resource_radius * math.sin(angle)
                resource_nodes[r_id] = (x, y)
        else:
            # Use the grid layout for smaller graphs
            # Arrange processes at the top
            process_spacing = width / (process_count + 1)
            for i, p_id in enumerate(processes):
                process_nodes[p_id] = (process_spacing * (i + 1), height * 0.25)
            
            # Arrange resources at the bottom
            resource_spacing = width / (resource_count + 1)
            for i, r_id in enumerate(resources):
                resource_nodes[r_id] = (resource_spacing * (i + 1), height * 0.75)
        
        # Draw nodes
        radius = 20
        
        # Find processes in deadlocks for highlighting
        deadlocked_processes = set()
        for cycle in deadlocks:
            deadlocked_processes.update(cycle)
        
        # Draw resource nodes (rectangles)
        for r_id, (x, y) in resource_nodes.items():
            resource = resources[r_id]
            
            # Color based on state
            if resource['state'] == 'owned':
                fill_color = "green"
            elif resource['state'] == 'free':
                fill_color = "lightgray"
            else:
                fill_color = "orange"
                
            # Highlight resources involved in deadlocks
            outline_width = 2
            for cycle in deadlocks:
                for p_id in cycle:
                    if p_id in processes and processes[p_id]['waiting_for'] == r_id:
                        fill_color = "orange"
                        outline_width = 3
                        break
                else:
                    continue
                break
            
            # Draw rectangle for resource
            rect_id = self.deadlock_canvas.create_rectangle(
                x-radius, y-radius, x+radius, y+radius,
                fill=fill_color, outline="black", width=outline_width,
                tags=(f"resource:{r_id}", "resource")
            )
            self.resource_node_ids[r_id] = rect_id
            
            text_id = self.deadlock_canvas.create_text(
                x, y, text=r_id, tags=(f"resource_label:{r_id}", "resource_label")
            )
            
            # Add tooltip and click behavior
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Enter>", 
                                        lambda e, rid=r_id: self._show_resource_tooltip(e, rid))
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Leave>", self._hide_tooltip)
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Button-1>", 
                                        lambda e, rid=r_id: self._select_resource(rid))
        
        # Draw process nodes (circles)
        for p_id, (x, y) in process_nodes.items():
            process = processes[p_id]
            
            # Color based on state
            if p_id in deadlocked_processes:
                fill_color = "red"
                outline_width = 3
            elif process['waiting_for'] is None:
                fill_color = "lightblue"
                outline_width = 2
            else:
                fill_color = "yellow"
                outline_width = 2
            
            # Draw circle for process
            circle_id = self.deadlock_canvas.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                fill=fill_color, outline="black", width=outline_width,
                tags=(f"process:{p_id}", "process")
            )
            self.process_node_ids[p_id] = circle_id
            
            text_id = self.deadlock_canvas.create_text(
                x, y, text=p_id, tags=(f"process_label:{p_id}", "process_label")
            )
            
            # Add tooltip and click behavior
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Enter>", 
                                        lambda e, pid=p_id: self._show_process_tooltip(e, pid))
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Leave>", self._hide_tooltip)
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Button-1>", 
                                        lambda e, pid=p_id: self._select_process(pid))
        
        # Draw edges for ownership (process to resource)
        for p_id, p_info in processes.items():
            if p_id in process_nodes:
                px, py = process_nodes[p_id]
                
                # Draw edges for owned resources
                for r_id in p_info['owns']:
                    if r_id in resource_nodes:
                        rx, ry = resource_nodes[r_id]
                        line_id = self.deadlock_canvas.create_line(
                            px, py+radius, rx, ry-radius,
                            arrow=tk.LAST, width=2, fill="black",
                            tags=(f"owns_edge:{p_id}:{r_id}", "edge")
                        )
        
        # Draw edges for waiting processes (process to resource)
        for p_id, p_info in processes.items():
            if p_id in process_nodes and p_info['waiting_for']:
                px, py = process_nodes[p_id]
                r_id = p_info['waiting_for']
                
                if r_id in resource_nodes:
                    rx, ry = resource_nodes[r_id]
                    # Determine if this edge is part of a deadlock
                    is_deadlocked = p_id in deadlocked_processes
                    
                    # Dashed line for waiting relationship
                    line_id = self.deadlock_canvas.create_line(
                        px, py+radius, rx, ry-radius,
                        dash=(4, 4), arrow=tk.LAST, width=2,
                        fill="red" if is_deadlocked else "gray",
                        tags=(f"waits_edge:{p_id}:{r_id}", "edge")
                    )
        
        # Highlight deadlock cycles
        for i, cycle in enumerate(deadlocks):
            # Create a semi-transparent overlay to highlight the deadlock cycle
            cycle_nodes = []
            for p_id in cycle:
                if p_id in process_nodes:
                    cycle_nodes.append(process_nodes[p_id])
            
            if cycle_nodes:
                # Create highlight path around the cycle
                for j in range(len(cycle_nodes)):
                    x1, y1 = cycle_nodes[j]
                    x2, y2 = cycle_nodes[(j + 1) % len(cycle_nodes)]
                    
                    self.deadlock_canvas.create_line(
                        x1, y1, x2, y2,
                        width=3, fill="red", dash=(8, 4),
                        tags=(f"cycle:{i}", "cycle_highlight"),
                        state=tk.DISABLED  # This line is just for visualization
                    )
                
                # Add cycle label
                center_x = sum(x for x, y in cycle_nodes) / len(cycle_nodes)
                center_y = sum(y for x, y in cycle_nodes) / len(cycle_nodes)
                self.deadlock_canvas.create_text(
                    center_x, center_y - 40,
                    text=f"Deadlock #{i+1}",
                    font=("Arial", 10, "bold"), fill="red",
                    tags=(f"cycle_label:{i}", "cycle_label")
                )
    
    def _apply_process_filter(self):
        """Filter the processes shown in the deadlock visualization"""
        filter_text = self.process_filter_var.get()
        if filter_text:
            try:
                processes = self.deadlock_detector.get_process_status()
                self.filtered_processes = [p_id for p_id in processes if filter_text.lower() in p_id.lower()]
                self.status_bar.config(text=f"Filter applied: {len(self.filtered_processes)} processes shown")
                self._update_deadlock_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply filter: {str(e)}")
        else:
            self._clear_process_filter()
    
    def _clear_process_filter(self):
        """Clear the process filter"""
        self.process_filter_var.set("")
        self.filtered_processes = None
        self.status_bar.config(text="Process filter cleared")
        self._update_deadlock_ui()
    
    def _analyze_deadlocks(self):
        """Perform detailed analysis on detected deadlocks"""
        # Check if UI elements have been initialized
        if not self.deadlock_suggestion_text:
            return
            
        deadlocks = self.deadlock_detector.detect_deadlocks()
        resources = self.deadlock_detector.get_resource_status()
        processes = self.deadlock_detector.get_process_status()
        
        self.deadlock_suggestion_text.config(state=tk.NORMAL)
        self.deadlock_suggestion_text.delete(1.0, tk.END)
        
        if not deadlocks:
            self.deadlock_suggestion_text.insert(tk.END, "No deadlocks detected. System is operating normally.\n\nThis means all resource requests can be satisfied without creating circular waits.")
        else:
            # Create detailed analysis and suggestions
            suggestions = []
            for cycle_idx, cycle in enumerate(deadlocks):
                cycle_str = " → ".join(cycle)
                suggestions.append(f"Deadlock #{cycle_idx+1}: {cycle_str}\n")
                
                # Find the resources involved
                deadlocked_resources = []
                resource_details = []
                
                for p_id in cycle:
                    if p_id in processes and processes[p_id]['waiting_for']:
                        wait_res = processes[p_id]['waiting_for']
                        deadlocked_resources.append(wait_res)
                        
                        # Get detailed allocation info
                        if wait_res in resources:
                            r_info = resources[wait_res]
                            avail = r_info.get('available_instances', 0)
                            total = r_info.get('total_instances', 1)
                            allocations = r_info.get('allocations', {})
                            alloc_info = ", ".join([f"{pid}:{amt}" for pid, amt in allocations.items()])
                            resource_details.append(f"  - {wait_res}: {avail}/{total} available, allocations: {{{alloc_info}}}")
                
                if resource_details:
                    suggestions.append("Resource allocation state:\n")
                    suggestions.extend([rd + "\n" for rd in resource_details])
                    suggestions.append("\n")
                
                # Generate suggestions
                if deadlocked_resources:
                    suggestions.append("Potential resolutions:\n")
                    
                    # Suggestion 1: Release a resource
                    for i, p_id in enumerate(cycle):
                        if p_id in processes:
                            wait_res = processes[p_id]['waiting_for']
                            if wait_res:
                                allocations = resources.get(wait_res, {}).get('allocations', {})
                                if allocations:
                                    owner_info = ", ".join([f"{pid} (holds {amt})" for pid, amt in allocations.items()])
                                    suggestions.append(f"1. Release '{wait_res}' held by {owner_info}\n")
                                    break
                    
                    # Suggestion 2: Terminate a process
                    suggestions.append(f"2. Terminate one process in the cycle (e.g., '{cycle[0]}')\n")
                    
                    # Suggestion 3: Priority-based resource allocation
                    suggestions.append(f"3. Implement priority-based allocation for resources: {', '.join(deadlocked_resources)}\n")
                    
                    # Banker's Algorithm explanation
                    suggestions.append("\nThis deadlock could have been prevented using the Banker's Algorithm, which ensures that resources are allocated only when it's safe to do so (i.e., when there's a sequence that allows all processes to complete).\n")
            
            self.deadlock_suggestion_text.insert(tk.END, "".join(suggestions))
        
        self.deadlock_suggestion_text.config(state=tk.DISABLED)
        self.status_bar.config(text="Deadlock analysis complete - see suggestions for resolution options")
    
    def _toggle_auto_analysis(self):
        """Toggle automatic deadlock analysis"""
        self.auto_analyze_active = self.auto_analyze_var.get()
        if self.auto_analyze_active:
            self.status_bar.config(text="Auto-analysis activated")
        else:
            self.status_bar.config(text="Auto-analysis deactivated")
    
    def _on_closing(self):
        """Handle application close"""
        # Stop all monitoring threads
        self.pipe_debugger.stop_monitoring()
        self.queue_debugger.stop_monitoring()
        self.shared_mem_debugger.stop_monitoring()
        self.deadlock_detector.stop_monitoring()
        
        # Stop simulations if active
        if self.simulation_active:
            self._stop_simulation()
            
        if self.deadlock_simulation_active:
            self.deadlock_simulation_active = False
        
        # Close the application
        self.root.destroy()
    
    def _cleanup_resources(self):
        """Periodically clean up inactive resources"""
        try:
            # Clean up resources in each debugger
            pipes_removed = self.pipe_debugger.cleanup_inactive_pipes(timeout=300)  # 5 minutes
            queues_removed = self.queue_debugger.cleanup_inactive_queues(timeout=300)
            shm_removed = self.shared_mem_debugger.cleanup_inactive_memory(timeout=300)
            
            if pipes_removed > 0 or queues_removed > 0 or shm_removed > 0:
                self.status_bar.config(text=f"Cleaned up inactive resources: {pipes_removed} pipes, {queues_removed} queues, {shm_removed} shared memory segments")
            
            # Schedule next cleanup
            self.root.after(600000, self._cleanup_resources)  # Run every 10 minutes
        except Exception as e:
            # Log the error but don't crash
            print(f"Error during resource cleanup: {e}")
            # Ensure the cleanup continues on schedule despite errors
            self.root.after(600000, self._cleanup_resources) 

    def _zoom_in_deadlock(self):
        """Zoom in on the deadlock visualization"""
        if not self.deadlock_canvas:
            return
            
        self.deadlock_canvas_scale *= 1.2
        # Get the canvas dimensions
        canvas_width = self.deadlock_canvas.winfo_width()
        canvas_height = self.deadlock_canvas.winfo_height()
        
        # Calculate the center point of the canvas
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Scale from the center
        self.deadlock_canvas.scale("all", center_x, center_y, 1.2, 1.2)
        
        # Update the status bar
        self.status_bar.config(text=f"Zoom level: {self.deadlock_canvas_scale:.1f}x")
        
        # Save the canvas state to prevent auto-refresh from resetting it
        self.canvas_needs_update = False
    
    def _zoom_out_deadlock(self):
        """Zoom out on the deadlock visualization"""
        if not self.deadlock_canvas:
            return
            
        self.deadlock_canvas_scale /= 1.2
        # Get the canvas dimensions
        canvas_width = self.deadlock_canvas.winfo_width()
        canvas_height = self.deadlock_canvas.winfo_height()
        
        # Calculate the center point of the canvas
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Scale from the center
        self.deadlock_canvas.scale("all", center_x, center_y, 0.8, 0.8)
        
        # Update the status bar
        self.status_bar.config(text=f"Zoom level: {self.deadlock_canvas_scale:.1f}x")
        
        # Save the canvas state to prevent auto-refresh from resetting it
        self.canvas_needs_update = False
    
    def _reset_deadlock_view(self):
        """Reset the deadlock visualization"""
        if not self.deadlock_canvas:
            return
            
        # Store the current scale to calculate the reset factor
        reset_factor = 1.0 / self.deadlock_canvas_scale
        
        # Get the canvas dimensions
        canvas_width = self.deadlock_canvas.winfo_width()
        canvas_height = self.deadlock_canvas.winfo_height()
        
        # Calculate the center point of the canvas
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Reset scale from the center
        self.deadlock_canvas.scale("all", center_x, center_y, reset_factor, reset_factor)
        
        # Reset the scale factor
        self.deadlock_canvas_scale = 1.0
        
        # Force a full redraw
        self.canvas_needs_update = True
        self._update_deadlock_ui()
        
        # Update the status bar
        self.status_bar.config(text="Zoom reset to 1.0x")
    
    def _deadlock_canvas_click(self, event):
        """Handle click on the deadlock visualization"""
        self.deadlock_canvas_drag_start = (event.x, event.y)
        self.deadlock_canvas_clicked_item = self.deadlock_canvas.find_closest(event.x, event.y)
    
    def _deadlock_canvas_drag(self, event):
        """Handle drag on the deadlock visualization"""
        if self.deadlock_canvas_drag_start:
            dx = event.x - self.deadlock_canvas_drag_start[0]
            dy = event.y - self.deadlock_canvas_drag_start[1]
            self.deadlock_canvas.move("all", dx, dy)
            self.deadlock_canvas_drag_start = (event.x, event.y)
    
    def _deadlock_canvas_zoom(self, event):
        """Handle zoom on the deadlock visualization"""
        # Get zoom direction from event (platform-specific)
        if event.delta:
            # Windows/macOS
            zoom_in = event.delta > 0
        elif event.num == 4:
            # Linux scroll up
            zoom_in = True
        elif event.num == 5:
            # Linux scroll down
            zoom_in = False
        else:
            return
        
        # Set zoom factor
        factor = 1.1 if zoom_in else 0.9
        
        # Get canvas coordinates for the mouse position
        x = self.deadlock_canvas.canvasx(event.x)
        y = self.deadlock_canvas.canvasy(event.y)
        
        # Update scale factor
        self.deadlock_canvas_scale *= factor
        
        # Apply zoom centered on mouse position
        self.deadlock_canvas.scale("all", x, y, factor, factor)
        
        # Update the status bar
        self.status_bar.config(text=f"Zoom level: {self.deadlock_canvas_scale:.1f}x")
    
    def _show_process_tooltip(self, event, process_id):
        """Show tooltip for a process node"""
        processes = self.deadlock_detector.get_process_status()
        if process_id not in processes:
            return
        
        process = processes[process_id]
        owned_resources = ", ".join(process['owns']) if process['owns'] else "None"
        waiting_for = process['waiting_for'] if process['waiting_for'] else "None"
        
        tooltip_text = f"Process: {process_id}\nOwns: {owned_resources}\nWaiting for: {waiting_for}"
        
        self._show_tooltip(event, tooltip_text)
    
    def _show_resource_tooltip(self, event, resource_id):
        """Show tooltip for a resource node"""
        resources = self.deadlock_detector.get_resource_status()
        if resource_id not in resources:
            return
        
        resource = resources[resource_id]
        total_instances = resource.get('total_instances', 1)
        available = resource.get('available_instances', 0)
        
        # Get allocation information
        allocations = resource.get('allocations', {})
        if allocations:
            alloc_str = ", ".join([f"{pid}:{amt}" for pid, amt in allocations.items()])
        else:
            alloc_str = "None"
            
        waiters = ", ".join(resource.get('waiters', [])) if resource.get('waiters', []) else "None"
        
        tooltip_text = f"Resource: {resource_id}\n"
        tooltip_text += f"State: {resource['state']}\n"
        tooltip_text += f"Total instances: {total_instances}\n"
        tooltip_text += f"Available: {available}\n"
        tooltip_text += f"Allocations: {alloc_str}\n"
        tooltip_text += f"Waiters: {waiters}"
        
        self._show_tooltip(event, tooltip_text)
    
    def _show_tooltip(self, event, text):
        """Display a tooltip at the cursor position"""
        x, y = event.x + 20, event.y + 10
        
        # Destroy any existing tooltip
        self._hide_tooltip()
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        
        # Position near the cursor
        self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        # Create label with tooltip text
        label = tk.Label(self.tooltip, text=text, justify=tk.LEFT,
                         background="#FFFFCC", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9))
        label.pack()
    
    def _hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def _select_process(self, process_id):
        """Handle selection of a process in the visualization"""
        # Update the process dropdown
        self.selected_process_var.set(process_id)
        
        # Highlight the selected process
        self._highlight_selected_node("process", process_id)
        
        # Show detailed information in the status bar
        processes = self.deadlock_detector.get_process_status()
        if process_id in processes:
            process = processes[process_id]
            owned_resources = ", ".join(process['owns']) if process['owns'] else "None"
            waiting_for = process['waiting_for'] if process['waiting_for'] else "None"
            self.status_bar.config(text=f"Selected process: {process_id} | Owns: {owned_resources} | Waiting for: {waiting_for}")
    
    def _select_resource(self, resource_id):
        """Handle selection of a resource in the visualization"""
        # Update the resource dropdown
        self.selected_resource_var.set(resource_id)
        
        # Highlight the selected resource
        self._highlight_selected_node("resource", resource_id)
        
        # Show detailed information in the status bar
        resources = self.deadlock_detector.get_resource_status()
        if resource_id in resources:
            resource = resources[resource_id]
            owner = resource['owner'] if resource['owner'] else "None"
            waiters = ", ".join(resource['waiters']) if resource['waiters'] else "None"
            self.status_bar.config(text=f"Selected resource: {resource_id} | State: {resource['state']} | Owner: {owner} | Waiters: {waiters}")
    
    def _highlight_selected_node(self, node_type, node_id):
        """Highlight the selected node and its relationships"""
        # Reset all highlights
        self.deadlock_canvas.itemconfig("process", width=2)
        self.deadlock_canvas.itemconfig("resource", width=2)
        self.deadlock_canvas.itemconfig("edge", width=2)
        
        if node_type == "process":
            # Highlight this process
            self.deadlock_canvas.itemconfig(f"process:{node_id}", width=4)
            
            # Highlight all owned resources and connecting edges
            processes = self.deadlock_detector.get_process_status()
            if node_id in processes:
                process = processes[node_id]
                
                # Highlight resources owned by this process
                for r_id in process['owns']:
                    self.deadlock_canvas.itemconfig(f"resource:{r_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"owns_edge:{node_id}:{r_id}", width=4)
                
                # Highlight resource this process is waiting for
                if process['waiting_for']:
                    r_id = process['waiting_for']
                    self.deadlock_canvas.itemconfig(f"resource:{r_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"waits_edge:{node_id}:{r_id}", width=4)
        
        elif node_type == "resource":
            # Highlight this resource
            self.deadlock_canvas.itemconfig(f"resource:{node_id}", width=4)
            
            # Highlight owner and waiting processes
            resources = self.deadlock_detector.get_resource_status()
            if node_id in resources:
                resource = resources[node_id]
                
                # Highlight owner
                if resource['owner']:
                    p_id = resource['owner']
                    self.deadlock_canvas.itemconfig(f"process:{p_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"owns_edge:{p_id}:{node_id}", width=4)
                
                # Highlight waiters
                for p_id in resource['waiters']:
                    self.deadlock_canvas.itemconfig(f"process:{p_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"waits_edge:{p_id}:{node_id}", width=4)
    
    def _toggle_simulation(self):
        """Toggle the simulation on/off"""
        if not self.simulation_active:
            # Start simulation
            self.simulation_active = True
            self.sim_button.configure(text="Stop Simulation")
            
            # Clear any previous simulation tasks
            for task_id in self.simulation_tasks:
                self.root.after_cancel(task_id)
            self.simulation_tasks = []
            
            # Start simulation with selected duration
            duration_text = self.sim_duration.get()
            if duration_text == "Continuous":
                # Run indefinitely until stopped
                self.simulate_ipc_activity()
            else:
                # Run for specified duration
                seconds = int(duration_text.rstrip("s"))
                self.simulate_ipc_activity()
                # Schedule automatic stop after duration
                stop_task = self.root.after(seconds * 1000, self._stop_simulation)
                self.simulation_tasks.append(stop_task)
                
        else:
            # Stop simulation
            self._stop_simulation()
    
    def _stop_simulation(self):
        """Stop the ongoing simulation"""
        self.simulation_active = False
        self.sim_button.configure(text="Run Demo Simulation")
        
        # Cancel any pending simulation tasks
        for task_id in self.simulation_tasks:
            self.root.after_cancel(task_id)
        self.simulation_tasks = []
        
        # Check if processes/resources were created during simulation
        process_count = len(self.deadlock_detector.processes)
        resource_count = len(self.deadlock_detector.resources)
        
        if process_count > 0 or resource_count > 0:
            # Ask user if they want to clean up
            if messagebox.askyesno("Clean Up Simulation", 
                                  f"Clear {process_count} processes and {resource_count} resources?"):
                self._clear_deadlock_data()
                self._update_status("Simulation stopped and data cleared")
            else:
                self._update_status("Simulation stopped (data preserved)")
        else:
            # Update status to show simulation stopped
            self._update_status("Simulation stopped")
    
    def simulate_ipc_activity(self):
        """Simulate IPC activity for demo purposes"""
        if not self.simulation_active:
            return
            
        # Get simulation speed factor (1-10)
        speed_factor = self.sim_speed_var.get()
            
        # Calculate how many events to create based on speed
        # At higher speeds, we'll generate more events but update UI less frequently
        events_per_cycle = min(speed_factor, 5)  # Cap at 5 to prevent overload
        
        # Determine probability of each event type based on speed
        # At higher speeds, we'll generate fewer unique events to reduce load
        create_probability = max(0.1, 0.3 - (speed_factor * 0.02))  # Decreases with speed
        delete_probability = min(0.4, 0.1 + (speed_factor * 0.03))  # Increases with speed
        
        # Batch changes to reduce UI updates
        actions_taken = 0
        
        # Run multiple events based on speed factor
        for _ in range(events_per_cycle):
            # Pipes simulation
            if random.random() < 0.3:
                pipe_id = f"pipe_{random.randint(1, 5)}"
                writer_pid = random.randint(1000, 9999)
                reader_pid = random.randint(1000, 9999)
                
                if random.random() < 0.6:  # Create or use pipe
                    if random.random() < create_probability:
                        # Check if pipe exists in active_pipes
                        if pipe_id not in self.pipe_debugger.active_pipes:
                            self.pipe_debugger.register_pipe(pipe_id)
                            self._log_event(f"Created pipe {pipe_id}")
                            actions_taken += 1
                    
                    if pipe_id in self.pipe_debugger.active_pipes:
                        # Update pipe status with PIDs
                        self.pipe_debugger.update_pipe_status(pipe_id, {
                            'writer_pid': f"process_{writer_pid}",
                            'reader_pid': f"process_{reader_pid}"
                        })
                        
                        # Simulate data transfer
                        bytes_sent = random.randint(10, 1000)
                        self.pipe_debugger.update_pipe_status(pipe_id, {
                            'status': 'transferring',
                            'bytes_transferred': bytes_sent,
                            'progress': random.randint(0, 100)
                        })
                        self._log_event(f"Transferred {bytes_sent} bytes through {pipe_id} from PID {writer_pid} to {reader_pid}")
                        actions_taken += 1
                else:  # Delete pipe
                    if pipe_id in self.pipe_debugger.active_pipes and random.random() < delete_probability:
                        self.pipe_debugger.unregister_pipe(pipe_id)
                        self._log_event(f"Deleted pipe {pipe_id}")
                        actions_taken += 1
            
            # Message queues simulation
            if random.random() < 0.3:
                queue_id = f"queue_{random.randint(1, 3)}"
                sender_pid = random.randint(1000, 9999)
                receiver_pid = random.randint(1000, 9999)
                
                if random.random() < 0.7:  # Create or use queue
                    if random.random() < 0.2:
                        # Check if queue exists in active_queues
                        if queue_id not in self.queue_debugger.active_queues:
                            self.queue_debugger.register_queue(queue_id, random.randint(5, 20))
                            self._log_event(f"Created message queue {queue_id}")
                    
                    if queue_id in self.queue_debugger.active_queues:
                        # Update queue status with PIDs
                        self.queue_debugger.update_queue_status(queue_id, {
                            'producer_pid': f"process_{sender_pid}",
                            'consumer_pid': f"process_{receiver_pid}"
                        })
                        
                        if random.random() < 0.7:  # Enqueue
                            queue_info = self.queue_debugger.active_queues[queue_id]
                            if queue_info['message_count'] < queue_info['capacity']:
                                msg_size = random.randint(10, 100)
                                self.queue_debugger.enqueue_message(queue_id, f"Message-{msg_size}")
                                self._log_event(f"Enqueued message to {queue_id} from PID {sender_pid}")
                            else:  # Dequeue
                                queue_info = self.queue_debugger.active_queues[queue_id]
                                if queue_info['message_count'] > 0:
                                    self.queue_debugger.dequeue_message(queue_id)
                                    self._log_event(f"Dequeued message from {queue_id} by PID {receiver_pid}")
                else:  # Delete queue
                    if queue_id in self.queue_debugger.active_queues and random.random() < 0.1:
                        self.queue_debugger.unregister_queue(queue_id)
                        self._log_event(f"Deleted message queue {queue_id}")
            
            # Shared memory simulation
            if random.random() < 0.3:
                segment_id = f"shm_{random.randint(1, 3)}"
                process_id = f"process_{random.randint(1000, 9999)}"
                
                if random.random() < 0.8:  # Create or use shared memory
                    if random.random() < 0.2:
                        # Check if segment exists
                        if segment_id not in self.shared_mem_debugger.shared_memories:
                            size = random.randint(1, 10) * 1024  # 1-10 KB
                            self.shared_mem_debugger.register_memory_segment(segment_id, size)
                            self._log_event(f"Created shared memory segment {segment_id} with size {size} bytes")
                    
                    if segment_id in self.shared_mem_debugger.shared_memories:
                        # Access shared memory
                        memory_info = self.shared_mem_debugger.shared_memories[segment_id]
                        offset = random.randint(0, memory_info['size'] - 100)  # Ensure we don't go out of bounds
                        
                        if random.random() < 0.5:  # Read
                            size_to_read = min(10, memory_info['size'] - offset)
                            self.shared_mem_debugger.read_from_memory(segment_id, offset, size_to_read, process_id)
                            self._log_event(f"Process {process_id} read from shared memory {segment_id} at offset {offset}")
                            
                            # Update status for visualization
                            self.shared_mem_debugger.update_memory_status(segment_id, {
                                'access_count': memory_info['access_count'] + 1,
                                'last_activity': time.time()
                            })
                        else:  # Write
                            data = f"Data-{random.randint(100, 999)}"
                            self.shared_mem_debugger.write_to_memory(segment_id, offset, data, process_id)
                            self._log_event(f"Process {process_id} wrote to shared memory {segment_id} at offset {offset}")
                            
                            # Update status for visualization
                            self.shared_mem_debugger.update_memory_status(segment_id, {
                                'access_count': memory_info['access_count'] + 1,
                                'last_activity': time.time(),
                                'last_writer': process_id
                            })
                        
                        # Lock/unlock
                        if random.random() < 0.2:
                            region_start = offset
                            region_end = offset + 50
                            
                            if random.random() < 0.5:  # Lock
                                # Check if not locked
                                region_locked = False
                                for (start, end), lock_info in memory_info['locks'].items():
                                    if region_start <= end and region_end >= start:
                                        region_locked = True
                                        break
                                        
                                if not region_locked:
                                    self.shared_mem_debugger.lock_region(segment_id, region_start, region_end, process_id)
                                    self._log_event(f"Process {process_id} locked shared memory {segment_id} region {region_start}-{region_end}")
                            else:  # Unlock
                                for (start, end), lock_info in list(memory_info['locks'].items()):
                                    if lock_info['owner'] == process_id:
                                        self.shared_mem_debugger.unlock_region(segment_id, start, end, process_id)
                                        self._log_event(f"Process {process_id} unlocked shared memory {segment_id} region {start}-{end}")
                                        break
                else:  # Delete shared memory
                    if segment_id in self.shared_mem_debugger.shared_memories and random.random() < 0.1:
                        self.shared_mem_debugger.unregister_shared_memory(segment_id)
                        self._log_event(f"Deleted shared memory segment {segment_id}")
            
            # Deadlock simulation
            if random.random() < 0.2:
                process_name = f"P{random.randint(1, 5)}"
                resource_name = f"R{random.randint(1, 5)}"
                
                if random.random() < 0.3:
                    # Register process or resource
                    if random.random() < 0.5:
                        if process_name not in self.deadlock_detector.processes:
                            self.deadlock_detector.register_process(process_name)
                            self._log_event(f"Registered process {process_name}")
                    else:
                        if resource_name not in self.deadlock_detector.resources:
                            self.deadlock_detector.register_resource(resource_name)
                            self._log_event(f"Registered resource {resource_name}")
                else:
                    # Resource allocation
                    if process_name in self.deadlock_detector.processes and resource_name in self.deadlock_detector.resources:
                        if random.random() < 0.7:  # Request
                            result = self.deadlock_detector.request_resource(process_name, resource_name)
                            if result:
                                self._log_event(f"Process {process_name} acquired resource {resource_name}")
                            else:
                                self._log_event(f"Process {process_name} waiting for resource {resource_name}")
                        else:  # Release
                            # Check if the process owns the resource
                            if resource_name in self.deadlock_detector.processes[process_name]['owns']:
                                self.deadlock_detector.release_resource(process_name, resource_name)
                                self._log_event(f"Process {process_name} released resource {resource_name}")
            
            # Update system metrics
            if actions_taken > 0 and actions_taken % 5 == 0:  # Only update metrics periodically
                self._update_system_metrics()
        
        # Schedule next update based on speed (faster speed = shorter delay)
        # Calculate delay in ms - higher speed means shorter delay
        # At higher speeds, we do more work per cycle but wait longer between cycles
        if speed_factor <= 5:
            delay = max(100, int(500 / speed_factor))  # Normal speed range
        else:
            # For very high speeds, increase the number of events per cycle
            # but keep a minimum delay to prevent UI freezing
            delay = max(100, int(200))  # Min 100ms, max 200ms delay
            
        task_id = self.root.after(delay, self.simulate_ipc_activity)
        self.simulation_tasks.append(task_id)
    
    # ------ UI Update Methods ------
    
    def _update_pipe_ui(self):
        """Update pipe UI elements"""
        # Get pipe status and update dropdown
        pipe_status = self.pipe_debugger.get_pipe_status()
        self.pipe_dropdown['values'] = list(pipe_status.keys())
        
        # Update status text
        self.pipe_status_text.config(state=tk.NORMAL)
        self.pipe_status_text.delete(1.0, tk.END)
        
        if not pipe_status:
            self.pipe_status_text.insert(tk.END, "No active pipes")
        else:
            status_text = "ACTIVE PIPES:\n\n"
            for pipe_id, pipe_info in pipe_status.items():
                status_text += f"Pipe ID: {pipe_id}\n"
                status_text += f"Status: {pipe_info.get('status', 'unknown')}\n"
                status_text += f"Writer PID: {pipe_info.get('writer_pid', 'None')}\n"
                status_text += f"Reader PID: {pipe_info.get('reader_pid', 'None')}\n"
                
                if pipe_info.get('status') == 'transferring':
                    status_text += f"Progress: {pipe_info.get('progress', 0)}%\n"
                    status_text += f"Bytes transferred: {pipe_info.get('bytes_transferred', 0)}\n"
                elif pipe_info.get('status') == 'bottleneck':
                    status_text += "WARNING: Bottleneck detected!\n"
                
                status_text += "\n"
            
            self.pipe_status_text.insert(tk.END, status_text)
        
        self.pipe_status_text.config(state=tk.DISABLED)
    
    def _update_queue_ui(self):
        """Update message queue UI elements"""
        # Get queue status and update dropdown
        queue_status = self.queue_debugger.get_queue_status()
        self.queue_dropdown['values'] = list(queue_status.keys())
        
        # Update status text
        self.queue_status_text.config(state=tk.NORMAL)
        self.queue_status_text.delete(1.0, tk.END)
        
        if not queue_status:
            self.queue_status_text.insert(tk.END, "No active message queues")
        else:
            status_text = "ACTIVE MESSAGE QUEUES:\n\n"
            for queue_id, queue_info in queue_status.items():
                status_text += f"Queue ID: {queue_id}\n"
                status_text += f"Status: {queue_info.get('status', 'unknown')}\n"
                status_text += f"Messages: {queue_info.get('message_count', 0)}/{queue_info.get('capacity', 'unknown')}\n"
                status_text += f"Producer PID: {queue_info.get('producer_pid', 'None')}\n"
                status_text += f"Consumer PID: {queue_info.get('consumer_pid', 'None')}\n"
                
                # Add warning for full queues
                if queue_info.get('message_count', 0) >= queue_info.get('capacity', 0):
                    status_text += "WARNING: Queue is full!\n"
                
                status_text += "\n"
            
            self.queue_status_text.insert(tk.END, status_text)
        
        self.queue_status_text.config(state=tk.DISABLED)
    
    def _update_shm_ui(self):
        """Update shared memory UI elements"""
        # Get memory status and update dropdown
        memory_status = self.shared_mem_debugger.get_memory_status()
        self.memory_dropdown['values'] = list(memory_status.keys())
        
        # Update status text
        self.shm_status_text.config(state=tk.NORMAL)
        self.shm_status_text.delete(1.0, tk.END)
        
        if not memory_status:
            self.shm_status_text.insert(tk.END, "No active shared memory segments")
        else:
            status_text = "ACTIVE SHARED MEMORY SEGMENTS:\n\n"
            for memory_id, memory_info in memory_status.items():
                status_text += f"Segment ID: {memory_id}\n"
                status_text += f"Status: {memory_info.get('status', 'unknown')}\n"
                status_text += f"Size: {memory_info.get('size', 0)} bytes\n"
                status_text += f"Access count: {memory_info.get('access_count', 0)}\n"
                status_text += f"Last writer: {memory_info.get('last_writer', 'None')}\n"
                
                # Add locked regions info
                locked_regions = memory_info.get('locked_regions', [])
                if locked_regions:
                    status_text += "Locked regions:\n"
                    for region in locked_regions:
                        status_text += f"  Offset {region.get('offset', 0)}, Size {region.get('size', 0)}"
                        status_text += f" (Owner: {region.get('owner', 'Unknown')})\n"
                
                status_text += "\n"
            
            self.shm_status_text.insert(tk.END, status_text)
        
        self.shm_status_text.config(state=tk.DISABLED)
    
    def _update_log_text(self):
        """Update log text based on current filters and state"""
        if self.log_paused:
            return
            
        # Remember current scroll position before updating
        if hasattr(self, '_log_scroll_position'):
            current_position = self._log_scroll_position
        else:
            current_position = 1.0  # Default to end
            
        # Apply filters based on checkboxes
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        # Get filter settings
        show_pipes = self.show_pipe_logs.get()
        show_queues = self.show_queue_logs.get()
        show_shm = self.show_shm_logs.get()
        show_deadlocks = self.show_deadlock_logs.get()
        
        # Filter entries
        for entry in self.log_entries:
            show_entry = True
            
            # Apply type filters
            if "pipe" in entry.lower() and not show_pipes:
                show_entry = False
            elif "queue" in entry.lower() and not show_queues:
                show_entry = False
            elif "shared memory" in entry.lower() and not show_shm:
                show_entry = False
            elif "deadlock" in entry.lower() and not show_deadlocks:
                show_entry = False
                
            # Apply text filter
            if self.log_filter and self.log_filter.lower() not in entry.lower():
                show_entry = False
                
            # Add filtered entry
            if show_entry:
                if self.log_text.index('end-1c') != '1.0':  # If not empty
                    self.log_text.insert(tk.END, "\n")
                self.log_text.insert(tk.END, entry)
                
        self.log_text.config(state=tk.DISABLED)
        
        # Restore scroll position - use the position from before the update
        self._log_scroll_position = current_position
        self.log_text.yview_moveto(current_position)
    
    def _update_overview_canvas(self):
        """Update the overview canvas"""
        # Clear the canvas
        self.overview_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.overview_canvas.winfo_width()
        height = self.overview_canvas.winfo_height()
        
        # Skip drawing if the canvas is not yet properly initialized
        if width < 50 or height < 50:
            # Schedule another attempt
            self.root.after(100, self._update_overview_canvas)
            return
            
        # Get current IPC state
        processes = self.deadlock_detector.processes
        resources = self.deadlock_detector.resources
        pipes = self.pipe_debugger.active_pipes
        queues = self.queue_debugger.active_queues
        memory_segments = self.shared_mem_debugger.shared_memories
        
        # Calculate counts for layout decisions
        active_processes = len(processes)
        active_pipes = len(pipes)
        active_queues = len(queues)
        active_memory = len(memory_segments)
        
        # Update active process count in UI
        self.active_process_count.config(text=f"{active_processes}")
        
        # Draw system components
        # Create mappings to track drawn objects for highlighting
        drawn_objects = {}
        
        # Create process ID mapping
        process_id_mapping = self._create_process_id_mapping()
        resource_id_mapping = self._create_resource_id_mapping()
        
        # Draw section titles
        self.overview_canvas.create_text(width/2, 20, text="PROCESSES", font=("Arial", 10, "bold"), fill="navy")
        
        # Draw processes at the top
        process_y = height * 0.2
        process_spacing = width / (active_processes + 1) if active_processes > 0 else width / 2
        process_positions = {}
        
        # Sort processes by ID number for consistent ordering
        sorted_processes = sorted(processes.items(), 
                                key=lambda x: int(x[0][1:]) if x[0].startswith("P") and x[0][1:].isdigit() else 999)
        
        for i, (process_id, process) in enumerate(sorted_processes):
            x = process_spacing * (i + 1)
            process_positions[process_id] = (x, process_y)
            
            # Use the process's original ID for display (P1, P2, etc.)
            # This ensures ID consistency with logs
            display_id = process_id
            if not process_id.startswith("P"):
                # If not in P# format, use the mapping
                for pid, mapped_id in process_id_mapping.items():
                    if pid == process_id and mapped_id.startswith("P"):
                        display_id = mapped_id
                        break
            
            # Color based on state (deadlocked processes are red)
            deadlocks = self.deadlock_detector.detect_deadlocks()
            is_deadlocked = any(process_id in cycle for cycle in deadlocks)
            color = "red" if is_deadlocked else ("yellow" if process.get('waiting_for') else "lightblue")
            
            # Check if this process should be highlighted - check all possible ID formats
            for elem, highlight_color, expiry_time in self.highlighted_elements:
                if elem["type"] == "process":
                    # Get canonical forms for comparison
                    element_id = self._get_canonical_process_id(elem["id"])
                    current_process_id = self._get_canonical_process_id(process_id)
                    
                    if element_id == current_process_id and time.time() < expiry_time:
                        # Draw highlight glow effect
                        glow_radius = 25
                        self.overview_canvas.create_oval(x-glow_radius, process_y-glow_radius, 
                                                      x+glow_radius, process_y+glow_radius, 
                                                      fill=highlight_color, outline="", stipple="gray50")
                        # Use brighter color for the process circle
                        color = "white"
                        break
            
            # Draw process as circle
            proc_circle = self.overview_canvas.create_oval(x-15, process_y-15, x+15, process_y+15, 
                                       fill=color, outline="black")
            proc_text = self.overview_canvas.create_text(x, process_y, text=display_id)
            
            # Store reference to drawn objects
            drawn_objects[f"process_{process_id}"] = (proc_circle, proc_text)
            drawn_objects[display_id] = (proc_circle, proc_text)
        
        # Draw RESOURCES title
        self.overview_canvas.create_text(width/2, height*0.35, text="RESOURCES", font=("Arial", 10, "bold"), fill="navy")
        
        # Draw resources in the middle
        resource_y = height * 0.5
        resource_spacing = width / (len(resources) + 1) if resources else width / 2
        resource_positions = {}
        
        # Sort resources by ID number for consistent ordering
        sorted_resources = sorted(resources.items(), 
                               key=lambda x: int(x[0][1:]) if x[0].startswith("R") and x[0][1:].isdigit() else 999)
        
        for i, (resource_id, resource) in enumerate(sorted_resources):
            x = resource_spacing * (i + 1)
            resource_positions[resource_id] = (x, resource_y)
            
            # Color based on state
            if resource.get('state') == 'owned':
                color = "green"
            elif resource.get('state') == 'free':
                color = "lightgray"
            else:
                color = "orange"
                
            # Check if this resource should be highlighted
            for elem, highlight_color, expiry_time in self.highlighted_elements:
                if elem["type"] == "resource":
                    # Get canonical forms for comparison
                    element_id = self._get_canonical_resource_id(elem["id"])
                    current_resource_id = self._get_canonical_resource_id(resource_id)
                    
                    if element_id == current_resource_id and time.time() < expiry_time:
                        # Draw highlight glow effect
                        glow_radius = 25
                        self.overview_canvas.create_rectangle(x-glow_radius, resource_y-glow_radius, 
                                                          x+glow_radius, resource_y+glow_radius, 
                                                          fill=highlight_color, outline="", stipple="gray50")
                        # Use brighter color
                        color = "white"
                        break
            
            # Draw resource as rectangle
            res_rect = self.overview_canvas.create_rectangle(x-15, resource_y-15, x+15, resource_y+15, 
                                                fill=color, outline="black")
            
            # Use the resource's original ID for display (R1, R2, etc.)
            # This ensures ID consistency with logs
            display_id = resource_id
            if not resource_id.startswith("R"):
                # If not in R# format, use the mapping
                for rid, mapped_id in resource_id_mapping.items():
                    if rid == resource_id and mapped_id.startswith("R"):
                        display_id = mapped_id
                        break
                        
            res_text = self.overview_canvas.create_text(x, resource_y, text=display_id)
            
            # Store reference to drawn objects
            drawn_objects[f"resource_{resource_id}"] = (res_rect, res_text)
            drawn_objects[display_id] = (res_rect, res_text)
        
        # Draw IPC Mechanism section titles
        # Only draw if there are any components to display
        if active_pipes > 0:
            self.overview_canvas.create_text(width * 0.25, height * 0.6, text="PIPES", font=("Arial", 10, "bold"), fill="navy")
        
        # Draw pipes on the left
        pipe_x = width * 0.25
        pipe_y_start = height * 0.7
        pipe_spacing = height * 0.2 / (active_pipes + 1) if active_pipes > 0 else height * 0.1
        
        for i, (pipe_id, pipe) in enumerate(pipes.items()):
            y = pipe_y_start + pipe_spacing * (i + 1)
            
            # Check if this pipe should be highlighted
            for elem, highlight_color, expiry_time in self.highlighted_elements:
                if elem["type"] == "pipe" and elem["id"] == pipe_id and time.time() < expiry_time:
                    # Draw highlight glow effect
                    self.overview_canvas.create_rectangle(pipe_x-60, y-15, pipe_x+60, y+15, 
                                                      fill=highlight_color, outline="", stipple="gray50")
                    break
            
            # Draw pipe
            pipe_rect = self.overview_canvas.create_rectangle(pipe_x-50, y-8, pipe_x+50, y+8, 
                                                fill="lightblue", outline="black")
            
            # Draw status indicator
            status = pipe.get('status', 'idle')
            if status == 'idle':
                status_color = "gray"
            elif status == 'transferring':
                status_color = "green"
            else:  # bottleneck
                status_color = "red"
            
            status_indicator = self.overview_canvas.create_oval(pipe_x+60, y-8, pipe_x+76, y+8, 
                                           fill=status_color, outline="black")
                                           
            # Store reference to drawn objects
            drawn_objects[f"pipe_{pipe_id}"] = (pipe_rect, status_indicator)
        
        # Draw queue title if needed
        if active_queues > 0:
            self.overview_canvas.create_text(width * 0.5, height * 0.6, text="MESSAGE QUEUES", font=("Arial", 10, "bold"), fill="navy")
            
        # Draw queues in the middle
        queue_x = width * 0.5
        queue_y_start = height * 0.7
        queue_spacing = height * 0.2 / (active_queues + 1) if active_queues > 0 else height * 0.1
        
        for i, (queue_id, queue) in enumerate(queues.items()):
            y = queue_y_start + queue_spacing * (i + 1)
            
            # Calculate fill level
            capacity = queue.get('capacity', 10)
            message_count = queue.get('message_count', 0)
            fill_ratio = message_count / capacity if capacity > 0 else 0
            
            # Check if this queue should be highlighted
            for elem, highlight_color, expiry_time in self.highlighted_elements:
                if elem["type"] == "queue" and elem["id"] == queue_id and time.time() < expiry_time:
                    # Draw highlight glow effect
                    self.overview_canvas.create_rectangle(queue_x-45, y-25, queue_x+45, y+25, 
                                                      fill=highlight_color, outline="", stipple="gray50")
                    break
            
            # Draw queue
            queue_width = 70
            fill_width = queue_width * fill_ratio
            
            queue_outline = self.overview_canvas.create_rectangle(queue_x-35, y-15, queue_x+35, y+15, 
                                                fill="white", outline="black")
            
            if fill_width > 0:
                queue_fill = self.overview_canvas.create_rectangle(queue_x-35, y-15, queue_x-35+fill_width, y+15, 
                                                    fill="green", outline="")
            
            queue_text = self.overview_canvas.create_text(queue_x, y, text=f"{message_count}/{capacity}")
            
            # Store reference to drawn objects
            drawn_objects[f"queue_{queue_id}"] = (queue_outline, queue_text)
        
        # Draw shared memory title if needed
        if active_memory > 0:
            self.overview_canvas.create_text(width * 0.75, height * 0.6, text="SHARED MEMORY", font=("Arial", 10, "bold"), fill="navy")
            
        # Draw shared memory segments on the right
        shm_x = width * 0.75
        shm_y_start = height * 0.7
        shm_spacing = height * 0.2 / (active_memory + 1) if active_memory > 0 else height * 0.1
        
        for i, (memory_id, memory) in enumerate(memory_segments.items()):
            y = shm_y_start + shm_spacing * (i + 1)
            
            # Check if this memory segment should be highlighted
            for elem, highlight_color, expiry_time in self.highlighted_elements:
                if elem["type"] == "shm" and elem["id"] == memory_id and time.time() < expiry_time:
                    # Draw highlight glow effect
                    self.overview_canvas.create_rectangle(shm_x-50, y-30, shm_x+50, y+30, 
                                                      fill=highlight_color, outline="", stipple="gray50")
                    break
            
            # Draw memory segment
            shm_rect = self.overview_canvas.create_rectangle(shm_x-40, y-20, shm_x+40, y+20, 
                                                fill="lightyellow", outline="black")
            
            # Draw locked regions if any
            locked_regions = memory.get('locked_regions', [])
            if locked_regions:
                lock_indicator = self.overview_canvas.create_rectangle(shm_x-30, y-10, shm_x-10, y+10, 
                                                    fill="red", outline="black")
                shm_text = self.overview_canvas.create_text(shm_x, y, text=f"Locked: {len(locked_regions)}")
            else:
                shm_text = self.overview_canvas.create_text(shm_x, y, text="Unlocked")
                
            # Store reference to drawn objects
            drawn_objects[f"shm_{memory_id}"] = (shm_rect, shm_text)
        
        # Draw relationships between processes and resources
        for process_id, process in processes.items():
            if process_id in process_positions:
                px, py = process_positions[process_id]
                
                # Draw owned resources
                for resource_id in process.get('owns', []):
                    if resource_id in resource_positions:
                        rx, ry = resource_positions[resource_id]
                        # Draw ownership line with animation effect if it's highlighted
                        highlighted = False
                        for elem, highlight_color, expiry_time in self.highlighted_elements:
                            if ((elem["type"] == "process" and elem["id"] == process_id) or
                                (elem["type"] == "resource" and elem["id"] == resource_id)) and time.time() < expiry_time:
                                highlighted = True
                                break
                                
                        if highlighted:
                            # Draw animated line (dashed, thicker, different color)
                            self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                          arrow=tk.LAST, fill="blue", width=2,
                                                          dash=(5, 2))
                        else:
                            # Normal line
                            self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                          arrow=tk.LAST, fill="black")
                
                # Draw waiting relationships
                waiting_for = process.get('waiting_for')
                if waiting_for and waiting_for in resource_positions:
                    rx, ry = resource_positions[waiting_for]
                    # Draw waiting line with animation effect if it's highlighted
                    highlighted = False
                    for elem, highlight_color, expiry_time in self.highlighted_elements:
                        if ((elem["type"] == "process" and elem["id"] == process_id) or
                            (elem["type"] == "resource" and elem["id"] == waiting_for)) and time.time() < expiry_time:
                            highlighted = True
                            break
                            
                    if highlighted:
                        # Draw animated line (thicker)
                        self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                      arrow=tk.LAST, fill="purple", width=2,
                                                      dash=(3, 2))
                    else:
                        # Normal waiting line
                        self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                      arrow=tk.LAST, fill="red", dash=(4, 4))
        
        # Clean up expired highlights
        current_time = time.time()
        self.highlighted_elements = [(elem, color, expiry) for elem, color, expiry in self.highlighted_elements 
                                    if current_time < expiry]
        
        # Schedule another update if there are still active highlights
        if self.highlighted_elements:
            self.root.after(100, self._update_overview_canvas)
    
    def _apply_log_filter(self):
        """Apply the filter text to the log entries"""
        filter_text = self.log_filter_var.get().strip()
        if filter_text:
            self.log_filter = filter_text
            self._update_status(f"Log filter applied: '{filter_text}'")
        else:
            self.log_filter = None
            self._update_status("Log filter cleared")
        
        # Update the log display with the filter
        self._update_log_text()
    
    def _clear_log_filter(self):
        """Clear the log filter"""
        self.log_filter_var.set("")
        self.log_filter = None
        self._update_status("Log filter cleared")
        
        # Update the log display
        self._update_log_text()
    
    def _refresh_ui(self):
        """Refresh all UI elements at a consistent rate"""
        # Throttle the refresh rate to prevent excessive redraws
        now = time.time()
        if hasattr(self, '_last_refresh_time') and now - self._last_refresh_time < 0.5:  # Max 2 fps
            # Schedule next refresh without performing updates
            self.root.after(self.refresh_rate, self._refresh_ui)
            return

        self._last_refresh_time = now
        
        # Update individual tabs
        self._update_pipe_ui()
        self._update_queue_ui()
        self._update_shm_ui()
        self._update_deadlock_ui()
        self._update_log_text()
        
        # Update overview last, to include latest information
        self._update_overview_canvas()
        
        # Schedule next refresh
        self.root.after(self.refresh_rate, self._refresh_ui)

    def _request_resource(self):
        """Request a resource for a process"""
        process_id = self.selected_process_var.get()
        resource_id = self.selected_resource_var.get()
        
        if process_id and resource_id:
            # Create an input dialog to get number of instances
            instances_dialog = tk.Toplevel(self.root)
            instances_dialog.title("Resource Instances")
            instances_dialog.transient(self.root)
            instances_dialog.grab_set()
            
            dialog_frame = ttk.Frame(instances_dialog, padding=10)
            dialog_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(dialog_frame, text=f"How many instances of {resource_id}\ndo you want to request for {process_id}?").pack(pady=5)
            
            instances_var = tk.StringVar(value="1")
            ttk.Entry(dialog_frame, textvariable=instances_var, width=10).pack(pady=5)
            
            def on_confirm():
                try:
                    instances = int(instances_var.get())
                    if instances <= 0:
                        raise ValueError("Instances must be greater than 0")
                    
                    # Close dialog
                    instances_dialog.destroy()
                    
                    # Request the resource
                    result = self.deadlock_detector.request_resource(process_id, resource_id, instances)
                    
                    if result:
                        self.status_bar.config(text=f"Process {process_id} acquired {instances} instance(s) of {resource_id}")
                    else:
                        self.status_bar.config(text=f"Process {process_id} waiting for {instances} instance(s) of {resource_id}")
                    
                    self._update_deadlock_ui()
                except ValueError as e:
                    messagebox.showerror("Input Error", str(e))
            
            button_frame = ttk.Frame(dialog_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="OK", command=on_confirm).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=instances_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Center the dialog
            instances_dialog.update_idletasks()
            w = instances_dialog.winfo_width()
            h = instances_dialog.winfo_height()
            x = (self.root.winfo_width() - w) // 2 + self.root.winfo_x()
            y = (self.root.winfo_height() - h) // 2 + self.root.winfo_y()
            instances_dialog.geometry(f"{w}x{h}+{x}+{y}")
    
    def _release_resource(self):
        """Release a resource from a process"""
        process_id = self.selected_process_var.get()
        resource_id = self.selected_resource_var.get()
        
        if process_id and resource_id:
            # Check if the process actually owns this resource
            process_info = self.deadlock_detector.get_process_status().get(process_id, {})
            if resource_id not in process_info.get('owns', []):
                self.status_bar.config(text=f"Process {process_id} does not own resource {resource_id}")
                return
            
            # Get the current allocation
            resource_info = self.deadlock_detector.get_resource_status().get(resource_id, {})
            current_allocation = resource_info.get('allocations', {}).get(process_id, 0)
            
            if current_allocation <= 0:
                self.status_bar.config(text=f"Process {process_id} does not have any instances of {resource_id}")
                return
            
            # Create an input dialog to get number of instances to release
            instances_dialog = tk.Toplevel(self.root)
            instances_dialog.title("Release Instances")
            instances_dialog.transient(self.root)
            instances_dialog.grab_set()
            
            dialog_frame = ttk.Frame(instances_dialog, padding=10)
            dialog_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(dialog_frame, text=f"Process {process_id} has {current_allocation} instance(s) of {resource_id}.\nHow many do you want to release?").pack(pady=5)
            
            instances_var = tk.StringVar(value=str(current_allocation))
            ttk.Entry(dialog_frame, textvariable=instances_var, width=10).pack(pady=5)
            
            def on_confirm():
                try:
                    instances = int(instances_var.get())
                    if instances <= 0 or instances > current_allocation:
                        raise ValueError(f"Instances must be between 1 and {current_allocation}")
                    
                    # Close dialog
                    instances_dialog.destroy()
                    
                    # Release the resource
                    self.deadlock_detector.release_resource(process_id, resource_id, instances)
                    
                    self.status_bar.config(text=f"Process {process_id} released {instances} instance(s) of {resource_id}")
                    self._update_deadlock_ui()
                except ValueError as e:
                    messagebox.showerror("Input Error", str(e))
            
            button_frame = ttk.Frame(dialog_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="OK", command=on_confirm).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=instances_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Center the dialog
            instances_dialog.update_idletasks()
            w = instances_dialog.winfo_width()
            h = instances_dialog.winfo_height()
            x = (self.root.winfo_width() - w) // 2 + self.root.winfo_x()
            y = (self.root.winfo_height() - h) // 2 + self.root.winfo_y()
            instances_dialog.geometry(f"{w}x{h}+{x}+{y}")
    
    def _simulate_deadlock(self):
        """Simulate a deadlock scenario or stop an ongoing simulation"""
        # If simulation is active, stop it
        if self.deadlock_simulation_active:
            self.deadlock_simulation_active = False
            self.deadlock_sim_button.configure(text="Simulate Deadlock")
            self._update_status("Deadlock simulation stopped")
            return
            
        # Otherwise, start a new simulation
        self.deadlock_simulation_active = True
        self.deadlock_sim_button.configure(text="Stop Simulation")
        
        # Reset current state for clean simulation
        self.deadlock_detector.clear_all()
        
        # Get simulation parameters
        try:
            process_count = int(self.sim_processes_var.get())
            resource_count = int(self.sim_resources_var.get())
            
            if process_count < 2 or resource_count < 2:
                messagebox.showwarning("Invalid Parameters", "Need at least 2 processes and 2 resources to create a deadlock.")
                # Reset button state
                self.deadlock_simulation_active = False
                self.deadlock_sim_button.configure(text="Simulate Deadlock")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for processes and resources.")
            # Reset button state
            self.deadlock_simulation_active = False
            self.deadlock_sim_button.configure(text="Simulate Deadlock")
            return
        
        # Create processes
        processes = []
        for i in range(process_count):
            p_id = f"P{i+1}"
            self.deadlock_detector.register_process(p_id)
            processes.append(p_id)
            self._log_event(f"Registered process {p_id}")
            
        # Create resources with varying instances - in sequential order
        resources = []
        for i in range(resource_count):
            r_id = f"R{i+1}"
            # Randomly decide number of instances (1-3)
            instances = random.randint(1, 3)
            self.deadlock_detector.register_resource(r_id, instances=instances)
            resources.append((r_id, instances))
            self._log_event(f"Registered resource {r_id}")
        
        # Allocate initial resources
        for i, p_id in enumerate(processes):
            # Each process gets one resource initially
            r_id, max_instances = resources[i % resource_count]
            # Allocate 1 or more instances but leave some available for others
            allocated = random.randint(1, max(1, max_instances - 1))
            self.deadlock_detector.request_resource(p_id, r_id, allocated)
            
        # Create circular wait condition
        for i, p_id in enumerate(processes):
            # Each process requests the next resource in the chain
            r_id, max_instances = resources[(i + 1) % resource_count]
            # Request more instances than available to ensure blocking
            requested = random.randint(1, max_instances)
            self.deadlock_detector.request_resource(p_id, r_id, requested)
            
        # Update status
        self.status_bar.config(text=f"Simulated deadlock with {process_count} processes and {resource_count} resources")
        
        # Update UI and analyze
        self._update_deadlock_ui()
        self._analyze_deadlocks()
    
    def _on_shm_selected(self, event=None):
        """Handle selection of a shared memory segment from dropdown"""
        selected_memory = self.op_memory_id_var.get()
        if selected_memory:
            # Update memory information in status bar
            memory_status = self.shared_mem_debugger.get_memory_status().get(selected_memory, {})
            size = memory_status.get("size", 0)
            access_count = memory_status.get("access_count", 0)
            self.status_bar.config(text=f"Selected memory: {selected_memory} | Size: {size} bytes | Accesses: {access_count}")
    
    def _write_to_memory(self):
        """Simulate writing to shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        data = self.shm_data_entry.get() or "Test data"
        size = len(data)
        
        if memory_id:
            self._write_shared_memory()
            self.status_bar.config(text=f"Data written to shared memory {memory_id} at offset {offset}")
    
    def _read_from_memory(self):
        """Simulate reading from shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            self._read_shared_memory()
            # In a real system, we would display the read data
            messagebox.showinfo("Memory Read", f"Read {size} bytes from {memory_id} at offset {offset}")
            self.status_bar.config(text=f"Data read from shared memory {memory_id} at offset {offset}")
    
    def _close_shared_memory(self):
        """Delete the selected shared memory segment"""
        memory_id = self.op_memory_id_var.get()
        if memory_id:
            self.shared_mem_debugger.unregister_memory_segment(memory_id)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} closed")
    
    def _lock_region(self):
        """Lock a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        start = int(self.lock_start_var.get() or "0")
        end = int(self.lock_end_var.get() or "100")
        size = end - start
        
        if memory_id and size > 0:
            self._lock_shared_memory()
            self.status_bar.config(text=f"Region locked in shared memory {memory_id} from {start} to {end}")
    
    def _unlock_region(self):
        """Unlock a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        start = int(self.lock_start_var.get() or "0")
        end = int(self.lock_end_var.get() or "100")
        size = end - start
        
        if memory_id and size > 0:
            self._unlock_shared_memory()
            self.status_bar.config(text=f"Region unlocked in shared memory {memory_id} from {start} to {end}")
    
    def _simulate_race_condition(self):
        """Simulate a race condition in shared memory access"""
        memory_id = self.op_memory_id_var.get()
        
        if memory_id:
            # Create two processes that will access the same memory region
            process1 = f"proc_{random.randint(1000, 9999)}"
            process2 = f"proc_{random.randint(1000, 9999)}"
            
            offset = int(self.memory_offset_var.get() or "0")
            
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            # Log the simulation start
            self.shared_mem_debugger.add_log_entry(
                memory_id, 
                f"Race condition simulation started: {process1} and {process2} accessing same region"
            )
            
            # Simulate concurrent access - first process writes
            self.memory_process_id_var.set(process1)
            self._write_shared_memory()
            
            # Second process writes to the same location without synchronization
            self.memory_process_id_var.set(process2)
            self._write_shared_memory()
            
            # Update status to indicate race condition
            memory_status["status"] = "race_condition"
            self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
            
            # Log the race condition
            self.shared_mem_debugger.add_log_entry(
                memory_id, 
                f"Race condition detected between {process1} and {process2} at offset {offset}"
            )
            
            self._update_shm_ui()
            self.status_bar.config(text=f"Race condition simulated on shared memory {memory_id}")
            
            # Reset process ID
            self.memory_process_id_var.set("")
    
    def _toggle_log_pause(self):
        """Toggle the event log pause state"""
        self.log_paused = not self.log_paused
        if self.log_paused:
            self.log_pause_button.configure(text="Resume Log")
            self._update_status("Event log updates paused")
        else:
            self.log_pause_button.configure(text="Pause Log")
            self._update_status("Event log updates resumed")
            # Force update with current data
            self._update_log_text()
    
    def _clear_log(self):
        """Clear the event log"""
        self.log_entries = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._update_status("Event log cleared")
    
    def _export_log(self):
        """Export the event log to a file"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Event Log"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for entry in self.log_entries:
                        f.write(f"{entry}\n")
                self._update_status(f"Event log exported to {file_path}")
            except Exception as e:
                self._update_status(f"Error exporting log: {str(e)}")
    
    def _log_event(self, message):
        """Log an event with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        
        # Add to log entries list, keeping only the maximum number
        self.log_entries.append(log_entry)
        
        # Trim log if it gets too large
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries = self.log_entries[-self.max_log_entries:]
        
        # Extract information about the event for overview highlighting
        highlighted_element = None
        highlight_color = "yellow"
        if "pipe" in message.lower():
            pipe_id = None
            for word in message.split():
                if word.startswith("pipe_"):
                    pipe_id = word
                    break
            if pipe_id:
                highlighted_element = {"type": "pipe", "id": pipe_id}
                
        elif "queue" in message.lower():
            queue_id = None
            for word in message.split():
                if word.startswith("queue_"):
                    queue_id = word
                    break
            if queue_id:
                highlighted_element = {"type": "queue", "id": queue_id}
                
        elif "shared memory" in message.lower() or "shm_" in message.lower():
            shm_id = None
            for word in message.split():
                if word.startswith("shm_"):
                    shm_id = word
                    break
            if shm_id:
                highlighted_element = {"type": "shm", "id": shm_id}
                
        elif any(x in message.lower() for x in ["process", "resource", "deadlock"]):
            # Highlight any process or resource mentioned
            process_id = None
            for word in message.split():
                # Match both "P5" format and "process_XXXX" format
                if word.startswith("P") and len(word) < 4:
                    process_id = word
                    highlighted_element = {"type": "process", "id": process_id}
                    if "deadlock" in message.lower():
                        highlight_color = "red"
                    break
                elif word.startswith("process_"):
                    process_id = word
                    # Get the canonical form of the process ID
                    canonical_id = self._get_canonical_process_id(process_id)
                    highlighted_element = {"type": "process", "id": canonical_id}
                    if "deadlock" in message.lower():
                        highlight_color = "red"
                    break
                elif word.startswith("R") and len(word) < 4:
                    resource_id = word
                    # Get the canonical form of the resource ID
                    canonical_id = self._get_canonical_resource_id(resource_id)
                    highlighted_element = {"type": "resource", "id": canonical_id}
                    break
                    
        # Store the highlighted element for next overview update
        if highlighted_element:
            # If this is a new process we're seeing in logs, try to register it
            if highlighted_element["type"] == "process" and highlighted_element["id"].startswith("process_"):
                pid = highlighted_element["id"].replace("process_", "")
                # Check if this process isn't already registered
                if not any(p_id == pid for p_id in self.deadlock_detector.processes):
                    # Add process to system for tracking and visualization
                    self.deadlock_detector.register_process(pid)
                    # Force a refresh of the process mappings
                    self._create_process_id_mapping()
            
            # Track all highlighted elements for better visibility on the overview
            self.highlighted_elements.append((highlighted_element, highlight_color, time.time() + 3))  # Highlight for 3 seconds
            
            # Force immediate overview update to show highlight
            # Only update UI if not throttled
            current_time = time.time()
            if current_time - self.last_ui_update >= self.ui_update_interval:
                self._update_overview_canvas()
                self.last_ui_update = current_time

        # If not paused, update the display
        if not self.log_paused and (len(self.log_entries) % 10 == 0):  # Only update UI every 10 entries
            # Save current scroll position
            text_widget = self.log_text
            current_position = text_widget.yview()[0]
            
            text_widget.config(state=tk.NORMAL)
            
            # Check if scrolled to bottom
            was_at_bottom = False
            if text_widget.yview()[1] > 0.9:  # If showing the last 10% of content
                was_at_bottom = True
            
            # Clear and repopulate with recent entries
            text_widget.delete(1.0, tk.END)
            
            # Show the last 100 entries or as many as we have
            display_entries = self.log_entries[-100:] if len(self.log_entries) > 100 else self.log_entries
            for i, entry in enumerate(display_entries):
                if i > 0:
                    text_widget.insert(tk.END, "\n")
                text_widget.insert(tk.END, entry)
            
            # Apply filtering if set
            if self.log_filter:
                self._apply_log_filter()
            else:
                # Auto-scroll only if we were already at the bottom
                if was_at_bottom:
                    text_widget.see(tk.END)
                else:
                    # Otherwise maintain the current scroll position
                    text_widget.yview_moveto(current_position)
                    # Update the saved position to match
                    self._log_scroll_position = current_position
                
            text_widget.config(state=tk.DISABLED)
    
    def _update_status(self, message):
        """Update the status bar with a message"""
        self.status_bar.config(text=message)
        # Log the status message to the console for debugging
        print(f"Status: {message}")

    def _update_system_metrics(self):
        """Update system metrics display with real values instead of simulated ones"""
        # Use actual IPC activity rather than random values
        active_processes = len(self.pipe_debugger.active_pipes) + len(self.queue_debugger.active_queues) + len(self.shared_mem_debugger.shared_memories)
        self.active_process_count.config(text=str(active_processes))
        
        # Update IPC counts in summary with real data
        self.pipe_count.config(text=f"Active: {len(self.pipe_debugger.active_pipes)}")
        self.queue_count.config(text=f"Active: {len(self.queue_debugger.active_queues)}")
        
        # Calculate total messages in queues
        total_messages = 0
        for queue_info in self.queue_debugger.active_queues.values():
            total_messages += queue_info.get('message_count', 0)
        self.queue_messages.config(text=f"Messages: {total_messages}")
        
        # Update shared memory counters
        self.shm_count.config(text=f"Active: {len(self.shared_mem_debugger.shared_memories)}")
        
        # Calculate total memory accesses
        total_accesses = 0
        for shm_info in self.shared_mem_debugger.shared_memories.values():
            total_accesses += shm_info.get('access_count', 0)
        self.shm_access.config(text=f"Accesses: {total_accesses}")
        
        # Update deadlock counters
        self.process_count.config(text=f"Processes: {len(self.deadlock_detector.processes)}")
        self.resource_count.config(text=f"Resources: {len(self.deadlock_detector.resources)}")
        
        # Check for deadlocks
        deadlocks = self.deadlock_detector.detect_deadlocks()
        self.deadlock_count.config(text=f"Deadlocks: {len(deadlocks)}")
        
        # Calculate operations per second based on recent log entries
        recent_entries = 0
        now = time.time()
        for entry in reversed(self.log_entries):
            # Try to extract timestamp from log entry
            try:
                timestamp_str = entry.split(']')[0].strip('[')
                entry_time = datetime.datetime.strptime(timestamp_str, "%H:%M:%S.%f").time()
                current_time = datetime.datetime.now().time()
                
                # Count entries from the last 5 seconds
                if (current_time.hour == entry_time.hour and 
                    current_time.minute == entry_time.minute and 
                    current_time.second - entry_time.second <= 5):
                    recent_entries += 1
            except:
                pass
        
        ops_per_sec = recent_entries // 5 if recent_entries > 0 else 0
        self.ipc_throughput.config(text=f"{ops_per_sec} ops/sec")
        
        # Update overview canvas to reflect current state
        self._update_overview_canvas()

    def _create_process_id_mapping(self):
        """Create a mapping between different process ID formats for consistent reference"""
        mapping = {}
        
        # Map processes from deadlock detector
        for i, process_id in enumerate(self.deadlock_detector.processes.keys()):
            short_id = f"P{i+1}"
            mapping[process_id] = short_id
            mapping[short_id] = process_id
            
            # Also map process_XXX format
            if not process_id.startswith("process_"):
                process_long_id = f"process_{process_id}"
                mapping[process_long_id] = short_id
                mapping[short_id] = process_long_id
        
        return mapping

    def _create_resource_id_mapping(self):
        """Create a mapping between different resource ID formats for consistent reference"""
        mapping = {}
        
        # Instead of relying on enumeration order, we need to preserve original IDs
        # This ensures R4 in logs remains R4 in the diagram
        for resource_id in self.deadlock_detector.resources.keys():
            # If the resource ID already follows the R# format, keep it as is
            if resource_id.startswith("R") and resource_id[1:].isdigit():
                mapping[resource_id] = resource_id
            else:
                # For other formats, assign a sequential number
                next_id = len(mapping) // 2 + 1
                short_id = f"R{next_id}"
                mapping[resource_id] = short_id
                mapping[short_id] = resource_id
        
        return mapping
        
    def _get_canonical_process_id(self, process_id):
        """Convert any process ID format to its canonical form"""
        mapping = self._create_process_id_mapping()
        
        if process_id in mapping:
            return mapping[process_id]
            
        # If not in mapping but has process_ prefix, try to extract numeric part
        if process_id.startswith("process_"):
            numeric_id = process_id.replace("process_", "")
            if numeric_id in mapping:
                return mapping[numeric_id]
                
        # If not found in mapping, return original
        return process_id
        
    def _get_canonical_resource_id(self, resource_id):
        """Convert any resource ID format to its canonical form"""
        mapping = self._create_resource_id_mapping()
        
        if resource_id in mapping:
            return mapping[resource_id]
                
        # If not found in mapping, return original
        return resource_id