# CaLLP Repository Architecture

This document describes the organization of the CaLLP application repository,
the responsibilities of its major directories and files, and the infrastructure
supporting the application.

---

## Repository Overview

```text
callp-app/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug.md
│   │   ├── feature.md
│   │   ├── research.md
│   │   └── task.md
│   └── pull_request_template.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AWS_ACCESS_GUIDE.md
│   ├── DATABASE_SETUP.md
│   ├── SE - Software Requirements Specification.pdf
│   └── git-workflow.md
│
├── .platform/
│   └── hooks/
│       └── postdeploy/
│           └── 01_configure_https.sh
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── landing/
├── resource_discovery/
│
├── manage.py
├── requirements.txt
├── .env.example
├── Procfile
│
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── SECURITY.md
```

> This tree represents the target repository architecture during migration
> from the original prototype. Some application and deployment files may not
> yet exist on all branches.

---

## `.github/`

GitHub-specific project management, issue tracking, and contribution
configuration.

```text
.github/
├── ISSUE_TEMPLATE/
│   └── GitHub issue templates used to categorize and standardize project work
│
└── pull_request_template.md
    └── standard structure and checklist for project pull requests
```

### `.github/ISSUE_TEMPLATE/`

Templates used when creating GitHub issues. Separating issue types provides
consistent information for different categories of project work.

```text
ISSUE_TEMPLATE/
├── bug.md
│   └── template for reporting software defects and unexpected behavior
│
├── feature.md
│   └── template for proposing new application features or enhancements
│
├── research.md
│   └── template for research, investigation, and exploratory work
│
└── task.md
    └── template for implementation, maintenance, documentation, and other
        general project tasks
```

---

docs/
├── ARCHITECTURE.md
│   └── repository structure and software architecture
│
├── INFRASTRUCTURE.md
│   └── AWS deployment topology, networking, security, domain,
│       HTTPS, RDS, IAM, and environment lifecycle
│
├── AWS_ACCESS_GUIDE.md
│   └── developer access to AWS, CloudShell, VPC resources,
│       RDS, and Elastic Beanstalk
│
├── DATABASE_SETUP.md
│   └── database initialization, schema/data loading,
│       application database user, and Django connectivity
│
├── SE - Software Requirements Specification.pdf
│   └── formal software requirements specification
│
└── git-workflow.md
    └── team Git and branch workflow

---

## `.platform/`

Elastic Beanstalk platform configuration deployed with the application.

```text
.platform/
└── hooks/
    └── postdeploy/
        └── 01_configure_https.sh
            └── provisions and configures HTTPS support for the
                single-instance development environment
```

This configuration is intended to make the nginx and certificate setup
reproducible when Elastic Beanstalk replaces the underlying EC2 instance.

---

## `config/`

Project-wide Django configuration. Application functionality should normally
live in individual Django applications rather than this package.

```text
config/
├── __init__.py
│   └── identifies config as a Python package
│
├── settings.py
│   └── Django project settings and environment configuration
│
├── urls.py
│   └── root URL configuration
│
├── asgi.py
│   └── ASGI application entry point
│
└── wsgi.py
    └── WSGI application entry point used by the deployed web application
```

---

## `landing/`

Primary Django application for the CaLLP web interface.

```text
landing/
├── migrations/
│   └── Django-managed database schema migrations
│
├── static/
│   └── application-specific CSS, JavaScript, images, and other static assets
│
├── templates/
│   └── Django HTML templates
│
├── admin.py
│   └── Django administrative interface configuration
│
├── apps.py
│   └── Django application configuration
│
├── models.py
│   └── application data models
│
├── tests.py
│   └── application tests
│
├── urls.py
│   └── application URL routing
│
└── views.py
    └── request handling and presentation logic
```

The exact structure will evolve as functionality is migrated from the
prototype.

---

## `resource_discovery/`

Resource discovery functionality migrated from the original prototype.

```text
resource_discovery/
└── ...
    └── resource searching, filtering, metadata extraction, and related
        discovery functionality
```

This section should be expanded as the prototype functionality is migrated and
its permanent module boundaries are established.

---

## Root Files

Repository-wide Django, deployment, dependency, and project configuration.

```text
callp-app/
├── manage.py
│   └── Django administrative command entry point
│
├── requirements.txt
│   └── Python dependencies required by the deployed application
│
├── .env.example
│   └── template documenting required local environment variables without
│       storing credentials
│
├── Procfile
│   └── defines the web process used by Elastic Beanstalk
│
├── .gitignore
│   └── excludes generated, local, secret, and machine-specific files from
│       source control
│
├── CONTRIBUTING.md
│   └── project contribution guidelines
│
├── LICENSE
│   └── project software license
│
├── README.md
│   └── primary project introduction and documentation entry point
│
└── SECURITY.md
    └── project security policy and vulnerability reporting information
```