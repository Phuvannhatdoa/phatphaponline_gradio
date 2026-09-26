#!/usr/bin/env python3
"""
GraphDB Loader - ETL Pipeline
Load TTL files to GraphDB via HTTP API

@version: v4.10 (2026-04-10)
@file: src/python/etl/graphdb_loader.py
"""

import os
import argparse
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


class GraphDBLoader:
    """Load TTL files to GraphDB"""
    
    # GraphDB default settings
    DEFAULT_REPO = "graphdb"
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 7200
    
    def __init__(self, host: str = None, port: int = None, repo: str = None):
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.repo = repo or self.DEFAULT_REPO
        self.base_url = f"http://{self.host}:{self.port}"
        
        self.stats = {
            'files_loaded': 0,
            'triples_loaded': 0,
            'errors': 0
        }
    
    def check_connection(self) -> bool:
        """Check if GraphDB is accessible"""
        try:
            response = requests.get(f"{self.base_url}/rest/repositories", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_repositories(self) -> List[Dict]:
        """Get list of repositories"""
        try:
            response = requests.get(f"{self.base_url}/rest/repositories")
            if response.status_code == 200:
                return response.json()
            return []
        except requests.RequestException as e:
            print(f"[GraphDBLoader] Error getting repositories: {e}")
            return []
    
    def create_repository(self, repo_id: str, repo_name: str = None) -> bool:
        """Create a new repository"""
        if repo_name is None:
            repo_name = repo_id
        
        config = {
            "id": repo_id,
            "title": repo_name,
            "type": "graphdb",
            "options": {
                "baseURL": "http://example.org/",
                "defaultNamespace": "http://phatphaponline.org/ontology#",
                "instanceNamespace": "http://phatphaponline.org/",
                "readonly": False,
                "preload": ["schema"],
                "storage": {"type": "disk", "location": "graphdb-home/data"}
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/repositories",
                json=config,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code in [200, 201, 204]
        except requests.RequestException as e:
            print(f"[GraphDBLoader] Error creating repository: {e}")
            return False
    
    def load_ttl_file(self, ttl_file: str, context: str = None, timeout: int = 120) -> Dict:
        """Load a TTL file to GraphDB"""
        filepath = Path(ttl_file)
        
        if not filepath.exists():
            return {"success": False, "error": f"File not found: {ttl_file}"}
        
        # Get file size for progress
        file_size = filepath.stat().st_size
        
        # Prepare the upload URL
        if context:
            # Named graph
            url = f"{self.base_url}/rest/data/{self.repo}"
            graph_param = f"?graph={context}"
        else:
            # Default graph
            url = f"{self.base_url}/rest/data/{self.repo}"
            graph_param = ""
        
        try:
            with open(filepath, 'rb') as f:
                start_time = time.time()
                
                response = requests.post(
                    url + graph_param,
                    data=f,
                    headers={
                        "Content-Type": "application/x-turtle",
                        "Accept": "application/json"
                    },
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                
                if response.status_code in [200, 201, 204]:
                    # Estimate triples (rough: ~10 chars per triple)
                    estimated_triples = file_size // 50
                    
                    self.stats['files_loaded'] += 1
                    self.stats['triples_loaded'] += estimated_triples
                    
                    return {
                        "success": True,
                        "file": ttl_file,
                        "size": file_size,
                        "elapsed": elapsed,
                        "estimated_triples": estimated_triples
                    }
                else:
                    self.stats['errors'] += 1
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text[:500]
                    }
                    
        except requests.RequestException as e:
            self.stats['errors'] += 1
            return {"success": False, "error": str(e)}
    
    def load_multiple(self, ttl_files: List[str], context_prefix: str = None) -> Dict:
        """Load multiple TTL files"""
        results = []
        
        for i, ttl_file in enumerate(ttl_files):
            print(f"[GraphDBLoader] Loading {i+1}/{len(ttl_files)}: {ttl_file}")
            
            # Use context prefix if provided
            context = None
            if context_prefix:
                filename = Path(ttl_file).stem
                context = f"{context_prefix}/{filename}"
            
            result = self.load_ttl_file(ttl_file, context)
            results.append(result)
            
            if result.get("success"):
                print(f"  ✓ Success ({result.get('elapsed', 0):.1f}s)")
            else:
                print(f"  ✗ Error: {result.get('error')}")
            
            # Small delay between files
            time.sleep(0.5)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "total": len(ttl_files),
            "success": success_count,
            "failed": len(ttl_files) - success_count,
            "results": results
        }
    
    def clear_repository(self) -> bool:
        """Clear all data from repository"""
        try:
            response = requests.delete(
                f"{self.base_url}/rest/data/{self.repo}",
                headers={"Accept": "application/json"}
            )
            return response.status_code in [200, 204]
        except requests.RequestException as e:
            print(f"[GraphDBLoader] Error clearing repository: {e}")
            return False
    
    def execute_sparql(self, query: str, timeout: int = 30) -> Optional[Dict]:
        """Execute SPARQL query"""
        try:
            response = requests.post(
                f"{self.base_url}/repositories/{self.repo}",
                params={"query": query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"[GraphDBLoader] SPARQL error: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get loader statistics"""
        return self.stats.copy()
    
    def get_size(self) -> Optional[int]:
        """Get total number of triples in repository"""
        query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
        result = self.execute_sparql(query)
        
        if result and result.get('results', {}).get('bindings'):
            return int(result['results']['bindings'][0]['count']['value'])
        return None


def main():
    parser = argparse.ArgumentParser(description='GraphDB Loader')
    parser.add_argument('--host', default='localhost', help='GraphDB host')
    parser.add_argument('--port', type=int, default=7200, help='GraphDB port')
    parser.add_argument('--repo', default='graphdb', help='Repository ID')
    parser.add_argument('--check', action='store_true', help='Check connection')
    parser.add_argument('--clear', action='store_true', help='Clear repository before load')
    parser.add_argument('--input', help='Input TTL file')
    parser.add_argument('--inputs', nargs='+', help='Multiple TTL files')
    parser.add_argument('--context-prefix', help='Context prefix for named graphs')
    
    args = parser.parse_args()
    
    loader = GraphDBLoader(args.host, args.port, args.repo)
    
    if args.check:
        # Check connection
        if loader.check_connection():
            print(f"[GraphDBLoader] ✓ Connected to GraphDB at {args.host}:{args.port}")
            
            repos = loader.get_repositories()
            print(f"[GraphDBLoader] Available repositories: {len(repos)}")
            for repo in repos:
                print(f"  - {repo.get('id')}: {repo.get('title')}")
            
            size = loader.get_size()
            if size is not None:
                print(f"[GraphDBLoader] Total triples: {size}")
        else:
            print(f"[GraphDBLoader] ✗ Cannot connect to GraphDB at {args.host}:{args.port}")
        return
    
    if args.clear:
        print(f"[GraphDBLoader] Clearing repository {args.repo}...")
        if loader.clear_repository():
            print("[GraphDBLoader] ✓ Repository cleared")
        else:
            print("[GraphDBLoader] ✗ Failed to clear repository")
    
    if args.input:
        # Single file
        result = loader.load_ttl_file(args.input)
        if result.get("success"):
            print(f"[GraphDBLoader] ✓ Loaded: {args.input}")
            print(f"  Size: {result.get('size')} bytes")
            print(f"  Time: {result.get('elapsed'):.1f}s")
        else:
            print(f"[GraphDBLoader] ✗ Error: {result.get('error')}")
    
    elif args.inputs:
        # Multiple files
        results = loader.load_multiple(args.inputs, args.context_prefix)
        print(f"\n[GraphDBLoader] === Load Summary ===")
        print(f"Total: {results['total']}")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        stats = loader.get_stats()
        print(f"[GraphDBLoader] Total files loaded: {stats['files_loaded']}")
        print(f"[GraphDBLoader] Estimated triples: {stats['triples_loaded']}")


if __name__ == '__main__':
    main()
