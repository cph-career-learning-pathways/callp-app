/*
==============================================
MySQL VERSION
==============================================
Created by: Clay Cordary
Last modified by: Roselie Freixas
CS 458 - Software Engineering
Version - v0.5
Last Modified: 05-OCT-2026

FILE 1 of 5: SCHEMA SETUP
Contains DROP TABLE / CREATE TABLE statements only.

** WARNING: This file is DESTRUCTIVE. **
Running this file drops and recreates every table in the schema,
permanently deleting all existing data (career_resource entries,
category mappings, user interests, non-reserved user accounts, etc).

Only run this file for an intentional full reset (e.g. initial setup,
or a deliberate wipe during early prototyping). Once real data exists
that you want to keep, do NOT run this file again - use ALTER TABLE
for structural changes instead.

After running this file, run 02_triggers.sql to restore database triggers, 03_seed_reserved_accounts.sql to restore
the three reserved system accounts, then 04_views.sql to recreate the
curator-visibility views.
==============================================
*/

/*
==============================
DROP ALL TABLES
==============================
*/

SET FOREIGN_KEY_CHECKS = 0;

drop table if exists account;
drop table if exists category;
drop table if exists source;
drop table if exists price_model;
drop table if exists filter;
drop table if exists career_resource;
drop table if exists curated_collection;
drop table if exists user_interests;
drop table if exists collection_resources;
drop table if exists resource_category;
drop table if exists resource_filter;
drop table if exists category_parent;

SET FOREIGN_KEY_CHECKS = 1;
/*

==============================
CREATE TABLES
==============================

===============================================================================
Table 'account' contains pertinent information about registered users,
including the three reserved system accounts used for career_resource attribution
- acc_id: unique 8-digit identifier for each user
           (00000000 reserved for the scraper/system account,
            99999999 reserved for the developer/testing placeholder account,
            11111111 reserved for the "Unset Curator" fallback account -
            all three are excluded from the UID generator's output range)
- acc_fname: user's first name
- acc_lname: user's last name
- acc_email: user's email address (must contain exactly one '@' and one '.')
- acc_role: role of the user within the system
- acc_status: the current status of the user account

uniqueness prevents multiple accounts from using the same email address
===============================================================================
*/

create table account
(acc_id            char(8)        not null    check (acc_id regexp '^[0-9]{8}$'),
 acc_fname         varchar(100)   not null,
 acc_lname         varchar(100)   not null,
 acc_email         varchar(50)    not null    check (regexp_like (
                                                        acc_email,
                                                        '^[^@.]+@[^@.]+[.][^@.]+$'
                                                    )),
 acc_role          varchar(10)    not null    check (acc_role in (
                                                        'student',
                                                        'teacher',
                                                        'admin',
                                                        'alumni',
                                                        'developer',
                                                        'system'
                                                    )),
 acc_status        varchar(20)    not null    check (acc_status in (
                                                        'active',
                                                        'inactive',
                                                        'suspended',
                                                        'pending',
                                                        'locked',
                                                        'archived',
                                                        'deleted'
                                                    )),

 primary key (acc_id),
 unique (acc_email)
);

/*
===============================================================================
Table 'category' contains the list of career-interest categories that
resources and user interests can be associated with
- category_id: unique 8-digit identifier for each category
- curator_id: user-id belonging to user responsible for creating and maintaining category
- category_type: identifies the type of category as 'skill', 'degree program', or 'career field'
- category_name: display name of the category such as 'resume', 'Computer Science', or 'SOC Analyst',
- is_active: flag to identify whether the category is currently in use

uniqueness ensures category names are unique within each category type
===============================================================================
*/

create table category
(category_id        char(8)         not null        check (category_id regexp '^[0-9]{8}$'),
 curator_id         char(8)         not null        default '11111111',
 category_type      varchar(20)     not null        check (category_type in (
                                                                'skill',
                                                                'degree program',
                                                                'career field'
                                                           )),
 category_name      varchar(100)    not null,
 is_active          char(1)         not null        default 'Y'     check (is_active in ('Y', 'N')),
 primary key (category_id),
 foreign key (curator_id) references account(acc_id),
 unique (category_type, category_name)
);

/*
===============================================================================
Table 'source' contains information about each source a resource refers
- source_id: unique 8-digit identifier for each source
- curator_id: foreign key to identify the user who provided the source
- source_name: name of the source
- source_domain: url/domain name that directs to the source
- source_trust: a filter for sources that can classify them as:
    - 'trusted':    vetted by developers, admins, and teachers
    - 'normal':     unvetted, but viewable to all users
    - 'blocked':    unable to be viewed as a resource, only seen by admins and developers
- source_add_date: date/time for when source was added, default current_timestamp
- source_up_date: date/time for when source was last checked/vetted, default null
===============================================================================
*/

create table source
(source_id          char(8)         not null    check (source_id regexp '^[0-9]{8}$'),
 curator_id         char(8)         not null    default '11111111',
 source_name        varchar(50),
 source_domain      varchar(253),
 source_trust       varchar(7)      not null   default 'normal'    check(source_trust in (
                                                                            'trusted',
                                                                            'normal',
                                                                            'blocked'
                                                                         )),
 source_add_date    datetime        not null    default (now()),
 source_up_date     datetime        default null,
 is_active          char(1)         not null    default 'Y'         check (is_active in ('Y', 'N')),
 primary key (source_id),
 foreign key (curator_id) references account(acc_id)
);

/*
===============================================================================
Table 'price_model' contains information regarding the pricing structure
- price_model_id: unique 8-digit identifier for each pricing model
- price_model_name: name of each price model
- is_active: flag to indicate whether the pricing model is accurate/retired

uniqueness prevents duplicate price model names
===============================================================================
*/

create table price_model
( price_model_id    char(8)         not null    check (price_model_id regexp '^[0-9]{8}$'),
  price_model_name  varchar(20)     not null,
  is_active         char(1)         not null    default 'Y'     check (is_active in ('Y', 'N')),
  primary key (price_model_id),
  unique (price_model_name)
);

/*
===============================================================================
Table 'filter' used to provide additional filters to fine-tune user searches
- filter_id: unique 8-digit identifier for filter
- curator_id: user-id belonging to user responsible for creating and maintaining filter
- filter_type: allows grouping of various filters
- filter_name: name of specific filter for searches
- is_active: flag to determine whether filter is currently in use

uniqueness ensures filter names are unique within each filter type
===============================================================================
*/

create table filter
(filter_id          char(8)         not null    check (filter_id regexp '^[0-9]{8}$'),
 curator_id         char(8)         not null    default '11111111',
 filter_type        varchar(30)     not null,
 filter_name        varchar(30)     not null,
 is_active          char(1)         not null    default 'Y'     check (is_active in ('Y', 'N')),
 primary key (filter_id),
 foreign key (curator_id) references account(acc_id),
 unique (filter_type, filter_name)
);

/*
===============================================================================
Table 'career_resource' contains pertinent information about each career resource
made available to users
- resource_id: unique 8-digit identifier for each career_resource
- curator_id: unique identifier of the real user who created this career_resource
              record (always a real user account - the scraper explicitly sets its
              own id on every insert it performs; defaults at the DB level to the
              reserved "Unset Curator" account, 11111111, ONLY as a safety net if
              an insert fails to supply curator_id - rows carrying this value flag
              an application-layer gap and should be audited/corrected)
- is_anonymous: 'Y'/'N' flag - when 'Y', the real curator_id above is preserved for
                internal auditing/moderation, but a public-facing view should mask it
                (display null/blank) rather than expose the creator's identity
- source_id: identifies the source associated with the career resource
- resource_title: title of the career resource displayed to users
- resource_url: unique URL linking to the external career resource
- resource_type: type of resource as 'course', 'article', or 'collection'
- resource_format: format of resource content as 'video', 'document', 'webpage', or 'mixed'
- resource_snippet: short description used for card-style previews
- resource_pub_date: date the career resource was originally published, when known
- resource_refresh_date: date and time the resource metadata was last refreshed by the application
- resource_duration: estimated duration in seconds to consume the resource, when known
- price_model_id: identifies the pricing model associated with the resource
- other_metadata: optional JSON data for additional resource-specific metadata
- is_active: 'Y'/'N' flag indicating whether the resource is currently in use

uniqueness prevents the same resource URL from being stored more than once
===============================================================================
*/

create table career_resource
(resource_id            char(8)         not null    check (resource_id regexp '^[0-9]{8}$'),
 curator_id             char(8)         not null    default '11111111',
 is_anonymous           char(1)         not null    default 'N'     check (is_anonymous in ('Y', 'N')),
 source_id              char(8)         not null,
 resource_title         varchar(150)    not null,
 resource_url           varchar(767)    not null,
 resource_type          varchar(15)     not null    check (resource_type in (
                                                                'course',
                                                                'article',
                                                                'collection'
                                                         )),
 resource_format        varchar(20)     not null    check (resource_format in (
                                                                'video',
                                                                'document',
                                                                'webpage',
                                                                'mixed'
                                                          )),
 resource_snippet       text,
 resource_pub_date      datetime,
 resource_refresh_date  datetime        not null    default (now()),
 resource_duration      bigint unsigned default null,
 price_model_id         char(8)         not null,
 other_metadata         JSON            default null,
 is_active              char(1)         not null    default 'Y'     check (is_active in ('Y', 'N')),
 primary key (resource_id),
 foreign key (curator_id) references account(acc_id),
 foreign key (source_id) references source(source_id),
 foreign key (price_model_id) references price_model(price_model_id),
 unique (resource_url)
);

/*
===============================================================================
Table 'curated_collection' used to gather resources into one manageable list
- collection_id: unique 8-digit identifier used to identify the collection
- curator_id: unique identifier of the real user who created this curated_collection
              record (always a real user account - the scraper explicitly sets its
              own id on every insert it performs; defaults at the DB level to the
              reserved "Unset Curator" account, 11111111, ONLY as a safety net if
              an insert fails to supply curator_id - rows carrying this value flag
              an application-layer gap and should be audited/corrected)
- collection_name: title of the collection
- collection_description: holds custom description for the collection
- collection_add_date: datetime collection was created
- collection_up_date: datetime collection was last checked/updated
- is_active: flag to determine whether collection is currently in use/active
===============================================================================
*/

create table curated_collection
(collection_id          char(8)         not null    check (collection_id regexp '^[0-9]{8}$'),
 curator_id             char(8)         not null    default '11111111',
 collection_name        varchar(100)    not null,
 collection_description text,
 collection_add_date    datetime        not null    default (now()),
 collection_up_date     datetime,
 is_active              char(1)         not null    default 'Y'     check (is_active in ('Y', 'N')),
 primary key (collection_id),
 foreign key (curator_id) references account(acc_id)
);

/*
===============================================================================
MULTI-VALUE HANDLER TABLE:
===============================================================================
Table 'user_interests' contains pertinent information about 'users' and their
associated 'categories' of interest
- user_id: unique identifier for the user
- category_id: unique identifier for the category
- intr_date: date the user added this category as an interest
- intr_score: priority score, between 1 and 5, user self-reports for skills
===============================================================================
*/

create table user_interests
(user_id            char(8)             not null,
 category_id        char(8)             not null,
 intr_date          datetime            not null        default (now()),
 intr_score         tinyint unsigned    default null    check (intr_score between 1 and 5),
 primary key (user_id, category_id),
 foreign key (user_id) references account(acc_id),
 foreign key (category_id) references category(category_id)
);

/*
===============================================================================
MULTI-VALUE HANDLER TABLE:
===============================================================================
Table 'collection_resources' associates various resources with collections that are curated
- collection_id: identifier of collection
- resource_id: identifier of resource from career_resource
- sort_order: position of resource according to wishes of curator
- add_date: datetime when resource was added to collection
===============================================================================
*/

create table collection_resources
(collection_id      char(8)             not null,
 resource_id        char(8)             not null,
 sort_order         tinyint unsigned    not null    check (sort_order between 0 and 50),
 add_date           datetime            not null    default (now()),
 primary key (collection_id, resource_id),
 foreign key (collection_id) references curated_collection(collection_id),
 foreign key (resource_id) references career_resource(resource_id)
);

/*
===============================================================================
MULTI-VALUE HANDLER TABLE
===============================================================================
Table 'resource_category' contains pertinent information about 'resources' and their
associated 'category'
- resource_id: unique identifier for the career_resource
- category_id: unique identifier for the category
===============================================================================
*/

create table resource_category
(resource_id        char(8)             not null,
 category_id        char(8)             not null,
 primary key (resource_id, category_id),
 foreign key (resource_id) references career_resource(resource_id),
 foreign key (category_id) references category(category_id)
);

/*
===============================================================================
MULTI-VALUE HANDLER TABLE
===============================================================================
Table 'resource_filter' contains pertinent information about 'resources' and their
associated 'filter'
- resource_id: unique identifier for the career_resource
- filter_id: unique identifier for the filter
===============================================================================
*/

create table resource_filter
(resource_id        char(8)             not null,
 filter_id          char(8)             not null,
 primary key (resource_id, filter_id),
 foreign key (resource_id) references career_resource(resource_id),
 foreign key (filter_id) references filter(filter_id)
);

/*
===============================================================================
MULTI-VALUE HANDLER TABLE
===============================================================================
Table 'category_parent' associates skills with other category types (degree program, career field)
- skill_id: category_id belonging to a category with category_type 'skill'
- parent_id: category_id belonging to a category with category_type
             'degree program' or 'career field'
===============================================================================
*/

create table category_parent
(skill_id           char(8)             not null,
 parent_id          char(8)             not null,
 primary key (skill_id, parent_id),
 foreign key (skill_id) references category(category_id),
 foreign key (parent_id) references category(category_id),
 check (skill_id <> parent_id)
);