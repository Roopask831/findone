"""ATS fixtures: Java backend resume vs mixed JDs."""

JAVA_RESUME = {
    "name": "Alex Java",
    "roles": [
        {
            "title": "Java Developer",
            "company": "Acme",
            "start_date": "2022-01",
            "end_date": "Present",
            "bullets": [
                "Built Spring Boot REST APIs and microservices",
                "Used Hibernate and JPA with MySQL",
                "Wrote JUnit tests and containerized services with Docker on AWS",
                "Published events with Kafka",
            ],
        }
    ],
    "skills": [
        "Java",
        "Spring Boot",
        "REST",
        "Microservices",
        "SQL",
        "MySQL",
        "Hibernate",
        "JPA",
        "Kafka",
        "Docker",
        "AWS",
        "JUnit",
        "Kubernetes",
    ],
    "education": [{"school": "State University", "degree": "B.S."}],
}

JD_STRONG_JAVA = """
Java Developer

Requirements:
- Professional experience with Java and Spring Boot
- Build REST APIs and microservices
- Hibernate and JPA for SQL MySQL access
- Docker and AWS deployments
- Unit tests with JUnit

Preferred:
- Kafka event-driven systems
- Kubernetes operations
"""

JD_GOOD_PARTIAL = """
Backend Software Engineer

Requirements:
- Java and Spring Boot for backend services
- Experience with COBOL mainframe batch jobs
- Salesforce Apex programming
- REST APIs for internal tools
"""

JD_WEAK_ANDROID = """
Android Engineer

Requirements:
- Kotlin and Jetpack Compose
- Android SDK and Play Store releases
- Mobile UI animations and Gradle modules
"""

JD_KEYWORD_TRAP = JD_STRONG_JAVA

JD_DATA_SCIENTIST = """
Data Scientist

Requirements:
- Python pandas numpy tensorflow
- Machine learning models and statistics
- Tableau dashboards and A/B testing
"""

JD_NO_HEADING = """
We need someone who can write Java and Spring Boot services.
You will design REST APIs and microservices used by internal tools.
Hibernate and JPA experience with MySQL is expected.
Docker and AWS should be familiar.
JUnit testing is part of the daily work.
"""

JD_NEEDS_MANUAL = """
Join us.
Benefits:
- 401k
- Unlimited PTO
Equal opportunity:
- We celebrate diversity
"""

JD_NICE_HEAVY = """
Java Developer

Requirements:
- Professional experience with Java and Spring Boot
- Build REST APIs for internal tools
- Deliver backend microservices in production
- Hibernate and JPA with MySQL

Preferred:
- COBOL mainframe expertise
- Salesforce Apex
- SAP ABAP programming
- Unreal Engine gameplay systems
"""

JD_STAFF = JD_STRONG_JAVA
JD_INTERN = JD_STRONG_JAVA
JD_FRONTEND_COBOL = """
Software Engineer

Requirements:
- COBOL and mainframe CICS
- JCL batch scheduling
- VSAM file design
"""
