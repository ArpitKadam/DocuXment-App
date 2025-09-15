# OPTIMIZED logger.py - HackRx 6.0 Competition Version

import os
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import threading

# --- Competition-Optimized Logging Configuration ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class Logger:
    """
    High-performance logger optimized for app.
    Features: Performance tracking, error monitoring, and competition metrics
    """
    
    def __init__(self):
        self.logger = None
        self.performance_metrics = {
            "total_requests": 0,
            "error_count": 0,
            "warning_count": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "session_start": datetime.now()
        }
        self.lock = threading.Lock()
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup multi-level logging with performance optimization"""
        
        # Create timestamped log file for this session
        session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Main log file
        main_log_file = os.path.join(LOG_DIR, f"{session_timestamp}_main.log")
        
        # Error-only log file for quick debugging
        error_log_file = os.path.join(LOG_DIR, f"{session_timestamp}_errors.log")
        
        # Performance metrics log
        metrics_log_file = os.path.join(LOG_DIR, f"{session_timestamp}_metrics.log")
        
        # Create logger instance
        self.logger = logging.getLogger("Logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # --- MAIN LOG HANDLER (All levels) ---
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=50*1024*1024,  # 50MB max file size
            backupCount=3,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)-15s | %(funcName)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        main_handler.setFormatter(main_formatter)
        
        # --- ERROR-ONLY HANDLER (Critical debugging) ---
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB max
            backupCount=2,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s | 🚨 ERROR | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        
        # --- PERFORMANCE METRICS HANDLER ---
        metrics_handler = RotatingFileHandler(
            metrics_log_file,
            maxBytes=5*1024*1024,   # 5MB max
            backupCount=1,
            encoding='utf-8'
        )
        metrics_handler.setLevel(logging.INFO)
        
        class MetricsFilter(logging.Filter):
            def filter(self, record):
                return hasattr(record, 'metric_type')
        
        metrics_handler.addFilter(MetricsFilter())
        metrics_formatter = logging.Formatter(
            '%(asctime)s | METRIC | %(message)s',
            datefmt='%H:%M:%S'
        )
        metrics_handler.setFormatter(metrics_formatter)

        # --- CONSOLE HANDLER ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            ' %(levelname)-8s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add all handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(metrics_handler)
        self.logger.addHandler(console_handler)
        
        # Log session start
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 SESSION STARTED")
        self.logger.info(f"📁 Main Log: {main_log_file}")
        self.logger.info(f"🚨 Error Log: {error_log_file}")
        self.logger.info(f"📊 Metrics Log: {metrics_log_file}")
        self.logger.info("=" * 80)
    
    def log_request_start(self, request_id, question_count, model_name):
        """Log the start of a request"""
        with self.lock:
            self.performance_metrics["total_requests"] += 1
        
        self.logger.info(f"🔥 REQUEST START | ID: {request_id} | Questions: {question_count} | Model: {model_name}")
    
    def log_request_end(self, request_id, total_time, question_count, cache_hits=0):
        """Log the completion of a request with performance metrics"""
        with self.lock:
            # Update performance metrics
            current_avg = self.performance_metrics["avg_response_time"]
            total_requests = self.performance_metrics["total_requests"]
            
            # Calculate new average
            self.performance_metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + total_time) / total_requests
            )
            self.performance_metrics["cache_hits"] += cache_hits
        
        avg_per_question = total_time / question_count if question_count > 0 else 0
        
        # Log to main log
        self.logger.info(f"✅ REQUEST END | ID: {request_id} | Total: {total_time:.2f}s | Avg/Q: {avg_per_question:.2f}s | Cache: {cache_hits}")
        
        # Log performance metric
        metric_record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"RESPONSE_TIME:{total_time:.3f},AVG_PER_QUESTION:{avg_per_question:.3f},CACHE_HITS:{cache_hits},TOTAL_QUESTIONS:{question_count}",
            args=(),
            exc_info=None
        )
        metric_record.metric_type = "performance"
        self.logger.handle(metric_record)
    
    def log_cache_hit(self, question_preview):
        """Log cache hit for performance tracking"""
        self.logger.debug(f"💾 CACHE HIT: {question_preview}")
    
    def log_model_response(self, question_preview, response_time, complexity="medium"):
        """Log individual model response"""
        self.logger.debug(f"🤖 MODEL RESPONSE | {complexity.upper()} | {response_time:.2f}s | {question_preview}")
    
    def log_error_with_context(self, error_msg, context=None):
        """Log error with additional context for debugging"""
        with self.lock:
            self.performance_metrics["error_count"] += 1
        
        error_details = f"❌ {error_msg}"
        if context:
            error_details += f" | Context: {context}"
        
        self.logger.error(error_details)
    
    def log_warning_with_context(self, warning_msg, context=None):
        """Log warning with context"""
        with self.lock:
            self.performance_metrics["warning_count"] += 1
        
        warning_details = f"⚠️ {warning_msg}"
        if context:
            warning_details += f" | Context: {context}"
        
        self.logger.warning(warning_details)
    
    def log_competition_metrics(self):
        """Log current competition performance metrics"""
        with self.lock:
            metrics = self.performance_metrics.copy()
            uptime = (datetime.now() - metrics["session_start"]).total_seconds() / 60
        
        metrics_summary = (
            f"📊 COMPETITION METRICS | "
            f"Requests: {metrics['total_requests']} | "
            f"Avg Response: {metrics['avg_response_time']:.2f}s | "
            f"Cache Hits: {metrics['cache_hits']} | "
            f"Errors: {metrics['error_count']} | "
            f"Uptime: {uptime:.1f}min"
        )
        
        self.logger.info(metrics_summary)
        
        # Log detailed metrics
        metric_record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"TOTAL_REQUESTS:{metrics['total_requests']},AVG_RESPONSE_TIME:{metrics['avg_response_time']:.3f},CACHE_HITS:{metrics['cache_hits']},ERROR_COUNT:{metrics['error_count']},WARNING_COUNT:{metrics['warning_count']},UPTIME_MINUTES:{uptime:.1f}",
            args=(),
            exc_info=None
        )
        metric_record.metric_type = "summary"
        self.logger.handle(metric_record)
        
        return metrics
    
    def get_performance_summary(self):
        """Get current performance metrics for API endpoints"""
        with self.lock:
            metrics = self.performance_metrics.copy()
            uptime = (datetime.now() - metrics["session_start"]).total_seconds()
            
            return {
                "total_requests": metrics["total_requests"],
                "avg_response_time": round(metrics["avg_response_time"], 3),
                "cache_hits": metrics["cache_hits"],
                "error_count": metrics["error_count"],
                "warning_count": metrics["warning_count"],
                "uptime_seconds": round(uptime, 1),
                "requests_per_minute": round(metrics["total_requests"] / max(uptime / 60, 1), 2),
                "cache_hit_rate": round(metrics["cache_hits"] / max(metrics["total_requests"], 1), 3) if metrics["total_requests"] > 0 else 0.0
            }
    
    # Convenience methods for backward compatibility
    def info(self, msg):
        self.logger.info(msg)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def warning(self, msg):
        with self.lock:
            self.performance_metrics["warning_count"] += 1
        self.logger.warning(f"⚠️ {msg}")
    
    def error(self, msg, exc_info=False):
        with self.lock:
            self.performance_metrics["error_count"] += 1
        self.logger.error(f"❌ {msg}", exc_info=exc_info)
    
    def critical(self, msg):
        self.logger.critical(f"🔥 CRITICAL: {msg}")

# Initialize the logger instance
logger = Logger()

# Session-specific logging functions
def log_start():
    """Log the start of session"""
    logger.log_competition_metrics()

def log_request(request_id, question_count, model_name):
    """Log API request start"""
    logger.log_request_start(request_id, question_count, model_name)

def log_response(request_id, total_time, question_count, cache_hits=0):
    """Log API response completion"""
    logger.log_request_end(request_id, total_time, question_count, cache_hits)

def get_performance_metrics():
    """Get current performance metrics"""
    return logger.get_performance_summary()

# Auto-log session start
log_start()