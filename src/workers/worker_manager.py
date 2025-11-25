"""
Worker Manager - Manages multiple language-specific workers
Can run all language workers or specific ones
"""
import asyncio
import logging
import os
import sys
from typing import List, Dict
from multiprocessing import Process

from workers.code_execution_worker import CodeExecutionWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(processName)s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages multiple code execution workers for different languages"""
    
    SUPPORTED_LANGUAGES = ["python", "java", "nodejs", "cpp"]
    
    def __init__(self, database_url: str):
        """
        Initialize worker manager
        
        Args:
            database_url: PostgreSQL database connection URL
        """
        self.database_url = database_url
        self.workers: Dict[str, Process] = {}
        logger.info("Worker manager initialized")
    
    def start_worker(self, language: str):
        """
        Start a worker for a specific language in a separate process
        
        Args:
            language: Programming language (python, java, nodejs, cpp)
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {language}")
            return
        
        if language in self.workers:
            logger.warning(f"Worker for {language} is already running")
            return
        
        logger.info(f"Starting {language} worker process...")
        
        # Create a separate process for this worker
        process = Process(
            target=self._run_worker,
            args=(language, self.database_url),
            name=f"Worker-{language}"
        )
        process.start()
        self.workers[language] = process
        
        logger.info(f"{language} worker started with PID {process.pid}")
    
    @staticmethod
    def _run_worker(language: str, database_url: str):
        """Run a worker in a separate process"""
        try:
            # Create new event loop for this process
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create and start worker
            worker = CodeExecutionWorker(language, database_url)
            loop.run_until_complete(worker.start())
            
        except Exception as e:
            logger.error(f"Error in {language} worker: {str(e)}", exc_info=True)
    
    def start_all_workers(self):
        """Start workers for all supported languages"""
        logger.info("Starting all language workers...")
        for language in self.SUPPORTED_LANGUAGES:
            self.start_worker(language)
        logger.info(f"All {len(self.SUPPORTED_LANGUAGES)} workers started")
    
    def stop_worker(self, language: str):
        """Stop a specific language worker"""
        if language not in self.workers:
            logger.warning(f"No worker found for {language}")
            return
        
        logger.info(f"Stopping {language} worker...")
        process = self.workers[language]
        process.terminate()
        process.join(timeout=10)
        
        if process.is_alive():
            logger.warning(f"{language} worker did not terminate, killing...")
            process.kill()
            process.join()
        
        del self.workers[language]
        logger.info(f"{language} worker stopped")
    
    def stop_all_workers(self):
        """Stop all running workers"""
        logger.info("Stopping all workers...")
        languages = list(self.workers.keys())
        for language in languages:
            self.stop_worker(language)
        logger.info("All workers stopped")
    
    def get_worker_status(self) -> Dict[str, str]:
        """Get the status of all workers"""
        status = {}
        for language in self.SUPPORTED_LANGUAGES:
            if language in self.workers:
                process = self.workers[language]
                status[language] = "running" if process.is_alive() else "dead"
            else:
                status[language] = "not_started"
        return status
    
    def monitor_workers(self):
        """Monitor workers and restart if they die"""
        logger.info("Monitoring workers...")
        while True:
            try:
                for language, process in list(self.workers.items()):
                    if not process.is_alive():
                        logger.error(f"{language} worker died, restarting...")
                        del self.workers[language]
                        self.start_worker(language)
                
                import time
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted, stopping all workers...")
                self.stop_all_workers()
                break
            except Exception as e:
                logger.error(f"Error in monitor: {str(e)}", exc_info=True)


def main():
    """Main entry point for worker manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Execution Worker Manager")
    parser.add_argument(
        "--languages",
        nargs="+",
        choices=["python", "java", "nodejs", "cpp", "all"],
        default=["all"],
        help="Languages to start workers for"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/online_judge"
        ),
        help="PostgreSQL database URL"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor and auto-restart workers"
    )
    
    args = parser.parse_args()
    
    # Create worker manager
    manager = WorkerManager(args.database_url)
    
    try:
        # Start workers
        if "all" in args.languages:
            manager.start_all_workers()
        else:
            for language in args.languages:
                manager.start_worker(language)
        
        # Monitor if requested
        if args.monitor:
            manager.monitor_workers()
        else:
            # Just wait for keyboard interrupt
            logger.info("Workers started. Press Ctrl+C to stop.")
            import time
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        manager.stop_all_workers()
        logger.info("Worker manager stopped")


if __name__ == "__main__":
    main()

