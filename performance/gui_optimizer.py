"""
GUI Performance Optimizer
Optimized GUI components for better responsiveness, memory usage, and user experience
"""

import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import time
import logging
import math
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import deque
import weakref
import gc

# Dark Theme Configuration for Optimized Components
class OptimizedDarkTheme:
    """Dark theme configuration optimized for performance"""
    # Primary colors (optimized for GUI performance)
    BG_PRIMARY = '#2B2B2B'
    BG_SECONDARY = '#363636'
    BG_TERTIARY = '#404040'

    # Text colors
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#CCCCCC'
    TEXT_DISABLED = '#808080'

    # Accent colors
    ACCENT_BLUE = '#0078D4'
    ACCENT_GREEN = '#107C10'
    ACCENT_ORANGE = '#FF8C00'
    ACCENT_RED = '#D13438'

    # Interactive colors
    HOVER_BG = '#464646'
    ACTIVE_BG = '#505050'
    SELECTED_BG = '#094771'

    # Component colors
    PROGRESS_BG = '#3A3A3A'
    PROGRESS_FILL = '#0078D4'
    PROGRESS_FILL_SUCCESS = '#107C10'
    PROGRESS_FILL_WARNING = '#FF8C00'
    PROGRESS_FILL_ERROR = '#D13438'

    INPUT_BG = '#3C3C3C'
    INPUT_BORDER = '#565656'
    INPUT_FOCUS = '#0078D4'

    LISTBOX_BG = '#3C3C3C'
    LISTBOX_SELECT = '#094771'
    LISTBOX_HOVER = '#464646'

logger = logging.getLogger(__name__)

@dataclass
class GUIMetrics:
    """GUI performance metrics"""
    render_time: float = 0.0
    update_frequency: float = 0.0
    memory_usage: int = 0
    widget_count: int = 0
    event_queue_size: int = 0
    lag_events: int = 0
    responsiveness_score: float = 100.0

class OptimizedWidget:
    """Base class for optimized widgets with performance tracking"""

    def __init__(self, parent=None):
        self.parent = parent
        self.children = []
        self.last_update = 0.0
        self.update_threshold = 0.016  # 60 FPS target
        self.dirty = False
        self.visible = True
        self.metrics = GUIMetrics()

        # Register with parent
        if parent and hasattr(parent, 'children'):
            parent.children.append(self)

    def mark_dirty(self):
        """Mark widget as needing update"""
        self.dirty = True
        if self.parent and hasattr(self.parent, 'mark_dirty'):
            self.parent.mark_dirty()

    def should_update(self) -> bool:
        """Check if widget should be updated based on throttling"""
        current_time = time.time()
        return (self.dirty and
                current_time - self.last_update >= self.update_threshold)

    def update_if_needed(self):
        """Update widget only if needed and not throttled"""
        if self.should_update() and self.visible:
            self.update_widget()
            self.dirty = False
            self.last_update = time.time()

    def update_widget(self):
        """Override in subclasses for actual update logic"""
        pass

    def cleanup(self):
        """Cleanup widget resources"""
        self.children.clear()
        if self.parent and hasattr(self.parent, 'children'):
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass

class OptimizedProgressBar(OptimizedWidget):
    """Memory-efficient progress bar with smooth animations and dark theme"""

    def __init__(self, parent, length=300, height=20, corner_radius=8, theme_style='default'):
        super().__init__(parent)
        self.parent_widget = parent
        self.length = length
        self.height = height
        self.corner_radius = corner_radius
        self.theme_style = theme_style
        self.value = 0.0
        self.max_value = 100.0

        # Theme colors based on style
        self.bg_color = OptimizedDarkTheme.PROGRESS_BG
        if theme_style == 'success':
            self.fill_color = OptimizedDarkTheme.PROGRESS_FILL_SUCCESS
        elif theme_style == 'warning':
            self.fill_color = OptimizedDarkTheme.PROGRESS_FILL_WARNING
        elif theme_style == 'error':
            self.fill_color = OptimizedDarkTheme.PROGRESS_FILL_ERROR
        else:
            self.fill_color = OptimizedDarkTheme.PROGRESS_FILL

        # Create tkinter widgets with dark theme
        self.frame = tk.Frame(parent, bg=OptimizedDarkTheme.BG_SECONDARY)
        self.canvas = tk.Canvas(self.frame, width=length, height=height,
                               highlightthickness=0, bg=OptimizedDarkTheme.BG_SECONDARY,
                               relief='flat', borderwidth=0)
        self.canvas.pack()

        # Animation state
        self.target_value = 0.0
        self.animation_speed = 0.15
        self.gradient_enabled = True

        # Draw initial state
        self.draw_progress()

    def set_value(self, value: float, animate: bool = True):
        """Set progress value with optional animation"""
        if animate:
            self.target_value = max(0, min(value, self.max_value))
        else:
            self.value = max(0, min(value, self.max_value))
            self.target_value = self.value
        self.mark_dirty()

    def update_widget(self):
        """Update progress bar with smooth animation"""
        if abs(self.value - self.target_value) > 0.1:
            # Animate towards target
            diff = self.target_value - self.value
            self.value += diff * self.animation_speed
            self.mark_dirty()  # Continue animation
        else:
            self.value = self.target_value

        self.draw_progress()

    def draw_progress(self):
        """Draw progress bar with rounded corners and dark theme"""
        self.canvas.delete("progress")

        # Calculate fill width
        fill_width = (self.value / self.max_value) * self.length

        # Draw rounded background
        self._draw_rounded_rectangle(0, 0, self.length, self.height,
                                   self.corner_radius, fill=self.bg_color,
                                   outline='', tags="progress")

        # Draw rounded progress fill
        if fill_width > self.corner_radius:
            self._draw_rounded_rectangle(0, 0, fill_width, self.height,
                                       self.corner_radius, fill=self.fill_color,
                                       outline='', tags="progress")
        elif fill_width > 0:
            # For very small progress, just draw a rounded edge
            self._draw_rounded_rectangle(0, 0, max(fill_width, self.corner_radius * 2),
                                       self.height, self.corner_radius,
                                       fill=self.fill_color, outline='', tags="progress")

    def _draw_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle on the canvas"""
        if x2 - x1 < radius * 2 or y2 - y1 < radius * 2:
            # Too small for rounded corners, draw regular rectangle
            return self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

        points = []
        # Top side
        points.extend([x1 + radius, y1, x2 - radius, y1])
        # Top-right arc
        for i in range(0, 91, 10):
            x = x2 - radius + radius * math.cos(math.radians(i))
            y = y1 + radius - radius * math.sin(math.radians(i))
            points.extend([x, y])
        # Right side
        points.extend([x2, y2 - radius])
        # Bottom-right arc
        for i in range(90, 181, 10):
            x = x2 - radius + radius * math.cos(math.radians(i))
            y = y2 - radius - radius * math.sin(math.radians(i))
            points.extend([x, y])
        # Bottom side
        points.extend([x1 + radius, y2])
        # Bottom-left arc
        for i in range(180, 271, 10):
            x = x1 + radius + radius * math.cos(math.radians(i))
            y = y2 - radius - radius * math.sin(math.radians(i))
            points.extend([x, y])
        # Left side
        points.extend([x1, y1 + radius])
        # Top-left arc
        for i in range(270, 361, 10):
            x = x1 + radius + radius * math.cos(math.radians(i))
            y = y1 + radius - radius * math.sin(math.radians(i))
            points.extend([x, y])

        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def pack(self, **kwargs):
        """Pack the progress bar frame"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the progress bar frame"""
        self.frame.grid(**kwargs)

class OptimizedTextDisplay(OptimizedWidget):
    """Memory-efficient text display with virtual scrolling and dark theme"""

    def __init__(self, parent, width=80, height=20, max_lines=10000, corner_radius=4):
        super().__init__(parent)
        self.parent_widget = parent
        self.max_lines = max_lines
        self.corner_radius = corner_radius

        # Text buffer with circular queue for memory efficiency
        self.text_buffer = deque(maxlen=max_lines)
        self.visible_start = 0
        self.visible_end = height

        # Create container frame with dark theme
        self.container = tk.Frame(parent, bg=OptimizedDarkTheme.BG_SECONDARY)

        # Create text widget with dark theme styling
        self.text_widget = tk.Text(self.container, width=width, height=height,
                                 wrap=tk.WORD, state=tk.DISABLED,
                                 bg=OptimizedDarkTheme.INPUT_BG,
                                 fg=OptimizedDarkTheme.TEXT_PRIMARY,
                                 insertbackground=OptimizedDarkTheme.TEXT_PRIMARY,
                                 selectbackground=OptimizedDarkTheme.SELECTED_BG,
                                 selectforeground=OptimizedDarkTheme.TEXT_PRIMARY,
                                 relief='flat', borderwidth=1,
                                 highlightthickness=1,
                                 highlightcolor=OptimizedDarkTheme.INPUT_FOCUS,
                                 highlightbackground=OptimizedDarkTheme.INPUT_BORDER,
                                 font=('Segoe UI', 9))

        # Scrollbar with dark theme
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL,
                                     command=self.on_scroll)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)

        # Bind events
        self.text_widget.bind('<MouseWheel>', self.on_mousewheel)
        self.text_widget.bind('<Key>', self.on_key)

    def append_text(self, text: str):
        """Append text efficiently"""
        lines = text.split('\n')
        for line in lines:
            self.text_buffer.append(line)

        self.mark_dirty()

    def update_widget(self):
        """Update visible text efficiently"""
        # Calculate visible range
        total_lines = len(self.text_buffer)
        visible_height = int(self.text_widget.cget('height'))

        # Adjust visible range
        if self.visible_end > total_lines:
            self.visible_end = total_lines
            self.visible_start = max(0, total_lines - visible_height)

        # Get visible text
        visible_lines = list(self.text_buffer)[self.visible_start:self.visible_end]
        visible_text = '\n'.join(visible_lines)

        # Update text widget
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, visible_text)
        self.text_widget.config(state=tk.DISABLED)

        # Update scrollbar
        if total_lines > 0:
            top = self.visible_start / total_lines
            bottom = self.visible_end / total_lines
            self.scrollbar.set(top, bottom)

    def on_scroll(self, *args):
        """Handle scrollbar events"""
        if args[0] == 'scroll':
            delta = int(args[1])
            self.scroll_lines(delta)
        elif args[0] == 'moveto':
            position = float(args[1])
            total_lines = len(self.text_buffer)
            visible_height = int(self.text_widget.cget('height'))
            self.visible_start = int(position * (total_lines - visible_height))
            self.visible_end = self.visible_start + visible_height
            self.mark_dirty()

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        delta = -1 if event.delta > 0 else 1
        self.scroll_lines(delta * 3)

    def on_key(self, event):
        """Handle keyboard scrolling"""
        if event.keysym == 'Up':
            self.scroll_lines(-1)
        elif event.keysym == 'Down':
            self.scroll_lines(1)
        elif event.keysym == 'Prior':  # Page Up
            self.scroll_lines(-10)
        elif event.keysym == 'Next':   # Page Down
            self.scroll_lines(10)

    def scroll_lines(self, delta: int):
        """Scroll by specified number of lines"""
        visible_height = int(self.text_widget.cget('height'))
        total_lines = len(self.text_buffer)

        self.visible_start = max(0, min(self.visible_start + delta,
                                      total_lines - visible_height))
        self.visible_end = self.visible_start + visible_height
        self.mark_dirty()

    def pack(self, **kwargs):
        """Pack text widget and scrollbar"""
        self.container.pack(**kwargs)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def grid(self, row, column, **kwargs):
        """Grid text widget and scrollbar"""
        self.container.grid(row=row, column=column, **kwargs)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

class OptimizedListbox(OptimizedWidget):
    """Virtual listbox for handling large datasets efficiently with dark theme"""

    def __init__(self, parent, width=30, height=10, selectmode=tk.SINGLE, corner_radius=4):
        super().__init__(parent)
        self.parent_widget = parent
        self.corner_radius = corner_radius

        # Data storage
        self.data = []
        self.filtered_data = []
        self.filter_func = None

        # Virtual scrolling
        self.visible_start = 0
        self.visible_count = height

        # Create container frame
        self.container = tk.Frame(parent, bg=OptimizedDarkTheme.BG_SECONDARY)

        # Create listbox with dark theme
        self.listbox = tk.Listbox(self.container, width=width, height=height,
                                selectmode=selectmode,
                                bg=OptimizedDarkTheme.LISTBOX_BG,
                                fg=OptimizedDarkTheme.TEXT_PRIMARY,
                                selectbackground=OptimizedDarkTheme.LISTBOX_SELECT,
                                selectforeground=OptimizedDarkTheme.TEXT_PRIMARY,
                                relief='flat', borderwidth=1,
                                highlightthickness=1,
                                highlightcolor=OptimizedDarkTheme.INPUT_FOCUS,
                                highlightbackground=OptimizedDarkTheme.INPUT_BORDER,
                                font=('Segoe UI', 9),
                                activestyle='none')

        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL,
                                     command=self.on_scroll)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Bind events
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind('<MouseWheel>', self.on_mousewheel)
        self.listbox.bind('<Motion>', self.on_motion)
        self.listbox.bind('<Leave>', self.on_leave)

        # Hover tracking
        self.hover_index = None

    def set_data(self, data: List[Any]):
        """Set listbox data efficiently"""
        self.data = data
        self.apply_filter()

    def set_filter(self, filter_func: Optional[Callable]):
        """Set filter function for data"""
        self.filter_func = filter_func
        self.apply_filter()

    def apply_filter(self):
        """Apply current filter to data"""
        if self.filter_func:
            self.filtered_data = [item for item in self.data
                                if self.filter_func(item)]
        else:
            self.filtered_data = self.data.copy()

        self.visible_start = 0
        self.mark_dirty()

    def update_widget(self):
        """Update visible listbox items"""
        # Clear current items
        self.listbox.delete(0, tk.END)

        # Calculate visible range
        total_items = len(self.filtered_data)
        visible_end = min(self.visible_start + self.visible_count, total_items)

        # Add visible items
        for i in range(self.visible_start, visible_end):
            self.listbox.insert(tk.END, str(self.filtered_data[i]))

        # Update scrollbar
        if total_items > 0:
            top = self.visible_start / total_items
            bottom = visible_end / total_items
            self.scrollbar.set(top, bottom)

    def on_scroll(self, *args):
        """Handle scrollbar events"""
        if args[0] == 'scroll':
            delta = int(args[1])
            self.scroll_items(delta)
        elif args[0] == 'moveto':
            position = float(args[1])
            total_items = len(self.filtered_data)
            self.visible_start = int(position * (total_items - self.visible_count))
            self.visible_start = max(0, min(self.visible_start,
                                          total_items - self.visible_count))
            self.mark_dirty()

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        delta = -1 if event.delta > 0 else 1
        self.scroll_items(delta)

    def scroll_items(self, delta: int):
        """Scroll by specified number of items"""
        total_items = len(self.filtered_data)
        self.visible_start = max(0, min(self.visible_start + delta,
                                      total_items - self.visible_count))
        self.mark_dirty()

    def on_select(self, event):
        """Handle selection events"""
        selection = self.listbox.curselection()
        if selection:
            # Adjust index for virtual scrolling
            actual_index = self.visible_start + selection[0]
            # Trigger custom selection callback if set
            if hasattr(self, 'selection_callback'):
                self.selection_callback(actual_index, self.filtered_data[actual_index])

    def on_motion(self, event):
        """Handle mouse motion for hover effects"""
        index = self.listbox.nearest(event.y)
        if index != self.hover_index:
            if self.hover_index is not None:
                # Reset previous hover item
                self.listbox.itemconfig(self.hover_index, bg=OptimizedDarkTheme.LISTBOX_BG)

            # Set new hover item
            self.hover_index = index
            current_selection = self.listbox.curselection()
            if index not in current_selection:
                self.listbox.itemconfig(index, bg=OptimizedDarkTheme.LISTBOX_HOVER)

    def on_leave(self, event):
        """Handle mouse leave"""
        if self.hover_index is not None:
            current_selection = self.listbox.curselection()
            if self.hover_index not in current_selection:
                self.listbox.itemconfig(self.hover_index, bg=OptimizedDarkTheme.LISTBOX_BG)
            self.hover_index = None

    def pack(self, **kwargs):
        """Pack listbox and scrollbar"""
        self.container.pack(**kwargs)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def grid(self, row, column, **kwargs):
        """Grid listbox and scrollbar"""
        self.container.grid(row=row, column=column, **kwargs)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

class GUIOptimizer:
    """Main GUI optimizer for managing performance across all widgets"""

    def __init__(self, update_interval: float = 0.016):  # 60 FPS
        self.update_interval = update_interval
        self.widgets: List[OptimizedWidget] = []
        self.running = False
        self.metrics = GUIMetrics()

        # Performance tracking
        self.frame_times = deque(maxlen=60)  # Last 60 frames
        self.last_gc_time = time.time()
        self.gc_interval = 10.0  # Garbage collect every 10 seconds

    def register_widget(self, widget: OptimizedWidget):
        """Register widget for optimization"""
        self.widgets.append(widget)

    def unregister_widget(self, widget: OptimizedWidget):
        """Unregister widget"""
        try:
            self.widgets.remove(widget)
        except ValueError:
            pass

    def start_optimization(self, root: tk.Tk):
        """Start GUI optimization loop"""
        self.running = True
        self.root = root
        self._optimization_loop()

    def stop_optimization(self):
        """Stop GUI optimization"""
        self.running = False

    def _optimization_loop(self):
        """Main optimization loop"""
        if not self.running:
            return

        frame_start = time.time()

        # Update all widgets that need updating
        updated_count = 0
        for widget in self.widgets[:]:  # Copy list to avoid modification issues
            try:
                if widget.should_update():
                    widget.update_if_needed()
                    updated_count += 1
            except Exception as e:
                logger.error(f"Widget update error: {e}")
                # Remove problematic widget
                self.unregister_widget(widget)

        # Garbage collection management
        current_time = time.time()
        if current_time - self.last_gc_time > self.gc_interval:
            gc.collect()
            self.last_gc_time = current_time

        # Update metrics
        frame_time = time.time() - frame_start
        self.frame_times.append(frame_time)
        self.metrics.render_time = frame_time
        self.metrics.widget_count = len(self.widgets)

        if len(self.frame_times) > 1:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.metrics.update_frequency = 1.0 / max(avg_frame_time, 0.001)

            # Calculate responsiveness score (based on frame rate)
            target_fps = 60
            actual_fps = self.metrics.update_frequency
            self.metrics.responsiveness_score = min(100, (actual_fps / target_fps) * 100)

        # Schedule next update
        delay = max(1, int(self.update_interval * 1000))  # Convert to milliseconds
        self.root.after(delay, self._optimization_loop)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'frame_rate': self.metrics.update_frequency,
            'avg_frame_time': sum(self.frame_times) / max(len(self.frame_times), 1),
            'widget_count': self.metrics.widget_count,
            'responsiveness_score': self.metrics.responsiveness_score,
            'memory_widgets': len(self.widgets),
            'optimization_running': self.running
        }

    def optimize_memory(self):
        """Perform memory optimization"""
        # Remove widgets that are no longer needed
        active_widgets = []
        for widget in self.widgets:
            try:
                # Check if widget's parent still exists
                if hasattr(widget, 'parent_widget') and widget.parent_widget:
                    active_widgets.append(widget)
                else:
                    widget.cleanup()
            except Exception:
                # Widget is no longer valid
                widget.cleanup()

        self.widgets = active_widgets

        # Force garbage collection
        gc.collect()

        logger.info(f"Memory optimization complete. Active widgets: {len(self.widgets)}")

# Global GUI optimizer instance
gui_optimizer = GUIOptimizer()

# Context manager for widget registration
class OptimizedWidgetContext:
    """Context manager for automatic widget registration"""

    def __init__(self, widget: OptimizedWidget):
        self.widget = widget

    def __enter__(self):
        gui_optimizer.register_widget(self.widget)
        return self.widget

    def __exit__(self, exc_type, exc_val, exc_tb):
        gui_optimizer.unregister_widget(self.widget)
        self.widget.cleanup()

# Utility functions for dark-themed optimized widgets
def create_optimized_progress_bar(parent, theme_style='default', **kwargs) -> OptimizedProgressBar:
    """Create optimized progress bar with dark theme and automatic registration"""
    progress_bar = OptimizedProgressBar(parent, theme_style=theme_style, **kwargs)
    gui_optimizer.register_widget(progress_bar)
    return progress_bar

def create_optimized_text_display(parent, **kwargs) -> OptimizedTextDisplay:
    """Create optimized text display with dark theme and automatic registration"""
    text_display = OptimizedTextDisplay(parent, **kwargs)
    gui_optimizer.register_widget(text_display)
    return text_display

def create_optimized_listbox(parent, **kwargs) -> OptimizedListbox:
    """Create optimized listbox with dark theme and automatic registration"""
    listbox = OptimizedListbox(parent, **kwargs)
    gui_optimizer.register_widget(listbox)
    return listbox

def configure_dark_theme_styles():
    """Configure ttk styles for dark theme across optimized widgets"""
    style = ttk.Style()

    # Use clam theme as base
    style.theme_use('clam')

    # Configure scrollbar for dark theme
    style.configure('Vertical.TScrollbar',
                   background=OptimizedDarkTheme.BG_SECONDARY,
                   troughcolor=OptimizedDarkTheme.BG_PRIMARY,
                   borderwidth=1,
                   arrowcolor=OptimizedDarkTheme.TEXT_SECONDARY,
                   darkcolor=OptimizedDarkTheme.BG_SECONDARY,
                   lightcolor=OptimizedDarkTheme.BG_SECONDARY)

    style.map('Vertical.TScrollbar',
             background=[('active', OptimizedDarkTheme.HOVER_BG),
                       ('pressed', OptimizedDarkTheme.ACTIVE_BG)])

    # Configure progressbar for dark theme
    style.configure('TProgressbar',
                   background=OptimizedDarkTheme.PROGRESS_FILL,
                   troughcolor=OptimizedDarkTheme.PROGRESS_BG,
                   borderwidth=1,
                   lightcolor=OptimizedDarkTheme.PROGRESS_FILL,
                   darkcolor=OptimizedDarkTheme.PROGRESS_FILL)

    return style

def start_gui_optimization(root: tk.Tk, enable_dark_theme: bool = True):
    """Start GUI optimization for root window with optional dark theme"""
    if enable_dark_theme:
        configure_dark_theme_styles()
        root.configure(bg=OptimizedDarkTheme.BG_PRIMARY)

    gui_optimizer.start_optimization(root)

def stop_gui_optimization():
    """Stop GUI optimization"""
    gui_optimizer.stop_optimization()