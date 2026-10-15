/*
==============================================
MySQL VERSION
==============================================
Clay Cordary
Last modified by: Roselie Freixas
CS 458 - Software Engineering
Version - v0.4
Last Modified: 02-OCT-2026

FILE 3 of 5: SEED RESERVED ACCOUNTS
Inserts the three reserved system accounts into 'account' table.

Run this AFTER 01_schema_setup.sql (requires account to exist).
Re-running is safe only if none of the reserved acc_id values already exist.
If any reserved account is already present, the insert for that acc_id will fail
on the primary key constraint.
==============================================
*/

/*
===============================================================================
Reserved system accounts
- 00000000: scraper/system account - explicitly set as curator_id by
  the scraper on every insert it performs
- 99999999: developer/testing placeholder account - used for dev-generated
  test entries during prototyping; true submitter anonymity is handled via
  the is_anonymous flag on career_resource, not by this account
- 11111111: "Unset Curator" fallback account - NOT an intentional
  origin value; this is the DB-level default for curator_id and should only
  ever appear if an insert failed to explicitly supply a curator_id. Rows
  carrying this value flag an application-layer bug and should be audited.
===============================================================================
*/

insert into account (acc_id, acc_fname, acc_lname, acc_email, acc_role, acc_status)
values ('00000000', 'System', 'Scraper', 'scraper@internal.system', 'system', 'active');

insert into account (acc_id, acc_fname, acc_lname, acc_email, acc_role, acc_status)
values ('99999999', 'Dev', 'Account', 'dev@internal.system', 'developer', 'active');

insert into account (acc_id, acc_fname, acc_lname, acc_email, acc_role, acc_status)
values ('11111111', 'Unset', 'Curator', 'unsetcurator@internal.system', 'system', 'active');

commit;
