"""
Reliability Layer
Implements ACK, retransmission, and sequence number management for UDP.
"""
import time
import threading
from typing import Dict, Optional, Callable
from collections import deque


class PendingMessage:
    """Represents a message waiting for acknowledgment."""
    
    def __init__(self, message: bytes, sequence_number: int, 
                 retry_callback: Callable, max_retries: int = 3, 
                 timeout: float = 0.5):
        self.message = message
        self.sequence_number = sequence_number
        self.retry_callback = retry_callback
        self.max_retries = max_retries
        self.timeout = timeout
        self.retries = 0
        self.sent_time = time.time()
        self.acked = False


class ReliabilityLayer:
    """Manages reliable message delivery over UDP."""
    
    def __init__(self, send_callback: Callable[[bytes], None], 
                 max_retries: int = 3, timeout: float = 0.5):
        """
        Initialize reliability layer.
        
        Args:
            send_callback: Function to call when sending a message
            max_retries: Maximum number of retransmission attempts
            timeout: Timeout in seconds before retransmission
        """
        self.send_callback = send_callback
        self.max_retries = max_retries
        self.timeout = timeout
        self.pending_messages: Dict[int, PendingMessage] = {}
        self.sequence_number = 0
        self.received_sequences = set()
        self.running = False
        self.lock = threading.Lock()
        self.retry_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the reliability layer background thread."""
        self.running = True
        self.retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self.retry_thread.start()
    
    def stop(self):
        """Stop the reliability layer."""
        self.running = False
        if self.retry_thread:
            self.retry_thread.join(timeout=1.0)
    
    def get_next_sequence_number(self) -> int:
        """Get the next sequence number."""
        with self.lock:
            self.sequence_number += 1
            return self.sequence_number
    
    def send_message(self, message: bytes, sequence_number: Optional[int] = None) -> int:
        """
        Send a message with reliability guarantees.
        
        Returns:
            The sequence number assigned to the message
        """
        if sequence_number is None:
            sequence_number = self.get_next_sequence_number()
        
        pending = PendingMessage(
            message, sequence_number, self.send_callback,
            self.max_retries, self.timeout
        )
        
        with self.lock:
            self.pending_messages[sequence_number] = pending
        
        # Send the message
        self.send_callback(message)
        pending.sent_time = time.time()
        
        return sequence_number
    
    def handle_ack(self, ack_number: int):
        """Handle an acknowledgment for a sequence number."""
        with self.lock:
            if ack_number in self.pending_messages:
                self.pending_messages[ack_number].acked = True
                del self.pending_messages[ack_number]
    
    def is_duplicate(self, sequence_number: int) -> bool:
        """Check if a sequence number has already been received."""
        with self.lock:
            if sequence_number in self.received_sequences:
                return True
            self.received_sequences.add(sequence_number)
            return False
    
    def _retry_loop(self):
        """Background thread that retries unacknowledged messages."""
        while self.running:
            current_time = time.time()
            to_retry = []
            
            with self.lock:
                for seq_num, pending in list(self.pending_messages.items()):
                    if pending.acked:
                        continue
                    
                    elapsed = current_time - pending.sent_time
                    if elapsed >= pending.timeout:
                        if pending.retries < pending.max_retries:
                            to_retry.append(pending)
                        else:
                            # Max retries reached, remove from pending
                            del self.pending_messages[seq_num]
            
            # Retry messages outside the lock
            for pending in to_retry:
                pending.retries += 1
                pending.sent_time = current_time
                pending.retry_callback(pending.message)
            
            time.sleep(0.1)  # Check every 100ms

