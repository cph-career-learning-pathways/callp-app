# Career and Lifelong Learning Pathway (CaLLP)

CaLLP is a web application designed to connect students and alumni with
external learning resources that support career development and lifelong
learning goals.

The application is being developed using Django and is deployed through AWS
Elastic Beanstalk with an Amazon RDS MySQL database.

## Development Site

The CaLLP development environment is available at:

**https://callp.dev**

The development site uses HTTPS and is hosted through AWS Elastic Beanstalk.

> The development environment is actively under construction and may change
> as functionality is migrated from the original prototype.

## Technology Overview

CaLLP currently uses or is being migrated toward the following technology
stack:

```text
Application
├── Python
├── Django
└── MySQL

Infrastructure
├── AWS Elastic Beanstalk
├── Amazon EC2
├── Amazon RDS
├── AWS Systems Manager Parameter Store
└── nginx

Domain / HTTPS
├── Porkbun DNS
├── callp.dev
├── Let's Encrypt
└── Certbot

Development
├── Git
└── GitHub
```

## Repository Structure

The working Django application uses the repository root as its deployment root.

```text
callp-app/
├── .github/
├── docs/
├── .platform/
├── config/
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

The repository is currently being migrated from the original prototype.
Some directories and deployment files shown above may not yet exist on all
branches.

See [Architecture](docs/ARCHITECTURE.md) for the detailed repository structure
and component responsibilities.

## Documentation

Project documentation is maintained in [`docs/`](docs/).

### Technical Documentation

- [Architecture](docs/ARCHITECTURE.md)  
  Repository organization, Django application structure, component
  responsibilities, and software architecture.

- [Infrastructure](docs/INFRASTRUCTURE.md)  
  AWS infrastructure, Elastic Beanstalk, RDS, networking, security groups,
  IAM, Parameter Store, domain/DNS, HTTPS, and infrastructure lifecycle.

- [AWS Access Guide](docs/AWS_ACCESS_GUIDE.md) -- **Pending Creation** 
  Procedures for developers to access AWS, CloudShell, VPC resources,
  Elastic Beanstalk, and RDS.

- [Database Setup](docs/DATABASE_SETUP.md) -- **Pending Creation** 
  RDS database initialization, schema and data loading, database accounts,
  and application database connectivity.

### Development Process

- [Git Workflow](docs/git-workflow.md)  
  Team branching, Git, and contribution workflow.

- [Contributing](CONTRIBUTING.md)  
  Project contribution expectations and guidelines.

- [Security Policy](SECURITY.md)  
  Security practices and vulnerability reporting information.

### Requirements

- [Software Requirements Specification](docs/SE%20-%20Software%20Requirements%20Specification.pdf)  
  Formal CaLLP software requirements specification.

## Development Architecture

At a high level, the development environment is structured as:

```text
                       Users
                         │
                         │ HTTPS
                         ▼
                     callp.dev
                         │
                    Porkbun DNS
                         │
                         ▼
                Elastic Beanstalk
                         │
                         ▼
                   EC2 / nginx
                         │
                         ▼
                      Django
                         │
                         │ MySQL
                         ▼
                    Amazon RDS
```

The RDS database is provisioned independently from Elastic Beanstalk.
Rebuilding or terminating the Elastic Beanstalk environment therefore does
not intentionally remove the database or its stored data.

For the complete deployment and infrastructure design, see
[Infrastructure](docs/INFRASTRUCTURE.md).

## Local Development

Detailed local development instructions will be updated as the original
prototype is migrated into this repository.

The target Django project structure uses:

```text
config/
```

as the project-wide Django configuration package, with `manage.py` located at
the repository root.

Local credentials and environment-specific values must not be committed to
Git. Required environment variables should be documented in:

```text
.env.example
```

Developers should use their own local `.env` file where appropriate.

## Database

The shared development database is hosted using Amazon RDS for MySQL.

Application code connects using a dedicated application database account.
Developer and administrative database accounts are kept separate from the
application account.

Database passwords and other credentials must never be committed to the
repository.

For database setup and initialization procedures, see
[Database Setup](docs/DATABASE_SETUP.md).

For AWS connectivity and developer access procedures, see
[AWS Access Guide](docs/AWS_ACCESS_GUIDE.md).

## Contributing

Before beginning development work, review:

1. [Contributing Guidelines](CONTRIBUTING.md)
2. [Git Workflow](docs/git-workflow.md)
3. [Architecture](docs/ARCHITECTURE.md)

Infrastructure or database work should also reference:

- [Infrastructure](docs/INFRASTRUCTURE.md)
- [AWS Access Guide](docs/AWS_ACCESS_GUIDE.md)  -- **Pending Creation** 
- [Database Setup](docs/DATABASE_SETUP.md)  -- **Pending Creation** 

Please use the appropriate GitHub issue template when creating bugs, features,
research items, or development tasks.

## Security

Do not commit:

```text
.env files
database passwords
AWS credentials
TLS certificates or private keys
database dumps containing application data
other local secrets
```

See [Security Policy](SECURITY.md) for project security guidance.

## License

See [LICENSE](LICENSE) for project licensing information.