#!/usr/bin/env python3
"""
GDPR Compliance Manager CLI Tool

Provides commands for managing GDPR compliance.
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from core.db.config import configure_database
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.gdpr import (
    ConsentManager, DataSubjectRights, DataAnonymizer,
    RetentionManager, GDPRAuditLogger, CookieConsentManager,
    ConsentType, ConsentStatus, DSARType, RetentionPolicy,
    AuditEventType, AuditSeverity
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


class GDPRCLI:
    """GDPR CLI tool"""
    
    def __init__(self):
        self.config = configure_database()
        self.postgres = PostgresAdapter(self.config)
        self.consent_manager = ConsentManager(self.postgres)
        self.data_subject_rights = DataSubjectRights(self.postgres, self.consent_manager)
        self.anonymizer = DataAnonymizer()
        self.retention_manager = RetentionManager(self.postgres)
        self.audit_logger = GDPRAuditLogger(self.postgres)
        self.cookie_consent = CookieConsentManager(self.postgres)
    
    async def export_user_data(self, user_id: int, format: str = "json"):
        """Export user data (Right to Access)"""
        print(f"\n📤 Exporting data for user {user_id}...")
        
        # Get user data
        data = await self.data_subject_rights.get_user_data(user_id)
        
        # Export to file
        export_path = await self.data_subject_rights.export_user_data(user_id, format)
        
        print(f"✅ Data exported to: {export_path}")
        print(f"   Records included: {len(data)}")
        
        # Log the export
        await self.audit_logger.log_data_export(
            user_id, "admin", format, 
            len(str(data))
        )
    
    async def anonymize_user(self, user_id: int):
        """Anonymize user data"""
        print(f"\n🎭 Anonymizing user {user_id}...")
        
        response = input("⚠️  This will anonymize all personal data. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
        
        success = await self.anonymizer.anonymize_user(user_id, self.postgres)
        
        if success:
            print("✅ User data anonymized successfully")
            
            # Log the action
            await self.audit_logger.log_data_anonymization(
                user_id, "admin", {"method": "full_anonymization"}
            )
        else:
            print("❌ Failed to anonymize user")
    
    async def delete_user_data(self, user_id: int):
        """Delete user data (Right to Erasure)"""
        print(f"\n🗑️  Deleting data for user {user_id}...")
        
        response = input("⚠️  This will permanently delete all user data. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
        
        success = await self.data_subject_rights.erase_user_data(user_id)
        
        if success:
            print("✅ User data deleted successfully")
            
            # Log the deletion
            await self.audit_logger.log_data_deletion(
                user_id, "admin", ["all"], "GDPR erasure request"
            )
        else:
            print("❌ Failed to delete user data")
    
    async def create_dsar(self, user_id: int, request_type: str):
        """Create Data Subject Access Request"""
        print(f"\n📋 Creating DSAR for user {user_id}...")
        
        dsar_type = DSARType(request_type)
        request = await self.data_subject_rights.create_request(
            user_id, dsar_type
        )
        
        print(f"✅ DSAR created: {request.request_id}")
        print(f"   Type: {request.request_type.value}")
        print(f"   Status: {request.status.value}")
        
        # Log the request
        await self.audit_logger.log_dsar(
            user_id, request_type, "requested",
            {"request_id": request.request_id}
        )
    
    async def apply_retention(self, dry_run: bool = False):
        """Apply retention policies"""
        print(f"\n🧹 Applying retention policies...")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        results = await self.retention_manager.apply_retention_policies(dry_run)
        
        print("\nResults:")
        for category, count in results.items():
            status = "Would delete" if dry_run else "Deleted"
            print(f"  {category}: {count} records ({status})")
        
        if not dry_run:
            # Log the action
            await self.audit_logger.log_retention_applied(
                "system", results
            )
    
    async def show_consent_report(self, user_id: int = None):
        """Show consent report"""
        print("\n📊 Consent Report")
        print("=" * 60)
        
        if user_id:
            # User-specific consents
            consents = await self.consent_manager.get_user_consents(user_id)
            
            if not consents:
                print(f"No consents found for user {user_id}")
                return
            
            print(f"\nUser {user_id} Consents:")
            for consent in consents:
                print(f"  Type: {consent.consent_type.value}")
                print(f"  Status: {consent.status.value}")
                print(f"  Granted: {consent.granted_at}")
                if consent.expires_at:
                    print(f"  Expires: {consent.expires_at}")
                print()
        else:
            # Overall statistics
            stats = await self.cookie_consent.get_consent_statistics()
            
            print(f"\nLast {stats['period_days']} days:")
            print(f"  Total consents: {stats['total_consents']}")
            
            print("\nBy category:")
            for cat in stats['by_category']:
                granted = cat['granted']
                total = cat['total']
                percent = (granted / total * 100) if total > 0 else 0
                print(f"  {cat['category']}: {granted}/{total} ({percent:.1f}%)")
    
    async def show_audit_trail(self, user_id: int, days: int = 30):
        """Show audit trail for user"""
        print(f"\n📋 Audit Trail for User {user_id}")
        print("=" * 60)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        events = await self.audit_logger.get_user_audit_trail(
            user_id, start_date
        )
        
        if not events:
            print(f"No audit events found for user {user_id} in last {days} days")
            return
        
        print(f"\nLast {days} days ({len(events)} events):")
        print("-" * 60)
        
        for event in events:
            print(f"{event['timestamp'][:19]} | {event['event_type']:<20} | {event['severity']:<8}")
            if event['details']:
                details = json.loads(event['details'])
                for key, value in list(details.items())[:3]:  # Show first 3 items
                    print(f"  {key}: {value}")
            print()
    
    async def place_legal_hold(self, user_id: int, data_type: str, reason: str):
        """Place legal hold on user data"""
        print(f"\n⚖️  Placing legal hold on user {user_id}...")
        
        success = await self.retention_manager.place_legal_hold(
            user_id, data_type, reason
        )
        
        if success:
            print("✅ Legal hold placed")
            
            # Log the action
            await self.audit_logger.log_event(
                "legal_hold_placed", user_id,
                {"data_type": data_type, "reason": reason}
            )
        else:
            print("❌ Failed to place legal hold")
    
    async def generate_compliance_report(self, days: int = 30):
        """Generate compliance report"""
        print(f"\n📊 Generating compliance report (last {days} days)...")
        
        report = await self.audit_logger.generate_compliance_report(
            days=days
        )
        
        print("\nGDPR Compliance Report")
        print("=" * 60)
        print(f"Period: {report['report_period']['start'][:10]} to {report['report_period']['end'][:10]}")
        
        print("\nAudit Summary:")
        summary = report['audit_summary']
        print(f"  Total events: {summary['total_events']}")
        print(f"  Unique users: {summary['unique_users']}")
        print(f"  Critical events: {summary['critical_events']}")
        print(f"  High severity: {summary['high_events']}")
        
        print("\nTop Event Types:")
        for event in report['events_by_type'][:5]:
            print(f"  {event['event_type']}: {event['count']}")
        
        print("\nDSAR Summary:")
        dsar = report['dsar_summary']
        if dsar['total_requests']:
            print(f"  Total requests: {dsar['total_requests']}")
            print(f"  Completed: {dsar['completed']}")
            print(f"  Avg completion time: {dsar['avg_days']:.1f} days")
        
        # Save report to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"gdpr_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_file}")
    
    async def close(self):
        """Close connections"""
        await self.postgres.close()


async def main():
    parser = argparse.ArgumentParser(description="GDPR Compliance Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Export user data
    export_parser = subparsers.add_parser('export', help='Export user data')
    export_parser.add_argument('user_id', type=int, help='User ID')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json')
    
    # Anonymize user
    anon_parser = subparsers.add_parser('anonymize', help='Anonymize user data')
    anon_parser.add_argument('user_id', type=int, help='User ID')
    
    # Delete user data
    delete_parser = subparsers.add_parser('delete', help='Delete user data')
    delete_parser.add_argument('user_id', type=int, help='User ID')
    
    # Create DSAR
    dsar_parser = subparsers.add_parser('dsar', help='Create DSAR request')
    dsar_parser.add_argument('user_id', type=int, help='User ID')
    dsar_parser.add_argument('--type', choices=['access', 'rectification', 'erasure', 
                                             'portability', 'restriction', 'object'],
                           required=True, help='DSAR type')
    
    # Apply retention
    retention_parser = subparsers.add_parser('retention', help='Apply retention policies')
    retention_parser.add_argument('--dry-run', action='store_true', help='Dry run only')
    
    # Consent report
    consent_parser = subparsers.add_parser('consent', help='Show consent report')
    consent_parser.add_argument('--user-id', type=int, help='Specific user ID')
    
    # Audit trail
    audit_parser = subparsers.add_parser('audit', help='Show audit trail')
    audit_parser.add_argument('user_id', type=int, help='User ID')
    audit_parser.add_argument('--days', type=int, default=30, help='Days to look back')
    
    # Legal hold
    hold_parser = subparsers.add_parser('hold', help='Place legal hold')
    hold_parser.add_argument('user_id', type=int, help='User ID')
    hold_parser.add_argument('--data-type', required=True, help='Data type')
    hold_parser.add_argument('--reason', required=True, help='Reason for hold')
    
    # Compliance report
    report_parser = subparsers.add_parser('report', help='Generate compliance report')
    report_parser.add_argument('--days', type=int, default=30, help='Days to include')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GDPRCLI()
    
    try:
        if args.command == 'export':
            await cli.export_user_data(args.user_id, args.format)
        
        elif args.command == 'anonymize':
            await cli.anonymize_user(args.user_id)
        
        elif args.command == 'delete':
            await cli.delete_user_data(args.user_id)
        
        elif args.command == 'dsar':
            await cli.create_dsar(args.user_id, args.type)
        
        elif args.command == 'retention':
            await cli.apply_retention(args.dry_run)
        
        elif args.command == 'consent':
            await cli.show_consent_report(getattr(args, 'user_id', None))
        
        elif args.command == 'audit':
            await cli.show_audit_trail(args.user_id, args.days)
        
        elif args.command == 'hold':
            await cli.place_legal_hold(args.user_id, args.data_type, args.reason)
        
        elif args.command == 'report':
            await cli.generate_compliance_report(args.days)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        await cli.close()


if __name__ == "__main__":
    asyncio.run(main())
