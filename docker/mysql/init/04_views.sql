/*
==============================================
Clay Cordary
Last modified by: Roselie Freixas
CS 458 - Software Engineering
Version - v0.5
Last Modified: 05-OCT-2026

FILE 4 of 5: VIEWS
Creates curator-visibility views on top of career_resource.

Run this AFTER 01_schema_setup.sql, 02_triggers, and 03_seed_reserved_accounts.sql.
==============================================
*/

/*
===============================================================================
Views for resource creator visibility
- public_resource_creators: masks curator_id when is_anonymous = 'Y', for use
  by any user-facing display of who added a resource
- admin_resource_creators: always shows the real curator_id, for internal
  moderation/auditing use only - should not be exposed to student-facing
  views or roles
===============================================================================
*/

create or replace view public_resource_creators as
select resource_id,
       resource_title,
       case
           when is_anonymous = 'Y' then null
           else curator_id
       end as curator_id,
       is_anonymous,
       source_id,
       resource_pub_date,
       resource_refresh_date
from career_resource;

create or replace view admin_resource_creators as
select resource_id,
       resource_title,
       curator_id,
       is_anonymous,
       source_id,
       resource_pub_date,
       resource_refresh_date
from career_resource;