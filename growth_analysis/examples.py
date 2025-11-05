"""
Example usage and demonstration of the Growth Analysis Engine

This script demonstrates how to use all components of the growth analysis engine
to perform comprehensive repository growth analysis and strategy recommendations.
"""

import random
from datetime import datetime, timedelta
from typing import List

# Import growth analysis components
from .core import GrowthAnalyzer, GrowthMetrics, GrowthPattern
from .predictors import GrowthPredictor
from .anomaly_detector import AnomalyDetector
from .benchmarking import BenchmarkAnalyzer, RepositoryProfile
from .forecasting import TrendForecaster
from .recommendations import StrategyRecommender, StrategicPlan


def generate_sample_growth_data(days: int = 90, start_stars: int = 100) -> List[GrowthMetrics]:
    """
    Generate realistic sample growth data for demonstration.
    
    Args:
        days: Number of days of data to generate
        start_stars: Starting number of stars
        
    Returns:
        List of GrowthMetrics objects
    """
    data = []
    current_date = datetime.now() - timedelta(days=days)
    
    # Base growth parameters
    base_growth_rate = 0.02  # 2% daily growth
    seasonality_amplitude = 0.1
    volatility = 0.05
    
    # Initialize metrics
    stars = start_stars
    forks = max(1, int(start_stars * 0.3))
    watchers = max(1, int(start_stars * 0.5))
    issues = random.randint(5, 20)
    pull_requests = random.randint(2, 10)
    commits = random.randint(10, 50)
    contributors = random.randint(1, 5)
    subscribers = max(1, int(start_stars * 0.4))
    
    for day in range(days):
        # Base growth with some randomness
        daily_stars_growth = stars * base_growth_rate * random.uniform(0.5, 1.5)
        daily_forks_growth = forks * base_growth_rate * 0.3 * random.uniform(0.5, 1.5)
        daily_watchers_growth = watchers * base_growth_rate * 0.4 * random.uniform(0.5, 1.5)
        
        # Apply seasonality (weekend dips)
        if current_date.weekday() >= 5:  # Weekend
            daily_stars_growth *= 0.7
            daily_forks_growth *= 0.8
            daily_watchers_growth *= 0.6
        
        # Add some growth anomalies occasionally
        if random.random() < 0.05:  # 5% chance of anomaly
            anomaly_multiplier = random.uniform(2, 5)  # Big spike
            daily_stars_growth *= anomaly_multiplier
            daily_forks_growth *= anomaly_multiplier
            daily_watchers_growth *= anomaly_multiplier
        
        # Update metrics
        stars += int(daily_stars_growth)
        forks += int(daily_forks_growth)
        watchers += int(daily_watchers_growth)
        
        # Update other metrics with more realistic patterns
        issues += random.randint(-2, 5)
        issues = max(0, issues)
        
        pull_requests += random.randint(-1, 3)
        pull_requests = max(0, pull_requests)
        
        commits += random.randint(-5, 15)
        commits = max(0, commits)
        
        contributors += random.randint(0, 2)
        
        subscribers += int(watchers * 0.1 * random.uniform(0.8, 1.2))
        
        # Create data point
        metrics = GrowthMetrics(
            date=current_date,
            stars=stars,
            forks=forks,
            watchers=watchers,
            issues=issues,
            pull_requests=pull_requests,
            commits=commits,
            contributors=contributors,
            subscribers=subscribers
        )
        
        data.append(metrics)
        current_date += timedelta(days=1)
    
    return data


def generate_sample_peer_repositories() -> List[RepositoryProfile]:
    """Generate sample peer repository profiles for benchmarking."""
    repositories = [
        RepositoryProfile(
            name="awesome-library",
            owner="developer1",
            language="Python",
            stars=1500,
            forks=300,
            watchers=450,
            age_days=800,
            topics=["machine-learning", "data-science", "api"],
            description="A comprehensive machine learning library",
            license="MIT",
            size_mb=45.2
        ),
        RepositoryProfile(
            name="web-framework",
            owner="devteam",
            language="JavaScript",
            stars=2800,
            forks=550,
            watchers=820,
            age_days=1200,
            topics=["web", "framework", "frontend"],
            description="Modern web development framework",
            license="Apache-2.0",
            size_mb=78.9
        ),
        RepositoryProfile(
            name="data-processor",
            owner="analytics-corp",
            language="Python",
            stars=850,
            forks=120,
            watchers=200,
            age_days=600,
            topics=["data", "processing", "analytics"],
            description="Large-scale data processing toolkit",
            license="GPL-3.0",
            size_mb=123.4
        ),
        RepositoryProfile(
            name="mobile-sdk",
            owner="mobile-devs",
            language="Swift",
            stars=420,
            forks=85,
            watchers=120,
            age_days=450,
            topics=["mobile", "sdk", "ios"],
            description="iOS mobile development SDK",
            license="MIT",
            size_mb=23.1
        ),
        RepositoryProfile(
            name="api-gateway",
            owner="backend-team",
            language="Go",
            stars=1200,
            forks=200,
            watchers=350,
            age_days=900,
            topics=["api", "gateway", "microservices"],
            description="Scalable API gateway solution",
            license="BSD-3-Clause",
            size_mb=34.7
        )
    ]
    
    return repositories


def run_comprehensive_growth_analysis():
    """Run a comprehensive growth analysis demonstration."""
    
    print("🚀 Growth Analysis Engine - Comprehensive Demo")
    print("=" * 60)
    
    # Step 1: Generate sample data
    print("\n📊 Step 1: Generating sample growth data...")
    growth_data = generate_sample_growth_data(days=120, start_stars=150)
    print(f"Generated {len(growth_data)} days of growth data")
    print(f"Date range: {growth_data[0].date.strftime('%Y-%m-%d')} to {growth_data[-1].date.strftime('%Y-%m-%d')}")
    print(f"Stars growth: {growth_data[0].stars} → {growth_data[-1].stars}")
    print(f"Forks growth: {growth_data[0].forks} → {growth_data[-1].forks}")
    
    # Step 2: Core Growth Pattern Analysis
    print("\n🔍 Step 2: Analyzing growth patterns...")
    analyzer = GrowthAnalyzer()
    analyzer.add_growth_data(growth_data)
    patterns = analyzer.analyze_growth_patterns()
    summary = analyzer.get_growth_summary()
    
    print(f"Detected {len(patterns)} growth patterns:")
    for pattern in patterns:
        print(f"  • {pattern.pattern_type}: {pattern.description}")
        print(f"    Confidence: {pattern.confidence:.2f}, Period: {pattern.start_date.strftime('%Y-%m-%d')}")
    
    # Step 3: Predictive Modeling
    print("\n🔮 Step 3: Building predictive models...")
    predictor = GrowthPredictor()
    try:
        model_performance = predictor.train_models(growth_data, target_metric='stars')
        print("Model performance:")
        for model_name, performance in model_performance.items():
            print(f"  • {model_name}: R² = {performance.r2_score:.3f}, RMSE = {performance.rmse:.1f}")
        
        # Generate predictions
        predictions = predictor.predict(growth_data[-1], days_ahead=30)
        print(f"\nGenerated {len(predictions)} days of predictions")
        print(f"Stars forecast: {predictions[0].predicted_value:.0f} → {predictions[-1].predicted_value:.0f}")
        print(f"Confidence range: {predictions[-1].confidence_lower:.0f} - {predictions[-1].confidence_upper:.0f}")
        
    except Exception as e:
        print(f"Predictive modeling failed: {e}")
        predictions = []
    
    # Step 4: Anomaly Detection
    print("\n🚨 Step 4: Detecting anomalies...")
    detector = AnomalyDetector()
    anomalies, anomaly_patterns = detector.detect_anomalies(growth_data)
    
    print(f"Detected {len(anomalies)} anomalies:")
    for anomaly in anomalies[:5]:  # Show first 5
        print(f"  • {anomaly.date.strftime('%Y-%m-%d')}: {anomaly.metric} = {anomaly.value:.0f} ({anomaly.severity})")
    
    print(f"\nDetected {len(anomaly_patterns)} anomaly patterns:")
    for pattern in anomaly_patterns:
        print(f"  • {pattern.pattern_type}: {pattern.description}")
    
    # Step 5: Benchmarking Analysis
    print("\n📈 Step 5: Benchmarking against peer repositories...")
    benchmarker = BenchmarkAnalyzer()
    
    # Add peer repositories
    peer_repos = generate_sample_peer_repositories()
    for peer_repo in peer_repos:
        peer_growth_data = generate_sample_growth_data(
            days=90, 
            start_stars=int(peer_repo.stars * 0.1)  # Simulate smaller initial growth
        )
        benchmarker.add_repository_data(peer_repo, peer_growth_data)
    
    # Add our target repository
    target_repo = RepositoryProfile(
        name="target-repo",
        owner="demo",
        language="Python",
        stars=growth_data[-1].stars,
        forks=growth_data[-1].forks,
        watchers=growth_data[-1].watchers,
        age_days=365,
        topics=["growth", "analysis", "automation"],
        description="Repository for growth analysis demo",
        license="MIT",
        size_mb=15.0
    )
    benchmarker.add_repository_data(target_repo, growth_data)
    
    # Perform benchmarking
    try:
        competitive_analysis = benchmarker.benchmark_repository("demo/target-repo")
        print(f"Competitive analysis complete:")
        print(f"  • Overall score: {competitive_analysis.overall_score:.2f}")
        print(f"  • Market position: {competitive_analysis.market_position}")
        print(f"  • Strengths: {len(competitive_analysis.strengths)}")
        print(f"  • Weaknesses: {len(competitive_analysis.weaknesses)}")
        
        # Show top benchmark results
        print("\nTop benchmark results:")
        for result in competitive_analysis.benchmark_results[:3]:
            print(f"  • {result.metric}: {result.performance_rating} ({result.percentile_rank:.1f}th percentile)")
            
    except Exception as e:
        print(f"Benchmarking failed: {e}")
        competitive_analysis = None
    
    # Step 6: Trend Forecasting
    print("\n📉 Step 6: Analyzing trends and forecasting...")
    forecaster = TrendForecaster()
    try:
        trend_analysis = forecaster.analyze_and_forecast(
            growth_data, 
            target_metric='stars',
            forecast_days=30
        )
        
        print(f"Trend analysis complete:")
        print(f"  • Overall trend: {trend_analysis.overall_trend}")
        print(f"  • Trend strength: {trend_analysis.trend_strength:.2f}")
        print(f"  • Growth rate: {trend_analysis.growth_rate:.1%}")
        print(f"  • Seasonality detected: {trend_analysis.seasonality_detected}")
        print(f"  • Confidence: {trend_analysis.confidence_assessment}")
        
        # Show forecast summary
        forecast_summary = forecaster.get_forecast_summary(trend_analysis)
        print(f"\nForecast insights:")
        for insight in forecast_summary['key_insights'][:3]:
            print(f"  • {insight}")
            
    except Exception as e:
        print(f"Trend forecasting failed: {e}")
        trend_analysis = None
    
    # Step 7: Strategy Recommendations
    print("\n💡 Step 7: Generating strategic recommendations...")
    recommender = StrategyRecommender()
    
    try:
        strategic_plan = recommender.generate_strategic_plan(
            repo_name="demo/target-repo",
            growth_patterns=patterns,
            predictions=predictions,
            anomalies=anomalies,
            anomaly_patterns=anomaly_patterns,
            competitive_analysis=competitive_analysis,
            trend_analysis=trend_analysis
        )
        
        print(f"Strategic plan generated:")
        print(f"  • Current status: {strategic_plan.current_status}")
        print(f"  • Overall score: {strategic_plan.overall_score:.2f}")
        print(f"  • Strategic priorities: {len(strategic_plan.strategic_priorities)}")
        
        print(f"\nImmediate actions ({len(strategic_plan.immediate_actions)}):")
        for action in strategic_plan.immediate_actions:
            print(f"  • {action.title} ({action.priority} priority)")
        
        print(f"\nMedium-term actions ({len(strategic_plan.medium_term_actions)}):")
        for action in strategic_plan.medium_term_actions:
            print(f"  • {action.title}")
        
        print(f"\nLong-term actions ({len(strategic_plan.long_term_actions)}):")
        for action in strategic_plan.long_term_actions:
            print(f"  • {action.title}")
        
        # Show strategy summary
        strategy_summary = recommender.get_strategy_summary(strategic_plan)
        print(f"\nStrategy summary:")
        print(f"  • Status: {strategy_summary['overall_assessment']['status_description']}")
        print(f"  • Risk level: {strategy_summary['risk_level']}")
        print(f"  • Implementation timeline: {strategy_summary['implementation_roadmap']['estimated_completion']}")
        
    except Exception as e:
        print(f"Strategy recommendation failed: {e}")
    
    print("\n✅ Growth analysis demo complete!")
    print("\nThis demonstrates the complete capabilities of the Growth Analysis Engine:")
    print("  ✓ Pattern detection and analysis")
    print("  ✓ Predictive modeling and forecasting")
    print("  ✓ Anomaly detection and monitoring")
    print("  ✓ Competitive benchmarking")
    print("  ✓ Trend analysis and confidence intervals")
    print("  ✓ Strategic recommendations and action planning")


def demonstrate_individual_components():
    """Demonstrate individual components of the growth analysis engine."""
    
    print("\n" + "="*60)
    print("INDIVIDUAL COMPONENT DEMONSTRATIONS")
    print("="*60)
    
    # Generate data once
    growth_data = generate_sample_growth_data(days=60, start_stars=100)
    
    # Core Analysis Demo
    print("\n1️⃣ CORE GROWTH ANALYSIS")
    print("-" * 30)
    analyzer = GrowthAnalyzer()
    analyzer.add_growth_data(growth_data)
    
    # Simulate some growth issues
    growth_data[-5].stars -= 50  # Create an anomaly
    growth_data[-3].stars += 100  # Create a spike
    
    patterns = analyzer.analyze_growth_patterns()
    print(f"Growth patterns detected: {len(patterns)}")
    
    # Predictive Modeling Demo
    print("\n2️⃣ PREDICTIVE MODELING")
    print("-" * 30)
    predictor = GrowthPredictor()
    try:
        predictor.train_models(growth_data)
        predictions = predictor.predict(growth_data[-1], days_ahead=14)
        print(f"14-day forecast generated: {predictions[0].predicted_value:.0f} → {predictions[-1].predicted_value:.0f}")
        print(f"Confidence level: {predictions[0].confidence_level}")
    except Exception as e:
        print(f"Prediction demo failed: {e}")
    
    # Anomaly Detection Demo
    print("\n3️⃣ ANOMALY DETECTION")
    print("-" * 30)
    detector = AnomalyDetector()
    anomalies, patterns = detector.detect_anomalies(growth_data)
    print(f"Anomalies detected: {len(anomalies)}")
    print(f"High severity: {sum(1 for a in anomalies if a.severity == 'high')}")
    
    # Benchmarking Demo
    print("\n4️⃣ COMPETITIVE BENCHMARKING")
    print("-" * 30)
    benchmarker = BenchmarkAnalyzer()
    peer_repos = generate_sample_peer_repositories()[:3]  # Just 3 for demo
    
    for peer_repo in peer_repos:
        peer_data = generate_sample_growth_data(days=30, start_stars=peer_repo.stars // 10)
        benchmarker.add_repository_data(peer_repo, peer_data)
    
    target_repo = RepositoryProfile(
        name="demo-target",
        owner="demo",
        language="Python",
        stars=growth_data[-1].stars,
        forks=growth_data[-1].forks,
        watchers=growth_data[-1].watchers,
        age_days=180,
        topics=["demo"],
        description="Demo repository",
        license="MIT",
        size_mb=10.0
    )
    benchmarker.add_repository_data(target_repo, growth_data)
    
    try:
        similar_repos = benchmarker.find_similar_repositories("demo/demo-target", {})
        print(f"Similar repositories found: {len(similar_repos)}")
    except Exception as e:
        print(f"Benchmarking demo failed: {e}")
    
    print("\n✅ Individual component demos complete!")


def run_performance_test():
    """Run a performance test with larger datasets."""
    
    print("\n" + "="*60)
    print("PERFORMANCE TEST WITH LARGE DATASET")
    print("="*60)
    
    import time
    
    # Generate large dataset
    print("Generating large dataset (365 days)...")
    start_time = time.time()
    large_growth_data = generate_sample_growth_data(days=365, start_stars=1000)
    generation_time = time.time() - start_time
    print(f"Data generation took {generation_time:.2f} seconds")
    
    # Test core analysis performance
    print("\nTesting core analysis performance...")
    start_time = time.time()
    
    analyzer = GrowthAnalyzer()
    analyzer.add_growth_data(large_growth_data)
    patterns = analyzer.analyze_growth_patterns()
    
    analysis_time = time.time() - start_time
    print(f"Core analysis completed in {analysis_time:.2f} seconds")
    print(f"Patterns detected: {len(patterns)}")
    
    # Test predictive modeling performance
    print("\nTesting predictive modeling performance...")
    start_time = time.time()
    
    predictor = GrowthPredictor()
    model_performance = predictor.train_models(large_growth_data)
    predictions = predictor.predict(large_growth_data[-1], days_ahead=60)
    
    prediction_time = time.time() - start_time
    print(f"Predictive modeling completed in {prediction_time:.2f} seconds")
    print(f"Models trained: {len(model_performance)}")
    print(f"Forecasts generated: {len(predictions)}")
    
    # Test anomaly detection performance
    print("\nTesting anomaly detection performance...")
    start_time = time.time()
    
    detector = AnomalyDetector()
    anomalies, anomaly_patterns = detector.detect_anomalies(large_growth_data)
    
    anomaly_time = time.time() - start_time
    print(f"Anomaly detection completed in {anomaly_time:.2f} seconds")
    print(f"Anomalies detected: {len(anomalies)}")
    
    total_time = analysis_time + prediction_time + anomaly_time
    print(f"\nTotal processing time: {total_time:.2f} seconds")
    print(f"Average time per day: {total_time/365*1000:.1f} ms/day")
    
    if total_time < 30:  # Less than 30 seconds for 365 days
        print("✅ Performance test PASSED - Real-time capable!")
    else:
        print("⚠️  Performance test WARNING - Consider optimization for real-time use")


if __name__ == "__main__":
    print("Growth Analysis Engine - Demo and Examples")
    print("Choose a demonstration:")
    print("1. Comprehensive analysis (full workflow)")
    print("2. Individual components demo")
    print("3. Performance test with large dataset")
    print("4. All demonstrations")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        run_comprehensive_growth_analysis()
    elif choice == "2":
        demonstrate_individual_components()
    elif choice == "3":
        run_performance_test()
    elif choice == "4":
        demonstrate_individual_components()
        print("\n" + "="*80 + "\n")
        run_comprehensive_growth_analysis()
        print("\n" + "="*80 + "\n")
        run_performance_test()
    else:
        print("Running comprehensive analysis by default...")
        run_comprehensive_growth_analysis()
    
    print("\n🎉 Demo completed! Check out the individual modules for customization options.")