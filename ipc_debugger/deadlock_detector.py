"""
Deadlock detection functionality for IPC Debugger.
"""

import time
import threading
import random
from queue import Queue, Full as QueueFull

class DeadlockDetector:
    def __init__(self):
        self.resources = {}  # Resource ID -> {owner, waiters, state}
        self.processes = {}  # Process ID -> {owns, waiting_for}
        self.log_queue = Queue(maxsize=1000)  # Limit to 1000 log entries
        self._running = False
        self._lock = threading.Lock()
        self.nx = None
        try:
            import networkx as nx
            self._has_networkx = True
            self.nx = nx
        except ImportError:
            self._has_networkx = False
    
    def start_monitoring(self):
        """Start monitoring for deadlocks"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_deadlocks)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring for deadlocks"""
        if not self._running:
            return  # Already stopped
            
        self._running = False
        
        if hasattr(self, '_monitor_thread'):
            try:
                # Give thread time to terminate gracefully
                self._monitor_thread.join(2.0)
                
                # Log if thread didn't terminate
                if self._monitor_thread.is_alive():
                    self._log_event({
                        'time': time.time(),
                        'action': 'warning',
                        'message': 'Monitor thread did not terminate cleanly'
                    })
            except Exception as e:
                # Log any errors during thread termination
                self._log_event({
                    'time': time.time(),
                    'action': 'error',
                    'message': f'Error terminating monitor thread: {str(e)}'
                })
    
    def _monitor_deadlocks(self):
        """Periodically check for deadlocks"""
        while self._running:
            time.sleep(0.5)
            
            # Grab a snapshot of the current state under the lock
            with self._lock:
                # Create a deep copy of necessary data to detect deadlocks
                resources_copy = {}
                for r_id, r_info in self.resources.items():
                    resources_copy[r_id] = {
                        'owner': r_info['owner'],
                        'waiters': r_info['waiters'].copy(),
                        'state': r_info['state']
                    }
                
                processes_copy = {}
                for p_id, p_info in self.processes.items():
                    processes_copy[p_id] = {
                        'owns': p_info['owns'].copy(),
                        'waiting_for': p_info['waiting_for']
                    }
            
            # Perform deadlock detection on the copied data
            deadlocks = self._detect_deadlocks_from_snapshot(resources_copy, processes_copy)
            
            # Log any detected deadlocks
            if deadlocks:
                with self._lock:
                    for cycle in deadlocks:
                        self._log_event({
                            'time': time.time(),
                            'action': 'deadlock_detected',
                            'processes': cycle
                        })
    
    def _detect_deadlocks_from_snapshot(self, resources, processes):
        """Detect deadlocks using a snapshot of resources and processes"""
        # For multi-instance resources, we need to implement the Banker's Algorithm
        # First, check if we can satisfy all waiting processes
        
        # Build allocation matrix, max matrix, and available resources vector
        resource_ids = list(resources.keys())
        process_ids = list(processes.keys())
        
        if not resource_ids or not process_ids:
            return []  # No resources or processes to check
        
        # Create allocation matrix (what each process currently has)
        allocation = {}
        for p_id in process_ids:
            allocation[p_id] = {}
            for r_id in resource_ids:
                if r_id in resources and p_id in resources[r_id]['allocations']:
                    allocation[p_id][r_id] = resources[r_id]['allocations'][p_id]
                else:
                    allocation[p_id][r_id] = 0
        
        # Create need matrix (what each process might still need)
        need = {}
        for p_id in process_ids:
            need[p_id] = {}
            for r_id in resource_ids:
                if processes[p_id]['waiting_for'] == r_id and p_id in resources[r_id]['waiting_for']:
                    need[p_id][r_id] = resources[r_id]['waiting_for'][p_id]
                else:
                    need[p_id][r_id] = 0
        
        # Available resources vector
        available = {}
        for r_id in resource_ids:
            available[r_id] = resources[r_id]['available_instances']
        
        # Build wait-for graph for processes that are definitely waiting
        wait_for = {}
        for p_id, process in processes.items():
            if process['waiting_for'] is not None:
                wait_resource = process['waiting_for']
                
                # Check if this resource is allocated to any process
                allocating_processes = []
                for other_p_id, other_p in processes.items():
                    if wait_resource in other_p['owns'] and other_p_id != p_id:
                        # This process has some of the resource we need
                        allocating_processes.append(other_p_id)
                
                if allocating_processes:
                    if p_id not in wait_for:
                        wait_for[p_id] = []
                    wait_for[p_id].extend(allocating_processes)
        
        # Check if we can use networkx for cycle detection
        if self._has_networkx and self.nx:
            # Use networkx for cycle detection
            G = self.nx.DiGraph()
            
            # Add all processes as nodes
            for process_id in processes:
                G.add_node(process_id)
            
            # Add edges for wait relationships
            for process_id, neighbors in wait_for.items():
                for neighbor in neighbors:
                    G.add_edge(process_id, neighbor)
            
            try:
                # For large graphs, simple_cycles can be expensive, so we use a timeout
                deadlocks = list(self.nx.simple_cycles(G))
                return deadlocks
            except Exception:
                # Fallback to simple detection on any error
                pass
        
        # Simple cycle detection using DFS (as a fallback)
        deadlocks = []
        
        def find_cycle(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            if node in wait_for:
                for neighbor in wait_for[node]:
                    cycle = find_cycle(neighbor, path, visited)
                    if cycle:
                        return cycle
            
            path.pop()
            return None
        
        # Check each process as a potential starting point
        for process_id in processes:
            visited = set()
            cycle = find_cycle(process_id, [], visited)
            if cycle:
                deadlocks.append(cycle)
        
        return deadlocks
    
    def register_resource(self, resource_id, resource_type='lock', instances=1):
        """Register a resource for deadlock tracking with multiple instances"""
        if instances <= 0:
            raise ValueError("Number of instances must be positive")
            
        with self._lock:
            if resource_id in self.resources:
                return False
            
            self.resources[resource_id] = {
                'type': resource_type,
                'total_instances': instances,
                'available_instances': instances,
                'allocations': {},  # Process ID -> number of instances allocated
                'waiters': [],
                'waiter_timestamps': {},  # Track when processes started waiting
                'waiting_for': {},  # Process ID -> number of instances requested
                'state': 'free'
            }
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_registered',
                'resource_id': resource_id,
                'resource_type': resource_type,
                'instances': instances
            })
            
            return True
    
    def register_process(self, process_id):
        """Register a process for deadlock tracking"""
        with self._lock:
            if process_id in self.processes:
                return False
            
            self.processes[process_id] = {
                'owns': [],
                'waiting_for': None
            }
            
            self._log_event({
                'time': time.time(),
                'action': 'process_registered',
                'process_id': process_id
            })
            
            return True
    
    def request_resource(self, process_id, resource_id, instances=1):
        """Track a process requesting multiple instances of a resource"""
        if instances <= 0:
            raise ValueError("Number of instances requested must be positive")
            
        with self._lock:
            if process_id not in self.processes or resource_id not in self.resources:
                return False
            
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Process can't request a resource if it's already waiting for something else
            if process['waiting_for'] is not None:
                return False
            
            # If resource has enough available instances, allocate them
            if resource['available_instances'] >= instances:
                # Update process's owned resources
                if resource_id not in process['owns']:
                    process['owns'].append(resource_id)
                
                # Update resource allocation
                current_allocation = resource['allocations'].get(process_id, 0)
                resource['allocations'][process_id] = current_allocation + instances
                resource['available_instances'] -= instances
                
                # Update resource state
                if resource['available_instances'] == 0:
                    resource['state'] = 'fully_allocated'
                else:
                    resource['state'] = 'partially_allocated'
                
                self._log_event({
                    'time': time.time(),
                    'action': 'resource_acquired',
                    'resource_id': resource_id,
                    'process_id': process_id,
                    'instances': instances
                })
                
                return True
            else:
                # Not enough available instances, add process to waiters
                if process_id not in resource['waiters']:
                    resource['waiters'].append(process_id)
                    # Record when process started waiting
                    resource['waiter_timestamps'][process_id] = time.time()
                    # Record how many instances the process is waiting for
                    resource['waiting_for'][process_id] = instances
                
                # Mark that this process is waiting for this resource
                process['waiting_for'] = resource_id
                
                self._log_event({
                    'time': time.time(),
                    'action': 'resource_waiting',
                    'resource_id': resource_id,
                    'process_id': process_id,
                    'instances_requested': instances,
                    'instances_available': resource['available_instances']
                })
                
                return False
    
    def release_resource(self, process_id, resource_id, instances=None):
        """Track a process releasing multiple instances of a resource"""
        with self._lock:
            if process_id not in self.processes or resource_id not in self.resources:
                return False
            
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Check if process holds this resource
            if resource_id not in process['owns']:
                return False
                
            # Get current allocation
            current_allocation = resource['allocations'].get(process_id, 0)
            if current_allocation == 0:
                return False
            
            # If instances is None or greater than allocated, release all
            if instances is None or instances >= current_allocation:
                instances_to_release = current_allocation
            else:
                instances_to_release = instances
            
            # Release the specified number of instances
            resource['allocations'][process_id] = current_allocation - instances_to_release
            resource['available_instances'] += instances_to_release
            
            # If process no longer holds any instances, remove from owns list
            if resource['allocations'][process_id] == 0:
                del resource['allocations'][process_id]
                process['owns'].remove(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_released',
                'resource_id': resource_id,
                'process_id': process_id,
                'instances_released': instances_to_release,
                'instances_now_available': resource['available_instances']
            })
            
            # Check if we can satisfy any waiting processes
            if resource['waiters']:
                # Try to satisfy waiters in order of arrival (FIFO)
                for waiter_id in list(resource['waiters']):
                    if waiter_id in self.processes:
                        wait_process = self.processes[waiter_id]
                        if wait_process['waiting_for'] == resource_id:
                            instances_needed = resource['waiting_for'].get(waiter_id, 1)
                            
                            # If we have enough instances available
                            if resource['available_instances'] >= instances_needed:
                                # Remove from waiters
                                resource['waiters'].remove(waiter_id)
                                if waiter_id in resource['waiter_timestamps']:
                                    del resource['waiter_timestamps'][waiter_id]
                                if waiter_id in resource['waiting_for']:
                                    del resource['waiting_for'][waiter_id]
                                
                                # Allocate instances
                                resource['allocations'][waiter_id] = instances_needed
                                resource['available_instances'] -= instances_needed
                                
                                # Update process status
                                if resource_id not in wait_process['owns']:
                                    wait_process['owns'].append(resource_id)
                                wait_process['waiting_for'] = None
                                
                                wait_time = 0
                                if waiter_id in resource['waiter_timestamps']:
                                    wait_time = time.time() - resource['waiter_timestamps'][waiter_id]
                                
                                self._log_event({
                                    'time': time.time(),
                                    'action': 'resource_acquired_after_wait',
                                    'resource_id': resource_id,
                                    'process_id': waiter_id,
                                    'instances': instances_needed,
                                    'wait_time': wait_time
                                })
                                
                                # Stop after satisfying one waiter (can be changed for different policies)
                                break
            
            # Update resource state
            if resource['available_instances'] == resource['total_instances']:
                resource['state'] = 'free'
            elif resource['available_instances'] == 0:
                resource['state'] = 'fully_allocated'
            else:
                resource['state'] = 'partially_allocated'
            
            return True
    
    def detect_deadlocks(self):
        """Detect deadlocks using wait-for graph analysis"""
        with self._lock:
            return self._detect_deadlocks_from_snapshot(self.resources, self.processes)
    
    def get_resource_status(self):
        """Get status information about resources"""
        with self._lock:
            return {r_id: {
                'type': r_info['type'],
                'state': r_info['state'],
                'owner': r_info.get('owner', None),
                'waiters': r_info.get('waiters', []).copy(),
                'total_instances': r_info.get('total_instances', 1),
                'available_instances': r_info.get('available_instances', 0),
                'allocations': r_info.get('allocations', {}).copy()
            } for r_id, r_info in self.resources.items()}
    
    def get_process_status(self):
        """Get status information about processes"""
        with self._lock:
            return {p_id: {
                'owns': p_info['owns'].copy(),
                'waiting_for': p_info['waiting_for']
            } for p_id, p_info in self.processes.items()}
    
    def get_logs(self):
        """Get all log entries"""
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())
        return logs
    
    def get_log_entries(self):
        """Get formatted log entries for UI display"""
        logs = []
        raw_logs = self.get_logs()  # This empties the queue, so we need to work with the returned logs
        for entry in raw_logs:
            # Determine if this is process or resource related
            if 'process_id' in entry:
                component_id = f"deadlock_process_{entry.get('process_id', 'unknown')}"
            elif 'resource_id' in entry:
                component_id = f"deadlock_resource_{entry.get('resource_id', 'unknown')}"
            else:
                component_id = "deadlock_detector"
                
            logs.append({
                'timestamp': entry.get('time', 0),
                'component_id': component_id,
                'message': entry.get('message', entry.get('action', 'unknown action'))
            })
        return logs
    
    def add_log_entry(self, component_id, message):
        """Add a custom log entry"""
        self._log_event({
            'time': time.time(),
            'action': 'info',
            'message': message,
            'component': component_id
        })
    
    def simulate_deadlock(self, num_processes=3, num_resources=3, timeout=10):
        """Simulate a deadlock scenario"""
        # Register processes and resources
        processes = [f"sim_process_{i}" for i in range(num_processes)]
        resources = [f"sim_resource_{i}" for i in range(num_resources)]
        
        with self._lock:
            for process_id in processes:
                self.register_process(process_id)
            
            for resource_id in resources:
                self.register_resource(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'deadlock_simulation_started',
                'processes': processes,
                'resources': resources
            })
        
        # Start simulation in a separate thread
        def _simulate():
            # First, have each process acquire one resource in order
            for i, process_id in enumerate(processes):
                resource_id = resources[i % num_resources]
                self.request_resource(process_id, resource_id)
                time.sleep(0.1)
            
            # Then, have each try to acquire the next resource, creating a circle
            for i, process_id in enumerate(processes):
                next_resource = resources[(i + 1) % num_resources]
                self.request_resource(process_id, next_resource)
                time.sleep(0.1)
            
            # Wait for detection
            time.sleep(timeout)
            
            # Release resources to resolve deadlock
            for i, process_id in enumerate(processes):
                resource_id = resources[i % num_resources]
                self.release_resource(process_id, resource_id)
            
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'action': 'deadlock_simulation_ended'
                })
        
        threading.Thread(target=_simulate).start()
        return {
            'processes': processes,
            'resources': resources
        }

    def _log_event(self, event):
        """Add an event to the log queue, dropping oldest if full"""
        try:
            self.log_queue.put_nowait(event)
        except QueueFull:
            # Queue is full, remove oldest entry and add new one
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(event)
            except:
                # If any error occurs, just ignore this log entry
                pass

    def unregister_process(self, process_id):
        """Unregister and cleanup a process from deadlock tracking"""
        with self._lock:
            if process_id not in self.processes:
                return False
            
            # Get the resources owned by this process
            owned_resources = self.processes[process_id]['owns'].copy()
            
            # Release all resources owned by this process
            for resource_id in owned_resources:
                if resource_id in self.resources:
                    resource = self.resources[resource_id]
                    # For multi-instance resources, release all instances owned by this process
                    if process_id in resource.get('allocations', {}):
                        instances_released = resource['allocations'][process_id]
                        resource['available_instances'] += instances_released
                        del resource['allocations'][process_id]
                        
                        # Update resource state based on available instances
                        if resource['available_instances'] == resource['total_instances']:
                            resource['state'] = 'free'
                        elif resource['available_instances'] == 0:
                            resource['state'] = 'fully_allocated'
                        else:
                            resource['state'] = 'partially_allocated'
                            
                        # Check if we can satisfy any waiting processes
                        if resource['waiters']:
                            # Try to satisfy waiters in order of arrival (FIFO)
                            for waiter_id in list(resource['waiters']):
                                if waiter_id in self.processes:
                                    wait_process = self.processes[waiter_id]
                                    if wait_process['waiting_for'] == resource_id:
                                        instances_needed = resource['waiting_for'].get(waiter_id, 1)
                                        
                                        # If we have enough instances available
                                        if resource['available_instances'] >= instances_needed:
                                            # Remove from waiters
                                            resource['waiters'].remove(waiter_id)
                                            if waiter_id in resource['waiter_timestamps']:
                                                del resource['waiter_timestamps'][waiter_id]
                                            if waiter_id in resource['waiting_for']:
                                                del resource['waiting_for'][waiter_id]
                                            
                                            # Allocate instances
                                            resource['allocations'][waiter_id] = instances_needed
                                            resource['available_instances'] -= instances_needed
                                            
                                            # Update process status
                                            if resource_id not in wait_process['owns']:
                                                wait_process['owns'].append(resource_id)
                                            wait_process['waiting_for'] = None
                                            
                                            self._log_event({
                                                'time': time.time(),
                                                'action': 'resource_acquired_after_process_unregister',
                                                'resource_id': resource_id,
                                                'process_id': waiter_id,
                                                'instances': instances_needed,
                                                'previous_owner': process_id
                                            })
                                            
                                            # Stop after satisfying one waiter (can be changed for different policies)
                                            break
                        
                        self._log_event({
                            'time': time.time(),
                            'action': 'resource_force_released',
                            'resource_id': resource_id,
                            'process_id': process_id,
                            'instances_released': instances_released
                        })
                    elif resource.get('owner') == process_id:
                        # Handle legacy single-instance resources
                        resource['owner'] = None
                        resource['state'] = 'free'
                        
                        # Handle waiters for single-instance resources
                        if resource['waiters']:
                            next_process_id = resource['waiters'][0]
                            oldest_wait_time = resource['waiter_timestamps'].get(next_process_id, time.time())
                            
                            # Find the process that's been waiting longest
                            for waiter_id, timestamp in resource['waiter_timestamps'].items():
                                if timestamp < oldest_wait_time:
                                    oldest_wait_time = timestamp
                                    next_process_id = waiter_id
                            
                            if next_process_id in self.processes:
                                # Remove from waiters list
                                resource['waiters'].remove(next_process_id)
                                if next_process_id in resource['waiter_timestamps']:
                                    del resource['waiter_timestamps'][next_process_id]
                                
                                # Assign resource
                                next_process = self.processes[next_process_id]
                                resource['state'] = 'owned'
                                resource['owner'] = next_process_id
                                next_process['owns'].append(resource_id)
                                next_process['waiting_for'] = None
                                
                                self._log_event({
                                    'time': time.time(),
                                    'action': 'resource_reassigned',
                                    'resource_id': resource_id,
                                    'process_id': next_process_id,
                                    'previous_owner': process_id
                                })
                        
                        self._log_event({
                            'time': time.time(),
                            'action': 'resource_force_released',
                            'resource_id': resource_id,
                            'process_id': process_id
                        })
            
            # Remove any entries where this process is waiting for a resource
            for resource_id, resource in self.resources.items():
                if process_id in resource['waiters']:
                    resource['waiters'].remove(process_id)
                    if process_id in resource['waiter_timestamps']:
                        del resource['waiter_timestamps'][process_id]
                    if process_id in resource.get('waiting_for', {}):
                        del resource['waiting_for'][process_id]
            
            # Remove the process
            del self.processes[process_id]
            
            self._log_event({
                'time': time.time(),
                'action': 'process_unregistered',
                'process_id': process_id
            })
            
            return True
    
    def set_resource_owner(self, resource_id, process_id, instances=1):
        """Set a process as the owner of a resource (with specified instances)"""
        with self._lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False
                
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # For multi-instance resources
            if 'allocations' in resource:
                # Check if there are enough instances available
                if resource['available_instances'] < instances:
                    return False
                
                # Update allocation
                current_allocation = resource['allocations'].get(process_id, 0)
                resource['allocations'][process_id] = current_allocation + instances
                resource['available_instances'] -= instances
                
                # Update state
                if resource['available_instances'] == 0:
                    resource['state'] = 'fully_allocated'
                else:
                    resource['state'] = 'partially_allocated'
            else:
                # For single-instance resources (legacy)
                # Check if resource is already owned
                if resource['state'] == 'owned' and resource['owner'] is not None:
                    # Release from previous owner
                    prev_owner = resource['owner']
                    if prev_owner in self.processes:
                        self.processes[prev_owner]['owns'].remove(resource_id)
                
                # Set new owner
                resource['state'] = 'owned'
                resource['owner'] = process_id
            
            # Add to process's owned resources if not already there
            if resource_id not in process['owns']:
                process['owns'].append(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_owner_set',
                'resource_id': resource_id,
                'process_id': process_id,
                'instances': instances
            })
            
            return True
    
    def add_waiting_process(self, resource_id, process_id):
        """Add a process to the waiters list for a resource"""
        with self._lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False
                
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Add to waiters if not already waiting
            if process_id not in resource['waiters']:
                resource['waiters'].append(process_id)
                resource['waiter_timestamps'][process_id] = time.time()
            
            # Set process waiting_for
            process['waiting_for'] = resource_id
            
            self._log_event({
                'time': time.time(),
                'action': 'process_waiting',
                'resource_id': resource_id,
                'process_id': process_id
            })
            
            return True
    
    def clear_all(self):
        """Clear all resources and processes from the deadlock detector"""
        with self._lock:
            self.resources = {}
            self.processes = {}
            
            self._log_event({
                'time': time.time(),
                'action': 'system_cleared',
                'message': 'All resources and processes cleared'
            })
            
            return True 