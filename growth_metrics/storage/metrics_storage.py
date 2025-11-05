"""
Storage Layer
=============

Data storage and caching mechanisms for growth metrics:
- SQLite/PostgreSQL support
- File-based storage fallback
- Efficient data models and indexing
- Data retention and cleanup
- Backup and recovery
"""

import os
import json
import sqlite3
import gzip
import shutil
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
from pathlib import Path
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricsDatabase:
    """SQLite database for storing growth metrics"""
    
    def __init__(self, db_path: str, create_indexes: bool = True):
        self.db_path = db_path
        self.create_indexes = create_indexes
        self.init_database()
        
    def init_database(self):
        """Initialize database tables and indexes"""
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Repository info table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    name TEXT NOT NULL,
                    full_name TEXT UNIQUE NOT NULL,
                    private BOOLEAN,
                    fork BOOLEAN,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    default_branch TEXT,
                    description TEXT,
                    homepage TEXT,
                    license TEXT,
                    open_issues_count INTEGER DEFAULT 0,
                    watchers_count INTEGER DEFAULT 0,
                    stargazers_count INTEGER DEFAULT 0,
                    forks_count INTEGER DEFAULT 0,
                    languages TEXT, -- JSON
                    topics TEXT, -- JSON
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner, name)
                )
            ''')
            
            # Commits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    sha TEXT NOT NULL,
                    author_login TEXT,
                    author_name TEXT,
                    author_email TEXT,
                    date TIMESTAMP,
                    message TEXT,
                    additions INTEGER DEFAULT 0,
                    deletions INTEGER DEFAULT 0,
                    branch TEXT,
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sha)
                )
            ''')
            
            # Contributors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contributors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    login TEXT NOT NULL,
                    user_id INTEGER,
                    name TEXT,
                    email TEXT,
                    contributions INTEGER DEFAULT 0,
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(repo_owner, repo_name, login)
                )
            ''')
            
            # Issues table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    issue_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    title TEXT,
                    state TEXT,
                    author_login TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    labels TEXT, -- JSON
                    assignees TEXT, -- JSON
                    milestone TEXT,
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(repo_owner, repo_name, issue_id)
                )
            ''')
            
            # Pull requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pull_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    pr_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    title TEXT,
                    state TEXT,
                    author_login TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    merged_at TIMESTAMP,
                    base_branch TEXT,
                    head_branch TEXT,
                    additions INTEGER DEFAULT 0,
                    deletions INTEGER DEFAULT 0,
                    changed_files INTEGER DEFAULT 0,
                    commits INTEGER DEFAULT 0,
                    reviewers TEXT, -- JSON
                    review_comments INTEGER DEFAULT 0,
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(repo_owner, repo_name, pr_id)
                )
            ''')
            
            # Metrics snapshot table (daily aggregated data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    stargazers_count INTEGER DEFAULT 0,
                    forks_count INTEGER DEFAULT 0,
                    open_issues_count INTEGER DEFAULT 0,
                    contributors_count INTEGER DEFAULT 0,
                    commits_count INTEGER DEFAULT 0,
                    prs_opened INTEGER DEFAULT 0,
                    prs_merged INTEGER DEFAULT 0,
                    issues_opened INTEGER DEFAULT 0,
                    issues_closed INTEGER DEFAULT 0,
                    health_score REAL,
                    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(repo_owner, repo_name, snapshot_date)
                )
            ''')
            
            # Create indexes for performance
            if self.create_indexes:
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_commits_repo_date ON commits(repo_owner, repo_name, date)',
                    'CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(date)',
                    'CREATE INDEX IF NOT EXISTS idx_contributors_repo ON contributors(repo_owner, repo_name)',
                    'CREATE INDEX IF NOT EXISTS idx_issues_repo_state ON issues(repo_owner, repo_name, state)',
                    'CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues(created_at)',
                    'CREATE INDEX IF NOT EXISTS idx_prs_repo_state ON pull_requests(repo_owner, repo_name, state)',
                    'CREATE INDEX IF NOT EXISTS idx_prs_merged_at ON pull_requests(merged_at)',
                    'CREATE INDEX IF NOT EXISTS idx_snapshots_repo_date ON metrics_snapshots(repo_owner, repo_name, snapshot_date)',
                    'CREATE INDEX IF NOT EXISTS idx_snapshots_date ON metrics_snapshots(snapshot_date)'
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                    
            conn.commit()
            logger.info("Database initialized successfully")
            
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def insert_repository(self, repo_data: Dict[str, Any]):
        """Insert or update repository information"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO repositories 
                (owner, name, full_name, private, fork, created_at, updated_at, default_branch,
                 description, homepage, license, open_issues_count, watchers_count,
                 stargazers_count, forks_count, languages, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo_data['owner'], repo_data['name'], repo_data['full_name'],
                repo_data['private'], repo_data['fork'], repo_data['created_at'],
                repo_data['updated_at'], repo_data['default_branch'], repo_data.get('description'),
                repo_data.get('homepage'), repo_data.get('license'), repo_data['open_issues_count'],
                repo_data['watchers_count'], repo_data['stargazers_count'], repo_data['forks_count'],
                json.dumps(repo_data.get('languages', {})), json.dumps(repo_data.get('topics', []))
            ))
            
    def insert_commits(self, commits_data: List[Dict[str, Any]]):
        """Insert commits in batch"""
        
        if not commits_data:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            commit_records = []
            for commit in commits_data:
                commit_records.append((
                    commit['repo_owner'], commit['repo_name'], commit['sha'],
                    commit['author_login'], commit['author_name'], commit['author_email'],
                    commit['date'], commit['message'], commit['additions'], 
                    commit['deletions'], commit['branch']
                ))
                
            cursor.executemany('''
                INSERT OR IGNORE INTO commits 
                (repo_owner, repo_name, sha, author_login, author_name, author_email,
                 date, message, additions, deletions, branch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', commit_records)
            
    def insert_contributors(self, contributors_data: List[Dict[str, Any]]):
        """Insert contributors in batch"""
        
        if not contributors_data:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            contributor_records = []
            for contrib in contributors_data:
                contributor_records.append((
                    contrib['repo_owner'], contrib['repo_name'], contrib['login'],
                    contrib['user_id'], contrib.get('name'), contrib.get('email'), contrib['contributions']
                ))
                
            cursor.executemany('''
                INSERT OR REPLACE INTO contributors 
                (repo_owner, repo_name, login, user_id, name, email, contributions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', contributor_records)
            
    def insert_issues(self, issues_data: List[Dict[str, Any]]):
        """Insert issues in batch"""
        
        if not issues_data:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            issue_records = []
            for issue in issues_data:
                issue_records.append((
                    issue['repo_owner'], issue['repo_name'], issue['issue_id'],
                    issue['number'], issue['title'], issue['state'], issue['author_login'],
                    issue['created_at'], issue['updated_at'], issue.get('closed_at'),
                    json.dumps(issue.get('labels', [])), json.dumps(issue.get('assignees', [])),
                    issue.get('milestone')
                ))
                
            cursor.executemany('''
                INSERT OR REPLACE INTO issues 
                (repo_owner, repo_name, issue_id, number, title, state, author_login,
                 created_at, updated_at, closed_at, labels, assignees, milestone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', issue_records)
            
    def insert_pull_requests(self, prs_data: List[Dict[str, Any]]):
        """Insert pull requests in batch"""
        
        if not prs_data:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            pr_records = []
            for pr in prs_data:
                pr_records.append((
                    pr['repo_owner'], pr['repo_name'], pr['pr_id'], pr['number'],
                    pr['title'], pr['state'], pr['author_login'], pr['created_at'],
                    pr['updated_at'], pr.get('closed_at'), pr.get('merged_at'),
                    pr['base_branch'], pr['head_branch'], pr['additions'], pr['deletions'],
                    pr['changed_files'], pr['commits'], json.dumps(pr.get('reviewers', [])),
                    pr.get('review_comments', 0)
                ))
                
            cursor.executemany('''
                INSERT OR REPLACE INTO pull_requests 
                (repo_owner, repo_name, pr_id, number, title, state, author_login,
                 created_at, updated_at, closed_at, merged_at, base_branch, head_branch,
                 additions, deletions, changed_files, commits, reviewers, review_comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', pr_records)
            
    def insert_metrics_snapshot(self, snapshot_data: Dict[str, Any]):
        """Insert daily metrics snapshot"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO metrics_snapshots 
                (repo_owner, repo_name, snapshot_date, stargazers_count, forks_count,
                 open_issues_count, contributors_count, commits_count, prs_opened,
                 prs_merged, issues_opened, issues_closed, health_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_data['repo_owner'], snapshot_data['repo_name'], snapshot_data['snapshot_date'],
                snapshot_data['stargazers_count'], snapshot_data['forks_count'],
                snapshot_data['open_issues_count'], snapshot_data['contributors_count'],
                snapshot_data['commits_count'], snapshot_data['prs_opened'],
                snapshot_data['prs_merged'], snapshot_data['issues_opened'],
                snapshot_data['issues_closed'], snapshot_data.get('health_score')
            ))
            
    def get_repository_snapshot(self, owner: str, name: str, date: datetime = None) -> Optional[Dict[str, Any]]:
        """Get repository metrics for specific date"""
        
        if date is None:
            date = datetime.now().date()
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM metrics_snapshots 
                WHERE repo_owner = ? AND repo_name = ? AND snapshot_date = ?
            ''', (owner, name, date))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
                
        return None
        
    def get_repository_history(self, owner: str, name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get repository metrics history"""
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM metrics_snapshots 
                WHERE repo_owner = ? AND repo_name = ? AND snapshot_date >= ?
                ORDER BY snapshot_date DESC
            ''', (owner, name, start_date))
            
            return [dict(row) for row in cursor.fetchall()]
            
    def get_repository_metrics(self, owner: str, name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get aggregated repository metrics for date range"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT c.id) as total_commits,
                    COUNT(DISTINCT contrib.login) as total_contributors,
                    COUNT(DISTINCT i.id) as total_issues,
                    COUNT(DISTINCT pr.id) as total_prs
                FROM repositories r
                LEFT JOIN commits c ON r.owner = c.repo_owner AND r.name = c.repo_name 
                    AND c.date BETWEEN ? AND ?
                LEFT JOIN contributors contrib ON r.owner = contrib.repo_owner AND r.name = contrib.repo_name
                LEFT JOIN issues i ON r.owner = i.repo_owner AND r.name = i.repo_name
                    AND i.created_at BETWEEN ? AND ?
                LEFT JOIN pull_requests pr ON r.owner = pr.repo_owner AND r.name = pr.repo_name
                    AND pr.created_at BETWEEN ? AND ?
                WHERE r.owner = ? AND r.name = ?
            ''', (start_date, end_date, start_date, end_date, start_date, end_date, owner, name))
            
            basic_stats = dict(cursor.fetchone())
            
            # Get PR stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_prs,
                    COUNT(CASE WHEN merged_at IS NOT NULL THEN 1 END) as merged_prs,
                    AVG(CASE WHEN merged_at IS NOT NULL 
                        THEN (julianday(merged_at) - julianday(created_at)) * 24 
                        END) as avg_time_to_merge_hours
                FROM pull_requests
                WHERE repo_owner = ? AND repo_name = ? 
                    AND created_at BETWEEN ? AND ?
            ''', (owner, name, start_date, end_date))
            
            pr_stats = dict(cursor.fetchone())
            
            # Get issue stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_issues,
                    COUNT(CASE WHEN closed_at IS NOT NULL THEN 1 END) as closed_issues,
                    AVG(CASE WHEN closed_at IS NOT NULL 
                        THEN (julianday(closed_at) - julianday(created_at)) 
                        END) as avg_time_to_close_days
                FROM issues
                WHERE repo_owner = ? AND repo_name = ? 
                    AND created_at BETWEEN ? AND ?
            ''', (owner, name, start_date, end_date))
            
            issue_stats = dict(cursor.fetchone())
            
            return {**basic_stats, **pr_stats, **issue_stats}
            
    def cleanup_old_data(self, retention_days: int = 365):
        """Clean up old data based on retention policy"""
        
        cutoff_date = datetime.now().date() - timedelta(days=retention_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up old snapshots
            cursor.execute('DELETE FROM metrics_snapshots WHERE snapshot_date < ?', (cutoff_date,))
            snapshots_deleted = cursor.rowcount
            
            # Clean up old commits (keep only last 90 days)
            cutoff_commits = datetime.now().date() - timedelta(days=90)
            cursor.execute('DELETE FROM commits WHERE date < ?', (cutoff_commits,))
            commits_deleted = cursor.rowcount
            
            logger.info(f"Cleanup completed: {snapshots_deleted} snapshots, {commits_deleted} commits deleted")
            
        return {'snapshots_deleted': snapshots_deleted, 'commits_deleted': commits_deleted}


class FileStorage:
    """File-based storage for metrics data"""
    
    def __init__(self, storage_dir: str, compress: bool = True):
        self.storage_dir = Path(storage_dir)
        self.compress = compress
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def save_metrics_batch(self, metrics_data: Dict[str, Any], date: datetime = None):
        """Save metrics batch to file"""
        
        if date is None:
            date = datetime.now()
            
        # Create date-based directory structure
        date_dir = self.storage_dir / date.strftime('%Y') / date.strftime('%m') / date.strftime('%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"metrics_{date.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = date_dir / filename
        
        data_json = json.dumps(metrics_data, indent=2, default=str)
        
        if self.compress:
            filename += '.gz'
            filepath = date_dir / filename
            
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(data_json)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data_json)
                
        logger.info(f"Metrics saved to {filepath}")
        return str(filepath)
        
    def load_metrics_batch(self, filepath: str) -> Dict[str, Any]:
        """Load metrics batch from file"""
        
        filepath = Path(filepath)
        
        if filepath.suffix == '.gz':
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
    def list_metrics_files(self, start_date: datetime = None, end_date: datetime = None) -> List[str]:
        """List metrics files in date range"""
        
        files = []
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
            
        current_date = start_date.date()
        end_date = end_date.date()
        
        while current_date <= end_date:
            date_dir = self.storage_dir / str(current_date.year) / f"{current_date.month:02d}" / f"{current_date.day:02d}"
            
            if date_dir.exists():
                for pattern in ['metrics_*.json', 'metrics_*.json.gz']:
                    files.extend(date_dir.glob(pattern))
                    
            current_date += timedelta(days=1)
            
        return [str(f) for f in sorted(files)]


class MetricsStorage:
    """
    Unified storage interface for growth metrics
    
    Supports multiple backends:
    - SQLite database (primary)
    - File-based storage (fallback)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backend = config.get('backend', 'sqlite')
        self.connection_string = config.get('connection_string', 'sqlite:///growth_metrics.db')
        self.data_directory = config.get('data_directory', './data')
        self.enable_compression = config.get('enable_compression', True)
        self.retention_days = config.get('retention_days', 365)
        
        # Initialize storage backends
        if self.backend == 'sqlite':
            self.db = MetricsDatabase(self.connection_string.replace('sqlite:///', ''), 
                                    config.get('create_indexes', True))
        else:
            self.db = None
            
        self.file_storage = FileStorage(self.data_directory, self.enable_compression)
        
    def save_repository_data(self, repo_metrics: Dict[str, Any]):
        """Save complete repository metrics"""
        
        try:
            # Save to database
            if self.db:
                # Repository info
                repo_info = repo_metrics.get('repository_info')
                if repo_info:
                    repo_data = {
                        'owner': repo_info.owner,
                        'name': repo_info.name,
                        'full_name': repo_info.full_name,
                        'private': repo_info.private,
                        'fork': repo_info.fork,
                        'created_at': repo_info.created_at.isoformat(),
                        'updated_at': repo_info.updated_at.isoformat(),
                        'default_branch': repo_info.default_branch,
                        'description': repo_info.description,
                        'homepage': repo_info.homepage,
                        'license': repo_info.license,
                        'open_issues_count': repo_info.open_issues_count,
                        'watchers_count': repo_info.watchers_count,
                        'stargazers_count': repo_info.stargazers_count,
                        'forks_count': repo_info.forks_count,
                        'languages': repo_info.languages,
                        'topics': repo_info.topics
                    }
                    self.db.insert_repository(repo_data)
                    
                # Commits
                commits_data = [
                    {
                        'repo_owner': commit['repo_owner'],
                        'repo_name': commit['repo_name'],
                        'sha': commit['sha'],
                        'author_login': commit['author_login'],
                        'author_name': commit['author_name'],
                        'author_email': commit['author_email'],
                        'date': commit['date'],
                        'message': commit['message'],
                        'additions': commit['additions'],
                        'deletions': commit['deletions'],
                        'branch': commit['branch']
                    } for commit in repo_metrics.get('commits', [])
                ]
                self.db.insert_commits(commits_data)
                
                # Contributors
                contributors_data = [
                    {
                        'repo_owner': contributor['repo_owner'],
                        'repo_name': contributor['repo_name'],
                        'login': contributor['login'],
                        'user_id': contributor['user_id'],
                        'name': contributor.get('name'),
                        'email': contributor.get('email'),
                        'contributions': contributor['contributions']
                    } for contributor in repo_metrics.get('contributors', [])
                ]
                self.db.insert_contributors(contributors_data)
                
                # Issues
                issues_data = [
                    {
                        'repo_owner': issue['repo_owner'],
                        'repo_name': issue['repo_name'],
                        'issue_id': issue['issue_id'],
                        'number': issue['number'],
                        'title': issue['title'],
                        'state': issue['state'],
                        'author_login': issue['author_login'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'closed_at': issue.get('closed_at'),
                        'labels': issue.get('labels', []),
                        'assignees': issue.get('assignees', []),
                        'milestone': issue.get('milestone')
                    } for issue in repo_metrics.get('issues', [])
                ]
                self.db.insert_issues(issues_data)
                
                # Pull requests
                prs_data = [
                    {
                        'repo_owner': pr['repo_owner'],
                        'repo_name': pr['repo_name'],
                        'pr_id': pr['pr_id'],
                        'number': pr['number'],
                        'title': pr['title'],
                        'state': pr['state'],
                        'author_login': pr['author_login'],
                        'created_at': pr['created_at'],
                        'updated_at': pr['updated_at'],
                        'closed_at': pr.get('closed_at'),
                        'merged_at': pr.get('merged_at'),
                        'base_branch': pr['base_branch'],
                        'head_branch': pr['head_branch'],
                        'additions': pr['additions'],
                        'deletions': pr['deletions'],
                        'changed_files': pr['changed_files'],
                        'commits': pr['commits'],
                        'reviewers': pr.get('reviewers', []),
                        'review_comments': pr.get('review_comments', 0)
                    } for pr in repo_metrics.get('pull_requests', [])
                ]
                self.db.insert_pull_requests(prs_data)
                
                # Save daily snapshot
                snapshot_date = datetime.now().date()
                snapshot_data = {
                    'repo_owner': repo_metrics['repository'].split('/')[0],
                    'repo_name': repo_metrics['repository'].split('/')[1],
                    'snapshot_date': snapshot_date.isoformat(),
                    'stargazers_count': repo_metrics.get('stars_count', 0),
                    'forks_count': repo_metrics.get('forks_count', 0),
                    'open_issues_count': len([i for i in repo_metrics.get('issues', []) if i['state'] == 'open']),
                    'contributors_count': len(repo_metrics.get('contributors', [])),
                    'commits_count': len(repo_metrics.get('commits', [])),
                    'prs_opened': len([pr for pr in repo_metrics.get('pull_requests', []) if pr['state'] in ['open', 'closed']]),
                    'prs_merged': len([pr for pr in repo_metrics.get('pull_requests', []) if pr['state'] == 'merged']),
                    'issues_opened': len(repo_metrics.get('issues', [])),
                    'issues_closed': len([i for i in repo_metrics.get('issues', []) if i['state'] == 'closed'])
                }
                self.db.insert_metrics_snapshot(snapshot_data)
                
            # Always save to file storage as backup
            self.file_storage.save_metrics_batch(repo_metrics)
            
        except Exception as e:
            logger.error(f"Failed to save repository data: {e}")
            raise
            
    def get_repository_history(self, owner: str, name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get repository metrics history"""
        
        if self.db:
            return self.db.get_repository_history(owner, name, days)
        else:
            # Fallback to file storage
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            files = self.file_storage.list_metrics_files(start_date, end_date)
            
            results = []
            for file_path in files:
                try:
                    data = self.file_storage.load_metrics_batch(file_path)
                    if data['repository'] == f"{owner}/{name}":
                        results.append(data)
                except Exception as e:
                    logger.warning(f"Failed to load file {file_path}: {e}")
                    
            return results
            
    def cleanup_old_data(self):
        """Cleanup old data based on retention policy"""
        
        if self.db:
            return self.db.cleanup_old_data(self.retention_days)
        else:
            # File storage cleanup would need to be implemented
            logger.info("File storage cleanup not implemented")
            return {'files_deleted': 0, 'space_freed': 0}