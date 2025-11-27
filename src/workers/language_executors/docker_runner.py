"""
Docker-based code execution runner
Provides secure, isolated execution of code in Docker containers
"""
import asyncio
import tempfile
import os
import shutil
import uuid
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DockerRunner:
    """Manages Docker container execution for code submissions"""
    
    # Docker images for each language
    IMAGES = {
        "python": "python:3.11-slim",
        "java": "eclipse-temurin:17-jdk",  
        "nodejs": "node:18-slim",
        "cpp": "gcc:latest"
    }
    
    def __init__(self, network: Optional[str] = None):
        """
        Initialize Docker runner
        
        Args:
            network: Docker network name to use (default: None for isolated execution)
                    Use None for security isolation, or specify a network if needed
        """
        # Use 'none' network for security isolation (no network access)
        # Code execution containers don't need network access
        self.network = network or "none"
    
    async def run_code(
        self,
        language: str,
        code: str,
        input_data: str,
        time_limit_ms: int,
        memory_limit_mb: int,
        compile_first: bool = False
    ) -> Dict[str, Any]:
        """
        Execute code in a Docker container
        
        Args:
            language: Programming language (python, java, nodejs, cpp)
            code: Source code to execute
            input_data: Input data for the program
            time_limit_ms: Time limit in milliseconds
            memory_limit_mb: Memory limit in MB
            compile_first: Whether to compile before execution (for Java, C++)
            
        Returns:
            Dictionary with:
                - success: bool
                - output: str
                - error: str
                - exit_code: int
                - execution_time_ms: int
                - memory_used_mb: int (if available)
        """
        container_name = None
        temp_dir = None
        
        try:
            # Get Docker image
            image = self.IMAGES.get(language.lower())
            if not image:
                raise ValueError(f"Unsupported language: {language}")
            
            # Create container name
            container_name = f"code_exec_{uuid.uuid4().hex[:12]}"
            
            # Get filename
            filename = self._get_code_filename(language)  # e.g., "Solution.java"
            file_stem = Path(filename).stem  # e.g., "Solution"
            
            # Encode code and input as base64 to safely pass through shell
            import base64
            code_b64 = base64.b64encode(code.encode('utf-8')).decode('ascii')
            input_b64 = base64.b64encode(input_data.encode('utf-8')).decode('ascii') if input_data.strip() else ""
            
            # Build command to write files and execute using base64 decode
            # Write code file using base64 decode
            write_code_cmd = f"echo '{code_b64}' | base64 -d > /workspace/{filename}"
            
            # Write input file if needed
            if input_data.strip():
                write_input_cmd = f"echo '{input_b64}' | base64 -d > /workspace/input.txt"
            else:
                write_input_cmd = "touch /workspace/input.txt"
            
            # Build execution command
            if compile_first:
                # For compiled languages, compile first then run
                compile_cmd = self._get_compile_command(language, filename)
                # Only run if we have input data (for compilation-only checks, input_data will be empty)
                if input_data.strip():
                    run_cmd = self._get_run_command(language, file_stem)  # e.g., "Solution" (without .java)
                    # Chain commands with && and proper escaping
                    full_cmd = f"{write_code_cmd} && {write_input_cmd} && {compile_cmd} && {run_cmd}"
                else:
                    # Compilation only (no execution)
                    full_cmd = f"{write_code_cmd} && {compile_cmd}"
            else:
                # For interpreted languages, write files and run directly
                full_cmd = f"{write_code_cmd} && {write_input_cmd} && {self._get_run_command(language, filename)}"
            
            logger.info(f"[FILE_DEBUG] Writing code directly into container (filename: {filename}, size: {len(code)} bytes)")
            
            # Calculate timeout (add 1 second buffer)
            timeout_seconds = (time_limit_ms / 1000.0) + 1.0
            
            # Run Docker container (no volume mount needed - files written inside container)
            result = await self._run_container(
                image=image,
                container_name=container_name,
                command=full_cmd,
                workdir="/workspace",
                volumes={},  # No volume mount - files written inside container
                network=self.network,
                timeout=timeout_seconds,
                memory_limit_mb=memory_limit_mb,
                input_file="input.txt"
            )
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "error": f"Execution exceeded time limit of {time_limit_ms}ms",
                "exit_code": 124,  # Timeout exit code
                "execution_time_ms": time_limit_ms,
                "memory_used_mb": 0
            }
        except Exception as e:
            logger.error(f"Error running code in Docker: {str(e)}", exc_info=True)
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": 1,
                "execution_time_ms": 0,
                "memory_used_mb": 0
            }
        finally:
            # Cleanup: remove container (if still exists)
            # Note: --rm flag should auto-remove container, but we ensure cleanup
            if container_name:
                await self._remove_container(container_name)
    
    async def _run_container(
        self,
        image: str,
        container_name: str,
        command: str,
        workdir: str,
        volumes: Dict[str, str],
        network: str,
        timeout: float,
        memory_limit_mb: int,
        input_file: str
    ) -> Dict[str, Any]:
        """Run a Docker container and capture output"""
        import time
        start_time = time.time()
        
        # Build docker run command
        docker_cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "--network", network,
            "--name", container_name,
            "--workdir", workdir,
            "--memory", f"{memory_limit_mb}m",
            "--memory-swap", f"{memory_limit_mb}m",  # Disable swap
            "--cpus", "1",  # Limit to 1 CPU
            "--ulimit", "nofile=64:64",  # Limit file descriptors
            # Temporarily removing --read-only to test if it's blocking volume access
            # "--read-only",  # Read-only root filesystem
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",  # Temporary filesystem
            "--security-opt", "no-new-privileges:true",
            # Note: Running as nobody might cause permission issues with mounted volumes
            # Temporarily removing --user to test if that's the issue
        ]
        
        # Add volume mounts (read-write for workspace, we need to write files)
        for host_path, container_path in volumes.items():
            volume_mount = f"{host_path}:{container_path}"
            docker_cmd.extend(["--volume", volume_mount])
            logger.info(f"[VOLUME_DEBUG] Mounting {host_path} -> {container_path} (mount string: {volume_mount})")
        
        # Add image and command (always use sh -c to handle && and redirections)
        # Redirect debug output to stderr so it doesn't pollute stdout
        debug_command = f"echo 'Files in {workdir}:' >&2 && ls -la {workdir} >&2 && echo '---Running command---' >&2 && {command}"
        docker_cmd.append(image)
        docker_cmd.extend(["sh", "-c", debug_command])
        
        # Execute Docker command
        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Read input file and send to stdin (only if volumes are mounted)
        # If no volumes, input file is written inside container, so no stdin needed
        input_data_bytes = None
        if volumes:
            # Get input from the mounted volume
            host_input_path = list(volumes.keys())[0]
            input_file_path = os.path.join(host_input_path, input_file)
            if os.path.exists(input_file_path):
                with open(input_file_path, 'rb') as f:
                    input_data_bytes = f.read()
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data_bytes),
                timeout=timeout
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            # Log full output for debugging (using INFO level so it shows up)
            logger.info(f"[DOCKER_DEBUG] Docker execution output (stdout): {output[:1000] if output else '(empty)'}")
            logger.info(f"[DOCKER_DEBUG] Docker execution error (stderr): {error[:1000] if error else '(empty)'}")
            
            # Try to get memory usage (if available)
            memory_used = 0
            try:
                inspect_result = await asyncio.create_subprocess_exec(
                    "docker", "inspect", container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                # Note: Container might be removed already, so this may fail
            except:
                pass
            
            return {
                "success": process.returncode == 0,
                "output": output,
                "error": error,
                "exit_code": process.returncode or 0,
                "execution_time_ms": execution_time,
                "memory_used_mb": memory_used
            }
            
        except asyncio.TimeoutError:
            # Kill the process
            try:
                process.kill()
                await process.wait()
            except:
                pass
            
            # Force remove container
            try:
                await asyncio.create_subprocess_exec(
                    "docker", "rm", "-f", container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
            except:
                pass
            
            raise
    
    async def _remove_container(self, container_id: str):
        """Remove a Docker container"""
        try:
            await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", container_id,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except:
            pass
    
    def _get_code_filename(self, language: str) -> str:
        """Get the filename for code based on language"""
        extensions = {
            "python": "solution.py",
            "java": "Solution.java",
            "nodejs": "solution.js",
            "cpp": "solution.cpp"
        }
        return extensions.get(language.lower(), "solution.txt")
    
    def _get_compile_command(self, language: str, code_file: str) -> str:
        """Get compilation command for compiled languages"""
        if language.lower() == "java":
            return f"javac {code_file}"
        elif language.lower() == "cpp":
            return f"g++ -o solution -std=c++17 -O2 {code_file}"
        else:
            return ""
    
    def _get_run_command(self, language: str, file_or_executable: str) -> str:
        """Get execution command for the language"""
        if language.lower() == "python":
            return f"python3 {file_or_executable} < input.txt"
        elif language.lower() == "java":
            # Java: compile creates Solution.class, run with java Solution
            # Extract class name (remove .java extension)
            class_name = file_or_executable.replace('.java', '')
            return f"java {class_name} < input.txt"
        elif language.lower() == "nodejs":
            return f"node {file_or_executable} < input.txt"
        elif language.lower() == "cpp":
            # C++: compile creates 'solution' executable
            return f"./solution < input.txt"
        else:
            return f"./{file_or_executable} < input.txt"

