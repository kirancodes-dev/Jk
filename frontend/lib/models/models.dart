class User {
  final int id;
  final String email;
  final String fullName;
  final String? phoneNumber;
  final String role;
  final String? districtName;

  User({
    required this.id,
    required this.email,
    required this.fullName,
    this.phoneNumber,
    required this.role,
    this.districtName,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['user_id'] ?? json['id'] ?? 0,
      email: json['email'] ?? '',
      fullName: json['full_name'] ?? 'User',
      phoneNumber: json['phone_number'],
      role: json['role'] ?? 'CITIZEN',
      districtName: json['district_name'] ?? json['district'] ?? 'Jharkhand',
    );
  }
}

class Challenge {
  final int id;
  final String title;
  final String description;
  final String category;
  final String? subCategory;
  final String urgency;
  final String priority;
  final String? expectedImpact;
  final String status;
  final String? districtName;
  final String? assignedUniversityName;
  final String createdAt;
  final String currentTier;
  final int escalationLevel;
  final String? escalatedBy;
  final String? escalationRemarks;

  Challenge({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    this.subCategory,
    required this.urgency,
    required this.priority,
    this.expectedImpact,
    required this.status,
    this.districtName,
    this.assignedUniversityName,
    required this.createdAt,
    this.currentTier = 'PANCHAYAT',
    this.escalationLevel = 1,
    this.escalatedBy,
    this.escalationRemarks,
  });

  factory Challenge.fromJson(Map<String, dynamic> json) {
    return Challenge(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      category: json['category'] ?? 'General',
      subCategory: json['sub_category'],
      urgency: json['urgency'] ?? 'Medium',
      priority: json['priority'] ?? 'MEDIUM',
      expectedImpact: json['expected_impact'],
      status: json['status'] ?? 'SUBMITTED',
      districtName: json['district_name'],
      assignedUniversityName: json['assigned_university_name'],
      createdAt: json['created_at'] ?? '',
      currentTier: json['current_tier'] ?? 'PANCHAYAT',
      escalationLevel: json['escalation_level'] ?? 1,
      escalatedBy: json['escalated_by'],
      escalationRemarks: json['escalation_remarks'],
    );
  }
}

class AIAnalysis {
  final int id;
  final String classifiedDomain;
  final String detectedPriority;
  final String? extractedKeywords;
  final String? requiredExpertise;
  final String? recommendedSolution;
  final double confidenceScore;

  AIAnalysis({
    required this.id,
    required this.classifiedDomain,
    required this.detectedPriority,
    this.extractedKeywords,
    this.requiredExpertise,
    this.recommendedSolution,
    required this.confidenceScore,
  });

  factory AIAnalysis.fromJson(Map<String, dynamic> json) {
    return AIAnalysis(
      id: json['id'] ?? 0,
      classifiedDomain: json['classified_domain'] ?? 'General',
      detectedPriority: json['detected_priority'] ?? 'MEDIUM',
      extractedKeywords: json['extracted_keywords'],
      requiredExpertise: json['required_expertise'],
      recommendedSolution: json['recommended_solution'],
      confidenceScore: (json['confidence_score'] ?? 0.9).toDouble(),
    );
  }
}

class UniversityMatch {
  final int universityId;
  final String institutionName;
  final String districtName;
  final double matchPercentage;
  final int ranking;
  final String? matchingFactors;

  UniversityMatch({
    required this.universityId,
    required this.institutionName,
    required this.districtName,
    required this.matchPercentage,
    required this.ranking,
    this.matchingFactors,
  });

  factory UniversityMatch.fromJson(Map<String, dynamic> json) {
    return UniversityMatch(
      universityId: json['university_id'] ?? 0,
      institutionName: json['institution_name'] ?? 'University',
      districtName: json['district_name'] ?? 'Jharkhand',
      matchPercentage: (json['match_percentage'] ?? 0.0).toDouble(),
      ranking: json['ranking'] ?? 1,
      matchingFactors: json['matching_factors'],
    );
  }
}

class SimilarChallenge {
  final int challengeId;
  final String title;
  final String districtName;
  final String status;
  final double similarityScore;

  SimilarChallenge({
    required this.challengeId,
    required this.title,
    required this.districtName,
    required this.status,
    required this.similarityScore,
  });

  factory SimilarChallenge.fromJson(Map<String, dynamic> json) {
    return SimilarChallenge(
      challengeId: json['challenge_id'] ?? 0,
      title: json['title'] ?? '',
      districtName: json['district_name'] ?? 'Jharkhand',
      status: json['status'] ?? 'SUBMITTED',
      similarityScore: (json['similarity_score'] ?? 0.0).toDouble(),
    );
  }
}

class StatusHistoryItem {
  final int id;
  final String? fromStatus;
  final String toStatus;
  final String updatedBy;
  final String? remarks;
  final String changedAt;

  StatusHistoryItem({
    required this.id,
    this.fromStatus,
    required this.toStatus,
    required this.updatedBy,
    this.remarks,
    required this.changedAt,
  });

  factory StatusHistoryItem.fromJson(Map<String, dynamic> json) {
    return StatusHistoryItem(
      id: json['id'] ?? 0,
      fromStatus: json['from_status'],
      toStatus: json['to_status'] ?? '',
      updatedBy: json['updated_by'] ?? 'System',
      remarks: json['remarks'],
      changedAt: json['changed_at'] ?? '',
    );
  }
}

class CommentItem {
  final int id;
  final int userId;
  final String authorName;
  final String authorRole;
  final String content;
  final String createdAt;

  CommentItem({
    required this.id,
    required this.userId,
    required this.authorName,
    required this.authorRole,
    required this.content,
    required this.createdAt,
  });

  factory CommentItem.fromJson(Map<String, dynamic> json) {
    return CommentItem(
      id: json['id'] ?? 0,
      userId: json['user_id'] ?? 0,
      authorName: json['author_name'] ?? 'User',
      authorRole: json['author_role'] ?? 'CITIZEN',
      content: json['content'] ?? '',
      createdAt: json['created_at'] ?? '',
    );
  }
}

class ProjectItem {
  final int id;
  final int challengeId;
  final String challengeTitle;
  final int universityId;
  final String universityName;
  final String? facultyMentorName;
  final String name;
  final String description;
  final double progressPercentage;
  final String currentStage;

  ProjectItem({
    required this.id,
    required this.challengeId,
    required this.challengeTitle,
    required this.universityId,
    required this.universityName,
    this.facultyMentorName,
    required this.name,
    required this.description,
    required this.progressPercentage,
    required this.currentStage,
  });

  factory ProjectItem.fromJson(Map<String, dynamic> json) {
    return ProjectItem(
      id: json['id'] ?? 0,
      challengeId: json['challenge_id'] ?? 0,
      challengeTitle: json['challenge_title'] ?? 'Challenge',
      universityId: json['university_id'] ?? 0,
      universityName: json['university_name'] ?? 'University',
      facultyMentorName: json['faculty_mentor_name'],
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      progressPercentage: (json['progress_percentage'] ?? 0.0).toDouble(),
      currentStage: json['current_stage'] ?? 'Ideation',
    );
  }
}

class MilestoneItem {
  final int id;
  final String title;
  final String? description;
  final double completionPercentage;
  final String status;
  final bool approvedByFaculty;

  MilestoneItem({
    required this.id,
    required this.title,
    this.description,
    required this.completionPercentage,
    required this.status,
    required this.approvedByFaculty,
  });

  factory MilestoneItem.fromJson(Map<String, dynamic> json) {
    return MilestoneItem(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'],
      completionPercentage: (json['completion_percentage'] ?? 0.0).toDouble(),
      status: json['status'] ?? 'NOT_STARTED',
      approvedByFaculty: json['approved_by_faculty'] ?? false,
    );
  }
}

class TaskItem {
  final int id;
  final String title;
  final int? assignedToStudentId;
  final String? assignedStudentName;
  final bool isCompleted;
  final String? submissionNotes;

  TaskItem({
    required this.id,
    required this.title,
    this.assignedToStudentId,
    this.assignedStudentName,
    required this.isCompleted,
    this.submissionNotes,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    return TaskItem(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      assignedToStudentId: json['assigned_to_student_id'],
      assignedStudentName: json['assigned_student_name'],
      isCompleted: json['is_completed'] ?? false,
      submissionNotes: json['submission_notes'],
    );
  }
}

class NotificationItem {
  final int id;
  final String title;
  final String message;
  final String notificationType;
  final int? referenceId;
  final bool isRead;
  final String createdAt;

  NotificationItem({
    required this.id,
    required this.title,
    required this.message,
    required this.notificationType,
    this.referenceId,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      notificationType: json['notification_type'] ?? 'INFO',
      referenceId: json['reference_id'],
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at'] ?? '',
    );
  }
}
