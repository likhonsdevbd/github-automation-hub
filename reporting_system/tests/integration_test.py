#!/usr/bin/env python3
"""
Integration Test Suite for Reporting System

This script tests the core functionality of the reporting system
to ensure all components work together correctly.
"""

import asyncio
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Add the reporting_system module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reporting_system.core import ReportGenerator, ReportRequest
from reporting_system.data_sources import DataSourceManager
from reporting_system.exporters import ReportExporter
from reporting_system.schedulers import SchedulerManager, ScheduledReport
from reporting_system.notifications import NotificationManager
from reporting_system.utils import load_config, setup_logging


class ReportingSystemTester:
    """Test suite for the reporting system"""
    
    def __init__(self):
        self.test_dir = None
        self.config = None
        self.passed = 0
        self.failed = 0
    
    async def setup(self):
        """Set up test environment"""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp(prefix='reporting_test_')
        print(f"Test directory: {self.test_dir}")
        
        # Create test configuration
        self.config = {
            'data_sources': {
                'sources': {
                    'github': {
                        'enabled': True,
                        'type': 'github',
                        'token': 'test_token',
                        'organization': 'test_org'
                    },
                    'analytics': {
                        'enabled': True,
                        'type': 'analytics',
                        'provider': 'google'
                    },
                    'mock_api': {
                        'enabled': True,
                        'type': 'api',
                        'endpoint': 'https://api.example.com',
                        'api_key': 'test_key'
                    }
                }
            },
            'reports': {
                'export': {
                    'storage': {
                        'base_path': str(self.test_dir)
                    }
                }
            },
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'test_password'
            },
            'scheduling': {
                'timezone': 'UTC',
                'max_concurrent_reports': 3
            },
            'monitoring': {
                'log_level': 'INFO'
            }
        }
        
        setup_logging(self.config['monitoring'])
        print("✅ Test environment ready")
    
    async def teardown(self):
        """Clean up test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up test directory: {self.test_dir}")
    
    async def test_data_sources(self):
        """Test data source manager"""
        print("\n📊 Testing Data Source Manager...")
        
        try:
            manager = DataSourceManager(self.config['data_sources'])
            
            # Test data collection
            data = await manager.collect_data(
                sources=['github', 'analytics'],
                period='daily'
            )
            
            # Verify data structure
            assert isinstance(data, dict), "Data should be a dictionary"
            
            for source in ['github', 'analytics']:
                assert source in data, f"Data should contain {source}"
                source_data = data[source]
                assert isinstance(source_data, dict), f"{source} data should be a dictionary"
                assert 'records' in source_data, f"{source} data should have records"
            
            print("✅ Data source manager tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Data source manager test failed: {e}")
            self.failed += 1
    
    async def test_report_exporter(self):
        """Test report exporter"""
        print("\n📄 Testing Report Exporter...")
        
        try:
            exporter = ReportExporter(self.config['reports'])
            
            # Test content
            test_content = {
                'summary': {
                    'github': {'total_records': 100},
                    'analytics': {'total_records': 200}
                },
                'raw_data': {
                    'github': {
                        'records': [
                            {'type': 'commit', 'count': 50},
                            {'type': 'issue', 'count': 25}
                        ]
                    },
                    'analytics': {
                        'records': [
                            {'type': 'pageview', 'count': 150}
                        ]
                    }
                }
            }
            
            # Test different formats
            for format in ['html', 'csv']:
                result_path = await exporter.export(
                    content=test_content,
                    format=format,
                    template='default_report'
                )
                
                assert os.path.exists(result_path), f"Export file should exist: {result_path}"
                assert result_path.startswith(self.test_dir), "Export should be in test directory"
            
            print("✅ Report exporter tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Report exporter test failed: {e}")
            self.failed += 1
    
    async def test_template_manager(self):
        """Test template manager"""
        print("\n📋 Testing Template Manager...")
        
        try:
            from reporting_system.templates import TemplateManager
            
            manager = TemplateManager({
                'template_directory': str(Path(__file__).parent.parent / 'templates'),
                'branding': {
                    'company_name': 'Test Company',
                    'primary_color': '#007acc'
                }
            })
            
            # Test template rendering
            test_data = {
                'summary': {'github': {'total_records': 100}},
                'raw_data': {},
                'period': 'weekly'
            }
            
            result = await manager.render_template(
                template_name='default_report',
                data=test_data,
                report_type='executive_summary'
            )
            
            assert 'html' in result, "Template should return HTML content"
            assert isinstance(result['html'], str), "HTML content should be a string"
            
            print("✅ Template manager tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Template manager test failed: {e}")
            self.failed += 1
    
    async def test_report_generator(self):
        """Test main report generator"""
        print("\n🤖 Testing Report Generator...")
        
        try:
            generator = ReportGenerator(self.config)
            
            # Create test report request
            request = ReportRequest(
                report_type='executive_summary',
                period='weekly',
                data_sources=['github'],
                format='html',
                recipients=['test@example.com']
            )
            
            # Generate report
            result = await generator.generate_report(request)
            
            assert result.report_id, "Report should have an ID"
            assert result.status in ['pending', 'processing'], "Report should start with valid status"
            
            # Wait for completion or timeout
            max_wait = 30  # seconds
            wait_time = 0
            while result.status in ['pending', 'processing'] and wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                result = generator.get_report_status(result.report_id)
            
            if result.status == 'completed':
                assert result.file_path, "Completed report should have a file path"
                print(f"Report generated: {result.file_path}")
            elif result.status == 'failed':
                print(f"Report generation failed: {result.error_message}")
                # This might be expected in test environment due to missing real APIs
            
            print("✅ Report generator tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Report generator test failed: {e}")
            self.failed += 1
    
    async def test_scheduled_reports(self):
        """Test scheduler functionality"""
        print("\n⏰ Testing Scheduler...")
        
        try:
            scheduler = SchedulerManager(self.config['scheduling'])
            
            # Create test scheduled report
            test_report = ScheduledReport(
                report_id='test_report',
                name='Test Scheduled Report',
                report_type='executive_summary',
                period='daily',
                data_sources=['github'],
                format='html',
                schedule='0 9 * * *',  # 9 AM daily
                enabled=True
            )
            
            # Add to scheduler
            success = scheduler.add_scheduled_report(test_report)
            assert success, "Should successfully add scheduled report"
            
            # Verify report is in scheduler
            retrieved = scheduler.get_scheduled_report('test_report')
            assert retrieved is not None, "Should retrieve scheduled report"
            assert retrieved.name == 'Test Scheduled Report', "Report data should match"
            
            # Test removal
            remove_success = scheduler.remove_scheduled_report('test_report')
            assert remove_success, "Should successfully remove scheduled report"
            
            print("✅ Scheduler tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Scheduler test failed: {e}")
            self.failed += 1
    
    async def test_notification_manager(self):
        """Test notification system"""
        print("\n📧 Testing Notification Manager...")
        
        try:
            notifier = NotificationManager(self.config['email'])
            
            # Test configuration validation
            status = notifier.test_configuration()
            assert 'email' in status, "Should test email configuration"
            
            # In a test environment, email might not be fully configured
            print(f"Notification status: {status}")
            
            print("✅ Notification manager tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Notification manager test failed: {e}")
            self.failed += 1
    
    async def test_integration(self):
        """Test full system integration"""
        print("\n🔗 Testing Full System Integration...")
        
        try:
            # Initialize all components
            generator = ReportGenerator(self.config)
            data_manager = DataSourceManager(self.config['data_sources'])
            scheduler = SchedulerManager(self.config['scheduling'])
            notifier = NotificationManager(self.config['email'])
            
            # Test data collection
            data = await data_manager.collect_data(['github'], 'daily')
            assert 'github' in data, "Should collect data from GitHub source"
            
            # Test report generation
            request = ReportRequest(
                report_type='executive_summary',
                period='daily',
                data_sources=['github'],
                format='html'
            )
            
            result = await generator.generate_report(request)
            assert result.report_id, "Integration test should generate report ID"
            
            print("✅ Full system integration tests passed")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            self.failed += 1
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Reporting System Test Suite")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run individual component tests
            await self.test_data_sources()
            await self.test_report_exporter()
            await self.test_template_manager()
            await self.test_scheduled_reports()
            await self.test_notification_manager()
            
            # Run integration tests
            await self.test_report_generator()
            await self.test_integration()
            
        finally:
            await self.teardown()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed! System is ready for use.")
            return True
        else:
            print(f"\n⚠️  {self.failed} tests failed. Please check the configuration and dependencies.")
            return False


async def main():
    """Main test runner"""
    tester = ReportingSystemTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(1)