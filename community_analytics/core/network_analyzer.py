"""
Social Network Analysis System

Analyzes social relationships, collaboration patterns, and network dynamics
within the repository community to understand interaction patterns and identify
key influencers, bridges, and community clusters.
"""

import asyncio
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, FrozenSet
import statistics
import math
import networkx as nx
from dataclasses import dataclass

from github_api_client import GitHubAPIClient


@dataclass
class NetworkNode:
    """Individual node in the social network (contributor)"""
    login: str
    github_id: int
    
    # Basic metrics
    total_contributions: int
    first_activity_date: datetime
    last_activity_date: Optional[datetime]
    
    # Network position metrics
    degree_centrality: float = 0.0  # Direct connections
    betweenness_centrality: float = 0.0  # Bridge connections
    closeness_centrality: float = 0.0  # Overall network reach
    eigenvector_centrality: 0.0  # Connection to important nodes
    
    # Community role
    role: str = "member"  # core_member, maintainer, bridge, peripheral, isolated
    
    # Interaction patterns
    collaborators: Set[str] = field(default_factory=set)
    interaction_types: Dict[str, int] = field(default_factory=dict)  # type -> count
    
    # Influence metrics
    influence_score: float = 0.0
    mentoring_score: float = 0.0
    collaboration_diversity: float = 0.0
    
    # Activity patterns
    active_periods: List[Tuple[datetime, datetime]] = field(default_factory=list)
    collaboration_frequency: float = 0.0
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if not self.last_activity_date:
            self.last_activity_date = datetime.now()
        
        # Calculate collaboration frequency
        if self.collaborators:
            active_days = (self.last_activity_date - self.first_activity_date).days
            self.collaboration_frequency = len(self.collaborators) / max(1, active_days / 30)  # per month
        
        # Calculate collaboration diversity
        total_collaborations = sum(self.interaction_types.values())
        if total_collaborations > 0:
            diversity_score = 0
            for count in self.interaction_types.values():
                p = count / total_collaborations
                diversity_score -= p * math.log2(p) if p > 0 else 0
            self.collaboration_diversity = min(1.0, diversity_score / math.log2(len(self.interaction_types) + 1))


@dataclass
class NetworkEdge:
    """Connection between two contributors"""
    contributor1: str
    contributor2: str
    
    # Edge attributes
    interaction_count: int
    interaction_types: Dict[str, int]  # type -> count
    first_interaction_date: datetime
    last_interaction_date: datetime
    relationship_strength: float  # 0-1
    
    # Specific collaboration data
    co_authored_commits: int = 0
    reviewed_prs: int = 0
    issues_discussed: int = 0
    discussions_participated: int = 0
    
    def __post_init__(self):
        """Calculate relationship strength"""
        # Weighted combination of interaction types
        weights = {
            'co_author': 3.0,    # Strong collaboration
            'review': 2.0,       # Code review relationship
            'discussion': 1.5,   # Active discussion
            'mention': 1.0       # Basic interaction
        }
        
        weighted_score = 0
        for interaction_type, count in self.interaction_types.items():
            weight = weights.get(interaction_type, 1.0)
            weighted_score += count * weight
        
        # Normalize by interaction timespan
        timespan_days = (self.last_interaction_date - self.first_interaction_date).days
        if timespan_days > 0:
            self.relationship_strength = min(1.0, weighted_score / (timespan_days / 30))  # Per month
        else:
            self.relationship_strength = min(1.0, weighted_score)


@dataclass
class CommunityCluster:
    """Identified community cluster/community"""
    cluster_id: int
    members: Set[str]
    density: float  # How interconnected the cluster is
    avg_clustering_coefficient: float
    
    # Cluster characteristics
    cluster_role: str = "specialized"  # specialized, general, bridge, core
    
    # Activity patterns
    avg_contributions_per_member: float = 0.0
    collaboration_intensity: float = 0.0
    diversity_score: float = 0.0
    
    # Connection to other clusters
    bridge_contributors: List[str] = field(default_factory=list)
    external_connections: int = 0


@dataclass
class NetworkAnalysis:
    """Comprehensive network analysis results"""
    timestamp: datetime
    total_nodes: int
    total_edges: int
    network_density: float
    
    # Network metrics
    avg_clustering_coefficient: float = 0.0
    network_diameter: int = 0
    avg_path_length: float = 0.0
    
    # Central nodes
    most_connected: List[str] = field(default_factory=list)  # Top by degree
    key_bridges: List[str] = field(default_factory=list)     # Top by betweenness
    most_influential: List[str] = field(default_factory=list) # Top by eigenvector
    
    # Community structure
    identified_clusters: List[CommunityCluster] = field(default_factory=list)
    cluster_count: int = 0
    modularity_score: float = 0.0
    
    # Network health
    isolated_nodes: int = 0
    bridge_nodes: int = 0
    core_contributors: int = 0
    peripheral_contributors: int = 0
    
    # Evolution metrics
    growth_rate: float = 0.0  # Network growth over time
    collaboration_trend: float = 0.0  # Collaboration intensity trend
    
    # Recommendations
    network_recommendations: List[str] = field(default_factory=list)


class SocialNetworkAnalyzer:
    """
    Analyze social networks and collaboration patterns within the community.
    
    This class provides comprehensive network analysis including centrality measures,
    community detection, and network evolution tracking.
    """
    
    def __init__(self):
        """Initialize the network analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Network analysis parameters
        self.min_interaction_threshold = 2  # Minimum interactions to create edge
        self.centrality_top_k = 10  # Top K nodes for centrality rankings
        
        # Historical network data
        self.network_history: List[NetworkAnalysis] = []
        self.network_graph: nx.Graph = nx.Graph()
        
        # Node and edge data
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: Dict[FrozenSet[str], NetworkEdge] = {}
    
    async def analyze_social_network(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int = 180
    ) -> NetworkAnalysis:
        """
        Perform comprehensive social network analysis.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            lookback_days: Days of historical data to analyze
            
        Returns:
            NetworkAnalysis with comprehensive network metrics
        """
        self.logger.info(f"Analyzing social network for {owner}/{repo}")
        
        # Collect collaboration data
        collaboration_data = await self._collect_collaboration_data(client, owner, repo, lookback_days)
        
        # Build network graph
        await self._build_network_graph(collaboration_data)
        
        # Calculate network metrics
        network_metrics = self._calculate_network_metrics()
        
        # Detect community clusters
        community_clusters = self._detect_community_clusters()
        
        # Identify key contributors and roles
        self._identify_contributor_roles()
        
        # Analyze network health and evolution
        health_metrics = self._analyze_network_health()
        
        # Generate recommendations
        recommendations = self._generate_network_recommendations()
        
        # Create comprehensive analysis
        network_analysis = NetworkAnalysis(
            timestamp=datetime.now(),
            total_nodes=len(self.nodes),
            total_edges=len(self.edges),
            network_density=nx.density(self.network_graph),
            avg_clustering_coefficient=nx.average_clustering(self.network_graph),
            network_diameter=nx.diameter(self.network_graph) if nx.is_connected(self.network_graph) else 0,
            avg_path_length=nx.average_shortest_path_length(self.network_graph) if nx.is_connected(self.network_graph) else 0,
            most_connected=health_metrics['most_connected'],
            key_bridges=health_metrics['key_bridges'],
            most_influential=health_metrics['most_influential'],
            identified_clusters=community_clusters,
            cluster_count=len(community_clusters),
            modularity_score=self._calculate_modularity_score(community_clusters),
            isolated_nodes=health_metrics['isolated_nodes'],
            bridge_nodes=health_metrics['bridge_nodes'],
            core_contributors=health_metrics['core_contributors'],
            peripheral_contributors=health_metrics['peripheral_contributors'],
            growth_rate=health_metrics['growth_rate'],
            collaboration_trend=health_metrics['collaboration_trend'],
            network_recommendations=recommendations
        )
        
        # Store for historical analysis
        self.network_history.append(network_analysis)
        
        return network_analysis
    
    async def _collect_collaboration_data(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Collect collaboration data from various sources"""
        
        since_date = datetime.now() - timedelta(days=lookback_days)
        
        try:
            # Collect data concurrently
            prs, commits, issues, comments, reviews = await asyncio.gather(
                client.get_pull_requests(owner, repo, state="all"),
                client.get_commits(owner, repo, since=since_date),
                client.get_issues(owner, repo, state="all", since=since_date),
                client.get_issue_comments(owner, repo, since=since_date),
                client.get_review_comments(owner, repo, since=since_date),
                return_exceptions=True
            )
            
            # Handle potential exceptions
            data = {}
            for key, result in zip(['prs', 'commits', 'issues', 'comments', 'reviews'], 
                                 [prs, commits, issues, comments, reviews]):
                data[key] = result if not isinstance(result, Exception) else []
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect collaboration data: {e}")
            return {}
    
    async def _build_network_graph(self, collaboration_data: Dict[str, Any]):
        """Build the network graph from collaboration data"""
        
        # Initialize nodes for all contributors
        all_contributors = set()
        
        # Extract contributors from all data sources
        for pr in collaboration_data.get('prs', []):
            author = pr.get('user', {}).get('login')
            if author:
                all_contributors.add(author)
                all_contributors.add(f"author_{pr.get('number')}")  # For analysis
        
        for commit in collaboration_data.get('commits', []):
            author = commit.get('author', {})
            login = author.get('login')
            if login:
                all_contributors.add(login)
            
            # Extract co-authors from commit messages
            commit_message = commit.get('commit', {}).get('message', '')
            co_authors = self._extract_co_authors(commit_message)
            all_contributors.update(co_authors)
        
        for issue in collaboration_data.get('issues', []):
            author = issue.get('user', {}).get('login')
            if author:
                all_contributors.add(author)
        
        for comment in collaboration_data.get('comments', []):
            author = comment.get('user', {}).get('login')
            if author:
                all_contributors.add(author)
        
        for review in collaboration_data.get('reviews', []):
            author = review.get('user', {}).get('login')
            if author:
                all_contributors.add(author)
        
        # Create nodes
        self.nodes.clear()
        self.network_graph.clear()
        
        for contributor in all_contributors:
            if contributor and not contributor.startswith('author_'):  # Skip pseudo-nodes
                node = NetworkNode(
                    login=contributor,
                    github_id=0,  # Would need additional API call
                    total_contributions=0,
                    first_activity_date=datetime.now() - timedelta(days=30),
                    last_activity_date=datetime.now()
                )
                self.nodes[contributor] = node
                self.network_graph.add_node(contributor)
        
        # Build edges from interactions
        self.edges.clear()
        
        # Co-authorship relationships
        await self._build_co_authorship_edges(collaboration_data.get('commits', []))
        
        # PR review relationships
        await self._build_review_edges(collaboration_data.get('prs', []), collaboration_data.get('reviews', []))
        
        # Discussion relationships
        await self._build_discussion_edges(collaboration_data.get('issues', []), collaboration_data.get('comments', []))
        
        # Add edges to graph
        for edge_key, edge in self.edges.items():
            self.network_graph.add_edge(edge.contributor1, edge.contributor2, 
                                      weight=edge.relationship_strength)
    
    async def _build_co_authorship_edges(self, commits: List[Dict[str, Any]]):
        """Build edges based on co-authorship of commits"""
        
        # Group commits by co-authors
        co_authorship_groups = defaultdict(set)
        
        for commit in commits:
            commit_message = commit.get('commit', {}).get('message', '')
            co_authors = self._extract_co_authors(commit_message)
            
            # Add primary author
            author = commit.get('author', {})
            login = author.get('login')
            if login:
                co_authors.add(login)
            
            # Create edges between all pairs of co-authors
            co_author_list = list(co_authors)
            for i in range(len(co_author_list)):
                for j in range(i + 1, len(co_author_list)):
                    author1, author2 = co_author_list[i], co_author_list[j]
                    pair = frozenset([author1, author2])
                    co_authorship_groups[pair].add(commit.get('sha', ''))
        
        # Create edges for significant co-authorship
        for pair, commit_shas in co_authorship_groups.items():
            if len(commit_shas) >= self.min_interaction_threshold:
                contributors = list(pair)
                edge_key = frozenset(contributors)
                
                if edge_key not in self.edges:
                    self.edges[edge_key] = NetworkEdge(
                        contributor1=contributors[0],
                        contributor2=contributors[1],
                        interaction_count=len(commit_shas),
                        interaction_types={'co_author': len(commit_shas)},
                        first_interaction_date=datetime.now() - timedelta(days=90),
                        last_interaction_date=datetime.now(),
                        relationship_strength=0.0,
                        co_authored_commits=len(commit_shas)
                    )
                else:
                    self.edges[edge_key].co_authored_commits += len(commit_shas)
                    self.edges[edge_key].interaction_count += len(commit_shas)
                    self.edges[edge_key].interaction_types['co_author'] = self.edges[edge_key].co_authored_commits
    
    async def _build_review_edges(self, prs: List[Dict[str, Any]], reviews: List[Dict[str, Any]]):
        """Build edges based on PR review relationships"""
        
        # Create mapping from PR to reviewers
        pr_reviewers = defaultdict(set)
        
        for review in reviews:
            reviewer = review.get('user', {}).get('login')
            pr_number = review.get('pull_request_url', '').split('/')[-1]  # Extract PR number
            if reviewer and pr_number:
                pr_reviewers[pr_number].add(reviewer)
        
        # Create edges between PR authors and reviewers
        for pr in prs:
            author = pr.get('user', {}).get('login')
            pr_number = str(pr.get('number', ''))
            
            if author and pr_number in pr_reviewers:
                for reviewer in pr_reviewers[pr_number]:
                    pair = frozenset([author, reviewer])
                    
                    if pair not in self.edges:
                        self.edges[pair] = NetworkEdge(
                            contributor1=author,
                            contributor2=reviewer,
                            interaction_count=1,
                            interaction_types={'review': 1},
                            first_interaction_date=datetime.now() - timedelta(days=90),
                            last_interaction_date=datetime.now(),
                            relationship_strength=0.0,
                            reviewed_prs=1
                        )
                    else:
                        self.edges[pair].reviewed_prs += 1
                        self.edges[pair].interaction_count += 1
                        self.edges[pair].interaction_types['review'] = self.edges[pair].reviewed_prs
    
    async def _build_discussion_edges(self, issues: List[Dict[str, Any]], comments: List[Dict[str, Any]]):
        """Build edges based on discussion participation"""
        
        # Group comments by issue
        issue_discussions = defaultdict(lambda: {'author': None, 'commenters': set()})
        
        # Track issue authors
        for issue in issues:
            author = issue.get('user', {}).get('login')
            issue_number = str(issue.get('number', ''))
            if author and issue_number:
                issue_discussions[issue_number]['author'] = author
        
        # Track commenters
        for comment in comments:
            commenter = comment.get('user', {}).get('login')
            issue_url = comment.get('issue_url', '')
            issue_number = issue_url.split('/')[-1] if issue_url else ''
            
            if commenter and issue_number:
                issue_discussions[issue_number]['commenters'].add(commenter)
        
        # Create edges based on discussion participation
        for issue_number, discussion in issue_discussions.items():
            author = discussion['author']
            commenters = discussion['commenters']
            
            if author:
                for commenter in commenters:
                    pair = frozenset([author, commenter])
                    
                    if pair not in self.edges:
                        self.edges[pair] = NetworkEdge(
                            contributor1=author,
                            contributor2=commenter,
                            interaction_count=1,
                            interaction_types={'discussion': 1},
                            first_interaction_date=datetime.now() - timedelta(days=90),
                            last_interaction_date=datetime.now(),
                            relationship_strength=0.0,
                            issues_discussed=1
                        )
                    else:
                        self.edges[pair].issues_discussed += 1
                        self.edges[pair].interaction_count += 1
                        self.edges[pair].interaction_types['discussion'] = self.edges[pair].issues_discussed
    
    def _extract_co_authors(self, commit_message: str) -> Set[str]:
        """Extract co-authors from commit message"""
        co_authors = set()
        
        # Look for "Co-authored-by" patterns
        import re
        co_author_pattern = r'Co-authored-by:\s+(.+?)\s+<'
        matches = re.findall(co_author_pattern, commit_message, re.IGNORECASE)
        
        for match in matches:
            # Extract name (would need additional API calls to get usernames)
            # For now, just use the email or name as identifier
            email_match = re.search(r'<(.+?)>', match)
            if email_match:
                email = email_match.group(1)
                co_authors.add(email)
        
        return co_authors
    
    def _calculate_network_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive network metrics"""
        
        metrics = {}
        
        # Degree centrality
        degree_centrality = nx.degree_centrality(self.network_graph)
        for login, centrality in degree_centrality.items():
            if login in self.nodes:
                self.nodes[login].degree_centrality = centrality
        
        # Betweenness centrality
        betweenness_centrality = nx.betweenness_centrality(self.network_graph)
        for login, centrality in betweenness_centrality.items():
            if login in self.nodes:
                self.nodes[login].betweenness_centrality = centrality
        
        # Closeness centrality
        closeness_centrality = nx.closeness_centrality(self.network_graph)
        for login, centrality in closeness_centrality.items():
            if login in self.nodes:
                self.nodes[login].closeness_centrality = centrality
        
        # Eigenvector centrality (only if graph is connected)
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.network_graph)
            for login, centrality in eigenvector_centrality.items():
                if login in self.nodes:
                    self.nodes[login].eigenvector_centrality = centrality
        except nx.PowerIterationFailedConvergence:
            self.logger.warning("Eigenvector centrality calculation failed")
        
        return {
            'degree_centrality': degree_centrality,
            'betweenness_centrality': betweenness_centrality,
            'closeness_centrality': closeness_centrality
        }
    
    def _detect_community_clusters(self) -> List[CommunityCluster]:
        """Detect community clusters using modularity-based algorithms"""
        
        # Use Louvain algorithm for community detection
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(self.network_graph)
        except ImportError:
            # Fallback to simple connected components if community library not available
            components = list(nx.connected_components(self.network_graph))
            partition = {}
            for i, component in enumerate(components):
                for node in component:
                    partition[node] = i
        
        # Group nodes by community
        communities = defaultdict(list)
        for node, community_id in partition.items():
            communities[community_id].append(node)
        
        # Create community cluster objects
        clusters = []
        for cluster_id, members in communities.items():
            if len(members) < 2:  # Skip single-node clusters
                continue
            
            # Calculate cluster density
            subgraph = self.network_graph.subgraph(members)
            density = nx.density(subgraph)
            clustering_coeff = nx.average_clustering(subgraph)
            
            # Determine cluster role
            cluster_role = self._determine_cluster_role(members, density)
            
            # Calculate cluster metrics
            avg_contributions = statistics.mean([
                self.nodes[member].total_contributions for member in members 
                if member in self.nodes
            ]) if members else 0
            
            # Identify bridge contributors
            bridge_contributors = self._identify_bridge_contributors(members)
            
            cluster = CommunityCluster(
                cluster_id=cluster_id,
                members=set(members),
                density=density,
                avg_clustering_coefficient=clustering_coeff,
                cluster_role=cluster_role,
                avg_contributions_per_member=avg_contributions,
                bridge_contributors=bridge_contributors
            )
            
            clusters.append(cluster)
        
        return clusters
    
    def _determine_cluster_role(self, members: List[str], density: float) -> str:
        """Determine the role/function of a cluster"""
        
        # Analyze cluster characteristics
        total_contributions = sum(
            self.nodes[member].total_contributions for member in members 
            if member in self.nodes
        )
        
        avg_degree = statistics.mean([
            self.nodes[member].degree_centrality for member in members 
            if member in self.nodes
        ]) if members else 0
        
        # Classify based on density and connections
        if density > 0.6 and avg_degree > 0.3:
            return "core"  # Highly connected core group
        elif density > 0.3 and avg_degree > 0.2:
            return "specialized"  # Specialized working group
        else:
            return "peripheral"  # Loosely connected peripheral group
    
    def _identify_bridge_contributors(self, cluster_members: List[str]) -> List[str]:
        """Identify contributors who bridge this cluster to others"""
        
        bridges = []
        
        for member in cluster_members:
            if member not in self.nodes:
                continue
            
            node = self.nodes[member]
            external_connections = 0
            
            # Count connections outside the cluster
            for neighbor in node.collaborators:
                if neighbor not in cluster_members:
                    external_connections += 1
            
            # If significant external connections, classify as bridge
            if external_connections >= 2:
                bridges.append(member)
        
        return bridges
    
    def _identify_contributor_roles(self):
        """Identify roles for all contributors based on network position"""
        
        for login, node in self.nodes.items():
            degree = node.degree_centrality
            betweenness = node.betweenness_centrality
            total_contributions = node.total_contributions
            
            # Role classification based on network metrics and contributions
            if degree >= 0.8 and total_contributions >= 50:
                node.role = "maintainer"
            elif degree >= 0.6 and betweenness >= 0.5:
                node.role = "bridge"
            elif degree >= 0.4 and total_contributions >= 20:
                node.role = "core_member"
            elif degree <= 0.1:
                node.role = "peripheral"
            else:
                node.role = "member"
            
            # Calculate influence score
            influence_score = (
                node.degree_centrality * 0.3 +
                node.betweenness_centrality * 0.3 +
                node.eigenvector_centrality * 0.2 +
                min(1.0, total_contributions / 50) * 0.2
            )
            node.influence_score = influence_score * 100
            
            # Calculate mentoring score (based on review activity and collaboration)
            mentoring_score = min(100, len(node.collaborators) * 10 + node.review_participation * 5)
            node.mentoring_score = mentoring_score
    
    def _analyze_network_health(self) -> Dict[str, Any]:
        """Analyze overall network health and identify key contributors"""
        
        # Sort nodes by different centrality measures
        by_degree = sorted(
            self.nodes.items(), 
            key=lambda x: x[1].degree_centrality, 
            reverse=True
        )
        
        by_betweenness = sorted(
            self.nodes.items(), 
            key=lambda x: x[1].betweenness_centrality, 
            reverse=True
        )
        
        by_influence = sorted(
            self.nodes.items(), 
            key=lambda x: x[1].influence_score, 
            reverse=True
        )
        
        # Count nodes by role
        role_counts = Counter(node.role for node in self.nodes.values())
        
        # Calculate growth rate (simplified - would need historical data)
        growth_rate = 0.0
        if len(self.network_history) >= 2:
            previous_nodes = self.network_history[-2].total_nodes
            current_nodes = len(self.nodes)
            if previous_nodes > 0:
                growth_rate = ((current_nodes - previous_nodes) / previous_nodes) * 100
        
        # Calculate collaboration trend
        collaboration_trend = 0.0
        avg_collaboration_frequency = statistics.mean([
            node.collaboration_frequency for node in self.nodes.values() 
            if node.collaboration_frequency > 0
        ]) if self.nodes else 0
        
        return {
            'most_connected': [login for login, _ in by_degree[:self.centrality_top_k]],
            'key_bridges': [login for login, _ in by_betweenness[:self.centrality_top_k]],
            'most_influential': [login for login, _ in by_influence[:self.centrality_top_k]],
            'isolated_nodes': role_counts.get('peripheral', 0),
            'bridge_nodes': role_counts.get('bridge', 0),
            'core_contributors': role_counts.get('maintainer', 0) + role_counts.get('core_member', 0),
            'peripheral_contributors': role_counts.get('peripheral', 0),
            'growth_rate': growth_rate,
            'collaboration_trend': collaboration_trend
        }
    
    def _calculate_modularity_score(self, clusters: List[CommunityCluster]) -> float:
        """Calculate modularity score for community structure"""
        
        if not clusters:
            return 0.0
        
        # Simple modularity approximation based on cluster density
        total_density = sum(cluster.density for cluster in clusters)
        expected_density = len(clusters) * 0.25  # Expected density for random clustering
        
        if expected_density > 0:
            modularity = min(1.0, total_density / expected_density)
        else:
            modularity = 0.0
        
        return modularity
    
    def _generate_network_recommendations(self) -> List[str]:
        """Generate actionable network improvement recommendations"""
        
        recommendations = []
        
        # Analyze network structure
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)
        
        if total_nodes > 0:
            density = nx.density(self.network_graph)
            
            # Low connectivity recommendations
            if density < 0.1:
                recommendations.append("Increase collaboration opportunities to improve network connectivity")
            
            # Isolated nodes recommendations
            isolated_count = len([node for node in self.nodes.values() if node.degree_centrality < 0.1])
            if isolated_count > total_nodes * 0.3:
                recommendations.append(f"Engage {isolated_count} isolated contributors with targeted outreach")
            
            # Bridge analysis
            bridge_count = len([node for node in self.nodes.values() if node.role == "bridge"])
            if bridge_count == 0:
                recommendations.append("Identify and develop bridge contributors to connect community segments")
            
            # Core contributor retention
            core_count = len([node for node in self.nodes.values() if node.role in ["maintainer", "core_member"]])
            if core_count < total_nodes * 0.2:
                recommendations.append("Develop more core contributors to strengthen community foundation")
            
            # Collaboration diversity
            low_diversity_count = len([
                node for node in self.nodes.values() 
                if node.collaboration_diversity < 0.3
            ])
            if low_diversity_count > total_nodes * 0.4:
                recommendations.append("Encourage diverse collaboration patterns across the community")
        
        return recommendations
    
    def get_contributor_network_profile(self, login: str) -> Optional[NetworkNode]:
        """Get detailed network profile for a specific contributor"""
        return self.nodes.get(login)
    
    def identify_collaboration_opportunities(self, limit: int = 10) -> List[Tuple[str, str, float]]:
        """Identify potential collaboration opportunities between contributors"""
        
        opportunities = []
        
        # Find contributors who could benefit from collaboration
        for login, node in self.nodes.items():
            # Look for contributors with similar expertise but low collaboration
            if node.role in ["member", "peripheral"] and len(node.collaborators) < 3:
                
                # Find potential collaborators (similar contribution patterns)
                for other_login, other_node in self.nodes.items():
                    if (login != other_login and 
                        other_login not in node.collaborators and
                        other_node.role in ["core_member", "maintainer", "bridge"]):
                        
                        # Calculate collaboration potential
                        potential_score = (
                            other_node.mentoring_score * 0.4 +
                            min(100, len(other_node.collaborators) * 5) * 0.3 +
                            node.total_contributions * 2 * 0.3
                        )
                        
                        if potential_score > 50:  # Threshold for collaboration potential
                            opportunities.append((login, other_login, potential_score))
        
        # Sort by potential and return top opportunities
        opportunities.sort(key=lambda x: x[2], reverse=True)
        return opportunities[:limit]
    
    def get_network_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive network summary report"""
        
        if not self.network_history:
            return {"error": "No network data available"}
        
        latest_analysis = self.network_history[-1]
        
        # Node role distribution
        role_distribution = Counter(node.role for node in self.nodes.values())
        
        # Top contributors by different metrics
        top_by_centrality = sorted(
            self.nodes.items(), 
            key=lambda x: x[1].degree_centrality, 
            reverse=True
        )[:5]
        
        top_by_influence = sorted(
            self.nodes.items(), 
            key=lambda x: x[1].influence_score, 
            reverse=True
        )[:5]
        
        # Cluster analysis
        cluster_summary = []
        for cluster in latest_analysis.identified_clusters:
            cluster_summary.append({
                "cluster_id": cluster.cluster_id,
                "size": len(cluster.members),
                "density": cluster.density,
                "role": cluster.cluster_role,
                "bridge_contributors": cluster.bridge_contributors
            })
        
        return {
            "network_structure": {
                "total_contributors": latest_analysis.total_nodes,
                "total_connections": latest_analysis.total_edges,
                "network_density": latest_analysis.network_density,
                "avg_clustering": latest_analysis.avg_clustering_coefficient,
                "modularity": latest_analysis.modularity_score
            },
            "contributor_roles": dict(role_distribution),
            "top_contributors": {
                "by_centrality": [login for login, _ in top_by_centrality],
                "by_influence": [login for login, _ in top_by_influence]
            },
            "community_clusters": cluster_summary,
            "network_health": {
                "isolated_contributors": latest_analysis.isolated_nodes,
                "bridge_contributors": latest_analysis.bridge_nodes,
                "core_contributors": latest_analysis.core_contributors,
                "growth_rate": latest_analysis.growth_rate
            },
            "key_insights": {
                "most_connected": latest_analysis.most_connected[:3],
                "key_bridges": latest_analysis.key_bridges[:3],
                "most_influential": latest_analysis.most_influential[:3]
            },
            "recommendations": latest_analysis.network_recommendations
        }