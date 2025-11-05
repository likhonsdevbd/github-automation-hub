#!/usr/bin/env python3
"""
Automation Hub CLI - Command-line interface for the GitHub automation system.

Provides safe, compliant automation tools with comprehensive monitoring
and emergency controls for GitHub repository growth automation.
"""

import sys
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime

from .automation_manager import AutomationManager
from .config_manager import ConfigManager


class AutomationHubCLI:
    """Command-line interface for the automation hub."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.automation_manager = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        config = self.config_manager.get_config()
        log_config = config['logging']
        
        logging.basicConfig(
            level=getattr(logging, log_config['level'].upper()),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_config['file']),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run(self, args=None):
        """Run the CLI with the given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            parsed_args.func(parsed_args)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    def create_parser(self):
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='Automation Hub - GitHub Repository Growth Automation System',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s status                    # Check current status
  %(prog)s config create-template    # Create configuration template
  %(prog)s config validate           # Validate current configuration
  %(prog)s follow --username testuser # Follow a specific user
  %(prog)s unfollow-candidates       # Find users to unfollow
  %(prog)s audit-report              # Generate audit report
            """
        )
        
        parser.add_argument('--config', '-c', 
                           help='Path to configuration file')
        parser.add_argument('--version', action='version', 
                           version='Automation Hub 1.0.0')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Check automation status')
        status_parser.add_argument('--detailed', action='store_true',
                                  help='Show detailed status information')
        status_parser.set_defaults(func=self.cmd_status)
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        template_parser = config_subparsers.add_parser('create-template', 
                                                       help='Create configuration template')
        template_parser.add_argument('--output', '-o', default='config_template.yaml',
                                    help='Output file for template (default: config_template.yaml)')
        template_parser.set_defaults(func=self.cmd_config_create_template)
        
        validate_parser = config_subparsers.add_parser('validate', 
                                                       help='Validate current configuration')
        validate_parser.set_defaults(func=self.cmd_config_validate)
        
        show_parser = config_subparsers.add_parser('show', 
                                                   help='Show current configuration')
        show_parser.set_defaults(func=self.cmd_config_show)
        
        # Follow command
        follow_parser = subparsers.add_parser('follow', help='Follow operations')
        follow_parser.add_argument('--username', required=True,
                                  help='Username to follow')
        follow_parser.add_argument('--dry-run', action='store_true',
                                  help='Simulate follow without actually following')
        follow_parser.set_defaults(func=self.cmd_follow)
        
        # Unfollow candidates command
        unfollow_parser = subparsers.add_parser('unfollow-candidates', 
                                                help='Find unfollow candidates')
        unfollow_parser.add_argument('--limit', type=int, default=10,
                                    help='Maximum number of candidates to show')
        unfollow_parser.add_argument('--priority', choices=['high', 'medium', 'low'], 
                                    default='high',
                                    help='Priority level filter')
        unfollow_parser.set_defaults(func=self.cmd_unfollow_candidates)
        
        # Execute unfollow command
        execute_parser = subparsers.add_parser('execute-unfollow', 
                                               help='Execute unfollow actions')
        execute_parser.add_argument('--usernames', nargs='+', required=True,
                                   help='List of usernames to unfollow')
        execute_parser.add_argument('--dry-run', action='store_true',
                                   help='Simulate unfollow without actually unfollowing')
        execute_parser.set_defaults(func=self.cmd_execute_unfollow)
        
        # Audit command
        audit_parser = subparsers.add_parser('audit', help='Audit and reporting')
        audit_subparsers = audit_parser.add_subparsers(dest='audit_action')
        
        report_parser = audit_subparsers.add_parser('report', 
                                                    help='Generate comprehensive audit report')
        report_parser.add_argument('--output', '-o',
                                  help='Output file for audit report')
        report_parser.add_argument('--format', choices=['json', 'summary'], 
                                  default='summary',
                                  help='Report format')
        report_parser.set_defaults(func=self.cmd_audit_report)
        
        export_parser = audit_subparsers.add_parser('export', 
                                                    help='Export telemetry data')
        export_parser.add_argument('--output', '-o',
                                  help='Output file for export')
        export_parser.add_argument('--format', choices=['json', 'csv'], 
                                  default='json',
                                  help='Export format')
        export_parser.set_defaults(func=self.cmd_audit_export)
        
        # Safety command
        safety_parser = subparsers.add_parser('safety', help='Safety and compliance')
        safety_parser.add_argument('--check', action='store_true',
                                  help='Check current safety status')
        safety_parser.add_argument('--enable', action='store_true',
                                  help='Enable automation (requires explicit confirmation)')
        safety_parser.add_argument('--disable', action='store_true',
                                  help='Disable automation')
        safety_parser.set_defaults(func=self.cmd_safety)
        
        return parser
    
    def cmd_status(self, args):
        """Show automation status."""
        print("🤖 Automation Hub Status")
        print("=" * 50)
        
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        status = self.automation_manager.get_status_report()
        
        print(f"Status: {'🟢 Running' if status['is_running'] else '🔴 Stopped'}")
        print(f"Runtime: {status['runtime_hours']:.1f} hours")
        print(f"Total Actions: {status['stats']['total_actions']}")
        print(f"Success Rate: {(status['stats']['successful_actions'] / max(status['stats']['total_actions'], 1) * 100):.1f}%")
        
        if args.detailed:
            print("\n📊 Detailed Statistics:")
            print(f"  Successful Actions: {status['stats']['successful_actions']}")
            print(f"  Failed Actions: {status['stats']['failed_actions']}")
            print(f"  422 Errors: {status['stats']['422_errors']} (enforcement signals)")
            print(f"  429 Errors: {status['stats']['429_errors']} (rate limits)")
            print(f"  Follow-back Ratio: {status['follow_back_ratio']:.2f}")
            
            print("\n⚡ Rate Limit Status:")
            rate_status = status['rate_limit_status']
            for bucket_name, bucket_info in rate_status['buckets'].items():
                print(f"  {bucket_name}: {bucket_info['tokens']:.0f}/{bucket_info['capacity']} tokens")
            
            print("\n🛡️  Compliance Status:")
            compliance = status['compliance_status']
            print(f"  Status: {compliance['status']}")
            if compliance['issues']:
                print(f"  Issues: {', '.join(compliance['issues'])}")
    
    def cmd_config_create_template(self, args):
        """Create configuration template."""
        print(f"Creating configuration template at {args.output}")
        
        self.config_manager.create_template_config(args.output)
        print(f"✅ Configuration template created successfully!")
        print(f"📝 Please review and customize {args.output}")
        print(f"🔧 Then set GITHUB_TOKEN environment variable and run validation")
    
    def cmd_config_validate(self, args):
        """Validate current configuration."""
        print("Validating configuration...")
        
        try:
            config = self.config_manager.get_config()
            safety_status = self.config_manager.get_safety_status()
            
            print("✅ Configuration is valid")
            print("\n🛡️  Safety Status:")
            print(f"  Automation Enabled: {safety_status['automation_enabled']}")
            print(f"  Auto Follow: {safety_status['auto_follow_enabled']}")
            print(f"  Auto Unfollow: {safety_status['auto_unfollow_enabled']}")
            
            print("\n⚡ Rate Limits:")
            rate_config = safety_status['rate_limit_safety']
            print(f"  Max Actions/Hour: {rate_config['max_actions_per_hour']}")
            print(f"  Base Delay: {rate_config['base_delay_seconds']}s")
            
            # Token validation
            if self.automation_manager is None:
                self.automation_manager = AutomationManager(args.config)
            
            github_client = self.automation_manager.github_client
            if github_client.validate_token():
                print("✅ GitHub token is valid")
            else:
                print("❌ GitHub token is invalid or expired")
        
        except Exception as e:
            print(f"❌ Configuration validation failed: {str(e)}")
            sys.exit(1)
    
    def cmd_config_show(self, args):
        """Show current configuration."""
        config = self.config_manager.get_config()
        print(json.dumps(config, indent=2))
    
    def cmd_follow(self, args):
        """Follow a user."""
        print(f"Following user: {args.username}")
        
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        if args.dry_run:
            print("🧪 DRY RUN - No actual actions will be performed")
        
        try:
            if args.dry_run:
                print(f"✅ Would follow {args.username} (dry run)")
            else:
                success = self.automation_manager.execute_follow_action(args.username)
                if success:
                    print(f"✅ Successfully followed {args.username}")
                else:
                    print(f"❌ Failed to follow {args.username}")
                    sys.exit(1)
        except Exception as e:
            print(f"❌ Error following {args.username}: {str(e)}")
            sys.exit(1)
    
    def cmd_unfollow_candidates(self, args):
        """Find unfollow candidates."""
        print(f"Finding unfollow candidates (priority: {args.priority})")
        
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        candidates = self.automation_manager.get_follow_back_candidates()
        
        if not candidates:
            print("No unfollow candidates found")
            return
        
        # Filter by priority
        if args.priority == 'high':
            candidates = [c for c in candidates if c['priority_score'] >= 2.0]
        elif args.priority == 'medium':
            candidates = [c for c in candidates if 1.0 <= c['priority_score'] < 2.0]
        else:  # low
            candidates = [c for c in candidates if c['priority_score'] < 1.0]
        
        # Limit results
        candidates = candidates[:args.limit]
        
        print(f"\n📋 Found {len(candidates)} unfollow candidates:")
        print("-" * 60)
        print(f"{'Username':<20} {'Score':<8} {'Repos':<6} {'Followers':<10}")
        print("-" * 60)
        
        for candidate in candidates:
            print(f"{candidate['username']:<20} {candidate['priority_score']:<8.1f} "
                  f"{candidate['public_repos']:<6} {candidate['followers_count']:<10}")
        
        print(f"\n💡 To unfollow these users, run:")
        usernames = ' '.join(c['username'] for c in candidates)
        print(f"   {sys.argv[0]} execute-unfollow --usernames {usernames}")
    
    def cmd_execute_unfollow(self, args):
        """Execute unfollow actions."""
        print(f"Executing unfollow for {len(args.usernames)} users")
        
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        if args.dry_run:
            print("🧪 DRY RUN - No actual actions will be performed")
            for username in args.usernames:
                print(f"   Would unfollow {username}")
            return
        
        success_count = 0
        for username in args.usernames:
            try:
                success = self.automation_manager.execute_unfollow_action(username)
                if success:
                    print(f"✅ Unfollowed {username}")
                    success_count += 1
                else:
                    print(f"❌ Failed to unfollow {username}")
            except Exception as e:
                print(f"❌ Error unfollowing {username}: {str(e)}")
        
        print(f"\n📊 Results: {success_count}/{len(args.usernames)} successful")
    
    def cmd_audit_report(self, args):
        """Generate audit report."""
        print("Generating audit report...")
        
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        if args.format == 'summary':
            self.print_audit_summary()
        else:
            self.export_audit_json(args.output)
    
    def print_audit_summary(self):
        """Print human-readable audit summary."""
        if not self.automation_manager.telemetry:
            print("No telemetry data available")
            return
        
        performance = self.automation_manager.telemetry.get_performance_summary()
        compliance = self.automation_manager.telemetry.get_compliance_report()
        
        print("📋 Automation Hub Audit Report")
        print("=" * 50)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 Session Summary:")
        session = performance['session_duration']
        print(f"  Duration: {session['hours']:.1f} hours")
        print(f"  Start: {session['start_time']}")
        
        print(f"\n🎯 Action Statistics:")
        actions = performance['action_statistics']
        print(f"  Total Actions: {actions['total_actions']}")
        print(f"  Success Rate: {actions['success_rate']:.1f}%")
        print(f"  Actions/Hour: {actions['actions_per_hour']:.1f}")
        
        print(f"\n⚡ Performance Metrics:")
        perf = performance['performance_metrics']
        print(f"  Average Latency: {perf['average_action_latency']:.2f}s")
        print(f"  Total Events: {perf['total_events']}")
        
        print(f"\n🛡️  Compliance Assessment:")
        print(f"  Compliance Score: {compliance['compliance_score']:.1f}/100")
        
        if compliance['risk_indicators']:
            print(f"\n⚠️  Risk Indicators:")
            for risk in compliance['risk_indicators']:
                print(f"  {risk['severity'].upper()}: {risk['description']}")
        
        if compliance['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in compliance['recommendations']:
                print(f"  • {rec}")
    
    def export_audit_json(self, output_file):
        """Export audit data as JSON."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"audit_report_{timestamp}.json"
        
        if not self.automation_manager.telemetry:
            print("No telemetry data to export")
            return
        
        report_data = {
            'report_type': 'audit_report',
            'generated_at': datetime.now().isoformat(),
            'performance_summary': self.automation_manager.telemetry.get_performance_summary(),
            'compliance_report': self.automation_manager.telemetry.get_compliance_report(),
            'status_report': self.automation_manager.get_status_report()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"✅ Audit report exported to {output_file}")
    
    def cmd_audit_export(self, args):
        """Export telemetry data."""
        if not self.automation_manager:
            self.automation_manager = AutomationManager(args.config)
        
        if not self.automation_manager.telemetry:
            print("Telemetry is not enabled")
            return
        
        output_file = self.automation_manager.telemetry.export_metrics(
            format=args.format,
            output_file=args.output
        )
        
        if output_file:
            print(f"✅ Telemetry data exported to {output_file}")
    
    def cmd_safety(self, args):
        """Safety and compliance commands."""
        safety_status = self.config_manager.get_safety_status()
        
        if args.check:
            print("🛡️  Automation Hub Safety Status")
            print("=" * 50)
            
            print(f"Automation Enabled: {'✅ YES' if safety_status['automation_enabled'] else '❌ NO'}")
            print(f"Auto Follow: {'✅ ENABLED' if safety_status['auto_follow_enabled'] else '❌ DISABLED'}")
            print(f"Auto Unfollow: {'✅ ENABLED' if safety_status['auto_unfollow_enabled'] else '❌ DISABLED'}")
            
            print(f"\n⚡ Rate Limits:")
            rate_config = safety_status['rate_limit_safety']
            print(f"  Max Actions/Hour: {rate_config['max_actions_per_hour']}")
            print(f"  Base Delay: {rate_config['base_delay_seconds']}s")
            print(f"  Exponential Backoff: {'✅' if rate_config['exponential_backoff_enabled'] else '❌'}")
            
            print(f"\n🛡️  Compliance Features:")
            compliance = safety_status['compliance_features']
            for feature, enabled in compliance.items():
                print(f"  {feature.replace('_', ' ').title()}: {'✅' if enabled else '❌'}")
        
        if args.enable:
            print("⚠️  ENABLING AUTOMATION")
            print("This will enable automatic GitHub actions.")
            confirm = input("Type 'ENABLE' to confirm: ")
            
            if confirm == 'ENABLE':
                self.config_manager.update_config({'automation.enabled': True})
                print("✅ Automation enabled")
            else:
                print("❌ Confirmation failed, automation not enabled")
        
        if args.disable:
            print("🛑 DISABLING AUTOMATION")
            self.config_manager.update_config({
                'automation.enabled': False,
                'follow_unfollow.auto_follow_enabled': False,
                'follow_unfollow.auto_unfollow_enabled': False
            })
            print("✅ Automation disabled")


def main():
    """Main entry point."""
    cli = AutomationHubCLI()
    cli.run()


if __name__ == '__main__':
    main()
