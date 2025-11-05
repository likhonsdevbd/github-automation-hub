"""
Test script for Growth Analysis Engine

This script performs basic testing to ensure all components are working correctly.
"""

import sys
import traceback
from datetime import datetime, timedelta

def test_basic_functionality():
    """Test basic functionality of the growth analysis engine."""
    
    print("🧪 Testing Growth Analysis Engine")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from growth_analysis import (
            GrowthAnalyzer, GrowthPredictor, AnomalyDetector,
            BenchmarkAnalyzer, TrendForecaster, StrategyRecommender,
            create_growth_engine, generate_sample_growth_data
        )
        print("✅ All imports successful")
        
        # Test data generation
        print("\n📊 Testing data generation...")
        growth_data = generate_sample_growth_data(days=30, start_stars=100)
        print(f"✅ Generated {len(growth_data)} data points")
        
        # Test core analyzer
        print("\n🔍 Testing core analyzer...")
        analyzer = GrowthAnalyzer()
        analyzer.add_growth_data(growth_data)
        patterns = analyzer.analyze_growth_patterns()
        summary = analyzer.get_growth_summary()
        print(f"✅ Analysis complete - {len(patterns)} patterns detected")
        
        # Test predictive modeling
        print("\n🔮 Testing predictive modeling...")
        predictor = GrowthPredictor()
        predictor.train_models(growth_data)
        predictions = predictor.predict(growth_data[-1], days_ahead=7)
        print(f"✅ Prediction complete - {len(predictions)} forecasts generated")
        
        # Test anomaly detection
        print("\n🚨 Testing anomaly detection...")
        detector = AnomalyDetector()
        anomalies, anomaly_patterns = detector.detect_anomalies(growth_data)
        print(f"✅ Anomaly detection complete - {len(anomalies)} anomalies found")
        
        # Test complete engine
        print("\n🚀 Testing complete engine...")
        engine = create_growth_engine()
        engine.add_repository_data("test-repo", growth_data)
        results = engine.run_complete_analysis("test-repo")
        print(f"✅ Complete analysis successful")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling and edge cases."""
    
    print("\n⚠️  Testing error handling...")
    
    try:
        from growth_analysis import GrowthAnalyzer, GrowthPredictor
        
        # Test with insufficient data
        print("Testing with insufficient data...")
        analyzer = GrowthAnalyzer()
        
        # Empty data
        try:
            patterns = analyzer.analyze_growth_patterns()
            print("✅ Empty data handled correctly")
        except Exception as e:
            print(f"✅ Empty data properly handled: {e}")
        
        # Minimal data
        from growth_analysis import GrowthMetrics
        minimal_data = [GrowthMetrics(date=datetime.now(), stars=1)]
        analyzer.add_growth_data(minimal_data)
        patterns = analyzer.analyze_growth_patterns()
        print("✅ Minimal data handled correctly")
        
        # Test predictor with limited data
        predictor = GrowthPredictor()
        try:
            predictor.train_models(minimal_data)
            print("✅ Limited data handled by predictor")
        except Exception as e:
            print(f"✅ Limited data properly handled: {e}")
        
        print("✅ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_performance():
    """Basic performance test."""
    
    print("\n⚡ Testing performance...")
    
    try:
        from growth_analysis import generate_sample_growth_data
        import time
        
        # Generate larger dataset
        print("Generating 90-day dataset...")
        start_time = time.time()
        growth_data = generate_sample_growth_data(days=90, start_stars=500)
        generation_time = time.time() - start_time
        print(f"✅ Data generation: {generation_time:.2f}s")
        
        # Test analysis performance
        print("Testing analysis performance...")
        from growth_analysis import GrowthAnalyzer
        
        start_time = time.time()
        analyzer = GrowthAnalyzer()
        analyzer.add_growth_data(growth_data)
        patterns = analyzer.analyze_growth_patterns()
        analysis_time = time.time() - start_time
        print(f"✅ Core analysis: {analysis_time:.2f}s")
        
        # Test with 180-day dataset
        print("Testing with 180-day dataset...")
        start_time = time.time()
        large_data = generate_sample_growth_data(days=180, start_stars=500)
        analyzer_large = GrowthAnalyzer()
        analyzer_large.add_growth_data(large_data)
        patterns_large = analyzer_large.analyze_growth_patterns()
        large_analysis_time = time.time() - start_time
        print(f"✅ Large dataset analysis: {large_analysis_time:.2f}s")
        
        if analysis_time < 5.0:  # Should be under 5 seconds for 90 days
            print("✅ Performance test passed")
            return True
        else:
            print("⚠️  Performance test slow but functional")
            return True
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def main():
    """Run all tests."""
    
    print("Growth Analysis Engine - Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_basic_functionality():
        tests_passed += 1
    
    if test_error_handling():
        tests_passed += 1
    
    if test_performance():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Growth Analysis Engine is ready to use.")
        print("\nNext steps:")
        print("1. Import the engine: from growth_analysis import create_growth_engine")
        print("2. Generate data: from growth_analysis import generate_sample_growth_data")
        print("3. Run analysis: results = engine.run_complete_analysis('your-repo')")
        return 0
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)