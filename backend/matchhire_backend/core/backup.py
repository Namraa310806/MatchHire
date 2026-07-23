"""
Backup and Recovery Module

Provides database backup strategy, snapshot strategy, index recovery,
disaster recovery documentation, and restore validation.
"""

import gzip
import logging
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Backup types."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(Enum):
    """Backup status."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"


@dataclass
class BackupResult:
    """Result of a backup operation."""
    backup_type: BackupType
    status: BackupStatus
    file_path: str = ""
    size_bytes: int = 0
    duration_seconds: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    status: BackupStatus
    backup_file: str = ""
    duration_seconds: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackupStrategy(ABC):
    """Abstract base class for backup strategies."""
    
    @abstractmethod
    def backup(self, destination: str) -> BackupResult:
        """Perform backup."""
        pass
        
    @abstractmethod
    def restore(self, backup_file: str) -> RestoreResult:
        """Restore from backup."""
        pass


class PostgreSQLBackupStrategy(BackupStrategy):
    """
    PostgreSQL backup strategy using pg_dump.
    """
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or self._get_db_config()
        
    def _get_db_config(self) -> Dict[str, str]:
        """Get database configuration from Django settings."""
        databases = getattr(settings, "DATABASES", {})
        db_config = databases.get("default", {})
        
        return {
            "dbname": db_config.get("NAME", "matchhire"),
            "user": db_config.get("USER", "matchhire"),
            "password": db_config.get("PASSWORD", ""),
            "host": db_config.get("HOST", "localhost"),
            "port": db_config.get("PORT", "5432"),
        }
        
    def backup(self, destination: str) -> BackupResult:
        """
        Perform PostgreSQL backup using pg_dump.
        
        Args:
            destination: Destination directory for backup file
            
        Returns:
            BackupResult
        """
        start_time = datetime.utcnow()
        
        try:
            # Create destination directory if needed
            os.makedirs(destination, exist_ok=True)
            
            # Generate backup filename
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(destination, f"matchhire_backup_{timestamp}.sql.gz")
            
            # Build pg_dump command
            pg_dump_cmd = [
                "pg_dump",
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['dbname']}",
                "--no-owner",
                "--no-acl",
                "--format=plain",
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config["password"]
            
            # Execute pg_dump and compress
            with subprocess.Popen(
                pg_dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            ) as proc:
                with gzip.open(backup_file, "wb") as f:
                    f.write(proc.stdout.read())
                    
                if proc.wait() != 0:
                    error = proc.stderr.read().decode()
                    raise Exception(f"pg_dump failed: {error}")
                    
            # Get file size
            file_size = os.path.getsize(backup_file)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Backup completed: {backup_file} ({file_size} bytes, {duration:.2f}s)")
            
            return BackupResult(
                backup_type=BackupType.FULL,
                status=BackupStatus.SUCCESS,
                file_path=backup_file,
                size_bytes=file_size,
                duration_seconds=duration,
                metadata={
                    "database": self.db_config["dbname"],
                    "compressed": True,
                },
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Backup failed: {e}")
            
            return BackupResult(
                backup_type=BackupType.FULL,
                status=BackupStatus.FAILED,
                duration_seconds=duration,
                metadata={"error": str(e)},
            )
            
    def restore(self, backup_file: str) -> RestoreResult:
        """
        Restore PostgreSQL database from backup.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            RestoreResult
        """
        start_time = datetime.utcnow()
        
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
                
            # Decompress and restore
            psql_cmd = [
                "psql",
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['dbname']}",
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config["password"]
            
            with gzip.open(backup_file, "rb") as f:
                with subprocess.Popen(
                    psql_cmd,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                ) as proc:
                    proc.stdin.write(f.read())
                    proc.stdin.close()
                    
                    if proc.wait() != 0:
                        error = proc.stderr.read().decode()
                        raise Exception(f"psql failed: {error}")
                        
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Restore completed: {backup_file} ({duration:.2f}s)")
            
            return RestoreResult(
                status=BackupStatus.SUCCESS,
                backup_file=backup_file,
                duration_seconds=duration,
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Restore failed: {e}")
            
            return RestoreResult(
                status=BackupStatus.FAILED,
                backup_file=backup_file,
                duration_seconds=duration,
                metadata={"error": str(e)},
            )


class BackupManager:
    """
    Backup management system.
    
    Manages scheduled backups, retention, and validation.
    """
    
    def __init__(self, backup_dir: str = "./backups", strategy: BackupStrategy = None):
        self.backup_dir = backup_dir
        self.strategy = strategy or PostgreSQLBackupStrategy()
        self._schedule: List[Dict[str, Any]] = []
        
    def create_backup(self, backup_type: BackupType = BackupType.FULL) -> BackupResult:
        """
        Create a backup.
        
        Args:
            backup_type: Type of backup to create
            
        Returns:
            BackupResult
        """
        logger.info(f"Creating {backup_type.value} backup...")
        return self.strategy.backup(self.backup_dir)
        
    def restore_backup(self, backup_file: str) -> RestoreResult:
        """
        Restore from a backup.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            RestoreResult
        """
        logger.info(f"Restoring from backup: {backup_file}")
        return self.strategy.restore(backup_file)
        
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of backup information
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
            
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("matchhire_backup_") and filename.endswith(".sql.gz"):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                # Extract timestamp from filename
                try:
                    timestamp_str = filename.replace("matchhire_backup_", "").replace(".sql.gz", "")
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except:
                    timestamp = datetime.fromtimestamp(stat.st_mtime)
                    
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size_bytes": stat.st_size,
                    "size_mb": stat.st_size / 1024 / 1024,
                    "created_at": timestamp.isoformat(),
                    "age_days": (datetime.utcnow() - timestamp).days,
                })
                
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
        
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        Delete backups older than retention period.
        
        Args:
            retention_days: Number of days to retain backups
            
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted_count = 0
        for backup in backups:
            backup_date = datetime.fromisoformat(backup["created_at"])
            if backup_date < cutoff_date:
                try:
                    os.remove(backup["filepath"])
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup['filename']}: {e}")
                    
        return deleted_count
        
    def validate_backup(self, backup_file: str) -> bool:
        """
        Validate a backup file.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if backup is valid
        """
        try:
            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False
                
            # Check file size
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                logger.error(f"Backup file is empty: {backup_file}")
                return False
                
            # Try to decompress to validate
            with gzip.open(backup_file, "rb") as f:
                # Read first 1KB to validate
                f.read(1024)
                
            logger.info(f"Backup validation passed: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup validation failed: {e}")
            return False


class SnapshotManager:
    """
    Snapshot management for Elasticsearch indices.
    """
    
    def __init__(self):
        self._elasticsearch_client = None
        
    def _get_client(self):
        """Get Elasticsearch client."""
        if self._elasticsearch_client is None:
            try:
                from apps.search.providers.elasticsearch_provider import ElasticsearchProvider
                provider = ElasticsearchProvider()
                self._elasticsearch_client = provider.client
            except:
                logger.warning("Elasticsearch not available")
        return self._elasticsearch_client
        
    def create_snapshot(self, repository: str, snapshot_name: str) -> Dict[str, Any]:
        """
        Create an Elasticsearch snapshot.
        
        Args:
            repository: Snapshot repository name
            snapshot_name: Snapshot name
            
        Returns:
            Snapshot result
        """
        client = self._get_client()
        
        if client is None:
            return {"status": "failed", "error": "Elasticsearch not available"}
            
        try:
            # Create snapshot
            response = client.snapshot.create(
                repository=repository,
                snapshot=snapshot_name,
                wait_for_completion=False,
            )
            
            logger.info(f"Snapshot created: {snapshot_name}")
            
            return {
                "status": "success",
                "snapshot": snapshot_name,
                "repository": repository,
                "response": response,
            }
            
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return {"status": "failed", "error": str(e)}
            
    def restore_snapshot(self, repository: str, snapshot_name: str,
                       indices: str = "*") -> Dict[str, Any]:
        """
        Restore an Elasticsearch snapshot.
        
        Args:
            repository: Snapshot repository name
            snapshot_name: Snapshot name
            indices: Indices to restore (default: all)
            
        Returns:
            Restore result
        """
        client = self._get_client()
        
        if client is None:
            return {"status": "failed", "error": "Elasticsearch not available"}
            
        try:
            response = client.snapshot.restore(
                repository=repository,
                snapshot=snapshot_name,
                indices=indices,
                wait_for_completion=False,
            )
            
            logger.info(f"Snapshot restore initiated: {snapshot_name}")
            
            return {
                "status": "success",
                "snapshot": snapshot_name,
                "repository": repository,
                "indices": indices,
                "response": response,
            }
            
        except Exception as e:
            logger.error(f"Snapshot restore failed: {e}")
            return {"status": "failed", "error": str(e)}
            
    def list_snapshots(self, repository: str) -> List[Dict[str, Any]]:
        """
        List all snapshots in a repository.
        
        Args:
            repository: Snapshot repository name
            
        Returns:
            List of snapshots
        """
        client = self._get_client()
        
        if client is None:
            return []
            
        try:
            response = client.snapshot.get_repository(repository=repository)
            snapshots = client.snapshot.get(repository=repository, snapshot="_all")
            
            return snapshots.get("snapshots", [])
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []


class DisasterRecoveryPlan:
    """
    Disaster recovery plan documentation and execution.
    """
    
    def __init__(self):
        self.backup_manager = BackupManager()
        self.snapshot_manager = SnapshotManager()
        
    def create_recovery_point(self) -> Dict[str, Any]:
        """
        Create a complete recovery point (database + indices).
        
        Returns:
            Recovery point information
        """
        logger.info("Creating recovery point...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": None,
            "elasticsearch": None,
        }
        
        # Backup database
        db_result = self.backup_manager.create_backup()
        results["database"] = {
            "status": db_result.status.value,
            "file": db_result.file_path,
            "size_bytes": db_result.size_bytes,
        }
        
        # Snapshot Elasticsearch (if available)
        try:
            snapshot_name = f"recovery_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            es_result = self.snapshot_manager.create_snapshot("backups", snapshot_name)
            results["elasticsearch"] = es_result
        except:
            results["elasticsearch"] = {"status": "skipped", "reason": "Elasticsearch not available"}
            
        return results
        
    def execute_recovery_plan(self, backup_file: str = None,
                            snapshot_name: str = None) -> Dict[str, Any]:
        """
        Execute disaster recovery.
        
        Args:
            backup_file: Database backup file to restore
            snapshot_name: Elasticsearch snapshot to restore
            
        Returns:
            Recovery results
        """
        logger.info("Executing disaster recovery...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": None,
            "elasticsearch": None,
        }
        
        # Restore database
        if backup_file:
            db_result = self.backup_manager.restore_backup(backup_file)
            results["database"] = {
                "status": db_result.status.value,
                "file": backup_file,
                "duration_seconds": db_result.duration_seconds,
            }
        else:
            # Use latest backup
            backups = self.backup_manager.list_backups()
            if backups:
                latest = backups[0]
                db_result = self.backup_manager.restore_backup(latest["filepath"])
                results["database"] = {
                    "status": db_result.status.value,
                    "file": latest["filepath"],
                    "duration_seconds": db_result.duration_seconds,
                }
            else:
                results["database"] = {"status": "failed", "error": "No backup available"}
                
        # Restore Elasticsearch
        if snapshot_name:
            es_result = self.snapshot_manager.restore_snapshot("backups", snapshot_name)
            results["elasticsearch"] = es_result
            
        return results
        
    def validate_recovery(self) -> Dict[str, Any]:
        """
        Validate that recovery is possible.
        
        Returns:
            Validation results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {"available": False, "latest_backup": None},
            "elasticsearch": {"available": False, "latest_snapshot": None},
        }
        
        # Check database backups
        backups = self.backup_manager.list_backups()
        if backups:
            latest = backups[0]
            if self.backup_manager.validate_backup(latest["filepath"]):
                results["database"] = {
                    "available": True,
                    "latest_backup": latest,
                }
                
        # Check Elasticsearch snapshots
        try:
            snapshots = self.snapshot_manager.list_snapshots("backups")
            if snapshots:
                results["elasticsearch"] = {
                    "available": True,
                    "latest_snapshot": snapshots[-1],
                }
        except:
            pass
            
        results["can_recover"] = results["database"]["available"]
        
        return results


# Global instances
backup_manager = BackupManager()
snapshot_manager = SnapshotManager()
disaster_recovery = DisasterRecoveryPlan()
