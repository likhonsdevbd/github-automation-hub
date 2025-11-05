"""
Benchmarking Against Similar Repositories

This module provides capabilities to benchmark repository growth against
similar repositories, identifying relative performance and competitive positioning.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import statistics
import warnings


@dataclass
class RepositoryProfile:
    """Data class for repository profile information."""
    name: str
    owner: str
    language: str
    stars: int
    forks: int
    watchers: int
    age_days: int
    topics: List[str]
    description: str
    license: Optional[str]
    size_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'owner': self.owner,
            'language': self.language,
            'stars': self.stars,
            'forks': self.forks,
            'watchers': self.watchers,
            'age_days': self.age_days,
            'topics': self.topics,
            'description': self.description,
            'license': self.license,
            'size_mb': self.size_mb
        }


@dataclass
class BenchmarkResult:
    """Data class for benchmark comparison results."""
    metric: str
    target_value: float
    peer_values: List[float]
    percentile_rank: float
    z_score: float
    performance_rating: str
    gap_from_median: float
    recommendations: List[str]


@dataclass
class CompetitiveAnalysis:
    """Data class for competitive analysis results."""
    repository_name: str
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    market_position: str
    peer_repositories: List[str]
    benchmark_results: List[BenchmarkResult]
    growth_opportunities: List[str]
    risk_areas: List[str]


class BenchmarkAnalyzer:
    """
    Repository benchmarking system that compares growth metrics
    against similar repositories and provides competitive insights.
    """
    
    def __init__(self):
        self.peer_repositories = []
        self.repository_index = {}
        self.growth_data = {}
        self.comparison_cache = {}
        
    def add_repository_data(self, repo_profile: RepositoryProfile, 
                          growth_data: List) -> None:
        """
        Add repository profile and growth data for benchmarking.
        
        Args:
            repo_profile: Repository profile information
            growth_data: Historical growth metrics for the repository
        """
        repo_key = f"{repo_profile.owner}/{repo_profile.name}"
        
        # Store repository profile
        self.repository_index[repo_key] = repo_profile
        
        # Store growth data
        self.growth_data[repo_key] = growth_data
        
        # Add to peer repository list
        self.peer_repositories.append(repo_key)
    
    def find_similar_repositories(self, target_repo: str, 
                                 similarity_criteria: Dict[str, Any]) -> List[str]:
        """
        Find repositories similar to the target based on specified criteria.
        
        Args:
            target_repo: Target repository identifier (owner/name)
            similarity_criteria: Criteria for similarity (language, age, size, etc.)
            
        Returns:
            List of similar repository identifiers
        """
        if target_repo not in self.repository_index:
            raise ValueError(f"Repository {target_repo} not found in index")
        
        target_profile = self.repository_index[target_repo]
        similar_repos = []
        
        for repo_key in self.peer_repositories:
            if repo_key == target_repo:
                continue
                
            repo_profile = self.repository_index[repo_key]
            similarity_score = self._calculate_similarity_score(
                target_profile, repo_profile, similarity_criteria
            )
            
            if similarity_score > 0.6:  # Minimum 60% similarity
                similar_repos.append((repo_key, similarity_score))
        
        # Sort by similarity score and return top matches
        similar_repos.sort(key=lambda x: x[1], reverse=True)
        return [repo[0] for repo in similar_repos[:10]]  # Top 10 matches
    
    def _calculate_similarity_score(self, target: RepositoryProfile, 
                                  peer: RepositoryProfile, 
                                  criteria: Dict[str, Any]) -> float:
        """Calculate similarity score between two repositories."""
        score = 0.0
        weight_sum = 0.0
        
        # Language similarity (weight: 0.3)
        if criteria.get('language_weight', 0.3) > 0:
            language_weight = criteria.get('language_weight', 0.3)
            if target.language.lower() == peer.language.lower():
                score += 1.0 * language_weight
            weight_sum += language_weight
        
        # Age similarity (weight: 0.2)
        if criteria.get('age_weight', 0.2) > 0:
            age_weight = criteria.get('age_weight', 0.2)
            age_diff = abs(target.age_days - peer.age_days)
            age_similarity = max(0, 1 - (age_diff / max(target.age_days, peer.age_days, 1)))
            score += age_similarity * age_weight
            weight_sum += age_weight
        
        # Size similarity (weight: 0.2)
        if criteria.get('size_weight', 0.2) > 0:
            size_weight = criteria.get('size_weight', 0.2)
            size_diff = abs(target.size_mb - peer.size_mb)
            size_similarity = max(0, 1 - (size_diff / max(target.size_mb, peer.size_mb, 1)))
            score += size_similarity * size_weight
            weight_sum += size_weight
        
        # Stars similarity (weight: 0.15)
        if criteria.get('stars_weight', 0.15) > 0:
            stars_weight = criteria.get('stars_weight', 0.15)
            stars_diff = abs(np.log(target.stars + 1) - np.log(peer.stars + 1))
            stars_similarity = max(0, 1 - stars_diff / 10)  # Normalize log difference
            score += stars_similarity * stars_weight
            weight_sum += stars_weight
        
        # Topic similarity (weight: 0.15)
        if criteria.get('topics_weight', 0.15) > 0:
            topics_weight = criteria.get('topics_weight', 0.15)
            if target.topics and peer.topics:
                common_topics = set(target.topics) & set(peer.topics)
                total_topics = set(target.topics) | set(peer.topics)
                topic_similarity = len(common_topics) / len(total_topics) if total_topics else 0
                score += topic_similarity * topics_weight
                weight_sum += topics_weight
        
        return score / weight_sum if weight_sum > 0 else 0.0
    
    def benchmark_repository(self, target_repo: str, 
                           similar_repos: Optional[List[str]] = None,
                           similarity_criteria: Optional[Dict[str, Any]] = None) -> CompetitiveAnalysis:
        """
        Perform comprehensive benchmark analysis for a repository.
        
        Args:
            target_repo: Target repository identifier
            similar_repos: List of similar repositories (auto-detect if None)
            similarity_criteria: Criteria for finding similar repos
            
        Returns:
            Competitive analysis results
        """
        if target_repo not in self.growth_data:
            raise ValueError(f"No growth data found for repository {target_repo}")
        
        target_profile = self.repository_index[target_repo]
        target_growth_data = self.growth_data[target_repo]
        
        # Find similar repositories if not provided
        if similar_repos is None:
            similarity_criteria = similarity_criteria or {
                'language_weight': 0.3,
                'age_weight': 0.2,
                'size_weight': 0.2,
                'stars_weight': 0.15,
                'topics_weight': 0.15
            }
            similar_repos = self.find_similar_repositories(target_repo, similarity_criteria)
        
        if not similar_repos:
            raise ValueError("No similar repositories found for comparison")
        
        # Perform benchmark analysis for each metric
        benchmark_results = []
        
        # Analyze current metrics
        current_metrics = self._extract_current_metrics(target_growth_data)
        metrics_to_analyze = ['stars', 'forks', 'watchers', 'contributors', 'issues', 'pull_requests']
        
        for metric in metrics_to_analyze:
            target_value = current_metrics.get(metric, 0)
            
            if target_value > 0:
                peer_values = []
                for peer_repo in similar_repos:
                    if peer_repo in self.growth_data:
                        peer_metrics = self._extract_current_metrics(self.growth_data[peer_repo])
                        peer_values.append(peer_metrics.get(metric, 0))
                
                if peer_values:
                    benchmark_result = self._perform_metric_benchmark(
                        metric, target_value, peer_values, target_repo
                    )
                    benchmark_results.append(benchmark_result)
        
        # Analyze growth rates
        growth_metrics = ['stars_growth_rate', 'forks_growth_rate', 'commits_growth_rate']
        
        for growth_metric in growth_metrics:
            target_growth = self._calculate_growth_rate(target_growth_data, growth_metric)
            
            if target_growth is not None:
                peer_growth_rates = []
                for peer_repo in similar_repos:
                    if peer_repo in self.growth_data:
                        peer_growth = self._calculate_growth_rate(
                            self.growth_data[peer_repo], growth_metric
                        )
                        if peer_growth is not None:
                            peer_growth_rates.append(peer_growth)
                
                if peer_growth_rates:
                    benchmark_result = self._perform_growth_benchmark(
                        growth_metric, target_growth, peer_growth_rates, target_repo
                    )
                    benchmark_results.append(benchmark_result)
        
        # Perform overall competitive analysis
        competitive_analysis = self._create_competitive_analysis(
            target_repo, similar_repos, benchmark_results
        )
        
        return competitive_analysis
    
    def _extract_current_metrics(self, growth_data: List) -> Dict[str, float]:
        """Extract current metric values from growth data."""
        if not growth_data:
            return {}
        
        latest_data = max(growth_data, key=lambda x: x.date)
        
        return {
            'stars': latest_data.stars,
            'forks': latest_data.forks,
            'watchers': latest_data.watchers,
            'contributors': latest_data.contributors,
            'issues': latest_data.issues,
            'pull_requests': latest_data.pull_requests
        }
    
    def _calculate_growth_rate(self, growth_data: List, metric: str) -> Optional[float]:
        """Calculate growth rate for a specific metric."""
        if len(growth_data) < 2:
            return None
        
        sorted_data = sorted(growth_data, key=lambda x: x.date)
        
        try:
            if metric == 'stars_growth_rate':
                start_value = sorted_data[0].stars
                end_value = sorted_data[-1].stars
            elif metric == 'forks_growth_rate':
                start_value = sorted_data[0].forks
                end_value = sorted_data[-1].forks
            elif metric == 'commits_growth_rate':
                start_value = sorted_data[0].commits
                end_value = sorted_data[-1].commits
            else:
                return None
            
            if start_value > 0:
                return (end_value - start_value) / start_value
            else:
                return 0.0 if end_value == 0 else float('inf')
        
        except Exception:
            return None
    
    def _perform_metric_benchmark(self, metric: str, target_value: float, 
                                peer_values: List[float], target_repo: str) -> BenchmarkResult:
        """Perform benchmark analysis for a single metric."""
        if not peer_values:
            peer_values = [0]
        
        # Calculate statistics
        peer_mean = statistics.mean(peer_values)
        peer_median = statistics.median(peer_values)
        
        # Calculate percentile rank
        percentile_rank = sum(1 for pv in peer_values if pv <= target_value) / len(peer_values) * 100
        
        # Calculate z-score
        if len(peer_values) > 1:
            peer_std = statistics.stdev(peer_values)
            z_score = (target_value - peer_mean) / peer_std if peer_std > 0 else 0
        else:
            z_score = 0
        
        # Determine performance rating
        if percentile_rank >= 90:
            performance_rating = "excellent"
        elif percentile_rank >= 75:
            performance_rating = "good"
        elif percentile_rank >= 50:
            performance_rating = "average"
        elif percentile_rank >= 25:
            performance_rating = "below_average"
        else:
            performance_rating = "poor"
        
        # Calculate gap from median
        gap_from_median = (target_value - peer_median) / peer_median * 100 if peer_median > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_metric_recommendations(
            metric, percentile_rank, performance_rating, gap_from_median
        )
        
        return BenchmarkResult(
            metric=metric,
            target_value=target_value,
            peer_values=peer_values,
            percentile_rank=percentile_rank,
            z_score=z_score,
            performance_rating=performance_rating,
            gap_from_median=gap_from_median,
            recommendations=recommendations
        )
    
    def _perform_growth_benchmark(self, metric: str, target_growth: float, 
                                peer_growth_rates: List[float], target_repo: str) -> BenchmarkResult:
        """Perform benchmark analysis for growth rates."""
        # Filter out infinite values
        valid_peer_rates = [rate for rate in peer_growth_rates if rate != float('inf') and not np.isnan(rate)]
        
        if not valid_peer_rates:
            valid_peer_rates = [0]
        
        # Cap extreme growth rates for better comparison
        capped_target_growth = min(max(target_growth, -1), 5)  # Cap between -100% and 500%
        capped_peer_rates = [min(max(rate, -1), 5) for rate in valid_peer_rates]
        
        peer_mean = statistics.mean(capped_peer_rates)
        peer_median = statistics.median(capped_peer_rates)
        
        # Calculate percentile rank
        percentile_rank = sum(1 for pv in capped_peer_rates if pv <= capped_target_growth) / len(capped_peer_rates) * 100
        
        # Calculate z-score
        if len(capped_peer_rates) > 1:
            peer_std = statistics.stdev(capped_peer_rates)
            z_score = (capped_target_growth - peer_mean) / peer_std if peer_std > 0 else 0
        else:
            z_score = 0
        
        # Determine performance rating
        if percentile_rank >= 80:
            performance_rating = "high_growth"
        elif percentile_rank >= 60:
            performance_rating = "moderate_growth"
        elif percentile_rank >= 40:
            performance_rating = "average_growth"
        elif percentile_rank >= 20:
            performance_rating = "slow_growth"
        else:
            performance_rating = "stagnant"
        
        # Calculate gap from median (as percentage)
        gap_from_median = (capped_target_growth - peer_median) * 100
        
        # Generate recommendations
        recommendations = self._generate_growth_recommendations(
            metric, percentile_rank, performance_rating, gap_from_median
        )
        
        return BenchmarkResult(
            metric=metric,
            target_value=capped_target_growth,
            peer_values=capped_peer_rates,
            percentile_rank=percentile_rank,
            z_score=z_score,
            performance_rating=performance_rating,
            gap_from_median=gap_from_median,
            recommendations=recommendations
        )
    
    def _generate_metric_recommendations(self, metric: str, percentile_rank: float, 
                                       performance_rating: str, gap_from_median: float) -> List[str]:
        """Generate recommendations based on metric performance."""
        recommendations = []
        
        if performance_rating == "excellent":
            recommendations.append(f"Maintain excellent performance in {metric}")
            recommendations.append("Document successful strategies for other metrics")
        elif performance_rating == "good":
            recommendations.append(f"Strong performance in {metric} - consider optimization to reach excellence")
        elif performance_rating == "average":
            recommendations.append(f"{metric} performance is average - investigate improvement opportunities")
        elif performance_rating == "below_average":
            recommendations.append(f"{metric} performance below average - prioritize improvement efforts")
            recommendations.append("Analyze peer repositories with better performance for best practices")
        elif performance_rating == "poor":
            recommendations.append(f"Poor {metric} performance - immediate action recommended")
            recommendations.append("Conduct detailed analysis of top-performing similar repositories")
        
        # Specific metric recommendations
        if metric == "stars":
            if percentile_rank < 50:
                recommendations.append("Focus on visibility: improve documentation, examples, and marketing")
        elif metric == "forks":
            if percentile_rank < 50:
                recommendations.append("Encourage contributions: improve contribution guidelines and onboarding")
        elif metric == "watchers":
            if percentile_rank < 50:
                recommendations.append("Increase engagement: regular updates, community interaction")
        elif metric == "issues":
            if percentile_rank > 75:
                recommendations.append("High issue volume - consider improving testing and documentation")
            elif percentile_rank < 25:
                recommendations.append("Low issue engagement - may indicate visibility or usability issues")
        
        return recommendations
    
    def _generate_growth_recommendations(self, metric: str, percentile_rank: float, 
                                       performance_rating: str, gap_from_median: float) -> List[str]:
        """Generate recommendations based on growth rate performance."""
        recommendations = []
        
        if "high_growth" in performance_rating:
            recommendations.append("Excellent growth rate - maintain current momentum")
            recommendations.append("Monitor for sustainability and potential challenges")
        elif "moderate_growth" in performance_rating:
            recommendations.append("Steady growth - consider strategies to accelerate")
        elif "average_growth" in performance_rating:
            recommendations.append("Average growth rate - identify growth acceleration opportunities")
        elif "slow_growth" in performance_rating:
            recommendations.append("Slow growth detected - review strategy and identify bottlenecks")
        elif "stagnant" in performance_rating:
            recommendations.append("Growth stagnation - urgent strategy review and intervention needed")
        
        # Specific growth metric recommendations
        if "stars_growth" in metric:
            if percentile_rank < 30:
                recommendations.append("Focus on visibility: SEO optimization, community engagement")
        elif "forks_growth" in metric:
            if percentile_rank < 30:
                recommendations.append("Encourage forking: improve contribution process, clear examples")
        elif "commits_growth" in metric:
            if percentile_rank < 30:
                recommendations.append("Boost development activity: feature roadmap, contributor onboarding")
        
        return recommendations
    
    def _create_competitive_analysis(self, target_repo: str, 
                                   similar_repos: List[str], 
                                   benchmark_results: List[BenchmarkResult]) -> CompetitiveAnalysis:
        """Create comprehensive competitive analysis."""
        target_profile = self.repository_index[target_repo]
        
        # Calculate overall score
        scores = []
        for result in benchmark_results:
            if result.performance_rating in ["excellent", "good", "high_growth"]:
                scores.append(1.0)
            elif result.performance_rating in ["average", "moderate_growth"]:
                scores.append(0.7)
            elif result.performance_rating in ["below_average", "slow_growth"]:
                scores.append(0.4)
            else:
                scores.append(0.1)
        
        overall_score = statistics.mean(scores) if scores else 0.0
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for result in benchmark_results:
            if result.performance_rating in ["excellent", "good", "high_growth"]:
                strengths.append(f"{result.metric}: {result.performance_rating} ({result.percentile_rank:.1f}th percentile)")
            elif result.performance_rating in ["poor", "stagnant"]:
                weaknesses.append(f"{result.metric}: {result.performance_rating} ({result.percentile_rank:.1f}th percentile)")
        
        # Determine market position
        if overall_score >= 0.8:
            market_position = "leader"
        elif overall_score >= 0.6:
            market_position = "strong_competitor"
        elif overall_score >= 0.4:
            market_position = "average_performer"
        else:
            market_position = "lagging"
        
        # Identify growth opportunities
        growth_opportunities = []
        risk_areas = []
        
        for result in benchmark_results:
            if result.gap_from_median < -20:  # More than 20% below median
                growth_opportunities.append(f"Improve {result.metric} - {result.gap_from_median:.1f}% below peer median")
            elif result.z_score < -1:  # More than 1 standard deviation below mean
                risk_areas.append(f"{result.metric} performance significantly below peers")
        
        # Add general opportunities and risks
        if overall_score < 0.5:
            growth_opportunities.append("Overall strategy optimization needed to reach peer performance levels")
        
        if any("stagnant" in r.performance_rating or "poor" in r.performance_rating for r in benchmark_results):
            risk_areas.append("Multiple underperforming metrics indicate potential strategy issues")
        
        return CompetitiveAnalysis(
            repository_name=target_repo,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            market_position=market_position,
            peer_repositories=similar_repos,
            benchmark_results=benchmark_results,
            growth_opportunities=growth_opportunities,
            risk_areas=risk_areas
        )
    
    def compare_specific_repositories(self, repo1: str, repo2: str) -> Dict[str, Any]:
        """
        Direct comparison between two specific repositories.
        
        Args:
            repo1: First repository identifier
            repo2: Second repository identifier
            
        Returns:
            Comparison results dictionary
        """
        if repo1 not in self.growth_data or repo2 not in self.growth_data:
            raise ValueError("One or both repositories not found in dataset")
        
        profile1 = self.repository_index[repo1]
        profile2 = self.repository_index[repo2]
        
        data1 = self.growth_data[repo1]
        data2 = self.growth_data[repo2]
        
        # Extract current metrics
        metrics1 = self._extract_current_metrics(data1)
        metrics2 = self._extract_current_metrics(data2)
        
        comparison = {
            'repo1': {
                'identifier': repo1,
                'profile': profile1.to_dict(),
                'current_metrics': metrics1
            },
            'repo2': {
                'identifier': repo2,
                'profile': profile2.to_dict(),
                'current_metrics': metrics2
            },
            'comparison': {}
        }
        
        # Compare each metric
        for metric in ['stars', 'forks', 'watchers', 'contributors', 'issues', 'pull_requests']:
            value1 = metrics1.get(metric, 0)
            value2 = metrics2.get(metric, 0)
            
            if value1 > 0 and value2 > 0:
                ratio = value1 / value2
                difference = value1 - value2
                
                comparison['comparison'][metric] = {
                    'repo1_value': value1,
                    'repo2_value': value2,
                    'ratio': ratio,
                    'difference': difference,
                    'leader': repo1 if value1 > value2 else repo2,
                    'percentage_diff': ((value1 - value2) / value2) * 100 if value2 > 0 else 0
                }
        
        # Compare growth rates
        for growth_metric in ['stars_growth_rate', 'forks_growth_rate', 'commits_growth_rate']:
            growth1 = self._calculate_growth_rate(data1, growth_metric)
            growth2 = self._calculate_growth_rate(data2, growth_metric)
            
            if growth1 is not None and growth2 is not None:
                comparison['comparison'][growth_metric] = {
                    'repo1_growth': growth1,
                    'repo2_growth': growth2,
                    'difference': growth1 - growth2,
                    'leader': repo1 if growth1 > growth2 else repo2,
                    'relative_difference': ((growth1 - growth2) / abs(growth2)) * 100 if growth2 != 0 else 0
                }
        
        return comparison
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """
        Get a summary of benchmarking capabilities and data.
        
        Returns:
            Dictionary containing benchmark summary
        """
        return {
            'total_repositories': len(self.peer_repositories),
            'tracked_repositories': list(self.peer_repositories),
            'languages_covered': list(set(repo.language for repo in self.repository_index.values())),
            'age_range_days': {
                'min': min(repo.age_days for repo in self.repository_index.values()),
                'max': max(repo.age_days for repo in self.repository_index.values()),
                'average': statistics.mean(repo.age_days for repo in self.repository_index.values())
            },
            'stars_range': {
                'min': min(repo.stars for repo in self.repository_index.values()),
                'max': max(repo.stars for repo in self.repository_index.values()),
                'median': statistics.median(repo.stars for repo in self.repository_index.values())
            }
        }