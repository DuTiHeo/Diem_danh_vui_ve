# Database Schema Design

## ERD (Entity-Relationship Diagram)

```mermaid
erDiagram
    users ||--o{ students : "may link to"
    users ||--o{ courses : "lectures"
    users ||--o{ audit_logs : "performs"
    
    buildings ||--o{ courses : "default location"
    buildings ||--o{ attendance_sessions : "held at"
    
    courses ||--o{ enrollments : "has"
    courses ||--o{ attendance_sessions : "has"
    
    students ||--o{ enrollments : "enrolled in"
    students ||--o{ attendance_records : "has"
    
    attendance_sessions ||--o{ qr_tokens : "generates"
    attendance_sessions ||--o{ attendance_records : "records"

    users {
        uuid id PK
        string email UK
        string full_name
        string role "LECTURER | STUDENT | ADMIN"
        string microsoft_id UK
        timestamp created_at
    }

    students {
        uuid id PK
        string student_code UK "8 digits"
        string full_name
        uuid user_id FK "nullable"
    }

    buildings {
        uuid id PK
        string code UK "A2, B, C, D, D2"
        string name
        float latitude
        float longitude
        int radius_meters
    }

    courses {
        uuid id PK
        string course_code
        string course_name
        string class_section
        string room_name
        uuid building_id FK
        uuid lecturer_id FK
        string excel_template_path
        int total_sessions
        timestamp created_at
    }

    enrollments {
        uuid id PK
        uuid course_id FK
        uuid student_id FK
        int ordinal_number "STT in Excel"
    }

    attendance_sessions {
        uuid id PK
        uuid course_id FK
        int session_number "1..N"
        uuid building_id FK
        string status "PENDING | OPEN | CLOSED"
        timestamp started_at
        timestamp ended_at
    }

    qr_tokens {
        uuid id PK
        uuid session_id FK
        string token_hash
        string pin_code UK "6 digits"
        timestamp expires_at
        boolean is_revoked
        timestamp created_at
    }

    attendance_records {
        uuid id PK
        uuid session_id FK
        uuid student_id FK
        string status "ATTENDED | ABSENT"
        timestamp marked_at
        float latitude "nullable"
        float longitude "nullable"
        float distance_meters "nullable"
        string method "QR | PIN_ANONYMOUS | MANUAL"
        uuid updated_by_lecturer_id FK "nullable"
    }

    audit_logs {
        uuid id PK
        uuid user_id FK
        string action
        string details
        string ip_address
        string user_agent
        timestamp created_at
    }
```

## Indexes
- `users.email` (UNIQUE)
- `users.microsoft_id` (UNIQUE)
- `students.student_code` (UNIQUE)
- `qr_tokens.pin_code` (UNIQUE, INDEX for fast lookup)
- `attendance_sessions.course_id` (INDEX)
- `enrollments.course_id`, `enrollments.student_id` (UNIQUE composite)
- `attendance_records.session_id`, `attendance_records.student_id` (UNIQUE composite)

