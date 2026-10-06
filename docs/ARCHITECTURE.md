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
│   ├── INFRASTRUCTURE.md
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
├── frontend/
│   ├── account_page/
│   ├── search_page/
│   └── landing/
│
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

## `docs/`

Project documentation, technical references, and developer guides.

```text
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
```

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

## `frontend/`

Contains the user-facing Django components that make up the CaLLP web
interface.

Rather than implementing the entire interface as a single monolithic Django
application, frontend functionality is divided into modular components based
on distinct areas of the website.

```text
frontend/
├── account_page/
│   └── account, profile, and related user-facing functionality
│
├── search_page/
│   └── resource search and discovery interface
│
└── landing/
    └── landing page and associated public-facing interface
```

Each component may be implemented as its own Django application where
appropriate. A component can therefore maintain the templates, static assets,
URL routing, views, tests, and other application code specific to that portion
of the website.

A typical frontend component may use a structure such as:

```text
frontend/
└── component_name/
    ├── migrations/
    │   └── Django-managed database schema migrations, when required
    │
    ├── static/
    │   └── component-specific CSS, JavaScript, images, and other static assets
    │
    ├── templates/
    │   └── component-specific Django HTML templates
    │
    ├── __init__.py
    │   └── identifies the component as a Python package
    │
    ├── admin.py
    │   └── Django administrative interface configuration, when required
    │
    ├── apps.py
    │   └── Django application configuration
    │
    ├── models.py
    │   └── component-specific data models, when required
    │
    ├── tests.py
    │   └── component tests
    │
    ├── urls.py
    │   └── component URL routing
    │
    └── views.py
        └── request handling and presentation logic
```

Not every frontend component is required to contain every file or directory
shown above. Components should contain only the functionality they require.

Shared frontend functionality should be factored into an appropriate shared
location rather than duplicated between components as the frontend
architecture develops.

The exact frontend component structure will evolve as functionality is
migrated from the original prototype and additional website areas are
implemented.

---

## `resource_discovery/`

Resource discovery functionality migrated from the original prototype.

```text
resource_discovery/
└── ...
    └── resource searching, filtering, metadata extraction, and related
        discovery functionality
```

`resource_discovery/` contains the underlying resource discovery functionality
rather than the user-facing search interface. The corresponding presentation
and interaction layer belongs in the appropriate component under `frontend/`,
such as `frontend/search_page/`.

This separation allows resource discovery logic to evolve independently from
the website interface that consumes it.

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