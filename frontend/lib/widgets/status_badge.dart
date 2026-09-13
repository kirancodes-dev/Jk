import 'package:flutter/material.dart';
import '../core/theme.dart';

enum StatusBadgeType { status, priority, tier }

class StatusBadge extends StatelessWidget {
  final String status;
  final bool isTier;
  final bool isPriority;
  final double fontSize;
  final StatusBadgeType? type;

  const StatusBadge({
    super.key,
    String? status,
    String? label,
    this.isTier = false,
    this.isPriority = false,
    this.fontSize = 10,
    this.type,
  }) : status = status ?? label ?? '';

  @override
  Widget build(BuildContext context) {
    if (type == StatusBadgeType.tier || isTier) {
      return _buildTierBadge();
    }
    if (type == StatusBadgeType.priority || isPriority) {
      return _buildPriorityBadge();
    }
    return _buildStatusBadge();
  }

  Widget _buildPriorityBadge() {
    Color bg;
    Color fg;
    final p = status.toUpperCase();

    if (p == 'CRITICAL') {
      bg = const Color(0xFFFEE2E2);
      fg = const Color(0xFFDC2626);
    } else if (p == 'HIGH') {
      bg = const Color(0xFFFFEDD5);
      fg = const Color(0xFFEA580C);
    } else if (p == 'MEDIUM') {
      bg = const Color(0xFFFEF3C7);
      fg = const Color(0xFFD97706);
    } else {
      bg = const Color(0xFFF1F5F9);
      fg = const Color(0xFF64748B);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withOpacity(0.2), width: 0.8),
      ),
      child: Text(
        p,
        style: TextStyle(
          color: fg,
          fontWeight: FontWeight.bold,
          fontSize: fontSize,
          letterSpacing: 0.2,
        ),
      ),
    );
  }

  Widget _buildTierBadge() {
    Color bg;
    Color fg;
    String label;
    IconData icon;

    switch (status.toUpperCase()) {
      case 'PANCHAYAT':
        bg = const Color(0xFFFEF3C7);
        fg = const Color(0xFFB45309);
        label = 'Level 1: Panchayat (GP)';
        icon = Icons.home_work_outlined;
        break;
      case 'BLOCK':
        bg = const Color(0xFFE0E7FF);
        fg = const Color(0xFF3730A3);
        label = 'Level 2: Block (BDO)';
        icon = Icons.location_city_outlined;
        break;
      case 'DISTRICT':
        bg = const Color(0xFFCCFBF1);
        fg = const Color(0xFF0F766E);
        label = 'Level 3: District (DC)';
        icon = Icons.account_balance_outlined;
        break;
      case 'STATE':
      default:
        bg = const Color(0xFFDCFCE7);
        fg = const Color(0xFF15803D);
        label = 'Level 4: State HQ';
        icon = Icons.shield_outlined;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withOpacity(0.25), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: fontSize + 2, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: fg,
              fontWeight: FontWeight.w700,
              fontSize: fontSize,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge() {
    Color bg;
    Color fg;
    String cleanStatus = status.replaceAll('_', ' ').toUpperCase();

    switch (status.toUpperCase()) {
      case 'SUBMITTED':
        bg = const Color(0xFFF1F5F9);
        fg = const Color(0xFF475569);
        break;
      case 'AI_ANALYSIS':
      case 'UNDER_REVIEW':
        bg = const Color(0xFFFEF3C7);
        fg = const Color(0xFFB45309);
        break;
      case 'VALIDATED':
      case 'APPROVED':
        bg = const Color(0xFFE0F2FE);
        fg = const Color(0xFF0369A1);
        break;
      case 'UNIVERSITY_ASSIGNED':
      case 'ADOPTED':
        bg = const Color(0xFFF3E8FF);
        fg = const Color(0xFF7E22CE);
        break;
      case 'PROJECT_STARTED':
      case 'RESEARCH':
      case 'IN_PROGRESS':
        bg = const Color(0xFFFEF9C3);
        fg = const Color(0xFFA16207);
        break;
      case 'PROTOTYPE':
      case 'TESTING':
        bg = const Color(0xFFFFEDD5);
        fg = const Color(0xFFC2410C);
        break;
      case 'DEPLOYMENT':
      case 'RESOLVED':
      case 'COMPLETED':
        bg = const Color(0xFFDCFCE7);
        fg = const Color(0xFF15803D);
        break;
      case 'REJECTED':
        bg = const Color(0xFFFEE2E2);
        fg = const Color(0xFFB91C1C);
        break;
      default:
        bg = AppTheme.borderSubtle;
        fg = AppTheme.textSecondary;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withOpacity(0.2), width: 0.8),
      ),
      child: Text(
        cleanStatus,
        style: TextStyle(
          color: fg,
          fontWeight: FontWeight.w700,
          fontSize: fontSize,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
