# CaLLP Infrastructure

This document describes the infrastructure used to deploy and operate the
Career and Lifelong Learning Pathway (CaLLP) application.

It documents the relationship between the application's AWS resources,
networking, domain, HTTPS configuration, database, credentials, and deployment
environment.

Procedural instructions for developers should be maintained separately in the
appropriate access or setup guide.

---

## 1. Infrastructure Overview

The CaLLP development application is hosted in AWS using Elastic Beanstalk and
Amazon RDS.

The public development domain is registered and managed through Porkbun.

```text
                         Internet
                            │
                            │ HTTPS
                            ▼
                        callp.dev
                     www.callp.dev
                            │
                            ▼
                       Porkbun DNS
                            │
                            ▼
                 Elastic Beanstalk
                   CaLLP-Dev-env
                            │
                            ▼
                      EC2 Instance
                            │
                     nginx / HTTPS
                            │
                     Django / WSGI
                            │
                            │ MySQL TCP 3306
                            ▼
                       Amazon RDS
                      callp-dev-db
                            │
                            ▼
                      callp_dev_db
```

The RDS database is provisioned independently from Elastic Beanstalk.

This separation is intentional. Replacing or terminating the Elastic Beanstalk
environment must not terminate the RDS database or its stored application data.

---

## 2. Development Environment

The current AWS environment is the CaLLP development environment.

```text
Environment
├── Elastic Beanstalk: CaLLP-Dev-env
├── Environment type: Single instance
├── AWS Region: us-west-2
├── Platform: Python 3.14 / Amazon Linux 2023
├── Architecture: x86_64
├── EC2 instance class: t3.micro
└── Database: callp-dev-db
```

The environment currently uses a single-instance Elastic Beanstalk
configuration rather than a load-balanced environment.

This keeps the development infrastructure relatively simple and avoids the
additional recurring cost of an Application Load Balancer.

A future production environment may use a different architecture.

---

## 3. Domain and DNS

The public development domain is:

```text
callp.dev
```

The domain is registered through Porkbun, which also provides authoritative DNS
for the domain.

The following DNS relationships are configured:

```text
callp.dev
    │
    │ ALIAS
    ▼
CaLLP-Dev-env.eba-hpqjwwfm.us-west-2.elasticbeanstalk.com


www.callp.dev
    │
    │ CNAME
    ▼
CaLLP-Dev-env.eba-hpqjwwfm.us-west-2.elasticbeanstalk.com
```

The Elastic Beanstalk hostname is the infrastructure destination. Users access
the application through `callp.dev` or `www.callp.dev`.

The domain must not be pointed directly at the current EC2 instance's IP
address because Elastic Beanstalk may replace that instance.

### `.dev` HTTPS Requirement

The `.dev` top-level domain is HSTS-preloaded by modern browsers.

As a result, the CaLLP development site must provide valid HTTPS. Plain HTTP
cannot be relied upon for browser access to the domain.

---

## 4. Elastic Beanstalk

Elastic Beanstalk manages the application hosting environment.

```text
Elastic Beanstalk
└── CaLLP-Dev-env
    ├── Python platform
    ├── Amazon Linux 2023
    ├── EC2 instance
    ├── nginx reverse proxy
    ├── application environment variables
    └── application deployment lifecycle
```

Elastic Beanstalk may replace its underlying EC2 instance during environment
rebuilds, platform updates, configuration changes, or other lifecycle events.

The application must therefore treat EC2 instances as replaceable
infrastructure.

Configuration performed manually on an EC2 instance must not be considered
permanent infrastructure.

---

## 5. HTTPS and nginx

HTTPS currently terminates directly on the Elastic Beanstalk EC2 instance.

The development environment does not currently use an Application Load
Balancer.

```text
Internet
   │
   ├── HTTP :80
   │       │
   │       └── 301 redirect to HTTPS
   │
   └── HTTPS :443
           │
           ▼
         nginx
           │
           ▼
     Django application
```

### Certificate

TLS certificates are currently provided by Let's Encrypt using Certbot.

The certificate covers:

```text
callp.dev
www.callp.dev
```

The current certificate is stored on the EC2 instance using the standard
Certbot paths:

```text
/etc/letsencrypt/live/callp.dev/fullchain.pem
/etc/letsencrypt/live/callp.dev/privkey.pem
```

Certificate files and private keys must never be committed to the repository.

### nginx HTTPS Configuration

The verified HTTPS server configuration uses the existing Elastic Beanstalk
application proxy configuration:

```text
/etc/nginx/conf.d/elasticbeanstalk/00_application.conf
```

The HTTPS server listens on TCP port 443 and proxies application requests
through this existing Beanstalk configuration.

The Beanstalk `healthd.conf` file is not duplicated into the HTTPS server.

### HTTP Redirect

Requests for:

```text
http://callp.dev
http://www.callp.dev
```

are redirected with HTTP 301 responses to their corresponding HTTPS URLs.

The Elastic Beanstalk default HTTP server remains available as the nginx
default server. A separate named server handles redirects for the CaLLP domain.

### Current Persistence Status

The HTTPS configuration has been successfully validated on the current EC2
instance.

The following behavior has been verified:

```text
http://callp.dev
    → 301 → https://callp.dev
    → 200 OK

http://www.callp.dev
    → 301 → https://www.callp.dev
    → 200 OK
```

However, the current Certbot installation, certificate state, and custom nginx
configuration were initially established manually on the current EC2 instance.

They must therefore be automated through Elastic Beanstalk deployment
configuration before HTTPS can be considered resilient to instance
replacement.

The planned repository location for this automation is:

```text
.platform/
└── hooks/
    └── postdeploy/
        └── 01_configure_https.sh
```

The deployment automation should:

1. Ensure Certbot and its nginx integration are available.
2. Determine whether the required certificate already exists.
3. Obtain a certificate when necessary.
4. Avoid unnecessarily requesting a new certificate on every deployment.
5. Configure the HTTPS nginx server.
6. Configure the HTTP-to-HTTPS redirect.
7. Validate nginx configuration before reloading it.
8. Preserve Certbot certificate renewal.
9. Recover correctly when Elastic Beanstalk creates a replacement instance.

---

## 6. VPC and Networking

Elastic Beanstalk and RDS reside in the same AWS VPC.

```text
VPC
vpc-0af02992f0d51bd7a
│
├── Elastic Beanstalk
│   └── EC2 / Django
│
└── Amazon RDS
    └── callp-dev-db
```

The development environment and database use the same VPC so application
traffic can reach RDS through AWS networking without exposing the database
publicly.

The RDS instance is configured as:

```text
Publicly accessible: No
MySQL port:          3306
```

---

## 7. Security Groups

Network access between application components is controlled using AWS security
groups.

### Elastic Beanstalk EC2 Security Group

```text
Security Group:
sg-08c470728edcd66dc
```

Public application traffic currently includes:

```text
HTTP     TCP 80
HTTPS    TCP 443
```

SSH access used for EC2 Instance Connect is restricted using the AWS-managed
EC2 Instance Connect prefix list rather than exposing SSH broadly to the
internet.

### RDS Security Group

```text
Security Group:
callp-dev-rds-sg
sg-003de1d1c5fab41e8
```

The RDS security group permits MySQL traffic on TCP port 3306 from the Elastic
Beanstalk EC2 security group.

Conceptually:

```text
Elastic Beanstalk EC2
sg-08c470728edcd66dc
        │
        │ TCP 3306
        ▼
RDS Security Group
sg-003de1d1c5fab41e8
        │
        ▼
callp-dev-db
```

MySQL port 3306 must not be opened to `0.0.0.0/0`.

---

## 8. Amazon RDS

CaLLP uses Amazon RDS for MySQL database hosting.

```text
RDS Instance
└── callp-dev-db
    └── Database
        └── callp_dev_db
```

The database is maintained independently of the Elastic Beanstalk environment.

### Database Lifecycle

The intended resource lifecycle is:

```text
Elastic Beanstalk
    │
    ├── may be rebuilt
    ├── may replace EC2
    └── may be terminated

RDS
    │
    └── remains intact independently
```

Application deployments and Beanstalk environment replacement must not destroy
the database.

---

## 9. Database Accounts

Database accounts are separated by responsibility. Application code should not
use an administrative or developer database account.

```text
callp_admin
    └── RDS master/admin account

Developer accounts
    ├── BlueSkyes643
    ├── Cxdary
    ├── theRivetedRose-admin
    └── YellowjayFlies

callp_web_app
    └── Django application account
```

### RDS Master Account

```text
callp_admin
```

`callp_admin` is the RDS master administrative account.

It is used for database-level administrative operations that require elevated
privileges, such as creating MySQL users and managing their grants.

The master account must not be used by the Django application for routine
database access.

### Developer Accounts

Each developer requiring direct database access uses an individual account
rather than sharing the RDS master account.

Verified developer accounts are:

```text
BlueSkyes643
Cxdary
theRivetedRose-admin
YellowjayFlies
```

Individual developer accounts provide separation between developer activity,
application access, and RDS master administration.

Developer privileges should be limited to those required for development and
database maintenance. Operations requiring RDS master privileges should use
`callp_admin` only when necessary.

### Django Application Account

Django connects to MySQL using:

```text
callp_web_app
```

The account has privileges on:

```text
callp_dev_db.*
```

It does not receive server-wide administrative privileges.

The verified MySQL grants are:

```text
GRANT USAGE ON *.* TO `callp_web_app`@`%`
GRANT ALL PRIVILEGES ON `callp_dev_db`.* TO `callp_web_app`@`%`
```

The `%` host wildcard applies at the MySQL account layer. Network access remains
restricted by the AWS VPC and security groups.

The application account has been independently verified to authenticate to
`callp_dev_db` and read the populated database.

### Account Responsibility Summary

```text
RDS administration
└── callp_admin

Developer database access
├── BlueSkyes643
├── Cxdary
├── theRivetedRose-admin
└── YellowjayFlies

Django application
└── callp_web_app
```

Database passwords and other authentication credentials for these accounts
must never be committed to the repository or included in project
documentation.

---

## 10. Database Connection Configuration

The deployed Django application receives database connection information
through Elastic Beanstalk environment configuration.

```text
RDS_DB_NAME
    → callp_dev_db

RDS_HOSTNAME
    → RDS endpoint

RDS_PORT
    → 3306

RDS_USERNAME
    → callp_web_app

RDS_PASSWORD
    → AWS Systems Manager Parameter Store
```

The database password must not be committed to Git or stored in application
source code.

---

## 11. Parameter Store and Secrets

The `callp_web_app` database password is stored as an AWS Systems Manager
Parameter Store `SecureString`.

```text
Parameter:
/callp/dev/rds/password
```

The parameter is encrypted and is referenced by Elastic Beanstalk rather than
placing the password directly into source control.

The credential path is:

```text
AWS Systems Manager Parameter Store
        │
        │ /callp/dev/rds/password
        ▼
Elastic Beanstalk environment
        │
        │ RDS_PASSWORD
        ▼
Django
        │
        │ callp_web_app
        ▼
Amazon RDS
```

The parameter ARN is:

```text
arn:aws:ssm:us-west-2:919551760563:parameter/callp/dev/rds/password
```

The secret value itself must never appear in project documentation.

---

## 12. IAM

The Elastic Beanstalk EC2 instances use the role:

```text
aws-elasticbeanstalk-ec2-role
```

A narrowly scoped inline policy allows this role to retrieve only the
application database password parameter.

```text
Policy:
CallpDevRdsPasswordAccess

Allowed action:
ssm:GetParameter

Allowed resource:
/callp/dev/rds/password
```

Conceptually:

```text
aws-elasticbeanstalk-ec2-role
        │
        │ ssm:GetParameter
        ▼
/callp/dev/rds/password
```

The application role should not receive broad access to unrelated Parameter
Store values.

---

## 13. Django Deployment Architecture

The target Django repository structure uses the repository root as the
deployment root.

```text
callp-app/
├── manage.py
├── requirements.txt
├── Procfile
├── .platform/
├── config/
├── landing/
└── resource_discovery/
```

The Django project configuration package is:

```text
config/
```

This avoids the duplicated project-directory naming used by the original
prototype.

The expected WSGI application entry point is:

```text
config.wsgi:application
```

The `Procfile` will define the web process used by Elastic Beanstalk.

Application-specific deployment configuration will be finalized during the
prototype migration.

---

## 14. Infrastructure Lifecycle

The infrastructure is intentionally divided into resources with different
lifecycles.

```text
Persistent
├── RDS database
├── database data
├── Parameter Store secrets
├── Porkbun domain
└── DNS configuration

Replaceable
├── Elastic Beanstalk environment
├── EC2 instance
├── application deployment
└── generated nginx runtime configuration
```

Infrastructure configuration required by a replacement EC2 instance should be
represented in the repository or another persistent infrastructure service.

Manual changes made only to a running EC2 instance are not considered durable
configuration.

---

## 15. Repository Infrastructure Configuration

Infrastructure-related files that belong in source control are expected to
include:

```text
callp-app/
├── Procfile
│   └── Elastic Beanstalk web process configuration
│
├── .platform/
│   └── Elastic Beanstalk platform hooks and nginx/HTTPS automation
│
├── .env.example
│   └── documents expected environment variables without secret values
│
└── docs/
    ├── INFRASTRUCTURE.md
    ├── AWS_ACCESS_GUIDE.md
    └── DATABASE_SETUP.md
```

The following must not be committed:

```text
.env
database passwords
AWS credentials
TLS private keys
Let's Encrypt certificate files
database dumps containing application data
local Elastic Beanstalk CLI state
```

---

## 16. Related Documentation

```text
docs/
├── ARCHITECTURE.md
│   └── repository and software architecture
│
├── INFRASTRUCTURE.md
│   └── AWS, networking, deployment, domain, HTTPS, database, IAM,
│       and infrastructure lifecycle
│
├── AWS_ACCESS_GUIDE.md
│   └── developer procedures for accessing AWS resources
│
├── DATABASE_SETUP.md
│   └── database initialization, population, users, and connectivity
│
├── SE - Software Requirements Specification.pdf
│   └── formal software requirements
│
└── git-workflow.md
    └── team Git and branching workflow
```

---

## 17. Current Infrastructure Status

The following infrastructure has been established and verified:

```text
✓ callp.dev registered through Porkbun
✓ callp.dev DNS points to Elastic Beanstalk
✓ www.callp.dev DNS points to Elastic Beanstalk
✓ Elastic Beanstalk and RDS share the same VPC
✓ RDS is not publicly accessible
✓ Beanstalk security group is authorized to reach RDS on TCP 3306
✓ callp_web_app database account created and tested
✓ Database password stored as an SSM SecureString
✓ Beanstalk EC2 role authorized to retrieve the password parameter
✓ Beanstalk environment successfully resolves the Parameter Store secret
✓ TCP 443 enabled for the web application
✓ Let's Encrypt certificate issued for callp.dev and www.callp.dev
✓ nginx successfully serves both domains over HTTPS
✓ HTTP requests redirect to HTTPS
```

The following infrastructure work remains:

```text
○ Move the verified Certbot/nginx configuration into persistent
  Elastic Beanstalk deployment automation

○ Complete the Django migration into the callp-app repository

○ Configure Django for RDS environment variables

○ Configure the production-style Django security settings required by
  callp.dev

○ Configure the final Procfile / WSGI process

○ Configure static-file collection and serving

○ Validate Django migrations against the existing populated RDS schema

○ Perform the first Django deployment to CaLLP-Dev-env

○ Validate the complete browser → Django → RDS path
```

---

## 18. Maintenance

This document should be updated when changes are made to:

- AWS services used by CaLLP
- VPC or subnet architecture
- security groups
- Elastic Beanstalk environment topology
- database hosting or lifecycle
- database accounts and application access
- IAM roles or application permissions
- Parameter Store configuration
- domain or DNS configuration
- HTTPS termination or certificate management
- deployment architecture
- development, staging, or production environments

Procedural instructions should remain in the appropriate setup/access guide
rather than being duplicated here.